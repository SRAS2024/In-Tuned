# detector/detector.py
# High fidelity local emotion detector v30-espt-meta
# Seven core emotions, 1 to 250 words, English / Spanish / Portuguese only.
#
# v30 changes vs v29-espt-meta:
# - Adds lightweight lemmatization / morphology fallback for EN / ES / PT:
#   * lookup_with_lemma() wraps lexicon lookup so inflected forms like
#     "worried", "llorando", "preocupadas" map more reliably to base entries.
#   * Uses simple heuristics per language; does not require external NLP libs.
# - Keeps existing trigram-based _semantic_guess() as a further fallback.
#
# v29 changes vs v28-espt:
# - Fix Spanish temporal phrase typos ("melhor" -> "mejor").
# - Add phrase-level uncertainty / certainty detection across EN / ES / PT:
#   * Captures hedges like "not sure", "no sé", "nao sei", "no tengo idea",
#     "não tenho certeza", etc.
#   * These phrases feed into uncertainty_count / certainty_count and thus
#     influence global intensity, certainty vs uncertainty shaping, and
#     hedge-aware softening of negative emotions.

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
    score: float          # raw internal strength
    percent: float        # intensity percentage 0 to 100 (sum across emotions ≤ 100)


@dataclass
class DetectorOutput:
    text: str
    language: Dict[str, float]
    emotions: Dict[str, EmotionResult]
    # mixture_vector represents intensity weights in [0, 1]
    # whose sum is ≤ 1, not a normalized probability simplex.
    mixture_vector: Dict[str, float]
    dominant: EmotionResult
    current: EmotionResult
    arousal: float
    sarcasm: float
    humor: float
    confidence: float
    risk_level: str
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Utility functions
# =============================================================================


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    return text.strip()


def strip_diacritics(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def normalize_for_search(text: str) -> str:
    """
    Lowercase, normalize quotes, strip diacritics, and collapse whitespace.
    Keeps punctuation so regex word boundaries remain meaningful.
    """
    t = normalize_text(text).lower()
    t = strip_diacritics(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_for_phrase(text: str) -> str:
    """
    Like normalize_for_search, but also normalizes underscores to spaces so that
    user text with spaces matches lexicon phrases registered with either style.
    """
    t = normalize_for_search(text)
    t = t.replace("_", " ")
    return t


# Tokenizer keeps internal apostrophes inside words for EN/ES/PT contractions.
TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ_']+|[^\w\s]", re.UNICODE)


def _merge_hyphenated_compounds(tokens: List[str]) -> List[str]:
    """
    Merge simple hyphenated compounds: word '-' word -> wordword.
    This helps match lexicon keys like 'pissedoff' when input is 'pissed-off'.
    """
    if not tokens:
        return tokens
    out: List[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if (
            tok == "-"
            and out
            and i + 1 < len(tokens)
            and any(ch.isalpha() for ch in out[-1])
            and any(ch.isalpha() for ch in tokens[i + 1])
        ):
            merged = out[-1] + tokens[i + 1]
            out[-1] = merged
            i += 2
            continue
        out.append(tok)
        i += 1
    return out


def tokenize(text: str) -> List[str]:
    tokens = TOKEN_RE.findall(text)
    return _merge_hyphenated_compounds(tokens)


def _reconstruct_text(tokens: List[str]) -> str:
    """
    Rebuild tokens into a readable string, avoiding spaces before punctuation.
    This is used only when truncating to max words.
    """
    if not tokens:
        return ""
    out: List[str] = []
    for tok in tokens:
        if not out:
            out.append(tok)
            continue
        if re.fullmatch(r"[^\w\s]", tok, flags=re.UNICODE):
            out[-1] += tok
        else:
            out.append(" " + tok)
    return "".join(out).strip()


def is_emoji(char: str) -> bool:
    """
    Emoji detector for single codepoints.

    Important fix:
    - Do NOT count variation selectors (FE0F) as emojis.
      They get tokenized separately in sequences like "❤️".
    """
    if not char:
        return False
    cp = ord(char)
    return (
        0x1F300 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x26FF
        or 0x2700 <= cp <= 0x27BF
    )


def join_for_lex(token: str) -> str:
    """Normalize token for lexicon and marker lookups."""
    token = token.strip()
    token = token.strip("`'\"")
    if token.startswith("#") or token.startswith("@"):
        token = token[1:]
    token = token.lower()
    token = unicodedata.normalize("NFD", token)
    token = "".join(ch for ch in token if unicodedata.category(ch) != "Mn")
    token = token.replace(" ", "_")
    return token


def detect_word_count(tokens: List[str]) -> int:
    """Alphabetic word count (used for truncation and classic length logic)."""
    count = 0
    for t in tokens:
        if any(ch.isalpha() for ch in t):
            count += 1
    return count


def detect_emoji_count(tokens: List[str]) -> int:
    """Count emoji tokens as meaningful short-text units."""
    c = 0
    for t in tokens:
        if len(t) == 1 and is_emoji(t):
            c += 1
    return c


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


LEXICON_TOKEN: Dict[str, Dict[str, Dict[str, float]]] = {
    "en": {},
    "es": {},
    "pt": {},
}


def _register_words(lang: str, emotion: str, words: List[str], base: float) -> None:
    """Register words normalized into the lexicon."""
    table = LEXICON_TOKEN[lang]
    for w in words:
        wl = join_for_lex(w)
        vec = table.get(wl, _vec())
        vec[emotion] = vec.get(emotion, 0.0) + base
        table[wl] = vec


# -----------------------------------------------------------------------------
# Base lexicon (identical to original v27 with minor extensions where noted)
# -----------------------------------------------------------------------------

# English core
_register_words(
    "en",
    "anger",
    [
        "angry",
        "mad",
        "furious",
        "irritated",
        "irritating",
        "annoyed",
        "annoying",
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
        "frustrating",
        "upset",
        "fuming",
        "outraged",
    ],
    2.2,
)
_register_words(
    "en",
    "disgust",
    [
        "disgusted",
        "gross",
        "grossed",
        "nasty",
        "disgusting",
        "revolting",
        "sickening",
        "sickened",
        "queasy",
        "repulsed",
        "repulsive",
        "yuck",
        "ew",
        "eww",
        "ewww",
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
        "concerned",
        "concern",
        "panic",
        "panicking",
        "petrified",
        "nervous",
        "frightened",
        "overthinking",
        "paranoid",
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
        "good",
        "grateful",
        "thankful",
        "delighted",
        "excited",
        "ecstatic",
        "overjoyed",
        "hyped",
        "hype",
        "joyful",
        "joy",
        "content",
        "satisfied",
        "relieved",
        "hopeful",
        "better",
        "peaceful",
        "smiling",
        "smile",
        "lol",
        "lolol",
        "lmao",
        "lmfao",
        "rofl",
        "haha",
        "hahaha",
        "awesome",
        "amazing",
        "fantastic",
        "great",
        "dope",
        "lit",
        "fire",
        "slay",
        "slayed",
        "iconic",
        "cute",
        "cutie",
        "loveit",
        "lovethis",
        "blessed",
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
        "devastated",
        "heartbroken",
        "heartache",
        "lonely",
        "alone",
        "crying",
        "cried",
        "cries",
        "tearful",
        "blue",
        "grief",
        "grieving",
        "meh",
        "low",
        "drained",
        "burnedout",
        "burntout",
        "empty",
        "numb",
        "broken",
        "lost",
        "exhausted",
        "hopeless",
        "overwhelmed",
        "worse",
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
        "stan",
        "simp",
        "simping",
        "ship",
        "ships",
        "thirsty",
        "infatuated",
        "devoted",
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
        "omfg",
        "cantbelieve",
        "cannotbelieve",
        "unexpected",
        "nooo",
        "what",
        "wtf",
        "no_way",
        "shook",
        "shooketh",
    ],
    2.1,
)

# Extra English slang
_register_words(
    "en",
    "anger",
    [
        "salty",
        "pressed",
        "triggered",
        "ugh",
        "smh",
        "livid",
        "bs",
        "trash",
        "garbage",
        "stupid",
        "idiot",
        "idiots",
        "clown",
        "clowns",
        "bullshit",
    ],
    1.8,
)
_register_words(
    "en",
    "fear",
    [
        "worriedaf",
        "scaredaf",
        "anxiousaf",
        "shook",
        "spooked",
        "freaking",
        "freaked",
        "freakingout",
        "lowkey_scared",
        "stressed",
        "stressful",
    ],
    1.8,
)
_register_words(
    "en",
    "joy",
    [
        "stoked",
        "pumped",
        "vibing",
        "vibes",
        "chilling",
        "chillin",
        "chill",
        "hypebeast",
        "litty",
        "w",
        "dub",
        "winning",
        "contentment",
        "gracefilled",
    ],
    1.7,
)
_register_words(
    "en",
    "sadness",
    [
        "burnt",
        "burntout",
        "burnedout",
        "heartbroken",
        "drained",
        "notokay",
        "not_okay",
        "notfine",
        "not_fine",
    ],
    1.9,
)
_register_words(
    "en",
    "passion",
    [
        "bae",
        "babe",
        "baby",
        "my_love",
        "my_world",
        "soulmate",
        "smitten",
        "crushing",
        "crushin",
        "lowkey_inlove",
        "my_person",
    ],
    2.0,
)
_register_words(
    "en",
    "disgust",
    [
        "icky",
        "grossedout",
        "nastyaf",
        "crusty",
        "yikes",
    ],
    1.7,
)

# Small EN affirmations for 1 to 2 word inputs (low weight)
_register_words(
    "en",
    "joy",
    [
        "ok", "okay", "okey", "alright", "aight", "nice", "cool",
        "yay", "yayy", "yess", "yup", "yeah", "yea",
    ],
    0.9,
)

# Spanish core
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
        "recaliente",
        "hinchado",
        "harta",
        "harto",
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
        "cringe",
        "cringi",
        "guacala",
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
        "panico",
        "peligro",
        "tenso",
        "tensa",
        "estresado",
        "estresada",
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
        "alegria",
        "emocionado",
        "emocionada",
        "agradecido",
        "agradecida",
        "sonriendo",
        "jaja",
        "jajaja",
        "jajajaja",
        "jeje",
        "jejeje",
        "xd",
        "xddd",
        "genial",
        "que_bueno",
        "que_bien",
        "me_encanta",
        "encanta",
        "buenisimo",
        "felicidad",
        "mejor",
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
        "llore",
        "pena",
        "dolor",
        "tristeza",
        "depre",
        "bajoneado",
        "bajoneada",
        "vacio",
        "rota",
        "roto",
        "apagado",
        "apagada",
        "peor",
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
        "atraccion",
        "te_quiero",
        "te_amo",
        "me_fascina",
        "me_encantas",
        "te_adoro",
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
        "impactada",
        "wow",
        "guau",
        "no_lo_creo",
        "increible",
    ],
    2.1,
)

# Spanish dialects and slang
_register_words(
    "es",
    "anger",
    [
        "cabreado",
        "cabreada",
        "emputado",
        "emputada",
        "rayado",
        "rayada",
        "encabronado",
        "encabronada",
        "bronca",
        "ardido",
        "ardida",
    ],
    2.1,
)
_register_words(
    "es",
    "joy",
    [
        "chevere",
        "chido",
        "bacano",
        "brutal",
        "guay",
        "que_lindo",
        "precioso",
        "preciosa",
        "lindisimo",
        "bendecido",
        "bendecida",
    ],
    1.8,
)
_register_words(
    "es",
    "sadness",
    [
        "desanimado",
        "desanimada",
        "apagado",
        "apagada",
        "hundido",
        "hundida",
    ],
    1.9,
)
_register_words(
    "es",
    "passion",
    [
        "carino",
        "mi_vida",
        "mi_amor",
        "cielito",
        "corazon",
        "tesoro",
        "cosita",
        "amor_de_mi_vida",
    ],
    2.1,
)

# Small ES affirmations for short inputs (low weight)
_register_words(
    "es",
    "joy",
    ["bien", "bueno", "vale", "ok", "okay", "listo", "genial"],
    0.9,
)

# Portuguese core
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
        "odio",
        "frustrado",
        "frustrada",
        "puto",
        "puta_da_vida",
        "bolado",
        "bolada",
        "pistola",
        "aff",
        "affs",
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
        "cringe",
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
        "panico",
        "tenso",
        "tensa",
        "estressado",
        "estressada",
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
        "kk",
        "kkk",
        "kkkk",
        "kkkkk",
        "kkkkkk",
        "rs",
        "rsrs",
        "rsrsrs",
        "haha",
        "hahaha",
        "top",
        "daora",
        "amei",
        "maravilhoso",
        "maravilhosa",
        "perfeito",
        "perfeita",
        "felicidade",
        "melhor",
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
        "solidao",
        "chorando",
        "chorei",
        "chorar",
        "magoa",
        "dor",
        "chateado",
        "chateada",
        "bad",
        "na_bad",
        "abalado",
        "abalada",
        "desanimado",
        "desanimada",
        "mal",
        "pra_baixo",
        "pior",
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
        "tesao",
        "desejo",
        "desejando",
        "gostoso",
        "gostosa",
        "te_amo",
        "te_adoro",
        "crush",
        "apaixonadinho",
        "apaixonadinha",
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
        "nao_acredito",
        "meu_deus",
        "mds",
    ],
    2.1,
)

