# advanced_detector.py
# High fidelity local emotion detector v6.0, multilingual.
# Seven core dimensions with richer nuance.
# Purely local engine with support for:
# English, Spanish, Portuguese, French, Italian, German, Dutch, Polish
# plus phrase level support for Chinese, Japanese, and Korean.
#
# Tuned for very short inputs (1-2 words or emoji only)
# up to about 250 words of text.

from __future__ import annotations

import re
import difflib
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Tuple, Optional, Set
from functools import lru_cache

try:  # pragma: no cover
    from .errors import InvalidTextError  # type: ignore
except Exception:  # pragma: no cover
    class InvalidTextError(ValueError):
        pass


# =============================================================================
# Data model
# =============================================================================

CORE_KEYS = ("anger", "disgust", "fear", "joy", "sadness", "passion", "surprise")


@dataclass
class EmotionResult:
    anger: float
    disgust: float
    fear: float
    joy: float
    sadness: float
    passion: float
    surprise: float
    dominant_emotion: str
    low_signal: bool = False
    secondary_emotion: str = "N/A"
    mixed_state: bool = False
    # v6 meta metrics
    valence: float = 0.0
    arousal: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DetectorConfig:
    """
    Simple tuning hooks for the local detector.

    You can call set_detector_config(window_min_tokens=80, ...)
    from application code without editing this file.
    """

    # Sliding window mode for longer texts
    window_min_tokens: int = 60
    window_size_tokens: int = 40
    window_step_tokens: int = 20

    # Threshold for special short text handling
    short_text_token_threshold: int = 3


DEFAULT_CONFIG = DetectorConfig()


def set_detector_config(**kwargs: Any) -> None:
    """
    Update the default detector configuration at runtime.

    Example:
        set_detector_config(window_min_tokens=80, short_text_token_threshold=4)
    """
    for key, value in kwargs.items():
        if hasattr(DEFAULT_CONFIG, key):
            setattr(DEFAULT_CONFIG, key, value)


# =============================================================================
# Unicode helpers
# =============================================================================


def _strip_accents(text: str) -> str:
    """
    Remove combining accents for accent-insensitive matching.
    """
    try:
        norm = unicodedata.normalize("NFD", text)
        return "".join(ch for ch in norm if not unicodedata.combining(ch))
    except Exception:
        return text


# =============================================================================
# Multilingual lexicons and resources
# =============================================================================

# JOY
JOY: Set[str] = {
    # English base
    "love",
    "loved",
    "loving",
    "lovely",
    "like",
    "liked",
    "likes",
    "happy",
    "happi",
    "joy",
    "joyful",
    "cheer",
    "cheerful",
    "glad",
    "content",
    "contented",
    "relief",
    "relieved",
    "calm",
    "serene",
    "peace",
    "peaceful",
    "hope",
    "hopeful",
    "optimism",
    "optimistic",
    "delight",
    "delighted",
    "delightful",
    "pleased",
    "smile",
    "laugh",
    "laughing",
    "laughed",
    "awesome",
    "amazing",
    "wonderful",
    "fantastic",
    "great",
    "good",
    "fine",
    "ok",
    "okay",
    "alright",
    "relaxed",
    "chill",
    "chilling",
    "vibe",
    "vibes",
    "vibing",
    "proud",
    "success",
    "win",
    "won",
    "dub",
    "w",
    "best",
    "perfect",
    "beautiful",
    "brilliant",
    "cute",
    "enjoy",
    "enjoyed",
    "enjoying",
    "thrilled",
    "ecstatic",
    "elated",
    "euphoric",
    "uplift",
    "brighten",
    "grace",
    "gratitude",
    "grateful",
    "thankful",
    "support",
    "supported",
    "comfort",
    "comfortable",
    "comfy",
    "yay",
    "hurray",
    "woohoo",
    "blessed",
    "secure",
    "reassured",
    "excited",
    "exciting",
    "pumped",
    "stoked",
    "hyped",
    "hype",
    "lit",
    "dope",
    "lol",
    "lmao",
    "lmfao",
    "rofl",
    "grinning",
    "wholesome",
    # Spanish
    "feliz",
    "felices",
    "felicidad",
    "alegre",
    "alegria",
    "alegría",
    "contento",
    "contenta",
    "tranquilo",
    "tranquila",
    "orgulloso",
    "orgullosa",
    "agradecido",
    "agradecida",
    "bendecido",
    "bendecida",
    "sonrisa",
    "sonreir",
    "sonreír",
    "sonriendo",
    "risa",
    "risas",
    "bendecidos",
    # Portuguese
    "felicidade",
    "contente",
    "tranquilo",
    "tranquila",
    "orgulhoso",
    "orgulhosa",
    "agradecido",
    "agradecida",
    "abençoado",
    "abençoada",
    "sorriso",
    "sorrir",
    "sorrindo",
    "risada",
    "risadas",
    "abençoados",
    "grato",
    "grata",
    # French
    "heureux",
    "heureuse",
    "bonheur",
    "joyeux",
    "joyeuse",
    "content",
    "contente",
    "sourire",
    "souriant",
    "souriante",
    "rire",
    "reconnaissant",
    "reconnaissante",
    "béni",
    "bénie",
    # Italian
    "felice",
    "felicità",
    "gioia",
    "gioioso",
    "gioiosa",
    "contento",
    "contenta",
    "sorriso",
    "sorridere",
    "soddisfatto",
    "soddisfatta",
    "grato",
    "grata",
    "benedetto",
    "benedetta",
    # German
    "glücklich",
    "glucklich",
    "freude",
    "froh",
    "zufrieden",
    "erleichtert",
    "stolz",
    "lächeln",
    "lacheln",
    "lachen",
    "dankbar",
    "gesegnet",
    # Dutch
    "blij",
    "gelukkig",
    "vreugde",
    "tevreden",
    "opluchting",
    "trots",
    "dankbaar",
    "gezegend",
    "lachen",
    "glimlach",
    # Polish
    "szczesliwy",
    "szczesliwa",
    "szczęśliwy",
    "szczęśliwa",
    "szczescie",
    "szczęście",
    "radosc",
    "radość",
    "zadowolony",
    "zadowolona",
    "usmiech",
    "uśmiech",
    "smiech",
    "śmiech",
    "wdzieczny",
    "wdzięczny",
    "wdzieczna",
    "wdzięczna",
    "blogoslawiony",
    "błogosławiony",
    "blogoslawiona",
    "błogosławiona",
}

# v6: regional joyful slang and colloquialisms
JOY.update(
    {
        # Latin American Spanish
        "chévere",
        "chevere",
        "bacán",
        "bacan",
        "chido",
        "padre",
        "genial",
        "copado",
        "rebueno",
        "rebien",
        # Brazilian Portuguese
        "legal",
        "massa",
        "maneiro",
        "top",
        "topzera",
        "daora",
        "da hora",
        "show",
        "showdebola",
        # European Portuguese
        "porreiro",
        "fixe",
        # French casual
        "cool",
        "tropbien",
        "tropbon",
        # Italian casual
        "fico",
        "fighissimo",
    }
)

SADNESS: Set[str] = {
    # English base
    "sad",
    "sadden",
    "saddened",
    "down",
    "blue",
    "depress",
    "depressed",
    "depressing",
    "cry",
    "cried",
    "crying",
    "tear",
    "tearful",
    "teary",
    "lonely",
    "alone",
    "miserable",
    "heartbroken",
    "broken",
    "sorrow",
    "grief",
    "grieving",
    "grieve",
    "grieved",
    "mourning",
    "bereaved",
    "remorse",
    "regret",
    "regretful",
    "sorry",
    "homesick",
    "melancholy",
    "gloomy",
    "hopeless",
    "helpless",
    "tired",
    "drained",
    "exhausted",
    "empty",
    "aching",
    "pain",
    "hurt",
    "hurtful",
    "painful",
    "forlorn",
    "downcast",
    "somber",
    "sombre",
    "ashamed",
    "shame",
    "loss",
    "losing",
    "miss",
    "missing",
    "overwhelmed",
    "burnout",
    "burnedout",
    "suffer",
    "suffering",
    "suffers",
    "hard",
    "harder",
    "hardest",
    "hardship",
    "struggle",
    "struggled",
    "struggling",
    "difficult",
    "difficulty",
    "disappointed",
    "disappointing",
    "rough",
    "tough",
    "draining",
    "discouraged",
    "numb",
    "meh",
    "idc",
    "couldcareless",
    "emptyinside",
    "overit",
    "sooverit",
    "sooverthis",
    # Spanish
    "triste",
    "tristeza",
    "solo",
    "sola",
    "soledad",
    "llorar",
    "llorando",
    "llanto",
    "deprimido",
    "deprimida",
    "depresion",
    "depresión",
    "culpa",
    "culpable",
    # Portuguese
    "sozinho",
    "sozinha",
    "triste",
    "tristeza",
    "solidão",
    "solidao",
    "chorar",
    "chorando",
    "deprimido",
    "deprimida",
    "depressao",
    "depressão",
    "culpado",
    "culpada",
    # French
    "triste",
    "tristesse",
    "seul",
    "seule",
    "solitude",
    "pleurer",
    "pleurant",
    "déprimé",
    "deprime",
    "déprimée",
    "deprimee",
    "dépression",
    "depression",
    "culpabilité",
    # Italian
    "triste",
    "tristezza",
    "solo",
    "sola",
    "solitudine",
    "piangere",
    "piangendo",
    "depresso",
    "depressa",
    "depressione",
    "colpa",
    # German
    "traurig",
    "traurigkeit",
    "einsam",
    "einsamkeit",
    "weinen",
    "weinend",
    "depressiv",
    "depression",
    "schuld",
    # Dutch
    "verdrietig",
    "verdriet",
    "eenzaam",
    "eenzaamheid",
    "huilen",
    "huilend",
    "depressief",
    "depressie",
    "schuld",
    # Polish
    "smutny",
    "smutna",
    "smutek",
    "samotny",
    "samotna",
    "samotnosc",
    "samotność",
    "placz",
    "płacz",
    "plakac",
    "płakać",
    "depresja",
    "wina",
}

ANGER: Set[str] = {
    # English base
    "angry",
    "anger",
    "mad",
    "furious",
    "livid",
    "rage",
    "raging",
    "irritated",
    "irritating",
    "annoyed",
    "annoying",
    "upset",
    "hate",
    "hated",
    "hates",
    "hating",
    "outraged",
    "resentful",
    "hostile",
    "fume",
    "fuming",
    "yell",
    "shout",
    "shouting",
    "scream",
    "screaming",
    "frustrated",
    "frustrating",
    "infuriating",
    "disrespect",
    "insult",
    "insulted",
    "offended",
    "betrayed",
    "backstabbed",
    "lied",
    "lying",
    "cheated",
    "deceived",
    "seethe",
    "seething",
    "boil",
    "boiling",
    "spite",
    "vengeful",
    "irate",
    "ticked",
    "tickedoff",
    "ragequit",
    "pissed",
    "pissedoff",
    "pissing",
    "pisses",
    "piss",
    "enraged",
    "fedup",
    "trash",
    "trashy",
    "stupid",
    "idiot",
    "jerk",
    "whatthehell",
    "ugh",
    "salty",
    "smh",
    "bs",
    "wtf",
    "triggered",
    # Spanish
    "enojado",
    "enojada",
    "enojo",
    "furioso",
    "furiosa",
    "rabia",
    "ira",
    "molesto",
    "molesta",
    "frustrado",
    "frustrada",
    "odio",
    # Portuguese
    "bravo",
    "brava",
    "raiva",
    "irritado",
    "irritada",
    "furioso",
    "furiosa",
    "ódio",
    "odio",
    "frustrado",
    "frustrada",
    # French
    "furieux",
    "furieuse",
    "colère",
    "colere",
    "faché",
    "fache",
    "fâché",
    "fâchée",
    "fachée",
    "énervé",
    "enervé",
    "enerve",
    "énervée",
    "enervee",
    # Italian
    "arrabbiato",
    "arrabbiata",
    "rabbia",
    "furioso",
    "furiosa",
    "odio",
    "infastidito",
    "infastidita",
    # German
    "wütend",
    "wutend",
    "zornig",
    "ärgerlich",
    "argerlich",
    "wut",
    "zorn",
    # Dutch
    "boos",
    "woedend",
    "kwaad",
    "woede",
    # Polish
    "zly",
    "zły",
    "zla",
    "zła",
    "gniew",
    "wściekły",
    "wsciekly",
    "wściekła",
    "wsciekla",
    "złość",
    "zlosc",
}

# v6: stronger anger slang, profanity and regional expressions
ANGER.update(
    {
        # English profanity / insults
        "fuck",
        "fucking",
        "fuckin",
        "fuckyou",
        "bitch",
        "bitches",
        "asshole",
        "bastard",
        "dumbass",
        "loser",
        "bullshit",
        "shit",
        "sucks",
        "suck",
        # Spanish anger slang
        "mierda",
        "cabron",
        "cabrón",
        "maldito",
        "maldita",
        "harto",
        "harta",
        "hartode",
        "hartade",
        "enfadado",
        "enfadada",
        # Portuguese anger slang (Brazil and Portugal)
        "merda",
        "droga",
        "porra",
        "raivoso",
        "raivosa",
        "chateado",
        "chateada",
        # French anger slang
        "merde",
        "putain",
        # Italian anger slang
        "incazzato",
        "incazzata",
        # German anger slang
        "scheisse",
        "scheiße",
        # Dutch anger slang
        "kut",
        "klote",
        # Polish anger slang
        "kurwa",
    }
)

