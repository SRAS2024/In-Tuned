# tests/test_auth.py
"""
Authentication Tests

Tests for user registration, login, logout, and password management.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient


class TestRegistration:
    """Tests for user registration."""

    def test_register_success(self, client: FlaskClient):
        """Test successful registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["ok"] is True
        assert "user" in data["data"]
        assert data["data"]["user"]["username"] == "johndoe"
        assert data["data"]["user"]["email"] == "john@example.com"
        # Password hash should not be returned
        assert "password_hash" not in data["data"]["user"]

    def test_register_missing_fields(self, client: FlaskClient):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                # Missing other fields
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["ok"] is False
        assert "error" in data

    def test_register_invalid_email(self, client: FlaskClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "invalid-email",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["ok"] is False

    def test_register_weak_password(self, client: FlaskClient):
        """Test registration with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "weak",  # Too short, no uppercase, no number
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["ok"] is False

    def test_register_duplicate_email(self, client: FlaskClient):
        """Test registration with duplicate email."""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
            },
        )

        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "email": "john@example.com",  # Same email
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 409
        data = response.get_json()
        assert data["ok"] is False


class TestLogin:
    """Tests for user login."""

    def test_login_success_with_email(self, client: FlaskClient):
        """Test successful login with email."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
            },
        )

        # Logout
        client.post("/api/auth/logout")

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "identifier": "john@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert "user" in data["data"]

    def test_login_success_with_username(self, client: FlaskClient):
        """Test successful login with username."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
            },
        )

        # Logout
        client.post("/api/auth/logout")

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "identifier": "johndoe",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_login_invalid_credentials(self, client: FlaskClient):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "identifier": "nonexistent@example.com",
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["ok"] is False

    def test_login_wrong_password(self, client: FlaskClient):
        """Test login with wrong password."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
            },
        )

        # Logout
        client.post("/api/auth/logout")

        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "identifier": "john@example.com",
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["ok"] is False


class TestLogout:
    """Tests for user logout."""

    def test_logout_success(self, auth_client: FlaskClient):
        """Test successful logout."""
        response = auth_client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_logout_not_logged_in(self, client: FlaskClient):
        """Test logout when not logged in."""
        response = client.post("/api/auth/logout")

        # Should still return success
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True


class TestCurrentUser:
    """Tests for getting current user."""

    def test_get_current_user_authenticated(self, auth_client: FlaskClient):
        """Test getting current user when authenticated."""
        response = auth_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert "user" in data["data"]
        assert data["data"]["user"] is not None

    def test_get_current_user_not_authenticated(self, client: FlaskClient):
        """Test getting current user when not authenticated."""
        response = client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["user"] is None


class TestUpdatePreferences:
    """Tests for updating user preferences."""

    def test_update_language(self, auth_client: FlaskClient):
        """Test updating preferred language."""
        response = auth_client.post(
            "/api/auth/update-settings",
            json={
                "preferred_language": "es",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["user"]["preferred_language"] == "es"

    def test_update_theme(self, auth_client: FlaskClient):
        """Test updating preferred theme."""
        response = auth_client.post(
            "/api/auth/update-settings",
            json={
                "preferred_theme": "light",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["user"]["preferred_theme"] == "light"

    def test_update_invalid_language(self, auth_client: FlaskClient):
        """Test updating with invalid language."""
        response = auth_client.post(
            "/api/auth/update-settings",
            json={
                "preferred_language": "invalid",
            },
        )

        assert response.status_code == 400

    def test_update_unauthenticated(self, client: FlaskClient):
        """Test updating preferences when not authenticated."""
        response = client.post(
            "/api/auth/update-settings",
            json={
                "preferred_language": "es",
            },
        )

        assert response.status_code == 401
