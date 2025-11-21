# detector/detector.py
# High fidelity local emotion detector v15-espt
# Seven core emotions, 1 to 250 words, English / Spanish / Portuguese only.

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
    confidence: float
    risk_level: str
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
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


# -----------------------------------------------------------------------------
# Base lexicon
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
        "burntout",
        "empty",
        "numb",
        "broken",
        "lost",
        "exhausted",
        "hopeless",
        "overwhelmed",
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
        "pánico",
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
        "alegría",
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
        "buenísimo",
        "felicidad",
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
        "pena",
        "dolor",
        "tristeza",
        "depre",
        "bajoneado",
        "bajoneada",
        "vacío",
        "vacio",
        "rota",
        "roto",
        "apagado",
        "apagada",
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
        "increíble",
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
        "chévere",
        "chido",
        "bacano",
        "brutal",
        "guay",
        "que_lindo",
        "precioso",
        "preciosa",
        "lindisimo",
        "lindísima",
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
        "cariño",
        "carino",
        "mi_vida",
        "mi_amor",
        "cielito",
        "corazon",
        "corazón",
        "tesoro",
        "cosita",
        "amor_de_mi_vida",
    ],
    2.1,
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
        "ódio",
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
        "pânico",
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
        "solidao",
        "chorando",
        "chorei",
        "chorar",
        "mágoa",
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
        "não_acredito",
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
        "incrível",
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
        "não_to_bem",
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
        "mozão",
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
        "difícil",
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
        "difícil",
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
        "perdí",
        "falleció",
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
        "ausência",
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

# Multiword phrase lexicon (normalized literally as plain text)
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
    "feeling blessed": _vec(joy=2.0, passion=0.5),
    "grateful for you": _vec(joy=1.8, passion=0.8),
    "in love with you": _vec(passion=2.7, joy=1.3),
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
    # Spanish
    "no aguanto más": _vec(anger=1.5, sadness=2.0),
    "no aguanto mas": _vec(anger=1.5, sadness=2.0),
    "no lo soporto": _vec(anger=2.0, disgust=1.0),
    "me rompe el corazón": _vec(sadness=3.0),
    "me parte el corazón": _vec(sadness=3.0),
    "no fue una semana fácil": _vec(sadness=2.3, fear=0.7),
    "no fue una semana facil": _vec(sadness=2.3, fear=0.7),
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
    # Spanish grief and bittersweet
    "no puedo creer que se haya ido": _vec(sadness=3.1, surprise=0.9),
    "no puedo creer que se fue": _vec(sadness=3.0, surprise=0.9),
    "está en un lugar mejor": _vec(sadness=2.4, joy=1.4),
    "esta en un lugar mejor": _vec(sadness=2.4, joy=1.4),
    "sentimiento agridulce": _vec(sadness=2.2, joy=1.4),
    # Portuguese
    "não aguento mais": _vec(anger=1.5, sadness=2.0),
    "nao aguento mais": _vec(anger=1.5, sadness=2.0),
    "me parte o coração": _vec(sadness=3.0),
    "me parte meu coração": _vec(sadness=3.0),
    "me parte o coracao": _vec(sadness=3.0),
    "nao foi uma semana facil": _vec(sadness=2.3, fear=0.7),
    "não foi uma semana fácil": _vec(sadness=2.3, fear=0.7),
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
]

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
        "hella",
        "highkey",
        "lowkey",
        "crazy",
        "crazyyy",
        "mega",
        "ultra",
    },
    "es": {"muy", "re", "súper", "super", "demasiado", "tan"},
    "pt": {"muito", "super", "demais", "tão", "tao", "pra", "bastante"},
}
DIMINISHERS = {
    "en": {"kind", "kinda", "sort", "little", "bit", "maybe", "possibly"},
    "es": {"un", "poco", "algo", "quizas", "quizás", "tal_vez"},
    "pt": {"um", "pouco", "meio", "talvez"},
}

NEGATIONS = {
    "en": {
        "not",
        "never",
        "no",
        "dont",
        "don't",
        "isnt",
        "isn't",
        "cant",
        "can't",
        "wont",
        "won't",
        "nothing",
    },
    "es": {"no", "nunca", "jamás", "jamas", "nada"},
    "pt": {"não", "nao", "nem", "nunca", "jamais"},
}

