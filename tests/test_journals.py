# tests/test_journals.py
"""
Journal Entry Tests

Tests for journal CRUD operations.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient


class TestJournalList:
    """Tests for listing journals."""

    def test_list_journals_empty(self, auth_client: FlaskClient):
        """Test listing journals when none exist."""
        response = auth_client.get("/api/journals")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"] == []

    def test_list_journals_unauthenticated(self, client: FlaskClient):
        """Test listing journals when not authenticated."""
        response = client.get("/api/journals")

        assert response.status_code == 401


class TestJournalCreate:
    """Tests for creating journals."""

    def test_create_journal(self, auth_client: FlaskClient):
        """Test creating a journal entry."""
        response = auth_client.post(
            "/api/journals",
            json={
                "title": "My First Journal",
                "journal_text": "Today was a great day!",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["journal"]["title"] == "My First Journal"

    def test_create_journal_with_analysis(self, auth_client: FlaskClient):
        """Test creating a journal entry with analysis data."""
        response = auth_client.post(
            "/api/journals",
            json={
                "title": "Analyzed Entry",
                "source_text": "I am feeling happy",
                "analysis_json": {"dominant": "joy"},
                "journal_text": "Notes about my mood",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["ok"] is True

    def test_create_journal_missing_title(self, auth_client: FlaskClient):
        """Test creating a journal without title."""
        response = auth_client.post(
            "/api/journals",
            json={
                "journal_text": "No title provided",
            },
        )

        assert response.status_code == 400

    def test_create_journal_unauthenticated(self, client: FlaskClient):
        """Test creating a journal when not authenticated."""
        response = client.post(
            "/api/journals",
            json={
                "title": "My Journal",
                "journal_text": "Content",
            },
        )

        assert response.status_code == 401


class TestJournalGet:
    """Tests for getting a specific journal."""

    def test_get_journal(self, auth_client: FlaskClient):
        """Test getting a specific journal entry."""
        # Create a journal first
        create_response = auth_client.post(
            "/api/journals",
            json={
                "title": "Test Journal",
                "journal_text": "Test content",
            },
        )
        journal_id = create_response.get_json()["data"]["journal"]["id"]

        # Get the journal
        response = auth_client.get(f"/api/journals/{journal_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["journal"]["title"] == "Test Journal"

    def test_get_journal_not_found(self, auth_client: FlaskClient):
        """Test getting a non-existent journal."""
        response = auth_client.get("/api/journals/99999")

        assert response.status_code == 404


class TestJournalUpdate:
    """Tests for updating journals."""

    def test_update_journal_title(self, auth_client: FlaskClient):
        """Test updating a journal title."""
        # Create a journal first
        create_response = auth_client.post(
            "/api/journals",
            json={
                "title": "Original Title",
                "journal_text": "Content",
            },
        )
        journal_id = create_response.get_json()["data"]["journal"]["id"]

        # Update the journal
        response = auth_client.put(
            f"/api/journals/{journal_id}",
            json={
                "title": "Updated Title",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["journal"]["title"] == "Updated Title"

    def test_update_journal_content(self, auth_client: FlaskClient):
        """Test updating journal content."""
        # Create a journal first
        create_response = auth_client.post(
            "/api/journals",
            json={
                "title": "Test Journal",
                "journal_text": "Original content",
            },
        )
        journal_id = create_response.get_json()["data"]["journal"]["id"]

        # Update the journal
        response = auth_client.put(
            f"/api/journals/{journal_id}",
            json={
                "journal_text": "Updated content",
            },
        )

        assert response.status_code == 200

    def test_update_journal_not_found(self, auth_client: FlaskClient):
        """Test updating a non-existent journal."""
        response = auth_client.put(
            "/api/journals/99999",
            json={
                "title": "New Title",
            },
        )

        assert response.status_code == 404


class TestJournalDelete:
    """Tests for deleting journals."""

    def test_delete_journal(self, auth_client: FlaskClient):
        """Test deleting a journal entry."""
        # Create a journal first
        create_response = auth_client.post(
            "/api/journals",
            json={
                "title": "To Be Deleted",
                "journal_text": "Content",
            },
        )
        journal_id = create_response.get_json()["data"]["journal"]["id"]

        # Delete the journal
        response = auth_client.delete(f"/api/journals/{journal_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

        # Verify it's deleted
        get_response = auth_client.get(f"/api/journals/{journal_id}")
        assert get_response.status_code == 404

    def test_delete_journal_not_found(self, auth_client: FlaskClient):
        """Test deleting a non-existent journal."""
        response = auth_client.delete("/api/journals/99999")

        assert response.status_code == 404


class TestJournalPin:
    """Tests for pinning/unpinning journals."""

    def test_pin_journal(self, auth_client: FlaskClient):
        """Test pinning a journal entry."""
        # Create a journal first
        create_response = auth_client.post(
            "/api/journals",
            json={
                "title": "To Be Pinned",
                "journal_text": "Content",
            },
        )
        journal_id = create_response.get_json()["data"]["journal"]["id"]

        # Pin the journal
        response = auth_client.post(
            f"/api/journals/{journal_id}/pin",
            json={"is_pinned": True},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["data"]["journal"]["is_pinned"] is True

    def test_unpin_journal(self, auth_client: FlaskClient):
        """Test unpinning a journal entry."""
        # Create and pin a journal first
        create_response = auth_client.post(
            "/api/journals",
            json={
                "title": "Pinned Journal",
                "journal_text": "Content",
            },
        )
        journal_id = create_response.get_json()["data"]["journal"]["id"]

        auth_client.post(
            f"/api/journals/{journal_id}/pin",
            json={"is_pinned": True},
        )

        # Unpin the journal
        response = auth_client.post(
            f"/api/journals/{journal_id}/pin",
            json={"is_pinned": False},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["journal"]["is_pinned"] is False
