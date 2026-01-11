# app/blueprints/entries.py
"""
Journal Entries Blueprint

Handles journal entry CRUD operations:
- List entries
- Get single entry
- Create entry
- Update entry
- Delete entry
- Pin/unpin entry
"""

from __future__ import annotations

from flask import Blueprint, request, g

from app.db.repositories.journal_repository import JournalRepository
from app.db.repositories.audit_repository import AuditRepository
from app.utils.responses import api_response, paginated_response
from app.utils.validation import (
    validate_request,
    CREATE_JOURNAL_SCHEMA,
    UPDATE_JOURNAL_SCHEMA,
    ValidationSchema,
    boolean_field,
    integer_field,
    text_field,
)
from app.utils.security import require_login, get_client_ip
from app.utils.errors import NotFoundError, ValidationError
from app.services.detector_service import detect_self_harm_flag

entries_bp = Blueprint("entries", __name__)


# Pagination schema
PAGINATION_SCHEMA = ValidationSchema(
    fields=[
        integer_field("page", required=False, min_value=1, max_value=10000),
        integer_field("per_page", required=False, min_value=1, max_value=100),
        text_field("search", required=False, max_length=200),
    ]
)


@entries_bp.route("", methods=["GET"])
@require_login
def list_journals():
    """List all journals for the authenticated user."""
    journal_repo = JournalRepository()

    # Parse query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "", type=str).strip()

    # Validate pagination
    page = max(1, min(page, 10000))
    per_page = max(1, min(per_page, 100))

    user_id = g.user_id

    if search:
        # Search journals
        journals = journal_repo.search_journals(
            user_id=user_id,
            search_term=search,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        # For search, we don't have exact total count, estimate
        total = len(journals) if len(journals) < per_page else per_page * 2
    else:
        # List all journals
        journals = journal_repo.find_by_user(
            user_id=user_id,
            limit=per_page,
            offset=(page - 1) * per_page,
            include_content=False,
        )
        total = journal_repo.count_by_user(user_id)

    return paginated_response(
        items=journals,
        total=total,
        page=page,
        per_page=per_page,
    )


@entries_bp.route("/<int:journal_id>", methods=["GET"])
@require_login
def get_journal(journal_id: int):
    """Get a specific journal entry."""
    journal_repo = JournalRepository()

    journal = journal_repo.find_by_user_and_id(g.user_id, journal_id)

    if not journal:
        raise NotFoundError("Journal not found", resource_type="journal")

    return api_response(data={"journal": journal})


@entries_bp.route("", methods=["POST"])
@require_login
@validate_request(CREATE_JOURNAL_SCHEMA)
def create_journal(validated_data: dict):
    """Create a new journal entry."""
    journal_repo = JournalRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id

    # Check for self-harm keywords
    source_text = validated_data.get("source_text", "")
    journal_text = validated_data.get("journal_text", "")
    has_flag = detect_self_harm_flag(source_text) or detect_self_harm_flag(journal_text)

    journal = journal_repo.create_journal(
        user_id=user_id,
        title=validated_data["title"],
        source_text=source_text,
        analysis_json=validated_data.get("analysis_json"),
        journal_text=journal_text,
        has_self_harm_flag=has_flag,
    )

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="create",
        resource_type="journal",
        resource_id=str(journal["id"]),
        after_state={"title": journal["title"], "has_self_harm_flag": has_flag},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(
        data={"journal": journal},
        message="Journal created successfully",
        status_code=201,
    )


@entries_bp.route("/<int:journal_id>", methods=["PUT"])
@require_login
@validate_request(UPDATE_JOURNAL_SCHEMA)
def update_journal(journal_id: int, validated_data: dict):
    """Update a journal entry."""
    journal_repo = JournalRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id

    # Get current state for audit
    old_journal = journal_repo.find_by_user_and_id(user_id, journal_id)
    if not old_journal:
        raise NotFoundError("Journal not found", resource_type="journal")

    # Check for self-harm keywords in updated content
    journal_text = validated_data.get("journal_text")
    has_flag = None
    if journal_text is not None:
        has_flag = detect_self_harm_flag(journal_text)

    journal = journal_repo.update_journal(
        user_id=user_id,
        journal_id=journal_id,
        title=validated_data.get("title"),
        journal_text=journal_text,
        has_self_harm_flag=has_flag,
    )

    if not journal:
        raise NotFoundError("Journal not found", resource_type="journal")

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="update",
        resource_type="journal",
        resource_id=str(journal_id),
        before_state={"title": old_journal.get("title")},
        after_state={"title": journal.get("title")},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"journal": journal})


@entries_bp.route("/<int:journal_id>", methods=["DELETE"])
@require_login
def delete_journal(journal_id: int):
    """Delete a journal entry."""
    journal_repo = JournalRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id

    # Get journal for audit before deletion
    old_journal = journal_repo.find_by_user_and_id(user_id, journal_id)
    if not old_journal:
        raise NotFoundError("Journal not found", resource_type="journal")

    success = journal_repo.delete_journal(user_id, journal_id)

    if not success:
        raise NotFoundError("Journal not found", resource_type="journal")

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="delete",
        resource_type="journal",
        resource_id=str(journal_id),
        before_state={"title": old_journal.get("title")},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="Journal deleted successfully")


@entries_bp.route("/<int:journal_id>/pin", methods=["POST"])
@require_login
def pin_journal(journal_id: int):
    """Toggle the pinned status of a journal entry."""
    schema = ValidationSchema(
        fields=[
            boolean_field("is_pinned", required=False, default=True),
        ]
    )

    data = request.get_json(silent=True) or {}
    validated_data = schema.validate(data)

    journal_repo = JournalRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id
    is_pinned = validated_data.get("is_pinned", True)

    # Get current state
    old_journal = journal_repo.find_by_user_and_id(user_id, journal_id)
    if not old_journal:
        raise NotFoundError("Journal not found", resource_type="journal")

    journal = journal_repo.toggle_pin(user_id, journal_id, is_pinned)

    if not journal:
        raise NotFoundError("Journal not found", resource_type="journal")

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="pin" if is_pinned else "unpin",
        resource_type="journal",
        resource_id=str(journal_id),
        before_state={"is_pinned": old_journal.get("is_pinned")},
        after_state={"is_pinned": is_pinned},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"journal": journal})


@entries_bp.route("/stats", methods=["GET"])
@require_login
def get_journal_stats():
    """Get journal statistics for the authenticated user."""
    journal_repo = JournalRepository()

    stats = journal_repo.get_user_journal_stats(g.user_id)

    return api_response(data={"stats": stats})


@entries_bp.route("/export", methods=["GET"])
@require_login
def export_journals():
    """Export all journals for the authenticated user."""
    journal_repo = JournalRepository()

    include_analysis = request.args.get("include_analysis", "true").lower() == "true"

    journals = journal_repo.export_journals(
        user_id=g.user_id,
        include_analysis=include_analysis,
    )

    return api_response(
        data={
            "journals": journals,
            "count": len(journals),
            "exported_at": None,  # Will be set by client
        }
    )
