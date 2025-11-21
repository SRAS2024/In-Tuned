# detector/formatter.py
# Formatter for EmotionDetector output.
# Shapes detector results into a JSON friendly structure for the UI.

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    # Relative import when used as a package
    from .detector import analyze_text, EMOTIONS, InvalidTextError
except ImportError:  # pragma: no cover
    # Fallback for running this file directly
    from detector import analyze_text, EMOTIONS, InvalidTextError  # type: ignore


# =============================================================================
# Localization data
# =============================================================================


def _normalize_locale(locale: Optional[str]) -> str:
    if not locale:
        return "en"
    loc = str(locale).lower()
    if loc.startswith("es"):
        return "es"
    if loc.startswith("pt") or loc.startswith("br"):
        return "pt"
    return "en"


EMOTION_LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        "anger": "Anger",
        "disgust": "Disgust",
        "fear": "Fear",
        "joy": "Joy",
        "sadness": "Sadness",
        "passion": "Passion",
        "surprise": "Surprise",
    },
    "es": {
        "anger": "Ira",
        "disgust": "Asco",
        "fear": "Miedo",
        "joy": "Alegría",
        "sadness": "Tristeza",
        "passion": "Pasión",
        "surprise": "Sorpresa",
    },
    "pt": {
        "anger": "Raiva",
        "disgust": "Nojo",
        "fear": "Medo",
        "joy": "Alegria",
        "sadness": "Tristeza",
        "passion": "Paixão",
        "surprise": "Surpresa",
    },
}

