# detector/lexicon_loader.py
"""
Lexicon Loader and Integration Module

This module loads and integrates the enhanced lexicons with the main detector,
providing:
- Combined emotion lexicons for EN/ES/PT
- Enhanced phrase detection
- Expanded self-harm patterns
- Linguistic processing helpers
"""

from __future__ import annotations

import re
import unicodedata
import logging
from typing import Dict, List, Tuple, Optional, Set, Any

logger = logging.getLogger(__name__)


# =========================================================================
# IMPORT ENHANCED LEXICONS
# =========================================================================

try:
    from .lexicons.english import (
        ENGLISH_LEXICON,
        ENGLISH_PHRASES,
        ENGLISH_INTENSIFIERS,
    )
    from .lexicons.spanish import (
        SPANISH_LEXICON,
        SPANISH_PHRASES,
        SPANISH_INTENSIFIERS,
    )
    from .lexicons.portuguese import (
        PORTUGUESE_LEXICON,
        PORTUGUESE_PHRASES,
        PORTUGUESE_INTENSIFIERS,
    )
    from .lexicons.safety import (
        SELF_HARM_PATTERNS_EN,
        SELF_HARM_PATTERNS_ES,
        SELF_HARM_PATTERNS_PT,
        CRISIS_INDICATORS,
        get_all_hard_patterns,
        get_all_soft_patterns,
    )
    LEXICONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Enhanced lexicons not available: {e}")
    LEXICONS_AVAILABLE = False
    ENGLISH_LEXICON = {}
    ENGLISH_PHRASES = {}
    ENGLISH_INTENSIFIERS = {}
    SPANISH_LEXICON = {}
    SPANISH_PHRASES = {}
    SPANISH_INTENSIFIERS = {}
    PORTUGUESE_LEXICON = {}
    PORTUGUESE_PHRASES = {}
    PORTUGUESE_INTENSIFIERS = {}
    SELF_HARM_PATTERNS_EN = {"hard": [], "soft": []}
    SELF_HARM_PATTERNS_ES = {"hard": [], "soft": []}
    SELF_HARM_PATTERNS_PT = {"hard": [], "soft": []}
    CRISIS_INDICATORS = {}


# =========================================================================
# LINGUISTIC PROCESSING
# =========================================================================

def normalize_text(text: str) -> str:
    """Normalize text for processing."""
    # Unicode normalization
    text = unicodedata.normalize("NFC", text)
    # Normalize quotes and apostrophes
    text = text.replace("'", "'").replace("'", "'")
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("–", "-").replace("—", "-")
    return text.strip()


def strip_diacritics(text: str) -> str:
    """Remove diacritics/accents for matching."""
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def normalize_for_lookup(text: str) -> str:
    """Normalize text for lexicon lookup."""
    t = normalize_text(text).lower()
    t = strip_diacritics(t)
    t = re.sub(r"\s+", "_", t).strip("_")
    return t


def tokenize_text(text: str) -> List[str]:
    """Tokenize text preserving contractions and important punctuation."""
    # Pattern keeps apostrophes inside words
    pattern = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ_']+|[^\w\s]", re.UNICODE)
    return pattern.findall(text)


# =========================================================================
# MORPHOLOGICAL EXPANSION
# =========================================================================

# Common English verb endings for expansion
EN_VERB_SUFFIXES = [
    ("", "s", "ed", "ing", "er", "est"),
    ("y", "ies", "ied", "ying"),
    ("e", "es", "ed", "ing"),
]

# Common Spanish verb endings
ES_VERB_SUFFIXES = {
    "ar": ["o", "as", "a", "amos", "áis", "an", "é", "aste", "ó", "aron",
           "aba", "abas", "ábamos", "aban", "ando"],
    "er": ["o", "es", "e", "emos", "éis", "en", "í", "iste", "ió", "ieron",
           "ía", "ías", "íamos", "ían", "iendo"],
    "ir": ["o", "es", "e", "imos", "ís", "en", "í", "iste", "ió", "ieron",
           "ía", "ías", "íamos", "ían", "iendo"],
}

# Common Portuguese verb endings
PT_VERB_SUFFIXES = {
    "ar": ["o", "as", "a", "amos", "am", "ei", "aste", "ou", "aram",
           "ava", "avas", "ávamos", "avam", "ando"],
    "er": ["o", "es", "e", "emos", "em", "i", "este", "eu", "eram",
           "ia", "ias", "íamos", "iam", "endo"],
    "ir": ["o", "es", "e", "imos", "em", "i", "iste", "iu", "iram",
           "ia", "ias", "íamos", "iam", "indo"],
}


