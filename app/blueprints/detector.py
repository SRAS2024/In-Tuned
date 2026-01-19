# app/blueprints/detector.py
"""
Emotion Detector Blueprint

Handles emotion analysis API:
- Analyze text for emotional content
"""

from __future__ import annotations

import logging
from flask import Blueprint, request, current_app, g

from app.utils.responses import api_response, api_error
from app.utils.validation import validate_request, ANALYZE_TEXT_SCHEMA
from app.utils.security import rate_limit
from app.utils.errors import ValidationError
from app.services.detector_service import analyze_emotion

detector_bp = Blueprint("detector", __name__)

# Module logger for diagnostic output
logger = logging.getLogger(__name__)


@detector_bp.route("/analyze", methods=["POST"])
@rate_limit(limit=30, window_seconds=60)
def analyze_text():
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

    Response shape (success):
        {
            "ok": true,
            "data": {
                "text": "...",
                "locale": "en",
                "coreMixture": [...],
                "analysis": [...],
                "results": { "dominant": {...}, "current": {...} },
                "metrics": {...},
                "risk": {...}
            }
        }

    Response shape (error):
        {
            "ok": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human readable message",
                "details": {...}
            }
        }
    """
    request_id = getattr(g, "request_id", "unknown")

    # Validate Content-Type - accept JSON or parse best-effort
    content_type = request.content_type or ""
    is_json_content = "application/json" in content_type.lower()

    # Try to parse JSON body
    try:
        data = request.get_json(silent=True, force=True) or {}
    except Exception as e:
        logger.warning(
            "Failed to parse JSON body",
            extra={
                "request_id": request_id,
                "content_type": content_type,
                "error": str(e),
            },
        )
        return api_error(
            message="Invalid JSON in request body",
            code="INVALID_JSON",
            status_code=400,
            details={"content_type": content_type},
        )

    # Validate using schema
    try:
        validated_data = ANALYZE_TEXT_SCHEMA.validate(data)
    except ValidationError as e:
        logger.info(
            "Validation failed for analyze request",
            extra={
                "request_id": request_id,
                "error": e.message,
                "details": e.details,
            },
        )
        raise

    text = validated_data["text"]
    locale = validated_data.get("locale") or "en"
    region = validated_data.get("region")

    # Additional validation: reject empty text after stripping
    if not text.strip():
        logger.info(
            "Empty text rejected",
            extra={"request_id": request_id},
        )
        return api_error(
            message="Text cannot be empty",
            code="EMPTY_TEXT",
            status_code=400,
            details={"field": "text"},
        )

    # Diagnostic logging (do not log full text for privacy)
    text_length = len(text)
    word_count = len(text.split())
    logger.info(
        "Analyze request received",
        extra={
            "request_id": request_id,
            "json_parsed": True,
            "text_length": text_length,
            "word_count": word_count,
            "locale": locale,
            "region": region,
            "content_type": content_type,
        },
    )

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

        logger.info(
            "Analysis completed successfully",
            extra={
                "request_id": request_id,
                "has_result": result is not None,
            },
        )

        return api_response(data=result)

    except ValueError as e:
        logger.warning(
            "Analysis validation error",
            extra={
                "request_id": request_id,
                "error": str(e),
            },
        )
        raise ValidationError(message=str(e), field="text")

    except Exception as e:
        logger.error(
            f"Analysis error: {str(e)}",
            extra={
                "request_id": request_id,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return api_error(
            message="Analysis failed. Please try again.",
            code="ANALYSIS_ERROR",
            status_code=500,
            details={"error_type": type(e).__name__},
        )
