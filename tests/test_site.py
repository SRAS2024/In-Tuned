# tests/test_site.py
"""
Site Tests

Tests for site state, health checks, and static pages.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient


class TestSiteState:
    """Tests for site state endpoint."""

    def test_get_site_state(self, client: FlaskClient):
        """Test getting site state."""
        response = client.get("/api/site-state")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert "maintenance_mode" in data["data"]
        assert "notice" in data["data"]


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client: FlaskClient):
        """Test health check returns healthy status."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["status"] == "healthy"
        assert "database" in data["data"]
        assert "version" in data["data"]


class TestVersion:
    """Tests for version endpoint."""

    def test_get_version(self, client: FlaskClient):
        """Test getting API version info."""
        response = client.get("/api/version")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert "name" in data["data"]
        assert "version" in data["data"]
        assert "environment" in data["data"]


class TestStaticPages:
    """Tests for static pages."""

    def test_index_page(self, client: FlaskClient):
        """Test that index page is served."""
        response = client.get("/")

        # Should return HTML content
        assert response.status_code == 200

    def test_admin_page(self, client: FlaskClient):
        """Test that admin page is served."""
        response = client.get("/admin")

        # Should return HTML content
        assert response.status_code == 200
