# app/utils/responses.py
"""
API Response Helpers

This module provides standardized API response formatting for consistent
success and error response shapes across all endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from flask import jsonify, Response


def api_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200,
    **kwargs: Any,
) -> Tuple[Response, int]:
    """
    Create a standardized success API response.

    Args:
        data: The response data (can be dict, list, or any JSON-serializable value)
        message: Optional success message
        status_code: HTTP status code (default: 200)
        **kwargs: Additional fields to include in the response

    Returns:
        Tuple of (Response, status_code)

    Example response:
        {
            "ok": true,
            "data": {...},
            "message": "Success"
        }
    """
    response = {"ok": True}

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    # Add any additional fields
    for key, value in kwargs.items():
        if key not in response:
            response[key] = value

    return jsonify(response), status_code


def api_error(
    message: str,
    code: str = "ERROR",
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Tuple[Response, int]:
    """
    Create a standardized error API response.

    Args:
        message: Error message
        code: Error code for client handling
        status_code: HTTP status code (default: 400)
        details: Additional error details
        **kwargs: Additional fields to include in the error

    Returns:
        Tuple of (Response, status_code)

    Example response:
        {
            "ok": false,
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Email is required",
                "details": {"field": "email"}
            }
        }
    """
    error = {
        "code": code,
        "message": message,
    }

    if details:
        error["details"] = details

    for key, value in kwargs.items():
        if key not in error:
            error[key] = value

    return jsonify({"ok": False, "error": error}), status_code


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    status_code: int = 200,
    **kwargs: Any,
) -> Tuple[Response, int]:
    """
    Create a standardized paginated response.

    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        per_page: Number of items per page
        status_code: HTTP status code (default: 200)
        **kwargs: Additional fields to include in the response

    Returns:
        Tuple of (Response, status_code)

    Example response:
        {
            "ok": true,
            "data": [...],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 100,
                "total_pages": 5,
                "has_next": true,
                "has_prev": false
            }
        }
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    response = {
        "ok": True,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }

    for key, value in kwargs.items():
        if key not in response:
            response[key] = value

    return jsonify(response), status_code


def created_response(
    data: Any,
    message: str = "Created successfully",
    location: Optional[str] = None,
) -> Tuple[Response, int]:
    """
    Create a standardized 201 Created response.

    Args:
        data: The created resource data
        message: Success message
        location: Optional URL of the created resource

    Returns:
        Tuple of (Response, 201)
    """
    response = {
        "ok": True,
        "data": data,
        "message": message,
    }

    resp = jsonify(response)

    if location:
        resp.headers["Location"] = location

    return resp, 201


def no_content_response() -> Tuple[str, int]:
    """
    Create a 204 No Content response.

    Returns:
        Tuple of ("", 204)
    """
    return "", 204


def accepted_response(
    message: str = "Request accepted for processing",
    task_id: Optional[str] = None,
) -> Tuple[Response, int]:
    """
    Create a 202 Accepted response for async operations.

    Args:
        message: Acceptance message
        task_id: Optional task ID for tracking

    Returns:
        Tuple of (Response, 202)
    """
    response = {
        "ok": True,
        "message": message,
    }

    if task_id:
        response["task_id"] = task_id

    return jsonify(response), 202


# Convenience functions for common status codes

def ok(data: Any = None, **kwargs) -> Tuple[Response, int]:
    """Return a 200 OK response."""
    return api_response(data=data, **kwargs)


def bad_request(message: str, code: str = "BAD_REQUEST", **kwargs) -> Tuple[Response, int]:
    """Return a 400 Bad Request response."""
    return api_error(message=message, code=code, status_code=400, **kwargs)


def unauthorized(message: str = "Authentication required", **kwargs) -> Tuple[Response, int]:
    """Return a 401 Unauthorized response."""
    return api_error(message=message, code="AUTH_REQUIRED", status_code=401, **kwargs)


def forbidden(message: str = "Permission denied", **kwargs) -> Tuple[Response, int]:
    """Return a 403 Forbidden response."""
    return api_error(message=message, code="PERMISSION_DENIED", status_code=403, **kwargs)


def not_found(message: str = "Resource not found", **kwargs) -> Tuple[Response, int]:
    """Return a 404 Not Found response."""
    return api_error(message=message, code="NOT_FOUND", status_code=404, **kwargs)


def conflict(message: str, **kwargs) -> Tuple[Response, int]:
    """Return a 409 Conflict response."""
    return api_error(message=message, code="CONFLICT", status_code=409, **kwargs)


def too_many_requests(message: str = "Rate limit exceeded", retry_after: Optional[int] = None) -> Tuple[Response, int]:
    """Return a 429 Too Many Requests response."""
    details = {"retry_after": retry_after} if retry_after else None
    return api_error(message=message, code="RATE_LIMITED", status_code=429, details=details)


def internal_error(message: str = "An internal error occurred") -> Tuple[Response, int]:
    """Return a 500 Internal Server Error response."""
    return api_error(message=message, code="INTERNAL_ERROR", status_code=500)
