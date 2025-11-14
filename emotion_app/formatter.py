# -*- coding: utf-8 -*-
from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from typing import Dict, List, Tuple, Optional, Any

from .detector import EmotionResult

EMOTIONS = ["anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"]
_IDX = {k: i for i, k in enumerate(EMOTIONS)}

# Expanded pair names with more nuanced emotional blends
PAIR_NAMES = {
    tuple(sorted(["anger", "disgust"])): "Contempt",
    tuple(sorted(["anger", "fear"])): "Outrage",
    tuple(sorted(["fear", "sadness"])): "Worry and sorrow",
    tuple(sorted(["joy", "sadness"])): "Nostalgia",
    tuple(sorted(["joy", "fear"])): "Awe",
    tuple(sorted(["joy", "disgust"])): "Schadenfreude",
    tuple(sorted(["joy", "surprise"])): "Delighted surprise",
    tuple(sorted(["fear", "surprise"])): "Shock",
    tuple(sorted(["anger", "surprise"])): "Indignant shock",
    tuple(sorted(["passion", "joy"])): "In love",
    tuple(sorted(["passion", "fear"])): "Aflutter",
}

# Expanded triad names for deeper subtleties
TRIAD_NAMES = {
    tuple(sorted(["anger", "disgust", "fear"])): "Moral outrage",
    tuple(sorted(["anger", "sadness", "fear"])): "Distress",
    tuple(sorted(["joy", "fear", "sadness"])): "Bittersweet anticipation",
    tuple(sorted(["joy", "sadness", "disgust"])): "Embarrassed amusement",
}

# Prototypes for nuanced blends across all cores
PROTOTYPES = {
    # Sadness and grief family
    "Gentle sadness":    [0.00, 0.00, 0.05, 0.10, 0.55, 0.00, 0.05],
    "Reflective sorrow": [0.00, 0.00, 0.10, 0.15, 0.70, 0.00, 0.05],
    "Hopeful grief":     [0.00, 0.00, 0.15, 0.25, 0.60, 0.10, 0.05],
    "Grief":             [0.05, 0.00, 0.05, 0.05, 0.70, 0.10, 0.05],
    "Mourning":          [0.05, 0.00, 0.05, 0.03, 0.80, 0.05, 0.02],
    "Heartbroken":       [0.20, 0.00, 0.02, 0.03, 0.55, 0.20, 0.00],

    # Romantic and affection spectrum
    "Soft affection":    [0.00, 0.00, 0.05, 0.55, 0.05, 0.60, 0.10],
    "Romantic yearning": [0.00, 0.00, 0.10, 0.20, 0.40, 0.85, 0.10],
    "In love":           [0.00, 0.00, 0.05, 0.55, 0.05, 0.75, 0.10],
    "Infatuated":        [0.05, 0.00, 0.05, 0.45, 0.05, 0.80, 0.10],

    # Anger family
    "Frustrated":        [0.45, 0.05, 0.05, 0.05, 0.30, 0.10, 0.00],
    "Outrage":           [0.60, 0.05, 0.15, 0.02, 0.12, 0.06, 0.00],
    "Contempt":          [0.40, 0.30, 0.05, 0.05, 0.15, 0.05, 0.00],

    # Fear and anxiety family
    "Anxious":           [0.05, 0.00, 0.60, 0.05, 0.20, 0.05, 0.05],
    "Panicked":          [0.10, 0.00, 0.65, 0.00, 0.15, 0.05, 0.05],
    "Terrified":         [0.15, 0.00, 0.70, 0.00, 0.10, 0.00, 0.05],

    # Joy and calm family
    "Joyful":            [0.02, 0.00, 0.02, 0.80, 0.05, 0.09, 0.02],
    "Bittersweet":       [0.00, 0.00, 0.05, 0.45, 0.40, 0.05, 0.05],
    "Calm":              [0.00, 0.00, 0.05, 0.60, 0.10, 0.15, 0.10],
}

