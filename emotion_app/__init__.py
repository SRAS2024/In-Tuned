# emotion_app/__init__.py
"""
Public package interface for emotion_app.

Exports a stable API for the rest of the app, regardless of internal function
names in detector.py (detect_emotions vs emotion_detector).
"""

from __future__ import annotations

import importlib
from typing import Any

# --- Load detector lazily to avoid hard import failures at package import time ---
_det = importlib.import_module(".detector", __name__)

# Export dataclass (required)
try:
    EmotionResult = getattr(_det, "EmotionResult")
except AttributeError as exc:
    raise ImportError("EmotionResult not found in emotion_app.detector") from exc

# Find a callable detector by common names and expose it as `_emotion_fn`
_emotion_fn = (
    getattr(_det, "emotion_detector", None)
    or getattr(_det, "detect_emotions", None)
    or getattr(_det, "analyze_emotions", None)
)
if _emotion_fn is None or not callable(_emotion_fn):
    raise ImportError(
        "No callable emotion detector found in emotion_app.detector. "
        "Define def detect_emotions(text: str) -> EmotionResult (or emotion_detector)."
    )

# --- Errors (primary definitions or fallbacks) ---
try:
    _err = importlib.import_module(".errors", __name__)
    InvalidTextError = getattr(_err, "InvalidTextError")
    ServiceUnavailableError = getattr(_err, "ServiceUnavailableError")
except Exception:
    class InvalidTextError(ValueError):  # type: ignore
        """Raised when input text is missing or invalid."""
        pass

    class ServiceUnavailableError(RuntimeError):  # type: ignore
        """Raised when the external service cannot be reached."""
        pass


def _normalize_text(text: Any) -> str:
    """Coerce input to a string for the detector."""
    if text is None:
        return ""
    return str(text)


def emotion_detector(text: Any) -> EmotionResult:
    """Stable public entry point.

    Responsibilities:
      - Coerce input to string
      - Enforce nonempty text and raise InvalidTextError on blanks
      - Translate low level ValueError or connectivity issues into
        InvalidTextError or ServiceUnavailableError
    """
    s = _normalize_text(text)
    if not s.strip():
        raise InvalidTextError("Input text is required and cannot be blank.")

    try:
        # Most detectors use the simple signature `text: str`
        return _emotion_fn(s)  # type: ignore[misc]
    except InvalidTextError:
        # Already in the unified error type
        raise
    except ValueError as exc:
        # Any validation style ValueError from the underlying model
        raise InvalidTextError(str(exc)) from exc
    except RuntimeError as exc:
        # Treat generic runtime issues as service availability problems
        raise ServiceUnavailableError(str(exc)) from exc


# --- Formatter (optional but recommended) ---
try:
    _fmt = importlib.import_module(".formatter", __name__)
    format_emotions = getattr(_fmt, "format_emotions")
except Exception:
    # Safe fallback: return the dataclass as a dict if formatter not available
    def format_emotions(result: Any):  # type: ignore
        try:
            return result.to_dict()  # type: ignore[attr-defined]
        except Exception:
            return vars(result)


__all__ = [
    "EmotionResult",
    "emotion_detector",
    "format_emotions",
    "InvalidTextError",
    "ServiceUnavailableError",
]