FEAR: Set[str] = {
    # English base
    "scare",
    "scared",
    "afraid",
    "fear",
    "fearful",
    "terrified",
    "terrify",
    "terrifying",
    "anxious",
    "anxiety",
    "worry",
    "worried",
    "worrying",
    "panic",
    "panicked",
    "panicking",
    "nervous",
    "phobia",
    "frighten",
    "frightened",
    "tense",
    "uneasy",
    "alarmed",
    "concerned",
    "concern",
    "dread",
    "spook",
    "shaky",
    "shaking",
    "uncertain",
    "unsure",
    "doubt",
    "doubted",
    "doubting",
    "threat",
    "threatened",
    "unsafe",
    "unease",
    "apprehensive",
    "jitters",
    "restless",
    "paranoid",
    "stressed",
    "stress",
    "pressured",
    "pressure",
    "overwhelmed",
    "overwhelm",
    "deadline",
    "exam",
    "interview",
    "test",
    "difficult",
    "difficulty",
    "worrier",
    "spooked",
    "worriedsick",
    # Spanish
    "miedo",
    "temor",
    "asustado",
    "asustada",
    "preocupado",
    "preocupada",
    "ansioso",
    "ansiosa",
    "ansiedad",
    "nervioso",
    "nerviosa",
    # Portuguese
    "medo",
    "temor",
    "assustado",
    "assustada",
    "preocupado",
    "preocupada",
    "ansioso",
    "ansiosa",
    "ansiedade",
    "nervoso",
    "nervosa",
    # French
    "peur",
    "craintif",
    "craintive",
    "inquiet",
    "inquiète",
    "inquiette",
    "anxieux",
    "anxieuse",
    "anxiété",
    "anxiete",
    "nerveux",
    "nerveuse",
    # Italian
    "paura",
    "timore",
    "spaventato",
    "spaventata",
    "preoccupato",
    "preoccupata",
    "ansioso",
    "ansiosa",
    "ansia",
    "nervoso",
    "nervosa",
    # German
    "angst",
    "furcht",
    "fürchten",
    "furchten",
    "besorgt",
    "sorge",
    "nervös",
    "nervos",
    "ängstlich",
    "angstlich",
    # Dutch
    "bang",
    "angst",
    "bezorgd",
    "ongerust",
    "nerveus",
    # Polish
    "strach",
    "boje",
    "boję",
    "boisz",
    "przestraszony",
    "przestraszona",
    "zaniepokojony",
    "zaniepokojona",
    "napiety",
    "napięty",
    "nerwowy",
    "nerwowa",
}

DISGUST: Set[str] = {
    # English base
    "disgust",
    "disgusted",
    "disgusting",
    "gross",
    "nasty",
    "revolting",
    "repulsed",
    "repulsive",
    "sicken",
    "sickened",
    "sickening",
    "vile",
    "filthy",
    "dirty",
    "yuck",
    "ew",
    "eww",
    "creep",
    "creepy",
    "rotten",
    "stink",
    "stinks",
    "stinky",
    "abhorrent",
    "appalling",
    "offensive",
    "repugnant",
    "foul",
    "toxic",
    "contaminated",
    "putrid",
    "icky",
    "cringe",
    "cringy",
    "grossed",
    # Spanish
    "asco",
    "asqueroso",
    "asquerosa",
    "repugnante",
    "repulsivo",
    "repulsiva",
    "desagradable",
    # Portuguese
    "nojo",
    "nojento",
    "nojenta",
    "repugnante",
    "repulsivo",
    "repulsiva",
    "desagradavel",
    "desagradável",
    # French
    "dégoût",
    "degout",
    "dégoûtant",
    "degoutant",
    "dégoûtante",
    "degoutante",
    "répugnant",
    "repugnant",
    # Italian
    "disgusto",
    "disgustoso",
    "disgustosa",
    "ripugnante",
    "ripulsivo",
    "ripulsiva",
    "schifoso",
    "schifosa",
    # German
    "ekel",
    "ekelhaft",
    "widerlich",
    "abstoßend",
    "abstossend",
    # Dutch
    "walging",
    "walgelijk",
    "degoutant",
    "afschuwelijk",
    # Polish
    "wstręt",
    "wstret",
    "obrzydliwy",
    "obrzydliwa",
    "odpychający",
    "odpychajacy",
}

# v6: disgust slang that often overlaps with anger
DISGUST.update(
    {
        "shit",
        "mierda",
        "merda",
        "merde",
        "scheisse",
        "scheiße",
        "nojera",
    }
)

PASSION: Set[str] = {
    # English base
    "passion",
    "passionate",
    "desire",
    "desiring",
    "yearn",
    "yearning",
    "longing",
    "craving",
    "infatuated",
    "infatuation",
    "obsessed",
    "devoted",
    "devotion",
    "adore",
    "adoring",
    "adored",
    "cherish",
    "cherished",
    "romance",
    "romantic",
    "smitten",
    "inlove",
    "soulmate",
    "crush",
    "flushed",
    "butterflies",
    "attracted",
    "allured",
    "enamored",
    "enamoured",
    "fond",
    "fondness",
    "chemistry",
    "spark",
    "magnetic",
    "commit",
    "committed",
    "commitment",
    "marry",
    "marriage",
    "engage",
    "engaged",
    "proposal",
    "propose",
    "fiance",
    "fiancé",
    "fiancee",
    "fiancée",
    "wed",
    "wedding",
    "husband",
    "wife",
    "partner",
    "girlfriend",
    "boyfriend",
    "care",
    "cares",
    "caring",
    "beloved",
    "hot",
    "sexy",
    "handsome",
    "gorgeous",
    "pretty",
    "stunning",
    "attractive",
    "cute",
    "simp",
    "simping",
    # Spanish
    "apasionado",
    "apasionada",
    "deseo",
    "enamorado",
    "enamorada",
    "te amo",
    "te quiero",
    "amor",
    "cariño",
    # Portuguese
    "apaixonado",
    "apaixonada",
    "desejo",
    "apaixonar",
    "amado",
    "amada",
    "te amo",
    "te adoro",
    "amor",
    "carinho",
    # French
    "passionné",
    "passionnee",
    "amoureux",
    "amoureuse",
    "je t'aime",
    "mon amour",
    # Italian
    "passione",
    "appassionato",
    "appassionata",
    "innamorato",
    "innamorata",
    "ti amo",
    "amore",
    "amore mio",
    # German
    "leidenschaft",
    "leidenschaftlich",
    "verliebt",
    "ich liebe dich",
    "schatz",
    # Dutch
    "passie",
    "gepassioneerd",
    "verliefd",
    "ik hou van je",
    # Polish
    "pasja",
    "namiętny",
    "namietny",
    "namiętna",
    "namietna",
    "zakochany",
    "zakochana",
    "kocham cię",
    "kocham cie",
}

SURPRISE: Set[str] = {
    # English base
    "surprise",
    "surprised",
    "surprising",
    "astonish",
    "astonished",
    "astonishing",
    "amaze",
    "amazed",
    "amazing",
    "shocked",
    "shock",
    "unexpected",
    "unexpectedly",
    "sudden",
    "suddenly",
    "whoa",
    "woah",
    "wow",
    "omg",
    "wtf",
    "gasp",
    "unbelievable",
    "no",
    "noway",
    "holy",
    "plot",
    "twist",
    "didnt",
    "didn't",
    # Spanish
    "sorprendido",
    "sorprendida",
    "sorprendente",
    "increible",
    "increíble",
    # Portuguese
    "surpreso",
    "surpresa",
    "surpreendente",
    "inacreditavel",
    "inacreditável",
    # French
    "surpris",
    "surprise",
    "étonné",
    "etonne",
    "incroyable",
    # Italian
    "sorpreso",
    "sorpresa",
    "sorprendente",
    "incredibile",
    # German
    "überrascht",
    "uberrascht",
    "erstaunt",
    "unglaublich",
    # Dutch
    "verrast",
    "verrassing",
    "ongelofelijk",
    # Polish
    "zaskoczony",
    "zaskoczona",
    "niesamowite",
    "niewiarygodne",
}

# Strong intensity subsets (checked by prefix against stems)
JOY_STRONG = {
    "ecstatic",
    "euphoric",
    "overjoyed",
    "thrilled",
}
SADNESS_STRONG = {
    "heartbroken",
    "devastated",
    "grief",
    "mourning",
    "tristeza",
    "depresion",
    "depressao",
    "depression",
}
ANGER_STRONG = {
    "furious",
    "livid",
    "enraged",
    "seething",
    "rage",
    "rabia",
    "raiva",
}
FEAR_STRONG = {
    "terrified",
    "panic",
    "panicked",
    "miedo",
    "medo",
    "angst",
}
PASSION_STRONG = {
    "obsessed",
    "smitten",
    "madly",
    "apaixonado",
    "apasionado",
    "innamorato",
    "verliebt",
}
SURPRISE_STRONG = {
    "shocked",
    "wtf",
    "omg",
    "increible",
    "inacreditavel",
    "incroyable",
}

INTENT_COMMIT = {
    "want to marry",
    "want to propose",
    "plan to marry",
    "planning to marry",
    "intend to marry",
    "intend to propose",
    "i will marry",
    "i will propose",
    "ask her to marry",
    "ask him to marry",
    "ready to commit",
    "ready for marriage",
    "ready to settle",
    "settle down",
    "build a life",
    "start a family",
}
INTENT_DESIRE = {
    "i want",
    "i wanna",
    "i would love",
    "i like",
    "i love",
    "i adore",
    "i need",
    "cant wait",
    "can't wait",
    "dying to",
    "itching to",
    "i'm in love",
    "im in love",
    "i am in love",
    "in love with",
    "falling in love",
    "fell in love",
}
INTENT_REASSURE = {
    "it will be ok",
    "it will be okay",
    "we will be ok",
    "we will be okay",
    "everything will be fine",
    "i believe in us",
    "we will make it",
    "i trust you",
    "i trust god",
    "i trust that",
}
INTENT_DEESCALATE = {
    "let us calm down",
    "let's calm down",
    "take a breath",
    "breathe",
    "we can talk",
    "i am listening",
    "i'm listening",
    "i am here",
    "i'm here",
    "no need to fight",
    "let us not fight",
    "let's not fight",
}

