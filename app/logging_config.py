# app/logging_config.py
"""
Logging Configuration

This module sets up structured logging with support for JSON output,
request ID tracing, and automatic secret redaction.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from flask import Flask, g, has_request_context, request


# Patterns for secrets that should be redacted
SECRET_PATTERNS: List[re.Pattern] = [
    re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', re.IGNORECASE),
    re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', re.IGNORECASE),
    re.compile(r'secret["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', re.IGNORECASE),
    re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', re.IGNORECASE),
    re.compile(r'authorization["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', re.IGNORECASE),
    re.compile(r'bearer\s+[a-zA-Z0-9._-]+', re.IGNORECASE),
    re.compile(r'password_hash["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', re.IGNORECASE),
]

# Fields that should never be logged
SENSITIVE_FIELDS: Set[str] = {
    "password",
    "password_hash",
    "secret_key",
    "api_key",
    "token",
    "authorization",
    "cookie",
    "session",
    "credit_card",
    "ssn",
    "social_security",
}


def redact_secrets(message: str) -> str:
    """Redact secrets from log messages."""
    for pattern in SECRET_PATTERNS:
        message = pattern.sub("[REDACTED]", message)
    return message


def redact_dict(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    """Recursively redact sensitive fields from a dictionary."""
    if depth > 10:  # Prevent infinite recursion
        return {"_redacted": "max_depth_exceeded"}

    result = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Check if key is sensitive
        if any(field in key_lower for field in SENSITIVE_FIELDS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item, depth + 1) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str):
            result[key] = redact_secrets(value)
        else:
            result[key] = value

    return result


class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
            record.remote_addr = request.remote_addr
            record.method = request.method
            record.path = request.path
        else:
            record.request_id = getattr(record, "request_id", "-")
            record.remote_addr = "-"
            record.method = "-"
            record.path = "-"
        return True


class SecretRedactionFilter(logging.Filter):
    """Redact secrets from log messages."""

    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled

    def filter(self, record: logging.LogRecord) -> bool:
        if self.enabled and record.msg:
            record.msg = redact_secrets(str(record.msg))
            if record.args:
                record.args = tuple(
                    redact_secrets(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        # Add request context if available
        if hasattr(record, "remote_addr") and record.remote_addr != "-":
            log_data["request"] = {
                "remote_addr": record.remote_addr,
                "method": record.method,
                "path": record.path,
            }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "message",
                "request_id",
                "remote_addr",
                "method",
                "path",
            }:
                if isinstance(value, dict):
                    log_data[key] = redact_dict(value)
                else:
                    log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text format for development."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", "-")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        base_msg = f"[{timestamp}] [{record.levelname}] [{request_id}] {record.getMessage()}"

        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)

        return base_msg


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper())
    log_format = app.config.get("LOG_FORMAT", "json")
    redact_secrets_enabled = app.config.get("LOG_REDACT_SECRETS", True)

    # Remove default handlers
    app.logger.handlers = []

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Add filters
    handler.addFilter(RequestIdFilter())
    handler.addFilter(SecretRedactionFilter(enabled=redact_secrets_enabled))

    # Set formatter based on environment
    if log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    # Add handler to app logger
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    # Also configure werkzeug logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(handler)
    werkzeug_logger.setLevel(log_level)

    # Configure psycopg logger to be less verbose
    psycopg_logger = logging.getLogger("psycopg")
    psycopg_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the standard configuration."""
    logger = logging.getLogger(name)
    return logger
