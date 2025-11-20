# detector/detector.py
# High fidelity local emotion detector v8-espt
# Seven core emotions, 1–250 words, English / Spanish / Portuguese only.

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, asdict
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any


# =============================================================================
# Public API
# =============================================================================


EMOTIONS: Tuple[str, ...] = (
    "anger",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "passion",
    "surprise",
)


class InvalidTextError(ValueError):
    """Raised when the input text is empty, too long, or otherwise invalid."""


@dataclass
class EmotionResult:
    label: str
    emoji: str
    score: float
    percent: float


@dataclass
class DetectorOutput:
    text: str
    language: Dict[str, float]
    emotions: Dict[str, EmotionResult]
    mixture_vector: Dict[str, float]
    dominant: EmotionResult
    current: EmotionResult
    arousal: float
    sarcasm: float
    confidence: float
    risk_level: str
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # EmotionResult objects are already converted by asdict
        return result


# =============================================================================
# Core data: lexicons, intensifiers, etc.
# =============================================================================


def _vec(**kwargs: float) -> Dict[str, float]:
    """Convenience for small emotion vectors."""
    v = {e: 0.0 for e in EMOTIONS}
    for k, val in kwargs.items():
        if k in v:
            v[k] = float(val)
    return v


# Base lexicon (not exhaustive, but tuned for common expressions)
# Each token maps to an emotion vector; language specific dictionaries.
LEXICON_TOKEN: Dict[str, Dict[str, Dict[str, float]]] = {
    "en": {},
    "es": {},
    "pt": {},
}

# Simple helper to register many words with same emotion
def _register_words(lang: str, emotion: str, words: List[str], base: float) -> None:
    table = LEXICON_TOKEN[lang]
    for w in words:
        wl = w.lower()
        vec = table.get(wl, _vec())
        vec[emotion] = vec.get(emotion, 0.0) + base
        table[wl] = vec


# English
_register_words(
    "en",
    "anger",
    [
        "angry",
        "mad",
        "furious",
        "irritated",
        "annoyed",
        "pissed",
        "pissedoff",
        "rage",
        "raging",
        "hate",
        "hated",
        "hates",
        "hating",
        "resent",
        "resentful",
        "frustrated",
        "upset",
    ],
    2.2,
)
_register_words(
    "en",
    "disgust",
    [
        "disgusted",
        "gross",
        "nasty",
        "disgusting",
        "revolting",
        "sickening",
        "sickened",
        "queasy",
        "repulsed",
        "yuck",
        "ew",
        "eww",
    ],
    2.1,
)
_register_words(
    "en",
    "fear",
    [
        "afraid",
        "scared",
        "terrified",
        "terrifying",
        "anxious",
        "anxiety",
        "worried",
        "worry",
        "panic",
        "panicking",
        "petrified",
        "nervous",
        "frightened",
    ],
    2.2,
)
_register_words(
    "en",
    "joy",
    [
        "happy",
        "happier",
        "happiest",
        "glad",
        "grateful",
        "thankful",
        "delighted",
        "excited",
        "joyful",
        "joy",
        "content",
        "satisfied",
        "smiling",
        "smile",
        "lol",
        "lmao",
        "haha",
        "hahaha",
    ],
    2.0,
)
_register_words(
    "en",
    "sadness",
    [
        "sad",
        "sadder",
        "saddest",
        "down",
        "depressed",
        "unhappy",
        "miserable",
        "heartbroken",
        "lonely",
        "alone",
        "crying",
        "cried",
        "cries",
        "tearful",
        "blue",
        "grief",
        "grieving",
    ],
    2.2,
)
_register_words(
    "en",
    "passion",
    [
        "love",
        "loved",
        "loving",
        "inlove",
        "crush",
        "obsessed",
        "desire",
        "desiring",
        "horny",
        "attracted",
        "attraction",
        "adorable",
        "adoring",
        "hot",
        "sexy",
    ],
    2.3,
)
_register_words(
    "en",
    "surprise",
    [
        "surprised",
        "shocked",
        "amazed",
        "wow",
        "whoa",
        "omg",
        "cantbelieve",
        "unexpected",
        "nooo",
        "what",
        "wtf",
        "no_way",
    ],
    2.1,
)