# Portuguese dialects and slang
_register_words(
    "pt",
    "joy",
    [
        "felicidade",
        "massa",
        "topzera",
        "da_hora",
        "legal",
        "show",
        "maravilha",
        "sensacional",
        "incrivel",
        "lindo",
        "linda",
    ],
    1.8,
)
_register_words(
    "pt",
    "sadness",
    [
        "nao_to_bem",
    ],
    1.9,
)
_register_words(
    "pt",
    "passion",
    [
        "meu_amor",
        "minha_vida",
        "meu_bem",
        "querido",
        "querida",
        "mozao",
        "lindinho",
        "lindinha",
        "fofo",
        "fofa",
        "saudade",
    ],
    2.1,
)
_register_words(
    "pt",
    "sadness",
    [
        "saudade",
        "saudades",
    ],
    1.8,
)

# Small PT affirmations for short inputs (low weight)
_register_words(
    "pt",
    "joy",
    ["bem", "boa", "beleza", "valeu", "ok", "okay", "showzinho"],
    0.9,
)

# Nuance and dialect extensions for subtle rough day patterns
_register_words(
    "en",
    "sadness",
    [
        "hard",
        "difficult",
        "tough",
        "rough",
        "exhausted",
        "tired",
        "overwhelmed",
        "overwhelming",
        "draining",
    ],
    1.3,
)
_register_words(
    "en",
    "fear",
    [
        "stressed",
        "stressful",
    ],
    1.5,
)
_register_words(
    "es",
    "sadness",
    [
        "cansado",
        "cansada",
        "agotado",
        "agotada",
        "dificil",
    ],
    1.4,
)
_register_words(
    "es",
    "fear",
    [
        "estresado",
        "estresada",
    ],
    1.5,
)
_register_words(
    "pt",
    "sadness",
    [
        "cansado",
        "cansada",
        "exausto",
        "exausta",
        "dificil",
    ],
    1.4,
)
_register_words(
    "pt",
    "fear",
    [
        "estressado",
        "estressada",
    ],
    1.5,
)

# Grief, loss and bittersweet nuance across languages
_register_words(
    "en",
    "sadness",
    [
        "bittersweet",
        "pain",
        "painful",
        "hurt",
        "hurts",
        "hurting",
        "absence",
        "gone",
        "losing",
        "loss",
        "mourning",
        "mourn",
        "mourned",
        "linger",
        "lingers",
        "lingering",
        "passed",
        "funeral",
    ],
    1.9,
)
_register_words(
    "en",
    "joy",
    [
        "bittersweet",
    ],
    0.9,
)
_register_words(
    "es",
    "sadness",
    [
        "duelo",
        "luto",
        "perdida",
        "perdido",
        "perdimos",
        "perdi",
        "fallecio",
        "se_fue",
        "ausencia",
        "agridulce",
    ],
    1.9,
)
_register_words(
    "es",
    "joy",
    [
        "agridulce",
    ],
    0.8,
)
_register_words(
    "pt",
    "sadness",
    [
        "luto",
        "perda",
        "perdi",
        "perdemos",
        "faleceu",
        "se_foi",
        "ausencia",
        "agridoce",
    ],
    1.9,
)
_register_words(
    "pt",
    "joy",
    [
        "agridoce",
    ],
    0.8,
)

# Abbreviations and acronyms with emotional priors
_register_words(
    "en",
    "sadness",
    ["idk", "idk.", "idk,"],
    0.8,
)
_register_words(
    "en",
    "anger",
    ["smh", "wtf", "ffs"],
    1.4,
)
_register_words(
    "en",
    "joy",
    ["tbh", "ngl", "fr", "frfr"],
    0.6,
)
_register_words(
    "es",
    "passion",
    ["tqm", "tqm.", "tqm!"],
    1.8,
)
_register_words(
    "es",
    "anger",
    ["nmms", "no_mames", "hdp"],
    1.7,
)
_register_words(
    "pt",
    "joy",
    ["kkk", "kkkk", "kkkkk"],
    1.4,
)
_register_words(
    "pt",
    "anger",
    ["aff", "pqp", "mds"],
    1.3,
)

# Profanity mapped into core emotions so swear-only inputs are not neutral
_register_words(
    "en",
    "anger",
    [
        "fuck",
        "fucking",
        "fuckin",
        "damn",
        "dammit",
        "damnit",
        "hell",
    ],
    2.6,
)
_register_words(
    "en",
    "disgust",
    [
        "shit",
        "bitch",
        "asshole",
        "crap",
    ],
    2.3,
)
_register_words(
    "en",
    "sadness",
    [
        "damn",
        "dammit",
        "damnit",
    ],
    1.2,
)
_register_words(
    "es",
    "anger",
    [
        "mierda",
        "joder",
        "carajo",
        "puta",
        "pendejo",
        "pendeja",
    ],
    2.5,
)
_register_words(
    "es",
    "disgust",
    [
        "mierda",
        "puta",
    ],
    2.2,
)
_register_words(
    "pt",
    "anger",
    [
        "merda",
        "porra",
        "caralho",
        "bosta",
        "puta",
        "pqp",
    ],
    2.5,
)
_register_words(
    "pt",
    "disgust",
    [
        "merda",
        "bosta",
    ],
    2.2,
)

# Multiword phrase lexicon (registered in raw form, normalized later)
PHRASE_LEXICON: Dict[str, Dict[str, float]] = {
    # English
    "on cloud nine": _vec(joy=3.0),
    "over the moon": _vec(joy=3.0),
    "fed up": _vec(anger=1.6, sadness=1.4),
    "at my wits end": _vec(anger=1.4, sadness=1.7),
    "sick to my stomach": _vec(disgust=2.5, fear=1.0),
    "heart broken": _vec(sadness=3.0),
    "heartbroken": _vec(sadness=3.0),
    "to die for": _vec(passion=2.0, joy=1.0),
    "i hate you": _vec(anger=3.0, disgust=1.5),
    "i hate myself": _vec(anger=2.0, sadness=2.0),
    "i am done": _vec(sadness=2.0, anger=1.0),
    "rough day": _vec(sadness=2.0),
    "hard day": _vec(sadness=2.0),
    "tough day": _vec(sadness=2.0),
    "long day": _vec(sadness=1.6),
    "not the easiest week": _vec(sadness=2.3, fear=0.7),
    "not an easy week": _vec(sadness=2.0, fear=0.7),
    "lowkey happy": _vec(joy=1.5, sadness=0.5),
    "low key happy": _vec(joy=1.5, sadness=0.5),
    "highkey happy": _vec(joy=2.0),
    "high key happy": _vec(joy=2.0),
    "i am dead": _vec(joy=1.0, surprise=1.0),
    "im dead": _vec(joy=1.0, surprise=1.0),
    "no cap": _vec(joy=0.5, passion=0.5),
    "so proud of you": _vec(joy=2.0, passion=1.0),
    "proud of you": _vec(joy=1.6, passion=0.6),
    "all good now": _vec(joy=1.4, sadness=0.3),
    "it is okay now": _vec(joy=1.2, sadness=0.4),
    "i am not ok": _vec(sadness=2.5, fear=0.7),
    "im not ok": _vec(sadness=2.5, fear=0.7),
    "i am not okay": _vec(sadness=2.5, fear=0.7),
    "im not okay": _vec(sadness=2.5, fear=0.7),
    "not doing great": _vec(sadness=2.3),
    "not doing so great": _vec(sadness=2.3),
    "not feeling great": _vec(sadness=2.2),
    "i feel empty": _vec(sadness=2.7),
    "i feel alone": _vec(sadness=2.7),
    "i miss you": _vec(sadness=2.2, passion=1.0),
    "missing you": _vec(sadness=2.0, passion=1.0),
    "feel like giving up": _vec(sadness=2.6, fear=1.0),
    "feeling blessed": _vec(joy=2.0, passion=0.5),
    "grateful for you": _vec(joy=1.8, passion=0.8),
    "in love with you": _vec(passion=2.7, joy=1.3),
    # New profanity and frustration phrases
    "fuck this": _vec(anger=3.0, disgust=1.2, sadness=0.8),
    "fuck this shit": _vec(anger=3.2, disgust=1.6, sadness=1.0),
    "what the hell": _vec(anger=1.4, surprise=1.4),
    "what the hell man": _vec(anger=1.6, surprise=1.6),
    "son of a bitch": _vec(anger=2.8, disgust=1.3),
    # Bereavement and bittersweet English phrases
    "i can't believe he's gone": _vec(sadness=3.2, surprise=1.0),
    "i cant believe hes gone": _vec(sadness=3.2, surprise=1.0),
    "can't believe he's gone": _vec(sadness=3.0, surprise=1.0),
    "cant believe hes gone": _vec(sadness=3.0, surprise=1.0),
    "cant believe he is gone": _vec(sadness=3.0, surprise=1.0),
    "i can't believe she is gone": _vec(sadness=3.2, surprise=1.0),
    "i cant believe she is gone": _vec(sadness=3.2, surprise=1.0),
    "he is in a better place": _vec(sadness=2.4, joy=1.4),
    "he's in a better place": _vec(sadness=2.4, joy=1.4),
    "she is in a better place": _vec(sadness=2.4, joy=1.4),
    "she's in a better place": _vec(sadness=2.4, joy=1.4),
    "they are in a better place": _vec(sadness=2.3, joy=1.3),
    "in a better place now": _vec(sadness=2.2, joy=1.4),
    "bittersweet feeling": _vec(sadness=2.2, joy=1.4),
    # Pop culture and historical shortcuts
    "9/11": _vec(sadness=2.8, fear=1.5),
    "september 11": _vec(sadness=2.8, fear=1.5),
    "titanic": _vec(sadness=2.2, passion=1.0),
    "world cup final": _vec(joy=2.2, surprise=1.3),
    "game of thrones ending": _vec(anger=1.8, sadness=1.3, disgust=1.0),
    "avengers endgame": _vec(joy=1.9, sadness=1.0, surprise=1.2),
    # Spanish
    "no aguanto más": _vec(anger=1.5, sadness=2.0),
    "no aguanto mas": _vec(anger=1.5, sadness=2.0),
    "no lo soporto": _vec(anger=2.0, disgust=1.0),
    "me rompe el corazón": _vec(sadness=3.0),
    "me parte el corazón": _vec(sadness=3.0),
    "no fue una semana fácil": _vec(sadness=2.3, fear=0.7),
    "no fue una semana facil": _vec(sadness=2.3, fear=0.7),
    "me da igual": _vec(sadness=0.8),
    "estar hasta las narices": _vec(anger=2.0, disgust=1.0),
    "no me importa un carajo": _vec(anger=1.8, disgust=1.2),
    "que miedo": _vec(fear=2.0),
    "que asco": _vec(disgust=2.0),
    "que rabia": _vec(anger=2.0),
    "que bueno": _vec(joy=2.0),
    "te quiero mucho": _vec(passion=2.3, joy=1.0),
    "te amo mucho": _vec(passion=2.5, joy=1.2),
    "todo bien ahora": _vec(joy=1.4, sadness=0.4),
    "no estoy bien": _vec(sadness=2.5, fear=0.7),
    "no me siento bien": _vec(sadness=2.5, fear=0.7),
    "me siento mal": _vec(sadness=2.2, fear=0.6),
    "me siento solo": _vec(sadness=2.5),
    "me siento sola": _vec(sadness=2.5),
    "te extraño mucho": _vec(sadness=2.4, passion=1.0),
    "te extraño": _vec(sadness=2.0, passion=0.8),
    "me da igual si": _vec(sadness=1.1),
    "tqm": _vec(passion=2.3, joy=1.0),
    "tq mucho": _vec(passion=2.1, joy=0.9),
    # Spanish grief and bittersweet
    "no puedo creer que se haya ido": _vec(sadness=3.1, surprise=0.9),
    "no puedo creer que se fue": _vec(sadness=3.0, surprise=0.9),
    "está en un lugar mejor": _vec(sadness=2.4, joy=1.4),
    "esta en un lugar mejor": _vec(sadness=2.4, joy=1.4),
    "sentimiento agridulce": _vec(sadness=2.2, joy=1.4),
    # Portuguese
    "não aguento más": _vec(anger=1.5, sadness=2.0),
    "nao aguento mais": _vec(anger=1.5, sadness=2.0),
    "me parte o coração": _vec(sadness=3.0),
    "me parte meu coração": _vec(sadness=3.0),
    "me parte o coracao": _vec(sadness=3.0),
    "nao foi uma semana facil": _vec(sadness=2.3, fear=0.7),
    "não foi uma semana fácil": _vec(sadness=2.3, fear=0.7),
    "de saco cheio": _vec(anger=2.1, sadness=1.2),
    "tô nem aí": _vec(sadness=0.7),
    "to nem ai": _vec(sadness=0.7),
    "com o coração na mão": _vec(sadness=2.2, fear=1.0),
    "que medo": _vec(fear=2.0),
    "que nojo": _vec(disgust=2.0),
    "que raiva": _vec(anger=2.0),
    "que bom": _vec(joy=2.0),
    "te amo muito": _vec(passion=2.5, joy=1.2),
    "te amo demais": _vec(passion=2.5, joy=1.3),
    "tudo bem agora": _vec(joy=1.4, sadness=0.4),
    "não estou bem": _vec(sadness=2.5, fear=0.7),
    "nao estou bem": _vec(sadness=2.5, fear=0.7),
    "nao to bem": _vec(sadness=2.5, fear=0.7),
    "não to bem": _vec(sadness=2.5, fear=0.7),
    "me sinto mal": _vec(sadness=2.2, fear=0.6),
    "sinto sua falta": _vec(sadness=2.4, passion=1.0),
    "morro de saudade": _vec(sadness=2.5, passion=1.1),
    # Portuguese grief and bittersweet
    "não consigo acreditar que ele se foi": _vec(sadness=3.1, surprise=0.9),
    "nao consigo acreditar que ele se foi": _vec(sadness=3.1, surprise=0.9),
    "ele está em um lugar melhor": _vec(sadness=2.4, joy=1.4),
    "ele esta em um lugar melhor": _vec(sadness=2.4, joy=1.4),
    "ela está em um lugar melhor": _vec(sadness=2.4, joy=1.4),
    "ela esta em um lugar melhor": _vec(sadness=2.4, joy=1.4),
    "sentimento agridoce": _vec(sadness=2.2, joy=1.4),
}