PHRASES: List[Tuple[str, str, float]] = [
    # Joy and gratitude English
    ("over the moon", "joy", 1.8),
    ("on cloud nine", "joy", 1.6),
    ("could not be happier", "joy", 1.9),
    ("couldn't be happier", "joy", 1.9),
    ("walking on air", "joy", 1.6),
    ("choosing joy", "joy", 1.2),
    ("deciding to be grateful", "joy", 1.1),
    ("so proud of you", "joy", 1.4),
    ("so proud of myself", "joy", 1.4),
    ("feeling blessed", "joy", 1.6),
    ("feeling so blessed", "joy", 1.8),
    ("so grateful for you", "joy", 1.6),
    ("grateful for you", "joy", 1.5),
    ("so thankful for you", "joy", 1.6),
    # Joy Spanish Portuguese French etc
    ("muy feliz", "joy", 1.6),
    ("tan feliz", "joy", 1.5),
    ("me siento feliz", "joy", 1.7),
    ("estoy muy feliz", "joy", 1.8),
    ("sou muito feliz", "joy", 1.8),
    ("estou muito feliz", "joy", 1.8),
    ("me sinto feliz", "joy", 1.7),
    ("je suis très heureux", "joy", 1.8),
    ("je suis tres heureux", "joy", 1.8),
    ("je suis très heureuse", "joy", 1.8),
    ("je suis tres heureuse", "joy", 1.8),
    ("je suis tellement heureux", "joy", 1.9),
    ("je suis tellement heureuse", "joy", 1.9),
    ("sono così felice", "joy", 1.8),
    ("sono cosi felice", "joy", 1.8),
    ("ich bin so glücklich", "joy", 1.8),
    ("ik ben zo gelukkig", "joy", 1.8),
    # Sadness and grief English
    ("in tears", "sadness", 1.4),
    ("cry my eyes out", "sadness", 1.9),
    ("crying my eyes out", "sadness", 1.9),
    ("heart is broken", "sadness", 1.9),
    ("broke my heart", "sadness", 2.0),
    ("it broke my heart", "sadness", 2.0),
    ("i feel empty", "sadness", 1.6),
    ("despite the suffering", "sadness", 1.6),
    ("despite everything", "sadness", 1.0),
    ("in spite of the pain", "sadness", 1.6),
    ("rough day", "sadness", 1.8),
    ("tough day", "sadness", 1.7),
    ("hard day", "sadness", 1.6),
    ("burnt out", "sadness", 1.7),
    ("burned out", "sadness", 1.7),
    ("it is what it is", "sadness", 1.1),
    ("im so done", "sadness", 1.6),
    ("i am so done", "sadness", 1.6),
    ("so done with this", "sadness", 1.7),
    # Sadness multilingual
    ("muy triste", "sadness", 1.7),
    ("me siento triste", "sadness", 1.8),
    ("estoy muy triste", "sadness", 1.9),
    ("estou muito triste", "sadness", 1.9),
    ("me sinto triste", "sadness", 1.8),
    ("je suis très triste", "sadness", 1.9),
    ("je suis tres triste", "sadness", 1.9),
    ("sono così triste", "sadness", 1.9),
    ("ich bin so traurig", "sadness", 1.9),
    ("ik ben zo verdrietig", "sadness", 1.9),
    ("jest mi bardzo smutno", "sadness", 1.9),
    ("no puedo más", "sadness", 2.0),
    ("no puedo mas", "sadness", 2.0),
    ("não aguento mais", "sadness", 2.0),
    ("nao aguento mais", "sadness", 2.0),
    ("je n'en peux plus", "sadness", 2.0),
    ("je nen peux plus", "sadness", 2.0),
    ("non ce la faccio più", "sadness", 2.0),
    ("non ce la faccio piu", "sadness", 2.0),
    ("ich kann nicht mehr", "sadness", 2.0),
    ("nie dam rady", "sadness", 1.9),
    # Anger
    ("boiling with rage", "anger", 2.0),
    ("lost my temper", "anger", 1.7),
    ("at my wits end", "anger", 1.5),
    ("at my wit's end", "anger", 1.5),
    ("pisses me off", "anger", 2.3),
    ("pissed me off", "anger", 2.3),
    ("really pisses me off", "anger", 2.4),
    ("he pisses me off", "anger", 2.4),
    ("she pisses me off", "anger", 2.4),
    ("makes me so mad", "anger", 2.0),
    ("he drives me crazy", "anger", 1.9),
    ("she drives me crazy", "anger", 1.9),
    ("get on my nerves", "anger", 1.6),
    ("getting on my nerves", "anger", 1.6),
    ("im so mad", "anger", 1.9),
    ("i am so mad", "anger", 1.9),
    ("so done with you", "anger", 1.9),
    # Anger multilingual
    ("me pone furioso", "anger", 2.0),
    ("me pone furiosa", "anger", 2.0),
    ("me da mucha rabia", "anger", 2.1),
    ("isso me deixa com raiva", "anger", 2.1),
    ("je suis tellement en colère", "anger", 2.0),
    ("sono così arrabbiato", "anger", 2.0),
    ("sono cosi arrabbiato", "anger", 2.0),
    ("ich bin so wütend", "anger", 2.0),
    ("ik ben zo boos", "anger", 2.0),
    # Fear
    ("out of my mind with worry", "fear", 1.9),
    ("worried sick", "fear", 1.7),
    ("so worried about", "fear", 1.6),
    ("cant stop worrying", "fear", 1.7),
    ("can't stop worrying", "fear", 1.7),
    # Fear multilingual
    ("tengo mucho miedo", "fear", 1.9),
    ("tengo miedo", "fear", 1.7),
    ("tengo miedo de", "fear", 1.8),
    ("estoy muy preocupado", "fear", 1.7),
    ("estoy muy preocupada", "fear", 1.7),
    ("me preocupa", "fear", 1.5),
    ("estou muito preocupado", "fear", 1.7),
    ("estou muito preocupada", "fear", 1.7),
    ("tenho medo de", "fear", 1.8),
    ("isso me preocupa", "fear", 1.6),
    ("je suis très inquiet", "fear", 1.8),
    ("je suis tres inquiet", "fear", 1.8),
    ("je suis très inquiète", "fear", 1.8),
    ("je suis tres inquiete", "fear", 1.8),
    ("sono molto preoccupato", "fear", 1.8),
    ("ich habe solche angst", "fear", 1.9),
    ("ik ben zo bang", "fear", 1.8),
    ("bardzo się boję", "fear", 1.9),
    ("bardzo sie boje", "fear", 1.9),
    # Disgust
    ("sick to my stomach", "disgust", 1.7),
    ("gives me the creeps", "disgust", 1.7),
    ("creeps me out", "disgust", 1.7),
    ("offensive and repulsive", "disgust", 1.7),
    ("makes my skin crawl", "disgust", 1.7),
    # Disgust multilingual
    ("me da asco", "disgust", 1.9),
    ("que asco", "disgust", 1.9),
    ("que nojento", "disgust", 1.9),
    ("tenho nojo", "disgust", 1.9),
    ("ça me dégoûte", "disgust", 1.9),
    ("ca me degoute", "disgust", 1.9),
    ("che schifo", "disgust", 1.9),
    ("das ist ekelhaft", "disgust", 1.9),
    # Passion
    ("head over heels", "passion", 2.0),
    ("butterflies in my stomach", "passion", 1.6),
    ("madly in love", "passion", 2.0),
    ("in love", "passion", 2.2),
    ("i'm in love", "passion", 2.4),
    ("im in love", "passion", 2.4),
    ("i am in love", "passion", 2.4),
    ("in love with", "passion", 2.3),
    ("falling in love", "passion", 2.1),
    ("fell in love", "passion", 2.1),
    ("i want to marry", "passion", 2.0),
    ("i want to marry you", "passion", 2.2),
    ("i want to marry her", "passion", 2.2),
    ("i want to marry him", "passion", 2.2),
    ("i miss you so much", "passion", 2.0),
    ("i miss you", "passion", 1.4),
    # Passion multilingual
    ("estoy muy enamorado", "passion", 2.2),
    ("estoy muy enamorada", "passion", 2.2),
    ("estoy enamorado de ti", "passion", 2.4),
    ("estoy enamorada de ti", "passion", 2.4),
    ("te extraño tanto", "passion", 2.0),
    ("te extraño", "passion", 1.5),
    ("sou muito apaixonado", "passion", 2.2),
    ("sou muito apaixonada", "passion", 2.2),
    ("estou apaixonado por você", "passion", 2.4),
    ("estou apaixonada por você", "passion", 2.4),
    ("sinto sua falta", "passion", 1.7),
    ("je suis fou amoureux", "passion", 2.3),
    ("je suis folle amoureuse", "passion", 2.3),
    ("je t'aime tellement", "passion", 2.4),
    ("tu me manques tellement", "passion", 2.0),
    ("sono follemente innamorato", "passion", 2.3),
    ("sono follemente innamorata", "passion", 2.3),
    ("mi manchi tanto", "passion", 2.0),
    ("ich bin so verliebt", "passion", 2.3),
    ("du fehlst mir so", "passion", 2.0),
    ("ik ben zo verliefd", "passion", 2.3),
    ("ik mis je zo", "passion", 2.0),
    ("jestem w tobie zakochany", "passion", 2.3),
    ("jestem w tobie zakochana", "passion", 2.3),
    # Surprise and incredulity
    ("i could not believe", "surprise", 1.7),
    ("i can't believe", "surprise", 1.7),
    ("i cannot believe", "surprise", 1.7),
    ("could not believe", "surprise", 1.7),
    ("never thought this would happen", "surprise", 1.8),
    ("out of nowhere", "surprise", 1.7),
    ("came out of nowhere", "surprise", 1.7),
    # Surprise multilingual
    ("no lo puedo creer", "surprise", 1.9),
    ("no puedo creerlo", "surprise", 1.9),
    ("no me lo creo", "surprise", 1.9),
    ("não acredito", "surprise", 1.9),
    ("nao acredito", "surprise", 1.9),
    ("je n'arrive pas à y croire", "surprise", 1.9),
    ("je narrive pas a y croire", "surprise", 1.9),
    ("je ne peux pas y croire", "surprise", 1.9),
    ("non ci posso credere", "surprise", 1.9),
    ("ich kann es nicht glauben", "surprise", 1.9),
    ("ik kan het niet geloven", "surprise", 1.9),
    ("nie mogę w to uwierzyć", "surprise", 1.9),
    ("nie moge w to uwierzyc", "surprise", 1.9),
    # CJK joy
    ("很开心", "joy", 1.8),
    ("好开心", "joy", 1.8),
    ("很高兴", "joy", 1.8),
    ("好高兴", "joy", 1.8),
    ("好幸福", "joy", 1.9),
    ("楽しい", "joy", 1.7),
    ("嬉しい", "joy", 1.7),
    ("うれしい", "joy", 1.7),
    ("幸せ", "joy", 1.8),
    ("행복해", "joy", 1.8),
    ("행복하다", "joy", 1.8),
    ("기뻐", "joy", 1.7),
    # CJK sadness
    ("很难过", "sadness", 1.9),
    ("好难过", "sadness", 1.9),
    ("伤心", "sadness", 1.9),
    ("傷心", "sadness", 1.9),
    ("悲しい", "sadness", 1.9),
    ("かなしい", "sadness", 1.9),
    ("슬퍼", "sadness", 1.9),
    ("슬프다", "sadness", 1.9),
    # CJK anger
    ("生气", "anger", 2.0),
    ("生氣", "anger", 2.0),
    ("很生气", "anger", 2.1),
    ("好生气", "anger", 2.1),
    ("怒ってる", "anger", 2.1),
    ("怒っている", "anger", 2.1),
    ("화나", "anger", 2.1),
    ("화났다", "anger", 2.1),
    # CJK fear
    ("害怕", "fear", 1.9),
    ("很怕", "fear", 1.8),
    ("好怕", "fear", 1.8),
    ("怖い", "fear", 1.9),
    ("こわい", "fear", 1.9),
    ("무서워", "fear", 1.9),
    ("무섭다", "fear", 1.9),
    # CJK disgust
    ("恶心", "disgust", 1.9),
    ("噁心", "disgust", 1.9),
    ("好恶心", "disgust", 1.9),
    ("気持ち悪い", "disgust", 1.9),
    ("きもちわるい", "disgust", 1.9),
    ("징그러", "disgust", 1.9),
    ("징그럽다", "disgust", 1.9),
    # CJK passion
    ("爱你", "passion", 2.3),
    ("愛你", "passion", 2.3),
    ("我爱你", "passion", 2.4),
    ("我愛你", "passion", 2.4),
    ("喜欢你", "passion", 2.2),
    ("好きです", "passion", 2.3),
    ("大好き", "passion", 2.4),
    ("사랑해", "passion", 2.4),
    # CJK surprise
    ("天哪", "surprise", 1.7),
    ("竟然", "surprise", 1.7),
    ("居然", "surprise", 1.7),
    ("ありえない", "surprise", 1.8),
    ("あり得ない", "surprise", 1.8),
    ("헐", "surprise", 1.7),
    ("진짜요", "surprise", 1.7),
]

# v6: additional colloquial and dialect specific phrases
PHRASES.extend(
    [
        # English short negative life evaluations
        ("life's a bitch", "sadness", 2.1),
        ("lifes a bitch", "sadness", 2.1),
        ("life is a bitch", "sadness", 2.1),
        ("life sucks", "sadness", 2.0),
        ("my life sucks", "sadness", 2.1),
        ("fuck my life", "sadness", 2.1),
        ("fml", "sadness", 1.9),
        # English short insults and high anger
        ("fuck you", "anger", 2.4),
        ("go fuck yourself", "anger", 2.6),
        ("screw you", "anger", 2.1),
        ("you suck", "anger", 1.9),
        ("shut up", "anger", 1.6),
        # English casual positive slang
        ("im so hyped", "joy", 1.8),
        ("so hyped", "joy", 1.6),
        ("thats awesome", "joy", 1.4),
        ("thats fire", "joy", 1.4),
        ("thats lit", "joy", 1.5),
        # Latin American Spanish frustration and sadness
        ("estoy harto de", "anger", 2.0),
        ("estoy harta de", "anger", 2.0),
        ("ya basta", "anger", 2.0),
        ("mi vida es una mierda", "sadness", 2.2),
        ("mi vida es una porquería", "sadness", 2.2),
        ("mi vida es una porqueria", "sadness", 2.2),
        ("mi vida apesta", "sadness", 2.1),
        ("ando mal", "sadness", 1.7),
        ("ando muy mal", "sadness", 1.9),
        ("re mal", "sadness", 1.8),
        ("estoy hecho mierda", "sadness", 2.1),
        ("estoy hecha mierda", "sadness", 2.1),
        # Latin American Spanish joy slang
        ("esta re bien", "joy", 1.7),
        ("esta re bueno", "joy", 1.7),
        ("esta rebueno", "joy", 1.7),
        ("esta chido", "joy", 1.6),
        ("esta muy chido", "joy", 1.8),
        ("esta muy padre", "joy", 1.7),
        ("esta chevere", "joy", 1.7),
        ("está chévere", "joy", 1.7),
        # Brazilian Portuguese frustration and sadness
        ("tô de saco cheio", "anger", 2.1),
        ("to de saco cheio", "anger", 2.1),
        ("não aguento mais isso", "sadness", 2.2),
        ("nao aguento mais isso", "sadness", 2.2),
        ("minha vida é uma merda", "sadness", 2.3),
        ("minha vida e uma merda", "sadness", 2.3),
        ("tô mal", "sadness", 1.8),
        ("to mal", "sadness", 1.8),
        ("tô péssimo", "sadness", 1.9),
        ("tô pessimo", "sadness", 1.9),
        ("to pessimo", "sadness", 1.9),
        ("to péssimo", "sadness", 1.9),
        # Brazilian Portuguese joy slang
        ("tô de boa", "joy", 1.5),
        ("to de boa", "joy", 1.5),
        ("tá de boa", "joy", 1.5),
        ("ta de boa", "joy", 1.5),
        ("tá tudo certo", "joy", 1.4),
        ("ta tudo certo", "joy", 1.4),
        ("tá top", "joy", 1.6),
        ("ta top", "joy", 1.6),
        ("arrasou", "joy", 1.7),
        # European Portuguese frustration
        ("estou farto disto", "anger", 2.0),
        ("estou farta disto", "anger", 2.0),
        # French sadness and frustration
        ("ma vie est nulle", "sadness", 2.1),
        ("ma vie est de la merde", "sadness", 2.3),
        ("j'en ai marre", "anger", 1.9),
        ("jen ai marre", "anger", 1.9),
        # Italian sadness
        ("la mia vita fa schifo", "sadness", 2.3),
        # German sadness
        ("mein leben ist scheiße", "sadness", 2.3),
        ("mein leben ist scheisse", "sadness", 2.3),
    ]
)