# Spanish
_register_words(
    "es",
    "anger",
    [
        "enojado",
        "enojada",
        "enojados",
        "furioso",
        "furiosa",
        "molesto",
        "molesta",
        "rabia",
        "odio",
        "odiar",
        "frustrado",
        "frustrada",
    ],
    2.2,
)
_register_words(
    "es",
    "disgust",
    [
        "asco",
        "asqueroso",
        "asquerosa",
        "repugnante",
        "repulsivo",
        "repulsiva",
        "me_da_asco",
    ],
    2.1,
)
_register_words(
    "es",
    "fear",
    [
        "miedo",
        "asustado",
        "asustada",
        "aterrado",
        "aterrada",
        "ansioso",
        "ansiosa",
        "ansiedad",
        "preocupado",
        "preocupada",
        "nervioso",
        "nerviosa",
        "pánico",
    ],
    2.2,
)
_register_words(
    "es",
    "joy",
    [
        "feliz",
        "contento",
        "contenta",
        "alegre",
        "alegría",
        "emocionado",
        "emocionada",
        "agradecido",
        "agradecida",
        "sonriendo",
        "jaja",
        "jajaja",
    ],
    2.0,
)
_register_words(
    "es",
    "sadness",
    [
        "triste",
        "tristes",
        "deprimido",
        "deprimida",
        "infeliz",
        "solo",
        "sola",
        "soledad",
        "llorando",
        "llorar",
        "lloré",
        "lloré",
        "pena",
        "dolor",
    ],
    2.2,
)
_register_words(
    "es",
    "passion",
    [
        "amor",
        "amo",
        "amas",
        "amamos",
        "apasionado",
        "apasionada",
        "enamorado",
        "enamorada",
        "deseo",
        "deseando",
        "atracción",
        "te_quiero",
        "te_amo",
    ],
    2.3,
)
_register_words(
    "es",
    "surprise",
    [
        "sorprendido",
        "sorprendida",
        "choqueado",
        "impactado",
        "wow",
        "guau",
        "no_lo_creo",
        "increíble",
    ],
    2.1,
)

# Portuguese
_register_words(
    "pt",
    "anger",
    [
        "bravo",
        "brava",
        "irritado",
        "irritada",
        "com_raiva",
        "raiva",
        "odiar",
        "odeio",
        "ódio",
        "frustrado",
        "frustrada",
        "puto",
        "puta_da_vida",
    ],
    2.2,
)
_register_words(
    "pt",
    "disgust",
    [
        "nojo",
        "nojento",
        "nojenta",
        "asco",
        "repugnante",
        "que_nojo",
    ],
    2.1,
)
_register_words(
    "pt",
    "fear",
    [
        "medo",
        "assustado",
        "assustada",
        "aterrorizado",
        "aterrorizada",
        "ansioso",
        "ansiosa",
        "ansiedade",
        "preocupado",
        "preocupada",
        "nervoso",
        "nervosa",
        "pânico",
    ],
    2.2,
)
_register_words(
    "pt",
    "joy",
    [
        "feliz",
        "contente",
        "alegre",
        "alegria",
        "animado",
        "animada",
        "empolgado",
        "empolgada",
        "grato",
        "grata",
        "obrigado",
        "obrigada",
        "kkk",
        "kkkk",
        "haha",
        "hahaha",
    ],
    2.0,
)
_register_words(
    "pt",
    "sadness",
    [
        "triste",
        "tristes",
        "deprimido",
        "deprimida",
        "infeliz",
        "sozinho",
        "sozinha",
        "solidão",
        "chorando",
        "chorei",
        "chorar",
        "mágoa",
        "dor",
    ],
    2.2,
)
_register_words(
    "pt",
    "passion",
    [
        "amor",
        "amo",
        "ama",
        "amamos",
        "apaixonado",
        "apaixonada",
        "tesão",
        "desejo",
        "desejando",
        "gostoso",
        "gostosa",
        "te_amo",
        "te_adoro",
    ],
    2.3,
)
_register_words(
    "pt",
    "surprise",
    [
        "surpreso",
        "surpresa",
        "chocado",
        "chocada",
        "uau",
        "nossa",
        "caramba",
        "não_acredito",
        "meu_deus",
    ],
    2.1,
)

