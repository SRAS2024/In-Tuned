# detector/lexicons/__init__.py
"""
Enhanced Lexicon Module for Emotion Detection

This module provides comprehensive lexicons for emotion detection across
English, Spanish, and Portuguese, including:
- Modern slang and colloquialisms
- Internet/social media speak
- Pop culture references
- Regional variations
- Conjugation patterns
- Idiomatic expressions
"""

from .english import ENGLISH_LEXICON, ENGLISH_PHRASES, ENGLISH_INTENSIFIERS
from .spanish import SPANISH_LEXICON, SPANISH_PHRASES, SPANISH_INTENSIFIERS
from .portuguese import PORTUGUESE_LEXICON, PORTUGUESE_PHRASES, PORTUGUESE_INTENSIFIERS
from .safety import (
    SELF_HARM_PATTERNS_EN,
    SELF_HARM_PATTERNS_ES,
    SELF_HARM_PATTERNS_PT,
    CRISIS_INDICATORS,
)

__all__ = [
    "ENGLISH_LEXICON",
    "ENGLISH_PHRASES",
    "ENGLISH_INTENSIFIERS",
    "SPANISH_LEXICON",
    "SPANISH_PHRASES",
    "SPANISH_INTENSIFIERS",
    "PORTUGUESE_LEXICON",
    "PORTUGUESE_PHRASES",
    "PORTUGUESE_INTENSIFIERS",
    "SELF_HARM_PATTERNS_EN",
    "SELF_HARM_PATTERNS_ES",
    "SELF_HARM_PATTERNS_PT",
    "CRISIS_INDICATORS",
]