# Mixed emotion patterns English, plus a couple of Romance examples
MIXED_PATTERNS: List[Tuple[str, Dict[str, float]]] = [
    ("excited and nervous", {"joy": 1.1, "fear": 1.1}),
    ("excited but nervous", {"joy": 1.1, "fear": 1.1}),
    ("scared but excited", {"fear": 1.0, "joy": 1.0}),
    ("nervous but excited", {"fear": 1.0, "joy": 1.0}),
    ("happy and scared", {"joy": 1.0, "fear": 1.1}),
    ("happy but scared", {"joy": 1.0, "fear": 1.1}),
    ("happy and anxious", {"joy": 0.9, "fear": 1.1}),
    ("happy but anxious", {"joy": 0.9, "fear": 1.1}),
    ("sad but grateful", {"sadness": 1.0, "joy": 0.9}),
    ("grateful but sad", {"sadness": 1.0, "joy": 0.9}),
    ("angry and hurt", {"anger": 1.0, "sadness": 1.1}),
    ("angry but hurt", {"anger": 1.0, "sadness": 1.1}),
    ("hurt and angry", {"anger": 1.0, "sadness": 1.1}),
    ("love you but", {"passion": 0.8, "sadness": 1.0}),
    ("i love you but", {"passion": 0.8, "sadness": 1.0}),
    ("worried but hopeful", {"fear": 0.9, "joy": 0.9}),
    ("afraid but hopeful", {"fear": 0.9, "joy": 0.9}),
    ("bitter sweet", {"joy": 0.9, "sadness": 0.9}),
    ("bittersweet", {"joy": 0.9, "sadness": 0.9}),
    # Romance language blends
    ("triste pero agradecido", {"sadness": 1.0, "joy": 0.9}),
    ("triste pero agradecida", {"sadness": 1.0, "joy": 0.9}),
    ("feliz pero nervioso", {"joy": 1.0, "fear": 1.0}),
    ("feliz pero nerviosa", {"joy": 1.0, "fear": 1.0}),
    ("feliz mas com medo", {"joy": 1.0, "fear": 1.0}),
    ("heureux mais inquiet", {"joy": 1.0, "fear": 1.0}),
    ("heureuse mais inquiète", {"joy": 1.0, "fear": 1.0}),
]

EMOJI = {
    "joy": {
        "😀",
        "😄",
        "😁",
        "😃",
        "😊",
        "☺️",
        "🙂",
        "🥳",
        "😌",
        "😅",
        ":)",
        ":-)",
        ":D",
        ":-D",
    },
    "sadness": {
        "😢",
        "😭",
        "☹️",
        "🙁",
        "😞",
        "😔",
        "🥹",
        ":(",
        ":-(",
        ":'(",
        "T_T",
    },
    "anger": {
        "😠",
        "😡",
        "😤",
        ">:(",
        "!!1",
        "😾",
    },
    "fear": {
        "😨",
        "😰",
        "😱",
        "😬",
        "🥺",
    },
    "disgust": {
        "🤢",
        "🤮",
    },
    "passion": {
        "😍",
        "😘",
        "🥰",
        "❤️",
        "💖",
        "💘",
        "💗",
        "💓",
        "💞",
        "💕",
        "💝",
        "<3",
    },
    "surprise": {
        "😲",
        "😳",
        "😮",
        "😯",
        "🤯",
        "😦",
        "😧",
        "😵",
    },
}

# Attraction oriented short phrases like "She is so hot"
ATTRACTION_SUBJECTS = {
    "she",
    "he",
    "they",
    "them",
    "her",
    "him",
    "girl",
    "girls",
    "guy",
    "guys",
    "woman",
    "women",
    "man",
    "men",
    "boy",
    "boys",
    "you",
    # Romantic pronouns multilingual
    "ella",
    "el",
    "él",
    "ele",
    "ela",
    "elle",
    "lui",
    "lei",
    "er",
    "sie",
    "hij",
    "zij",
    "ona",
    "on",
}

ATTRACTION_ADJECTIVES = {
    "hot",
    "sexy",
    "beautiful",
    "handsome",
    "pretty",
    "stunning",
    "attractive",
    "cute",
    "fine",
    # Spanish
    "guapo",
    "guapa",
    "hermoso",
    "hermosa",
    "lindo",
    "linda",
    "atractivo",
    "atractiva",
    # Portuguese
    "lindo",
    "linda",
    "gato",
    "gata",
    "bonito",
    "bonita",
    "atraente",
    # French
    "beau",
    "belle",
    "magnifique",
    # Italian
    "bello",
    "bella",
    "carino",
    "carina",
    # German
    "hübsch",
    "hubsch",
    "attraktiv",
    # Dutch
    "knap",
    "mooi",
    # Polish
    "przystojny",
    "ładna",
    "ladna",
}

CONFRONTATIONAL_QUESTION_PATTERNS = [
    "who do you think you are",
    "what is your problem",
    "what's your problem",
    "whats your problem",
    "what is wrong with you",
    "what's wrong with you",
    "whats wrong with you",
    "are you kidding me",
    "are you serious right now",
    "can you not",
    "why would you do that",
    "what were you thinking",
]

NEGATIONS: Set[str] = {
    # English
    "not",
    "no",
    "never",
    "hardly",
    "barely",
    "without",
    "lack",
    "lacking",
    "isnt",
    "isn't",
    "dont",
    "don't",
    "cant",
    "can't",
    "wont",
    "won't",
    "aint",
    "ain't",
    # Spanish
    "no",
    "nunca",
    "jamás",
    "jamas",
    # Portuguese
    "não",
    "nao",
    "nunca",
    "jamais",
    "nem",
    # French
    "ne",
    "pas",
    "jamais",
    "aucun",
    # Italian
    "non",
    "mai",
    # German
    "kein",
    "keine",
    "keinen",
    "keiner",
    "niemals",
    "nie",
    "nicht",
    # Dutch
    "geen",
    "niet",
    "nooit",
    # Polish
    "nie",
    "nigdy",
}

INTENSIFIERS: Set[str] = {
    # English
    "very",
    "really",
    "so",
    "extremely",
    "super",
    "incredibly",
    "totally",
    "absolutely",
    "quite",
    "truly",
    "deeply",
    "utterly",
    "highly",
    "too",
    "literally",
    "highkey",
    # Spanish
    "muy",
    "tan",
    "tanto",
    "bastante",
    "demasiado",
    # Portuguese
    "muito",
    "tão",
    "tao",
    "bastante",
    "demais",
    # French
    "très",
    "tres",
    "tellement",
    "vraiment",
    # Italian
    "molto",
    "tantissimo",
    "così",
    "cosi",
    # German
    "sehr",
    "wirklich",
    "total",
    "ziemlich",
    # Dutch
    "erg",
    "heel",
    "echt",
    "best",
    # Polish
    "bardzo",
    "strasznie",
}

DAMPENERS: Set[str] = {
    # English
    "slightly",
    "somewhat",
    "kinda",
    "kind",
    "sort",
    "sorta",
    "a",
    "bit",
    "little",
    "mildly",
    "barely",
    # Spanish
    "un",
    "poco",
    "algo",
    # Portuguese
    "um",
    "pouco",
    # French
    "un peu",
    "peu",
    # Italian
    "un po",
    "un po'",
    "poco",
    # German
    "ein bisschen",
    "bisschen",
    # Dutch
    "een beetje",
    "beetje",
    # Polish
    "troche",
    "trochę",
}

HEDGES: Set[str] = {
    # English
    "maybe",
    "perhaps",
    "possibly",
    "i guess",
    "i suppose",
    "i think",
    "sort of",
    "kind of",
    "kinda",
    "ish",
    "lowkey",
    # Spanish
    "quizás",
    "quizas",
    "tal vez",
    "talvez",
    "creo que",
    "supongo que",
    # Portuguese
    "talvez",
    "acho que",
    # French
    "peut-être",
    "peutetre",
    "je crois",
    "je pense",
    # Italian
    "forse",
    "credo che",
    # German
    "vielleicht",
    "ich glaube",
    # Dutch
    "misschien",
    "ik denk",
    # Polish
    "może",
    "moze",
    "chyba",
}

CONTRASTIVE: Set[str] = {
    # English
    "but",
    "however",
    "though",
    "although",
    "yet",
    "nevertheless",
    "nonetheless",
    "still",
    "even so",
    "despite",
    "even though",
    "whereas",
    "regardless",
    # Spanish
    "pero",
    "sin",
    "embargo",
    "aunque",
    # Portuguese
    "mas",
    "porém",
    "porem",
    "embora",
    # French
    "mais",
    "cependant",
    "pourtant",
    "toutefois",
    # Italian
    "ma",
    "però",
    "pero",
    "tuttavia",
    # German
    "aber",
    "doch",
    "jedoch",
    "trotzdem",
    # Dutch
    "maar",
    "echter",
    "toch",
    # Polish
    "ale",
    "jednak",
    "chociaż",
    "chociaz",
}

TEMPORAL_POS: Set[str] = {
    "now",
    "finally",
    "at",
    "last",
    # Spanish
    "ahora",
    "ya",
    "por",
    "fin",
    # Portuguese
    "agora",
    "finalmente",
    # French
    "maintenant",
    "enfin",
    # Italian
    "adesso",
    "ora",
    "finalmente",
    # German
    "jetzt",
    "endlich",
    # Dutch
    "nu",
    "eindelijk",
    # Polish
    "teraz",
    "wreszcie",
}

TEMPORAL_NEG: Set[str] = {
    "still",
    "yet",
    "anymore",
    "no",
    "longer",
    # Spanish
    "todavía",
    "todavia",
    "aún",
    "aun",
    # Portuguese
    "ainda",
    # French
    "encore",
    "toujours",
    # Italian
    "ancora",
    # German
    "noch",
    "immer",
    # Dutch
    "nog",
    "nog steeds",
    # Polish
    "ciągle",
    "ciagle",
}

STANCE_1P: Set[str] = {
    # English
    "i",
    "im",
    "i'm",
    "ive",
    "i've",
    "me",
    "my",
    "mine",
    "we",
    "our",
    "ours",
    # Spanish
    "yo",
    "me",
    "mi",
    "mio",
    "mía",
    "mia",
    "nosotros",
    "nosotras",
    "nuestro",
    "nuestra",
    # Portuguese
    "eu",
    "meu",
    "minha",
    "nós",
    "nos",
    "nosso",
    "nossa",
    # French
    "je",
    "moi",
    "mon",
    "ma",
    "nous",
    "notre",
    # Italian
    "io",
    "me",
    "mio",
    "mia",
    "noi",
    "nostro",
    "nostra",
    # German
    "ich",
    "mir",
    "mich",
    "mein",
    "wir",
    "uns",
    # Dutch
    "ik",
    "mij",
    "mijn",
    "wij",
    "ons",
    # Polish
    "ja",
    "mnie",
    "mi",
    "moja",
    "mój",
    "moj",
    "my",
}

NEGATED_PAIRS = {
    ("no", "joy"): ("joy", "sadness", 1.1),
    ("no", "hope"): ("joy", "sadness", 1.1),
    ("without", "hope"): ("joy", "sadness", 1.0),
    ("not", "happy"): ("joy", "sadness", 1.0),
    ("not", "angry"): ("anger", "fear", 0.8),
    ("no", "love"): ("passion", "sadness", 1.0),
    ("not", "inlove"): ("passion", "sadness", 1.0),
    ("not", "in"): ("passion", "sadness", 0.9),
}

# =============================================================================
# Tokenization helpers
# =============================================================================

# Unicode aware tokenization:
# - \w+ captures words in all scripts (Latin with accents, CJK, etc.)
# - [^\w\s] keeps punctuation and emojis as separate tokens.
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)

MISSPELLINGS = {
    "hapy": "happy",
    "happpy": "happy",
    "happ": "happy",
    "angy": "angry",
    "angree": "angry",
    "discusting": "disgusting",
    "discust": "disgust",
    "woried": "worried",
    "anxios": "anxious",
    "scarry": "scary",
    "lonley": "lonely",
    "miserible": "miserable",
    "wierd": "weird",
    "definately": "definitely",
    "releived": "relieved",
    "beleive": "believe",
    "cant": "can't",
    "wont": "won't",
    "im": "i'm",
}