# Multiword phrase lexicon (normalized with underscores or joined tokens)
PHRASE_LEXICON: Dict[str, Dict[str, float]] = {
    # English
    "on cloud nine": _vec(joy=3.0),
    "sick to my stomach": _vec(disgust=2.5, fear=1.0),
    "heart broken": _vec(sadness=3.0),
    "heartbroken": _vec(sadness=3.0),
    "to die for": _vec(passion=2.0, joy=1.0),
    "i hate you": _vec(anger=3.0, disgust=1.5),
    "i hate myself": _vec(anger=2.0, sadness=2.0),
    "i am done": _vec(sadness=2.0, anger=1.0),
    # Spanish
    "no aguanto más": _vec(anger=1.5, sadness=2.0),
    "no lo soporto": _vec(anger=2.0, disgust=1.0),
    "me rompe el corazón": _vec(sadness=3.0),
    "me parte el corazón": _vec(sadness=3.0),
    # Portuguese
    "não aguento mais": _vec(anger=1.5, sadness=2.0),
    "me parte o coração": _vec(sadness=3.0),
    "me parte meu coração": _vec(sadness=3.0),
}

# Intensifiers and diminishers
INTENSIFIERS = {
    "en": {
        "very",
        "really",
        "so",
        "super",
        "extremely",
        "incredibly",
        "totally",
        "absolutely",
        "completely",
        "too",
        "sooo",
        "soooo",
    },
    "es": {"muy", "re", "súper", "super", "demasiado", "tan"},
    "pt": {"muito", "super", "demais", "tão", "pra", "bastante"},
}
DIMINISHERS = {
    "en": {"kind", "kinda", "sort", "little", "bit"},
    "es": {"un", "poco", "algo"},
    "pt": {"um", "pouco", "meio"},
}

NEGATIONS = {
    "en": {"not", "never", "no", "dont", "don't", "isnt", "isn't", "cant", "can't", "wont", "won't", "nothing"},
    "es": {"no", "nunca", "jamás", "nada"},
    "pt": {"não", "nem", "nunca", "jamais"},
}

CONTRAST_WORDS = {
    "en": {"but", "however", "though", "yet"},
    "es": {"pero", "sin", "embargo", "aunque"},
    "pt": {"mas", "porém", "contudo", "embora"},
}

PROFANITIES = {
    "en": {"fuck", "fucking", "shit", "bitch", "asshole", "damn"},
    "es": {"mierda", "joder", "carajo", "puta", "pendejo"},
    "pt": {"merda", "porra", "caralho", "puta", "bosta"},
}

# Language function words for detection
LANG_FUNCTION_WORDS = {
    "en": {"the", "and", "is", "am", "are", "you", "i", "my", "me", "it", "of", "to", "in"},
    "es": {"el", "la", "los", "las", "y", "es", "soy", "eres", "estoy", "yo", "tú", "mi", "me"},
    "pt": {"o", "a", "os", "as", "e", "é", "sou", "estou", "você", "voce", "eu", "meu", "minha"},
}

# Emoji mappings
BASE_EMOJI = {
    "anger": "😡",
    "disgust": "🤢",
    "fear": "😨",
    "joy": "😄",
    "sadness": "😢",
    "passion": "😍",
    "surprise": "😲",
}

AROUSAL_EMOJI = {
    "fear": "😱",
    "surprise": "😱",
    "anger": "🤬",
    "sadness": "😭",
    "disgust": "🤮",
}

