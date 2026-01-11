# app/utils/errors.py
"""
Error Handling

This module provides centralized error handling with structured error codes
and safe error messages for API responses.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Flask, jsonify, request, g


# Error codes for consistent API responses
class ErrorCode:
    """Standard error codes for API responses."""

    # Authentication errors (1xxx)
    AUTH_REQUIRED = "AUTH_001"
    INVALID_CREDENTIALS = "AUTH_002"
    SESSION_EXPIRED = "AUTH_003"
    ACCOUNT_LOCKED = "AUTH_004"
    ACCOUNT_DISABLED = "AUTH_005"

    # Authorization errors (2xxx)
    PERMISSION_DENIED = "AUTHZ_001"
    ADMIN_REQUIRED = "AUTHZ_002"
    RESOURCE_NOT_OWNED = "AUTHZ_003"

    # Validation errors (3xxx)
    VALIDATION_FAILED = "VAL_001"
    INVALID_INPUT = "VAL_002"
    MISSING_FIELD = "VAL_003"
    INVALID_FORMAT = "VAL_004"
    VALUE_TOO_LONG = "VAL_005"
    VALUE_TOO_SHORT = "VAL_006"
    INVALID_EMAIL = "VAL_007"
    WEAK_PASSWORD = "VAL_008"

    # Resource errors (4xxx)
    NOT_FOUND = "RES_001"
    ALREADY_EXISTS = "RES_002"
    CONFLICT = "RES_003"

    # Rate limiting errors (5xxx)
    RATE_LIMITED = "RATE_001"
    TOO_MANY_REQUESTS = "RATE_002"

    # Server errors (9xxx)
    INTERNAL_ERROR = "SRV_001"
    DATABASE_ERROR = "SRV_002"
    SERVICE_UNAVAILABLE = "SRV_003"


class APIError(Exception):
    """
    Base exception for API errors.

    Provides a consistent structure for error responses including:
    - HTTP status code
    - Error code for client handling
    - Human-readable message
    - Optional details for debugging
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = ErrorCode.VALIDATION_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        response = {
            "ok": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
            },
        }

        if self.details:
            response["error"]["details"] = self.details

        return response


class ValidationError(APIError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            status_code=400,
            error_code=ErrorCode.VALIDATION_FAILED,
            details=error_details,
        )


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = ErrorCode.AUTH_REQUIRED,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
        )


class AuthorizationError(APIError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str = ErrorCode.PERMISSION_DENIED,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
        )


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type

        super().__init__(
            message=message,
            status_code=404,
            error_code=ErrorCode.NOT_FOUND,
            details=details,
        )


class ConflictError(APIError):
    """Raised when there's a resource conflict (e.g., duplicate)."""

    def __init__(
        self,
        message: str = "Resource already exists",
        field: Optional[str] = None,
    ):
        details = {}
        if field:
            details["field"] = field

        super().__init__(
            message=message,
            status_code=409,
            error_code=ErrorCode.ALREADY_EXISTS,
            details=details,
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            status_code=429,
            error_code=ErrorCode.RATE_LIMITED,
            details=details,
        )


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application."""

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle custom API errors."""
        app.logger.warning(
            f"API Error: {error.error_code} - {error.message}",
            extra={
                "request_id": getattr(g, "request_id", "unknown"),
                "error_code": error.error_code,
                "status_code": error.status_code,
            },
        )
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "ok": False,
            "error": {
                "code": ErrorCode.INVALID_INPUT,
                "message": "Bad request",
            },
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            "ok": False,
            "error": {
                "code": ErrorCode.AUTH_REQUIRED,
                "message": "Authentication required",
            },
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            "ok": False,
            "error": {
                "code": ErrorCode.PERMISSION_DENIED,
                "message": "Permission denied",
            },
        }), 403

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        # Check if this is an API request
        if request.path.startswith("/api/"):
            return jsonify({
                "ok": False,
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": "Resource not found",
                },
            }), 404

        # For non-API requests, serve the SPA
        return app.send_static_file("index.html")

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            "ok": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": f"Method {request.method} not allowed",
            },
        }), 405

    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        """Handle 413 Request Entity Too Large errors."""
        return jsonify({
            "ok": False,
            "error": {
                "code": "PAYLOAD_TOO_LARGE",
                "message": "Request payload is too large",
            },
        }), 413

    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle 429 Too Many Requests errors."""
        return jsonify({
            "ok": False,
            "error": {
                "code": ErrorCode.RATE_LIMITED,
                "message": "Too many requests. Please try again later.",
            },
        }), 429

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(
            f"Internal Server Error: {str(error)}",
            extra={
                "request_id": getattr(g, "request_id", "unknown"),
                "path": request.path,
                "method": request.method,
            },
            exc_info=True,
        )

        return jsonify({
            "ok": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An internal error occurred",
            },
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        app.logger.error(
            f"Unexpected Error: {type(error).__name__}: {str(error)}",
            extra={
                "request_id": getattr(g, "request_id", "unknown"),
                "path": request.path,
                "method": request.method,
                "error_type": type(error).__name__,
            },
            exc_info=True,
        )

        # Don't expose internal error details in production
        return jsonify({
            "ok": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An unexpected error occurred",
            },
        }), 500
