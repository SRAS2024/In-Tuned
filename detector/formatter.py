# detector/formatter.py
# Formatter for EmotionDetector output.
# Shapes detector results into a JSON friendly structure for the UI.

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    # Relative import when used as a package
    from .detector import analyze_text, EMOTIONS
except ImportError:  # pragma: no cover
    # Fallback for running this file directly
    from detector import analyze_text, EMOTIONS  # type: ignore


# =============================================================================
# Localization data
# =============================================================================


def _normalize_locale(locale: Optional[str]) -> str:
    if not locale:
        return "en"
    loc = locale.lower()
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
# Idea:
#   very_low  → faint trace of that emotion
#   low       → mild or background emotion
#   moderate  → clear and present emotion
#   high      → strong or intense
#   very_high → extreme, like rage, panic, devastation, euphoria
EMOTION_INTENSITY_LABELS: Dict[str, Dict[str, Dict[str, str]]] = {
    "en": {
        "anger": {
            "very_low": "Slightly annoyed",
            "low": "Frustrated",
            "moderate": "Angry",
            "high": "Very angry",
            "very_high": "Furious",
        },
        "sadness": {
            "very_low": "Slightly down",
            "low": "Down",
            "moderate": "Sad",
            "high": "Very sad",
            "very_high": "Devastated",
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
            "high": "Very loving",
            "very_high": "Deeply in love",
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
            "very_low": "Levemente desanimado",
            "low": "Desanimado",
            "moderate": "Triste",
            "high": "Muy triste",
            "very_high": "Devastado",
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
            "very_low": "Afecto leve",
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
            "very_low": "Levemente abatido",
            "low": "Abatido",
            "moderate": "Triste",
            "high": "Muito triste",
            "very_high": "Devastado",
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
            "very_low": "Afeto leve",
            "low": "Carinhoso",
            "moderate": "Amoroso",
            "high": "Muito amoroso",
            "very_high": "Profundamente apaixonado",
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

    Falls back to the base labels if there is no matching entry
    or if the intensity is effectively zero.
    """
    if not emotion_id or percent <= 0.01:
        return {
            "bucket": None,
            "nuanced_en": None,
            "nuanced_local": None,
        }

    loc = _normalize_locale(locale)
    bucket = _intensity_bucket_from_percent(percent)

    en_map = EMOTION_INTENSITY_LABELS.get("en", {}).get(emotion_id, {})
    loc_map = EMOTION_INTENSITY_LABELS.get(loc, {}).get(emotion_id, {})

    nuanced_en = en_map.get(bucket)
    nuanced_local = loc_map.get(bucket)

    if nuanced_en is None and nuanced_local is None:
        return {
            "bucket": None,
            "nuanced_en": None,
            "nuanced_local": None,
        }

    return {
        "bucket": bucket,
        "nuanced_en": nuanced_en,
        "nuanced_local": nuanced_local,
    }


def _get_intensity_phrase_for_lang(
    emotion_id: str,
    percent: float,
    lang: str,
) -> str:
    """
    Get a human label for a single emotion at a given percent,
    for a specific language.
    """
    bucket = _intensity_bucket_from_percent(percent)
    lang = _normalize_locale(lang)

    label_map = EMOTION_INTENSITY_LABELS.get(lang, {}).get(emotion_id, {})
    phrase = label_map.get(bucket)
    if phrase:
        return phrase

    # Fallback to base labels
    base = EMOTION_LABELS.get(lang, {}).get(emotion_id)
    if base:
        return base
    return EMOTION_LABELS["en"].get(emotion_id, emotion_id)


# Special pairwise mixture labels for some common combinations
# Keyed by language then (primary, secondary)
COMBO_SPECIAL_LABELS: Dict[str, Dict[Tuple[str, str], str]] = {
    "en": {
        ("sadness", "anger"): "Hurt and angry",
        ("anger", "sadness"): "Angry and hurt",
        ("sadness", "fear"): "Sad and worried",
        ("fear", "sadness"): "Worried and sad",
        ("joy", "sadness"): "Bittersweet, both happy and sad",
        ("sadness", "joy"): "Bittersweet, both sad and hopeful",
        ("joy", "surprise"): "Excited and pleasantly surprised",
        ("surprise", "joy"): "Pleasantly surprised and excited",
        ("joy", "passion"): "Warm, loving joy",
        ("passion", "joy"): "Deeply loving and joyful",
        ("fear", "disgust"): "Disturbed and uneasy",
        ("disgust", "fear"): "Repulsed and uneasy",
    },
    "es": {
        ("sadness", "anger"): "Dolido y enojado",
        ("anger", "sadness"): "Enojado y dolido",
        ("sadness", "fear"): "Triste y preocupado",
        ("fear", "sadness"): "Preocupado y triste",
        ("joy", "sadness"): "Agridulce, feliz y triste a la vez",
        ("sadness", "joy"): "Agridulce, triste pero con algo de esperanza",
        ("joy", "surprise"): "Emocionado y gratamente sorprendido",
        ("surprise", "joy"): "Gratamente sorprendido y emocionado",
        ("joy", "passion"): "Alegría cálida y amorosa",
        ("passion", "joy"): "Profundamente amoroso y alegre",
        ("fear", "disgust"): "Perturbado e inquieto",
        ("disgust", "fear"): "Repugnado e inquieto",
    },
    "pt": {
        ("sadness", "anger"): "Magoado e com raiva",
        ("anger", "sadness"): "Com raiva e magoado",
        ("sadness", "fear"): "Triste e preocupado",
        ("fear", "sadness"): "Preocupado e triste",
        ("joy", "sadness"): "Agridoce, feliz e triste ao mesmo tempo",
        ("sadness", "joy"): "Agridoce, triste mas com alguma esperança",
        ("joy", "surprise"): "Animado e agradavelmente surpreso",
        ("surprise", "joy"): "Agradavelmente surpreso e animado",
        ("joy", "passion"): "Alegria calorosa e amorosa",
        ("passion", "joy"): "Profundamente apaixonado e alegre",
        ("fear", "disgust"): "Perturbado e desconfortável",
        ("disgust", "fear"): "Com nojo e apreensivo",
    },
}


def _lookup_special_combo(
    primary: str,
    secondary: str,
    locale: str,
) -> Optional[str]:
    loc = _normalize_locale(locale)
    by_lang = COMBO_SPECIAL_LABELS.get(loc, {})
    phrase = by_lang.get((primary, secondary))
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

    # Base intensity phrases
    p_en = _get_intensity_phrase_for_lang(primary_id, p_percent, "en")
    s_en = _get_intensity_phrase_for_lang(secondary_id, s_percent, "en")

    p_loc = _get_intensity_phrase_for_lang(primary_id, p_percent, loc)
    s_loc = _get_intensity_phrase_for_lang(secondary_id, s_percent, loc)

    # Check for special pairwise meaning first
    special_en = _lookup_special_combo(primary_id, secondary_id, "en")
    special_loc = _lookup_special_combo(primary_id, secondary_id, loc)

    if special_en or special_loc:
        return special_en or p_en, special_loc or p_loc

    # Generic blend patterns based on weights
    def lower_first(s: str) -> str:
        if not s:
            return s
        return s[0].lower() + s[1:]

    if loc == "es":
        mostly_en = f"{p_en} with some {lower_first(s_en)}"
        mixed_en = f"Mixed {lower_first(p_en)} and {lower_first(s_en)}"

        mostly_loc = f"{p_loc} con algo de {lower_first(s_loc)}"
        mixed_loc = f"Mezcla de {lower_first(p_loc)} y {lower_first(s_loc)}"
    elif loc == "pt":
        mostly_en = f"{p_en} with some {lower_first(s_en)}"
        mixed_en = f"Mixed {lower_first(p_en)} and {lower_first(s_en)}"

        mostly_loc = f"{p_loc} com um pouco de {lower_first(s_loc)}"
        mixed_loc = f"Mistura de {lower_first(p_loc)} e {lower_first(s_loc)}"
    else:
        mostly_en = f"{p_en} with some {lower_first(s_en)}"
        mixed_en = f"Mixed {lower_first(p_en)} and {lower_first(s_en)}"
        mostly_loc = mostly_en
        mixed_loc = mixed_en

    # Decide which pattern to use
    if primary_weight >= 0.6 and secondary_weight >= 0.2:
        return mostly_en, mostly_loc
    if primary_weight >= 0.45 and secondary_weight >= 0.3:
        return mixed_en, mixed_loc

    # If we got here, just keep the primary intensity phrase
    return p_en, p_loc


def _apply_mixture_nuance_to_current(
    block: Dict[str, Any],
    mixture_vector: Dict[str, float],
    locale: str,
) -> Dict[str, Any]:
    """
    Take the current result block and refine its nuanced labels by looking
    at the mixture of all seven emotions. This keeps the primary emotion
    but adjusts wording when there is a strong secondary emotion.
    """
    if not block:
        return block
    if not mixture_vector:
        return block

    primary_id = block.get("emotionId")
    if not primary_id:
        return block

    # Sort mixture from strongest to weakest
    items = sorted(
        mixture_vector.items(), key=lambda kv: float(kv[1]), reverse=True
    )
    if not items:
        return block

    # Find weight for the primary emotion
    primary_weight: Optional[float] = None
    for eid, w in items:
        if eid == primary_id:
            primary_weight = float(w)
            break

    if primary_weight is None:
        primary_id, primary_weight = items[0]

    # Find strongest secondary emotion above a minimum threshold
    secondary_id: Optional[str] = None
    secondary_weight: float = 0.0
    for eid, w in items:
        if eid == primary_id:
            continue
        w_val = float(w)
        if w_val > secondary_weight:
            secondary_id = eid
            secondary_weight = w_val

    # If there is no meaningful secondary emotion, keep the base nuance
    if secondary_id is None or secondary_weight < 0.15:
        return block

    combo_en, combo_loc = _build_combo_phrases(
        primary_id, primary_weight, secondary_id, secondary_weight, locale
    )

    if combo_en:
        block["nuancedLabel"] = combo_en
    if combo_loc:
        block["nuancedLabelLocalized"] = combo_loc

    # Expose a little more detail for the UI if needed
    block["primaryEmotionId"] = primary_id
    block["primaryEmotionWeight"] = round(primary_weight, 6)
    block["secondaryEmotionId"] = secondary_id
    block["secondaryEmotionWeight"] = round(secondary_weight, 6)

    return block


# =============================================================================
# Hotline data
# =============================================================================


@dataclass
class HotlineInfo:
    region_code: str        # ISO country code or "INTL"
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
    # United States
    "US": HotlineInfo(
        region_code="US",
        region_name={
            "en": "United States",
            "es": "Estados Unidos",
            "pt": "Estados Unidos",
        },
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
    # Canada
    "CA": HotlineInfo(
        region_code="CA",
        region_name={
            "en": "Canada",
            "es": "Canadá",
            "pt": "Canadá",
        },
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
    # Brazil
    "BR": HotlineInfo(
        region_code="BR",
        region_name={
            "en": "Brazil",
            "es": "Brasil",
            "pt": "Brasil",
        },
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
    # Portugal
    "PT": HotlineInfo(
        region_code="PT",
        region_name={
            "en": "Portugal",
            "es": "Portugal",
            "pt": "Portugal",
        },
        label={
            "en": "SOS Voz Amiga",
            "es": "SOS Voz Amiga",
            "pt": "SOS Voz Amiga",
        },
        number="+351 213 544 545",
        url="https://www.sosvozamiga.org",
        notes={
            "en": "Several numbers and schedules; check the website for details.",
            "es": "Hay varios números y horarios; consulta el sitio web para más detalles.",
            "pt": "Existem vários números e horários; veja o site para detalhes.",
        },
    ),
    # Spain
    "ES": HotlineInfo(
        region_code="ES",
        region_name={
            "en": "Spain",
            "es": "España",
            "pt": "Espanha",
        },
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
    # Mexico
    "MX": HotlineInfo(
        region_code="MX",
        region_name={
            "en": "Mexico",
            "es": "México",
            "pt": "México",
        },
        label={
            "en": "Línea de la Vida",
            "es": "Línea de la Vida",
            "pt": "Línea de la Vida",
        },
        number="800 911 2000",
        url=None,
        notes={
            "en": "Free national helpline for emotional support and crisis.",
            "es": "Línea nacional gratuita para apoyo emocional y crisis.",
            "pt": "Linha nacional gratuita para apoio emocional e crises.",
        },
    ),
    # Fallback international guidance
    "INTL": HotlineInfo(
        region_code="INTL",
        region_name={
            "en": "Your region",
            "es": "Tu región",
            "pt": "Sua região",
        },
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
    code = region.upper()
    if code in HOTLINES:
        return code
    return "INTL"


def get_hotline_for_region(region: Optional[str], locale: str) -> Dict[str, Any]:
    code = _normalize_region(region)
    hotline = HOTLINES.get(code) or HOTLINES["INTL"]
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
    """Format a single emotion row for both analysis and mixture tables."""
    loc = _normalize_locale(locale)
    label_en = EMOTION_LABELS["en"][emotion_id]
    label_local = EMOTION_LABELS[loc][emotion_id]
    percent = float(detector_emotion.get("percent", mixture_value * 100.0))
    score = float(detector_emotion.get("score", 0.0))
    emoji = detector_emotion.get("emoji", "😐")

    return {
        "id": emotion_id,
        "label": label_en,
        "labelLocalized": label_local,
        "emoji": emoji,
        "score": round(score, 4),
        "scoreDisplay": f"{score:.3f}",
        "percent": round(percent, 3),
        "percentDisplay": f"{percent:.1f}",
        "mixture": round(mixture_value, 6),
    }


def _format_result_block(
    kind: str,
    detector_result: Dict[str, Any],
    locale: str,
) -> Dict[str, Any]:
    """
    Format dominant or current result, with intensity aware nuanced labels.

    Dominant uses only the core emotion label so it always matches
    one of the seven base emotions. Current emotion can use nuanced wording.
    """
    loc = _normalize_locale(locale)
    emotion_id = detector_result.get("label", "")
    label_en = EMOTION_LABELS["en"].get(emotion_id, emotion_id)
    label_local = EMOTION_LABELS[loc].get(emotion_id, label_en)
    score = float(detector_result.get("score", 0.0))
    percent = float(detector_result.get("percent", 0.0))
    emoji = detector_result.get("emoji", "😐")

    if kind == "current":
        nuance = _pick_nuanced_labels(emotion_id, percent, loc)
    else:
        nuance = {
            "bucket": None,
            "nuanced_en": None,
            "nuanced_local": None,
        }

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


def _compute_mixture_profile(
    mixture_vector: Dict[str, float]
) -> Dict[str, Any]:
    """
    Compute some extra metrics that describe how mixed the emotions are:
    - dominantStrength: normalized weight of strongest emotion
    - secondaryStrength: normalized weight of second emotion
    - entropy: information entropy of the mixture
    - mixtureType: simple qualitative description
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

    # Simple qualitative description
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

    It runs the emotion detector and returns a JSON friendly dict
    that matches what the front end needs:
      - ordered lists for mixture bars and analysis rows
      - localized labels for EN, ES, PT
      - dominant and current emotion blocks with emojis and nuanced labels
      - hotline information based on region
      - mixture profile metrics
    """
    loc = _normalize_locale(locale)
    raw = analyze_text(text, domain=domain)

    mixture_vector: Dict[str, float] = raw.get("mixture_vector", {}) or {}
    emotions_raw: Dict[str, Dict[str, Any]] = raw.get("emotions", {}) or {}

    # Keep a stable order for the UI
    emotion_order = list(EMOTIONS)

    mixture_rows: List[Dict[str, Any]] = []
    analysis_rows: List[Dict[str, Any]] = []

    for emotion_id in emotion_order:
        det_em = emotions_raw.get(emotion_id, {})
        mix_val = float(mixture_vector.get(emotion_id, 0.0))
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

    dominant_block = _format_result_block(
        "dominant", raw.get("dominant", {}), loc
    )

    current_raw = raw.get("current", {})
    current_block = _format_result_block(
        "current", current_raw, loc
    )
    # Refine the current block with mixture aware nuance
    current_block = _apply_mixture_nuance_to_current(
        current_block, mixture_vector, loc
    )

    hotline = get_hotline_for_region(region, loc)

    mixture_profile = _compute_mixture_profile(mixture_vector)

    payload: Dict[str, Any] = {
        "text": raw.get("text", text),
        "locale": loc,
        "languageGuess": raw.get("language", {}),
        "emotionOrder": emotion_order,
        "coreMixture": mixture_rows,
        "analysis": analysis_rows,
        "results": {
            "dominant": dominant_block,
            "current": current_block,
        },
        "metrics": {
            "arousal": raw.get("arousal", 0.0),
            "sarcasm": raw.get("sarcasm", 0.0),
            "confidence": raw.get("confidence", 0.0),
            "mixtureProfile": mixture_profile,
        },
        "risk": {
            "level": raw.get("risk_level", "none"),
            "hotline": hotline,
        },
        "meta": raw.get("meta", {}),
    }
    return payload


# Small CLI helper for quick manual testing
if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    sample_text = " ".join(sys.argv[1:]) or "I am really happy but a bit anxious."
    result = format_for_client(sample_text, locale="en", region="US")
    print(json.dumps(result, ensure_ascii=False, indent=2))