# Self harm / suicide risk patterns
SELF_HARM_PATTERNS = [
    # English
    r"\bkill myself\b",
    r"\bkill me\b",
    r"\bwant to die\b",
    r"\bwant to disappear\b",
    r"\bend my life\b",
    r"\bno reason to live\b",
    r"\bself[-\s]?harm\b",
    r"\bhurt myself\b",
    r"\bsuicide\b",
    # Spanish
    r"\bquiero morir\b",
    r"\bno quiero vivir\b",
    r"\bquitarme la vida\b",
    r"\bmat(?:arme|arme)\b",
    r"\bsuicidio\b",
    r"\bhacerme daño\b",
    r"\bautolesi",
    # Portuguese
    r"\bquero morrer\b",
    r"\bnão quero viver\b",
    r"\bme matar\b",
    r"\btirar minha vida\b",
    r"\bsuic[ií]dio\b",
    r"\bauto[-\s]?mutila",
    r"\bauto[-\s]?les",
]

SELF_HARM_REGEX = [re.compile(pat, flags=re.IGNORECASE) for pat in SELF_HARM_PATTERNS]

# Beta coefficients for arousal boosting
AROUSAL_BETA = {
    "anger": 0.9,
    "disgust": 0.5,
    "fear": 0.9,
    "joy": 0.7,
    "sadness": 0.3,
    "passion": 0.8,
    "surprise": 1.0,
}


# =============================================================================
# Utility functions
# =============================================================================


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    # Normalize common apostrophes etc.
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    return text.strip()


TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text)


def is_emoji(char: str) -> bool:
    if not char:
        return False
    cp = ord(char)
    # Basic ranges for emoji
    return (
        0x1F300 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x26FF
        or 0x2700 <= cp <= 0x27BF
        or 0xFE00 <= cp <= 0xFE0F
    )


def join_for_lex(token: str) -> str:
    """Normalize token for lexicon lookups: lower, remove accents, join spaces."""
    token = token.lower()
    token = unicodedata.normalize("NFD", token)
    token = "".join(ch for ch in token if unicodedata.category(ch) != "Mn")
    token = token.replace(" ", "_")
    return token


def detect_word_count(tokens: List[str]) -> int:
    count = 0
    for t in tokens:
        if any(ch.isalpha() for ch in t):
            count += 1
    return count


@lru_cache(maxsize=8192)
def detect_language_proportions(text: str) -> Dict[str, float]:
    tokens = [t.lower() for t in tokenize(text)]
    if not tokens:
        return {"en": 1 / 3, "es": 1 / 3, "pt": 1 / 3, "unknown": 0.0}

    scores = {"en": 0.0, "es": 0.0, "pt": 0.0}

    for tok in tokens:
        base = join_for_lex(tok)
        for lang, fn_words in LANG_FUNCTION_WORDS.items():
            if base in fn_words:
                scores[lang] += 1.5
        # Character based hints
        if "ñ" in tok or "¿" in tok or "¡" in tok:
            scores["es"] += 1.2
        if any(ch in tok for ch in ["ã", "õ", "ç", "ê", "ô"]):
            scores["pt"] += 1.2
        if any(ch in tok for ch in ["th", "ing"]):
            scores["en"] += 0.4

    total = sum(scores.values())
    if total <= 0:
        return {"en": 1 / 3, "es": 1 / 3, "pt": 1 / 3, "unknown": 0.0}

    for k in list(scores.keys()):
        scores[k] = scores[k] / total

    scores["unknown"] = 0.0
    return scores


def detect_self_harm_risk(text: str) -> str:
    text_norm = normalize_text(text).lower()
    hits = 0
    for rx in SELF_HARM_REGEX:
        if rx.search(text_norm):
            hits += 1
    if hits == 0:
        return "none"
    if hits == 1:
        return "possible"
    if hits == 2:
        return "likely"
    return "severe"