def expand_english_word(word: str) -> Set[str]:
    """Expand an English word to its likely inflections."""
    forms = {word}
    base = word.rstrip("s").rstrip("ed").rstrip("ing")
    forms.add(base)

    # Add common suffixes
    for suffix_group in EN_VERB_SUFFIXES:
        for suffix in suffix_group:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[:-len(suffix)] if suffix else word
                for s in suffix_group:
                    forms.add(stem + s)
                break

    return forms


def expand_spanish_word(word: str) -> Set[str]:
    """Expand a Spanish word to its likely conjugations."""
    forms = {word}

    for ending, suffixes in ES_VERB_SUFFIXES.items():
        if word.endswith(ending):
            stem = word[:-len(ending)]
            for suffix in suffixes:
                forms.add(stem + suffix)
            break

    # Gender/number variations for adjectives
    if word.endswith("o"):
        forms.add(word[:-1] + "a")  # masculine -> feminine
        forms.add(word + "s")  # singular -> plural
        forms.add(word[:-1] + "as")  # feminine plural
    elif word.endswith("a"):
        forms.add(word[:-1] + "o")
        forms.add(word + "s")
        forms.add(word[:-1] + "os")
    elif word.endswith("e"):
        forms.add(word + "s")

    return forms


def expand_portuguese_word(word: str) -> Set[str]:
    """Expand a Portuguese word to its likely conjugations."""
    forms = {word}

    for ending, suffixes in PT_VERB_SUFFIXES.items():
        if word.endswith(ending):
            stem = word[:-len(ending)]
            for suffix in suffixes:
                forms.add(stem + suffix)
            break

    # Gender/number variations
    if word.endswith("o"):
        forms.add(word[:-1] + "a")
        forms.add(word + "s")
        forms.add(word[:-1] + "as")
    elif word.endswith("a"):
        forms.add(word[:-1] + "o")
        forms.add(word + "s")
        forms.add(word[:-1] + "os")
    elif word.endswith("e"):
        forms.add(word + "s")

    return forms


# =========================================================================
# LEXICON MERGING
# =========================================================================

def merge_lexicons(
    base_lexicon: Dict[str, Dict[str, float]],
    enhanced_lexicon: Dict[str, Dict[str, float]],
    preference: str = "max",
) -> Dict[str, Dict[str, float]]:
    """
    Merge two lexicons together.

    Args:
        base_lexicon: Original lexicon
        enhanced_lexicon: New lexicon to merge in
        preference: How to handle conflicts - "max", "sum", or "enhanced"

    Returns:
        Merged lexicon
    """
    result = {}

    # Copy base lexicon
    for word, emotions in base_lexicon.items():
        result[word] = dict(emotions)

    # Merge enhanced lexicon
    for word, emotions in enhanced_lexicon.items():
        if word not in result:
            result[word] = dict(emotions)
        else:
            for emotion, weight in emotions.items():
                if emotion not in result[word]:
                    result[word][emotion] = weight
                elif preference == "max":
                    result[word][emotion] = max(result[word][emotion], weight)
                elif preference == "sum":
                    result[word][emotion] = result[word][emotion] + weight
                else:  # "enhanced"
                    result[word][emotion] = weight

    return result


def get_combined_lexicon(lang: str) -> Dict[str, Dict[str, float]]:
    """Get the combined lexicon for a language."""
    lang = lang.lower()[:2]

    if lang == "en":
        return ENGLISH_LEXICON
    elif lang == "es":
        return SPANISH_LEXICON
    elif lang == "pt":
        return PORTUGUESE_LEXICON
    else:
        return {}


def get_combined_phrases(lang: str) -> Dict[str, Dict[str, float]]:
    """Get the combined phrase lexicon for a language."""
    lang = lang.lower()[:2]

    if lang == "en":
        return ENGLISH_PHRASES
    elif lang == "es":
        return SPANISH_PHRASES
    elif lang == "pt":
        return PORTUGUESE_PHRASES
    else:
        return {}


def get_intensifiers(lang: str) -> Dict[str, float]:
    """Get intensifiers for a language."""
    lang = lang.lower()[:2]

    if lang == "en":
        return ENGLISH_INTENSIFIERS
    elif lang == "es":
        return SPANISH_INTENSIFIERS
    elif lang == "pt":
        return PORTUGUESE_INTENSIFIERS
    else:
        return {}


# =========================================================================
# SELF-HARM PATTERN COMPILATION
# =========================================================================