# Build a normalized phrase lexicon so matching is accent and spacing robust.
PHRASE_LEXICON_NORM: Dict[str, Dict[str, float]] = {}
for k, v in PHRASE_LEXICON.items():
    nk = normalize_for_phrase(k)
    PHRASE_LEXICON_NORM[nk] = v

# Precompile normalized phrase patterns once.
PHRASE_REGEX_NORM: List[Tuple[re.Pattern, Dict[str, float]]] = []
for phrase_norm, vec in PHRASE_LEXICON_NORM.items():
    if not phrase_norm:
        continue
    pat = re.compile(rf"(?<!\w){re.escape(phrase_norm)}(?!\w)")
    PHRASE_REGEX_NORM.append((pat, vec))


# Emoticons and text faces, applied as patterns on the raw text
EMOTICON_PATTERNS: List[Tuple[re.Pattern, Dict[str, float]]] = [
    (re.compile(r"(?:(?:\:|\=)\-?\)+)"), _vec(joy=1.8)),
    (re.compile(r"(?:(?:\:|\=)\-?\(+)"), _vec(sadness=1.8)),
    (re.compile(r";\-?\)"), _vec(joy=1.4, passion=0.6)),
    (re.compile(r":'\("), _vec(sadness=2.0)),
    (re.compile(r":'\)"), _vec(joy=1.5, sadness=0.8)),
    (re.compile(r":D+"), _vec(joy=2.0)),
    (re.compile(r"XD+"), _vec(joy=2.0, surprise=0.8)),
    (re.compile(r">:\("), _vec(anger=2.0)),
    (re.compile(r":\/"), _vec(sadness=1.1, disgust=0.9)),
    (re.compile(r":P+"), _vec(joy=1.2, passion=0.4)),
    (re.compile(r"<3"), _vec(passion=2.0, joy=0.8)),
    (re.compile(r"\^_\^"), _vec(joy=1.6)),
    (re.compile(r"T_T"), _vec(sadness=2.1)),
]

# Rhetorical question and stance patterns
RHETORICAL_PATTERNS: List[Tuple[re.Pattern, Dict[str, float], float]] = [
    (re.compile(r"\bare you kidding\b", re.IGNORECASE), _vec(anger=1.0, surprise=1.4), 0.6),
    (re.compile(r"\bare you serious\b", re.IGNORECASE), _vec(anger=0.7, surprise=1.1), 0.5),
    (re.compile(r"\breally\?{2,}", re.IGNORECASE), _vec(anger=0.6, surprise=1.0), 0.4),
    (re.compile(r"\bhow could you\b", re.IGNORECASE), _vec(anger=1.4, sadness=0.8), 0.7),
    (re.compile(r"\bis this a joke\b", re.IGNORECASE), _vec(anger=0.8, surprise=1.0), 0.5),
    # English frustration rhetorical
    (
        re.compile(r"\bhow (?:the )?hell do you think i feel\b", re.IGNORECASE),
        _vec(anger=2.2, sadness=1.1),
        0.9,
    ),
    # Spanish / Portuguese fixes, no trailing word-boundary after '?'
    (re.compile(r"\ben serio\?+", re.IGNORECASE), _vec(anger=0.6, surprise=0.8), 0.4),
    (re.compile(r"\bfala serio\?+", re.IGNORECASE), _vec(anger=0.6, surprise=0.8), 0.4),
]

# Metaphor and figurative language cues
METAPHOR_PATTERNS: List[Tuple[re.Pattern, Dict[str, float]]] = [
    (re.compile(r"\bi[' ]?m drowning\b", re.IGNORECASE), _vec(sadness=2.0, fear=1.0)),
    (re.compile(r"\bdrowning in (work|stress|debt)", re.IGNORECASE), _vec(sadness=1.6, fear=1.0)),
    (re.compile(r"\bcarrying the weight of the world\b", re.IGNORECASE), _vec(sadness=2.3)),
    (re.compile(r"\bwalking on eggshells\b", re.IGNORECASE), _vec(fear=2.0, sadness=1.0)),
    (re.compile(r"\bbutterflies in my stomach\b", re.IGNORECASE), _vec(passion=1.6, fear=0.6, joy=0.8)),
    (re.compile(r"\bheart (?:is )?(?:on fire|burning)\b", re.IGNORECASE), _vec(passion=2.0, anger=0.8)),
    (re.compile(r"\bcrushed me\b", re.IGNORECASE), _vec(sadness=2.0)),
    # Spanish
    (re.compile(r"\bme estoy ahogando\b", re.IGNORECASE), _vec(sadness=2.0, fear=1.0)),
    (re.compile(r"\bme ahogo\b", re.IGNORECASE), _vec(sadness=1.7, fear=1.0)),
    (re.compile(r"\bcon el corazon en la mano\b", re.IGNORECASE), _vec(sadness=2.2, fear=1.0)),
    # Portuguese
    (re.compile(r"\bestou me afogando\b", re.IGNORECASE), _vec(sadness=2.0, fear=1.0)),
    (re.compile(r"\bcarregando o mundo nas costas\b", re.IGNORECASE), _vec(sadness=2.3)),
    (re.compile(r"\bcom o coracao na mao\b", re.IGNORECASE), _vec(sadness=2.2, fear=1.0)),
]


# Intensifiers and diminishers
INTENSIFIERS = {
    "en": {
        "very", "really", "so", "super", "extremely", "incredibly", "totally",
        "absolutely", "completely", "too", "sooo", "soooo", "hella", "highkey",
        "crazy", "crazyyy", "mega", "ultra", "literally", "insanely",
        "wild", "wildly", "ridiculously",
    },
    "es": {"muy", "re", "super", "demasiado", "tan"},
    "pt": {"muito", "super", "demais", "tao", "pra", "bastante"},
}
DIMINISHERS = {
    "en": {
        "kind", "kinda", "sort", "sorta", "little", "bit", "maybe", "possibly",
        "kind_of", "sort_of", "a_bit", "a_little",
    },
    "es": {"un", "poco", "algo", "quizas", "tal_vez"},
    "pt": {"um", "pouco", "meio", "talvez"},
}

NEGATIONS = {
    "en": {
        "not", "never", "no", "dont", "don't", "isnt", "isn't",
        "cant", "can't", "wont", "won't", "nothing",
    },
    "es": {"no", "nunca", "jamas", "nada"},
    "pt": {"nao", "nem", "nunca", "jamais"},
}

CONTRAST_WORDS = {
    "en": {"but", "however", "though", "yet", "anyway", "even_so"},
    "es": {"pero", "sin", "embargo", "aunque"},
    "pt": {"mas", "porem", "contudo", "embora"},
}

CONDITIONAL_MARKERS = {
    "en": {"if", "unless"},
    "es": {"si"},
    "pt": {"se"},
}
CAUSAL_MARKERS = {
    "en": {"because", "since", "cause"},
    "es": {"porque", "ya_que", "por_eso"},
    "pt": {"porque", "por_que", "ja_que", "por_isso"},
}

PROFANITIES = {
    "en": {"fuck", "fucking", "fuckin", "shit", "bitch", "asshole", "damn", "dammit", "damnit", "wtf", "hell"},
    "es": {"mierda", "joder", "carajo", "puta", "pendejo", "pendeja"},
    "pt": {"merda", "porra", "caralho", "puta", "bosta", "pqp"},
}

UNCERTAINTY_WORDS = {
    "en": {
        "maybe", "perhaps", "kinda", "sorta", "guess", "idk", "idk.", "idk,",
        "unsure", "not_sure", "probably", "possibly", "i_guess", "i_think",
        "idek", "idkman", "idk_man", "idk_bro",
    },
    "es": {
        "quizas", "tal", "vez", "tal_vez", "supongo", "no_se", "creo",
        "creo_que", "capaz",
    },
    "pt": {
        "talvez", "acho", "acho_que", "nao_sei", "provavelmente", "quem_sabe",
    },
}

CERTAINTY_WORDS = {
    "en": {
        "definitely", "for_sure", "forreal", "fr", "frfr", "no_cap",
        "literally", "deadass", "for_real", "no_doubt",
    },
    "es": {"definitivamente", "seguro", "segura", "claro", "obvio"},
    "pt": {"com_certeza", "certeza", "claro", "obvio"},
}

PRAGMATIC_SOFTENERS = {
    "en": {"just", "like", "kinda", "sorta", "sort_of", "kind_of"},
    "es": {"como_que", "un_poco", "medio"},
    "pt": {"tipo", "meio", "sei_la"},
}
MANNER_MARKERS = {
    "en": {"lowkey", "highkey", "literally"},
    "es": {"en_plan"},
    "pt": {"ne", "ue"},
}

TEMPORAL_PERSIST = {
    "en": {"still", "again", "always", "lately"},
    "es": {"todavia", "siempre", "otra_vez"},
    "pt": {"ainda", "sempre", "de_novo"},
}
TEMPORAL_RESOLVE = {
    "en": {"anymore", "no_longer", "finally", "better_now", "moved_on"},
    "es": {"ya_no", "al_final", "por_fin", "ya_estoy_mejor"},
    "pt": {"ja_nao", "ja_estou_melhor", "agora_estou_bem"},
}

FEEL_MARKERS = {
    "en": {"feel", "feeling", "felt", "feelings"},
    "es": {"siento", "sentir", "sentido", "sintiendo", "me_siento"},
    "pt": {"sinto", "sentir", "sentido", "sentindo", "me_sinto"},
}

LANG_FUNCTION_WORDS = {
    "en": {"the", "and", "is", "am", "are", "you", "i", "my", "me", "it", "of", "to", "in"},
    "es": {"el", "la", "los", "las", "y", "es", "soy", "eres", "estoy", "yo", "tu", "mi", "me"},
    "pt": {"o", "a", "os", "as", "e", "e", "sou", "estou", "voce", "eu", "meu", "minha"},
}


def _normalize_marker_dict(d: Dict[str, set]) -> Dict[str, set]:
    return {lang: {join_for_lex(w) for w in words} for lang, words in d.items()}


INTENSIFIERS = _normalize_marker_dict(INTENSIFIERS)
DIMINISHERS = _normalize_marker_dict(DIMINISHERS)
NEGATIONS = _normalize_marker_dict(NEGATIONS)
CONTRAST_WORDS = _normalize_marker_dict(CONTRAST_WORDS)
CONDITIONAL_MARKERS = _normalize_marker_dict(CONDITIONAL_MARKERS)
CAUSAL_MARKERS = _normalize_marker_dict(CAUSAL_MARKERS)
PROFANITIES = _normalize_marker_dict(PROFANITIES)
UNCERTAINTY_WORDS = _normalize_marker_dict(UNCERTAINTY_WORDS)
CERTAINTY_WORDS = _normalize_marker_dict(CERTAINTY_WORDS)
PRAGMATIC_SOFTENERS = _normalize_marker_dict(PRAGMATIC_SOFTENERS)
MANNER_MARKERS = _normalize_marker_dict(MANNER_MARKERS)
TEMPORAL_PERSIST = _normalize_marker_dict(TEMPORAL_PERSIST)
TEMPORAL_RESOLVE = _normalize_marker_dict(TEMPORAL_RESOLVE)
FEEL_MARKERS = _normalize_marker_dict(FEEL_MARKERS)
LANG_FUNCTION_WORDS = _normalize_marker_dict(LANG_FUNCTION_WORDS)

