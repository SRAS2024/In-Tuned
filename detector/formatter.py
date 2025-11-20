# detector/formatter.py
# Formatter for EmotionDetector output.
# Shapes detector results into a JSON friendly structure for the UI.

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

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
            "low": "Nervous",
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
            "very_low": "Mild discomfort",
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
            "low": "Molesto",
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
            "low": "Nervioso",
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
            "very_low": "Ligeramente incómodo",
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
            "low": "Incomodado",
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
            "low": "Nervoso",
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
    """Format dominant/current result, with intensity aware nuanced labels."""
    loc = _normalize_locale(locale)
    emotion_id = detector_result.get("label", "")
    label_en = EMOTION_LABELS["en"].get(emotion_id, emotion_id)
    label_local = EMOTION_LABELS[loc].get(emotion_id, label_en)
    score = float(detector_result.get("score", 0.0))
    percent = float(detector_result.get("percent", 0.0))
    emoji = detector_result.get("emoji", "😐")

    nuance = _pick_nuanced_labels(emotion_id, percent, loc)
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
    """
    loc = _normalize_locale(locale)
    raw = analyze_text(text, domain=domain)

    mixture_vector: Dict[str, float] = raw.get("mixture_vector", {})
    emotions_raw: Dict[str, Dict[str, Any]] = raw.get("emotions", {})

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
    current_block = _format_result_block(
        "current", raw.get("current", {}), loc
    )

    hotline = get_hotline_for_region(region, loc)

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