CONTRAST_WORDS = {
    "en": {"but", "however", "though", "yet"},
    "es": {"pero", "sin", "embargo", "aunque"},
    "pt": {"mas", "porém", "porem", "contudo", "embora"},
}

PROFANITIES = {
    "en": {"fuck", "fucking", "shit", "bitch", "asshole", "damn", "wtf"},
    "es": {"mierda", "joder", "carajo", "puta", "pendejo", "pendeja"},
    "pt": {"merda", "porra", "caralho", "puta", "bosta", "pqp"},
}

# Uncertainty and certainty markers
UNCERTAINTY_WORDS = {
    "en": {
        "maybe",
        "perhaps",
        "kinda",
        "sorta",
        "guess",
        "idk",
        "idk.",
        "idk,",
        "unsure",
        "not_sure",
        "probably",
        "possibly",
    },
    "es": {
        "quizas",
        "quizás",
        "tal",
        "vez",
        "tal_vez",
        "supongo",
        "no_se",
        "no_sé",
        "creo",
    },
    "pt": {
        "talvez",
        "acho",
        "acho_que",
        "nao_sei",
        "não_sei",
        "provavelmente",
        "quem_sabe",
    },
}

CERTAINTY_WORDS = {
    "en": {"definitely", "for_sure", "forreal", "fr", "frfr", "no_cap", "literally"},
    "es": {"definitivamente", "seguro", "segura", "claro", "obvio"},
    "pt": {"com_certeza", "certeza", "claro", "obvio", "óbvio"},
}

# Feel / experience markers to boost nearby adjectives
FEEL_MARKERS = {
    "en": {"feel", "feeling", "felt", "feelings"},
    "es": {"siento", "sentir", "sentido", "sintiendo", "me_siento"},
    "pt": {"sinto", "sentir", "sentido", "sentindo", "me_sinto"},
}
FEEL_MARKERS_ALL = set().union(*FEEL_MARKERS.values())

# Language function words for detection
LANG_FUNCTION_WORDS = {
    "en": {"the", "and", "is", "am", "are", "you", "i", "my", "me", "it", "of", "to", "in"},
    "es": {"el", "la", "los", "las", "y", "es", "soy", "eres", "estoy", "yo", "tú", "tu", "mi", "me"},
    "pt": {"o", "a", "os", "as", "e", "é", "sou", "estou", "você", "voce", "eu", "meu", "minha"},
}

# Self vs other pronoun hints
SELF_PRONOUNS_ALL = {
    "i",
    "im",
    "i'm",
    "me",
    "my",
    "mine",
    "yo",
    "mi",
    "mio",
    "mia",
    "mios",
    "mias",
    "eu",
    "meu",
    "minha",
    "meus",
    "minhas",
}
OTHER_PRONOUNS_ALL = {
    "he",
    "she",
    "they",
    "him",
    "her",
    "them",
    "el",
    "ella",
    "ellos",
    "ellas",
    "ele",
    "ela",
    "eles",
    "elas",
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

# Self harm and suicide risk patterns
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
    r"\bcant go on\b",
    r"\bcan[']?t go on\b",
    r"\bdone with life\b",
    # Spanish
    r"\bquiero morir\b",
    r"\bno quiero vivir\b",
    r"\bquitarme la vida\b",
    r"\bmat(?:arme|arme)\b",
    r"\bsuicidio\b",
    r"\bhacerme daño\b",
    r"\bautolesi",
    r"\bno puedo mas\b",
    r"\bno puedo más\b",
    # Portuguese
    r"\bquero morrer\b",
    r"\bnão quero viver\b",
    r"\bnao quero viver\b",
    r"\bme matar\b",
    r"\btirar minha vida\b",
    r"\bsuic[ií]dio\b",
    r"\bauto[-\s]?mutila",
    r"\bauto[-\s]?les",
    r"\nnao aguento viver\b",
    r"\bnão aguento viver\b",
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

# Simple domain based multipliers for fine tuning in different contexts
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

# Emotion sign for valence
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
# Utility functions
# =============================================================================


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    return text.strip()


TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text)


def is_emoji(char: str) -> bool:
    if not char:
        return False
    cp = ord(char)
    return (
        0x1F300 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x26FF
        or 0x2700 <= cp <= 0x27BF
        or 0xFE00 <= cp <= 0xFE0F
    )