def compute_sarcasm_probability(text: str, mixture_hint: Optional[Dict[str, float]] = None) -> float:
    t = text.lower()
    score = 0.0

    patterns = [
        "yeah right",
        "as if",
        "/s",
        "sure,",
        "sure.",
        "totally",
        '"sure"',
        "claro que sí",
        "claro que nao",
        "claro que não",
    ]
    for p in patterns:
        if p in t:
            score += 0.4

    # Positive words with "lol/lmao" next to clearly negative expressions
    if "lol" in t or "lmao" in t or "jaja" in t or "kkk" in t:
        if any(w in t for w in ["hate", "sad", "cry", "triste", "deprimido", "deprimida", "triste", "sozinho"]):
            score += 0.3

    if mixture_hint:
        # Very mixed strong positive and strong negative is suspicious
        pos = mixture_hint.get("joy", 0.0) + mixture_hint.get("passion", 0.0)
        neg = mixture_hint.get("anger", 0.0) + mixture_hint.get("sadness", 0.0) + mixture_hint.get("disgust", 0.0)
        if pos > 0.25 and neg > 0.25:
            score += 0.2

    return max(0.0, min(1.0, score))


def choose_emoji(
    emotion: str, mixture: Dict[str, float], arousal: float, sarcasm_prob: float
) -> str:
    base = BASE_EMOJI.get(emotion, "😐")

    # Sarcastic joy tends to become 🙃
    if emotion == "joy" and sarcasm_prob > 0.55:
        return "🙃"

    # Blends and arousal tweaks
    if arousal > 0.6:
        if emotion in ("fear", "surprise"):
            return AROUSAL_EMOJI["fear"]
        if emotion == "anger":
            if mixture.get("disgust", 0.0) > 0.25:
                return "😤"
            return AROUSAL_EMOJI["anger"]
        if emotion == "sadness":
            return AROUSAL_EMOJI["sadness"]
        if emotion == "disgust":
            return AROUSAL_EMOJI["disgust"]

    if emotion == "passion" and mixture.get("joy", 0.0) > 0.25:
        return "🥰"

    if emotion == "anger" and mixture.get("disgust", 0.0) > 0.25:
        return "😤"

    return base


# =============================================================================
# Emotion detector implementation
# =============================================================================