# NEW: phrase-level hedging / certainty cues (accent-insensitive via normalize_for_phrase).
UNCERTAINTY_PHRASES: Dict[str, List[str]] = {
    "en": [
        "not sure",
        "no idea",
        "don't know",
        "dont know",
        "have no idea",
        "have absolutely no idea",
        "can't tell",
        "cannot tell",
        "could be",
        "might be",
    ],
    "es": [
        "no se",
        "no sé",
        "no tengo idea",
        "no tengo ni idea",
        "no estoy seguro",
        "no estoy segura",
        "no estoy tan seguro",
        "no estoy tan segura",
        "no lo tengo claro",
        "no tengo muy claro",
    ],
    "pt": [
        "nao sei",
        "não sei",
        "nao tenho certeza",
        "não tenho certeza",
        "não faço ideia",
        "nao faco ideia",
        "tenho minhas duvidas",
        "tenho minhas dúvidas",
    ],
}

CERTAINTY_PHRASES: Dict[str, List[str]] = {
    "en": [
        "for sure",
        "for real",
        "for real though",
        "no doubt",
        "without a doubt",
        "of course",
        "for certain",
        "dead ass",
        "deadass",
        "no cap",
    ],
    "es": [
        "sin duda",
        "sin ninguna duda",
        "claro que si",
        "claro que sí",
        "por supuesto",
        "es obvio",
        "es seguro",
        "es muy claro",
    ],
    "pt": [
        "sem duvida",
        "sem dúvida",
        "com certeza",
        "tenho certeza",
        "é obvio",
        "e obvio",
        "com toda certeza",
    ],
}

FEEL_MARKERS_ALL = set().union(*FEEL_MARKERS.values())

_SELF_PRONOUNS_RAW = {
    "i", "im", "i'm", "me", "my", "mine",
    "yo", "mi", "mio", "mia", "mios", "mias",
    "eu", "meu", "minha", "meus", "minhas",
}
_OTHER_PRONOUNS_RAW = {
    "he", "she", "they", "him", "her", "them",
    "el", "ella", "ellos", "ellas",
    "ele", "ela", "eles", "elas",
    "you", "tu", "voce",
}
SELF_PRONOUNS_ALL = {join_for_lex(p) for p in _SELF_PRONOUNS_RAW}
OTHER_PRONOUNS_ALL = {join_for_lex(p) for p in _OTHER_PRONOUNS_RAW}

DIALECT_HINTS: Dict[str, Dict[str, set]] = {
    "en": {
        "aave": {"finna", "ion", "wanna", "tryna", "nah", "bruh", "fam", "yall", "ya'll"},
        "us_internet": {"lol", "lmao", "tbh", "ngl", "smh", "wtf", "idk", "fr", "frfr"},
        "uk": {"mate", "bloody", "cheers", "colour"},
        "aus": {"arvo", "heaps"},
    },
    "es": {
        "mx": {"wey", "guey", "nmms", "orale"},
        "spain": {"tio", "tia", "guay", "flipando"},
        "cone_sur": {"che", "boludo", "re", "capaz"},
    },
    "pt": {
        "br_sp": {"mano", "veio", "vei", "parca", "tipo"},
        "br_ne": {"oxente", "visse"},
        "pt_pt": {"fixe", "giro", "porreiro"},
        "br_net": {"kkk", "kkkk", "mds", "aff"},
    },
}


def _normalize_dialect_hints() -> None:
    for lang, dialects in DIALECT_HINTS.items():
        for dialect, cues in dialects.items():
            DIALECT_HINTS[lang][dialect] = {join_for_lex(c) for c in cues}


_normalize_dialect_hints()

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

# Self harm and threats

SELF_HARM_HARD_PATTERNS = [
    r"\bkill myself\b",
    r"\bwant to die\b",
    r"\bwant to disappear\b",
    r"\bend my life\b",
    r"\bno reason to live\b",
    r"\bself[-\s]?harm\b",
    r"\bhurt myself\b",
    r"\bsuicide\b",
    r"\bcant go on\b",
    r"\bcan[']?t go on\b",
    r"\bdone with life\b",
    # Spanish
    r"\bquiero morir\b",
    r"\bno quiero vivir\b",
    r"\bquitarme la vida\b",
    r"\bno puedo mas\b",
    r"\bno puedo más\b",
    r"\bsuicidio\b",
    r"\bhacerme daño\b",
    r"\bautolesi\w*\b",
    # Portuguese
    r"\bquero morrer\b",
    r"\bnão quero viver\b",
    r"\bnao quero viver\b",
    r"\b(vou|quero|queria) me matar\b",
    r"\btirar minha vida\b",
    r"\bsuic[ií]dio\b",
    r"\bauto[-\s]?mutila\w*\b",
    r"\bauto[-\s]?les\w*\b",
]
SELF_HARM_SOFT_PATTERNS = [
    r"\bkill me\b",
    r"\bi[' ]?m dead\b",
    r"\bim dead\b",
    r"\bme muero\b",
    r"\bme quero morrer\b",
    r"\bme matar\b",
]


def _compile_norm_regex(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(strip_diacritics(p), flags=re.IGNORECASE) for p in patterns]


SELF_HARM_HARD_REGEX = _compile_norm_regex(SELF_HARM_HARD_PATTERNS)
SELF_HARM_SOFT_REGEX = _compile_norm_regex(SELF_HARM_SOFT_PATTERNS)

THREAT_PATTERNS = [
    r"\bkill you\b",
    r"\bkill him\b",
    r"\bkill her\b",
    r"\bte voy a matar\b",
    r"\bvou te matar\b",
]
THREAT_REGEX = _compile_norm_regex(THREAT_PATTERNS)

AROUSAL_BETA = {
    "anger": 0.9,
    "disgust": 0.5,
    "fear": 0.9,
    "joy": 0.7,
    "sadness": 0.3,
    "passion": 0.8,
    "surprise": 1.0,
}

DOMAIN_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "romantic": {"passion": 1.12, "joy": 1.05},
    "relationship": {"passion": 1.08, "sadness": 1.03},
    "support": {"sadness": 1.06, "fear": 1.06},
    "customer_support": {"anger": 1.08, "sadness": 1.04, "disgust": 1.04},
    "therapy": {"sadness": 1.05, "fear": 1.05, "joy": 1.02},
    "social": {"joy": 1.04, "passion": 1.04},
    "whatsapp": {"joy": 1.03, "passion": 1.05, "sadness": 1.04},
    "chat": {"joy": 1.03, "passion": 1.03},
    "prayer": {"passion": 1.05, "joy": 1.03, "sadness": 1.02},
}

EMOTION_SIGN: Dict[str, float] = {
    "joy": 1.0,
    "passion": 1.0,
    "surprise": 0.4,
    "anger": -1.0,
    "disgust": -1.0,
    "fear": -1.0,
    "sadness": -1.0,
}


# =============================================================================
# Language detection and semantic index
# =============================================================================


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

        for lang in ("en", "es", "pt"):
            table = LEXICON_TOKEN.get(lang, {})
            if base in table:
                scores[lang] += 0.9

        if "ñ" in tok or "¿" in tok or "¡" in tok:
            scores["es"] += 1.2
        if any(ch in tok for ch in ["ã", "õ", "ç", "ê", "ô", "á", "é", "í", "ó", "ú"]):
            scores["pt"] += 1.0
        if any(sub in tok for sub in ["th", "ing"]):
            scores["en"] += 0.4

    total = sum(scores.values())
    if total <= 0:
        return {"en": 1 / 3, "es": 1 / 3, "pt": 1 / 3, "unknown": 0.0}

    for k in list(scores.keys()):
        scores[k] = scores[k] / total

    scores["unknown"] = 0.0
    return scores


def _compute_trigrams(word: str) -> List[str]:
    return [word[i: i + 3] for i in range(max(0, len(word) - 2))]


LEXICON_TRIGRAMS: Dict[str, Dict[str, List[str]]] = {"en": {}, "es": {}, "pt": {}}


def _build_semantic_index() -> None:
    for lang, table in LEXICON_TOKEN.items():
        tri = {}
        for token in table.keys():
            if len(token) >= 4:
                tri[token] = _compute_trigrams(token)
        LEXICON_TRIGRAMS[lang] = tri


# =============================================================================
# Risk and pragmatics helpers
# =============================================================================


def detect_self_harm_risk(text: str, humor_score: float = 0.0) -> str:
    text_search = normalize_for_search(text)
    hard_hits = 0
    soft_hits = 0

    for rx in SELF_HARM_HARD_REGEX:
        if rx.search(text_search):
            hard_hits += 1
    for rx in SELF_HARM_SOFT_REGEX:
        if rx.search(text_search):
            soft_hits += 1

    if hard_hits == 0 and soft_hits == 0:
        return "none"

    if hard_hits >= 2:
        return "severe"
    if hard_hits == 1:
        return "likely"

    if soft_hits > 0:
        if humor_score > 0.5:
            return "none"
        return "possible"

    return "none"


def detect_threat_level(text: str, humor_score: float = 0.0) -> str:
    text_search = normalize_for_search(text)
    hits = 0
    for rx in THREAT_REGEX:
        if rx.search(text_search):
            hits += 1
    if hits == 0:
        return "none"
    if humor_score > 0.7 and hits == 1:
        return "possible"
    if hits == 1:
        return "likely"
    return "severe"


def compute_humor_score(text: str, tokens: List[str]) -> float:
    t = text.lower()

    laugh_like = 0
    for tok in tokens:
        base = join_for_lex(tok)
        if base in {"lol", "lmao", "lmfao", "rofl", "haha", "jaja", "jeje", "kk", "kkk"}:
            laugh_like += 1
            continue
        if re.fullmatch(r"(ha){2,}|(ja){2,}|(je){2,}|k{2,}", base):
            laugh_like += 1

    emoji_laugh = 0
    for ch in text:
        if ch in {"😂", "🤣", "😹"}:
            emoji_laugh += 1

    hyperbole_patterns = [
        r"\bi[' ]?m dead\b",
        r"\bim dead\b",
        r"\bkill me\b",
        r"\bdied laughing\b",
        r"\bdying of laughter\b",
    ]
    hyperbole = 0
    for pat in hyperbole_patterns:
        if re.search(pat, t):
            hyperbole += 1

    laugh_score = min(1.0, (laugh_like + emoji_laugh * 1.5) / 4.0)
    hyperbole_score = min(1.0, hyperbole * 0.6)

    exclam = t.count("!")
    exclam_score = min(1.0, exclam / 6.0)

    score = 0.6 * laugh_score + 0.3 * hyperbole_score + 0.1 * exclam_score
    return max(0.0, min(1.0, score))


def compute_sarcasm_probability(
    text: str,
    mixture_hint: Optional[Dict[str, float]] = None,
    rhetorical_score: float = 0.0,
    humor_score: float = 0.0,
) -> float:
    t_raw = text.lower()
    t_norm = normalize_for_phrase(text)
    score = 0.0

    patterns = [
        "yeah right",
        "as if",
        "/s",
        "sure,",
        "sure.",
        "totally",
        '"sure"',
        "ok sure",
        "sure jan",
        "claro que si",
        "claro que nao",
        "ta bom",
        "ta bom entao",
        "ah claro",
        "ah, claro",
    ]
    for p in patterns:
        pn = normalize_for_phrase(p)
        if p in t_raw or pn in t_norm:
            score += 0.4

    if any(k in t_raw for k in ["lol", "lmao", "jaja", "jeje", "kkk", "kkkk"]):
        if any(
            w in t_raw for w in [
                "hate",
                "sad",
                "cry",
                "triste",
                "deprimido",
                "sozinho",
                "sozinha",
            ]
        ):
            score += 0.25

    if mixture_hint:
        pos = mixture_hint.get("joy", 0.0) + mixture_hint.get("passion", 0.0)
        neg = (
            mixture_hint.get("anger", 0.0)
            + mixture_hint.get("sadness", 0.0)
            + mixture_hint.get("disgust", 0.0)
        )
        if pos > 0.25 and neg > 0.25:
            score += 0.2

    score += 0.25 * min(1.0, rhetorical_score)
    score -= 0.2 * humor_score

    return max(0.0, min(1.0, score))


def choose_emoji(
    emotion: str,
    mixture: Dict[str, float],
    arousal: float,
    sarcasm_prob: float,
    global_intensity: float,
    max_emotion_intensity: float,
) -> str:
    # Neutral override for very low signal
    if global_intensity < 0.05 and max_emotion_intensity < 0.03:
        return "😐"

    base = BASE_EMOJI.get(emotion, "😐")

    if emotion == "joy" and sarcasm_prob > 0.55:
        return "🙃"

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
# Morphology expansion + lemma-based fallback
# =============================================================================


def _english_variants(word: str) -> List[str]:
    variants: List[str] = []
    if len(word) > 3:
        variants.append(word + "s")
        variants.append(word + "ed")
        variants.append(word + "ing")
        variants.append(word + "er")
        variants.append(word + "est")
    if word.endswith("y") and len(word) > 3:
        base = word[:-1]
        variants.append(base + "ies")
    return variants


