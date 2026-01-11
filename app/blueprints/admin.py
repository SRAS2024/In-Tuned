# app/blueprints/admin.py
"""
Admin Blueprint

Handles administrative functionality:
- Admin authentication
- Site maintenance mode
- Notice management
- Feedback viewing
"""

from __future__ import annotations

from datetime import datetime
from io import StringIO

from flask import Blueprint, request, session, g, Response, current_app

from app.db.repositories.site_repository import SiteRepository
from app.db.repositories.feedback_repository import FeedbackRepository
from app.db.repositories.audit_repository import AuditRepository
from app.db.repositories.user_repository import UserRepository
from app.utils.responses import api_response, api_error, paginated_response
from app.utils.validation import ValidationSchema, text_field, boolean_field
from app.utils.security import require_admin, get_client_ip, rate_limit
from app.utils.errors import AuthenticationError, ValidationError, NotFoundError

admin_bp = Blueprint("admin", __name__)


# Validation schemas
ADMIN_LOGIN_SCHEMA = ValidationSchema(
    fields=[
        text_field("username", max_length=100),
        text_field("password", max_length=100),
    ]
)

MAINTENANCE_SCHEMA = ValidationSchema(
    fields=[
        boolean_field("enabled", required=True),
        text_field("message", required=False, max_length=500),
        text_field("dev_password", required=False, max_length=100),
    ]
)

NOTICE_SCHEMA = ValidationSchema(
    fields=[
        text_field("text", max_length=500),
        boolean_field("is_active", required=False, default=True),
    ]
)


@admin_bp.route("/login", methods=["POST"])
@rate_limit(limit=5, window_seconds=60)
def admin_login():
    """Authenticate admin for the admin portal."""
    data = request.get_json(silent=True) or {}
    validated = ADMIN_LOGIN_SCHEMA.validate(data)

    username = validated["username"]
    password = validated["password"]

    audit_repo = AuditRepository()

    # Check against configured admin credentials
    admin_username = current_app.config.get("ADMIN_USERNAME", "")
    admin_password = current_app.config.get("ADMIN_PASSWORD", "")

    if not admin_username or not admin_password:
        current_app.logger.warning(
            "Admin credentials not configured",
            extra={"request_id": getattr(g, "request_id", "unknown")},
        )
        return api_error(
            message="Admin authentication not configured",
            code="AUTH_NOT_CONFIGURED",
            status_code=500,
        )

    if username != admin_username:
        audit_repo.log_action(
            actor_id=None,
            actor_type="admin",
            action="admin_login_failed",
            resource_type="admin",
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
            metadata={"reason": "invalid_username"},
        )
        raise AuthenticationError(
            message="Not authorized",
            error_code="INVALID_CREDENTIALS",
        )

    # Plain text password comparison (like original server.py)
    if password != admin_password:
        audit_repo.log_action(
            actor_id=None,
            actor_type="admin",
            action="admin_login_failed",
            resource_type="admin",
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
            metadata={"reason": "invalid_password"},
        )
        raise AuthenticationError(
            message="Not authorized",
            error_code="INVALID_CREDENTIALS",
        )

    session["is_admin"] = True

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="admin_login",
        resource_type="admin",
        ip_address=get_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="Welcome, Admin!")


@admin_bp.route("/logout", methods=["POST"])
def admin_logout():
    """End admin session."""
    was_admin = session.pop("is_admin", None)

    if was_admin:
        audit_repo = AuditRepository()
        audit_repo.log_action(
            actor_id=None,
            actor_type="admin",
            action="admin_logout",
            resource_type="admin",
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
        )

    return api_response(message="Logged out successfully")


@admin_bp.route("/site-state", methods=["GET"])
@require_admin
def get_admin_site_state():
    """Admin view of site settings and recent notices."""
    site_repo = SiteRepository()

    settings = site_repo.get_settings()
    notices = site_repo.get_all_notices(limit=10)

    return api_response(
        data={
            "settings": settings,
            "notices": notices,
        }
    )


