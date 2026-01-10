# detector/external_lexicon.py
# External lexicon fetcher for expanding emotion detection vocabulary
# Integrates with Urban Dictionary (slang), Free Dictionary API (English),
# and equivalent sources for Spanish and Portuguese.
#
# This module provides asynchronous/batch fetching of word definitions
# from external APIs and extracts emotion weights based on definition
# content analysis.

from __future__ import annotations

import json
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from functools import lru_cache

# ---------------------------------------------------------------------------
# Emotion keywords for definition analysis
# These keywords in definitions suggest emotional associations
# ---------------------------------------------------------------------------

EMOTION_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "en": {
        "anger": [
            "angry", "mad", "furious", "rage", "hostile", "irritated", "annoyed",
            "resentful", "bitter", "hatred", "hate", "frustrated", "infuriated",
            "outraged", "enraged", "irate", "wrathful", "provoked", "aggravated",
            "indignant", "livid", "fuming", "seething", "antagonistic", "violent"
        ],
        "disgust": [
            "disgusting", "gross", "nasty", "revolting", "repulsive", "sickening",
            "vile", "foul", "loathsome", "offensive", "repugnant", "abhorrent",
            "distasteful", "nauseating", "unpleasant", "horrible", "awful",
            "repellent", "objectionable", "obnoxious", "detestable", "yucky"
        ],
        "fear": [
            "afraid", "scared", "terrified", "frightened", "anxious", "worried",
            "nervous", "panic", "dread", "horror", "alarmed", "apprehensive",
            "uneasy", "fearful", "trembling", "petrified", "spooked", "timid",
            "cowardly", "paranoid", "phobic", "terrifying", "scary", "creepy"
        ],
        "joy": [
            "happy", "joyful", "glad", "pleased", "delighted", "cheerful",
            "content", "satisfied", "blissful", "elated", "ecstatic", "jubilant",
            "merry", "overjoyed", "thrilled", "euphoric", "positive", "good",
            "wonderful", "excellent", "great", "amazing", "fantastic", "awesome",
            "fun", "funny", "hilarious", "amusing", "entertaining", "laugh",
            "celebrate", "enjoyable", "pleasant", "nice", "lovely", "beautiful"
        ],
        "sadness": [
            "sad", "unhappy", "depressed", "miserable", "sorrowful", "melancholy",
            "gloomy", "mournful", "grief", "heartbroken", "dejected", "despondent",
            "hopeless", "dismal", "tragic", "painful", "suffering", "anguish",
            "despair", "lonely", "forlorn", "blue", "down", "upset", "crying",
            "tears", "weeping", "loss", "death", "dying", "mourn", "bereaved"
        ],
        "passion": [
            "love", "loving", "passionate", "desire", "romantic", "intimate",
            "affection", "attraction", "devoted", "adore", "cherish", "longing",
            "yearning", "infatuation", "obsession", "lust", "sensual", "erotic",
            "sexual", "hot", "sexy", "attractive", "beautiful", "gorgeous",
            "crush", "sweetheart", "beloved", "darling", "dear", "caring"
        ],
        "surprise": [
            "surprised", "shocked", "amazed", "astonished", "astounded",
            "unexpected", "sudden", "startled", "stunned", "bewildered",
            "dumbfounded", "flabbergasted", "speechless", "incredible",
            "unbelievable", "remarkable", "extraordinary", "unusual", "strange",
            "weird", "odd", "peculiar", "wonder", "awe", "marvel"
        ]
    },
    "es": {
        "anger": [
            "enojado", "enfadado", "furioso", "rabia", "ira", "hostil", "irritado",
            "resentido", "amargado", "odio", "frustrado", "indignado", "molesto",
            "agresivo", "violento", "colérico", "airado", "encolerizado", "rabioso"
        ],
        "disgust": [
            "asqueroso", "repugnante", "desagradable", "repulsivo", "nauseabundo",
            "horrible", "asqueado", "ofensivo", "detestable", "odioso", "vil",
            "inmundo", "sucio", "feo", "grotesco", "abominable", "asco"
        ],
        "fear": [
            "miedo", "asustado", "aterrorizado", "temeroso", "ansioso", "preocupado",
            "nervioso", "pánico", "horror", "alarmado", "aprensivo", "aterrado",
            "espantado", "cobarde", "paranoico", "fóbico", "terrorífico", "escalofriante"
        ],
        "joy": [
            "feliz", "alegre", "contento", "satisfecho", "encantado", "dichoso",
            "gozoso", "jubiloso", "eufórico", "positivo", "bueno", "maravilloso",
            "excelente", "genial", "increíble", "fantástico", "divertido", "gracioso",
            "chistoso", "entretenido", "agradable", "bonito", "hermoso", "lindo"
        ],
        "sadness": [
            "triste", "infeliz", "deprimido", "miserable", "melancólico", "afligido",
            "luto", "desolado", "desesperado", "doloroso", "sufrimiento", "angustia",
            "pena", "solitario", "llorando", "lágrimas", "pérdida", "muerte", "morir"
        ],
        "passion": [
            "amor", "amoroso", "apasionado", "deseo", "romántico", "íntimo",
            "afecto", "atracción", "devoto", "adorar", "anhelo", "enamorado",
            "obsesión", "sensual", "erótico", "sexual", "atractivo", "hermoso",
            "querido", "cariño", "cariñoso", "amado", "amante"
        ],
        "surprise": [
            "sorprendido", "impactado", "asombrado", "inesperado", "repentino",
            "atónito", "estupefacto", "boquiabierto", "increíble", "extraordinario",
            "raro", "extraño", "peculiar", "maravilla", "asombroso"
        ]
    },
    "pt": {
        "anger": [
            "raiva", "zangado", "furioso", "irritado", "bravo", "enfurecido",
            "hostil", "resentido", "amargurado", "ódio", "frustrado", "indignado",
            "chateado", "agressivo", "violento", "colérico", "irado", "nervoso"
        ],
        "disgust": [
            "nojento", "repugnante", "desagradável", "repulsivo", "nauseante",
            "horrível", "ofensivo", "detestável", "odioso", "vil", "imundo",
            "sujo", "feio", "grotesco", "abominável", "nojo", "asco"
        ],
        "fear": [
            "medo", "assustado", "aterrorizado", "temeroso", "ansioso", "preocupado",
            "nervoso", "pânico", "horror", "alarmado", "apreensivo", "apavorado",
            "medroso", "covarde", "paranoico", "fóbico", "aterrorizante", "arrepiante"
        ],
        "joy": [
            "feliz", "alegre", "contente", "satisfeito", "encantado", "ditoso",
            "jubiloso", "eufórico", "positivo", "bom", "maravilhoso", "excelente",
            "genial", "incrível", "fantástico", "divertido", "engraçado", "hilário",
            "agradável", "bonito", "lindo", "belo", "legal", "maneiro"
        ],
        "sadness": [
            "triste", "infeliz", "deprimido", "miserável", "melancólico", "aflito",
            "luto", "desolado", "desesperado", "doloroso", "sofrimento", "angústia",
            "pena", "solitário", "chorando", "lágrimas", "perda", "morte", "morrer"
        ],
        "passion": [
            "amor", "amoroso", "apaixonado", "desejo", "romântico", "íntimo",
            "afeto", "atração", "devoto", "adorar", "anseio", "apaixonado",
            "obsessão", "sensual", "erótico", "sexual", "atraente", "lindo",
            "querido", "carinho", "carinhoso", "amado", "amante"
        ],
        "surprise": [
            "surpreso", "chocado", "espantado", "inesperado", "repentino",
            "atônito", "estupefato", "boquiaberto", "incrível", "extraordinário",
            "estranho", "esquisito", "peculiar", "maravilha", "surpreendente"
        ]
    }
}