def _spanish_variants(word: str) -> List[str]:
    variants: List[str] = []
    if word.endswith("o"):
        base = word[:-1]
        variants.extend(
            [
                base + "a",
                base + "os",
                base + "as",
                base + "ito",
                base + "itos",
                base + "ita",
                base + "itas",
            ]
        )
    if word.endswith("a"):
        base = word[:-1]
        variants.extend([base + "o", base + "os", base + "as"])
    if word.endswith("ito") or word.endswith("ita"):
        base = word[:-3]
        variants.extend([base + "o", base + "a"])
    if word.endswith("isimo"):
        base = word[: -len("isimo")]
        variants.extend([base + "o", base + "a"])
    return variants


def _portuguese_variants(word: str) -> List[str]:
    variants: List[str] = []
    if word.endswith("o"):
        base = word[:-1]
        variants.extend(
            [
                base + "a",
                base + "os",
                base + "as",
                base + "inho",
                base + "inha",
                base + "inhos",
                base + "inhas",
            ]
        )
    if word.endswith("a"):
        base = word[:-1]
        variants.extend([base + "o", base + "os", base + "as"])
    if word.endswith("inho") or word.endswith("inha"):
        base = word[:-4]
        variants.extend([base + "o", base + "a"])
    if word.endswith("issimo"):
        base = word[: -len("issimo")]
        variants.extend([base + "o", base + "a"])
    return variants


def _expand_lexicon_morphology() -> None:
    for lang, table in LEXICON_TOKEN.items():
        new_entries: Dict[str, Dict[str, float]] = {}
        for word, vec in list(table.items()):
            if len(word) < 3:
                continue
            if lang == "en":
                candidates = _english_variants(word)
            elif lang == "es":
                candidates = _spanish_variants(word)
            elif lang == "pt":
                candidates = _portuguese_variants(word)
            else:
                candidates = []
            for v in candidates:
                if not v:
                    continue
                if v in table or v in new_entries:
                    continue
                new_entries[v] = {e: val * 0.8 for e, val in vec.items()}
        table.update(new_entries)


_expand_lexicon_morphology()
_build_semantic_index()


def _scale_word_intensity(lang: str, words: List[str], factor: float) -> None:
    table = LEXICON_TOKEN.get(lang, {})
    for w in words:
        base = join_for_lex(w)
        if base in table:
            for e in EMOTIONS:
                table[base][e] = table[base].get(e, 0.0) * factor


_scale_word_intensity("en", ["furious", "livid", "outraged", "devastated"], 1.5)
_scale_word_intensity("en", ["annoyed", "irritated", "upset"], 0.7)
_scale_word_intensity("es", ["furioso", "furiosa", "luto"], 1.4)
_scale_word_intensity("pt", ["pistola", "luto"], 1.4)


@lru_cache(maxsize=8192)
def _semantic_guess(lang: str, token_norm: str) -> Dict[str, float]:
    table = LEXICON_TOKEN.get(lang, {})
    tri_index = LEXICON_TRIGRAMS.get(lang, {})
    if not table or not tri_index:
        return {}
    if len(token_norm) < 4:
        return {}
    t_tri = _compute_trigrams(token_norm)
    if not t_tri:
        return {}
    best_score = 0.0
    best_token = None
    set_t = set(t_tri)
    for lex_token, tri_list in tri_index.items():
        set_l = set(tri_list)
        inter = len(set_t & set_l)
        if inter == 0:
            continue
        union = len(set_t | set_l)
        if union == 0:
            continue
        sim = inter / float(union)
        if sim > best_score:
            best_score = sim
            best_token = lex_token
    if not best_token or best_score < 0.45:
        return {}
    base_vec = table[best_token]
    return {e: base_vec.get(e, 0.0) * best_score * 0.6 for e in EMOTIONS}


# NEW: simple lemma-based fallback (v30)


def lemmatize_en(tok_norm: str) -> str:
    """Very lightweight English lemmatizer for common inflections."""
    if len(tok_norm) > 4 and tok_norm.endswith("ing"):
        return tok_norm[:-3]
    if len(tok_norm) > 3 and tok_norm.endswith("ed"):
        return tok_norm[:-2]
    if len(tok_norm) > 3 and tok_norm.endswith("s"):
        # don't strip 'ss'
        if not tok_norm.endswith("ss"):
            return tok_norm[:-1]
    return tok_norm


def lemmatize_es(tok_norm: str) -> str:
    """Rough Spanish lemmatizer to collapse gender/number/participles."""
    suffixes = (
        "ciones", "ciones", "cion", "siones", "sion",
        "ados", "adas", "idos", "idas",
        "ando", "iendo",
        "ados", "adas",
        "ado", "ada", "ido", "ida",
        "itos", "itas", "ito", "ita",
        "os", "as", "o", "a",
    )
    for suf in suffixes:
        if tok_norm.endswith(suf) and len(tok_norm) > len(suf) + 2:
            return tok_norm[:-len(suf)]
    return tok_norm


def lemmatize_pt(tok_norm: str) -> str:
    """Rough Portuguese lemmatizer to collapse gender/number/participles."""
    suffixes = (
        "ções", "coes", "cao",
        "ados", "adas", "idos", "idas",
        "ando", "endo", "indo",
        "ado", "ada", "ido", "ida",
        "inhos", "inhas", "inho", "inha",
        "os", "as", "o", "a",
    )
    for suf in suffixes:
        if tok_norm.endswith(suf) and len(tok_norm) > len(suf) + 2:
            return tok_norm[:-len(suf)]
    return tok_norm


def lookup_with_lemma(lang: str, tok_norm: str) -> Dict[str, float]:
    """
    Lexicon lookup that first checks the surface form, then a simple lemma.
    """
    table = LEXICON_TOKEN.get(lang, {})
    if not table:
        return {}
    if tok_norm in table:
        return table[tok_norm]

    if lang == "en":
        lemma = lemmatize_en(tok_norm)
    elif lang == "es":
        lemma = lemmatize_es(tok_norm)
    elif lang == "pt":
        lemma = lemmatize_pt(tok_norm)
    else:
        lemma = tok_norm

    if lemma != tok_norm and lemma in table:
        return table[lemma]

    return {}


# =============================================================================
# Higher order analysis helpers
# =============================================================================


def compute_code_switch_score(tokens: List[str]) -> Tuple[float, Dict[str, int]]:
    lang_counts = {"en": 0, "es": 0, "pt": 0}
    for tok in tokens:
        if not any(ch.isalpha() for ch in tok):
            continue
        norm = join_for_lex(tok)
        for lang in ("en", "es", "pt"):
            table = LEXICON_TOKEN.get(lang, {})
            if norm in table:
                lang_counts[lang] += 1
    total_hits = sum(lang_counts.values())
    if total_hits < 4:
        return 0.0, lang_counts
    sorted_langs = sorted(lang_counts.items(), key=lambda kv: kv[1], reverse=True)
    primary_hits = sorted_langs[0][1]
    secondary_hits = sorted_langs[1][1]
    if secondary_hits == 0:
        return 0.0, lang_counts
    ratio = secondary_hits / float(total_hits)
    return max(0.0, min(1.0, ratio)), lang_counts


def compute_emotion_entropy(mixture: Dict[str, float]) -> float:
    eps = 1e-9
    probs = [max(eps, v) for v in mixture.values()]
    s = sum(probs)
    if s <= 0:
        return 0.0
    probs = [p / s for p in probs]
    entropy = 0.0
    for p in probs:
        entropy -= p * math.log(p, 2.0)
    return entropy


def compute_intensity_band(global_intensity: float) -> str:
    if global_intensity < 0.15:
        return "very_low"
    if global_intensity < 0.35:
        return "low"
    if global_intensity < 0.6:
        return "moderate"
    if global_intensity < 0.85:
        return "high"
    return "very_high"


def compute_clause_features(tokens: List[str]) -> Tuple[int, set]:
    token_bases = [join_for_lex(t) for t in tokens]
    all_contrast = set().union(*CONTRAST_WORDS.values())
    all_conditional = set().union(*CONDITIONAL_MARKERS.values())
    punctuation = {".", "!", "?", ";", ","}

    contrast_indices: List[int] = []
    conditional_indices: set = set()

    for idx, base in enumerate(token_bases):
        if base in all_contrast:
            contrast_indices.append(idx)

    for idx, base in enumerate(token_bases):
        if base in all_conditional:
            j = idx + 1
            steps = 0
            while j < len(tokens) and tokens[j] not in punctuation and steps < 12:
                conditional_indices.add(j)
                j += 1
                steps += 1

    last_contrast_index = contrast_indices[-1] if contrast_indices else -1
    return last_contrast_index, conditional_indices


def compute_negation_scope(tokens: List[str]) -> set:
    all_neg = set().union(*NEGATIONS.values())
    punctuation = {".", "!", "?", ";", ","}
    negated_positions: set = set()
    for i, tok in enumerate(tokens):
        base = join_for_lex(tok)
        if base in all_neg:
            j = i + 1
            steps = 0
            while j < len(tokens) and tokens[j] not in punctuation and steps < 7:
                negated_positions.add(j)
                j += 1
                steps += 1
    return negated_positions


def apply_valence_aware_negation(base_vec: Dict[str, float]) -> Dict[str, float]:
    pos = base_vec.get("joy", 0.0) + base_vec.get("passion", 0.0) + 0.4 * base_vec.get("surprise", 0.0)
    neg = (
        base_vec.get("anger", 0.0)
        + base_vec.get("sadness", 0.0)
        + base_vec.get("disgust", 0.0)
        + base_vec.get("fear", 0.0)
        + 0.4 * base_vec.get("surprise", 0.0)
    )
    if pos == 0 and neg == 0:
        return base_vec
    new_vec = dict(base_vec)
    if pos > neg:
        for e in ("joy", "passion", "surprise"):
            new_vec[e] *= 0.3
        new_vec["sadness"] += pos * 0.45
        new_vec["fear"] += pos * 0.25
        new_vec["anger"] += pos * 0.1
    else:
        for e in ("anger", "sadness", "fear", "disgust"):
            new_vec[e] *= 0.4
        relief = neg * 0.55
        new_vec["joy"] += relief * 0.7
        new_vec["passion"] += relief * 0.3
    return new_vec