def _build_approx_targets() -> Set[str]:
    base = set().union(JOY, SADNESS, ANGER, FEAR, DISGUST, PASSION, SURPRISE)
    expanded: Set[str] = set()
    for w in base:
        if not w:
            continue
        expanded.add(w)
        expanded.add(_strip_accents(w))
    return expanded


APPROX_TARGETS: Set[str] = _build_approx_targets()


def _normalize_elongation(text: str) -> str:
    return re.sub(r"([A-Za-z])\1{2,}", r"\1\1", text)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> List[str]:
    """
    Tokenize into unicode words and punctuation.
    Normalizes elongation like "soooo" -> "soo".
    """
    text = _normalize_elongation(text)
    text = _normalize_whitespace(text)
    # Collapse repeated boosters like "so so so" -> "so"
    text = re.sub(r"\b(so|very|really)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    return [t.lower() for t in TOKEN_RE.findall(text)]


def _stem(tok: str) -> str:
    if not tok.isalpha():
        return tok
    for suf in ("'s", "ing", "ed", "ly", "ness", "ful", "ment", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            return tok[: -len(suf)]
    return tok


def _window(tokens: List[str], i: int, size: int = 3) -> Iterable[str]:
    start = max(0, i - size)
    return tokens[start:i]


@lru_cache(maxsize=4096)
def _approx_correction(stem: str) -> str:
    """
    Approximate correction that is accent insensitive and typo aware.
    """
    raw = stem
    norm = _strip_accents(raw)
    if norm in MISSPELLINGS:
        return MISSPELLINGS[norm]
    if norm in APPROX_TARGETS:
        return norm
    matches = difflib.get_close_matches(norm, APPROX_TARGETS, n=1, cutoff=0.90)
    return matches[0] if matches else raw


def _meaningful_token_count(tokens: List[str]) -> int:
    return sum(1 for t in tokens if t.isalpha() and len(t) >= 3)


# =============================================================================
# Language guesser (used for both scoring and introspection)
# =============================================================================


def _guess_language(text: str) -> str:
    """
    Lightweight heuristic language guesser.
    Returns ISO like codes: en, es, pt, fr, it, de, nl, pl, zh, ja, ko.
    Defaults to en if uncertain.
    """
    t = text.lower()

    # CJK ranges first
    for ch in t:
        code = ord(ch)
        if 0x4E00 <= code <= 0x9FFF:
            return "zh"
        if 0x3040 <= code <= 0x30FF:
            return "ja"
        if 0xAC00 <= code <= 0xD7AF:
            return "ko"

    toks = _tokens(text)
    joined = " " + " ".join(toks) + " "

    scores: Dict[str, float] = {c: 0.0 for c in ("en", "es", "pt", "fr", "it", "de", "nl", "pl")}

    def bump(lang: str, w: float = 1.0) -> None:
        scores[lang] += w

    # Spanish
    for marker in (
        " el ",
        " la ",
        " que ",
        " de ",
        " y ",
        " pero ",
        " porque ",
        "estoy ",
        "estas ",
        "estás ",
        "gracias",
    ):
        if marker in joined:
            bump("es", 1.0)
    if any(ch in t for ch in "ñáéíóú"):
        bump("es", 0.6)

    # Portuguese
    for marker in (" não ", " nao ", " você", " voce", "tudo bem", "obrigado", "obrigada", "saudade"):
        if marker in joined:
            bump("pt", 1.0)
    if any(ch in t for ch in "ãõç"):
        bump("pt", 0.8)

    # French
    for marker in (" je ", " moi ", " ne ", " pas ", "vous ", "avec ", "pour ", "merci", "très ", "tres "):
        if marker in joined:
            bump("fr", 1.0)
    if any(ch in t for ch in "éèêàùçôî"):
        bump("fr", 0.6)

    # Italian
    for marker in (" ciao", " grazie", "non ", "perché", "perche", "sono ", "sei ", "allora"):
        if marker in joined:
            bump("it", 1.0)

    # German
    for marker in (" ich ", " nicht", " und ", "aber ", "dass ", "schön", "schon", "sehr "):
        if marker in joined:
            bump("de", 1.0)
    if "ß" in t:
        bump("de", 0.8)

    # Dutch
    for marker in (" ik ", " jij ", " je ", " niet", " maar ", " wij ", " we ", " heel ", " erg "):
        if marker in joined:
            bump("nl", 1.0)

    # Polish
    for marker in (" nie ", " jestem", " masz ", "dzień", "dzien", "proszę", "prosze", "dziękuję", "dziekuje"):
        if marker in joined:
            bump("pl", 1.0)
    if any(ch in t for ch in "ąćęłńóśżź"):
        bump("pl", 0.8)

    # If one language clearly dominates, return it
    best_lang = "en"
    best_score = 0.0
    for code, score in scores.items():
        if score > best_score:
            best_lang, best_score = code, score

    return best_lang if best_score >= 1.0 else "en"


# =============================================================================
# Sentence and clause splitting
# =============================================================================

_SENT_ENDERS = {".", "!", "?", "?!", "!?"}


def _split_sentences_from_tokens(
    tokens: List[str], max_sentences: int = 16
) -> List[List[str]]:
    """
    Split tokens into sentence like segments, capped to max_sentences,
    suitable for up to roughly 250 words.
    """
    if not tokens:
        return [[]]
    sents: List[List[str]] = []
    current: List[str] = []
    for t in tokens:
        current.append(t)
        if t in _SENT_ENDERS or (t == ";" and len(current) >= 6):
            sents.append(current)
            current = []
    if current:
        sents.append(current)
    if not sents:
        sents = [tokens[:]]

    if len(sents) <= max_sentences:
        return sents

    keep = sents[:max_sentences]
    overflow: List[str] = []
    for s in sents[max_sentences:]:
        overflow.extend(s)
    keep[-1].extend(overflow)
    return keep


def _split_clauses_in_sentence(sent_tokens: List[str]) -> List[List[str]]:
    if not sent_tokens:
        return [[]]
    clauses: List[List[str]] = []
    current: List[str] = []
    for t in sent_tokens:
        if t in CONTRASTIVE:
            if current:
                clauses.append(current)
            current = []
            continue
        if t in {",", ";", ":"} and len(current) >= 6:
            current.append(t)
            clauses.append(current)
            current = []
            continue
        current.append(t)
    if current:
        clauses.append(current)
    return clauses or [sent_tokens]


# =============================================================================
# Scoring utilities
# =============================================================================


def _blank_scores() -> Dict[str, float]:
    return {k: 0.0 for k in CORE_KEYS}


def _merge(acc: Dict[str, float], inc: Dict[str, float], scale: float = 1.0) -> None:
    for k in CORE_KEYS:
        acc[k] += inc.get(k, 0.0) * scale


def _emoji_boost(tok: str) -> Dict[str, float]:
    scores = _blank_scores()
    for emo, bag in EMOJI.items():
        if tok in bag:
            scores[emo] += 1.3
    return scores


def _punctuation_emphasis(ahead: str) -> float:
    bangs = ahead.count("!")
    if bangs >= 3:
        return 1.18
    if bangs == 2:
        return 1.10
    if bangs == 1:
        return 1.05
    return 1.0


def _surprise_punctuation_bonus(text: str) -> float:
    if re.search(r"(\?\!|\!\?)", text):
        return 0.15
    if re.search(r"[?!]{2,}", text):
        return 0.08
    return 0.0


def _in_lex(target: str, bag: Set[str]) -> bool:
    if target in bag:
        return True
    stripped = _strip_accents(target)
    if stripped in bag:
        return True
    if len(target) >= 4:
        for w in bag:
            if w.startswith(target) or _strip_accents(w).startswith(target):
                return True
    return False


def _is_strong(stem: str, bag: Set[str]) -> bool:
    if stem in bag:
        return True
    if len(stem) >= 4:
        return any(w.startswith(stem) for w in bag)
    return False


def _lex_hit(stem: str) -> Dict[str, float]:
    s = _blank_scores()

    if _in_lex(stem, JOY):
        base = 1.0
        if _is_strong(stem, JOY_STRONG):
            base = 1.6
        s["joy"] += base

    if _in_lex(stem, SADNESS):
        base = 1.0
        if _is_strong(stem, SADNESS_STRONG):
            base = 1.6
        s["sadness"] += base

    if _in_lex(stem, ANGER):
        base = 1.0
        if _is_strong(stem, ANGER_STRONG):
            base = 1.6
        s["anger"] += base

    if _in_lex(stem, FEAR):
        base = 1.0
        if _is_strong(stem, FEAR_STRONG):
            base = 1.6
        s["fear"] += base

    if _in_lex(stem, DISGUST):
        s["disgust"] += 1.0

    if _in_lex(stem, PASSION):
        base = 1.0
        if _is_strong(stem, PASSION_STRONG):
            base = 1.5
        s["passion"] += base

    if _in_lex(stem, SURPRISE):
        base = 1.0
        if _is_strong(stem, SURPRISE_STRONG):
            base = 1.4
        s["surprise"] += base

    return s


def _apply_phrases(text_lower: str) -> Dict[str, float]:
    out = _blank_scores()
    for phrase, emo, w in PHRASES:
        if phrase in text_lower:
            out[emo] += w
    return out


def _apply_mixed_patterns(text_lower: str, scores: Dict[str, float]) -> None:
    for pattern, delta in MIXED_PATTERNS:
        if pattern in text_lower:
            for k, v in delta.items():
                scores[k] += v


def _apply_negated_pairs(tokens: List[str], scores: Dict[str, float]) -> None:
    for i in range(len(tokens) - 1):
        bigram = (tokens[i], tokens[i + 1])
        if bigram in NEGATED_PAIRS:
            src, dst, mult = NEGATED_PAIRS[bigram]
            scores[dst] += 0.9 * mult
            scores[src] *= 0.6


def _rhetorical_question_boost(tokens: List[str]) -> float:
    text = " ".join(tokens)
    cues = [
        "what if",
        "what happens if",
        "am i going to",
        "are we going to",
        "is it going to",
        "how will i",
        "how can i",
        "why does this always",
    ]
    return 0.25 if any(c in text for c in cues) else 0.0


def _because_clause_dampener(tokens: List[str]) -> float:
    text = " ".join(tokens)
    if any(k in text for k in ("because", "since", "as ", "due to")):
        return 0.9
    return 1.0


def _harvest_meta_counts(tokens: List[str]) -> Dict[str, float]:
    joined = "".join(tokens)
    return {
        "_exclam_count": float(joined.count("!")),
        "_dots_count": float(joined.count("...")),
        "_heart_count": float(joined.count("❤️") + joined.count("<3")),
        "_laugh_count": float(joined.count("haha") + joined.count("lol")),
    }


def _arousal_valence_nudge(scores: Dict[str, float]) -> None:
    anger = scores.get("anger", 0.0)
    fear = scores.get("fear", 0.0)
    joy = scores.get("joy", 0.0)
    passion = scores.get("passion", 0.0)
    sadness = scores.get("sadness", 0.0)
    disgust = scores.get("disgust", 0.0)

    exclam = scores.pop("_exclam_count", 0.0)
    dots = scores.pop("_dots_count", 0.0)
    hearts = scores.pop("_heart_count", 0.0)
    laughs = scores.pop("_laugh_count", 0.0)

    high_arousal = min(exclam * 0.01, 0.05)
    low_arousal = min(dots * 0.01, 0.05)
    warm = min((hearts + laughs) * 0.01, 0.05)

    scores["anger"] = anger * (1.0 + high_arousal)
    scores["fear"] = fear * (1.0 + high_arousal)
    scores["joy"] = joy * (1.0 + warm)
    scores["passion"] = passion * (1.0 + warm)
    scores["sadness"] = sadness * (1.0 + low_arousal)
    scores["disgust"] = disgust * (1.0 + low_arousal)


def _apply_exclamation_emphasis(tokens: List[str], scores: Dict[str, float]) -> None:
    if "!" not in tokens:
        return

    bangs = tokens.count("!")
    factor = 1.0 + min(bangs * 0.03, 0.12)

    pos_mag = scores.get("joy", 0.0) + scores.get("passion", 0.0)
    neg_mag = (
        scores.get("anger", 0.0)
        + scores.get("fear", 0.0)
        + 0.5 * scores.get("disgust", 0.0)
    )

    if pos_mag >= neg_mag:
        for k in ("joy", "passion", "surprise"):
            scores[k] *= factor
    else:
        for k in ("anger", "fear", "surprise"):
            scores[k] *= factor


def _apply_feeling_focus(text_lower: str, scores: Dict[str, float]) -> None:
    cues_strong = (
        "i feel",
        "i'm feeling",
        "im feeling",
        "i really feel",
        "i truly feel",
        "i honestly feel",
        "makes me feel",
        "made me feel",
        "it makes me feel",
        "i feel so",
        "i feel really",
        # Spanish Portuguese French Italian
        "me siento",
        "me sinto",
        "me siento tan",
        "me sinto tão",
        "me sinto tao",
        "je me sens",
        "je me sens tellement",
        "mi sento",
        "mi sento così",
        "mi sento cosi",
        # German Dutch Polish
        "ich fühle mich",
        "ich fuhle mich",
        "ik voel me",
        "czuje sie",
        "czuję się",
    )
    if not any(c in text_lower for c in cues_strong):
        return

    factor = 1.08
    if any(
        x in text_lower
        for x in ("really", "so ", "very ", "muy ", "muito ", "très ", "tres ", "sehr ")
    ):
        factor = 1.12

    for k in CORE_KEYS:
        scores[k] *= factor


def _apply_short_text_rules(
    tokens: List[str],
    text_lower: str,
    scores: Dict[str, float],
    language: str,
) -> None:
    """
    Additional handling for ultra short inputs.

    This focuses on common ambiguous replies like "im fine", "ok",
    short insults like "fuck you", and compact crisis phrases
    in all supported languages.
    """
    total_tokens = len(tokens)
    alpha_tokens = sum(1 for t in tokens if t.isalpha())

    threshold = min(6, max(1, DEFAULT_CONFIG.short_text_token_threshold))
    if total_tokens > threshold and alpha_tokens > threshold:
        return

    simple = text_lower.strip()
    simple = re.sub(r"\s+", " ", simple)

    # If we have emoji heavy content, fall back on normal emoji logic
    if alpha_tokens == 0:
        return

    # High intensity short insults that usually express strong anger
    strong_anger_patterns = [
        # English
        "fuck you",
        "f you",
        "f u",
        "go fuck yourself",
        "screw you",
        "you suck",
        "shut up",
        "i hate you",
        "hate you",
        # Spanish
        "vete a la mierda",
        "andate a la mierda",
        "vete al carajo",
        # Portuguese
        "vai se foder",
        "vai se ferrar",
        "vai tomar no cu",
        "vai para o inferno",
        "vai pro inferno",
        # French
        "va te faire foutre",
        # Italian
        "vai a fanculo",
        # German
        "leck mich",
        # Dutch
        "rot op",
        # Polish
        "spierdalaj",
    ]
    if any(simple == p or simple.startswith(p + " ") for p in strong_anger_patterns):
        scores["anger"] += 2.2
        scores["disgust"] += 0.5
        scores["sadness"] += 0.3
        scores["joy"] *= 0.3

    # Short crisis statements where sadness and fear dominate
    crisis_patterns = [
        # English
        "i want to die",
        "i wanna die",
        "want to die",
        "want die",
        "wish i was dead",
        "wish i were dead",
        "kill myself",
        "end my life",
        # Spanish
        "quiero morir",
        "quisiera morir",
        "tengo ganas de morir",
        "matarme",
        # Portuguese
        "quero morrer",
        "queria morrer",
        "tenho vontade de morrer",
        "me matar",
        # French
        "je veux mourir",
        "j'en peux plus de vivre",
        # Italian
        "voglio morire",
        # German
        "ich will sterben",
        # Dutch
        "ik wil dood",
        # Polish
        "chcę umrzeć",
        "chce umrzeć",
        "chce umrzec",
    ]
    if any(simple.startswith(p) for p in crisis_patterns):
        scores["sadness"] += 2.5
        scores["fear"] += 1.3
        scores["anger"] += 0.4
        scores["joy"] *= 0.2

    # English style "im fine", "its fine", "ok then", etc
    base_fine_patterns = {
        "im fine",
        "i'm fine",
        "i am fine",
        "fine",
        "im ok",
        "i'm ok",
        "i am ok",
        "im okay",
        "i'm okay",
        "i am okay",
        "its fine",
        "it's fine",
        "that is fine",
    }
    if any(simple.startswith(p) for p in base_fine_patterns):
        exclam = "!" in simple
        neg_emoji = any(e in simple for e in ("😢", "😭", "🙁", "😞", "😔", "🥺"))
        if exclam and not neg_emoji:
            scores["joy"] += 0.8
        else:
            scores["sadness"] += 1.0
            scores["anger"] += 0.25
            scores["joy"] *= 0.6

    if any(
        kw in simple for kw in ("ok then", "fine then", "ok whatever", "ok, whatever")
    ):
        scores["sadness"] += 0.8
        scores["anger"] += 0.4
        scores["joy"] *= 0.4

    # Spanish and Portuguese "estoy bien", "estou bem", "tudo bem"
    if language in ("es", "pt"):
        if any(
            phrase in simple
            for phrase in (
                "estoy bien",
                "todo bien",
                "estoy re bien",
                "estou bem",
                "to bem",
                "tô bem",
                "tudo bem",
                "tá bem",
                "ta bem",
            )
        ):
            exclam = "!" in simple
            if exclam:
                scores["joy"] += 0.6
            else:
                scores["sadness"] += 0.4
                scores["joy"] += 0.2

    # French "ça va", "ca va"
    if language == "fr":
        if "ca va" in simple or "ça va" in simple:
            exclam = "!" in simple
            if exclam:
                scores["joy"] += 0.6
            else:
                scores["sadness"] += 0.35
                scores["joy"] += 0.2

    # Italian "sto bene"
    if language == "it" and "sto bene" in simple:
        exclam = "!" in simple
        if exclam:
            scores["joy"] += 0.6
        else:
            scores["sadness"] += 0.35
            scores["joy"] += 0.2

    # German "alles gut", "mir geht es gut"
    if language == "de":
        if "alles gut" in simple or "mir geht es gut" in simple:
            exclam = "!" in simple
            if exclam:
                scores["joy"] += 0.6
            else:
                scores["sadness"] += 0.3
                scores["joy"] += 0.25

    # Dutch "het gaat goed", "gaat goed"
    if language == "nl":
        if "het gaat goed" in simple or "gaat goed" in simple:
            exclam = "!" in simple
            if exclam:
                scores["joy"] += 0.6
            else:
                scores["sadness"] += 0.3
                scores["joy"] += 0.25

    # Polish "wszystko dobrze", "jest ok", "jest okej"
    if language == "pl":
        if (
            "wszystko dobrze" in simple
            or "jest ok" in simple
            or "jest okej" in simple
        ):
            exclam = "!" in simple
            if exclam:
                scores["joy"] += 0.6
            else:
                scores["sadness"] += 0.35
                scores["joy"] += 0.25


# =============================================================================
# Clause and sentence scorers
# =============================================================================


def _desire_commitment_bonus(text_lower: str) -> Dict[str, float]:
    out = _blank_scores()
    if any(p in text_lower for p in INTENT_COMMIT):
        out["passion"] += 2.3
        out["joy"] += 0.6
    if any(p in text_lower for p in INTENT_DESIRE):
        out["passion"] += 1.6
        out["joy"] += 0.4
    if " in love" in text_lower or text_lower.startswith("in love"):
        out["passion"] += 2.2
        out["joy"] += 0.4
    # Simple Romance language commitment signals
    if any(
        p in text_lower
        for p in (
            "quiero casarme",
            "quero me casar",
            "quero casar",
            "je veux t'épouser",
            "je veux tepouser",
            "voglio sposarti",
            "ich will dich heiraten",
            "ik wil met je trouwen",
            "chcę się z tobą ożenić",
            "chce sie z toba ozenic",
        )
    ):
        out["passion"] += 2.5
        out["joy"] += 0.7
    return out


def _apply_reassurance_and_deescalation(
    text_lower: str, scores: Dict[str, float]
) -> None:
    has_reassure = any(p in text_lower for p in INTENT_REASSURE)
    has_deesc = any(p in text_lower for p in INTENT_DEESCALATE)

    # Simple multilingual reassurance
    reassure_phrases = [
        "todo va a estar bien",
        "todo estará bien",
        "todo estara bien",
        "vai dar tudo certo",
        "tudo vai ficar bem",
        "tout ira bien",
        "andrà tutto bene",
        "andrà tutto a posto",
        "es wird alles gut",
        "alles wird gut",
        "alles komt goed",
        "wszystko będzie dobrze",
        "wszystko bedzie dobrze",
    ]
    if any(p in text_lower for p in reassure_phrases):
        has_reassure = True

    if not (has_reassure or has_deesc):
        return

    neg_keys = ("fear", "anger", "sadness")
    if has_reassure:
        for k in neg_keys:
            scores[k] *= 0.9
        scores["joy"] += 0.25
    if has_deesc:
        scores["anger"] *= 0.8
        scores["fear"] *= 0.92
        scores["joy"] += 0.15


def _scope_has_negation(win_before: Iterable[str]) -> bool:
    return any(wt in NEGATIONS or wt.endswith("n't") for wt in win_before)


def _contains_any(
    tokens: List[str], bag: Set[str], extra: Optional[Iterable[str]] = None
) -> bool:
    if extra:
        if any(x in " ".join(tokens) for x in extra):
            return True
    for raw in tokens:
        stem = _approx_correction(_stem(raw))
        if _in_lex(stem, bag):
            return True
    return False


def _is_positive_clause(tokens: List[str]) -> bool:
    return _contains_any(tokens, JOY, extra=("in love",)) or _contains_any(
        tokens, PASSION, extra=("in love",)
    )


def _is_negative_clause(tokens: List[str]) -> bool:
    return (
        _contains_any(tokens, FEAR)
        or _contains_any(tokens, SADNESS)
        or _contains_any(tokens, ANGER)
        or _contains_any(tokens, DISGUST)
    )


def _sarcasm_cue(tokens: List[str]) -> bool:
    text = " ".join(tokens)
    cues = [
        "yeah right",
        "as if",
        "sure buddy",
        "sure jan",
        "what a joy",
        "great job",
        "so fun",
        "how lovely",
        "what a delight",
        "yeah no",
        "yeah, no",
    ]
    if any(c in text for c in cues):
        return True

    # Deadpan positive adjective with period in a negative context
    if re.search(r"\b(great|amazing|wonderful|fantastic|perfect)\.\b", text):
        if _is_negative_clause(tokens):
            return True

    # Simple Romance language sarcasm markers
    if "si claro" in text or "sí claro" in text or "pois sim" in text:
        return True

    return False


def _apply_attraction_patterns(tokens: List[str], scores: Dict[str, float]) -> None:
    if not tokens:
        return

    stems = [_stem(t) for t in tokens]
    for i, st in enumerate(stems):
        if st not in ATTRACTION_SUBJECTS:
            continue

        window = stems[i + 1 : i + 5]
        if not window:
            continue

        for j, adj in enumerate(window):
            if adj in {"is", "s", "est", "é", "e"}:
                continue

            between = stems[i + 1 : i + 1 + j]
            if adj in ATTRACTION_ADJECTIVES:
                scope = stems[max(0, i - 3) : i + 1 + j]
                if any(w in NEGATIONS or w.endswith("n't") for w in scope):
                    continue

                weight = 2.2
                if any(w in INTENSIFIERS for w in between):
                    weight *= 1.25

                scores["passion"] += weight
                scores["joy"] += 0.4 * (weight / 2.2)
                return


def _apply_rhetorical_confrontation(
    text_lower: str, scores: Dict[str, float]
) -> None:
    if any(p in text_lower for p in CONFRONTATIONAL_QUESTION_PATTERNS):
        scores["anger"] += 1.2
        scores["disgust"] += 0.35
        scores["fear"] *= 0.7
        scores["surprise"] += 0.15


def _apply_colloquial_overrides(
    tokens: List[str], text_lower: str, scores: Dict[str, float]
) -> None:
    if not tokens:
        return

    has_negative_context = any(
        cue in text_lower
        for cue in (
            " but ",
            "but ",
            " no ",
            "doesnt",
            "doesn't",
            "didnt",
            "didn't",
            "pero ",
            " mas ",
            "mais ",
            "mais que",
        )
    )

    if "whatever" in text_lower:
        if has_negative_context:
            scores["sadness"] += 1.0
            scores["anger"] += 0.7
            scores["joy"] *= 0.35
        else:
            scores["sadness"] += 0.25
            scores["anger"] += 0.15
            scores["joy"] *= 0.8

    if any(
        phrase in text_lower
        for phrase in (
            "thats fine",
            "that's fine",
            "that is fine",
            "its fine",
            "it's fine",
            "fine whatever",
            "ok then",
            "okay then",
            "fine then",
            # Romance language equivalents
            "esta bien",
            "está bien",
            "esta tudo bem",
            "está tudo bem",
            "cest bon",
            "c'est bon",
            "va bene",
            "ist schon gut",
        )
    ):
        scores["sadness"] += 0.8
        scores["anger"] += 0.5
        scores["joy"] *= 0.45

    if "rough day" in text_lower or "tough day" in text_lower:
        scores["sadness"] += 0.9


def _apply_not_x_but_y(tokens: List[str], scores: Dict[str, float]) -> None:
    """
    Handle patterns like "I am not sad, I am angry"
    across supported languages, transferring weight
    from the first emotion to the second.
    """
    if len(tokens) < 4:
        return

    lex_by_emo: Dict[str, Set[str]] = {
        "joy": JOY,
        "sadness": SADNESS,
        "anger": ANGER,
        "fear": FEAR,
        "disgust": DISGUST,
        "passion": PASSION,
        "surprise": SURPRISE,
    }

    n = len(tokens)
    for i, tok in enumerate(tokens):
        if tok not in NEGATIONS and not tok.endswith("n't"):
            continue

        emo1: Optional[str] = None
        emo1_idx: Optional[int] = None
        for j in range(i + 1, min(n, i + 6)):
            raw = tokens[j]
            if not raw.isalpha():
                continue
            stem = _approx_correction(_stem(raw))
            for emo, bag in lex_by_emo.items():
                if _in_lex(stem, bag):
                    emo1 = emo
                    emo1_idx = j
                    break
            if emo1 is not None:
                break

        if emo1 is None or emo1_idx is None:
            continue

        emo2: Optional[str] = None
        emo2_idx: Optional[int] = None
        for j in range(emo1_idx + 1, min(n, emo1_idx + 10)):
            raw = tokens[j]
            if not raw.isalpha():
                continue
            stem = _approx_correction(_stem(raw))
            for emo, bag in lex_by_emo.items():
                if emo == emo1:
                    continue
                if _in_lex(stem, bag):
                    emo2 = emo
                    emo2_idx = j
                    break
            if emo2 is not None:
                break

        if emo2 is None or emo2_idx is None:
            continue

        between = tokens[emo1_idx + 1 : emo2_idx]
        between_joined = " ".join(between)
        bridge_bonus = 1.0
        if any(
            kw in between_joined
            for kw in (
                "just",
                "only",
                "simply",
                "solo",
                "solamente",
                "apenas",
                "só",
                "so ",
            )
        ):
            bridge_bonus = 1.15

        src_val = scores.get(emo1, 0.0)
        dst_val = scores.get(emo2, 0.0)
        if src_val <= 0 and dst_val <= 0:
            continue

        scores[emo1] = src_val * 0.35
        scores[emo2] = dst_val + src_val * 0.55 * bridge_bonus + 0.12 * bridge_bonus

        # Only apply once per clause to avoid over correction
        break


def _score_clause(tokens: List[str]) -> Dict[str, float]:
    scores = _blank_scores()
    n_alpha = 0

    text_lower = " ".join(tokens)

    _merge(scores, _apply_phrases(text_lower))
    _merge(scores, _desire_commitment_bonus(text_lower), 1.0)

    scores.update(_harvest_meta_counts(tokens))

    for i, raw in enumerate(tokens):
        stem = _stem(raw)
        if raw.isalpha():
            n_alpha += 1

        _merge(scores, _emoji_boost(raw))

        stem = _approx_correction(stem)
        base = _lex_hit(stem)
        if any(base.values()):
            weight = 1.0
            win = list(_window(tokens, i, size=3))

            if any(wt in INTENSIFIERS for wt in win):
                weight *= 1.25
            if any(wt in DAMPENERS for wt in win):
                weight *= 0.7
            if any(wt in HEDGES for wt in win):
                weight *= 0.9

            if _scope_has_negation(win):
                weight *= -0.9

            if any(wt in TEMPORAL_POS for wt in win):
                weight *= 1.05
            if any(wt in TEMPORAL_NEG for wt in win):
                weight *= 0.95
            if any(wt in STANCE_1P for wt in win):
                weight *= 1.05

            tail = "".join(tokens[i : i + 4])
            weight *= _punctuation_emphasis(tail)
            if raw.isalpha() and len(raw) >= 3 and raw.upper() == raw:
                weight *= 1.08

            for k, v in base.items():
                if v:
                    scores[k] += v * weight

    rq_boost = _rhetorical_question_boost(tokens)
    if rq_boost:
        scores["fear"] += rq_boost

    s_damp = _because_clause_dampener(tokens)
    scores["surprise"] *= s_damp

    _apply_exclamation_emphasis(tokens, scores)

    for emo, opp in [
        ("joy", "sadness"),
        ("fear", "anger"),
        ("anger", "fear"),
        ("disgust", "joy"),
        ("sadness", "joy"),
        ("passion", "sadness"),
        ("surprise", "fear"),
    ]:
        if scores[emo] < 0:
            scores[opp] += abs(scores[emo]) * 0.6
            scores[emo] = 0.0

    if "?" in tokens:
        scores["fear"] += 0.1
        scores["joy"] *= 0.985

    if any(t in STANCE_1P for t in tokens):
        for k in scores:
            scores[k] *= 1.03

    if _sarcasm_cue(tokens):
        scores["joy"] *= 0.6

    _apply_attraction_patterns(tokens, scores)
    _apply_rhetorical_confrontation(text_lower, scores)
    _apply_colloquial_overrides(tokens, text_lower, scores)
    _apply_mixed_patterns(text_lower, scores)
    _apply_not_x_but_y(tokens, scores)
    _apply_feeling_focus(text_lower, scores)

    text_seg = "".join(tokens)
    if re.search(r"\b[A-Z]{4,}\b", text_seg):
        scores["anger"] *= 1.05
        scores["joy"] *= 1.03

    # Normalize by alphabetic token count, but keep floor 1
    denom = max(n_alpha, 1)
    for k in CORE_KEYS:
        scores[k] = scores[k] / denom

    _apply_negated_pairs(tokens, scores)
    _apply_reassurance_and_deescalation(text_lower, scores)

    if _surprise_punctuation_bonus("".join(tokens)):
        scores["surprise"] += 0.05

    _arousal_valence_nudge(scores)

    return scores


def _sentence_emphasis_weight(
    tokens: List[str], idx: int, n_sent: int
) -> float:
    text = "".join(tokens)
    bangs = text.count("!")
    qmarks = text.count("?")
    caps_tokens = sum(
        1 for t in tokens if t.isalpha() and len(t) >= 3 and t.upper() == t
    )
    alpha_tokens = sum(1 for t in tokens if t.isalpha())
    caps_ratio = (caps_tokens / alpha_tokens) if alpha_tokens else 0.0

    punct_boost = 1.0 + min(bangs * 0.02 + qmarks * 0.008, 0.08)
    caps_boost = 1.0 + min(caps_ratio * 0.18, 0.08)
    pos_boost = 1.0 + min((idx / max(1, n_sent - 1)) * 0.10, 0.10)

    return punct_boost * caps_boost * pos_boost


# =============================================================================
# Aggregation and post processing
# =============================================================================


def _squash(x: float) -> float:
    if x <= 0.0:
        return 0.0
    return x / (1.0 + x)


def _clamp_scores(raw: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for k, v in raw.items():
        val = _squash(v)
        if val < 0.005:
            val = 0.0
        if val > 1.0:
            val = 1.0
        out[k] = val
    return out


def _normalize_for_mixture(scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, scores.get(k, 0.0)) for k in CORE_KEYS)
    if total <= 0.0:
        return {k: 0.0 for k in CORE_KEYS}
    return {k: max(0.0, scores.get(k, 0.0)) / total for k in CORE_KEYS}


def _apply_contrast_bias_if_any(
    sent_tokens: List[str],
    clauses: List[List[str]],
    per_clause_scores: List[Dict[str, float]],
    out: Dict[str, float],
) -> None:
    if not any(c in sent_tokens for c in CONTRASTIVE):
        return
    if len(clauses) < 2:
        return

    toks = sent_tokens
    try:
        first_contrast_idx = min(i for i, t in enumerate(toks) if t in CONTRASTIVE)
    except ValueError:
        return

    left_idx_last = 0
    running_len = 0
    for ci, cl in enumerate(clauses):
        running_len += len(cl)
        if running_len > first_contrast_idx:
            left_idx_last = max(0, ci - 1)
            break
    left_clauses = clauses[: left_idx_last + 1] or [clauses[0]]
    right_clauses = clauses[left_idx_last + 1 :] or [clauses[-1]]

    left_pos = any(_is_positive_clause(c) for c in left_clauses)
    left_neg = any(_is_negative_clause(c) for c in left_clauses)
    right_pos = any(_is_positive_clause(c) for c in right_clauses)
    right_neg = any(_is_negative_clause(c) for c in right_clauses)

    def mix_sum(cl_idxs, keys):
        s = 0.0
        for i in cl_idxs:
            sc = per_clause_scores[i]
            s += sum(sc.get(k, 0.0) for k in keys)
        return s

    left_ids = list(range(0, left_idx_last + 1))
    right_ids = list(range(left_idx_last + 1, len(clauses)))
    neg_keys = ("fear", "sadness", "anger", "disgust")
    pos_keys = ("joy", "passion")
    left_neg_num = mix_sum(left_ids, neg_keys)
    right_pos_num = mix_sum(right_ids, pos_keys)
    left_pos_num = mix_sum(left_ids, pos_keys)
    right_neg_num = mix_sum(right_ids, neg_keys)

    if (left_neg or left_neg_num > 0) and (right_pos or right_pos_num > 0):
        for k in ("fear", "sadness", "anger", "disgust"):
            out[k] *= 1.08
        for k in ("joy", "passion"):
            out[k] *= 0.985
        return

    if (left_pos or left_pos_num > 0) and (right_neg or right_neg_num > 0):
        for k in ("fear", "sadness", "anger", "disgust"):
            out[k] *= 1.12
        for k in ("joy", "passion"):
            out[k] *= 0.97
        return


def _aggregate_sentence(sent_tokens: List[str]) -> Dict[str, float]:
    clause_scores: List[Tuple[Dict[str, float], float]] = []
    numeric_by_clause: List[Dict[str, float]] = []
    clauses = _split_clauses_in_sentence(sent_tokens)
    for cl in clauses:
        sc = _score_clause(cl)
        tail = "".join(cl[-4:]) if cl else ""
        emph = _punctuation_emphasis(tail)
        alpha_len = sum(1 for t in cl if t.isalpha())
        len_boost = 0.9 if alpha_len <= 3 else 1.0
        clause_scores.append((sc, emph * len_boost))
        numeric_by_clause.append(sc)

    if not clause_scores:
        return _blank_scores()

    out = _blank_scores()
    total_w = sum(w for _, w in clause_scores) or 1.0
    for sc, w in clause_scores:
        for k in CORE_KEYS:
            out[k] += sc[k] * (w / total_w)

    _apply_contrast_bias_if_any(sent_tokens, clauses, numeric_by_clause, out)
    return out


def _aggregate_sentences(sentences: List[List[str]]) -> Dict[str, float]:
    if not sentences:
        return _blank_scores()

    n = len(sentences)
    per_sent: List[Tuple[Dict[str, float], float]] = []
    for idx, s in enumerate(sentences):
        sc = _aggregate_sentence(s)
        w = _sentence_emphasis_weight(s, idx, n)
        per_sent.append((sc, w))

    weights = [w for _, w in per_sent]
    sum_w = sum(weights) or 1.0
    weights = [w / sum_w for w in weights]

    if n >= 5:
        uni = 1.0 / n
        weights = [0.6 * w + 0.4 * uni for w in weights]

    sum_w = sum(weights) or 1.0
    weights = [w / sum_w for w in weights]

    raw = _blank_scores()
    for (sc, _), w in zip(per_sent, weights):
        for k in CORE_KEYS:
            raw[k] += sc[k] * w
    return raw


def _score_windows(tokens: List[str]) -> List[Dict[str, Any]]:
    """
    Sliding window scoring over longer texts to capture emotional turns.
    Returns a list of window descriptors with raw scores.
    """
    n = len(tokens)
    config = DEFAULT_CONFIG
    min_tokens = max(20, config.window_min_tokens)
    if n < min_tokens:
        return []

    size = max(24, min(config.window_size_tokens, n))
    step = max(8, min(config.window_step_tokens, size // 2))

    windows: List[Dict[str, Any]] = []
    start = 0
    while start < n:
        end = min(n, start + size)
        seg = tokens[start:end]
        if _meaningful_token_count(seg) == 0:
            if end == n:
                break
            start += step
            continue

        sc = _aggregate_sentence(seg)
        norm = _normalize_for_mixture(sc)
        dominant = _choose_dominant(norm, low_signal=False)
        windows.append(
            {
                "start_index": start,
                "end_index": end,
                "token_count": len(seg),
                "tokens": seg,
                "scores": sc,
                "dominant": dominant,
            }
        )

        if end == n:
            break
        start += step

    return windows


def _apply_window_level_adjustment(
    tokens: List[str], base_scores: Dict[str, float]
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """
    For longer texts, blend sentence level aggregate with
    sliding window aggregate to better respect emotional turns.
    """
    windows = _score_windows(tokens)
    if not windows:
        return base_scores, []

    win_agg = _blank_scores()
    total_len = 0.0
    for w in windows:
        sc = w.get("scores", {})
        ln = float(w.get("token_count", len(w.get("tokens", []))))
        if ln <= 0:
            continue
        total_len += ln
        for k in CORE_KEYS:
            win_agg[k] += sc.get(k, 0.0) * ln

    if total_len <= 0.0:
        return base_scores, windows

    for k in CORE_KEYS:
        win_agg[k] /= total_len

    blended = _blank_scores()
    doc_w = 0.6
    win_w = 0.4
    for k in CORE_KEYS:
        blended[k] = base_scores.get(k, 0.0) * doc_w + win_agg.get(k, 0.0) * win_w

    return blended, windows


def _is_low_signal(tokens: List[str], raw_scores: Dict[str, float]) -> bool:
    """
    Decide whether the signal is too weak to trust.

    For v6 this considers phrase-only CJK text, emoji only, and short texts.
    """
    meaningful = _meaningful_token_count(tokens)
    peak = max((v for v in raw_scores.values()), default=0.0)
    total = sum(max(v, 0.0) for v in raw_scores.values())
    distinct = sum(1 for v in raw_scores.values() if v > 0.06)

    # If purely phrase or emoji based but still strong, do not mark low signal.
    if meaningful == 0:
        return peak < 0.05

    if peak >= 0.05:
        return False

    if meaningful == 1 and total < 0.04 and distinct <= 1:
        return True

    if meaningful <= 3 and total < 0.025 and distinct <= 1:
        return True

    return False


def _choose_dominant(scores: Dict[str, float], low_signal: bool = False) -> str:
    if low_signal:
        return "N/A"

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_key, top_val = ordered[0]
    second_key, second_val = ordered[1]

    if top_val < 0.05:
        return "N/A"

    neg_keys = {"fear", "sadness", "anger", "disgust"}
    pos_keys = {"joy", "passion"}

    pos_peak = max(scores[k] for k in pos_keys)
    neg_peak = max(scores[k] for k in neg_keys)
    pos_total = sum(scores[k] for k in pos_keys)
    neg_total = sum(scores[k] for k in neg_keys)

    if (
        pos_peak >= 0.30
        and neg_peak >= 0.20
        and pos_total >= 0.35
        and neg_total >= 0.25
        and neg_peak >= pos_peak * 0.5
    ):
        dominant_neg = max(neg_keys, key=lambda k: scores[k])
        return dominant_neg

    gap = top_val - second_val
    if gap < 0.06:
        negative = neg_keys
        appetitive = pos_keys
        inter_neg = negative & {top_key, second_key}
        inter_pos = appetitive & {top_key, second_key}
        if inter_neg and inter_pos:
            return next(iter(inter_neg))

    return top_key


def _dominance_profile(
    scores: Dict[str, float], low_signal: bool = False
) -> Tuple[str, str, bool]:
    if low_signal:
        return "N/A", "N/A", False

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if not ordered:
        return "N/A", "N/A", False

    top_key, top_val = ordered[0]
    second_key, second_val = ordered[1] if len(ordered) > 1 else ("N/A", 0.0)

    if top_val < 0.05:
        return "N/A", "N/A", False

    numeric_top_key = top_key
    numeric_second_key = second_key

    dominant = _choose_dominant(scores, low_signal=False)

    if dominant != numeric_top_key:
        candidate_key = numeric_top_key
        candidate_val = scores.get(numeric_top_key, top_val)
    else:
        candidate_key = numeric_second_key
        candidate_val = scores.get(numeric_second_key, second_val)

    if candidate_val < 0.04:
        return dominant, "N/A", False

    pos = {"joy", "passion"}
    neg = {"sadness", "fear", "anger", "disgust"}

    mixed = (
        (dominant in pos and candidate_key in neg)
        or (dominant in neg and candidate_key in pos)
    )

    pair = {dominant, candidate_key}
    min_pair_val = min(scores.get(dominant, 0.0), scores.get(candidate_key, 0.0))

    if not mixed:
        if pair == {"joy", "sadness"} and min_pair_val >= 0.15:
            mixed = True
        elif pair == {"joy", "fear"} and min_pair_val >= 0.15:
            mixed = True
        elif "passion" in pair and "sadness" in pair and min_pair_val >= 0.15:
            mixed = True
        elif pair == {"fear", "sadness"} and min_pair_val >= 0.16:
            mixed = True
        elif pair == {"anger", "disgust"} and min_pair_val >= 0.16:
            mixed = True

    if (
        not mixed
        and top_val >= 0.18
        and second_val >= 0.15
        and abs(top_val - second_val) <= 0.08
    ):
        mixed = True

    return dominant, candidate_key, mixed


def _compute_meta_metrics(
    final_scores: Dict[str, float],
    low_signal: bool,
    tokens: List[str],
) -> Dict[str, float]:
    """
    Compute document level valence, arousal and confidence
    from final scores and token features.
    """
    pos = final_scores.get("joy", 0.0) + final_scores.get("passion", 0.0)
    neg = (
        final_scores.get("sadness", 0.0)
        + final_scores.get("fear", 0.0)
        + final_scores.get("anger", 0.0)
        + final_scores.get("disgust", 0.0)
    )
    denom = pos + neg
    if denom > 0:
        valence = (pos - neg) / denom
    else:
        valence = 0.0

    exclam = tokens.count("!")
    qmarks = tokens.count("?")
    caps_tokens = sum(
        1 for t in tokens if t.isalpha() and len(t) >= 3 and t.upper() == t
    )
    alpha_tokens = sum(1 for t in tokens if t.isalpha())
    caps_ratio = (caps_tokens / alpha_tokens) if alpha_tokens else 0.0

    base_energy = (
        final_scores.get("anger", 0.0)
        + final_scores.get("fear", 0.0)
        + final_scores.get("passion", 0.0)
        + final_scores.get("surprise", 0.0)
    )
    punct_boost = min(exclam * 0.05 + qmarks * 0.03, 0.4)
    caps_boost = min(caps_ratio * 0.4, 0.4)
    arousal = base_energy * 0.75 + punct_boost + caps_boost
    if arousal > 1.0:
        arousal = 1.0

    ordered_vals = sorted(final_scores.values(), reverse=True)
    peak = ordered_vals[0] if ordered_vals else 0.0
    second = ordered_vals[1] if len(ordered_vals) > 1 else 0.0
    spread = max(0.0, peak - second)
    non_trivial = sum(1 for v in final_scores.values() if v >= 0.08)

    if low_signal or peak < 0.05:
        confidence = 0.15
    else:
        confidence = (
            0.45 * peak
            + 0.35 * spread
            + 0.2 * (non_trivial / float(len(CORE_KEYS)))
        )
        if confidence > 1.0:
            confidence = 1.0
        if confidence < 0.0:
            confidence = 0.0

    return {
        "valence": float(valence),
        "arousal": float(arousal),
        "confidence": float(confidence),
    }


def _extract_reasons(
    text: str,
    tokens: List[str],
    final_scores: Dict[str, float],
) -> Dict[str, List[str]]:
    """
    Heuristic explanation of which words or phrases contributed
    to each emotion score.
    """
    reasons: Dict[str, List[str]] = {k: [] for k in CORE_KEYS}
    if not text or not tokens:
        return reasons

    text_lower = text.lower()

    # Phrase based reasons
    for phrase, emo, _ in PHRASES:
        if final_scores.get(emo, 0.0) < 0.08:
            continue
        if phrase in text_lower and phrase not in reasons[emo]:
            reasons[emo].append(phrase)
            if len(reasons[emo]) >= 4:
                continue

    # Lexical reasons
    lex_map = {
        "joy": JOY,
        "sadness": SADNESS,
        "anger": ANGER,
        "fear": FEAR,
        "disgust": DISGUST,
        "passion": PASSION,
        "surprise": SURPRISE,
    }
    for raw in tokens:
        if not raw:
            continue
        if not raw.isalpha() and raw not in {"<3", "❤️"}:
            continue
        stem = _approx_correction(_stem(raw))
        for emo, bag in lex_map.items():
            if final_scores.get(emo, 0.0) < 0.08:
                continue
            if _in_lex(stem, bag) and raw not in reasons[emo]:
                reasons[emo].append(raw)
                if len(reasons[emo]) >= 5:
                    break

    # Emoji reasons
    for emo, emoji_set in EMOJI.items():
        if final_scores.get(emo, 0.0) < 0.08:
            continue
        if any(e in tokens for e in emoji_set):
            if "emoji" not in reasons[emo]:
                reasons[emo].append("emoji")

    return reasons


def _collect_patterns_fired(text_lower: str) -> List[str]:
    patterns: List[str] = []

    for pattern, _ in MIXED_PATTERNS:
        if pattern in text_lower:
            patterns.append(f"mixed:{pattern}")

    if any(p in text_lower for p in INTENT_COMMIT):
        patterns.append("commitment_intent")

    if any(p in text_lower for p in INTENT_DESIRE):
        patterns.append("desire_intent")

    if any(p in text_lower for p in INTENT_REASSURE):
        patterns.append("reassurance")
    if any(p in text_lower for p in INTENT_DEESCALATE):
        patterns.append("deescalation")

    if any(p in text_lower for p in CONFRONTATIONAL_QUESTION_PATTERNS):
        patterns.append("confrontational_question")

    return patterns


def _score_document(
    tokens: List[str],
    text_str: str,
) -> Tuple[Dict[str, float], List[Dict[str, Any]], bool, str]:
    """
    Core document level scoring before clamping and dominance.

    Returns:
        raw_scores, windows, low_signal, language
    """
    if not tokens:
        return _blank_scores(), [], True, "en"

    sentences = _split_sentences_from_tokens(tokens, max_sentences=16)
    raw = _aggregate_sentences(sentences)
    raw, windows = _apply_window_level_adjustment(tokens, raw)
    raw["surprise"] += _surprise_punctuation_bonus("".join(tokens)) * 0.2

    language = _guess_language(text_str)
    text_lower = text_str.lower()

    _apply_short_text_rules(tokens, text_lower, raw, language)

    alpha_tokens = sum(1 for t in tokens if t.isalpha())
    total_tokens = len(tokens)
    threshold = min(6, max(1, DEFAULT_CONFIG.short_text_token_threshold))
    if total_tokens <= threshold or alpha_tokens <= 2:
        max_raw = max(raw.values()) if raw else 0.0
        if max_raw > 0.0:
            for k in CORE_KEYS:
                raw[k] *= 1.2

    low_signal = _is_low_signal(tokens, raw)
    return raw, windows, low_signal, language


# =============================================================================
# Public API
# =============================================================================


def detect_emotions(text: str, use_watson_if_available: bool = False) -> EmotionResult:
    """
    Main multilingual detector entry point.

    Purely local scoring with a true zero baseline that supports:
    English, Spanish, Portuguese, French, Italian, German, Dutch, Polish
    and phrase based cues for Chinese, Japanese and Korean.

    Calibrated for 1 to about 250 words.
    """
    if text is None:
        raise InvalidTextError("Input text is required")

    text_str = str(text)
    if not text_str.strip():
        raise InvalidTextError("Input text is required")

    low_signal = False
    scores: Dict[str, float]
    tokens: List[str] = []

    try:
        tokens = _tokens(text_str)
        if not tokens:
            scores = _blank_scores()
            low_signal = True
        else:
            raw, _windows, low_signal, _lang = _score_document(tokens, text_str)
            scores = _clamp_scores(raw)
    except Exception:
        low_signal = True
        scores = _blank_scores()
        tokens = []

    mix_for_dominance = _normalize_for_mixture(scores)
    dominant, secondary, mixed = _dominance_profile(
        mix_for_dominance, low_signal=low_signal
    )

    meta = _compute_meta_metrics(scores, low_signal, tokens)

    result = EmotionResult(
        anger=float(scores.get("anger", 0.0)),
        disgust=float(scores.get("disgust", 0.0)),
        fear=float(scores.get("fear", 0.0)),
        joy=float(scores.get("joy", 0.0)),
        sadness=float(scores.get("sadness", 0.0)),
        passion=float(scores.get("passion", 0.0)),
        surprise=float(scores.get("surprise", 0.0)),
        dominant_emotion=dominant,
        low_signal=low_signal,
        secondary_emotion=secondary,
        mixed_state=mixed,
        valence=meta["valence"],
        arousal=meta["arousal"],
        confidence=meta["confidence"],
    )
    return result


def explain_emotions(text: str, use_watson_if_available: bool = False) -> Dict[str, Any]:
    """
    Developer facing introspection helper.

    Returns tokens, per sentence breakdown, raw aggregate scores and the
    final clamped scores, together with the dominant and secondary
    emotions, mixed state flag, guessed language, window level view,
    meta metrics and a simple reasons list per emotion.
    """
    if text is None or not str(text).strip():
        raise InvalidTextError("Input text is required")

    text_str = str(text)
    tokens = _tokens(text_str)
    sentences = _split_sentences_from_tokens(tokens, max_sentences=16)

    # Per sentence breakdown for debugging
    per_sentence = []
    per_sentence_weights = []
    for idx, s in enumerate(sentences):
        sc_sentence = _aggregate_sentence(s)
        per_sentence.append(
            {
                "sentence_tokens": s,
                "sentence_scores": sc_sentence,
                "clauses": _split_clauses_in_sentence(s),
            }
        )
        per_sentence_weights.append(_sentence_emphasis_weight(s, idx, len(sentences)))

    sw = per_sentence_weights[:]
    total = sum(sw) or 1.0
    sw = [w / total for w in sw]
    if len(sw) >= 5:
        uni = 1.0 / len(sw)
        sw = [0.6 * w + 0.4 * uni for w in sw]
    total = sum(sw) or 1.0
    sw = [w / total for w in sw]

    agg, windows, low_signal, language = _score_document(tokens, text_str)
    final = _clamp_scores(agg)

    mix_for_dominance = _normalize_for_mixture(final)
    dominant, secondary, mixed = _dominance_profile(
        mix_for_dominance, low_signal=low_signal
    )

    meta = _compute_meta_metrics(final, low_signal, tokens)
    reasons = _extract_reasons(text_str, tokens, final)
    patterns_fired = _collect_patterns_fired(text_str.lower())

    return {
        "text": text,
        "language": language,
        "tokens": tokens,
        "sentences": sentences,
        "per_sentence": per_sentence,
        "sentence_weights": sw,
        "aggregate_scores": agg,
        "final_scores": final,
        "dominant": dominant,
        "secondary": secondary,
        "mixed_state": mixed,
        "low_signal": low_signal,
        "windows": windows,
        "meta": meta,
        "reasons": reasons,
        "patterns_fired": patterns_fired,
    }


emotion_detector = detect_emotions