# Slang emotion indicators (for Urban Dictionary processing)
SLANG_EMOTION_INDICATORS: Dict[str, List[str]] = {
    "anger": [
        "pissed", "salty", "triggered", "pressed", "heated", "tilted", "mad",
        "tight", "beefing", "throwing hands", "catch these hands", "toxic"
    ],
    "disgust": [
        "cringe", "ick", "gross", "sus", "sketchy", "janky", "crusty", "musty",
        "basic", "trash", "garbage", "mid", "L", "ratio"
    ],
    "fear": [
        "lowkey scared", "freaked", "spooked", "shook", "paranoid", "sus",
        "sketched out", "creeped out", "big yikes", "concerning"
    ],
    "joy": [
        "lit", "fire", "dope", "sick", "based", "goated", "W", "bussin",
        "slaps", "hits different", "vibing", "living", "blessed", "ate",
        "slay", "iconic", "king", "queen", "gas", "heat", "valid", "real"
    ],
    "sadness": [
        "down bad", "hurting", "broken", "lost", "empty", "numb", "dead inside",
        "crying", "sobbing", "depressed", "done", "over it", "gutted", "rip"
    ],
    "passion": [
        "simp", "simping", "stan", "stanning", "ship", "shipping", "thirsty",
        "down bad", "caught feelings", "crushing", "lowkey obsessed", "wifey",
        "hubby", "bae", "zaddy", "snack", "meal", "fine", "baddie"
    ],
    "surprise": [
        "shook", "shooketh", "mindblown", "wild", "insane", "crazy", "bruh",
        "no cap", "fr fr", "deadass", "lowkey", "highkey", "ong", "on god"
    ]
}

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------

# Urban Dictionary unofficial API
URBAN_DICTIONARY_API = "https://api.urbandictionary.com/v0/define"

# Free Dictionary API (English)
FREE_DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries"

# Spanish dictionary APIs
# Using Libre Translate's dictionary or fallback sources
SPANISH_DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/es"

# Portuguese dictionary API
PORTUGUESE_DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/pt-BR"

# WordsAPI (requires API key, optional)
WORDS_API_BASE = "https://wordsapicom.p.rapidapi.com/words"

# Rate limiting configuration
RATE_LIMIT_DELAY = 0.5  # seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries

# SSL context for HTTPS requests
SSL_CONTEXT = ssl.create_default_context()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class WordDefinition:
    """Represents a word and its definition(s) from an external source."""
    word: str
    language: str
    source: str
    definitions: List[str]
    examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    part_of_speech: Optional[str] = None
    thumbs_up: int = 0  # For Urban Dictionary popularity


@dataclass
class EmotionWeight:
    """Extracted emotion weights for a word."""
    word: str
    language: str
    emotions: Dict[str, float]
    confidence: float
    source: str


# ---------------------------------------------------------------------------
# API Fetchers
# ---------------------------------------------------------------------------