def detect_dialect(tokens: List[str], lang_props: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
    token_bases = [join_for_lex(t) for t in tokens]
    scores: Dict[str, float] = {}
    for lang, dialects in DIALECT_HINTS.items():
        lang_weight = lang_props.get(lang, 0.0)
        if lang_weight <= 0:
            continue
        for dialect, cues in dialects.items():
            count = sum(1 for b in token_bases if b in cues)
            if count > 0:
                key = f"{lang}_{dialect}"
                scores[key] = scores.get(key, 0.0) + count * lang_weight
    if not scores:
        return "unknown", 0.0, {}
    best = max(scores.items(), key=lambda kv: kv[1])
    total = sum(scores.values())
    confidence = best[1] / total if total > 0 else 1.0
    return best[0], confidence, scores


def compute_temporal_cues(tokens: List[str], text_raw: str, lang_props: Dict[str, float]) -> Dict[str, float]:
    """
    Detect temporal shape:
    - persist: ongoing / repeated
    - resolve: getting better / relief
    - worsen: getting worse / deteriorating
    Works across EN / ES / PT using token markers and phrase cues.
    """
    bases = [join_for_lex(t) for t in tokens]
    persist = 0.0
    resolve = 0.0
    worsen = 0.0

    # Token level markers such as "still", "ya_no", "ainda", etc.
    for b in bases:
        for lang, words in TEMPORAL_PERSIST.items():
            if b in words:
                persist += 1.0 * lang_props.get(lang, 0.0)
        for lang, words in TEMPORAL_RESOLVE.items():
            if b in words:
                resolve += 1.0 * lang_props.get(lang, 0.0)

    # Phrase level cues on normalized text
    t_norm = normalize_for_phrase(text_raw)

    # English improvement phrases
    en_weight = lang_props.get("en", 1.0)
    en_resolve_phrases = [
        "getting better",
        "gotten better",
        "got better",
        "has gotten better",
        "has been getting better",
        "is getting better",
        "things are better",
        "feeling better",
        "feel better",
        "a bit better",
        "a little better",
        "better each day",
        "better every day",
        "steadily better",
        "has improved",
        "have improved",
        "is improving",
        "are improving",
        "turned out ok",
        "turned out okay",
    ]
    if any(p in t_norm for p in en_resolve_phrases):
        resolve += 0.9 * en_weight

    # English worsening phrases
    en_worsen_phrases = [
        "getting worse",
        "gotten worse",
        "got worse",
        "has gotten worse",
        "has been getting worse",
        "is getting worse",
        "only getting worse",
        "took a turn for the worse",
        "took a turn for the worst",
        "turn for the worse",
        "turn for the worst",
        "going downhill",
        "went downhill",
        "fell apart",
        "falling apart",
        "keeps getting worse",
        "kept getting worse",
        "is worse now",
        "are worse now",
    ]
    if any(p in t_norm for p in en_worsen_phrases):
        worsen += 0.9 * en_weight

    # Spanish improvement phrases
    es_weight = lang_props.get("es", 1.0)
    es_resolve_phrases = [
        "va mejor",
        "ha ido mejor",
        "ha estado mejor",
        "ha mejorado",
        "han mejorado",
        "esta mejorando",
        "está mejorando",
        "me siento mejor",
        "me estoy sintiendo mejor",   # FIXED: mejor, not melhor
        "cada dia mejor",             # FIXED: mejor
        "cada dia un poco mejor",
        "cada dia estoy mejor",
    ]
    if any(p in t_norm for p in es_resolve_phrases):
        resolve += 0.9 * es_weight

    # Spanish worsening phrases
    es_worsen_phrases = [
        "va peor",
        "ha ido peor",
        "ha estado peor",
        "se puso peor",
        "se ha puesto peor",
        "esta peor",
        "está peor",
        "se puso mal",
        "se ha puesto mal",
        "cada vez peor",
        "todo va peor",
        "todo se puso peor",
    ]
    if any(p in t_norm for p in es_worsen_phrases):
        worsen += 0.9 * es_weight

    # Portuguese improvement phrases
    pt_weight = lang_props.get("pt", 1.0)
    pt_resolve_phrases = [
        "vai melhorando",
        "tem melhorado",
        "tenho melhorado",
        "ficou melhor",
        "ficando melhor",
        "estou melhor",
        "to melhor",
        "tô melhor",
        "me sinto melhor",
        "me sentindo melhor",
        "cada dia melhor",
        "cada vez melhor",
    ]
    if any(p in t_norm for p in pt_resolve_phrases):
        resolve += 0.9 * pt_weight

    # Portuguese worsening phrases
    pt_worsen_phrases = [
        "vai piorando",
        "tem piorado",
        "tenho piorado",
        "ficou pior",
        "ficando pior",
        "esta pior",
        "está pior",
        "ta pior",
        "tá pior",
        "so piora",
        "só piora",
        "cada vez pior",
        "tudo piorou",
        "tudo ficou pior",
    ]
    if any(p in t_norm for p in pt_worsen_phrases):
        worsen += 0.9 * pt_weight

    # Generic cues shared across languages
    if "used to" in t_norm:
        persist += 0.5
        resolve += 0.3
    if "anymore" in t_norm:
        resolve += 0.7
    if "better now" in t_norm or "mejor ahora" in t_norm or "melhor agora" in t_norm:
        resolve += 1.0
    if "worse now" in t_norm or "peor ahora" in t_norm or "pior agora" in t_norm:
        worsen += 1.0

    return {
        "persist": min(3.0, persist),
        "resolve": min(3.0, resolve),
        "worsen": min(3.0, worsen),
    }


def apply_temporal_modulation(
    intensity: Dict[str, float],
    cues: Dict[str, float],
) -> Dict[str, float]:
    """
    Use temporal cues to reshape intensity rather than only scaling.
    - resolve dominant: shift some sadness / fear into joy / passion / surprise.
    - worsen dominant: shift some joy / passion into sadness / fear / anger.
    - persist dominant: gently boost negative persistence.
    """
    if not intensity:
        return intensity

    out = dict(intensity)
    persist = cues.get("persist", 0.0)
    resolve = cues.get("resolve", 0.0)
    worsen = cues.get("worsen", 0.0)

    # Getting better, relief case
    if resolve > persist and resolve >= worsen and resolve > 0.0:
        reduction = min(0.35, 0.12 * resolve)

        sad_before = out.get("sadness", 0.0)
        fear_before = out.get("fear", 0.0)

        factor = 1.0 - reduction
        out["sadness"] = max(0.0, sad_before * factor)
        out["fear"] = max(0.0, fear_before * factor)

        released = max(0.0, sad_before - out["sadness"]) + max(
            0.0, fear_before - out["fear"]
        )

        if released > 0.0:
            out["joy"] = out.get("joy", 0.0) + released * 0.7
            out["passion"] = out.get("passion", 0.0) + released * 0.1
            out["surprise"] = out.get("surprise", 0.0) + released * 0.2
        else:
            out["joy"] = out.get("joy", 0.0) * (
                1.0 + min(0.25, 0.10 * resolve)
            )

    # Getting worse, deterioration case
    elif worsen > resolve and worsen >= persist and worsen > 0.0:
        increase = min(0.35, 0.12 * worsen)

        joy_before = out.get("joy", 0.0)
        passion_before = out.get("passion", 0.0)

        factor = 1.0 - increase
        out["joy"] = max(0.0, joy_before * factor)
        out["passion"] = max(0.0, passion_before * factor)

        released = max(0.0, joy_before - out["joy"]) + max(
            0.0, passion_before - out["passion"]
        )

        if released > 0.0:
            out["sadness"] = out.get("sadness", 0.0) + released * 0.6
            out["fear"] = out.get("fear", 0.0) + released * 0.25
            out["anger"] = out.get("anger", 0.0) + released * 0.15
        else:
            scale = 1.0 + min(0.3, 0.12 * worsen)
            for e in ("sadness", "fear", "anger"):
                out[e] = out.get(e, 0.0) * scale

    # Persistent or ongoing difficulty
    elif persist > resolve and persist >= worsen and persist > 0.0:
        factor = 1.0 + min(0.25, 0.10 * persist)
        for e in ("sadness", "fear", "anger"):
            out[e] = out.get(e, 0.0) * factor

    return out


def apply_emotion_interactions(
    intensity: Dict[str, float],
    text_norm: str,
) -> Dict[str, float]:
    out = dict(intensity)

    def shift(from_e: str, to_e: str, k: float) -> None:
        a = out.get(from_e, 0.0)
        b = out.get(to_e, 0.0)
        if a <= 0 or b <= 0:
            return
        delta = k * min(a, b)
        if delta <= 0:
            return
        out[from_e] = max(0.0, a - delta)
        out[to_e] = b + delta

    if out.get("joy", 0.0) > 0.12 and out.get("surprise", 0.0) > 0.12:
        shift("joy", "surprise", 0.25)

    if out.get("anger", 0.0) > 0.12 and out.get("fear", 0.0) > 0.12:
        shift("anger", "fear", 0.3)

    miss_you_cues = [
        "i miss you",
        "missing you",
        "te extrano",
        "saudade",
        "sinto sua falta",
    ]
    if any(p in text_norm for p in miss_you_cues):
        if out.get("sadness", 0.0) > 0 and out.get("passion", 0.0) > 0:
            borrow = 0.2 * min(out["sadness"], out["passion"])
            donor = "joy" if out.get("joy", 0.0) >= out.get("surprise", 0.0) else "surprise"
            if out.get(donor, 0.0) >= borrow:
                out[donor] -= borrow
                out["sadness"] += borrow

    return out


def apply_bias_fairness(
    intensity: Dict[str, float],
    dialect_label: str,
    profanity_count: int,
    humor_score: float,
) -> Dict[str, float]:
    out = dict(intensity)
    if profanity_count <= 0:
        return out
    casual_dialects = {"en_aave", "en_us_internet", "pt_br_net", "es_mx"}
    if dialect_label in casual_dialects:
        neg_sum = out.get("anger", 0.0) + out.get("disgust", 0.0)
        if neg_sum <= 0:
            return out
        reduction = min(0.3, 0.12 * profanity_count * (0.5 + 0.5 * humor_score))
        scale = 1.0 - reduction
        out["anger"] *= scale
        out["disgust"] *= scale
    return out


def apply_plausibility_constraints(
    intensity: Dict[str, float],
    text_norm: str,
) -> Dict[str, float]:
    out = dict(intensity)
    total = sum(out.values())
    if total <= 0:
        return out
    joy = out.get("joy", 0.0)
    sad = out.get("sadness", 0.0)
    bittersweet_flag = any(k in text_norm for k in ["bittersweet", "agridulce", "agridoce", "sentimento agridoce"])
    if joy > 0.45 * total and sad > 0.45 * total and not bittersweet_flag:
        if joy >= sad:
            out["sadness"] *= 0.55
        else:
            out["joy"] *= 0.55
    return out


def apply_profanity_emphasis(
    intensity: Dict[str, float],
    profanity_count: int,
    exclam_count: int,
    strong_emoji_count: int,
    word_count_effective: int,
) -> Dict[str, float]:
    """
    When profanity is present, treat exclamations and strong emojis as
    intensity amplifiers for negative emotions, while gently damping
    positive ones so "Fuck!!!" feels stronger than "Fuck" but does not
    blow up to one hundred percent.
    """
    out = dict(intensity)
    total = sum(out.values())
    if total <= 0 or profanity_count <= 0:
        return out

    ex_n = min(1.0, exclam_count / 4.0)
    prof_n = min(1.0, profanity_count / 3.0)
    emoji_n = min(1.0, strong_emoji_count / 3.0)

    boost = 0.18 * prof_n + 0.15 * ex_n + 0.12 * emoji_n
    if word_count_effective <= 3:
        boost += 0.08
    boost = max(0.0, min(0.6, boost))

    if boost <= 0:
        return out

    for e in ("anger", "disgust", "fear", "sadness"):
        out[e] = out.get(e, 0.0) * (1.0 + boost)

    damp = max(0.0, 1.0 - 0.45 * boost)
    for e in ("joy", "passion"):
        out[e] = out.get(e, 0.0) * damp

    return out


def blend_with_context(
    current: Dict[str, float],
    prev: Optional[Dict[str, float]],
    decay: float = 0.7,
) -> Dict[str, float]:
    if not prev:
        return current
    out = {}
    for e in EMOTIONS:
        out[e] = decay * current.get(e, 0.0) + (1.0 - decay) * prev.get(e, 0.0)
    return out


def soft_cap_single_word_dominance(
    intensity: Dict[str, float],
    word_count_effective: int,
    profanity_count: int = 0,
) -> Dict[str, float]:
    """
    Cap dominance for very short texts, but keep redistribution inside
    the same valence family so that single word swears do not create
    fake joy or passion.
    """
    out = dict(intensity)
    total = sum(out.values())
    if total <= 0 or word_count_effective > 4:
        return out

    dominant = max(out, key=out.get)
    max_val = out[dominant]

    if word_count_effective <= 1:
        base_ratio = 0.65
        if profanity_count > 0 and EMOTION_SIGN.get(dominant, 0.0) < 0:
            base_ratio = 0.8
    elif word_count_effective == 2:
        base_ratio = 0.75
        if profanity_count > 0 and EMOTION_SIGN.get(dominant, 0.0) < 0:
            base_ratio = 0.85
    else:
        base_ratio = 0.75

    cap = base_ratio * total
    if max_val <= cap or cap <= 0:
        return out

    excess = max_val - cap
    out[dominant] = cap

    dom_sign = EMOTION_SIGN.get(dominant, 0.0)
    if dom_sign >= 0:
        candidates = [e for e in EMOTIONS if e != dominant and EMOTION_SIGN.get(e, 0.0) >= 0]
    else:
        candidates = [e for e in EMOTIONS if e != dominant and EMOTION_SIGN.get(e, 0.0) <= 0]

    if not candidates:
        candidates = [e for e in EMOTIONS if e != dominant]

    if not candidates:
        return out

    share = excess / len(candidates)
    for e in candidates:
        out[e] += share

    return out


def detect_speaker_target(text_lower: str) -> str:
    if re.search(r"\bi hate myself\b", text_lower) or re.search(r"\bme odio\b", text_lower) or re.search(
        r"\bme odeio\b", text_lower
    ):
        return "self"
    if re.search(r"\bi hate you\b", text_lower) or re.search(r"\bte odio\b", text_lower) or re.search(
        r"\bte odeio\b", text_lower
    ):
        return "other"
    if re.search(r"\bi hate this\b", text_lower) or re.search(r"\bodio esto\b", text_lower) or re.search(
        r"\bodeio isso\b", text_lower
    ):
        return "world"
    return "mixed"


def adjust_for_speaker_target(
    intensity: Dict[str, float],
    target: str,
) -> Dict[str, float]:
    out = dict(intensity)
    if target == "self":
        boost = out.get("anger", 0.0) * 0.5
        out["anger"] *= 0.6
        out["sadness"] += boost * 0.7
        out["fear"] += boost * 0.3
    elif target == "other":
        out["anger"] *= 1.15
        out["sadness"] *= 0.9
    elif target == "world":
        out["fear"] *= 1.05
        out["sadness"] *= 1.05
    return out


# NEW: hedge-aware shaping of intensity based on uncertainty vs certainty.


def apply_hedging_shape(
    intensity: Dict[str, float],
    uncertainty_count: int,
    certainty_count: int,
) -> Dict[str, float]:
    """
    If the user hedges a lot ("not sure", "no sé", "nao sei", etc.)
    and certainty markers are weaker, soften extremes of emotion —
    especially strong negative attributions.
    """
    out = dict(intensity)
    if uncertainty_count <= 1 or uncertainty_count <= certainty_count:
        return out

    # Hedge factor in [0, 1]
    diff = uncertainty_count - certainty_count
    hedge = max(0.0, min(1.0, diff / 4.0))

    # Stronger softening on negative than on positive
    neg_scale = 1.0 - 0.3 * hedge
    pos_scale = 1.0 - 0.15 * hedge

    for e in ("anger", "disgust", "fear", "sadness"):
        out[e] = max(0.0, out.get(e, 0.0) * neg_scale)
    for e in ("joy", "passion", "surprise"):
        out[e] = max(0.0, out.get(e, 0.0) * pos_scale)

    return out


# NEW: basic narrative-focus and distance shaping.


def compute_narrative_focus(
    self_pronoun_count: int,
    other_pronoun_count: int,
    word_count_effective: int,
) -> Tuple[str, float]:
    """
    Rough sense of whether text is self-focused, other-focused or neutral,
    and how distant it is (third-person descriptions vs "I feel ...").
    """
    if word_count_effective <= 0:
        return "neutral", 0.0

    self_ratio = self_pronoun_count / float(word_count_effective)
    other_ratio = other_pronoun_count / float(word_count_effective)

    if self_ratio > other_ratio and self_ratio > 0.08:
        focus = "self"
    elif other_ratio > self_ratio and other_ratio > 0.08:
        focus = "other"
    else:
        focus = "neutral"

    # Narrative distance: more "other" and less "self" implies more distance
    distance = max(0.0, min(1.0, other_ratio - self_ratio))
    return focus, distance


def apply_narrative_distance(
    intensity: Dict[str, float],
    focus: str,
    distance: float,
) -> Dict[str, float]:
    """
    If emotion is mostly about someone else (high narrative distance),
    gently reduce intensity to reflect that it may feel less immediate.
    """
    out = dict(intensity)
    if focus != "other" or distance <= 0.0:
        return out

    scale = 1.0 - 0.2 * min(1.0, distance * 2.0)
    if scale >= 1.0:
        return out
    for e in EMOTIONS:
        out[e] = max(0.0, out.get(e, 0.0) * scale)
    return out


# =============================================================================
# Emotion detector implementation
# =============================================================================


class EmotionDetector:
    """Local emotion detector for EN / ES / PT with seven core emotions."""

    def __init__(self, max_words: int = 250) -> None:
        self.max_words = max_words

    def analyze(
        self,
        text: str,
        domain: Optional[str] = None,
        prev_mixture: Optional[Dict[str, float]] = None,
    ) -> DetectorOutput:
        if not isinstance(text, str):
            raise InvalidTextError("Text must be a string.")
        text = normalize_text(text)
        if not text:
            raise InvalidTextError("Text cannot be empty.")

        tokens = tokenize(text)
        alpha_word_count = detect_word_count(tokens)
        emoji_token_count = detect_emoji_count(tokens)
        truncated = False

        if alpha_word_count == 0 and emoji_token_count == 0:
            stripped = re.sub(r"\s+", "", text)
            if not stripped:
                raise InvalidTextError("No meaningful words found in text.")

        if alpha_word_count > self.max_words:
            truncated = True
            trimmed_tokens: List[str] = []
            wc = 0
            for tok in tokens:
                trimmed_tokens.append(tok)
                if any(ch.isalpha() for ch in tok):
                    wc += 1
                    if wc >= self.max_words:
                        break
            tokens = trimmed_tokens
            text = _reconstruct_text(tokens)
            alpha_word_count = self.max_words

        word_count_effective = alpha_word_count + emoji_token_count
        if word_count_effective == 0:
            word_count_effective = 1

        lang_props = detect_language_proportions(text)

        all_intens = set().union(*INTENSIFIERS.values())
        all_dimins = set().union(*DIMINISHERS.values())
        all_profanities = set().union(*PROFANITIES.values())
        all_uncertainty = set().union(*UNCERTAINTY_WORDS.values())
        all_certainty = set().union(*CERTAINTY_WORDS.values())
        all_softeners = set().union(*PRAGMATIC_SOFTENERS.values())

        exclam_count = text.count("!")
        question_count = text.count("?")
        ellipsis_count = text.count("...")
        allcaps_count = 0
        elongated_count = 0
        profanity_count = 0
        strong_emoji_count = 0
        uncertainty_count = 0
        certainty_count = 0
        self_pronoun_count = 0
        other_pronoun_count = 0

        text_lower = text.lower()
        text_phrase_norm = normalize_for_phrase(text)

        # Phrase-level uncertainty / certainty hits
        unc_phrase_hits = 0.0
        cert_phrase_hits = 0.0
        for lang, phrases in UNCERTAINTY_PHRASES.items():
            lang_weight = lang_props.get(lang, 1.0)
            if lang_weight <= 0:
                continue
            for phrase in phrases:
                pn = normalize_for_phrase(phrase)
                if pn in text_phrase_norm:
                    unc_phrase_hits += lang_weight

        for lang, phrases in CERTAINTY_PHRASES.items():
            lang_weight = lang_props.get(lang, 1.0)
            if lang_weight <= 0:
                continue
            for phrase in phrases:
                pn = normalize_for_phrase(phrase)
                if pn in text_phrase_norm:
                    cert_phrase_hits += lang_weight

        # Token-level features and word-based uncertainty / certainty counts
        for tok in tokens:
            if len(tok) > 2 and tok.isupper() and any(ch.isalpha() for ch in tok):
                allcaps_count += 1
            if re.search(r"(.)\1\1", tok, flags=re.IGNORECASE):
                elongated_count += 1

            tok_norm = join_for_lex(tok)
            if tok_norm in all_profanities:
                profanity_count += 1
            if tok_norm in all_uncertainty:
                uncertainty_count += 1
            if tok_norm in all_certainty:
                certainty_count += 1
            if len(tok) == 1 and is_emoji(tok):
                strong_emoji_count += 1

        # Phrase-level contributions
        if unc_phrase_hits > 0:
            uncertainty_count += int(round(unc_phrase_hits))
        if cert_phrase_hits > 0:
            certainty_count += int(round(cert_phrase_hits))

        R_global = {e: 0.0 for e in EMOTIONS}
        rhetorical_score = 0.0
        phrase_hits_total = 0
        emoticon_hits_total = 0

        # Phrase lexicon hits
        for phrase_pat, vec in PHRASE_REGEX_NORM:
            hits = len(list(phrase_pat.finditer(text_phrase_norm)))
            if hits > 0:
                phrase_hits_total += hits
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0) * hits

        # Emoticons
        for pattern, vec in EMOTICON_PATTERNS:
            matches = list(pattern.finditer(text))
            if matches:
                emoticon_hits_total += len(matches)
            for _m in matches:
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0)

        if alpha_word_count == 0 and emoji_token_count == 0 and (phrase_hits_total > 0 or emoticon_hits_total > 0):
            word_count_effective = 1

        # Rhetorical patterns
        for pat, vec, weight in RHETORICAL_PATTERNS:
            raw_matches = list(pat.finditer(text_lower))
            norm_matches = list(pat.finditer(text_phrase_norm))
            count = max(len(raw_matches), len(norm_matches))
            if count > 0:
                rhetorical_score += weight * count
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0) * count

        # Metaphors
        for pat, vec in METAPHOR_PATTERNS:
            raw_matches = list(pat.finditer(text_lower))
            norm_matches = list(pat.finditer(text_phrase_norm))
            count = max(len(raw_matches), len(norm_matches))
            if count > 0:
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0) * count

        contrast_index, conditional_indices = compute_clause_features(tokens)
        negated_indices = compute_negation_scope(tokens)

        total_tokens = len(tokens)
        second_half_index = total_tokens // 2 if total_tokens > 0 else 0

        last_clause_start = 0
        for idx, tok in enumerate(tokens):
            if tok in {".", "!", "?"}:
                last_clause_start = idx + 1

        R = {e: R_global[e] for e in EMOTIONS}

        humor_score = compute_humor_score(text, tokens)
        dialect_label, dialect_conf, dialect_scores = detect_dialect(tokens, lang_props)
        temporal_cues = compute_temporal_cues(tokens, text, lang_props)

        punctuation = {".", "!", "?", ";", ","}

        # Token-level emotion contributions
        for i, tok in enumerate(tokens):
            tok_norm = join_for_lex(tok)

            if any(ch.isalpha() for ch in tok):
                if tok_norm in SELF_PRONOUNS_ALL:
                    self_pronoun_count += 1
                elif tok_norm in OTHER_PRONOUNS_ALL:
                    other_pronoun_count += 1

            if not any(ch.isalpha() for ch in tok) and not is_emoji(tok):
                continue

            base_vec = {e: 0.0 for e in EMOTIONS}

            # Lexicon + lemma + semantic guess
            for lang, weight in lang_props.items():
                if lang not in LEXICON_TOKEN or weight <= 0:
                    continue
                vec_lex = lookup_with_lemma(lang, tok_norm)
                if vec_lex:
                    for e in EMOTIONS:
                        base_vec[e] += vec_lex.get(e, 0.0) * weight
                else:
                    approx_vec = _semantic_guess(lang, tok_norm)
                    if approx_vec:
                        for e in EMOTIONS:
                            base_vec[e] += approx_vec.get(e, 0.0) * weight

            # Emoji-driven base vectors
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
                elif cp in {"❤", "♥", "💖", "💘", "💝", "💞", "💓"}:
                    base_vec["passion"] += 2.6
                    base_vec["joy"] += 1.1
                elif cp in {"💔"}:
                    base_vec["sadness"] += 2.8
                    base_vec["passion"] += 1.0

            if all(val == 0.0 for val in base_vec.values()):
                continue

            alpha = 1.0
            self_focus_factor = 1.0

            clause_weight = 1.0
            if contrast_index >= 0:
                if i > contrast_index:
                    clause_weight *= 1.35
                else:
                    clause_weight *= 0.95
            if i >= second_half_index:
                clause_weight *= 1.1
            if i >= last_clause_start:
                clause_weight *= 1.05

            conditional_weight = 0.8 if i in conditional_indices else 1.0

            # Look behind for intensifiers, hedges, etc.
            j = i - 1
            steps = 0
            while j >= 0 and steps < 3:
                prev_tok = tokens[j]
                prev_norm = join_for_lex(prev_tok)
                if prev_norm in all_intens:
                    alpha += 0.5
                if prev_norm in all_dimins or prev_norm in all_softeners:
                    alpha -= 0.25
                if prev_norm in FEEL_MARKERS_ALL:
                    alpha += 0.2
                    self_focus_factor = max(self_focus_factor, 1.3)
                if prev_norm in SELF_PRONOUNS_ALL:
                    self_focus_factor = max(self_focus_factor, 1.2)
                if prev_norm in OTHER_PRONOUNS_ALL and self_focus_factor == 1.0:
                    self_focus_factor = 0.9
                if prev_tok in punctuation:
                    break
                j -= 1
                steps += 1

            # Look ahead a little
            k = i + 1
            steps_ahead = 0
            while k < len(tokens) and steps_ahead < 2:
                next_tok = tokens[k]
                if next_tok in punctuation:
                    break
                next_norm = join_for_lex(next_tok)
                if next_norm in all_intens:
                    alpha += 0.3
                if next_norm in all_dimins or next_norm in all_softeners:
                    alpha -= 0.15
                k += 1
                steps_ahead += 1

            if tok_norm in all_uncertainty:
                alpha -= 0.1
            if tok_norm in all_certainty:
                alpha += 0.1

            if tok_norm in all_profanities:
                alpha += 0.4

            alpha = max(0.2, alpha)

            if i in negated_indices:
                base_vec = apply_valence_aware_negation(base_vec)

            local_factor = clause_weight * self_focus_factor * conditional_weight

            for e in EMOTIONS:
                R[e] += base_vec[e] * alpha * local_factor

        # Global arousal
        def norm(count: int, scale: float) -> float:
            return min(1.0, count / scale)

        ex_n = norm(exclam_count, 3)
        q_n = norm(question_count, 3)
        ellipsis_n = norm(ellipsis_count, 2)
        caps_n = norm(allcaps_count, 3)
        elong_n = norm(elongated_count, 3)
        prof_n = norm(profanity_count, 2)
        emoji_n = norm(strong_emoji_count, 2)

        raw_arousal = (
            0.4 * ex_n
            + 0.3 * q_n
            + 0.15 * ellipsis_n
            + 0.3 * caps_n
            + 0.4 * elong_n
            + 0.4 * prof_n
            + 0.5 * emoji_n
        )
        A = max(0.0, min(1.0, raw_arousal))

        # Arousal-aware boosting
        R_boosted: Dict[str, float] = {}
        for e in EMOTIONS:
            boosted = R[e] * (1.0 + AROUSAL_BETA[e] * A)
            R_boosted[e] = max(0.0, boosted)

        # Domain multipliers
        domain_key = (domain or "").lower().strip()
        if domain_key:
            for key, mults in DOMAIN_MULTIPLIERS.items():
                if key in domain_key:
                    for e, factor in mults.items():
                        if e in R_boosted:
                            R_boosted[e] *= factor

        total_strength = sum(R_boosted.values())
        if total_strength <= 0:
            if profanity_count > 0 or strong_emoji_count > 0 or ex_n > 0:
                share0 = {e: 0.0 for e in EMOTIONS}
                share0["anger"] = 0.4
                share0["disgust"] = 0.25
                share0["sadness"] = 0.2
                share0["fear"] = 0.1
                share0["surprise"] = 0.05
            else:
                share0 = {e: 1.0 / len(EMOTIONS) for e in EMOTIONS}
            global_intensity_base = 0.25 * A
        else:
            share0 = {e: R_boosted[e] / total_strength for e in EMOTIONS}
            global_intensity_base = 1.0 - math.exp(-total_strength / 8.0)

        global_intensity_base = max(0.0, min(global_intensity_base, 0.995))

        # Certainty vs uncertainty shaping
        uncertainty_score = min(1.0, uncertainty_count / 4.0) + 0.4 * q_n
        certainty_score = min(1.0, certainty_count / 4.0) + 0.6 * ex_n
        net_certainty = max(-1.0, min(1.0, certainty_score - uncertainty_score))

        short_len_factor = min(1.0, word_count_effective / 5.0)
        net_certainty_short = net_certainty * short_len_factor

        certainty_adjust = 1.0 + 0.35 * net_certainty_short
        certainty_adjust = max(0.5, min(1.4, certainty_adjust))

        global_intensity = global_intensity_base * certainty_adjust
        global_intensity = max(0.0, min(global_intensity, 0.995))

        max_share0 = max(share0.values()) if share0 else 0.0
        if global_intensity < 0.12 and max_share0 < 0.45:
            global_intensity *= 0.7
            global_intensity = max(0.0, min(global_intensity, 0.995))

        # Length cap for very short inputs
        length_cap = 1.0
        if word_count_effective <= 1:
            length_cap = 0.35
        elif word_count_effective == 2:
            length_cap = 0.55
        elif word_count_effective == 3:
            length_cap = 0.7
        global_intensity *= length_cap
        global_intensity = max(0.0, min(global_intensity, 0.995))

        # Base intensity vector
        intensity = {e: share0[e] * global_intensity for e in EMOTIONS}

        # Higher-order shaping
        intensity = apply_temporal_modulation(intensity, temporal_cues)
        intensity = apply_emotion_interactions(intensity, text_phrase_norm)

        speaker_target = detect_speaker_target(text_lower)
        intensity = adjust_for_speaker_target(intensity, speaker_target)

        intensity = apply_profanity_emphasis(
            intensity,
            profanity_count=profanity_count,
            exclam_count=exclam_count,
            strong_emoji_count=strong_emoji_count,
            word_count_effective=word_count_effective,
        )

        intensity = apply_bias_fairness(intensity, dialect_label, profanity_count, humor_score)

        # Hedge-aware softening (phrase + token uncertainty)
        intensity = apply_hedging_shape(
            intensity,
            uncertainty_count=uncertainty_count,
            certainty_count=certainty_count,
        )

        # Narrative focus / distance
        narrative_focus, narrative_distance = compute_narrative_focus(
            self_pronoun_count=self_pronoun_count,
            other_pronoun_count=other_pronoun_count,
            word_count_effective=word_count_effective,
        )
        intensity = apply_plausibility_constraints(intensity, text_phrase_norm)
        intensity = apply_narrative_distance(
            intensity,
            focus=narrative_focus,
            distance=narrative_distance,
        )

        # Context blending and short-text dominance smoothing
        intensity = blend_with_context(intensity, prev_mixture, decay=0.7)
        intensity = soft_cap_single_word_dominance(
            intensity,
            word_count_effective,
            profanity_count=profanity_count,
        )

        final_global_intensity = sum(intensity.values())
        if final_global_intensity > 1.0:
            scale = 1.0 / final_global_intensity
            for e in EMOTIONS:
                intensity[e] *= scale
            final_global_intensity = 1.0

        neutral_flag = final_global_intensity < 0.02 and total_strength < 0.5

        if final_global_intensity <= 0:
            intensity = {e: 0.0 for e in EMOTIONS}
            mixture_share = {e: 1.0 / len(EMOTIONS) for e in EMOTIONS}
        else:
            mixture_share = {e: intensity[e] / final_global_intensity for e in EMOTIONS}

        positive_intensity = (
            intensity.get("joy", 0.0)
            + intensity.get("passion", 0.0)
            + 0.5 * intensity.get("surprise", 0.0)
        )
        negative_intensity = (
            intensity.get("anger", 0.0)
            + intensity.get("disgust", 0.0)
            + intensity.get("fear", 0.0)
            + intensity.get("sadness", 0.0)
            + 0.5 * intensity.get("surprise", 0.0)
        )

        valence_raw = 0.0
        for e in EMOTIONS:
            valence_raw += intensity[e] * EMOTION_SIGN.get(e, 0.0)

        valence_norm = (valence_raw / final_global_intensity) if final_global_intensity > 1e-6 else 0.0
        valence_norm = max(-1.0, min(1.0, valence_norm))

        self_focus_score = min(1.0, self_pronoun_count / 3.0)
        other_focus_score = min(1.0, other_pronoun_count / 3.0)

        sarcasm_prob = compute_sarcasm_probability(
            text,
            mixture_hint=mixture_share,
            rhetorical_score=rhetorical_score,
            humor_score=humor_score,
        )

        sorted_emotions = sorted(mixture_share.items(), key=lambda kv: kv[1], reverse=True)
        top_label, top_val = sorted_emotions[0]
        second_val = sorted_emotions[1][1] if len(sorted_emotions) > 1 else 0.0
        delta = max(0.0, top_val - second_val)

        length_factor = min(1.0, word_count_effective / 12.0)
        strength_factor = min(1.0, delta * 3.0)
        intensity_factor = min(1.0, final_global_intensity)
        certainty_factor = (net_certainty + 1.0) / 2.0

        confidence = (
            0.25 * length_factor
            + 0.25 * strength_factor
            + 0.2 * (1.0 - sarcasm_prob)
            + 0.15 * intensity_factor
            + 0.15 * certainty_factor
        )
        confidence = round(max(0.0, min(1.0, confidence)), 3)

        dominant_label = top_label

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

        if neutral_flag:
            dominant_label = "neutral"
            current_label = "neutral"

        max_emotion_intensity = max(intensity.values()) if intensity else 0.0

        dominant_emoji = choose_emoji(
            dominant_label, mixture_share, A, sarcasm_prob, final_global_intensity, max_emotion_intensity
        )
        current_emoji = choose_emoji(
            current_label, mixture_share, A, sarcasm_prob, final_global_intensity, max_emotion_intensity
        )

        emotions_detail: Dict[str, EmotionResult] = {}
        for e in EMOTIONS:
            score = R_boosted[e]
            percent = intensity[e] * 100.0
            emoji = choose_emoji(e, mixture_share, A, sarcasm_prob, final_global_intensity, max_emotion_intensity)
            emotions_detail[e] = EmotionResult(
                label=e,
                emoji=emoji,
                score=round(score, 4),
                percent=round(percent, 3),
            )

        risk_level = detect_self_harm_risk(text, humor_score=humor_score)
        threat_level = detect_threat_level(text, humor_score=humor_score)

        dominant_result = EmotionResult(
            label=dominant_label,
            emoji=dominant_emoji,
            score=round(R_boosted.get(dominant_label, 0.0), 4),
            percent=round(intensity.get(dominant_label, 0.0) * 100.0, 3),
        )
        current_result = EmotionResult(
            label=current_label,
            emoji=current_emoji,
            score=round(R_boosted.get(current_label, 0.0), 4),
            percent=round(intensity.get(current_label, 0.0) * 100.0, 3),
        )

        primary_language = max(lang_props.items(), key=lambda kv: kv[1])[0] if lang_props else "unknown"

        code_switch_score, lang_token_counts = compute_code_switch_score(tokens)
        emotional_entropy = compute_emotion_entropy(intensity)
        intensity_band = compute_intensity_band(final_global_intensity)

        emotional_density = 0.0
        if word_count_effective > 0:
            emotional_density = min(1.0, total_strength / float(max(word_count_effective, 1)))

        return DetectorOutput(
            text=text,
            language=lang_props,
            emotions=emotions_detail,
            mixture_vector={k: round(v, 6) for k, v in intensity.items()},
            dominant=dominant_result,
            current=current_result,
            arousal=round(A, 3),
            sarcasm=round(sarcasm_prob, 3),
            humor=round(humor_score, 3),
            confidence=confidence,
            risk_level=risk_level,
            meta={
                "word_count_alpha": alpha_word_count,
                "word_count_effective": word_count_effective,
                "emoji_token_count": emoji_token_count,
                "phrase_hits_total": phrase_hits_total,
                "emoticon_hits_total": emoticon_hits_total,
                "truncated_to_max_words": truncated,
                "exclamation_count": exclam_count,
                "question_count": question_count,
                "ellipsis_count": ellipsis_count,
                "allcaps_count": allcaps_count,
                "elongated_count": elongated_count,
                "profanity_count": profanity_count,
                "strong_emoji_count": strong_emoji_count,
                "uncertainty_count": uncertainty_count,
                "certainty_count": certainty_count,
                "certainty_score": round(certainty_score, 3),
                "uncertainty_score": round(uncertainty_score, 3),
                "net_certainty": round(net_certainty, 3),
                "self_pronoun_count": self_pronoun_count,
                "other_pronoun_count": other_pronoun_count,
                "self_focus_score": round(self_focus_score, 3),
                "other_focus_score": round(other_focus_score, 3),
                "narrative_focus": narrative_focus,
                "narrative_distance": round(narrative_distance, 3),
                "hedging_softening_applied": bool(
                    uncertainty_count > 1 and uncertainty_count > certainty_count
                ),
                "domain": domain,
                "primary_language": primary_language,
                "total_strength": round(total_strength, 4),
                "global_intensity_base": round(global_intensity_base, 4),
                "global_intensity": round(final_global_intensity, 4),
                "positive_intensity": round(positive_intensity, 4),
                "negative_intensity": round(negative_intensity, 4),
                "valence_raw": round(valence_raw, 4),
                "valence_normalized": round(valence_norm, 4),
                "code_switch_score": round(code_switch_score, 3),
                "lang_token_counts": lang_token_counts,
                "emotional_entropy_bits": round(emotional_entropy, 4),
                "intensity_band": intensity_band,
                "emotional_density": round(emotional_density, 4),
                "dialect_label": dialect_label,
                "dialect_confidence": round(dialect_conf, 3),
                "dialect_scores": dialect_scores,
                "rhetorical_score": round(rhetorical_score, 3),
                "temporal_cues": temporal_cues,
                "speaker_target": speaker_target,
                "threat_level": threat_level,
                "prev_context_used": prev_mixture is not None,
                "neutral": neutral_flag,
                "max_emotion_intensity": round(max_emotion_intensity, 4),
            },
        )


