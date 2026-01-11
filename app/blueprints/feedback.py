# app/blueprints/feedback.py
"""
Feedback Blueprint

Handles user feedback on analysis accuracy:
- Submit feedback
"""

from __future__ import annotations

from flask import Blueprint, request, g

from app.db.repositories.feedback_repository import FeedbackRepository
from app.utils.responses import api_response
from app.utils.validation import validate_request, FEEDBACK_SCHEMA
from app.utils.security import rate_limit

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("", methods=["POST"])
@rate_limit(limit=10, window_seconds=60)
@validate_request(FEEDBACK_SCHEMA)
def submit_feedback(validated_data: dict):
    """
    Submit anonymous feedback about analysis accuracy.

    Expected JSON body:
        {
            "entry_text": "...",          # Original analyzed text
            "analysis_json": {...},       # Full analysis data
            "feedback_text": "..."        # User's feedback (required)
        }

    Note: No user account is attached to feedback submissions.
    """
    feedback_repo = FeedbackRepository()

    result = feedback_repo.create_feedback(
        entry_text=validated_data["entry_text"],
        feedback_text=validated_data["feedback_text"],
        analysis_json=validated_data.get("analysis_json"),
    )

    return api_response(
        data={"feedback_id": result["id"]},
        message="Feedback submitted successfully. Thank you!",
        status_code=201,
    )
