# tests/conftest.py
"""
Test Configuration and Fixtures

This module provides pytest fixtures for testing the In-Tuned application.
"""

from __future__ import annotations

import os
import pytest
from typing import Generator

# Set testing environment before importing app
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://localhost:5432/intuned_test"
)
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-production"

from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.db.connection import get_connection


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """Create application for testing."""
    app = create_app("testing")

    # Create database tables
    with app.app_context():
        _init_test_db()

    yield app

    # Cleanup
    with app.app_context():
        _cleanup_test_db()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client: FlaskClient) -> FlaskClient:
    """Create an authenticated test client."""
    # Register and login a test user
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123",
        },
    )

    return client


@pytest.fixture
def admin_client(client: FlaskClient, app: Flask) -> FlaskClient:
    """Create an admin authenticated test client."""
    with client.session_transaction() as session:
        session["is_admin"] = True

    return client


def _init_test_db() -> None:
    """Initialize test database schema."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Create tables
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                preferred_language TEXT DEFAULT 'en',
                preferred_theme TEXT DEFAULT 'dark',
                is_active BOOLEAN DEFAULT TRUE,
                role TEXT DEFAULT 'user',
                failed_login_attempts INTEGER DEFAULT 0,
                last_failed_login TIMESTAMPTZ,
                last_login TIMESTAMPTZ,
                disabled_at TIMESTAMPTZ,
                disabled_reason TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS journals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                source_text TEXT,
                analysis_json JSONB,
                journal_text TEXT,
                is_pinned BOOLEAN DEFAULT FALSE,
                has_self_harm_flag BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS site_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                maintenance_mode BOOLEAN NOT NULL DEFAULT FALSE,
                maintenance_message TEXT
            );

            INSERT INTO site_settings (id, maintenance_mode, maintenance_message)
            VALUES (1, FALSE, NULL)
            ON CONFLICT (id) DO NOTHING;
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lexicon_files (
                id SERIAL PRIMARY KEY,
                language TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT,
                data BYTEA,
                uploaded_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                entry_text TEXT NOT NULL,
                analysis_json JSONB,
                feedback_text TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                actor_id INTEGER,
                actor_type TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                before_state JSONB,
                after_state JSONB,
                ip_address TEXT,
                user_agent TEXT,
                request_id TEXT,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        conn.commit()
        cur.close()


def _cleanup_test_db() -> None:
    """Clean up test database."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Truncate all tables
        cur.execute("TRUNCATE users, journals, notices, site_settings, lexicon_files, feedback, audit_log RESTART IDENTITY CASCADE;")

        conn.commit()
        cur.close()


@pytest.fixture(autouse=True)
def clean_db_between_tests(app: Flask) -> Generator[None, None, None]:
    """Clean database between tests."""
    yield

    with app.app_context():
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("TRUNCATE users, journals, feedback, audit_log RESTART IDENTITY CASCADE;")
            conn.commit()
            cur.close()