_DEFAULT_DETECTOR = EmotionDetector()


def analyze_text(
    text: str,
    domain: Optional[str] = None,
    prev_mixture: Optional[Dict[str, float]] = None,
) -> DetectorOutput:
    """
    Convenience wrapper for one shot analysis.
    """
    return _DEFAULT_DETECTOR.analyze(
        text=text,
        domain=domain,
        prev_mixture=prev_mixture,
    )


def analyze_text_dict(
    text: str,
    domain: Optional[str] = None,
    prev_mixture: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    JSON safe wrapper for APIs.
    """
    return analyze_text(text=text, domain=domain, prev_mixture=prev_mixture).to_dict()


__all__ = [
    "EMOTIONS",
    "InvalidTextError",
    "EmotionResult",
    "DetectorOutput",
    "EmotionDetector",
    "analyze_text",
    "analyze_text_dict",
]


if __name__ == "__main__":
    samples = [
        "happy",
        "ok",
        "😢",
        "❤️",
        "I miss you so much",
        "No estoy bien hoy",
        "tô com saudade e meio triste",
        "are you kidding me??",
        "lol im dead 😂",
        "this was a hard long week but im okay now",
        "it has been a good day but it has gotten worse lately",
        "era um dia bom mas agora tudo vai piorando",
        "fue un buen dia pero ahora va peor y cada vez peor",
        "foi um dia dificil mas tem melhorado bastante",
        "Fuck",
        "Fuck!",
        "Fuck!!!",
        "Damnit!",
        "Son of a bitch",
        "How the hell do you think I feel?",
        "Fuck this shit",
        "no sé si estoy triste o solo cansado",
        "não sei se estou com medo ou só preocupado",
    ]
    for s in samples:
        out = analyze_text_dict(s)
        print("\nTEXT:", s)
        print("DOMINANT:", out["dominant"])
        print("MIXTURE:", out["mixture_vector"])
        print("META:", {
            "profanity_count": out["meta"]["profanity_count"],
            "uncertainty_count": out["meta"]["uncertainty_count"],
            "certainty_count": out["meta"]["certainty_count"],
            "hedging_softening_applied": out["meta"]["hedging_softening_applied"],
            "neutral": out["meta"]["neutral"],
            "global_intensity": out["meta"]["global_intensity"],
            "intensity_band": out["meta"]["intensity_band"],
        })
        print("CONF:", out["confidence"])