def join_for_lex(token: str) -> str:
    """Normalize token for lexicon and marker lookups."""
    token = token.strip()
    if token.startswith("#") or token.startswith("@"):
        token = token[1:]
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

        # Function words as strong hints
        for lang, fn_words in LANG_FUNCTION_WORDS.items():
            if base in fn_words:
                scores[lang] += 1.5

        # Direct emotional lexicon hits as language hints
        for lang in ("en", "es", "pt"):
            table = LEXICON_TOKEN.get(lang, {})
            if base in table:
                scores[lang] += 0.9

        # Character based hints
        if "ñ" in tok or "¿" in tok or "¡" in tok:
            scores["es"] += 1.2
        if any(ch in tok for ch in ["ã", "õ", "ç", "ê", "ô", "á", "é", "í", "ó", "ú"]):
            scores["pt"] += 1.0
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
        "ok sure",
        "sure jan",
        "claro que sí",
        "claro que si",
        "claro que nao",
        "claro que não",
        "tá bom",
        "ta bom",
        "tá bom então",
        "ta bom entao",
        "ah claro",
        "ah, claro",
    ]
    for p in patterns:
        if p in t:
            score += 0.4

    if any(k in t for k in ["lol", "lmao", "jaja", "jeje", "kkk", "kkkk"]):
        if any(
            w in t
            for w in [
                "hate",
                "sad",
                "cry",
                "triste",
                "deprimido",
                "deprimida",
                "sozinho",
                "sozinha",
            ]
        ):
            score += 0.3

    if mixture_hint:
        pos = mixture_hint.get("joy", 0.0) + mixture_hint.get("passion", 0.0)
        neg = (
            mixture_hint.get("anger", 0.0)
            + mixture_hint.get("sadness", 0.0)
            + mixture_hint.get("disgust", 0.0)
        )
        if pos > 0.25 and neg > 0.25:
            score += 0.2

    return max(0.0, min(1.0, score))


def choose_emoji(
    emotion: str, mixture: Dict[str, float], arousal: float, sarcasm_prob: float
) -> str:
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
# Morphology expansion to cover dialects and inflections
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
    if word.endswith("isimo") or word.endswith("ísimo"):
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
    if word.endswith("issimo") or word.endswith("íssimo"):
        base = word[: -len("issimo")]
        variants.extend([base + "o", base + "a"])
    return variants


def _expand_lexicon_morphology() -> None:
    """Generate simple morphological variants to widen coverage."""
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


# =============================================================================
# Higher order analysis helpers
# =============================================================================


