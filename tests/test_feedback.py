# tests/test_feedback.py
"""
Feedback Tests

Tests for feedback submission.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient


class TestFeedbackSubmission:
    """Tests for feedback submission."""

    def test_submit_feedback(self, client: FlaskClient):
        """Test submitting feedback."""
        response = client.post(
            "/api/feedback",
            json={
                "entry_text": "I am happy today",
                "analysis_json": {"dominant": "joy"},
                "feedback_text": "The analysis was accurate!",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["ok"] is True
        assert "feedback_id" in data["data"]

    def test_submit_feedback_without_analysis(self, client: FlaskClient):
        """Test submitting feedback without analysis data."""
        response = client.post(
            "/api/feedback",
            json={
                "entry_text": "I am happy today",
                "feedback_text": "Great analysis!",
            },
        )

        assert response.status_code == 201

    def test_submit_feedback_missing_text(self, client: FlaskClient):
        """Test submitting feedback without entry text."""
        response = client.post(
            "/api/feedback",
            json={
                "feedback_text": "Great analysis!",
            },
        )

        assert response.status_code == 400

    def test_submit_feedback_missing_feedback(self, client: FlaskClient):
        """Test submitting feedback without feedback text."""
        response = client.post(
            "/api/feedback",
            json={
                "entry_text": "I am happy today",
            },
        )

        assert response.status_code == 400

    def test_submit_feedback_empty_feedback(self, client: FlaskClient):
        """Test submitting feedback with empty feedback text."""
        response = client.post(
            "/api/feedback",
            json={
                "entry_text": "I am happy today",
                "feedback_text": "",
            },
        )

        assert response.status_code == 400
