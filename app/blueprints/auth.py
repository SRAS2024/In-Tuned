# app/blueprints/auth.py
"""
Authentication Blueprint

Handles user authentication including:
- Registration
- Login/Logout
- Password reset
- Session management
- User preferences
"""

from __future__ import annotations

from flask import Blueprint, request, session, g, current_app

from app.db.repositories.user_repository import UserRepository
from app.db.repositories.audit_repository import AuditRepository
from app.utils.responses import api_response, api_error
from app.utils.validation import (
    validate_request,
    LOGIN_SCHEMA,
    REGISTER_SCHEMA,
    UPDATE_PREFERENCES_SCHEMA,
    PASSWORD_RESET_SCHEMA,
    ValidationSchema,
    password_field,
)
from app.utils.security import (
    require_login,
    get_client_ip,
    validate_password_strength,
    rate_limit,
)
from app.utils.errors import (
    ValidationError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@rate_limit(limit=3, window_seconds=60)
@validate_request(REGISTER_SCHEMA)
def register(validated_data: dict):
    """Register a new user account."""
    user_repo = UserRepository()
    audit_repo = AuditRepository()

    # Validate password strength
    password_result = validate_password_strength(
        validated_data["password"],
        min_length=current_app.config.get("PASSWORD_MIN_LENGTH", 8),
        require_uppercase=current_app.config.get("PASSWORD_REQUIRE_UPPERCASE", True),
        require_lowercase=current_app.config.get("PASSWORD_REQUIRE_LOWERCASE", True),
        require_digit=current_app.config.get("PASSWORD_REQUIRE_DIGIT", True),
        require_special=current_app.config.get("PASSWORD_REQUIRE_SPECIAL", False),
    )

    if not password_result.is_valid:
        raise ValidationError(
            message=password_result.errors[0],
            field="password",
            details={"errors": password_result.errors},
        )

    # Check if user already exists
    if user_repo.email_or_username_exists(
        validated_data["email"],
        validated_data["username"],
    ):
        raise ConflictError(
            message="Username or email already in use",
        )

    # Create user
    user = user_repo.create_user(
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
        username=validated_data["username"],
        email=validated_data["email"],
        password=validated_data["password"],
    )

    # Log the user in
    session["user_id"] = user["id"]
    session.permanent = True

    # Audit log
    audit_repo.log_action(
        actor_id=user["id"],
        actor_type="user",
        action="register",
        resource_type="user",
        resource_id=str(user["id"]),
        after_state=UserRepository.to_safe_payload(user),
        ip_address=get_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(
        data={"user": UserRepository.to_safe_payload(user)},
        message="Registration successful",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
@rate_limit(limit=5, window_seconds=60)
@validate_request(LOGIN_SCHEMA)
def login(validated_data: dict):
    """Authenticate a user and create a session."""
    user_repo = UserRepository()
    audit_repo = AuditRepository()

    identifier = validated_data["identifier"]
    password = validated_data["password"]

    # Find user
    user = user_repo.find_by_identifier(identifier)

    if not user:
        # Log failed attempt
        audit_repo.log_action(
            actor_id=None,
            actor_type="anonymous",
            action="login_failed",
            resource_type="user",
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
            metadata={"reason": "user_not_found", "identifier": identifier[:3] + "***"},
        )
        raise AuthenticationError(
            message="Invalid credentials",
            error_code="INVALID_CREDENTIALS",
        )

    # Check if account is locked
    lockout_minutes = current_app.config.get("LOCKOUT_DURATION_MINUTES", 15)
    if user_repo.is_locked_out(user["id"], lockout_minutes):
        audit_repo.log_action(
            actor_id=user["id"],
            actor_type="user",
            action="login_blocked",
            resource_type="user",
            resource_id=str(user["id"]),
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
            metadata={"reason": "account_locked"},
        )
        raise AuthenticationError(
            message="Account temporarily locked due to too many failed attempts. Please try again later.",
            error_code="ACCOUNT_LOCKED",
        )

    # Check if account is disabled
    if not user.get("is_active", True):
        raise AuthenticationError(
            message="Account has been disabled",
            error_code="ACCOUNT_DISABLED",
        )

    # Verify password
    if not user_repo.verify_password(user, password):
        # Increment failed attempts
        attempts = user_repo.increment_failed_login(user["id"])

        audit_repo.log_action(
            actor_id=user["id"],
            actor_type="user",
            action="login_failed",
            resource_type="user",
            resource_id=str(user["id"]),
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
            metadata={"reason": "invalid_password", "attempts": attempts},
        )

        raise AuthenticationError(
            message="Invalid credentials",
            error_code="INVALID_CREDENTIALS",
        )

    # Reset failed login attempts
    user_repo.reset_failed_login(user["id"])

    # Create session
    session["user_id"] = user["id"]
    session.permanent = True

    # Audit log
    audit_repo.log_action(
        actor_id=user["id"],
        actor_type="user",
        action="login",
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=get_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(
        data={"user": UserRepository.to_safe_payload(user)},
        message="Login successful",
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """End the current user session."""
    user_id = session.get("user_id")

    if user_id:
        audit_repo = AuditRepository()
        audit_repo.log_action(
            actor_id=user_id,
            actor_type="user",
            action="logout",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
        )

    session.pop("user_id", None)
    session.pop("is_admin", None)

    return api_response(message="Logout successful")


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """Get the currently authenticated user."""
    user_id = session.get("user_id")

    if not user_id:
        return api_response(data={"user": None})

    user_repo = UserRepository()
    user = user_repo.find_by_id(user_id)

    if not user:
        session.pop("user_id", None)
        return api_response(data={"user": None})

    return api_response(data={"user": UserRepository.to_safe_payload(user)})


@auth_bp.route("/update-settings", methods=["POST"])
@require_login
@validate_request(UPDATE_PREFERENCES_SCHEMA)
def update_settings(validated_data: dict):
    """Update user preferences."""
    user_repo = UserRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id

    # Get current state for audit
    old_user = user_repo.find_by_id(user_id)

    user = user_repo.update_preferences(
        user_id=user_id,
        preferred_language=validated_data.get("preferred_language"),
        preferred_theme=validated_data.get("preferred_theme"),
    )

    if not user:
        raise NotFoundError("User not found")

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="update_preferences",
        resource_type="user",
        resource_id=str(user_id),
        before_state={
            "preferred_language": old_user.get("preferred_language"),
            "preferred_theme": old_user.get("preferred_theme"),
        },
        after_state={
            "preferred_language": user.get("preferred_language"),
            "preferred_theme": user.get("preferred_theme"),
        },
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"user": UserRepository.to_safe_payload(user)})


@auth_bp.route("/reset-password", methods=["POST"])
@rate_limit(limit=3, window_seconds=60)
@validate_request(PASSWORD_RESET_SCHEMA)
def reset_password(validated_data: dict):
    """Reset password using identity verification."""
    user_repo = UserRepository()
    audit_repo = AuditRepository()

    # Validate passwords match
    if validated_data["new_password"] != validated_data["confirm_password"]:
        raise ValidationError(
            message="Passwords do not match",
            field="confirm_password",
        )

    # Validate password strength
    password_result = validate_password_strength(
        validated_data["new_password"],
        min_length=current_app.config.get("PASSWORD_MIN_LENGTH", 8),
    )

    if not password_result.is_valid:
        raise ValidationError(
            message=password_result.errors[0],
            field="new_password",
        )

    # Find user by identity verification
    user = user_repo.find_by_identity_verification(
        email=validated_data["email"],
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
    )

    if not user:
        # Log attempt but don't reveal if user exists
        audit_repo.log_action(
            actor_id=None,
            actor_type="anonymous",
            action="password_reset_failed",
            resource_type="user",
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(g, "request_id", None),
            metadata={"reason": "identity_verification_failed"},
        )
        raise NotFoundError("User not found with provided details")

    # Update password
    user_repo.update_password(user["id"], validated_data["new_password"])

    # Audit log
    audit_repo.log_action(
        actor_id=user["id"],
        actor_type="user",
        action="password_reset",
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=get_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="Password reset successful")


@auth_bp.route("/change-password", methods=["POST"])
@require_login
@rate_limit(limit=3, window_seconds=60)
def change_password():
    """Change password for authenticated user."""
    schema = ValidationSchema(
        fields=[
            password_field("current_password"),
            password_field("new_password"),
            password_field("confirm_password"),
        ]
    )

    data = request.get_json(silent=True) or {}
    validated_data = schema.validate(data)

    user_repo = UserRepository()
    audit_repo = AuditRepository()

    user_id = g.user_id
    user = user_repo.find_by_id(user_id)

    if not user:
        raise NotFoundError("User not found")

    # Verify current password
    if not user_repo.verify_password(user, validated_data["current_password"]):
        raise ValidationError(
            message="Current password is incorrect",
            field="current_password",
        )

    # Validate passwords match
    if validated_data["new_password"] != validated_data["confirm_password"]:
        raise ValidationError(
            message="Passwords do not match",
            field="confirm_password",
        )

    # Validate new password strength
    password_result = validate_password_strength(validated_data["new_password"])
    if not password_result.is_valid:
        raise ValidationError(
            message=password_result.errors[0],
            field="new_password",
        )

    # Update password
    user_repo.update_password(user_id, validated_data["new_password"])

    # Audit log
    audit_repo.log_action(
        actor_id=user_id,
        actor_type="user",
        action="password_change",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=get_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="Password changed successfully")
