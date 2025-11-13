import os
import json
import pytest
from server import app

# Force local fallback in tests
os.environ.pop("WATSON_NLU_APIKEY", None)
os.environ.pop("WATSON_NLU_URL", None)


def test_post_emotion_detector_ok():
    client = app.test_client()
    resp = client.post(
        "/emotionDetector",
        data=json.dumps(
            {
                "text": "I am thrilled, a bit anxious, and honestly surprised!"
            }
        ),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()

    # Core scores present
    for key in [
        "anger",
        "disgust",
        "fear",
        "joy",
        "sadness",
        "passion",
        "surprise",
        "dominant_emotion",
        "blended_emotion",
        "emotion",
        "confidence",
        "mixture",
        "components",
        "emoji",
        "emoji_emotion",
        "emoji_dominant",
        "emoji_primary",
        "present",
        "rationale",
        "low_signal",
        "same_label",
    ]:
        assert key in data, f"missing key: {key}"

    # Ranges and shapes for core scores
    for k in ["anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"]:
        v = float(data[k])
        assert 0.0 <= v <= 1.0

    assert isinstance(data["dominant_emotion"], str)
    assert isinstance(data["blended_emotion"], str)
    assert isinstance(data["emotion"], str)
    assert 0.0 <= float(data["confidence"]) <= 1.0
    assert data["low_signal"] is False

    # Mixture for charting
    mix = data["mixture"]
    assert isinstance(mix, dict)
    for k in ["anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"]:
        assert k in mix
        mv = float(mix[k])
        assert 0.0 <= mv <= 1.0
    # Mixture should have some nonzero mass for a rich sentence
    assert any(float(mix[k]) > 0.0 for k in mix)

    # Components are now a list of dicts with name and weight
    comps = data["components"]
    assert isinstance(comps, list)
    assert len(comps) >= 1
    assert isinstance(comps[0], dict)
    assert "name" in comps[0] and "weight" in comps[0]

    # Emoji fields
    emoji = data["emoji"]
    assert isinstance(emoji, list)
    assert len(emoji) >= 1
    assert all(isinstance(e, str) for e in emoji)

    emoji_emotion = data["emoji_emotion"]
    emoji_dominant = data["emoji_dominant"]
    assert isinstance(emoji_emotion, list)
    assert isinstance(emoji_dominant, list)
    assert len(emoji_emotion) >= 1
    assert len(emoji_dominant) >= 1
    assert isinstance(data["emoji_primary"], str)


def test_post_emotion_detector_low_signal_ok():
    """Inputs with almost no content should still return 200 with low_signal True."""
    client = app.test_client()
    resp = client.post(
        "/emotionDetector",
        data=json.dumps({"text": "am"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["low_signal"] is True
    # All core scores should be exactly zero in the low signal case
    for k in ["anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"]:
        assert float(data[k]) == 0.0

    assert data["emotion"] == "N/A"
    assert data["dominant_emotion"] == "N/A"
    assert data["emoji_primary"] == "❌"


def test_post_emotion_detector_bad_request():
    client = app.test_client()
    resp = client.post(
        "/emotionDetector",
        data=json.dumps({"text": "   "}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data
