# detector/enhanced_init.py
"""
Enhanced Detector Initialization

This module patches the existing detector with enhanced lexicons,
expanded self-harm detection, and improved linguistic processing.

Call `initialize_enhanced_detector()` at application startup to
enable the enhanced features.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Flag to track if initialization has been done
_initialized = False


def initialize_enhanced_detector() -> bool:
    """
    Initialize the detector with enhanced lexicons and safety patterns.

    This function:
    1. Loads enhanced emotion lexicons for EN/ES/PT
    2. Loads enhanced phrase lexicons
    3. Updates self-harm detection patterns
    4. Returns True on success, False on failure

    Should be called once at application startup.
    """
    global _initialized

    if _initialized:
        logger.debug("Enhanced detector already initialized")
        return True

    try:
        # Import detector module
        from . import detector as det

        # Import enhanced lexicons
        from .lexicon_loader import (
            ENGLISH_LEXICON,
            ENGLISH_PHRASES,
            SPANISH_LEXICON,
            SPANISH_PHRASES,
            PORTUGUESE_LEXICON,
            PORTUGUESE_PHRASES,
            get_safety_patterns,
            is_lexicons_loaded,
        )

        if not is_lexicons_loaded():
            logger.warning("Enhanced lexicons not available, using base lexicons")
            return False

        # Merge enhanced lexicons with existing ones
        _merge_enhanced_lexicons(det, {
            "en": ENGLISH_LEXICON,
            "es": SPANISH_LEXICON,
            "pt": PORTUGUESE_LEXICON,
        })

        # Merge enhanced phrases
        _merge_enhanced_phrases(det, {
            "en": ENGLISH_PHRASES,
            "es": SPANISH_PHRASES,
            "pt": PORTUGUESE_PHRASES,
        })

        # Update self-harm patterns
        _update_safety_patterns(det)

        _initialized = True
        logger.info("Enhanced detector initialized successfully")

        # Log statistics
        en_count = len(det.LEXICON_TOKEN.get("en", {}))
        es_count = len(det.LEXICON_TOKEN.get("es", {}))
        pt_count = len(det.LEXICON_TOKEN.get("pt", {}))
        phrase_count = len(det.PHRASE_LEXICON)

        logger.info(
            f"Lexicon stats: EN={en_count} words, ES={es_count} words, "
            f"PT={pt_count} words, Phrases={phrase_count}"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to initialize enhanced detector: {e}")
        return False


def _merge_enhanced_lexicons(
    det,
    enhanced_lexicons: Dict[str, Dict[str, Dict[str, float]]],
) -> None:
    """Merge enhanced lexicons into the detector's LEXICON_TOKEN."""
    for lang, lexicon in enhanced_lexicons.items():
        if lang not in det.LEXICON_TOKEN:
            det.LEXICON_TOKEN[lang] = {}

        existing = det.LEXICON_TOKEN[lang]

        for word, emotions in lexicon.items():
            # Normalize the word
            word_norm = det.join_for_lex(word)

            if word_norm not in existing:
                existing[word_norm] = {}

            for emotion, weight in emotions.items():
                # Use max weight between existing and enhanced
                current = existing[word_norm].get(emotion, 0.0)
                existing[word_norm][emotion] = max(current, weight)


def _merge_enhanced_phrases(
    det,
    enhanced_phrases: Dict[str, Dict[str, Dict[str, float]]],
) -> None:
    """Merge enhanced phrases into the detector's PHRASE_LEXICON."""
    for lang, phrases in enhanced_phrases.items():
        for phrase, emotions in phrases.items():
            # Normalize phrase for consistent lookup
            phrase_norm = det.normalize_for_phrase(phrase)

            if phrase_norm not in det.PHRASE_LEXICON:
                det.PHRASE_LEXICON[phrase_norm] = {}

            for emotion, weight in emotions.items():
                current = det.PHRASE_LEXICON[phrase_norm].get(emotion, 0.0)
                det.PHRASE_LEXICON[phrase_norm][emotion] = max(current, weight)

    # Rebuild phrase index
    det._rebuild_phrase_index()


def _update_safety_patterns(det) -> None:
    """Update the detector's self-harm patterns with enhanced ones."""
    from .lexicon_loader import get_safety_patterns

    hard_patterns, soft_patterns = get_safety_patterns()

    # Merge with existing patterns (don't replace, add to them)
    existing_hard = set()
    for pat in det.SELF_HARM_HARD_REGEX:
        existing_hard.add(pat.pattern)

    existing_soft = set()
    for pat in det.SELF_HARM_SOFT_REGEX:
        existing_soft.add(pat.pattern)

    # Add new patterns
    for pat in hard_patterns:
        if pat.pattern not in existing_hard:
            det.SELF_HARM_HARD_REGEX.append(pat)
            existing_hard.add(pat.pattern)

    for pat in soft_patterns:
        if pat.pattern not in existing_soft:
            det.SELF_HARM_SOFT_REGEX.append(pat)
            existing_soft.add(pat.pattern)

    logger.info(
        f"Safety patterns updated: {len(det.SELF_HARM_HARD_REGEX)} hard, "
        f"{len(det.SELF_HARM_SOFT_REGEX)} soft"
    )


def is_initialized() -> bool:
    """Check if enhanced detector has been initialized."""
    return _initialized


def get_lexicon_stats() -> Dict[str, int]:
    """Get statistics about loaded lexicons."""
    try:
        from . import detector as det

        return {
            "en_words": len(det.LEXICON_TOKEN.get("en", {})),
            "es_words": len(det.LEXICON_TOKEN.get("es", {})),
            "pt_words": len(det.LEXICON_TOKEN.get("pt", {})),
            "phrases": len(det.PHRASE_LEXICON),
            "hard_patterns": len(det.SELF_HARM_HARD_REGEX),
            "soft_patterns": len(det.SELF_HARM_SOFT_REGEX),
            "initialized": _initialized,
        }
    except Exception:
        return {"initialized": False}