@admin_bp.route("/maintenance", methods=["POST"])
@require_admin
def toggle_maintenance():
    """
    Toggle maintenance mode.

    When enabling maintenance, the developer password must be supplied.
    Disabling does not require the developer password.
    """
    data = request.get_json(silent=True) or {}
    validated = MAINTENANCE_SCHEMA.validate(data)

    enabled = validated["enabled"]
    message = validated.get("message")
    dev_password = validated.get("dev_password")

    # Require dev password to enable maintenance
    if enabled:
        config_dev_password = current_app.config.get("DEV_PASSWORD", "")
        if not config_dev_password:
            return api_error(
                message="Developer password not configured",
                code="CONFIG_ERROR",
                status_code=500,
            )

        # Plain text password comparison (like original server.py)
        if not dev_password or dev_password != config_dev_password:
            raise AuthenticationError(
                message="Developer password required",
                error_code="DEV_PASSWORD_REQUIRED",
            )

    site_repo = SiteRepository()
    audit_repo = AuditRepository()

    # Get current state for audit
    old_settings = site_repo.get_settings()

    result = site_repo.update_maintenance(enabled, message)

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="maintenance_toggle",
        resource_type="site_settings",
        resource_id="1",
        before_state={"maintenance_mode": old_settings.get("maintenance_mode")},
        after_state={"maintenance_mode": enabled},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(
        data={
            "maintenance_mode": result.get("maintenance_mode"),
            "maintenance_message": result.get("maintenance_message"),
        }
    )


@admin_bp.route("/notices", methods=["POST"])
@require_admin
def create_notice():
    """Create a new notice to appear on the main site."""
    data = request.get_json(silent=True) or {}
    validated = NOTICE_SCHEMA.validate(data)

    site_repo = SiteRepository()
    audit_repo = AuditRepository()

    notice = site_repo.create_notice(
        text=validated["text"],
        is_active=validated.get("is_active", True),
    )

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="create",
        resource_type="notice",
        resource_id=str(notice["id"]),
        after_state={"text": notice["text"], "is_active": notice["is_active"]},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"notice": notice}, status_code=201)


@admin_bp.route("/notices/<int:notice_id>", methods=["PATCH"])
@require_admin
def update_notice(notice_id: int):
    """Update notice active status."""
    schema = ValidationSchema(
        fields=[
            boolean_field("is_active", required=True),
        ]
    )

    data = request.get_json(silent=True) or {}
    validated = schema.validate(data)

    site_repo = SiteRepository()
    audit_repo = AuditRepository()

    notice = site_repo.update_notice(notice_id, validated["is_active"])

    if not notice:
        raise NotFoundError("Notice not found")

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="update",
        resource_type="notice",
        resource_id=str(notice_id),
        after_state={"is_active": validated["is_active"]},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"notice": notice})


@admin_bp.route("/feedback", methods=["GET"])
@require_admin
def get_feedback():
    """Get all feedback entries for review."""
    feedback_repo = FeedbackRepository()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    page = max(1, min(page, 1000))
    per_page = max(1, min(per_page, 100))

    feedback = feedback_repo.get_all_feedback(
        limit=per_page,
        offset=(page - 1) * per_page,
    )
    total = feedback_repo.get_feedback_count()

    return paginated_response(
        items=feedback,
        total=total,
        page=page,
        per_page=per_page,
    )


