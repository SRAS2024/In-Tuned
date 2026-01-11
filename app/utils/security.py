# app/utils/security.py
"""
Security Utilities

This module provides security-related utilities including:
- Password strength validation
- Input sanitization
- Rate limiting helpers
- CSRF protection helpers
- Session management helpers
"""

from __future__ import annotations

import html
import re
import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from flask import current_app, g, request, session

from app.utils.errors import AuthenticationError, AuthorizationError, RateLimitError


@dataclass
class PasswordStrengthResult:
    """Result of password strength validation."""

    is_valid: bool
    score: int  # 0-5
    errors: List[str]
    suggestions: List[str]


def validate_password_strength(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = False,
) -> PasswordStrengthResult:
    """
    Validate password strength according to configured policy.

    Args:
        password: The password to validate
        min_length: Minimum required length
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digit: Require at least one digit
        require_special: Require at least one special character

    Returns:
        PasswordStrengthResult with validation details
    """
    errors = []
    suggestions = []
    score = 0

    # Length check
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    else:
        score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            suggestions.append("Great password length!")

    # Uppercase check
    if require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    elif re.search(r"[A-Z]", password):
        score += 1

    # Lowercase check
    if require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    elif re.search(r"[a-z]", password):
        score += 1

    # Digit check
    if require_digit and not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    elif re.search(r"\d", password):
        score += 1

    # Special character check
    special_chars = r"[!@#$%^&*(),.?\":{}|<>]"
    if require_special and not re.search(special_chars, password):
        errors.append("Password must contain at least one special character")
    elif re.search(special_chars, password):
        score += 1

    # Common password patterns (basic check)
    common_patterns = [
        r"^password",
        r"^123456",
        r"^qwerty",
        r"^admin",
        r"^letmein",
        r"^welcome",
        r"^monkey",
        r"^dragon",
        r"^master",
    ]

    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password is too common. Please choose a more unique password.")
            score = max(0, score - 2)
            break

    # Add suggestions if score is low
    if score < 3:
        if len(password) < 12:
            suggestions.append("Consider using a longer password (12+ characters)")
        if not re.search(special_chars, password):
            suggestions.append("Adding special characters would make the password stronger")

    return PasswordStrengthResult(
        is_valid=len(errors) == 0,
        score=min(5, score),
        errors=errors,
        suggestions=suggestions,
    )


