# app/extensions.py
"""
Flask Extensions Initialization

This module initializes and configures all Flask extensions used by the application.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Flask, g, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    import psycopg

# CSRF Protection
csrf = CSRFProtect()


def init_extensions(app: Flask) -> None:
    """Initialize all Flask extensions."""
    # Initialize CSRF protection
    csrf.init_app(app)

    # Register database connection management
    init_db_connection(app)

    # Register request hooks
    register_request_hooks(app)

    # Initialize rate limiting
    init_rate_limiting(app)

    # Initialize caching
    init_caching(app)


def init_db_connection(app: Flask) -> None:
    """Initialize database connection management."""
    from app.db.connection import get_db_connection, close_db_connection

    @app.before_request
    def before_request() -> None:
        """Open database connection before each request."""
        g.db = None  # Will be lazily initialized

    @app.teardown_appcontext
    def teardown_db(exception: BaseException | None = None) -> None:
        """Close database connection after each request."""
        close_db_connection()


def get_db() -> "psycopg.Connection":
    """Get the database connection for the current request."""
    from app.db.connection import get_db_connection

    if not hasattr(g, "db") or g.db is None:
        g.db = get_db_connection()
    return g.db


# Proxy for database connection
db = LocalProxy(get_db)


def register_request_hooks(app: Flask) -> None:
    """Register request lifecycle hooks."""
    import uuid

    @app.before_request
    def add_request_id() -> None:
        """Add unique request ID for tracing."""
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        # Add request ID to response
        response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")

        # Add security headers from config
        for header, value in app.config.get("SECURITY_HEADERS", {}).items():
            response.headers[header] = value

        # Add CSP header
        csp_policy = app.config.get("CSP_POLICY", {})
        if csp_policy:
            csp_parts = []
            for directive, sources in csp_policy.items():
                csp_parts.append(f"{directive} {' '.join(sources)}")
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

        return response


def init_rate_limiting(app: Flask) -> None:
    """Initialize rate limiting."""
    if not app.config.get("RATELIMIT_ENABLED", True):
        return

    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[app.config.get("RATELIMIT_DEFAULT", "200 per day")],
            storage_uri=app.config.get("RATELIMIT_STORAGE_URL", "memory://"),
            strategy=app.config.get("RATELIMIT_STRATEGY", "fixed-window"),
            headers_enabled=app.config.get("RATELIMIT_HEADERS_ENABLED", True),
        )

        # Store limiter on app for access in blueprints
        app.extensions["limiter"] = limiter

    except ImportError:
        app.logger.warning(
            "flask-limiter not installed. Rate limiting disabled.",
            extra={"request_id": "startup"},
        )


def init_caching(app: Flask) -> None:
    """Initialize caching."""
    try:
        from flask_caching import Cache

        cache = Cache(
            app,
            config={
                "CACHE_TYPE": app.config.get("CACHE_TYPE", "simple"),
                "CACHE_DEFAULT_TIMEOUT": app.config.get("CACHE_DEFAULT_TIMEOUT", 300),
                "CACHE_KEY_PREFIX": app.config.get("CACHE_KEY_PREFIX", "intuned_"),
            },
        )

        app.extensions["cache"] = cache

    except ImportError:
        app.logger.warning(
            "flask-caching not installed. Caching disabled.",
            extra={"request_id": "startup"},
        )


def get_limiter(app: Flask):
    """Get the rate limiter instance."""
    return app.extensions.get("limiter")


def get_cache(app: Flask):
    """Get the cache instance."""
    return app.extensions.get("cache")