def compile_safety_patterns() -> Tuple[List[re.Pattern], List[re.Pattern]]:
    """
    Compile all self-harm patterns into regex objects.

    Returns:
        Tuple of (hard_patterns, soft_patterns) as compiled regexes
    """
    hard_patterns = []
    soft_patterns = []

    # Combine patterns from all languages
    all_hard = []
    all_soft = []

    for patterns_dict in [SELF_HARM_PATTERNS_EN, SELF_HARM_PATTERNS_ES, SELF_HARM_PATTERNS_PT]:
        all_hard.extend(patterns_dict.get("hard", []))
        all_soft.extend(patterns_dict.get("soft", []))

    # Compile with case-insensitivity and diacritic normalization
    for pattern in all_hard:
        try:
            # Strip diacritics from pattern for matching
            normalized_pattern = strip_diacritics(pattern)
            hard_patterns.append(
                re.compile(normalized_pattern, flags=re.IGNORECASE)
            )
        except re.error as e:
            logger.warning(f"Invalid regex pattern: {pattern} - {e}")

    for pattern in all_soft:
        try:
            normalized_pattern = strip_diacritics(pattern)
            soft_patterns.append(
                re.compile(normalized_pattern, flags=re.IGNORECASE)
            )
        except re.error as e:
            logger.warning(f"Invalid regex pattern: {pattern} - {e}")

    return hard_patterns, soft_patterns


def detect_crisis_indicators(text: str) -> Dict[str, bool]:
    """
    Detect crisis indicator categories in text.

    Returns dict with keys: urgency, finality, settling, trauma, help_seeking
    """
    text_lower = strip_diacritics(text.lower())
    results = {}

    for category, keywords in CRISIS_INDICATORS.items():
        results[category] = any(
            strip_diacritics(kw.lower()) in text_lower
            for kw in keywords
        )

    return results


# =========================================================================
# CONTEXT-AWARE ANALYSIS
# =========================================================================

def analyze_context(
    text: str,
    tokens: List[str],
    detected_lang: str,
) -> Dict[str, Any]:
    """
    Analyze contextual factors that may affect emotion interpretation.

    Returns context signals like:
    - negation presence
    - intensifier presence
    - question form
    - conditional/hypothetical
    """
    text_lower = text.lower()
    normalized = strip_diacritics(text_lower)

    # Negation detection
    negation_words = {
        "en": {"not", "no", "never", "dont", "doesn't", "didn't", "won't",
               "cant", "cannot", "hardly", "barely", "neither", "nor"},
        "es": {"no", "nunca", "jamás", "jamas", "tampoco", "ni", "ningún",
               "ningun", "ninguna", "nada", "nadie"},
        "pt": {"não", "nao", "nunca", "jamais", "nem", "nenhum", "nenhuma",
               "nada", "ninguém", "ninguem"},
    }

    lang = detected_lang.lower()[:2]
    neg_words = negation_words.get(lang, negation_words["en"])

    tokens_lower = [t.lower() for t in tokens]
    has_negation = any(strip_diacritics(w) in normalized for w in neg_words)

    # Intensifier detection
    intensifiers = get_intensifiers(lang)
    intensifier_score = 1.0
    for token in tokens_lower:
        norm_token = normalize_for_lookup(token)
        if norm_token in intensifiers:
            intensifier_score = max(intensifier_score, intensifiers[norm_token])

    # Question detection
    is_question = "?" in text or any(
        normalized.startswith(q)
        for q in ["is ", "are ", "do ", "does ", "can ", "will ", "would ",
                  "should ", "could ", "what ", "why ", "how ", "when ",
                  "es ", "está ", "esta ", "son ", "puede ", "puedo ",
                  "é ", "e ", "está ", "são ", "pode ", "posso "]
    )

    # Conditional/hypothetical
    conditional_markers = {
        "if ", "would ", "could ", "might ", "maybe ", "perhaps ",
        "si ", "podría ", "podria ", "quizás ", "quizas ", "tal vez ",
        "se ", "poderia ", "talvez ", "quem sabe ",
    }
    is_conditional = any(normalized.startswith(m) or f" {m}" in normalized
                         for m in conditional_markers)

    return {
        "has_negation": has_negation,
        "intensifier_score": intensifier_score,
        "is_question": is_question,
        "is_conditional": is_conditional,
    }


# =========================================================================
# INITIALIZATION
# =========================================================================

# Compile safety patterns on module load
COMPILED_HARD_PATTERNS, COMPILED_SOFT_PATTERNS = compile_safety_patterns()


def get_safety_patterns() -> Tuple[List[re.Pattern], List[re.Pattern]]:
    """Get compiled safety patterns."""
    return COMPILED_HARD_PATTERNS, COMPILED_SOFT_PATTERNS


def is_lexicons_loaded() -> bool:
    """Check if enhanced lexicons are available."""
    return LEXICONS_AVAILABLE


# Log lexicon status
if LEXICONS_AVAILABLE:
    logger.info(
        f"Enhanced lexicons loaded: "
        f"EN={len(ENGLISH_LEXICON)} words, "
        f"ES={len(SPANISH_LEXICON)} words, "
        f"PT={len(PORTUGUESE_LEXICON)} words"
    )