# Expanded emoji set with deeper nuance and more richness
EMOJI_SUGGEST = {
    # Subtle and nuanced labels
    "Gentle sadness": ["🥹", "😢"],
    "Reflective sorrow": ["😔", "🥹"],
    "Hopeful grief": ["🥲"],
    "Grief": ["😢", "💐"],
    "Mourning": ["😢", "🖤"],
    "Heartbroken": ["💔", "😢"],
    "Soft affection": ["🤍", "🤗"],
    "Romantic yearning": ["💘"],
    "In love": ["😍"],
    "Infatuated": ["🥰"],

    # Rich blended labels and cores
    "Angry": ["😠"],
    "Disgusted": ["🤢"],
    "Anxious": ["😨"],
    "Panicked": ["😰"],
    "Terrified": ["😱"],
    "Joyful": ["😊"],
    "Bittersweet": ["🥲"],
    "Calm": ["😌"],
    "Sad": ["😢"],
    "Shocked": ["😱"],
    "Awe": ["😮", "✨"],
    "Nostalgia": ["🕰️", "🙂"],
    "Contempt": ["😒"],
    "Outrage": ["😡"],
    "Melancholy": ["🎻"],
    "Frustrated": ["😤"],
    "Irritated": ["😒"],
    "Resentful": ["😠"],
    "Appalled": ["😧"],
    "Uneasy": ["😬"],
    "Apprehensive": ["😟"],
    "Relief": ["😮‍💨"],
    "Delighted surprise": ["🤩"],
    "Indignant shock": ["😤", "😳"],
    "Moral outrage": ["😤"],
    "Schadenfreude": ["😏"],
    "Embarrassed amusement": ["😅"],
    "Affectionate": ["🤗"],
    "Hopeful": ["🌟"],
    "N/A": ["❌"],

    # Direct mappings for the seven core names so dominant emojis always resolve
    "Anger": ["😠"],
    "Disgust": ["🤢"],
    "Fear": ["😨"],
    "Joy": ["😊"],
    "Sadness": ["😢"],
    "Passion": ["😍"],
    "Surprise": ["😱"],
}

# Helper numeric routines
def _normalize(scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0, scores.get(k, 0)) for k in EMOTIONS)
    if total <= 0:
        return {k: 0 for k in EMOTIONS}
    return {k: max(0, scores.get(k, 0)) / total for k in EMOTIONS}

def _entropy(p: Dict[str, float]) -> float:
    eps = 1e-12
    return -sum(pi * math.log(pi + eps) for pi in p.values() if pi > 0)

def _confidence(p: Dict[str, float]) -> float:
    total = sum(p.values())
    if total <= 0:
        return 0.0
    h = _entropy(p)
    hmax = math.log(len(EMOTIONS))
    return max(0.0, min(1.0, 1.0 - h / hmax))