def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent XSS and other injection attacks.

    Args:
        value: The input string to sanitize
        max_length: Optional maximum length to truncate to

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # HTML escape to prevent XSS
    sanitized = html.escape(value, quote=True)

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Normalize whitespace
    sanitized = " ".join(sanitized.split())

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.

    Args:
        filename: The original filename

    Returns:
        Safe filename with only allowed characters
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Allow only alphanumeric, dash, underscore, and dot
    safe_chars = set(string.ascii_letters + string.digits + "-_.")
    sanitized = "".join(c if c in safe_chars else "_" for c in filename)

    # Prevent double dots (path traversal)
    while ".." in sanitized:
        sanitized = sanitized.replace("..", ".")

    # Ensure it doesn't start with a dot
    if sanitized.startswith("."):
        sanitized = "_" + sanitized[1:]

    return sanitized or "unnamed"


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_hex(length // 2)


def generate_csrf_token() -> str:
    """Generate a CSRF token and store it in the session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = generate_token()
    return session["_csrf_token"]


def verify_csrf_token(token: str) -> bool:
    """Verify a CSRF token against the session token."""
    session_token = session.get("_csrf_token")
    if not session_token or not token:
        return False
    return secrets.compare_digest(session_token, token)


def require_login(func: Callable) -> Callable:
    """
    Decorator that requires user authentication.

    Usage:
        @require_login
        def my_protected_endpoint():
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            raise AuthenticationError("Authentication required")
        g.user_id = user_id
        return func(*args, **kwargs)

    return wrapper


def require_admin(func: Callable) -> Callable:
    """
    Decorator that requires admin authentication.

    Usage:
        @require_admin
        def my_admin_endpoint():
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            raise AuthorizationError(
                "Admin authorization required",
                error_code="ADMIN_REQUIRED",
            )
        return func(*args, **kwargs)

    return wrapper


def get_client_ip() -> str:
    """Get the client's IP address, handling proxies."""
    # Check for X-Forwarded-For header (when behind a proxy)
    if request.headers.get("X-Forwarded-For"):
        # Take the first IP in the chain
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()

    # Check for X-Real-IP header
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")

    # Fall back to remote_addr
    return request.remote_addr or "unknown"


def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    storage: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, int]:
    """
    Check if a rate limit has been exceeded.

    This is a simple in-memory implementation. For production,
    use Redis-based rate limiting via flask-limiter.

    Args:
        key: Unique key for the rate limit (e.g., "login:192.168.1.1")
        limit: Maximum number of requests allowed
        window_seconds: Time window in seconds
        storage: Optional dictionary for storing rate limit data

    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    # In-memory storage for simple cases
    if storage is None:
        if not hasattr(g, "_rate_limit_storage"):
            g._rate_limit_storage = {}
        storage = g._rate_limit_storage

    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    # Get or initialize the request history for this key
    if key not in storage:
        storage[key] = []

    # Remove expired entries
    storage[key] = [t for t in storage[key] if t > window_start]

    # Check limit
    current_count = len(storage[key])
    if current_count >= limit:
        return False, 0

    # Add current request
    storage[key].append(now)

    return True, limit - current_count - 1


def rate_limit(
    limit: int = 10,
    window_seconds: int = 60,
    key_func: Optional[Callable[[], str]] = None,
) -> Callable:
    """
    Decorator for rate limiting endpoints.

    Usage:
        @rate_limit(limit=5, window_seconds=60)
        def my_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func()
            else:
                key = f"{func.__name__}:{get_client_ip()}"

            is_allowed, remaining = check_rate_limit(key, limit, window_seconds)

            if not is_allowed:
                raise RateLimitError(
                    message="Too many requests. Please try again later.",
                    retry_after=window_seconds,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# RBAC (Role-Based Access Control)

class Permission:
    """Permission constants for RBAC."""

    # User permissions
    READ_OWN_PROFILE = "read:own_profile"
    UPDATE_OWN_PROFILE = "update:own_profile"
    DELETE_OWN_ACCOUNT = "delete:own_account"

    # Journal permissions
    CREATE_JOURNAL = "create:journal"
    READ_OWN_JOURNALS = "read:own_journals"
    UPDATE_OWN_JOURNALS = "update:own_journals"
    DELETE_OWN_JOURNALS = "delete:own_journals"

    # Analysis permissions
    USE_DETECTOR = "use:detector"
    SUBMIT_FEEDBACK = "submit:feedback"

    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_SITE = "manage:site"
    MANAGE_LEXICON = "manage:lexicon"
    VIEW_FEEDBACK = "view:feedback"
    VIEW_AUDIT_LOG = "view:audit_log"
    MAINTENANCE_MODE = "manage:maintenance"


# Role definitions
ROLES: Dict[str, Set[str]] = {
    "user": {
        Permission.READ_OWN_PROFILE,
        Permission.UPDATE_OWN_PROFILE,
        Permission.DELETE_OWN_ACCOUNT,
        Permission.CREATE_JOURNAL,
        Permission.READ_OWN_JOURNALS,
        Permission.UPDATE_OWN_JOURNALS,
        Permission.DELETE_OWN_JOURNALS,
        Permission.USE_DETECTOR,
        Permission.SUBMIT_FEEDBACK,
    },
    "admin": {
        # All user permissions
        Permission.READ_OWN_PROFILE,
        Permission.UPDATE_OWN_PROFILE,
        Permission.DELETE_OWN_ACCOUNT,
        Permission.CREATE_JOURNAL,
        Permission.READ_OWN_JOURNALS,
        Permission.UPDATE_OWN_JOURNALS,
        Permission.DELETE_OWN_JOURNALS,
        Permission.USE_DETECTOR,
        Permission.SUBMIT_FEEDBACK,
        # Admin-only permissions
        Permission.MANAGE_USERS,
        Permission.MANAGE_SITE,
        Permission.MANAGE_LEXICON,
        Permission.VIEW_FEEDBACK,
        Permission.VIEW_AUDIT_LOG,
        Permission.MAINTENANCE_MODE,
    },
}


def has_permission(permission: str, role: str = "user") -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLES.get(role, set())


def require_permission(permission: str) -> Callable:
    """
    Decorator that requires a specific permission.

    Usage:
        @require_permission(Permission.MANAGE_USERS)
        def admin_only_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user role from session or request
            role = "admin" if session.get("is_admin") else "user"

            if not has_permission(permission, role):
                raise AuthorizationError(
                    f"Permission denied: {permission}",
                    error_code="PERMISSION_DENIED",
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
