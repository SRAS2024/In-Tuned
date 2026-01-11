# app/blueprints/users.py
"""
Users Blueprint

Handles user management for authenticated users:
- Update profile
- Change email
- Delete account
"""

from __future__ import annotations

from flask import Blueprint, request, session, g

from app.db.repositories.user_repository import UserRepository
from app.db.repositories.journal_repository import JournalRepository
from app.db.repositories.audit_repository import AuditRepository
from app.utils.responses import api_response
from app.utils.validation import ValidationSchema, text_field, email_field, password_field
from app.utils.security import require_login, get_client_ip
from app.utils.errors import ValidationError, NotFoundError, ConflictError

users_bp = Blueprint("users", __name__)


# Validation schemas
UPDATE_PROFILE_SCHEMA = ValidationSchema(
    fields=[
        text_field("first_name", required=False, max_length=50),
        text_field("last_name", required=False, max_length=50),
    ]
)

CHANGE_EMAIL_SCHEMA = ValidationSchema(
    fields=[
        email_field("new_email"),
        password_field("password"),  # Require password to change email
    ]
)

DELETE_ACCOUNT_SCHEMA = ValidationSchema(
    fields=[
        password_field("password"),  # Require password to delete account
        text_field("confirmation", max_length=50),  # Must type "DELETE"
    ]
)


@users_bp.route("/profile", methods=["GET"])
@require_login
def get_profile():
    """Get the current user's profile."""
    user_repo = UserRepository()

    user = user_repo.find_by_id(g.user_id)
    if not user:
        raise NotFoundError("User not found")

    return api_response(data={"user": UserRepository.to_safe_payload(user)})


@users_bp.route("/profile", methods=["PUT"])
@require_login
def update_profile():
    """Update the current user's profile."""
    data = request.get_json(silent=True) or {}
    validated = UPDATE_PROFILE_SCHEMA.validate(data)

    user_repo = UserRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id

    # Get current state for audit
    old_user = user_repo.find_by_id(user_id)
    if not old_user:
        raise NotFoundError("User not found")

    # Build update data
    update_data = {}
    if validated.get("first_name"):
        update_data["first_name"] = validated["first_name"]
    if validated.get("last_name"):
        update_data["last_name"] = validated["last_name"]

    if not update_data:
        return api_response(data={"user": UserRepository.to_safe_payload(old_user)})

    user = user_repo.update(user_id, update_data)

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="update_profile",
        resource_type="user",
        resource_id=str(user_id),
        before_state={
            "first_name": old_user.get("first_name"),
            "last_name": old_user.get("last_name"),
        },
        after_state={
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
        },
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"user": UserRepository.to_safe_payload(user)})


@users_bp.route("/email", methods=["PUT"])
@require_login
def change_email():
    """Change the current user's email address."""
    data = request.get_json(silent=True) or {}
    validated = CHANGE_EMAIL_SCHEMA.validate(data)

    user_repo = UserRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id
    user = user_repo.find_by_id(user_id)

    if not user:
        raise NotFoundError("User not found")

    # Verify password
    if not user_repo.verify_password(user, validated["password"]):
        raise ValidationError(
            message="Password is incorrect",
            field="password",
        )

    new_email = validated["new_email"]

    # Check if email is already in use
    existing = user_repo.find_by_email(new_email)
    if existing and existing["id"] != user_id:
        raise ConflictError(
            message="Email address is already in use",
            field="new_email",
        )

    old_email = user.get("email")

    updated_user = user_repo.update_email(user_id, new_email)

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="change_email",
        resource_type="user",
        resource_id=str(user_id),
        before_state={"email": old_email},
        after_state={"email": new_email},
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(
        data={"user": UserRepository.to_safe_payload(updated_user)},
        message="Email updated successfully",
    )


@users_bp.route("/account", methods=["DELETE"])
@require_login
def delete_account():
    """Delete the current user's account."""
    data = request.get_json(silent=True) or {}
    validated = DELETE_ACCOUNT_SCHEMA.validate(data)

    user_repo = UserRepository()
    journal_repo = JournalRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id
    user = user_repo.find_by_id(user_id)

    if not user:
        raise NotFoundError("User not found")

    # Verify password
    if not user_repo.verify_password(user, validated["password"]):
        raise ValidationError(
            message="Password is incorrect",
            field="password",
        )

    # Verify confirmation
    if validated["confirmation"].upper() != "DELETE":
        raise ValidationError(
            message="Please type DELETE to confirm account deletion",
            field="confirmation",
        )

    # Get counts for audit
    journal_count = journal_repo.count_by_user(user_id)

    # Delete user (journals will cascade due to foreign key)
    success = user_repo.delete(user_id)

    if not success:
        raise NotFoundError("User not found")

    # Clear session
    session.clear()

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="delete_account",
        resource_type="user",
        resource_id=str(user_id),
        before_state={
            "email": user.get("email"),
            "username": user.get("username"),
            "journal_count": journal_count,
        },
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="Account deleted successfully")


@users_bp.route("/stats", methods=["GET"])
@require_login
def get_user_stats():
    """Get statistics for the current user."""
    journal_repo = JournalRepository()

    stats = journal_repo.get_user_journal_stats(g.user_id)

    return api_response(data={"stats": stats})


@users_bp.route("/export", methods=["GET"])
@require_login
def export_user_data():
    """Export all user data (GDPR compliance)."""
    user_repo = UserRepository()
    journal_repo = JournalRepository()

    user_id = g.user_id

    user = user_repo.find_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")

    journals = journal_repo.export_journals(user_id, include_analysis=True)

    export_data = {
        "user": UserRepository.to_safe_payload(user),
        "journals": journals,
        "journal_count": len(journals),
        "exported_at": None,  # Will be set by client
    }

    return api_response(data=export_data)