def compute_code_switch_score(tokens: List[str]) -> Tuple[float, Dict[str, int]]:
    """Rough estimate of code switching intensity based on lexicon hits per language."""
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
    """Shannon style entropy over the mixture vector in bits, for emotional complexity."""
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
    """Map global intensity into coarse band labels."""
    if global_intensity < 0.15:
        return "very_low"
    if global_intensity < 0.35:
        return "low"
    if global_intensity < 0.6:
        return "moderate"
    if global_intensity < 0.85:
        return "high"
    return "very_high"


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
        all_negations = set().union(*NEGATIONS.values())
        all_intens = set().union(*INTENSIFIERS.values())
        all_dimins = set().union(*DIMINISHERS.values())
        all_contrast = set().union(*CONTRAST_WORDS.values())
        all_profanities = set().union(*PROFANITIES.values())
        all_uncertainty = set().union(*UNCERTAINTY_WORDS.values())
        all_certainty = set().union(*CERTAINTY_WORDS.values())

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

        token_low = [tok.lower() for tok in tokens]

        for tok in tokens:
            if len(tok) > 2 and tok.isupper() and any(ch.isalpha() for ch in tok):
                allcaps_count += 1
            if re.search(r"(.)\1\1", tok, flags=re.IGNORECASE):
                elongated_count += 1
            if join_for_lex(tok) in all_profanities:
                profanity_count += 1
            if len(tok) == 1 and is_emoji(tok):
                strong_emoji_count += 1

        # Global phrase and emoticon contributions
        R_global = {e: 0.0 for e in EMOTIONS}
        text_lower = text.lower()
        for phrase, vec in PHRASE_LEXICON.items():
            if phrase in text_lower:
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0)

        for pattern, vec in EMOTICON_PATTERNS:
            for _m in pattern.finditer(text):
                for e in EMOTIONS:
                    R_global[e] += vec.get(e, 0.0)

        contrast_index = -1
        for idx, tok in enumerate(token_low):
            if join_for_lex(tok) in all_contrast:
                contrast_index = idx

        total_tokens = len(tokens)
        second_half_index = total_tokens // 2 if total_tokens > 0 else 0

        last_clause_start = 0
        for idx, tok in enumerate(tokens):
            if tok in {".", "!", "?"}:
                last_clause_start = idx + 1

        R = {e: R_global[e] for e in EMOTIONS}

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
            for lang, weight in lang_props.items():
                if lang not in LEXICON_TOKEN:
                    continue
                table = LEXICON_TOKEN[lang]
                if tok_norm in table:
                    for e in EMOTIONS:
                        base_vec[e] += table[tok_norm].get(e, 0.0) * weight

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
                elif cp in {"❤", "❤️", "💖", "💘", "💝", "💞", "💓"}:
                    base_vec["passion"] += 2.6
                    base_vec["joy"] += 1.1
                elif cp in {"💔"}:
                    base_vec["sadness"] += 2.8
                    base_vec["passion"] += 1.0

            if all(val == 0.0 for val in base_vec.values()):
                continue

            alpha = 1.0
            neg_factor = 1.0
            self_focus_factor = 1.0

            j = i - 1
            steps = 0
            while j >= 0 and steps < 3:
                prev_norm = join_for_lex(tokens[j])
                if prev_norm in all_intens:
                    alpha += 0.5
                if prev_norm in all_dimins:
                    alpha -= 0.3
                if prev_norm in all_negations:
                    neg_factor = -0.8
                if prev_norm in all_uncertainty:
                    alpha -= 0.2
                if prev_norm in all_certainty:
                    alpha += 0.15
                if prev_norm in SELF_PRONOUNS_ALL:
                    self_focus_factor = max(self_focus_factor, 1.2)
                if prev_norm in OTHER_PRONOUNS_ALL and self_focus_factor == 1.0:
                    self_focus_factor = 0.9
                if prev_norm in FEEL_MARKERS_ALL:
                    alpha += 0.2
                    self_focus_factor = max(self_focus_factor, 1.3)
                if tokens[j] in {".", "!", "?"}:
                    break
                j -= 1
                steps += 1

            if tok_norm in all_uncertainty:
                uncertainty_count += 1
                alpha -= 0.1
            if tok_norm in all_certainty:
                certainty_count += 1
                alpha += 0.1

            if tok_norm in all_profanities:
                alpha += 0.4

            alpha = max(0.2, alpha)

            clause_weight = 1.3 if i > contrast_index >= 0 else 1.0
            if i >= second_half_index:
                clause_weight *= 1.1
            if i >= last_clause_start:
                clause_weight *= 1.05

            local_factor = clause_weight * self_focus_factor

            for e in EMOTIONS:
                contribution = base_vec[e] * alpha * neg_factor * local_factor
                R[e] += contribution

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

        R_boosted: Dict[str, float] = {}
        for e in EMOTIONS:
            boosted = R[e] * (1.0 + AROUSAL_BETA[e] * A)
            R_boosted[e] = max(0.0, boosted)

        # Optional domain adjustments
        domain_key = (domain or "").lower().strip()
        if domain_key:
            for key, mults in DOMAIN_MULTIPLIERS.items():
                if key in domain_key:
                    for e, factor in mults.items():
                        if e in R_boosted:
                            R_boosted[e] *= factor

        total_strength = sum(R_boosted.values())
        if total_strength <= 0:
            share = {e: 1.0 / len(EMOTIONS) for e in EMOTIONS}
        else:
            share = {e: R_boosted[e] / total_strength for e in EMOTIONS}

        # Global intensity base with soft saturation.
        if total_strength <= 0:
            global_intensity_base = 0.0
        else:
            global_intensity_base = 1.0 - math.exp(-total_strength / 8.0)

        global_intensity_base = max(0.0, min(global_intensity_base, 0.995))

        # Certainty and uncertainty scaling based on language markers and punctuation.
        uncertainty_score = min(1.0, uncertainty_count / 4.0) + 0.4 * q_n
        certainty_score = min(1.0, certainty_count / 4.0) + 0.6 * ex_n
        net_certainty = max(-1.0, min(1.0, certainty_score - uncertainty_score))

        certainty_adjust = 1.0 + 0.35 * net_certainty
        certainty_adjust = max(0.5, min(1.4, certainty_adjust))

        global_intensity = global_intensity_base * certainty_adjust
        global_intensity = max(0.0, min(global_intensity, 0.995))

        # Neutral gate so weak, ambiguous signals stay low
        max_share = max(share.values()) if share else 0.0
        if global_intensity < 0.12 and max_share < 0.45:
            global_intensity *= 0.7
            global_intensity = max(0.0, min(global_intensity, 0.995))

        intensity = {e: share[e] * global_intensity for e in EMOTIONS}

        # Valence and polarity metrics
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
            sign = EMOTION_SIGN.get(e, 0.0)
            valence_raw += intensity[e] * sign

        if global_intensity > 1e-6:
            valence_norm = valence_raw / global_intensity
        else:
            valence_norm = 0.0
        valence_norm = max(-1.0, min(1.0, valence_norm))

        self_focus_score = min(1.0, self_pronoun_count / 3.0)
        other_focus_score = min(1.0, other_pronoun_count / 3.0)

        sarcasm_prob = compute_sarcasm_probability(text, share)
        sorted_emotions = sorted(share.items(), key=lambda kv: kv[1], reverse=True)
        top_label, top_val = sorted_emotions[0]
        second_val = sorted_emotions[1][1] if len(sorted_emotions) > 1 else 0.0
        delta = max(0.0, top_val - second_val)

        length_factor = min(1.0, word_count / 12.0)
        strength_factor = min(1.0, delta * 3.0)
        intensity_factor = global_intensity
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

        dominant_emoji = choose_emoji(dominant_label, share, A, sarcasm_prob)
        current_emoji = choose_emoji(current_label, share, A, sarcasm_prob)

        emotions_detail: Dict[str, EmotionResult] = {}
        for e in EMOTIONS:
            score = R_boosted[e]
            percent = intensity[e] * 100.0
            emoji = choose_emoji(e, share, A, sarcasm_prob)
            emotions_detail[e] = EmotionResult(
                label=e,
                emoji=emoji,
                score=round(score, 4),
                percent=round(percent, 3),
            )

        risk_level = detect_self_harm_risk(text)

        dominant_result = EmotionResult(
            label=dominant_label,
            emoji=dominant_emoji,
            score=round(R_boosted[dominant_label], 4),
            percent=round(intensity[dominant_label] * 100.0, 3),
        )
        current_result = EmotionResult(
            label=current_label,
            emoji=current_emoji,
            score=round(R_boosted[current_label], 4),
            percent=round(intensity[current_label] * 100.0, 3),
        )

        primary_language = max(lang_props.items(), key=lambda kv: kv[1])[0] if lang_props else "unknown"

        code_switch_score, lang_token_counts = compute_code_switch_score(tokens)
        emotional_entropy = compute_emotion_entropy(intensity)
        intensity_band = compute_intensity_band(global_intensity)

        emotional_density = 0.0
        if word_count > 0:
            emotional_density = min(1.0, total_strength / float(max(word_count, 1)))

        output = DetectorOutput(
            text=text,
            language=lang_props,
            emotions=emotions_detail,
            mixture_vector={k: round(v, 6) for k, v in intensity.items()},
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
                "domain": domain,
                "primary_language": primary_language,
                "total_strength": round(total_strength, 4),
                "global_intensity_base": round(global_intensity_base, 4),
                "global_intensity": round(global_intensity, 4),
                "positive_intensity": round(positive_intensity, 4),
                "negative_intensity": round(negative_intensity, 4),
                "valence_raw": round(valence_raw, 4),
                "valence_normalized": round(valence_norm, 4),
                "code_switch_score": round(code_switch_score, 3),
                "lang_token_counts": lang_token_counts,
                "emotional_entropy_bits": round(emotional_entropy, 4),
                "intensity_band": intensity_band,
                "emotional_density": round(emotional_density, 4),
            },
        )
        return output


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