def _make_request(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Make an HTTP GET request and return JSON response."""
    try:
        req = urllib.request.Request(url)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        req.add_header("User-Agent", "In-Tuned-Emotion-Detector/1.0")

        with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # Word not found
        print(f"HTTP Error {e.code} for {url}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error for {url}: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {url}: {e}")
        return None
    except Exception as e:
        print(f"Request error for {url}: {e}")
        return None


def fetch_urban_dictionary(word: str) -> List[WordDefinition]:
    """
    Fetch slang definitions from Urban Dictionary.
    Returns multiple definitions sorted by popularity.
    """
    encoded_word = urllib.parse.quote(word)
    url = f"{URBAN_DICTIONARY_API}?term={encoded_word}"

    data = _make_request(url)
    if not data or "list" not in data:
        return []

    results = []
    for entry in data["list"][:5]:  # Top 5 definitions
        definition = WordDefinition(
            word=word,
            language="en",
            source="urban_dictionary",
            definitions=[entry.get("definition", "")],
            examples=[entry.get("example", "")] if entry.get("example") else [],
            thumbs_up=entry.get("thumbs_up", 0)
        )
        results.append(definition)

    return results


def fetch_free_dictionary_en(word: str) -> List[WordDefinition]:
    """
    Fetch English definitions from Free Dictionary API.
    """
    encoded_word = urllib.parse.quote(word)
    url = f"{FREE_DICTIONARY_API}/en/{encoded_word}"

    data = _make_request(url)
    if not data or not isinstance(data, list):
        return []

    results = []
    for entry in data:
        word_text = entry.get("word", word)
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            definitions = []
            examples = []
            synonyms = []

            for defn in meaning.get("definitions", []):
                if defn.get("definition"):
                    definitions.append(defn["definition"])
                if defn.get("example"):
                    examples.append(defn["example"])
                synonyms.extend(defn.get("synonyms", []))

            synonyms.extend(meaning.get("synonyms", []))

            if definitions:
                wd = WordDefinition(
                    word=word_text,
                    language="en",
                    source="free_dictionary",
                    definitions=definitions,
                    examples=examples,
                    synonyms=list(set(synonyms)),
                    part_of_speech=pos
                )
                results.append(wd)

    return results


def fetch_free_dictionary_es(word: str) -> List[WordDefinition]:
    """
    Fetch Spanish definitions from Free Dictionary API.
    """
    encoded_word = urllib.parse.quote(word)
    url = f"{SPANISH_DICTIONARY_API}/{encoded_word}"

    data = _make_request(url)
    if not data or not isinstance(data, list):
        return []

    results = []
    for entry in data:
        word_text = entry.get("word", word)
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            definitions = []
            examples = []
            synonyms = []

            for defn in meaning.get("definitions", []):
                if defn.get("definition"):
                    definitions.append(defn["definition"])
                if defn.get("example"):
                    examples.append(defn["example"])
                synonyms.extend(defn.get("synonyms", []))

            if definitions:
                wd = WordDefinition(
                    word=word_text,
                    language="es",
                    source="free_dictionary",
                    definitions=definitions,
                    examples=examples,
                    synonyms=list(set(synonyms)),
                    part_of_speech=pos
                )
                results.append(wd)

    return results


def fetch_free_dictionary_pt(word: str) -> List[WordDefinition]:
    """
    Fetch Portuguese definitions from Free Dictionary API.
    """
    encoded_word = urllib.parse.quote(word)
    url = f"{PORTUGUESE_DICTIONARY_API}/{encoded_word}"

    data = _make_request(url)
    if not data or not isinstance(data, list):
        return []

    results = []
    for entry in data:
        word_text = entry.get("word", word)
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            definitions = []
            examples = []
            synonyms = []

            for defn in meaning.get("definitions", []):
                if defn.get("definition"):
                    definitions.append(defn["definition"])
                if defn.get("example"):
                    examples.append(defn["example"])
                synonyms.extend(defn.get("synonyms", []))

            if definitions:
                wd = WordDefinition(
                    word=word_text,
                    language="pt",
                    source="free_dictionary",
                    definitions=definitions,
                    examples=examples,
                    synonyms=list(set(synonyms)),
                    part_of_speech=pos
                )
                results.append(wd)

    return results


# ---------------------------------------------------------------------------
# Emotion Weight Extraction
# ---------------------------------------------------------------------------

def _normalize_text_for_matching(text: str) -> str:
    """Normalize text for keyword matching."""
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def extract_emotion_weights(
    definition: WordDefinition,
    min_confidence: float = 0.3
) -> Optional[EmotionWeight]:
    """
    Analyze a word definition to extract emotion weights.

    Uses keyword matching in definitions, examples, and synonyms
    to determine emotional associations.
    """
    lang = definition.language
    if lang not in EMOTION_KEYWORDS:
        lang = "en"  # Fallback to English keywords

    keywords = EMOTION_KEYWORDS[lang]

    # Combine all text for analysis
    all_text = " ".join(definition.definitions)
    all_text += " " + " ".join(definition.examples)
    all_text += " " + " ".join(definition.synonyms)
    all_text = _normalize_text_for_matching(all_text)

    # Count keyword hits per emotion
    emotion_scores: Dict[str, float] = {
        "anger": 0.0,
        "disgust": 0.0,
        "fear": 0.0,
        "joy": 0.0,
        "sadness": 0.0,
        "passion": 0.0,
        "surprise": 0.0
    }

    total_hits = 0

    for emotion, words in keywords.items():
        for kw in words:
            kw_norm = _normalize_text_for_matching(kw)
            if kw_norm in all_text:
                emotion_scores[emotion] += 1.0
                total_hits += 1
            # Partial match for compound keywords
            elif len(kw_norm) > 4:
                pattern = re.compile(r'\b' + re.escape(kw_norm[:4]) + r'\w*\b')
                if pattern.search(all_text):
                    emotion_scores[emotion] += 0.5
                    total_hits += 0.5

    # Check for slang indicators (especially for Urban Dictionary)
    if definition.source == "urban_dictionary":
        for emotion, indicators in SLANG_EMOTION_INDICATORS.items():
            for ind in indicators:
                ind_norm = _normalize_text_for_matching(ind)
                if ind_norm in all_text:
                    emotion_scores[emotion] += 1.5  # Higher weight for slang
                    total_hits += 1.5

    if total_hits == 0:
        return None

    # Normalize and scale scores
    max_score = max(emotion_scores.values())
    if max_score > 0:
        for emotion in emotion_scores:
            # Scale to 0-2.5 range (matching existing lexicon weights)
            emotion_scores[emotion] = (emotion_scores[emotion] / max_score) * 2.5

    # Calculate confidence based on hit density and popularity
    confidence = min(1.0, total_hits / 5.0)

    # Boost confidence for popular Urban Dictionary entries
    if definition.source == "urban_dictionary" and definition.thumbs_up > 1000:
        confidence = min(1.0, confidence * 1.2)

    if confidence < min_confidence:
        return None

    # Filter out very weak emotion associations
    filtered_emotions = {
        e: v for e, v in emotion_scores.items() if v >= 0.5
    }

    if not filtered_emotions:
        return None

    return EmotionWeight(
        word=definition.word,
        language=definition.language,
        emotions=filtered_emotions,
        confidence=confidence,
        source=definition.source
    )


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def fetch_and_extract_word(
    word: str,
    language: str = "en",
    include_slang: bool = True
) -> List[EmotionWeight]:
    """
    Fetch definitions for a word and extract emotion weights.

    Args:
        word: The word to look up
        language: Language code (en, es, pt)
        include_slang: Whether to include Urban Dictionary (English only)

    Returns:
        List of EmotionWeight objects
    """
    results = []
    definitions = []

    # Fetch from appropriate sources based on language
    if language == "en":
        definitions.extend(fetch_free_dictionary_en(word))
        if include_slang:
            time.sleep(RATE_LIMIT_DELAY)
            definitions.extend(fetch_urban_dictionary(word))
    elif language == "es":
        definitions.extend(fetch_free_dictionary_es(word))
    elif language == "pt":
        definitions.extend(fetch_free_dictionary_pt(word))

    # Extract emotion weights from definitions
    for defn in definitions:
        weight = extract_emotion_weights(defn)
        if weight:
            results.append(weight)

    return results


def batch_fetch_words(
    words: List[str],
    language: str = "en",
    include_slang: bool = True,
    progress_callback: Optional[callable] = None
) -> Dict[str, Dict[str, float]]:
    """
    Fetch and process multiple words, returning lexicon-compatible format.

    Args:
        words: List of words to look up
        language: Language code
        include_slang: Include Urban Dictionary for English
        progress_callback: Optional callback(word, index, total) for progress

    Returns:
        Dict in format {word: {emotion: weight}}
    """
    lexicon_entries: Dict[str, Dict[str, float]] = {}

    for idx, word in enumerate(words):
        if progress_callback:
            progress_callback(word, idx, len(words))

        try:
            weights = fetch_and_extract_word(word, language, include_slang)

            if weights:
                # Merge multiple definitions into single entry
                merged_emotions: Dict[str, float] = {}
                total_confidence = 0.0

                for w in weights:
                    for emotion, score in w.emotions.items():
                        if emotion not in merged_emotions:
                            merged_emotions[emotion] = 0.0
                        merged_emotions[emotion] += score * w.confidence
                    total_confidence += w.confidence

                # Average by confidence
                if total_confidence > 0:
                    for emotion in merged_emotions:
                        merged_emotions[emotion] /= total_confidence

                    lexicon_entries[word.lower()] = merged_emotions

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            print(f"Error processing word '{word}': {e}")
            continue

    return lexicon_entries


# ---------------------------------------------------------------------------
# Curated Word Lists for Expansion
# ---------------------------------------------------------------------------

# Common emotion-related slang terms to fetch from Urban Dictionary
SLANG_WORDS_TO_FETCH: List[str] = [
    # Joy/positive slang - Gen Z and Millennial
    "lit", "bussin", "fire", "dope", "goated", "based", "valid", "slaps",
    "hits different", "no cap", "finna", "bet", "vibing", "vibes", "slay",
    "ate", "serving", "iconic", "periodt", "sis", "queen", "king", "gas",
    "heat", "banger", "certified", "main character", "understood the assignment",
    "real", "fr", "frfr", "ong", "lowkey", "highkey", "deadass", "goat",
    "legendary", "epic", "clutch", "clean", "fresh", "sick", "rad", "gnarly",
    "on point", "killing it", "nailing it", "crushing it", "winning", "W",
    "dub", "blessed", "thankful", "grateful", "stoked", "hyped", "pumped",
    "turnt", "turnt up", "turned up", "amped", "jazzed", "gassed", "gassed up",
    "living my best life", "its the", "chef's kiss", "immaculate", "divine",
    "muah", "perfection", "flawless", "mwah", "chefs kiss", "mint", "brilliant",
    "wicked", "ace", "boss", "tight", "solid", "legit", "straight up",

    # AAVE and urban slang
    "fye", "drip", "swag", "flex", "flexing", "stunting", "finesse", "finessed",
    "bougie", "boujee", "ratchet", "turnt", "hype", "hypebeast", "fly",
    "on fleek", "baller", "ballin", "poppin", "popping", "slick", "smooth",
    "clutch", "ight", "aight", "woke", "stay woke", "clout", "clout chasing",
    "dripping", "drippy", "icy", "bling", "blinged out", "gucci", "chill",
    "chillin", "no worries", "all good", "cool beans", "word", "fasho",
    "yeet", "yeeted", "yoink", "ayy", "ayyy", "ayo", "skrt", "skrrt",
    "sheesh", "sheeeesh", "bustin", "hittin", "smackin", "thats cap",

    # British slang
    "chuffed", "buzzing", "mint", "sick", "wicked", "brilliant", "ace",
    "mega", "brill", "lush", "boss", "sound", "proper", "well good",
    "banging", "leng", "peng", "fit", "bare", "wagwan", "mandem", "fam",
    "innit", "bruv", "blud", "ting", "wasteman", "peak", "allow it",
    "safe", "calm", "long", "moist", "pukka", "sorted", "bless", "nang",

    # Australian slang
    "ripper", "bonzer", "beaut", "beauty", "stoked", "chuffed", "heaps",
    "fully sick", "mad", "choice", "choice bro", "sweet as", "wicked",
    "grouse", "tops", "ace", "legend", "ledge", "sicko", "banger",

    # Anger/negative slang
    "salty", "pressed", "triggered", "tilted", "beefing", "toxic", "cap",
    "capping", "sus", "mid", "basic", "cringe", "ick", "ratio", "L",
    "caught in 4k", "yikes", "big yikes", "sketchy", "janky", "crusty",
    "busted", "wack", "whack", "trash", "garbage", "dumpster fire", "clown",
    "bozo", "goofy", "lame", "corny", "cheesy", "sus", "suspicious", "sketch",
    "shady", "fishy", "off", "weird", "odd", "cringe", "cringy", "cringey",
    "embarrassing", "pathetic", "sad", "not it", "aint it", "cancelled",
    "canceled", "done", "finished", "over", "dead to me", "blocked",
    "unfollowed", "muted", "ignored", "ghosted", "left on read", "seen",
    "curved", "dissed", "roasted", "burned", "flamed", "dragged", "exposed",
    "outed", "called out", "put on blast", "ratio'd", "ratiod", "owned",
    "pwned", "rekt", "wrecked", "destroyed", "demolished", "obliterated",
    "bodied", "clapped", "slapped", "smacked", "whooped", "cooked",
    "bogus", "bootleg", "cheap", "tacky", "tasteless", "gaudy", "obnoxious",
    "annoying", "irritating", "infuriating", "maddening", "rage inducing",
    "problematic", "red flag", "major red flag", "walking red flag", "toxic",
    "manipulative", "gaslighting", "narcissistic", "entitled", "karen",

    # Sadness slang
    "down bad", "hurting", "gutted", "rip", "dead", "deceased", "crying",
    "sobbing", "im weak", "i cant", "done", "over it", "mood", "same",
    "big mood", "feels", "the feels", "all the feels", "right in the feels",
    "oof", "ooof", "yikes", "rough", "that hurts", "pain", "suffering",
    "depresso", "sad boi", "sad boy", "sad girl", "in my feels", "feeling",
    "broken", "shattered", "crushed", "devastated", "destroyed", "wrecked",
    "hurts", "stings", "burns", "cuts deep", "hits home", "too real",
    "relatable", "me", "literally me", "attacked", "called out", "exposed",
    "lonely", "lonesome", "alone", "isolated", "abandoned", "forgotten",
    "unloved", "unwanted", "rejected", "dumped", "left", "ghosted",
    "empty", "hollow", "numb", "drained", "exhausted", "burnt out",
    "burnout", "done", "over it", "cant anymore", "im done", "im out",
    "cries", "tears", "ugly crying", "bawling", "weeping", "sobbing",
    "heartbroken", "heartbreak", "heart hurts", "aching", "missing",
    "longing", "yearning", "pining", "grieving", "mourning", "lost",

    # Passion/attraction slang
    "simp", "simping", "stan", "stanning", "ship", "thirsty", "down bad",
    "caught feelings", "wifey", "hubby", "bae", "zaddy", "snack", "meal",
    "baddie", "fine", "shorty", "shawty", "boo", "ride or die", "main",
    "soulmate", "twin flame", "endgame", "otp", "ship", "shipped", "ships",
    "heart eyes", "crush", "crushing", "crushed", "fallen", "falling",
    "whipped", "sprung", "head over heels", "smitten", "obsessed",
    "hot", "hottie", "cutie", "cutie pie", "gorgeous", "stunning",
    "beautiful", "handsome", "attractive", "eye candy", "total babe",
    "heartthrob", "dreamboat", "stud", "hunk", "babe", "bombshell",
    "smoke show", "smokeshow", "dime", "dime piece", "ten", "perfect ten",
    "wifey material", "hubby material", "keeper", "the one", "my person",
    "my everything", "my world", "my heart", "my love", "my baby",
    "honeybun", "sweetie", "sweetheart", "darling", "dear", "hun", "babe",
    "baby", "bb", "bby", "luv", "luvs", "lovey", "lovebug", "cuddle bug",
    "snuggle bunny", "cuddles", "hugs", "kisses", "xoxo", "mwah",

    # Surprise slang
    "shook", "shooketh", "mindblown", "wild", "insane", "bruh", "bro",
    "what the", "say less", "facts", "spill", "tea", "receipts", "woah",
    "whoa", "wow", "omg", "omfg", "wtf", "wth", "hold up", "wait what",
    "excuse me", "pardon", "come again", "say that again", "huh", "wut",
    "im shook", "shookened", "gobsmacked", "flabbergasted", "speechless",
    "no way", "shut up", "get out", "stop", "stahp", "dead", "im dead",
    "deceased", "literally dying", "cant breathe", "crying", "screaming",
    "yelling", "hollering", "howling", "cackling", "dying", "im weak",
    "sent me", "took me out", "killed me", "slayed me", "ended me",
    "plot twist", "unexpected", "didnt see that coming", "out of nowhere",
    "bombshell", "dropped", "dropped like a bomb", "explosive", "shocking",
    "jaw dropping", "eye opening", "mind blowing", "game changer",
    "sus", "sussy", "sussy baka", "imposter", "among us", "red sus",

    # Internet/Gen Z additions
    "karen", "boomer", "zoomer", "millennial", "gen z", "gen alpha",
    "cheugy", "rent free", "touch grass", "chronically online", "unhinged",
    "feral", "girlboss", "gaslight", "gatekeep", "delulu", "its giving",
    "giving", "very demure", "brat", "core", "coded", "energy", "vibes",
    "aesthetic", "vibe check", "passed the vibe check", "failed the vibe check",
    "main character energy", "npc", "side character", "background character",
    "plot armor", "character development", "redemption arc", "villain arc",
    "chosen one", "protagonist", "antagonist", "anti hero", "morally grey",
    "red flag", "green flag", "beige flag", "ick", "the ick", "icks",
    "situationship", "entanglement", "talking stage", "roster", "rotation",
    "sneaky link", "fwb", "friends with benefits", "no strings attached",
    "casual", "exclusive", "official", "facebook official", "insta official",
    "soft launch", "hard launch", "public", "private", "low key", "high key",
    "brain rot", "brainrot", "terminally online", "parasocial", "fanfic",
    "headcanon", "canon", "fandom", "stan", "anti", "hater", "supporter",
    "era", "in my era", "entering my era", "villain era", "healing era",
    "hot girl summer", "sad girl autumn", "cuffing season", "summer fling"
]

# Common vocabulary words to enhance emotion detection
VOCABULARY_WORDS_EN: List[str] = [
    # Anger vocabulary - comprehensive
    "aggravated", "antagonized", "bitter", "contemptuous", "exasperated",
    "incensed", "indignant", "infuriated", "irate", "livid", "resentful",
    "seething", "vengeful", "vindictive", "wrathful", "acrimonious",
    "belligerent", "bellicose", "cantankerous", "choleric", "churlish",
    "contentious", "cross", "curmudgeonly", "disgruntled", "enraged",
    "ferocious", "fierce", "fiery", "fractious", "fuming", "grouchy",
    "grumpy", "heated", "hostile", "huffy", "ill-tempered", "impatient",
    "incensed", "inflamed", "irascible", "ireful", "maddened", "menacing",
    "murderous", "outraged", "peeved", "petulant", "piqued", "provoked",
    "querulous", "rabid", "raging", "rankled", "riled", "roiled", "savage",
    "scorching", "seething", "short-tempered", "sore", "spiteful", "splenetic",
    "stormy", "sulky", "sullen", "surly", "testy", "tetchy", "truculent",
    "turbulent", "umbrageous", "vehement", "venomous", "vexed", "violent",
    "virulent", "volcanic", "worked up", "wrath", "wrathful", "wroth",

    # Disgust vocabulary - comprehensive
    "abhorrent", "appalling", "contemptible", "deplorable", "despicable",
    "detestable", "distasteful", "execrable", "heinous", "loathsome",
    "nauseating", "objectionable", "odious", "reprehensible", "revolting",
    "abominable", "atrocious", "base", "beastly", "contemptible", "corrupt",
    "debased", "degenerate", "degrading", "depraved", "dirty", "disagreeable",
    "disreputable", "foul", "ghastly", "grimy", "grotesque", "gruesome",
    "hideous", "horrid", "ignoble", "ignominious", "impure", "indecent",
    "infamous", "iniquitous", "insufferable", "intolerable", "malodorous",
    "monstrous", "nefarious", "noisome", "noxious", "obnoxious", "obscene",
    "offensive", "opprobrious", "outrageous", "pestilent", "putrid", "rank",
    "raunchy", "repellent", "repugnant", "repulsive", "revolting", "rotten",
    "scandalous", "scurvy", "shameful", "sickening", "sleazy", "slimy",
    "sordid", "squalid", "stinking", "unclean", "unsavory", "vile", "vulgar",

    # Fear vocabulary - comprehensive
    "alarmed", "apprehensive", "aghast", "consternated", "dismayed",
    "daunted", "distressed", "fretful", "intimidated", "perturbed",
    "rattled", "trepidatious", "unnerved", "wary", "jittery", "afraid",
    "affrighted", "agitated", "antsy", "anxious", "awestruck", "chilled",
    "cowardly", "craven", "creeped out", "diffident", "discomposed",
    "disquieted", "disturbed", "edgy", "eerie", "excitable", "fainthearted",
    "fearful", "fidgety", "frantic", "fretful", "frightened", "frozen",
    "gutless", "haunted", "hesitant", "horrified", "hysterical", "jumpy",
    "lily-livered", "nervous", "neurotic", "overwrought", "panicked",
    "panicky", "paranoid", "petrified", "phobic", "pusillanimous", "quaking",
    "quavering", "quivering", "restless", "scared", "shaken", "shaky",
    "shell-shocked", "shrinking", "skittish", "spineless", "spooked",
    "startled", "stunned", "suspicious", "tense", "terrified", "terrorized",
    "timid", "timorous", "trembling", "tremulous", "troubled", "uneasy",
    "unglued", "unhinged", "unsettled", "uptight", "worried", "yellow",

    # Joy vocabulary - comprehensive
    "blissful", "buoyant", "ebullient", "effervescent", "elated",
    "enraptured", "euphoric", "exhilarated", "exuberant", "gleeful",
    "jovial", "jubilant", "mirthful", "radiant", "rapturous", "airy",
    "animated", "beatific", "beaming", "blithe", "blithesome", "breezy",
    "bright", "bubbly", "carefree", "cheerful", "cheery", "chirpy",
    "chipper", "comfortable", "content", "contented", "convivial", "delighted",
    "ecstatic", "elated", "enchanted", "energized", "enjoyable", "entertained",
    "enthusiastic", "enthralled", "exalted", "excited", "festive", "free",
    "frisky", "frolicsome", "fulfilled", "gay", "genial", "glad", "glorious",
    "good-humored", "gratified", "happy", "heartened", "hearty", "hilarious",
    "hopeful", "humorous", "in good spirits", "in high spirits", "jaunty",
    "jocund", "jolly", "joyful", "joyous", "laughing", "lighthearted",
    "lively", "merry", "optimistic", "overjoyed", "peaceful", "peppy",
    "perky", "playful", "pleased", "pleasurable", "rapturous", "relieved",
    "satisfied", "sparkling", "spirited", "sprightly", "sunny", "thrilled",
    "tickled", "transported", "triumphant", "upbeat", "vibrant", "vivacious",
    "wonderful", "zestful", "zippy",

    # Sadness vocabulary - comprehensive
    "bereft", "crestfallen", "dejected", "despairing", "disconsolate",
    "disheartened", "doleful", "downcast", "forlorn", "inconsolable",
    "lugubrious", "melancholic", "morose", "plaintive", "wistful",
    "afflicted", "agonized", "anguished", "bemoaning", "bereaved", "bitter",
    "black", "bleak", "blue", "brokenhearted", "bummed", "cheerless",
    "comfortless", "crushed", "dark", "defeated", "deflated", "depressed",
    "desolate", "despondent", "devastated", "disappointed", "discontented",
    "discouraged", "disenchanted", "dismal", "dispirited", "distraught",
    "distressed", "dolorous", "dour", "down", "downhearted", "dreary",
    "droopy", "dull", "elegiac", "funereal", "gloomy", "glum", "grave",
    "gray", "grief-stricken", "grieved", "grieving", "grim", "heavy-hearted",
    "helpless", "hopeless", "hurting", "in despair", "joyless", "lachrymose",
    "lamentable", "languishing", "listless", "lonely", "lonesome", "low",
    "low-spirited", "miserable", "moping", "mopey", "morbid", "mournful",
    "oppressed", "pained", "pathetic", "pensive", "pessimistic", "piteous",
    "pitiful", "rueful", "saddened", "somber", "sorrowful", "sorry",
    "spiritless", "stricken", "suffering", "sullen", "tearful", "tormented",
    "tragic", "troubled", "unhappy", "upset", "weepy", "woebegone", "woeful",
    "wounded", "wretched",

    # Passion vocabulary - comprehensive
    "amorous", "ardent", "besotted", "captivated", "devoted",
    "enamored", "entranced", "fervent", "infatuated", "smitten",
    "yearning", "zealous", "impassioned", "desirous", "lustful",
    "adoring", "affectionate", "amative", "attracted", "avid", "burning",
    "caring", "charmed", "cherishing", "consumed", "crazy about", "craving",
    "devoted", "doting", "drawn to", "eager", "earnest", "emotional",
    "enflamed", "engrossed", "enthralled", "enthusiastic", "excited",
    "fascinated", "fanatical", "fervid", "fiery", "fond", "frenzied",
    "glowing", "gone on", "gushing", "head over heels", "heartthrob",
    "heated", "hooked", "hot", "hung up", "hungry", "in love", "intent",
    "intense", "intoxicated", "keen", "kindled", "longing", "lovesick",
    "loving", "mad about", "mesmerized", "nutty about", "obsessed",
    "passionate", "pining", "possessed", "preoccupied", "rapturous",
    "romantic", "seduced", "sensual", "sexy", "spellbound", "steamy",
    "stimulated", "stirred", "struck", "sweet on", "taken with", "tender",
    "torrid", "transported", "turned on", "vehement", "warm", "wild about",
    "worshipful", "wrapped up in",

    # Surprise vocabulary - comprehensive
    "aghast", "astounded", "bewildered", "confounded", "dumbfounded",
    "flabbergasted", "gobsmacked", "nonplussed", "perplexed", "staggered",
    "stupefied", "thunderstruck", "taken aback", "baffled", "mystified",
    "agape", "agog", "amazed", "astonished", "awestruck", "blown away",
    "breathless", "caught off guard", "confused", "dazed", "discombobulated",
    "disconcerted", "disoriented", "dizzy", "electrified", "floored",
    "flustered", "frozen", "incredulous", "jolted", "knocked for a loop",
    "lost for words", "marveling", "open-mouthed", "overwhelmed", "paralyzed",
    "puzzled", "rattled", "reeling", "rendered speechless", "rocked",
    "scandalized", "shaken", "shocked", "speechless", "spellbound",
    "startled", "struck dumb", "stumped", "stunned", "surprised", "thrown",
    "unbelieving", "unnerved", "unsettled", "wide-eyed", "wondering", "wowed"
]

VOCABULARY_WORDS_ES: List[str] = [
    # Spanish emotion vocabulary - comprehensive
    # Anger
    "enfurecido", "colérico", "airado", "indignado", "resentido",
    "furioso", "rabioso", "iracundo", "irascible", "irritable",
    "malhumorado", "enojado", "cabreado", "encabronado", "mosqueado",
    "sulfurado", "enfadado", "molesto", "fastidiado", "hastiado",
    "exasperado", "impaciente", "frustrado", "agresivo", "hostil",
    "belicoso", "beligerante", "combativo", "pendenciero", "bronco",
    "brusco", "áspero", "gruñón", "cascarrabias", "refunfuñón",
    "berrinchudo", "corajudo", "temperamental", "violento", "brutal",

    # Disgust
    "asqueado", "repugnado", "horrorizado", "nauseado", "mareado",
    "repelido", "rechazado", "ofendido", "indignado", "escandalizado",
    "asqueroso", "repugnante", "repulsivo", "nauseabundo", "vomitivo",
    "horrendo", "horrible", "espantoso", "atroz", "abominable",
    "detestable", "odioso", "execrable", "inmundo", "sucio",
    "pútrido", "fétido", "maloliente", "pestilente", "hediondo",

    # Fear
    "espantado", "aterrado", "aterrorizado", "horrorizado", "pasmado",
    "asustado", "miedoso", "temeroso", "medroso", "cobarde",
    "acobardado", "amedrentado", "intimidado", "acoquinado", "acojonado",
    "nervioso", "ansioso", "angustiado", "inquieto", "intranquilo",
    "preocupado", "aprensivo", "alarmado", "sobresaltado", "perturbado",
    "desasosegado", "agitado", "alterado", "estremecido", "tembloroso",
    "paranoico", "fóbico", "pánico", "histérico", "desquiciado",

    # Joy
    "dichoso", "gozoso", "jubiloso", "radiante", "eufórico",
    "feliz", "contento", "alegre", "satisfecho", "complacido",
    "encantado", "entusiasmado", "emocionado", "ilusionado", "esperanzado",
    "optimista", "animado", "vivaz", "vivaracho", "jovial",
    "festivo", "risueño", "sonriente", "brillante", "resplandeciente",
    "exultante", "triunfante", "victorioso", "exitoso", "afortunado",
    "bendecido", "agradecido", "reconocido", "maravillado", "fascinado",
    "extasiado", "arrobado", "embelesado", "hechizado", "cautivado",

    # Sadness
    "afligido", "desolado", "abatido", "apenado", "desconsolado",
    "triste", "melancólico", "deprimido", "desanimado", "decaído",
    "alicaído", "apesadumbrado", "acongojado", "compungido", "consternado",
    "desolado", "desesperado", "desesperanzado", "pesimista", "derrotado",
    "devastado", "destrozado", "hundido", "hecho polvo", "roto",
    "herido", "lastimado", "dolido", "sufriente", "atormentado",
    "angustiado", "afectado", "conmovido", "sensibilizado", "emocionado",
    "nostálgico", "añorante", "solitario", "solo", "abandonado",

    # Passion
    "enamorado", "apasionado", "cautivado", "embelesado", "ardiente",
    "amoroso", "cariñoso", "afectuoso", "tierno", "dulce",
    "romántico", "sentimental", "sensible", "emotivo", "expresivo",
    "ferviente", "fervoroso", "vehemente", "intenso", "profundo",
    "devoto", "dedicado", "entregado", "rendido", "sometido",
    "obsesionado", "fascinado", "hechizado", "embrujado", "encantado",
    "seducido", "atraído", "tentado", "excitado", "estimulado",

    # Surprise
    "atónito", "estupefacto", "perplejo", "pasmado", "boquiabierto",
    "sorprendido", "asombrado", "maravillado", "impresionado", "impactado",
    "conmocionado", "sobrecogido", "alucinado", "flipado", "anonado",
    "desconcertado", "desorientado", "confundido", "turbado", "alterado",
    "sacudido", "conmovido", "electrizado", "galvanizado", "anonadado",

    # Mexican/Latin American slang
    "chido", "padre", "padrísimo", "órale", "ándale", "híjole",
    "chingón", "con madre", "a todo dar", "de poca", "bien",
    "gacho", "feo", "culero", "mamón", "pendejo", "güey",
    "agüitado", "sacado de onda", "clavado", "enganchado", "prendido"
]

VOCABULARY_WORDS_PT: List[str] = [
    # Portuguese emotion vocabulary - comprehensive
    # Anger (Raiva)
    "enfurecido", "colérico", "irado", "indignado", "ressentido",
    "furioso", "raivoso", "irascível", "irritável", "nervoso",
    "mal-humorado", "zangado", "bravo", "irritado", "chateado",
    "exasperado", "impaciente", "frustrado", "agressivo", "hostil",
    "belicoso", "beligerante", "combativo", "briguento", "esquentado",
    "grosso", "áspero", "ranzinza", "rabugento", "mal-encarado",
    "temperamental", "violento", "brutal", "feroz", "selvagem",
    "possesso", "louco de raiva", "fulo da vida", "puto", "putasso",

    # Disgust (Nojo)
    "enojado", "repugnado", "horrorizado", "nauseado", "enjoado",
    "repelido", "rejeitado", "ofendido", "indignado", "escandalizado",
    "nojento", "repugnante", "repulsivo", "nauseante", "vomitivo",
    "horrendo", "horrível", "espantoso", "atroz", "abominável",
    "detestável", "odioso", "execrável", "imundo", "sujo",
    "pútrido", "fétido", "malcheiroso", "pestilento", "fedorento",

    # Fear (Medo)
    "espantado", "aterrado", "aterrorizado", "horrorizado", "pasmado",
    "assustado", "medroso", "temeroso", "amedrontado", "covarde",
    "acovardado", "intimidado", "apavorado", "apanicado", "aflito",
    "nervoso", "ansioso", "angustiado", "inquieto", "intranquilo",
    "preocupado", "apreensivo", "alarmado", "sobressaltado", "perturbado",
    "desassossegado", "agitado", "alterado", "estremecido", "tremendo",
    "paranoico", "fóbico", "em pânico", "histérico", "descontrolado",
    "cagado de medo", "borrado", "com cagaço", "tenso", "arrepiado",

    # Joy (Alegria)
    "ditoso", "jubiloso", "radiante", "extasiado", "exultante",
    "feliz", "contente", "alegre", "satisfeito", "realizado",
    "encantado", "entusiasmado", "emocionado", "empolgado", "animado",
    "otimista", "animado", "vivaz", "espevitado", "jovial",
    "festivo", "risonho", "sorridente", "brilhante", "resplandecente",
    "triunfante", "vitorioso", "bem-sucedido", "afortunado", "sortudo",
    "abençoado", "agradecido", "grato", "maravilhado", "fascinado",
    "extasiado", "arrebatado", "encantado", "deslumbrado", "cativado",
    "felizão", "felicíssimo", "nas nuvens", "no céu", "radiante",

    # Sadness (Tristeza)
    "aflito", "desolado", "abatido", "angustiado", "inconsolável",
    "triste", "melancólico", "deprimido", "desanimado", "cabisbaixo",
    "abatido", "pesaroso", "consternado", "compungido", "amargurado",
    "desolado", "desesperado", "desesperançado", "pessimista", "derrotado",
    "devastado", "destroçado", "arrasado", "acabado", "destruído",
    "ferido", "magoado", "dolorido", "sofredor", "atormentado",
    "angustiado", "afetado", "comovido", "sensibilizado", "emocionado",
    "nostálgico", "saudoso", "solitário", "sozinho", "abandonado",
    "chateado", "pra baixo", "na fossa", "de luto", "choroso",

    # Passion (Paixão)
    "apaixonado", "encantado", "cativado", "arrebatado", "ardente",
    "amoroso", "carinhoso", "afetuoso", "terno", "doce",
    "romântico", "sentimental", "sensível", "emotivo", "expressivo",
    "fervoroso", "veemente", "intenso", "profundo", "forte",
    "devoto", "dedicado", "entregue", "rendido", "submisso",
    "obcecado", "fascinado", "enfeitiçado", "encantado", "hipnotizado",
    "seduzido", "atraído", "tentado", "excitado", "estimulado",
    "gamado", "caído", "louco por", "doido por", "vidrado",

    # Surprise (Surpresa)
    "atônito", "estupefato", "perplexo", "pasmo", "boquiaberto",
    "surpreso", "espantado", "maravilhado", "impressionado", "impactado",
    "chocado", "abalado", "alucinado", "abismado", "embasbacado",
    "desconcertado", "desorientado", "confuso", "perturbado", "alterado",
    "sacudido", "comovido", "eletrizado", "galvanizado", "estarrecido",
    "de queixo caído", "sem palavras", "sem reação", "paralisado", "congelado",

    # Brazilian slang
    "daora", "massa", "irado", "sinistro", "foda", "top", "show",
    "mó", "firmeza", "suave", "de boa", "tranquilo", "beleza",
    "bolado", "pistola", "p da vida", "mordido", "revoltado",
    "na bad", "tristão", "deprê", "desanimadão", "na merda",
    "apaixonadão", "gamadão", "caidinho", "envolvido", "amarrado",
    "chocado", "passado", "sem noção", "viajando", "bugado"
]


# ---------------------------------------------------------------------------
# Lexicon Expansion Functions
# ---------------------------------------------------------------------------

def expand_lexicon_from_external(
    current_lexicon: Dict[str, Dict[str, Dict[str, float]]],
    languages: List[str] = ["en", "es", "pt"],
    include_slang: bool = True,
    include_vocabulary: bool = True,
    progress_callback: Optional[callable] = None
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Expand the current lexicon with words from external sources.

    Args:
        current_lexicon: Existing lexicon in format {lang: {word: {emotion: weight}}}
        languages: Languages to expand
        include_slang: Fetch slang from Urban Dictionary (English)
        include_vocabulary: Fetch formal vocabulary words
        progress_callback: Optional callback for progress updates

    Returns:
        Merged lexicon with new entries
    """
    expanded = {lang: dict(current_lexicon.get(lang, {})) for lang in languages}

    for lang in languages:
        words_to_fetch = []

        if lang == "en":
            if include_slang:
                # Filter out words already in lexicon
                existing = set(expanded.get("en", {}).keys())
                new_slang = [w for w in SLANG_WORDS_TO_FETCH if w.lower() not in existing]
                words_to_fetch.extend(new_slang)

            if include_vocabulary:
                existing = set(expanded.get("en", {}).keys())
                new_vocab = [w for w in VOCABULARY_WORDS_EN if w.lower() not in existing]
                words_to_fetch.extend(new_vocab)

        elif lang == "es":
            if include_vocabulary:
                existing = set(expanded.get("es", {}).keys())
                new_vocab = [w for w in VOCABULARY_WORDS_ES if w.lower() not in existing]
                words_to_fetch.extend(new_vocab)

        elif lang == "pt":
            if include_vocabulary:
                existing = set(expanded.get("pt", {}).keys())
                new_vocab = [w for w in VOCABULARY_WORDS_PT if w.lower() not in existing]
                words_to_fetch.extend(new_vocab)

        if words_to_fetch:
            print(f"Fetching {len(words_to_fetch)} words for {lang}...")

            new_entries = batch_fetch_words(
                words_to_fetch,
                language=lang,
                include_slang=(lang == "en" and include_slang),
                progress_callback=progress_callback
            )

            # Merge new entries
            lang_lexicon = expanded.setdefault(lang, {})
            for word, emotions in new_entries.items():
                if word not in lang_lexicon:
                    lang_lexicon[word] = emotions
                else:
                    # Merge emotions, preferring higher weights
                    for emotion, weight in emotions.items():
                        if emotion not in lang_lexicon[word]:
                            lang_lexicon[word][emotion] = weight
                        else:
                            lang_lexicon[word][emotion] = max(
                                lang_lexicon[word][emotion],
                                weight
                            )

    return expanded


def get_expansion_stats(
    original: Dict[str, Dict[str, Dict[str, float]]],
    expanded: Dict[str, Dict[str, Dict[str, float]]]
) -> Dict[str, Any]:
    """
    Get statistics about lexicon expansion.
    """
    stats = {
        "languages": {},
        "total_original": 0,
        "total_expanded": 0,
        "total_new": 0
    }

    for lang in set(list(original.keys()) + list(expanded.keys())):
        orig_count = len(original.get(lang, {}))
        exp_count = len(expanded.get(lang, {}))
        new_count = exp_count - orig_count

        stats["languages"][lang] = {
            "original": orig_count,
            "expanded": exp_count,
            "new_words": new_count
        }

        stats["total_original"] += orig_count
        stats["total_expanded"] += exp_count
        stats["total_new"] += new_count

    return stats


# ---------------------------------------------------------------------------
# Export Functions
# ---------------------------------------------------------------------------

def export_lexicon_to_json(
    lexicon: Dict[str, Dict[str, Dict[str, float]]],
    filepath: str
) -> None:
    """Export lexicon to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=2)


def import_lexicon_from_json(filepath: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Import lexicon from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Direct Word Lookup API
# ---------------------------------------------------------------------------

def lookup_word(word: str, language: str = "en") -> Dict[str, Any]:
    """
    Look up a single word and return detailed information.

    Returns:
        Dict with definitions, extracted emotions, and source info
    """
    definitions = []

    if language == "en":
        definitions.extend(fetch_free_dictionary_en(word))
        definitions.extend(fetch_urban_dictionary(word))
    elif language == "es":
        definitions.extend(fetch_free_dictionary_es(word))
    elif language == "pt":
        definitions.extend(fetch_free_dictionary_pt(word))

    result = {
        "word": word,
        "language": language,
        "definitions": [],
        "extracted_emotions": None,
        "sources": []
    }

    all_emotions: Dict[str, float] = {}

    for defn in definitions:
        defn_info = {
            "source": defn.source,
            "text": defn.definitions,
            "examples": defn.examples,
            "synonyms": defn.synonyms,
            "part_of_speech": defn.part_of_speech
        }

        if defn.source == "urban_dictionary":
            defn_info["thumbs_up"] = defn.thumbs_up

        result["definitions"].append(defn_info)

        if defn.source not in result["sources"]:
            result["sources"].append(defn.source)

        # Extract emotions
        weight = extract_emotion_weights(defn)
        if weight:
            for emotion, score in weight.emotions.items():
                if emotion not in all_emotions:
                    all_emotions[emotion] = 0.0
                all_emotions[emotion] = max(all_emotions[emotion], score)

    if all_emotions:
        result["extracted_emotions"] = all_emotions

    return result