def _top_components(p: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(p.items(), key=lambda x: x[1], reverse=True)

def _title(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s

def _round3(x: float) -> float:
    return float(f"{x:.3f}")

def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def _norm(v: List[float]) -> float:
    n = math.sqrt(sum(x * x for x in v))
    return n if n > 0 else 1.0

def _cos(a: List[float], b: List[float]) -> float:
    return _dot(a, b) / (_norm(a) * _norm(b))

def _vector(p: Dict[str, float]) -> List[float]:
    return [p[k] for k in EMOTIONS]


# ---------------- Enhanced single state and blend overrides ----------------

def _single_state_overrides(p: Dict[str, float]) -> Optional[str]:
    ranked = _top_components(p)
    k1, v1 = ranked[0]
    k2, v2 = ranked[1]

    ang = p["anger"]
    sad = p["sadness"]
    joy = p["joy"]
    pas = p["passion"]
    fear = p["fear"]
    sur = p["surprise"]
    disg = p["disgust"]

    # Heartbreak: strong sadness with betrayal tone from anger or passion
    if sad >= 0.40 and joy <= 0.12 and (ang >= 0.15 or pas >= 0.18):
        return "Heartbroken"

    # Grief family
    if sad >= 0.55 and joy <= 0.20:
        if pas >= 0.20:
            return "Hopeful grief"
        if sad >= 0.70:
            return "Mourning"
        return "Grief"

    # Romantic spectrum
    if pas >= 0.60 and joy >= 0.25:
        return "In love"
    if pas >= 0.55 and sad >= 0.25:
        return "Romantic yearning"
    if pas >= 0.50 and joy >= 0.40:
        return "Soft affection"

    # Gentle sadness
    if sad >= 0.40 and joy >= 0.10 and pas < 0.18:
        return "Gentle sadness"

    # Anger family patterns
    if k1 == "anger" and v1 >= 0.45:
        if sad >= 0.25:
            return "Frustrated"
        if disg >= 0.20:
            return "Contempt"
        if fear >= 0.20:
            return "Outrage"

    # Fear family patterns
    if k1 == "fear" and v1 >= 0.45:
        if sur >= 0.25:
            return "Panicked"
        if joy <= 0.12 and sad <= 0.30:
            return "Anxious"

    # Joy family patterns
    if k1 == "joy" and v1 >= 0.50:
        if pas >= 0.30:
            return "In love"
        if sad >= 0.20:
            return "Bittersweet"
        if ang <= 0.10 and fear <= 0.10 and sad <= 0.15:
            return "Joyful"

    # Surprise family
    if k1 == "surprise" and v1 >= 0.50:
        if fear >= 0.25:
            return "Shocked"
        if joy >= 0.25:
            return "Delighted surprise"

    # Calm mixed positive
    if joy >= 0.40 and pas >= 0.15 and sad <= 0.20 and ang <= 0.15 and fear <= 0.15:
        return "Calm"

    return None


# ---------------- Blended label logic ----------------

def _blend_name(p: Dict[str, float]) -> str:
    ranked = _top_components(p)
    k1, v1 = ranked[0]
    k2, v2 = ranked[1]
    k3, v3 = ranked[2]

    # Dominant clear
    if v1 >= 0.60 and (v1 - v2) >= 0.15:
        return _title(k1)

    # Pair
    if (v1 + v2) >= 0.65 and abs(v1 - v2) <= 0.20:
        pair = tuple(sorted([k1, k2]))
        return PAIR_NAMES.get(pair, f"{_title(k1)} and {_title(k2)}")

    # Triad
    if (v1 + v2 + v3) >= 0.80 and v1 < 0.50:
        tri = tuple(sorted([k1, k2, k3]))
        return TRIAD_NAMES.get(tri, "Mixed state")

    # Soft blends
    if v1 < 0.35:
        return "Subtle blend"

    return f"{_title(k1)} leaning {_title(k2)}"


# ---------------- Rich label selection ----------------

def _best_prototype(p: Dict[str, float]) -> Tuple[str, float]:
    v = _vector(p)
    best = "N/A"
    bestsim = -1.0
    for label, proto in PROTOTYPES.items():
        sim = _cos(v, proto)
        if sim > bestsim:
            bestsim = sim
            best = label
    return best, bestsim

def _final_emotion_label(p: Dict[str, float]) -> str:
    total = sum(p.values())
    if total <= 0:
        return "N/A"

    override = _single_state_overrides(p)
    if override:
        return override

    ranked = _top_components(p)
    k1, v1 = ranked[0]
    k2, v2 = ranked[1]

    if {"passion", "joy"} == {k1, k2} and (v1 + v2) >= 0.55:
        return "In love"

    conf = _confidence(p)
    if v1 >= 0.20 and conf >= 0.12:
        label, sim = _best_prototype(p)
        if sim >= 0.68:
            return label

    if v1 < 0.20:
        return "N/A"

    return _title(k1)


# ---------------- Emoji helpers ----------------

def _emoji_for(label: str) -> List[str]:
    if label in EMOJI_SUGGEST:
        return EMOJI_SUGGEST[label]
    titled = _title(label)
    if titled in EMOJI_SUGGEST:
        return EMOJI_SUGGEST[titled]
    return ["❌"]

def _emoji_core(core: str) -> List[str]:
    return _emoji_for(_title(core))

def _resolve_emoji_pair(emoji_dom: List[str], emoji_em: List[str]) -> Tuple[List[str], List[str]]:
    """Ensure dominant emoji appears first and avoid duplication when possible."""
    if not emoji_dom:
        emoji_dom = ["❌"]
    if not emoji_em:
        emoji_em = ["❌"]

    dom = emoji_dom[0]
    cur = emoji_em[0]

    if dom == cur:
        # Try alternate for current label first
        if len(emoji_em) > 1 and emoji_em[1] != dom:
            cur = emoji_em[1]
        elif len(emoji_dom) > 1 and emoji_dom[1] != cur:
            dom = emoji_dom[1]

    return [dom], [cur]


# ---------------- Public formatter ----------------

def format_emotions(result: Any) -> Dict[str, Any]:
    if is_dataclass(result):
        base = asdict(result)
    elif isinstance(result, dict):
        base = dict(result)
    else:
        base = {}

    # Ensure all seven core scores are present as floats
    for k in EMOTIONS:
        base[k] = float(base.get(k, 0.0))

    raw = {k: base[k] for k in EMOTIONS}
    total_signal = sum(raw.values())
    low_signal_flag = bool(base.get("low_signal", False)) or total_signal <= 0.0

    if low_signal_flag:
        out = {k: 0.0 for k in EMOTIONS}
        return {
            **raw,
            "dominant_emotion": "N/A",
            "secondary_emotion": "N/A",
            "mixed_state": False,
            "blended_emotion": "N/A",
            "emotion": "N/A",
            "confidence": 0.0,
            "mixture": out,
            "present": {},
            "components": [],
            "emoji_emotion": ["❌"],
            "emoji_dominant": ["❌"],
            "same_label": True,
            "rationale": "Input contained too little usable language.",
            "low_signal": True,
            "emoji": ["❌"],
            "emoji_primary": "❌",
        }

    # Normalized mixture for prototype and blend logic
    p = _normalize(raw)
    blended = _blend_name(p)
    final_single = _final_emotion_label(p)
    conf = _confidence(p)

    ranked = _top_components(raw)

    # Use detector supplied dominance when available so UI and backend agree
    detector_dom = base.get("dominant_emotion") or "N/A"
    if detector_dom in EMOTIONS:
        dominant = detector_dom
    else:
        dominant = ranked[0][0] if ranked else "N/A"

    secondary = base.get("secondary_emotion", "N/A")
    mixed_state = bool(base.get("mixed_state", False))

    # Base emojis for current label and dominant core
    emoji_em = _emoji_for(final_single)
    emoji_dom = _emoji_core(dominant) if dominant != "N/A" else ["❌"]

    # Special tuning for sadness based families so icons show nuance not duplication
    if dominant == "sadness":
        sadness_override = {
            "Hopeful grief": ["😢"],
            "Gentle sadness": ["🥹"],
            "Reflective sorrow": ["😔"],
            "Grief": ["😢"],
            "Mourning": ["😢"],
            "Heartbroken": ["😢"],
        }
        if final_single in sadness_override:
            emoji_dom = sadness_override[final_single]

    # Final pass to ensure dominant then current and avoid duplicate faces
    emoji_dom, emoji_em = _resolve_emoji_pair(emoji_dom, emoji_em)

    mixture = {k: _round3(v) for k, v in p.items()}
    components = [[k, _round3(v)] for k, v in sorted(p.items(), key=lambda x: -x[1])]

    top3 = ", ".join(
        f"{_title(k)} {_round3(v)}" for k, v in _top_components(p)[:3]
    )
    rationale = (
        f"Top components: {top3}. "
        f"Dominant core is {_title(dominant)}. "
        f"Secondary core is {_title(secondary) if secondary != 'N/A' else 'none'}. "
        f"Rich label reflects blended meaning: {final_single}. "
        f"Context blend: {blended}."
    )

    return {
        **raw,
        "dominant_emotion": dominant,
        "secondary_emotion": secondary,
        "mixed_state": mixed_state,
        "blended_emotion": blended,
        "emotion": final_single,
        "confidence": _round3(conf),
        "mixture": mixture,
        "present": {k: _round3(v) for k, v in p.items() if v >= 0.03},
        "components": components,
        "emoji_emotion": emoji_em,
        "emoji_dominant": emoji_dom,
        "same_label": dominant == final_single,
        "rationale": rationale,
        "low_signal": False,
        "emoji": emoji_em,
        "emoji_primary": emoji_dom[0] if emoji_dom else "❌",
    }
