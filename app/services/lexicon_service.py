# app/services/lexicon_service.py
"""
Lexicon Service

Provides lexicon management functionality including external lookups
and lexicon expansion.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Import from the existing detector module
from detector.detector import LEXICON_TOKEN, set_lexicon_token
from detector.external_lexicon import (
    lookup_word,
    expand_lexicon_from_external,
    get_expansion_stats,
    fetch_and_extract_word,
    SLANG_WORDS_TO_FETCH,
    VOCABULARY_WORDS_EN,
    VOCABULARY_WORDS_ES,
    VOCABULARY_WORDS_PT,
)


# Valid emotions
VALID_EMOTIONS = {"anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"}


def lookup_word_external(word: str, language: str = "en") -> Dict[str, Any]:
    """
    Look up a word from external dictionary sources.

    Args:
        word: The word to look up
        language: Language code (en, es, pt)

    Returns:
        Dictionary containing:
        - word: The lookup word
        - language: The language
        - definitions: List of definitions from various sources
        - extracted_emotions: Extracted emotion weights
        - sources: List of sources used
    """
    return lookup_word(word, language)


def get_lexicon_stats() -> Dict[str, Any]:
    """
    Get statistics about the current emotion lexicon.

    Returns:
        Dictionary containing:
        - current_lexicon: Word counts per language
        - expansion_available: Number of words available for expansion
        - total_current: Total words in lexicon
        - total_expansion_available: Total words available for expansion
    """
    stats = {
        "current_lexicon": {},
        "expansion_available": {
            "slang_words": len(SLANG_WORDS_TO_FETCH),
            "vocabulary_en": len(VOCABULARY_WORDS_EN),
            "vocabulary_es": len(VOCABULARY_WORDS_ES),
            "vocabulary_pt": len(VOCABULARY_WORDS_PT),
        },
        "total_current": 0,
        "total_expansion_available": 0,
    }

    for lang, words in LEXICON_TOKEN.items():
        count = len(words)
        stats["current_lexicon"][lang] = count
        stats["total_current"] += count

    stats["total_expansion_available"] = (
        stats["expansion_available"]["slang_words"]
        + stats["expansion_available"]["vocabulary_en"]
        + stats["expansion_available"]["vocabulary_es"]
        + stats["expansion_available"]["vocabulary_pt"]
    )

    return stats


def expand_lexicon(
    languages: List[str] = None,
    include_slang: bool = True,
    include_vocabulary: bool = True,
    apply_immediately: bool = True,
) -> Dict[str, Any]:
    """
    Expand the emotion lexicon by fetching words from external sources.

    Args:
        languages: List of language codes to expand
        include_slang: Whether to include slang from Urban Dictionary
        include_vocabulary: Whether to include vocabulary words
        apply_immediately: Whether to apply changes to the detector

    Returns:
        Dictionary containing:
        - stats: Expansion statistics
        - applied: Whether changes were applied
        - message: Summary message
    """
    if languages is None:
        languages = ["en", "es", "pt"]

    # Get current lexicon
    original_lexicon = dict(LEXICON_TOKEN)

    # Expand with external sources
    expanded_lexicon = expand_lexicon_from_external(
        original_lexicon,
        languages=languages,
        include_slang=include_slang,
        include_vocabulary=include_vocabulary,
    )

    # Get expansion statistics
    stats = get_expansion_stats(original_lexicon, expanded_lexicon)

    # Apply to detector if requested
    if apply_immediately:
        set_lexicon_token(expanded_lexicon, expand_morphology=True)

    return {
        "stats": stats,
        "applied": apply_immediately,
        "message": f"Added {stats['total_new']} new words across {len(languages)} language(s)",
    }


def add_word_to_lexicon(
    word: str,
    language: str = "en",
    include_slang: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Add a single word to the lexicon by fetching from external sources.

    Args:
        word: The word to add
        language: Language code
        include_slang: Whether to include Urban Dictionary for English

    Returns:
        Dictionary with word details and emotions, or None if no emotions found
    """
    # Fetch and extract emotion weights
    weights = fetch_and_extract_word(word, language, include_slang)

    if not weights:
        return None

    # Merge weights into a single emotion vector
    merged_emotions: Dict[str, float] = {}
    for w in weights:
        for emotion, score in w.emotions.items():
            if emotion not in merged_emotions:
                merged_emotions[emotion] = 0.0
            merged_emotions[emotion] = max(merged_emotions[emotion], score)

    # Add to lexicon
    if language not in LEXICON_TOKEN:
        LEXICON_TOKEN[language] = {}

    LEXICON_TOKEN[language][word] = merged_emotions

    # Rebuild detector indices
    set_lexicon_token(LEXICON_TOKEN, expand_morphology=True)

    return {
        "word": word,
        "language": language,
        "emotions": merged_emotions,
        "sources": list(set(w.source for w in weights)),
    }


def add_custom_word(
    word: str,
    language: str,
    emotions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Add a word with custom emotion weights (no external lookup).

    Args:
        word: The word to add
        language: Language code
        emotions: Dictionary of emotion weights

    Returns:
        Dictionary with word details and filtered emotions

    Raises:
        ValueError: If no valid emotions are provided
    """
    # Filter and validate emotions
    filtered_emotions = {}
    for emotion, weight in emotions.items():
        if emotion in VALID_EMOTIONS:
            try:
                filtered_emotions[emotion] = float(weight)
            except (ValueError, TypeError):
                pass

    if not filtered_emotions:
        raise ValueError("At least one valid emotion weight is required")

    # Add to lexicon
    if language not in LEXICON_TOKEN:
        LEXICON_TOKEN[language] = {}

    LEXICON_TOKEN[language][word] = filtered_emotions

    # Rebuild detector indices
    set_lexicon_token(LEXICON_TOKEN, expand_morphology=True)

    return {
        "word": word,
        "language": language,
        "emotions": filtered_emotions,
    }


def get_word_emotions(word: str, language: str = "en") -> Optional[Dict[str, float]]:
    """
    Get the emotion weights for a word in the current lexicon.

    Args:
        word: The word to look up
        language: Language code

    Returns:
        Dictionary of emotion weights, or None if not found
    """
    lang_lexicon = LEXICON_TOKEN.get(language, {})
    return lang_lexicon.get(word.lower())


def remove_word_from_lexicon(word: str, language: str = "en") -> bool:
    """
    Remove a word from the lexicon.

    Args:
        word: The word to remove
        language: Language code

    Returns:
        True if word was removed, False if not found
    """
    lang_lexicon = LEXICON_TOKEN.get(language, {})
    if word.lower() in lang_lexicon:
        del lang_lexicon[word.lower()]
        set_lexicon_token(LEXICON_TOKEN, expand_morphology=True)
        return True
    return False
