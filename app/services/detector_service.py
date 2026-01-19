# app/services/detector_service.py
"""
Detector Service

Provides emotion analysis functionality by wrapping the detector module.
Includes enhanced lexicons, expanded self-harm detection, and consistent
output across English, Spanish, and Portuguese.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

# Import from the existing detector module
from detector.formatter import format_for_client
from detector.detector import InvalidTextError

logger = logging.getLogger(__name__)

# Initialize enhanced detector on module load
_detector_initialized = False


def _ensure_detector_initialized() -> None:
    """Ensure the enhanced detector is initialized."""
    global _detector_initialized
    if _detector_initialized:
        return

    try:
        from detector.enhanced_init import initialize_enhanced_detector
        if initialize_enhanced_detector():
            logger.info("Enhanced detector initialized successfully")
        else:
            logger.warning("Enhanced detector initialization returned False, using base detector")
    except ImportError as e:
        logger.warning(f"Enhanced detector not available: {e}")
    except Exception as e:
        logger.error(f"Error initializing enhanced detector: {e}")

    _detector_initialized = True


# Initialize on module load
_ensure_detector_initialized()


# Comprehensive self-harm keywords for flagging
# Organized by language with modern slang and variations
SELF_HARM_KEYWORDS: List[str] = [
    # =========================================================================
    # ENGLISH
    # =========================================================================
    # Direct statements
    "suicide",
    "suicidal",
    "kill myself",
    "end my life",
    "end it all",
    "hurt myself",
    "self harm",
    "self-harm",
    "cut myself",
    "want to die",
    "wanna die",
    "better off dead",
    "no reason to live",
    "nothing to live for",
    "cant go on",
    "can't go on",

    # Modern slang/euphemisms
    "off myself",
    "off thyself",
    "unalive",
    "unalive myself",
    "kms",  # kill myself
    "ctb",  # catch the bus
    "sewerslide",  # TikTok censorship bypass
    "sewer slide",
    "self delete",
    "permanent solution",
    "permanent sleep",

    # Hopelessness
    "no point in living",
    "done with life",
    "tired of living",
    "give up on life",
    "no hope left",
    "world would be better without me",

    # =========================================================================
    # PORTUGUESE (Brazilian & European)
    # =========================================================================
    # Direct statements
    "suicídio",
    "suicidio",
    "me matar",
    "quero morrer",
    "quero me matar",
    "tirar minha vida",
    "tirar a minha vida",
    "acabar com tudo",
    "acabar com a minha vida",
    "não aguento mais",
    "nao aguento mais",
    "não consigo mais",
    "nao consigo mais",

    # Self-harm
    "me machucar",
    "me cortar",
    "automutilação",
    "automutilacao",
    "autolesão",
    "autolesao",

    # Hopelessness
    "sem vontade de viver",
    "perdi a vontade de viver",
    "não há esperança",
    "nao ha esperanca",
    "fundo do poço",
    "desisti de tudo",

    # =========================================================================
    # SPANISH
    # =========================================================================
    # Direct statements
    "suicidio",
    "suicidarme",
    "matarme",
    "quitarme la vida",
    "quiero morir",
    "me quiero morir",
    "acabar con mi vida",
    "acabar con todo",
    "no puedo más",
    "no puedo mas",
    "no aguanto más",
    "no aguanto mas",

    # Self-harm
    "hacerme daño",
    "hacerme dano",
    "autolesión",
    "autolesion",
    "cortarme",
    "me corto",

    # Hopelessness
    "no quiero vivir",
    "sin razón para vivir",
    "sin razon para vivir",
    "sin ganas de vivir",
    "perdí las ganas de vivir",
    "perdi las ganas de vivir",
    "no hay esperanza",
    "sin esperanza",
    "me rindo",
    "me doy por vencido",
    "me doy por vencida",
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
        text: The text to analyze (1-250 words)
        locale: Language locale (en, es, pt)
        region: Geographic region (for hotline information)
        domain: Domain context (web, mobile, etc.)

    Returns:
        Formatted analysis results including:
        - coreMixture: Emotion percentages
        - analysis: Per-emotion scores
        - results: Dominant and current emotions with nuanced labels
        - metrics: Arousal, confidence, mixture profile
        - risk: Risk level and regional hotline info
        - meta: Additional metadata

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

        # Ensure consistent output structure
        _ensure_output_consistency(result, locale)

        return result

    except InvalidTextError as e:
        raise ValueError(str(e))


def _ensure_output_consistency(result: Dict[str, Any], locale: str) -> None:
    """
    Ensure the result has consistent structure across all languages.

    This normalizes any edge cases where the formatter might produce
    slightly different structures.
    """
    # Ensure all required fields exist
    required_fields = [
        "text", "locale", "analysis", "coreMixture", "results",
        "metrics", "risk", "meta"
    ]

    for field in required_fields:
        if field not in result:
            if field == "analysis":
                result[field] = []
            elif field == "coreMixture":
                result[field] = []
            elif field == "results":
                result[field] = {"dominant": {}, "current": {}}
            elif field == "metrics":
                result[field] = {}
            elif field == "risk":
                result[field] = {"level": "none"}
            elif field == "meta":
                result[field] = {}
            else:
                result[field] = None

    # Ensure results has both dominant and current
    if "results" in result:
        if "dominant" not in result["results"]:
            result["results"]["dominant"] = {}
        if "current" not in result["results"]:
            result["results"]["current"] = {}

    # Ensure risk has level
    if "risk" in result and "level" not in result["risk"]:
        result["risk"]["level"] = "none"


def detect_self_harm_flag(text: str) -> bool:
    """
    Detect potential self-harm content in text.

    Uses comprehensive keyword matching across English, Spanish,
    and Portuguese including modern slang and euphemisms.

    Args:
        text: The text to check

    Returns:
        True if self-harm keywords are detected
    """
    if not text:
        return False

    lowered = text.lower()

    # Check against all keywords
    for phrase in SELF_HARM_KEYWORDS:
        if phrase.lower() in lowered:
            return True

    return False


def detect_crisis_level(text: str) -> str:
    """
    Detect the crisis level of text.

    Returns:
        "severe" - Multiple strong indicators
        "likely" - Single strong indicator
        "possible" - Soft indicators present
        "none" - No indicators
    """
    if not text:
        return "none"

    # Use the detector's built-in risk detection
    try:
        from detector.detector import detect_self_harm_risk
        return detect_self_harm_risk(text, humor_score=0.0)
    except ImportError:
        # Fallback to simple keyword detection
        if detect_self_harm_flag(text):
            return "likely"
        return "none"


def get_detector_version() -> str:
    """Get the detector version string."""
    return "v31-espt-meta-db-enhanced"


def get_supported_languages() -> List[str]:
    """Get list of supported language codes."""
    return ["en", "es", "pt"]


def get_emotion_list() -> List[str]:
    """Get list of supported emotions."""
    return ["anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"]


def get_lexicon_stats() -> Dict[str, Any]:
    """Get statistics about the loaded lexicons."""
    try:
        from detector.enhanced_init import get_lexicon_stats
        return get_lexicon_stats()
    except ImportError:
        return {
            "initialized": False,
            "error": "Enhanced detector not available"
        }