class EmotionDetector:
    """Local emotion detector for EN / ES / PT with seven core emotions."""

    def __init__(self, max_words: int = 250) -> None:
        self.max_words = max_words

    def analyze(self, text: str, domain: Optional[str] = None) -> DetectorOutput:
        if not isinstance(text, str):
            raise InvalidTextError("Text must be a string.")
        text = normalize_text(text)
        if not text:
            raise InvalidTextError("Text cannot be empty.")

        tokens = tokenize(text)
        word_count = detect_word_count(tokens)
        truncated = False
        if word_count == 0:
            raise InvalidTextError("No meaningful words found in text.")

        if word_count > self.max_words:
            truncated = True
            # Truncate naive by words, not tokens
            trimmed_tokens: List[str] = []
            wc = 0
            for tok in tokens:
                trimmed_tokens.append(tok)
                if any(ch.isalpha() for ch in tok):
                    wc += 1
                    if wc >= self.max_words:
                        break
            tokens = trimmed_tokens
            text = "".join(tokens)
            word_count = self.max_words

        lang_props = detect_language_proportions(text)
        # Merge language specific sets for negation/intensity decisions
        all_negations = set().union(*NEGATIONS.values())
        all_intens = set().union(*INTENSIFIERS.values())
        all_dimins = set().union(*DIMINISHERS.values())
        all_contrast = set().union(*CONTRAST_WORDS.values())
        all_profanities = set().union(*PROFANITIES.values())

        # ------------------------------------------------------------------
        # Global features
        # ------------------------------------------------------------------
        exclam_count = text.count("!")
        question_count = text.count("?")
        allcaps_count = 0
        elongated_count = 0
        profanity_count = 0
        strong_emoji_count = 0

        token_low = [tok.lower() for tok in tokens]

        for tok in tokens:
            if len(tok) > 2 and tok.isupper() and any(ch.isalpha() for ch in tok):
                allcaps_count += 1
            # Elongated characters (e.g., sooo, nooo)
            if re.search(r"(.)\1\1", tok, flags=re.IGNORECASE):
                elongated_count += 1
            if join_for_lex(tok) in all_profanities:
                profanity_count += 1
            if len(tok) == 1 and is_emoji(tok):
                strong_emoji_count += 1

        # Phrase level contributions
        R_global = {e: 0.0 for e in EMOTIONS}
        text_lower = text.lower()
        for phrase, vec in PHRASE_LEXICON.items():
            if phrase in text_lower:
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0)

        # Contrast weighting: later clauses after "but", "pero", "mas" etc.
        contrast_index = -1
        for idx, tok in enumerate(token_low):
            if join_for_lex(tok) in all_contrast:
                contrast_index = idx

        # ------------------------------------------------------------------
        # Token level scoring
        # ------------------------------------------------------------------
        R = {e: R_global[e] for e in EMOTIONS}

        for i, tok in enumerate(tokens):
            tok_norm = join_for_lex(tok)
            if not any(ch.isalpha() for ch in tok) and not is_emoji(tok):
                continue

            # Base emotion vector from lexicon combining languages
            base_vec = {e: 0.0 for e in EMOTIONS}
            for lang, weight in lang_props.items():
                if lang not in LEXICON_TOKEN:
                    continue
                table = LEXICON_TOKEN[lang]
                if tok_norm in table:
                    for e in EMOTIONS:
                        base_vec[e] += table[tok_norm].get(e, 0.0) * weight

            # Emojis as direct emotion cues
            if len(tok) == 1 and is_emoji(tok):
                cp = tok
                if cp in {"😡", "🤬"}:
                    base_vec["anger"] += 2.5
                elif cp in {"🤢", "🤮"}:
                    base_vec["disgust"] += 2.5
                elif cp in {"😨", "😰", "😱"}:
                    base_vec["fear"] += 2.5
                elif cp in {"😄", "😊", "😁", "😂", "🤣"}:
                    base_vec["joy"] += 2.5
                elif cp in {"😢", "😭"}:
                    base_vec["sadness"] += 2.5
                elif cp in {"😍", "🥰", "😘", "😻"}:
                    base_vec["passion"] += 2.5
                elif cp in {"😲", "😳", "🙀"}:
                    base_vec["surprise"] += 2.5

            # Skip if no emotional content
            if all(val == 0.0 for val in base_vec.values()):
                continue

            # Intensity and damping from surrounding tokens
            alpha = 1.0
            neg_factor = 1.0

            # Look back up to 3 tokens for modifiers, negations, etc.
            j = i - 1
            steps = 0
            while j >= 0 and steps < 3:
                prev = join_for_lex(tokens[j])
                if prev in all_intens:
                    alpha += 0.5
                if prev in all_dimins:
                    alpha -= 0.3
                if prev in all_negations:
                    neg_factor = -0.8
                # Break scope on hard punctuation
                if tokens[j] in {".", "!", "?"}:
                    break
                j -= 1
                steps += 1

            # Profanities attached to emotion word amplify a bit
            if tok_norm in all_profanities:
                alpha += 0.4

            # Clause weight
            clause_weight = 1.3 if i > contrast_index >= 0 else 1.0

            for e in EMOTIONS:
                contribution = base_vec[e] * alpha * neg_factor * clause_weight
                R[e] += contribution

        # ------------------------------------------------------------------
        # Arousal
        # ------------------------------------------------------------------
        def norm(count: int, scale: float) -> float:
            return min(1.0, count / scale)

        ex_n = norm(exclam_count, 3)
        q_n = norm(question_count, 3)
        caps_n = norm(allcaps_count, 3)
        elong_n = norm(elongated_count, 3)
        prof_n = norm(profanity_count, 2)
        emoji_n = norm(strong_emoji_count, 2)

        raw_arousal = (
            0.4 * ex_n
            + 0.3 * q_n
            + 0.3 * caps_n
            + 0.4 * elong_n
            + 0.4 * prof_n
            + 0.5 * emoji_n
        )
        A = max(0.0, min(1.0, raw_arousal))

        # ------------------------------------------------------------------
        # Boost by arousal and clamp
        # ------------------------------------------------------------------
        R_boosted = {}
        for e in EMOTIONS:
            boosted = R[e] * (1.0 + AROUSAL_BETA[e] * A)
            R_boosted[e] = max(0.0, boosted)

        total = sum(R_boosted.values())
        if total <= 0:
            # Completely neutral text: uniform distribution with low confidence
            mixture = {e: 1.0 / len(EMOTIONS) for e in EMOTIONS}
        else:
            mixture = {e: R_boosted[e] / total for e in EMOTIONS}

        # ------------------------------------------------------------------
        # Sarcasm and confidence
        # ------------------------------------------------------------------
        sarcasm_prob = compute_sarcasm_probability(text, mixture)
        sorted_emotions = sorted(
            mixture.items(), key=lambda kv: kv[1], reverse=True
        )
        top_label, top_val = sorted_emotions[0]
        second_val = sorted_emotions[1][1] if len(sorted_emotions) > 1 else 0.0
        delta = max(0.0, top_val - second_val)

        length_factor = min(1.0, word_count / 12.0)
        strength_factor = min(1.0, delta * 3.0)
        confidence = 0.4 * length_factor + 0.4 * strength_factor + 0.2 * (
            1.0 - sarcasm_prob
        )
        confidence = round(max(0.0, min(1.0, confidence)), 3)

        # ------------------------------------------------------------------
        # Dominant vs current emotion
        # ------------------------------------------------------------------
        # Dominant: strongest component
        dominant_label = top_label

        # Current: if top two are close, bias based on blends
        margin = 0.08
        if second_val > 0 and abs(top_val - second_val) < margin:
            a, b = sorted([sorted_emotions[0][0], sorted_emotions[1][0]])
            blend_bias = {
                ("anger", "sadness"): "sadness",
                ("anger", "disgust"): "anger",
                ("joy", "passion"): "passion",
                ("fear", "surprise"): "fear",
                ("joy", "surprise"): "joy",
            }
            current_label = blend_bias.get((a, b), dominant_label)
        else:
            current_label = dominant_label

        # Emojis
        dominant_emoji = choose_emoji(dominant_label, mixture, A, sarcasm_prob)
        current_emoji = choose_emoji(current_label, mixture, A, sarcasm_prob)

        # Build per emotion results
        emotions_detail: Dict[str, EmotionResult] = {}
        for e in EMOTIONS:
            score = R_boosted[e]
            percent = mixture[e] * 100.0
            emoji = choose_emoji(e, mixture, A, sarcasm_prob)
            emotions_detail[e] = EmotionResult(
                label=e,
                emoji=emoji,
                score=round(score, 4),
                percent=round(percent, 3),
            )

        # Risk level
        risk_level = detect_self_harm_risk(text)

        dominant_result = EmotionResult(
            label=dominant_label,
            emoji=dominant_emoji,
            score=round(R_boosted[dominant_label], 4),
            percent=round(mixture[dominant_label] * 100.0, 3),
        )
        current_result = EmotionResult(
            label=current_label,
            emoji=current_emoji,
            score=round(R_boosted[current_label], 4),
            percent=round(mixture[current_label] * 100.0, 3),
        )

        output = DetectorOutput(
            text=text,
            language=lang_props,
            emotions=emotions_detail,
            mixture_vector={k: round(v, 6) for k, v in mixture.items()},
            dominant=dominant_result,
            current=current_result,
            arousal=round(A, 3),
            sarcasm=round(sarcasm_prob, 3),
            confidence=confidence,
            risk_level=risk_level,
            meta={
                "word_count": word_count,
                "truncated_to_max_words": truncated,
                "exclamation_count": exclam_count,
                "question_count": question_count,
                "allcaps_count": allcaps_count,
                "elongated_count": elongated_count,
                "profanity_count": profanity_count,
                "strong_emoji_count": strong_emoji_count,
                "domain": domain,
            },
        )
        return output


# Default singleton instance for simple imports
_DEFAULT_DETECTOR = EmotionDetector()


def analyze_text(text: str, domain: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience wrapper that returns a plain dict ready for JSON serialization.

    Example:
        from detector import analyze_text
        result = analyze_text("I am really happy but a bit anxious")
    """
    output = _DEFAULT_DETECTOR.analyze(text, domain=domain)
    return output.to_dict()
