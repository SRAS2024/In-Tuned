# tests/test_detector.py
"""
Detector Tests

Tests for emotion detection functionality.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from app.services.detector_service import (
    analyze_emotion,
    detect_self_harm_flag,
    get_emotion_list,
    get_supported_languages,
)


class TestDetectorService:
    """Tests for the detector service functions."""

    def test_analyze_emotion_english(self):
        """Test emotion analysis for English text."""
        result = analyze_emotion("I am so happy today!", locale="en")

        assert result is not None
        assert "coreMixture" in result
        assert "results" in result
        assert "dominant" in result["results"]
        assert "current" in result["results"]

    def test_analyze_emotion_spanish(self):
        """Test emotion analysis for Spanish text."""
        result = analyze_emotion("Estoy muy feliz hoy!", locale="es")

        assert result is not None
        assert "coreMixture" in result

    def test_analyze_emotion_portuguese(self):
        """Test emotion analysis for Portuguese text."""
        result = analyze_emotion("Estou muito feliz hoje!", locale="pt")

        assert result is not None
        assert "coreMixture" in result

    def test_analyze_emotion_empty_text(self):
        """Test emotion analysis with empty text."""
        with pytest.raises(ValueError):
            analyze_emotion("")

    def test_detect_self_harm_flag_english(self):
        """Test self-harm detection for English keywords."""
        assert detect_self_harm_flag("I want to hurt myself") is True
        assert detect_self_harm_flag("I am having a great day") is False

    def test_detect_self_harm_flag_portuguese(self):
        """Test self-harm detection for Portuguese keywords."""
        assert detect_self_harm_flag("não aguento mais") is True
        assert detect_self_harm_flag("Estou feliz") is False

    def test_detect_self_harm_flag_spanish(self):
        """Test self-harm detection for Spanish keywords."""
        assert detect_self_harm_flag("quitarme la vida") is True
        assert detect_self_harm_flag("Estoy contento") is False

    def test_detect_self_harm_flag_empty(self):
        """Test self-harm detection with empty text."""
        assert detect_self_harm_flag("") is False
        assert detect_self_harm_flag(None) is False

    def test_get_emotion_list(self):
        """Test getting the list of emotions."""
        emotions = get_emotion_list()

        assert len(emotions) == 7
        assert "joy" in emotions
        assert "sadness" in emotions
        assert "anger" in emotions
        assert "fear" in emotions
        assert "disgust" in emotions
        assert "surprise" in emotions
        assert "passion" in emotions

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = get_supported_languages()

        assert "en" in languages
        assert "es" in languages
        assert "pt" in languages


class TestDetectorAPI:
    """Tests for the detector API endpoints."""

    def test_analyze_endpoint(self, client: FlaskClient):
        """Test the /api/analyze endpoint."""
        response = client.post(
            "/api/analyze",
            json={
                "text": "I am feeling very happy and excited today!",
                "locale": "en",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert "data" in data
        assert "coreMixture" in data["data"]

    def test_analyze_empty_text(self, client: FlaskClient):
        """Test analyze with empty text."""
        response = client.post(
            "/api/analyze",
            json={
                "text": "",
                "locale": "en",
            },
        )

        assert response.status_code == 400

    def test_analyze_missing_text(self, client: FlaskClient):
        """Test analyze with missing text field."""
        response = client.post(
            "/api/analyze",
            json={
                "locale": "en",
            },
        )

        assert response.status_code == 400

    def test_analyze_spanish(self, client: FlaskClient):
        """Test analyze with Spanish locale."""
        response = client.post(
            "/api/analyze",
            json={
                "text": "Estoy muy triste y preocupado.",
                "locale": "es",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_analyze_portuguese(self, client: FlaskClient):
        """Test analyze with Portuguese locale."""
        response = client.post(
            "/api/analyze",
            json={
                "text": "Estou com raiva e frustrado.",
                "locale": "pt",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_analyze_with_region(self, client: FlaskClient):
        """Test analyze with region parameter."""
        response = client.post(
            "/api/analyze",
            json={
                "text": "I need help, I'm feeling really down.",
                "locale": "en",
                "region": "US",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
