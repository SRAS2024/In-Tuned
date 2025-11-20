# server.py
# In tuned backend server
# Serves the client app and exposes /api/analyze for emotion detection.

from __future__ import annotations

import os
from flask import Flask, request, jsonify

from detector.formatter import format_for_client
from detector.detector import InvalidTextError

# Create Flask app
app = Flask(__name__, static_folder="client", static_url_path="")


# ---------- Static client ----------

@app.route("/")
def index() -> object:
    """Serve the main app shell."""
    return app.send_static_file("index.html")


# ---------- Emotion analysis API ----------

@app.route("/api/analyze", methods=["POST"])
def api_analyze() -> object:
    """
    Analyze emotional tone of text.

    Expected JSON body:
        {
          "text": "...",
          "locale": "en" | "es" | "pt",
          "region": "US" | "BR" | ...,
          "session_id": "uuid",
          "token": "5000"
        }
    """
    data = request.get_json(silent=True) or {}

    text = data.get("text", "")
    locale = data.get("locale") or "en"
    region = data.get("region")
    token_body = data.get("token")
    token_header = request.headers.get("X-App-Token")
    token = token_body or token_header

    # Simple token gate
    if token and str(token) != "5000":
        return jsonify({"error": "Invalid token"}), 403

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Text is required"}), 400

    try:
        payload = format_for_client(
            text=text,
            locale=locale,
            region=region,
            domain="web",
        )
    except InvalidTextError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        # Do not leak internals to the client
        return jsonify({"error": "Internal server error"}), 500

    return jsonify(payload)


# ---------- Entry point ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
