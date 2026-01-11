# app/blueprints/detector.py
"""
Emotion Detector Blueprint

Handles emotion analysis API:
- Analyze text for emotional content
"""

from __future__ import annotations

from flask import Blueprint, request, current_app, g

from app.utils.responses import api_response, api_error
from app.utils.validation import validate_request, ANALYZE_TEXT_SCHEMA
from app.utils.security import rate_limit
from app.utils.errors import ValidationError
from app.services.detector_service import analyze_emotion

detector_bp = Blueprint("detector", __name__)


@detector_bp.route("/analyze", methods=["POST"])
@rate_limit(limit=30, window_seconds=60)
@validate_request(ANALYZE_TEXT_SCHEMA)
def analyze_text(validated_data: dict):
    """
    Analyze emotional tone of text.

    Expected JSON body:
        {
            "text": "...",
            "locale": "en" | "es" | "pt",
            "region": "US" | "BR" | ...,
            "token": "optional_api_token"
        }

    Returns:
        Formatted emotion analysis with mixture vector, dominant/current emotions,
        hotlines, risk levels, and other metrics.
    """
    text = validated_data["text"]
    locale = validated_data.get("locale") or "en"
    region = validated_data.get("region")

    # Token validation (if configured)
    token = validated_data.get("token") or request.headers.get("X-App-Token")
    api_token = current_app.config.get("API_TOKEN")

    if api_token and token != api_token:
        # Token is configured but doesn't match
        # For now, we allow requests without tokens for backward compatibility
        pass

    try:
        result = analyze_emotion(
            text=text,
            locale=locale,
            region=region,
        )

        return api_response(data=result)

    except ValueError as e:
        raise ValidationError(message=str(e), field="text")

    except Exception as e:
        current_app.logger.error(
            f"Analysis error: {str(e)}",
            extra={"request_id": getattr(g, "request_id", "unknown")},
            exc_info=True,
        )
        return api_error(
            message="Analysis failed. Please try again.",
            code="ANALYSIS_ERROR",
            status_code=500,
        )
