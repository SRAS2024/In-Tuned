# main.py
# Thin adapter so Gunicorn / Railway can import `main:app`.

from __future__ import annotations

import os

from server import app  # reuse the Flask app defined in server.py


if __name__ == "__main__":
    # This path is only used if you run `python main.py` yourself.
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