@admin_bp.route("/feedback/download", methods=["GET"])
@require_admin
def download_feedback():
    """Download all feedback as a formatted text document."""
    feedback_repo = FeedbackRepository()

    feedback = feedback_repo.get_feedback_for_export()

    # Build document content
    lines = []
    lines.append("=" * 60)
    lines.append("IN TUNED - FEEDBACK DOCUMENT")
    lines.append("=" * 60)
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Total Feedback Entries: {len(feedback)}")
    lines.append("=" * 60)
    lines.append("")

    for idx, row in enumerate(feedback, 1):
        lines.append("-" * 60)
        lines.append(f"FEEDBACK #{idx}")
        lines.append("-" * 60)
        lines.append(f"ID: {row['id']}")
        lines.append(f"Submitted: {row['created_at']}")
        lines.append("")
        lines.append("ENTRY TEXT:")
        lines.append(row["entry_text"] or "(empty)")
        lines.append("")

        analysis = row.get("analysis_json") or {}
        if analysis:
            results = analysis.get("results", {})
            dominant = results.get("dominant", {})
            current = results.get("current", {})

            dom_label = (
                dominant.get("labelLocalized")
                or dominant.get("nuancedLabel")
                or dominant.get("label")
                or "N/A"
            )
            cur_label = (
                current.get("labelLocalized")
                or current.get("nuancedLabel")
                or current.get("label")
                or "N/A"
            )

            lines.append("ANALYSIS SUMMARY:")
            lines.append(f"  Dominant: {dom_label}")
            lines.append(f"  Current: {cur_label}")

            core_mix = analysis.get("coreMixture", [])
            if core_mix:
                lines.append("  Core Mixture:")
                for em in core_mix:
                    if em.get("percent", 0) > 0:
                        lines.append(
                            f"    - {em.get('label', em.get('id', 'Unknown'))}: "
                            f"{em.get('percent', 0):.1f}%"
                        )
            lines.append("")

        lines.append("USER FEEDBACK:")
        lines.append(row["feedback_text"] or "(empty)")
        lines.append("")
        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF FEEDBACK DOCUMENT")
    lines.append("=" * 60)

    document_content = "\n".join(lines)

    return Response(
        document_content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=feedback_document.txt"},
    )


@admin_bp.route("/feedback/delete", methods=["DELETE"])
@require_admin
def delete_all_feedback():
    """Delete all feedback entries after download."""
    feedback_repo = FeedbackRepository()
    audit_repo = AuditRepository()

    count = feedback_repo.delete_all_feedback()

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="delete_all",
        resource_type="feedback",
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
        metadata={"deleted_count": count},
    )

    return api_response(data={"deleted_count": count})


@admin_bp.route("/audit-log", methods=["GET"])
@require_admin
def get_audit_log():
    """Get audit log entries."""
    audit_repo = AuditRepository()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action = request.args.get("action")
    resource_type = request.args.get("resource_type")

    page = max(1, min(page, 1000))
    per_page = max(1, min(per_page, 100))

    logs = audit_repo.get_logs(
        action=action,
        resource_type=resource_type,
        limit=per_page,
        offset=(page - 1) * per_page,
    )

    return api_response(data={"logs": logs})


@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    """List all users (admin only)."""
    user_repo = UserRepository()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    page = max(1, min(page, 1000))
    per_page = max(1, min(per_page, 100))

    users, total, total_pages = user_repo.paginate(
        page=page,
        per_page=per_page,
        order_by="created_at",
        order_dir="DESC",
    )

    # Convert to safe payloads
    safe_users = [UserRepository.to_safe_payload(u) for u in users]

    return paginated_response(
        items=safe_users,
        total=total,
        page=page,
        per_page=per_page,
    )


@admin_bp.route("/users/<int:user_id>/disable", methods=["POST"])
@require_admin
def disable_user(user_id: int):
    """Disable a user account."""
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "")

    user_repo = UserRepository()
    audit_repo = AuditRepository()

    success = user_repo.disable_user(user_id, reason)

    if not success:
        raise NotFoundError("User not found")

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="disable_user",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
        metadata={"reason": reason},
    )

    return api_response(message="User disabled successfully")


@admin_bp.route("/users/<int:user_id>/enable", methods=["POST"])
@require_admin
def enable_user(user_id: int):
    """Enable a disabled user account."""
    user_repo = UserRepository()
    audit_repo = AuditRepository()

    success = user_repo.enable_user(user_id)

    if not success:
        raise NotFoundError("User not found")

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="enable_user",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="User enabled successfully")


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def get_admin_stats():
    """Get admin dashboard statistics."""
    user_repo = UserRepository()
    feedback_repo = FeedbackRepository()

    user_stats = user_repo.get_user_stats()
    feedback_stats = feedback_repo.get_feedback_stats()

    return api_response(
        data={
            "users": user_stats,
            "feedback": feedback_stats,
        }
    )
