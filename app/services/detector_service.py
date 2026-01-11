# app/services/detector_service.py
"""
Detector Service

Provides emotion analysis functionality by wrapping the detector module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Import from the existing detector module
from detector.formatter import format_for_client
from detector.detector import InvalidTextError


# Self-harm keywords for flagging
SELF_HARM_KEYWORDS: List[str] = [
    # English
    "suicide",
    "kill myself",
    "end my life",
    "hurt myself",
    "self harm",
    "cut myself",
    "want to die",
    "better off dead",
    # Portuguese
    "não aguento mais",
    "nao aguento mais",
    "tirar minha vida",
    "tirar a minha vida",
    "me matar",
    "quero morrer",
    # Spanish
    "quitarme la vida",
    "hacerme daño",
    "quiero morir",
    "matarme",
]


def analyze_emotion(
    text: str,
    locale: str = "en",
    region: Optional[str] = None,
    domain: str = "web",
) -> Dict[str, Any]:
    """
    Analyze emotional tone of text.

    Args:
        text: The text to analyze
        locale: Language locale (en, es, pt)
        region: Geographic region (for hotline information)
        domain: Domain context (web, mobile, etc.)

    Returns:
        Formatted analysis results including:
        - coreMixture: Emotion percentages
        - results: Dominant and current emotions
        - meta: Additional metadata
        - hotlines: Regional crisis hotlines (if applicable)

    Raises:
        ValueError: If text is empty or invalid
        InvalidTextError: If text exceeds limits
    """
    if not text or not text.strip():
        raise ValueError("Text is required")

    try:
        result = format_for_client(
            text=text,
            locale=locale,
            region=region,
            domain=domain,
        )
        return result

    except InvalidTextError as e:
        raise ValueError(str(e))


def detect_self_harm_flag(text: str) -> bool:
    """
    Detect potential self-harm content in text.

    This is a simple keyword-based detector. It will later be
    enriched by lexicon-driven detector logic.

    Args:
        text: The text to check

    Returns:
        True if self-harm keywords are detected
    """
    if not text:
        return False

    lowered = text.lower()

    for phrase in SELF_HARM_KEYWORDS:
        if phrase in lowered:
            return True

    return False


def get_detector_version() -> str:
    """Get the detector version string."""
    return "v31-espt-meta-db"


def get_supported_languages() -> List[str]:
    """Get list of supported language codes."""
    return ["en", "es", "pt"]


def get_emotion_list() -> List[str]:
    """Get list of supported emotions."""
    return ["anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"]
