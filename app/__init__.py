# app/__init__.py
"""
In-Tuned Application Package

This module provides the Flask application factory and initializes
all required components including database, extensions, and blueprints.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import Flask

from app.config import get_config
from app.extensions import init_extensions
from app.logging_config import setup_logging


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory for creating Flask app instances.

    Args:
        config_name: Configuration environment name (development, staging, production).
                    If None, uses APP_ENV environment variable or defaults to development.

    Returns:
        Configured Flask application instance.
    """
    # Load configuration
    config = get_config(config_name)

    # Create Flask app
    app = Flask(
        __name__,
        static_folder="../client",
        static_url_path="",
        template_folder="../templates",
    )

    # Apply configuration
    app.config.from_object(config)

    # Setup logging
    setup_logging(app)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_cli_commands(app)

    # Log startup
    app.logger.info(
        f"Application initialized in {config.ENV} mode",
        extra={"request_id": "startup"},
    )

    return app


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.entries import entries_bp
    from app.blueprints.detector import detector_bp
    from app.blueprints.lexicon import lexicon_bp
    from app.blueprints.feedback import feedback_bp
    from app.blueprints.site import site_bp
    from app.blueprints.users import users_bp
    from app.blueprints.analytics import bp as analytics_bp

    # API blueprints with /api prefix
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(entries_bp, url_prefix="/api/journals")
    app.register_blueprint(detector_bp, url_prefix="/api")
    app.register_blueprint(lexicon_bp, url_prefix="/api/admin/lexicons")
    app.register_blueprint(feedback_bp, url_prefix="/api/feedback")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(analytics_bp)

    # Site blueprint for static pages and site-state
    app.register_blueprint(site_bp)


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""
    from app.utils.errors import register_error_handlers as register_handlers

    register_handlers(app)


def register_cli_commands(app: Flask) -> None:
    """Register CLI commands."""
    from app.cli import register_commands

    register_commands(app)
