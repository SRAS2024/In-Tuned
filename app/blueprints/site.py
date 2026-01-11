# app/blueprints/site.py
"""
Site Blueprint

Handles site-wide functionality:
- Static pages (index, admin)
- Site state (maintenance mode, notices)
- Health checks
"""

from __future__ import annotations

from flask import Blueprint, current_app, g

from app.db.repositories.site_repository import SiteRepository
from app.db.connection import check_database_health
from app.utils.responses import api_response

site_bp = Blueprint("site", __name__)


@site_bp.route("/")
def index():
    """Serve the main app shell."""
    return current_app.send_static_file("index.html")


@site_bp.route("/admin")
def admin_index():
    """Serve the administrative portal shell."""
    return current_app.send_static_file("admin.html")


@site_bp.route("/api/site-state", methods=["GET"])
def get_site_state():
    """
    Public endpoint for the client to know whether the site is in maintenance
    mode and what message or notice should be shown.

    Returns:
        {
            "maintenance_mode": bool,
            "maintenance_message": string or null,
            "notice": { "id": int, "text": string } or null
        }
    """
    site_repo = SiteRepository()
    state = site_repo.get_site_state()

    return api_response(data=state)


@site_bp.route("/api/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        {
            "status": "healthy" | "unhealthy",
            "database": "connected" | "disconnected",
            "version": "x.x.x"
        }
    """
    db_healthy = check_database_health()

    status = "healthy" if db_healthy else "unhealthy"

    return api_response(
        data={
            "status": status,
            "database": "connected" if db_healthy else "disconnected",
            "version": current_app.config.get("APP_VERSION", "unknown"),
        },
        status_code=200 if db_healthy else 503,
    )


@site_bp.route("/api/version", methods=["GET"])
def get_version():
    """Get API version information."""
    return api_response(
        data={
            "name": current_app.config.get("APP_NAME", "In-Tuned"),
            "version": current_app.config.get("APP_VERSION", "2.0.0"),
            "environment": current_app.config.get("ENV", "unknown"),
        }
    )