# Intensity specific labels for the current emotion
# Buckets: very_low, low, moderate, high, very_high
EMOTION_INTENSITY_LABELS: Dict[str, Dict[str, Dict[str, str]]] = {
    "en": {
        "anger": {
            "very_low": "Slightly irritated",
            "low": "Frustrated",
            "moderate": "Angry",
            "high": "Very angry",
            "very_high": "Furious",
        },
        "sadness": {
            "very_low": "A little low",
            "low": "Low and tired",
            "moderate": "Heavy hearted",
            "high": "Very sad and heavy",
            "very_high": "Heartbroken",
        },
        "joy": {
            "very_low": "Slightly pleased",
            "low": "Content",
            "moderate": "Happy",
            "high": "Very happy",
            "very_high": "Overjoyed",
        },
        "fear": {
            "very_low": "Slightly uneasy",
            "low": "Worried",
            "moderate": "Anxious",
            "high": "Very anxious",
            "very_high": "Panicked",
        },
        "passion": {
            "very_low": "Warm affection",
            "low": "Affectionate",
            "moderate": "Loving",
            "high": "Deeply loving",
            "very_high": "Intensely in love",
        },
        "disgust": {
            "very_low": "Slightly put off",
            "low": "Uncomfortable",
            "moderate": "Displeased",
            "high": "Disgusted",
            "very_high": "Repulsed",
        },
        "surprise": {
            "very_low": "Slightly surprised",
            "low": "Surprised",
            "moderate": "Very surprised",
            "high": "Shocked",
            "very_high": "Stunned",
        },
    },
    "es": {
        "anger": {
            "very_low": "Levemente molesto",
            "low": "Frustrado",
            "moderate": "Enojado",
            "high": "Muy enojado",
            "very_high": "Furioso",
        },
        "sadness": {
            "very_low": "Un poco bajo de ánimo",
            "low": "Desanimado",
            "moderate": "Con el corazón pesado",
            "high": "Muy triste y cargado",
            "very_high": "Destrozado",
        },
        "joy": {
            "very_low": "Levemente contento",
            "low": "Contento",
            "moderate": "Feliz",
            "high": "Muy feliz",
            "very_high": "Eufórico",
        },
        "fear": {
            "very_low": "Levemente inquieto",
            "low": "Preocupado",
            "moderate": "Ansioso",
            "high": "Muy ansioso",
            "very_high": "Aterrado",
        },
        "passion": {
            "very_low": "Afecto suave",
            "low": "Cariñoso",
            "moderate": "Amoroso",
            "high": "Muy amoroso",
            "very_high": "Profundamente enamorado",
        },
        "disgust": {
            "very_low": "Levemente incómodo",
            "low": "Incómodo",
            "moderate": "Disgustado",
            "high": "Muy disgustado",
            "very_high": "Repugnado",
        },
        "surprise": {
            "very_low": "Levemente sorprendido",
            "low": "Sorprendido",
            "moderate": "Muy sorprendido",
            "high": "Impactado",
            "very_high": "Atónito",
        },
    },
    "pt": {
        "anger": {
            "very_low": "Levemente incomodado",
            "low": "Irritado",
            "moderate": "Com raiva",
            "high": "Muito irritado",
            "very_high": "Furioso",
        },
        "sadness": {
            "very_low": "Um pouco para baixo",
            "low": "Abatido",
            "moderate": "Coração pesado",
            "high": "Muito triste e pesado",
            "very_high": "De coração partido",
        },
        "joy": {
            "very_low": "Levemente contente",
            "low": "Contente",
            "moderate": "Feliz",
            "high": "Muito feliz",
            "very_high": "Radiante",
        },
        "fear": {
            "very_low": "Levemente apreensivo",
            "low": "Preocupado",
            "moderate": "Ansioso",
            "high": "Muito ansioso",
            "very_high": "Apavorado",
        },
        "passion": {
            "very_low": "Afeto suave",
            "low": "Carinhoso",
            "moderate": "Amoroso",
            "high": "Muito amoroso",
            "very_high": "Intensamente apaixonado",
        },
        "disgust": {
            "very_low": "Levemente desconfortável",
            "low": "Desconfortável",
            "moderate": "Com nojo",
            "high": "Muito enojado",
            "very_high": "Repugnado",
        },
        "surprise": {
            "very_low": "Levemente surpreso",
            "low": "Surpreso",
            "moderate": "Muito surpreso",
            "high": "Chocado",
            "very_high": "Atônito",
        },
    },
}


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def _clamp(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _intensity_bucket_from_percent(percent: float) -> str:
    """
    Map a single emotion intensity percent to a coarse bucket.
    This is per emotion, not the global intensity band from detector.meta.
    """
    if percent >= 80.0:
        return "very_high"
    if percent >= 55.0:
        return "high"
    if percent >= 30.0:
        return "moderate"
    if percent >= 10.0:
        return "low"
    return "very_low"


def _pick_nuanced_labels(
    emotion_id: str,
    percent: float,
    locale: str,
) -> Dict[str, Optional[str]]:
    """
    Return nuanced labels for a given emotion and intensity percent.
    Falls back to base labels if no matching entry.
    """
    if not emotion_id or percent <= 0.01:
        return {"bucket": None, "nuanced_en": None, "nuanced_local": None}

    loc = _normalize_locale(locale)
    bucket = _intensity_bucket_from_percent(percent)

    en_map = EMOTION_INTENSITY_LABELS.get("en", {}).get(emotion_id, {})
    loc_map = EMOTION_INTENSITY_LABELS.get(loc, {}).get(emotion_id, {})

    nuanced_en = en_map.get(bucket)
    nuanced_local = loc_map.get(bucket)

    if nuanced_en is None and nuanced_local is None:
        return {"bucket": None, "nuanced_en": None, "nuanced_local": None}

    return {"bucket": bucket, "nuanced_en": nuanced_en, "nuanced_local": nuanced_local}


def _get_intensity_phrase_for_lang(
    emotion_id: str,
    percent: float,
    lang: str,
) -> str:
    """
    Get a human label for a single emotion at a given percent, for a language.
    """
    bucket = _intensity_bucket_from_percent(percent)
    lang = _normalize_locale(lang)

    label_map = EMOTION_INTENSITY_LABELS.get(lang, {}).get(emotion_id, {})
    phrase = label_map.get(bucket)
    if phrase:
        return phrase

    base = EMOTION_LABELS.get(lang, {}).get(emotion_id)
    if base:
        return base
    return EMOTION_LABELS["en"].get(emotion_id, emotion_id)


# Special pairwise mixture labels
COMBO_SPECIAL_LABELS: Dict[str, Dict[Tuple[str, str], str]] = {
    "en": {
        ("sadness", "anger"): "Hurt and angry",
        ("anger", "sadness"): "Angry and hurt",
        ("sadness", "fear"): "Sad and worried",
        ("fear", "sadness"): "Worried and sad",
        ("joy", "sadness"): "Bittersweet, both happy and sad",
        ("sadness", "joy"): "Bittersweet, sad but hopeful",
        ("joy", "surprise"): "Excited and pleasantly surprised",
        ("surprise", "joy"): "Pleasantly surprised and excited",
        ("joy", "passion"): "Warm loving joy",
        ("passion", "joy"): "Deeply loving and joyful",
        ("fear", "disgust"): "Disturbed and uneasy",
        ("disgust", "fear"): "Repulsed and uneasy",
        ("sadness", "passion"): "Missing someone you love",
        ("passion", "sadness"): "In love but hurting",
        ("fear", "passion"): "In love but afraid",
        ("passion", "fear"): "Afraid of losing someone you love",
        ("joy", "fear"): "Nervous excitement",
        ("fear", "joy"): "Excited but nervous",
        ("anger", "fear"): "Angry and anxious",
        ("fear", "anger"): "Anxious and angry",
        ("anger", "disgust"): "Angry and disgusted",
        ("disgust", "anger"): "Disgusted and angry",
        ("sadness", "disgust"): "Disappointed and let down",
        ("disgust", "sadness"): "Let down and uncomfortable",
        ("passion", "surprise"): "Pleasantly moved and surprised",
        ("surprise", "passion"): "Surprised and touched",
    },
    "es": {
        ("sadness", "anger"): "Dolido y enojado",
        ("anger", "sadness"): "Enojado y dolido",
        ("sadness", "fear"): "Triste y preocupado",
        ("fear", "sadness"): "Preocupado y triste",
        ("joy", "sadness"): "Agridulce, feliz y triste a la vez",
        ("sadness", "joy"): "Agridulce, triste pero con esperanza",
        ("joy", "surprise"): "Emocionado y gratamente sorprendido",
        ("surprise", "joy"): "Gratamente sorprendido y emocionado",
        ("joy", "passion"): "Alegría cálida y amorosa",
        ("passion", "joy"): "Profundamente amoroso y alegre",
        ("fear", "disgust"): "Perturbado e inquieto",
        ("disgust", "fear"): "Repugnado e inquieto",
        ("sadness", "passion"): "Echando de menos a alguien que amas",
        ("passion", "sadness"): "Enamorado pero dolido",
        ("fear", "passion"): "Enamorado pero con miedo",
        ("passion", "fear"): "Con miedo de perder a quien amas",
        ("joy", "fear"): "Emoción con nervios",
        ("fear", "joy"): "Nervioso pero ilusionado",
        ("anger", "fear"): "Enojado y ansioso",
        ("fear", "anger"): "Ansioso y enojado",
        ("anger", "disgust"): "Enojado y asqueado",
        ("disgust", "anger"): "Asqueado y enojado",
        ("sadness", "disgust"): "Decepcionado y desanimado",
        ("disgust", "sadness"): "Incómodo y desanimado",
        ("passion", "surprise"): "Conmovido y sorprendido",
        ("surprise", "passion"): "Sorprendido y tocado",
    },
    "pt": {
        ("sadness", "anger"): "Magoado e com raiva",
        ("anger", "sadness"): "Com raiva e magoado",
        ("sadness", "fear"): "Triste e preocupado",
        ("fear", "sadness"): "Preocupado e triste",
        ("joy", "sadness"): "Agridoce, feliz e triste ao mesmo tempo",
        ("sadness", "joy"): "Agridoce, triste mas esperançoso",
        ("joy", "surprise"): "Animado e agradavelmente surpreso",
        ("surprise", "joy"): "Agradavelmente surpreso e animado",
        ("joy", "passion"): "Alegria calorosa e amorosa",
        ("passion", "joy"): "Profundamente apaixonado e alegre",
        ("fear", "disgust"): "Perturbado e desconfortável",
        ("disgust", "fear"): "Com nojo e apreensivo",
        ("sadness", "passion"): "Com saudade de quem ama",
        ("passion", "sadness"): "Apaixonado mas magoado",
        ("fear", "passion"): "Apaixonado mas com medo",
        ("passion", "fear"): "Com medo de perder quem ama",
        ("joy", "fear"): "Animado e nervoso",
        ("fear", "joy"): "Nervoso mas animado",
        ("anger", "fear"): "Com raiva e ansioso",
        ("fear", "anger"): "Ansioso e com raiva",
        ("anger", "disgust"): "Com raiva e com nojo",
        ("disgust", "anger"): "Com nojo e com raiva",
        ("sadness", "disgust"): "Decepcionado e magoado",
        ("disgust", "sadness"): "Desconfortável e magoado",
        ("passion", "surprise"): "Comovido e surpreso",
        ("surprise", "passion"): "Surpreso e tocado",
    },
}


def _lookup_special_combo(
    primary: str,
    secondary: str,
    locale: str,
) -> Optional[str]:
    loc = _normalize_locale(locale)
    phrase = COMBO_SPECIAL_LABELS.get(loc, {}).get((primary, secondary))
    if phrase:
        return phrase
    if loc != "en":
        return COMBO_SPECIAL_LABELS.get("en", {}).get((primary, secondary))
    return None


def _build_combo_phrases(
    primary_id: str,
    primary_weight: float,
    secondary_id: str,
    secondary_weight: float,
    locale: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Given a primary and secondary emotion and their mixture weights, return
    a pair of phrases (en, localized) that describe the blend.
    """
    loc = _normalize_locale(locale)
    p_percent = max(primary_weight, 0.0) * 100.0
    s_percent = max(secondary_weight, 0.0) * 100.0

    p_en = _get_intensity_phrase_for_lang(primary_id, p_percent, "en")
    s_en = _get_intensity_phrase_for_lang(secondary_id, s_percent, "en")

    p_loc = _get_intensity_phrase_for_lang(primary_id, p_percent, loc)
    s_loc = _get_intensity_phrase_for_lang(secondary_id, s_percent, loc)

    special_en = _lookup_special_combo(primary_id, secondary_id, "en")
    special_loc = _lookup_special_combo(primary_id, secondary_id, loc)

    if special_en or special_loc:
        return special_en or p_en, special_loc or p_loc

    def lower_first(s: str) -> str:
        if not s:
            return s
        return s[0].lower() + s[1:]

    mostly_en = f"{p_en} with some {lower_first(s_en)}"
    mixed_en = f"Mixed {lower_first(p_en)} and {lower_first(s_en)}"

    if loc == "es":
        mostly_loc = f"{p_loc} con algo de {lower_first(s_loc)}"
        mixed_loc = f"Mezcla de {lower_first(p_loc)} y {lower_first(s_loc)}"
    elif loc == "pt":
        mostly_loc = f"{p_loc} com um pouco de {lower_first(s_loc)}"
        mixed_loc = f"Mistura de {lower_first(p_loc)} e {lower_first(s_loc)}"
    else:
        mostly_loc = mostly_en
        mixed_loc = mixed_en

    if primary_weight >= 0.6 and secondary_weight >= 0.2:
        return mostly_en, mostly_loc
    if primary_weight >= 0.45 and secondary_weight >= 0.3:
        return mixed_en, mixed_loc

    return p_en, p_loc


def _lc_first(s: str) -> str:
    if not s:
        return s
    return s[0].lower() + s[1:]


def _cap_first(s: str) -> str:
    if not s:
        return s
    return s[0].upper() + s[1:]


def _build_multi_emotion_phrase(
    primary_id: str,
    secondary_id: str,
    tertiary_id: str,
    mixture_vector: Dict[str, float],
    locale: str,
    meta: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Build a triad phrase for cases with three strong emotions.
    """
    loc = _normalize_locale(locale)

    pw = float(mixture_vector.get(primary_id, 0.0))
    sw = float(mixture_vector.get(secondary_id, 0.0))
    tw = float(mixture_vector.get(tertiary_id, 0.0))

    p_percent = pw * 100.0
    s_percent = sw * 100.0
    t_percent = tw * 100.0

    p_en = _get_intensity_phrase_for_lang(primary_id, p_percent, "en")
    s_en = _get_intensity_phrase_for_lang(secondary_id, s_percent, "en")
    t_en = _get_intensity_phrase_for_lang(tertiary_id, t_percent, "en")

    p_loc = _get_intensity_phrase_for_lang(primary_id, p_percent, loc)
    s_loc = _get_intensity_phrase_for_lang(secondary_id, s_percent, loc)
    t_loc = _get_intensity_phrase_for_lang(tertiary_id, t_percent, loc)

    meta = meta or {}
    pos_int = float(meta.get("positive_intensity", 0.0))
    neg_int = float(meta.get("negative_intensity", 0.0))
    mixed_valence = pos_int > 0.12 and neg_int > 0.12

    en_core = f"{_lc_first(p_en)}, {_lc_first(s_en)} and {_lc_first(t_en)}"

    if loc == "es":
        loc_core = f"{_lc_first(p_loc)}, {_lc_first(s_loc)} y {_lc_first(t_loc)}"
        loc_phrase = (
            _cap_first(f"sentimientos mezclados: {loc_core}")
            if mixed_valence
            else _cap_first(f"mezcla compleja de {loc_core}")
        )
    elif loc == "pt":
        loc_core = f"{_lc_first(p_loc)}, {_lc_first(s_loc)} e {_lc_first(t_loc)}"
        loc_phrase = (
            _cap_first(f"sentimentos mistos: {loc_core}")
            if mixed_valence
            else _cap_first(f"mistura complexa de {loc_core}")
        )
    else:
        loc_phrase = ""

    en_phrase = (
        _cap_first(f"mixed feelings: {en_core}")
        if mixed_valence
        else _cap_first(f"complex blend of {en_core}")
    )
    if not loc_phrase:
        loc_phrase = en_phrase

    return en_phrase, loc_phrase


def _compute_mixture_profile(
    mixture_vector: Dict[str, float]
) -> Dict[str, Any]:
    """
    Extra metrics describing mixture.
    """
    weights = [max(float(v), 0.0) for v in mixture_vector.values()]
    total = sum(weights)
    if total <= 0.0:
        return {
            "dominantStrength": 0.0,
            "secondaryStrength": 0.0,
            "entropy": 0.0,
            "mixtureType": "undefined",
        }

    normalized = [w / total for w in weights]
    sorted_norm = sorted(normalized, reverse=True)
    dominant_strength = sorted_norm[0] if sorted_norm else 0.0
    secondary_strength = sorted_norm[1] if len(sorted_norm) > 1 else 0.0

    entropy = 0.0
    for w in normalized:
        if w > 0.0:
            entropy -= w * math.log2(w)

    if dominant_strength >= 0.8:
        mix_type = "pure"
    elif dominant_strength >= 0.6 and secondary_strength <= 0.3:
        mix_type = "mostly_single"
    elif dominant_strength >= 0.45 and secondary_strength >= 0.25:
        mix_type = "mixed"
    else:
        mix_type = "highly_mixed"

    return {
        "dominantStrength": round(dominant_strength, 4),
        "secondaryStrength": round(secondary_strength, 4),
        "entropy": round(entropy, 4),
        "mixtureType": mix_type,
    }


def _apply_mixture_nuance_to_current(
    block: Dict[str, Any],
    mixture_vector: Dict[str, float],
    locale: str,
    mixture_profile: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Adjust nuanced labels for current emotion based on mixture.
    """
    if not block or not mixture_vector:
        return block

    primary_id = block.get("emotionId")
    if not primary_id:
        return block

    items = sorted(
        mixture_vector.items(), key=lambda kv: float(kv[1]), reverse=True
    )
    if not items:
        return block

    primary_weight = float(mixture_vector.get(primary_id, items[0][1]))

    secondary_id = None
    secondary_weight = 0.0
    tertiary_id = None
    tertiary_weight = 0.0

    for eid, w in items:
        if eid == primary_id:
            continue
        w_val = float(w)
        if w_val > secondary_weight:
            tertiary_id, tertiary_weight = secondary_id, secondary_weight
            secondary_id, secondary_weight = eid, w_val
        elif w_val > tertiary_weight:
            tertiary_id, tertiary_weight = eid, w_val

    mixture_profile = mixture_profile or _compute_mixture_profile(mixture_vector)
    mixture_type = mixture_profile.get("mixtureType", "undefined")
    meta = meta or {}

    if primary_weight < 0.08 and secondary_weight < 0.08:
        return block

    if (
        secondary_id is not None
        and tertiary_id is not None
        and secondary_weight >= 0.18
        and tertiary_weight >= 0.16
        and mixture_type in {"mixed", "highly_mixed"}
    ):
        combo_en, combo_loc = _build_multi_emotion_phrase(
            primary_id, secondary_id, tertiary_id, mixture_vector, locale, meta
        )
        block["nuancedLabel"] = combo_en
        block["nuancedLabelLocalized"] = combo_loc
        block["primaryEmotionId"] = primary_id
        block["primaryEmotionWeight"] = round(primary_weight, 6)
        block["secondaryEmotionId"] = secondary_id
        block["secondaryEmotionWeight"] = round(secondary_weight, 6)
        block["tertiaryEmotionId"] = tertiary_id
        block["tertiaryEmotionWeight"] = round(tertiary_weight, 6)
        block["mixtureSummaryKind"] = "triple"
        return block

    if secondary_id is None or secondary_weight < 0.15:
        block["mixtureSummaryKind"] = "single"
        return block

    combo_en, combo_loc = _build_combo_phrases(
        primary_id, primary_weight, secondary_id, secondary_weight, locale
    )
    if combo_en:
        block["nuancedLabel"] = combo_en
    if combo_loc:
        block["nuancedLabelLocalized"] = combo_loc

    block["primaryEmotionId"] = primary_id
    block["primaryEmotionWeight"] = round(primary_weight, 6)
    block["secondaryEmotionId"] = secondary_id
    block["secondaryEmotionWeight"] = round(secondary_weight, 6)
    block["mixtureSummaryKind"] = "pair"
    return block


# =============================================================================
# Hotline data
# =============================================================================


@dataclass
class HotlineInfo:
    region_code: str
    region_name: Dict[str, str]
    label: Dict[str, str]
    number: str
    url: Optional[str]
    notes: Dict[str, str]

    def to_locale_dict(self, locale: str) -> Dict[str, Any]:
        loc = _normalize_locale(locale)

        def pick(m: Dict[str, str]) -> str:
            return m.get(loc) or m.get("en") or ""

        return {
            "regionCode": self.region_code,
            "regionName": pick(self.region_name),
            "label": pick(self.label),
            "number": self.number,
            "url": self.url,
            "notes": pick(self.notes),
        }


HOTLINES: Dict[str, HotlineInfo] = {
    "US": HotlineInfo(
        region_code="US",
        region_name={"en": "United States", "es": "Estados Unidos", "pt": "Estados Unidos"},
        label={
            "en": "988 Suicide & Crisis Lifeline",
            "es": "Línea 988 de Suicidio y Crisis",
            "pt": "Linha 988 de Crise e Suicídio",
        },
        number="988",
        url="https://988lifeline.org",
        notes={
            "en": "Call or text 988, or use online chat if available in your area.",
            "es": "Llama o envía un mensaje al 988, o usa el chat en línea si está disponible.",
            "pt": "Ligue ou envie mensagem para 988, ou use o chat on-line se disponível.",
        },
    ),
    "CA": HotlineInfo(
        region_code="CA",
        region_name={"en": "Canada", "es": "Canadá", "pt": "Canadá"},
        label={
            "en": "988 Suicide Crisis Helpline",
            "es": "Línea 988 de Crisis de Suicidio",
            "pt": "Linha 988 de Crise de Suicídio",
        },
        number="988",
        url=None,
        notes={
            "en": "Call or text 988 for support anywhere in Canada.",
            "es": "Llama o envía un mensaje al 988 para apoyo en Canadá.",
            "pt": "Ligue ou envie mensagem para 988 em qualquer lugar do Canadá.",
        },
    ),
    "BR": HotlineInfo(
        region_code="BR",
        region_name={"en": "Brazil", "es": "Brasil", "pt": "Brasil"},
        label={
            "en": "CVV 188 Emotional Support",
            "es": "CVV 188 Apoyo Emocional",
            "pt": "CVV 188 Centro de Valorização da Vida",
        },
        number="188",
        url="https://www.cvv.org.br",
        notes={
            "en": "Free and confidential, available 24/7 in Portuguese.",
            "es": "Gratuito y confidencial, disponible 24/7 en portugués.",
            "pt": "Serviço gratuito e sigiloso, disponível 24h todos os dias.",
        },
    ),
    "PT": HotlineInfo(
        region_code="PT",
        region_name={"en": "Portugal", "es": "Portugal", "pt": "Portugal"},
        label={"en": "SOS Voz Amiga", "es": "SOS Voz Amiga", "pt": "SOS Voz Amiga"},
        number="+351 213 544 545",
        url="https://www.sosvozamiga.org",
        notes={
            "en": "Several numbers and schedules; check the website for details.",
            "es": "Hay varios números y horarios; consulta el sitio web para más detalles.",
            "pt": "Existem vários números e horários; veja o site para detalhes.",
        },
    ),
    "ES": HotlineInfo(
        region_code="ES",
        region_name={"en": "Spain", "es": "España", "pt": "Espanha"},
        label={
            "en": "024 Mental Health Hotline",
            "es": "Línea 024 'Llama a la vida'",
            "pt": "Linha 024 de Saúde Mental",
        },
        number="024",
        url=None,
        notes={
            "en": "You can also call the general emergency number 112 in urgent situations.",
            "es": "También puedes llamar al número general de emergencias 112 en casos urgentes.",
            "pt": "Em situações urgentes, também pode ligar para o número geral de emergência 112.",
        },
    ),
    "MX": HotlineInfo(
        region_code="MX",
        region_name={"en": "Mexico", "es": "México", "pt": "México"},
        label={"en": "Línea de la Vida", "es": "Línea de la Vida", "pt": "Línea de la Vida"},
        number="800 911 2000",
        url=None,
        notes={
            "en": "Free national helpline for emotional support and crisis.",
            "es": "Línea nacional gratuita para apoyo emocional y crisis.",
            "pt": "Linha nacional gratuita para apoio emocional e crises.",
        },
    ),
    "INTL": HotlineInfo(
        region_code="INTL",
        region_name={"en": "Your region", "es": "Tu región", "pt": "Sua região"},
        label={
            "en": "Local suicide prevention or emergency number",
            "es": "Línea local de prevención del suicidio o número de emergencias",
            "pt": "Linha local de prevenção ao suicídio ou número de emergência",
        },
        number="112 / 911",
        url="https://www.opencounseling.com/suicide-hotlines",
        notes={
            "en": "Call your local emergency number or look up a trusted hotline for your country.",
            "es": "Llama a tu número local de emergencias o busca una línea confiable en tu país.",
            "pt": "Ligue para o número local de emergência ou procure uma linha confiável no seu país.",
        },
    ),
}


def _normalize_region(region: Optional[str]) -> str:
    if not region:
        return "INTL"
    code = str(region).upper()
    return code if code in HOTLINES else "INTL"


def get_hotline_for_region(region: Optional[str], locale: str) -> Dict[str, Any]:
    hotline = HOTLINES.get(_normalize_region(region)) or HOTLINES["INTL"]
    return hotline.to_locale_dict(locale)


# =============================================================================
# Formatting helpers
# =============================================================================


def _format_emotion_row(
    emotion_id: str,
    detector_emotion: Dict[str, Any],
    mixture_value: float,
    locale: str,
) -> Dict[str, Any]:
    loc = _normalize_locale(locale)
    label_en = EMOTION_LABELS["en"].get(emotion_id, emotion_id)
    label_local = EMOTION_LABELS.get(loc, {}).get(emotion_id, label_en)
    percent = _safe_float(detector_emotion.get("percent"), mixture_value * 100.0)
    score = _safe_float(detector_emotion.get("score"), 0.0)
    emoji = detector_emotion.get("emoji", "😐")

    percent = _clamp(percent, 0.0, 100.0)
    score = max(score, 0.0)

    return {
        "id": emotion_id,
        "label": label_en,
        "labelLocalized": label_local,
        "emoji": emoji,
        "score": round(score, 4),
        "scoreDisplay": f"{score:.3f}",
        "percent": round(percent, 3),
        "percentDisplay": f"{percent:.1f}",
        "mixture": round(max(mixture_value, 0.0), 6),
    }


def _format_result_block(
    kind: str,
    detector_result: Dict[str, Any],
    locale: str,
) -> Dict[str, Any]:
    loc = _normalize_locale(locale)
    emotion_id = detector_result.get("label", "")
    label_en = EMOTION_LABELS["en"].get(emotion_id, emotion_id)
    label_local = EMOTION_LABELS.get(loc, {}).get(emotion_id, label_en)

    score = _safe_float(detector_result.get("score"), 0.0)
    percent = _safe_float(detector_result.get("percent"), 0.0)
    emoji = detector_result.get("emoji", "😐")

    percent = _clamp(percent, 0.0, 100.0)
    score = max(score, 0.0)

    if kind == "current":
        nuance = _pick_nuanced_labels(emotion_id, percent, loc)
    else:
        nuance = {"bucket": None, "nuanced_en": None, "nuanced_local": None}

    bucket = nuance["bucket"]
    nuanced_en = nuance["nuanced_en"] or label_en
    nuanced_local = nuance["nuanced_local"] or label_local

    return {
        "type": kind,
        "emotionId": emotion_id,
        "label": label_en,
        "labelLocalized": label_local,
        "emoji": emoji,
        "score": round(score, 4),
        "scoreDisplay": f"{score:.3f}",
        "percent": round(percent, 3),
        "percentDisplay": f"{percent:.1f}",
        "intensityBucket": bucket,
        "nuancedLabel": nuanced_en,
        "nuancedLabelLocalized": nuanced_local,
    }


def _fallback_raw(text: str, loc: str, reason: str) -> Dict[str, Any]:
    """
    Build a minimal raw detector-like structure so the client always renders.
    """
    emotions = {eid: {"label": eid, "emoji": "😐", "score": 0.0, "percent": 0.0} for eid in EMOTIONS}
    mixture_vector = {eid: 0.0 for eid in EMOTIONS}

    return {
        "text": text,
        "language": {"locale": loc, "confidence": 0.0},
        "emotions": emotions,
        "mixture_vector": mixture_vector,
        "dominant": {"label": "surprise", "emoji": "😐", "score": 0.0, "percent": 1.0},
        "current": {"label": "surprise", "emoji": "😐", "score": 0.0, "percent": 1.0},
        "arousal": 0.0,
        "sarcasm": 0.0,
        "confidence": 0.0,
        "risk_level": "none",
        "meta": {"fallback": True, "fallback_reason": reason},
    }


# =============================================================================
# Public API
# =============================================================================


def format_for_client(
    text: str,
    locale: str = "en",
    region: Optional[str] = None,
    domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High level function used by the backend or server.

    Always returns a JSON friendly dict matching client needs.
    Never raises for normal inputs.
    """
    loc = _normalize_locale(locale)

    try:
        raw = analyze_text(text, domain=domain)
        if not isinstance(raw, dict):
            raw = _fallback_raw(text, loc, "analyze_text returned non-dict")
    except InvalidTextError as e:
        raw = _fallback_raw(text, loc, f"InvalidTextError: {e}")
    except Exception as e:
        raw = _fallback_raw(text, loc, f"Exception: {e}")

    mixture_vector: Dict[str, float] = raw.get("mixture_vector", {}) or {}
    emotions_raw: Dict[str, Dict[str, Any]] = raw.get("emotions", {}) or {}

    emotion_order = list(EMOTIONS)

    mixture_rows: List[Dict[str, Any]] = []
    analysis_rows: List[Dict[str, Any]] = []

    for emotion_id in emotion_order:
        det_em = emotions_raw.get(emotion_id, {}) or {}
        mix_val = _safe_float(mixture_vector.get(emotion_id), 0.0)
        mix_val = max(mix_val, 0.0)

        row = _format_emotion_row(emotion_id, det_em, mix_val, loc)

        mixture_rows.append(
            {
                "id": row["id"],
                "label": row["label"],
                "labelLocalized": row["labelLocalized"],
                "emoji": row["emoji"],
                "percent": row["percent"],
                "percentDisplay": row["percentDisplay"],
            }
        )

        analysis_rows.append(
            {
                "id": row["id"],
                "label": row["label"],
                "labelLocalized": row["labelLocalized"],
                "emoji": row["emoji"],
                "score": row["score"],
                "scoreDisplay": row["scoreDisplay"],
                "mixture": row["mixture"],
            }
        )

    dominant_block = _format_result_block("dominant", raw.get("dominant", {}) or {}, loc)
    current_block = _format_result_block("current", raw.get("current", {}) or {}, loc)

    mixture_profile = _compute_mixture_profile(mixture_vector)
    meta = raw.get("meta", {}) or {}

    current_block = _apply_mixture_nuance_to_current(
        current_block, mixture_vector, loc, mixture_profile, meta
    )

    hotline = get_hotline_for_region(region, loc)

    payload: Dict[str, Any] = {
        "text": raw.get("text", text),
        "locale": loc,
        "languageGuess": raw.get("language", {}) or {},
        "emotionOrder": emotion_order,
        "coreMixture": mixture_rows,
        "analysis": analysis_rows,
        "results": {
            "dominant": dominant_block,
            "current": current_block,
        },
        "metrics": {
            "arousal": _safe_float(raw.get("arousal"), 0.0),
            "sarcasm": _safe_float(raw.get("sarcasm"), 0.0),
            "confidence": _safe_float(raw.get("confidence"), 0.0),
            "mixtureProfile": mixture_profile,
        },
        "risk": {
            "level": raw.get("risk_level", "none"),
            "hotline": hotline,
        },
        "meta": meta,
    }
    return payload


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    sample_text = " ".join(sys.argv[1:]) or "I am really happy but a bit anxious."
    result = format_for_client(sample_text, locale="en", region="US")
    print(json.dumps(result, ensure_ascii=False, indent=2))
