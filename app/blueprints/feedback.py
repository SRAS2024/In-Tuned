# app/blueprints/feedback.py
"""
Feedback Blueprint

Handles user feedback on analysis accuracy:
- Submit feedback
- Translate the feedback into runtime adjustments for the detector so
  future analyses learn from what users tell us was wrong or missing.
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

from flask import Blueprint

from app.db.repositories.feedback_repository import FeedbackRepository
from app.utils.responses import api_response
from app.utils.validation import validate_request, FEEDBACK_SCHEMA
from app.utils.security import rate_limit

logger = logging.getLogger(__name__)

feedback_bp = Blueprint("feedback", __name__)


# Map common emotion words (English / Spanish / Portuguese) to canonical ids.
_EMOTION_ALIASES = {
    "anger": "anger", "angry": "anger", "rage": "anger", "mad": "anger",
    "frustrated": "anger", "frustration": "anger",
    "ira": "anger", "enojo": "anger", "rabia": "anger", "raiva": "anger",
    "disgust": "disgust", "disgusted": "disgust", "asco": "disgust",
    "nojo": "disgust", "repulsion": "disgust",
    "fear": "fear", "afraid": "fear", "anxious": "fear", "anxiety": "fear",
    "miedo": "fear", "ansiedad": "fear", "medo": "fear", "ansiedade": "fear",
    "joy": "joy", "happy": "joy", "happiness": "joy", "alegria": "joy",
    "alegría": "joy", "felicidad": "joy", "felicidade": "joy", "feliz": "joy",
    "sad": "sadness", "sadness": "sadness", "down": "sadness",
    "tristeza": "sadness", "triste": "sadness",
    "passion": "passion", "love": "passion", "loving": "passion",
    "pasion": "passion", "pasión": "passion", "paixao": "passion",
    "paixão": "passion", "amor": "passion",
    "surprise": "surprise", "surprised": "surprise", "shock": "surprise",
    "shocked": "surprise", "sorpresa": "surprise", "surpresa": "surprise",
}

_DOWN_HINTS = (
    # English
    "does not fit", "doesnt fit", "doesn't fit", "wrong", "incorrect",
    "inaccurate", "not accurate", "should be lower", "is too high",
    "too high", "way too high", "less", "lower", "remove", "drop",
    # Spanish
    "no es", "no encaja", "no aplica", "es incorrecto", "muy alto",
    "demasiado alto", "menos", "bajar",
    # Portuguese
    "não é", "nao e", "não encaixa", "nao encaixa", "incorreto", "muito alto",
    "menos", "baixar", "errado",
)
_UP_HINTS = (
    "should be higher", "too low", "way too low", "more", "higher",
    "stronger", "raise", "increase",
    "muy bajo", "demasiado bajo", "más", "mas", "subir", "aumentar",
    "muito baixo", "deveria ser maior",
)


def _parse_feedback_directives(feedback_text: str) -> List[Tuple[str, str, float]]:
    """
    Parse the user's free-form feedback into (emotion, direction, strength)
    triples we can feed into `record_feedback_adjustment`.

    Examples this will pick up:
        - "sadness does not fit"          -> ("sadness", "down", 1.0)
        - "joy is inaccurate"             -> ("joy", "down", 1.0)
        - "anger should be slightly higher" -> ("anger", "up", 0.6)
        - "more passion please"           -> ("passion", "up", 1.0)
    """
    if not feedback_text:
        return []
    text = feedback_text.lower()

    directives: List[Tuple[str, str, float]] = []
    seen_pairs = set()

    # Look for emotion words and their nearest direction hint
    word_iter = list(re.finditer(r"[a-záéíóúñãâêôõç]+", text, re.UNICODE))
    for m in word_iter:
        word = m.group(0)
        emotion = _EMOTION_ALIASES.get(word)
        if not emotion:
            continue

        window = text[max(0, m.start() - 60): m.end() + 60]
        direction: str = ""
        if any(h in window for h in _DOWN_HINTS):
            direction = "down"
        elif any(h in window for h in _UP_HINTS):
            direction = "up"

        if not direction:
            continue

        strength = 0.6 if "slight" in window or "a bit" in window or "un poco" in window or "un pouco" in window else 1.0
        key = (emotion, direction)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        directives.append((emotion, direction, strength))

    return directives


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

    The feedback is stored and, if a clear correction is detected
    ("sadness does not fit", "anger should be higher", etc.), the runtime
    detector is nudged so similar future inputs reflect the correction.
    """
    feedback_repo = FeedbackRepository()

    entry_text = validated_data["entry_text"]
    feedback_text = validated_data["feedback_text"]
    analysis_json = validated_data.get("analysis_json")

    result = feedback_repo.create_feedback(
        entry_text=entry_text,
        feedback_text=feedback_text,
        analysis_json=analysis_json,
    )

    # Best-effort runtime learning. Failures here must never block
    # feedback submission.
    try:
        from detector.detector import record_feedback_adjustment

        directives = _parse_feedback_directives(feedback_text)
        for emotion, direction, strength in directives:
            record_feedback_adjustment(
                entry_text=entry_text,
                emotion=emotion,
                direction=direction,
                strength=strength,
            )
        if directives:
            logger.info(
                "Applied %d feedback directive(s) to detector",
                len(directives),
            )
    except Exception as exc:  # pragma: no cover - learning is best-effort
        logger.warning("Failed to apply feedback directives: %s", exc)

    return api_response(
        data={"feedback_id": result["id"]},
        message="Feedback submitted successfully. Thank you!",
        status_code=201,
    )
