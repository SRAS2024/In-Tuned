# server.py
# In tuned backend server
# Serves the client app and exposes APIs for emotion detection,
# accounts, journals, admin controls, and lexicon management.

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import psycopg
from psycopg import Binary
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from flask import Flask, request, jsonify, session

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from detector.formatter import format_for_client
from detector.detector import InvalidTextError, LEXICON_TOKEN, set_lexicon_token
from detector.external_lexicon import (
    lookup_word,
    expand_lexicon_from_external,
    get_expansion_stats,
    fetch_and_extract_word,
    SLANG_WORDS_TO_FETCH,
    VOCABULARY_WORDS_EN,
    VOCABULARY_WORDS_ES,
    VOCABULARY_WORDS_PT,
)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_text(text, max_words=250, field_name="text"):
    if not isinstance(text, str):
        raise ValueError(f"{field_name} must be a string")

    text = text.strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty")

    word_count = len(text.split())
    if word_count > max_words:
        raise ValueError(f"{field_name} exceeds maximum of {max_words} words")

    return text


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Admin credentials – read from environment variables only; no hardcoded defaults
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
DEV_PASSWORD = os.environ.get("DEV_PASSWORD", "")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    print("WARNING: ADMIN_USERNAME and/or ADMIN_PASSWORD environment variables are not set. Admin login will be denied.")

# Database URL (set this in Railway as an env var, typically using
# the Postgres.DATABASE_URL value)
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///intuned_dev.db"
    print("WARNING: DATABASE_URL not set. Using SQLite for development.")

# Create Flask app
app = Flask(__name__, static_folder="client", static_url_path="")

# Secret key for signed sessions
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# Session configuration
from datetime import timedelta

app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_REFRESH_EACH_REQUEST=True
)

# CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-App-Token'
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-App-Token")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        return response

# Request ID tracking
import uuid
from flask import g

@app.before_request
def add_request_id():
    g.request_id = str(uuid.uuid4())

@app.after_request
def add_request_id_header(response):
    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    return response


# ---------------------------------------------------------------------------
# Database helpers and schema
# ---------------------------------------------------------------------------


from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)
        yield conn
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                app.logger.error(f"Error closing connection: {e}")

def get_db() -> psycopg.Connection:
    """
    Open a new database connection.

    For this app we keep it simple and open a connection per request.
    Railway Postgres can handle this level of traffic.
    """
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)
    return conn


def init_db() -> None:
  """Create tables if they do not exist."""
  conn = get_db()
  cur = conn.cursor()

  # Users table
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      first_name TEXT NOT NULL,
      last_name TEXT NOT NULL,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      preferred_language TEXT DEFAULT 'en',
      preferred_theme TEXT DEFAULT 'dark',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
  )

  # Journals table
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS journals (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title TEXT NOT NULL,
      source_text TEXT,
      analysis_json JSONB,
      journal_text TEXT,
      is_pinned BOOLEAN DEFAULT FALSE,
      has_self_harm_flag BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
  )

  # Notices table (for optional notice banner on main site)
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS notices (
      id SERIAL PRIMARY KEY,
      text TEXT NOT NULL,
      is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
  )

  # Site settings table (single row)
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS site_settings (
      id INTEGER PRIMARY KEY,
      maintenance_mode BOOLEAN NOT NULL DEFAULT FALSE,
      maintenance_message TEXT
    );
    """
  )

  # Ensure there is exactly one settings row with id 1
  cur.execute(
    """
    INSERT INTO site_settings (id, maintenance_mode, maintenance_message)
    VALUES (1, FALSE, NULL)
    ON CONFLICT (id) DO NOTHING;
    """
  )

  # Lexicon files table (for uploaded dictionaries)
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS lexicon_files (
      id SERIAL PRIMARY KEY,
      language TEXT NOT NULL,
      filename TEXT NOT NULL,
      content_type TEXT,
      data BYTEA,
      uploaded_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
  )

  # Feedback table (for anonymous user feedback on analysis accuracy)
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS feedback (
      id SERIAL PRIMARY KEY,
      entry_text TEXT NOT NULL,
      analysis_json JSONB,
      feedback_text TEXT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
  )

  conn.commit()
  cur.close()
  conn.close()


# Initialize schema when module is imported
try:
    init_db()
except Exception as _init_err:
    print(f"WARNING: init_db() failed at startup: {_init_err}")
    print("Tables will be created on the first successful database connection.")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def current_user_id() -> Optional[int]:
  """Return the logged in user id from the session, or None."""
  uid = session.get("user_id")
  if isinstance(uid, int):
    return uid
  return None


def require_login() -> Optional[Any]:
  """Return an error response if the user is not logged in."""
  uid = current_user_id()
  if uid is None:
    return jsonify({"error": "Authentication required"}), 401
  return None


def is_admin() -> bool:
  """Check if the current session has admin privileges."""
  return bool(session.get("is_admin"))


def require_admin():
  if not is_admin():
    return jsonify({"error": "Admin authorization required"}), 401
  return None


SELF_HARM_KEYWORDS = [
  "suicide",
  "kill myself",
  "end my life",
  "hurt myself",
  "self harm",
  "cut myself",
  "não aguento mais",
  "nao aguento mais",
  "tirar minha vida",
  "tirar a minha vida",
  "me matar",
  "quitarme la vida",
  "hacerme daño",
]


def detect_self_harm_flag(text: str) -> bool:
  """Very simple keyword based self harm detector.

  This will later be replaced or enriched by lexicon driven detector logic.
  """
  if not text:
    return False
  lowered = text.lower()
  for phrase in SELF_HARM_KEYWORDS:
    if phrase in lowered:
      return True
  return False


def user_to_payload(row: Dict[str, Any]) -> Dict[str, Any]:
  """Select safe user fields to send to the client."""
  return {
    "id": row["id"],
    "first_name": row["first_name"],
    "last_name": row["last_name"],
    "username": row["username"],
    "email": row["email"],
    "preferred_language": row.get("preferred_language") or "en",
    "preferred_theme": row.get("preferred_theme") or "dark",
  }


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


def error_response(message, status_code=400):
    return jsonify({
        "ok": False,
        "error": {
            "message": message,
            "code": status_code
        }
    }), status_code

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return error_response("Endpoint not found", 404)
    # If the path looks like a static file (has a file extension),
    # return a real 404 so verification files, missing assets, etc.
    # are not silently replaced by the SPA shell.
    _, ext = os.path.splitext(request.path)
    if ext:
        return error_response("File not found", 404)
    return app.send_static_file("index.html")

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal error: {error}")
    return error_response("Internal server error", 500)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return error_response("An unexpected error occurred", 500)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------


@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        db_status = "connected"
        status = "healthy"
        status_code = 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        db_status = "disconnected"
        status = "unhealthy"
        status_code = 503

    return jsonify({
        "status": status,
        "database": db_status,
        "version": "2.0.0"
    }), status_code


# ---------------------------------------------------------------------------
# Static client
# ---------------------------------------------------------------------------


@app.route("/")
def index() -> object:
  """Serve the main app shell."""
  return app.send_static_file("index.html")


@app.route("/admin")
def admin_index() -> object:
  """Serve the administrative portal shell."""
  return app.send_static_file("admin.html")


# ---------------------------------------------------------------------------
# Emotion analysis API
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Public site state API (maintenance banner and notice)
# ---------------------------------------------------------------------------


@app.route("/api/site-state", methods=["GET"])
def api_site_state() -> object:
  """
  Public endpoint for the client to know whether the site is in maintenance
  mode and what message or notice should be shown.
  """
  conn = get_db()
  cur = conn.cursor()

  cur.execute("SELECT maintenance_mode, maintenance_message FROM site_settings WHERE id = 1;")
  row = cur.fetchone()
  maintenance_mode = bool(row["maintenance_mode"]) if row else False
  maintenance_message = row["maintenance_message"] if row else None

  cur.execute(
    """
    SELECT id, text
    FROM notices
    WHERE is_active = TRUE
    ORDER BY created_at DESC
    LIMIT 1;
    """
  )
  notice = cur.fetchone()

  cur.close()
  conn.close()

  return jsonify(
    {
      "maintenance_mode": maintenance_mode,
      "maintenance_message": maintenance_message,
      "notice": notice,
    }
  )


# ---------------------------------------------------------------------------
# Admin authentication and controls
# ---------------------------------------------------------------------------


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login() -> object:
  """Authenticate admin for the admin portal."""
  data = request.get_json(silent=True) or {}
  username = data.get("username") or ""
  password = data.get("password") or ""

  if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    print("WARNING: Admin login attempt but ADMIN_USERNAME/ADMIN_PASSWORD environment variables are not set.")
    return jsonify({"ok": False, "error": "Admin authentication not configured"}), 500

  if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
    session["is_admin"] = True
    return jsonify({"ok": True, "message": "Welcome, Admin!"})
  session["is_admin"] = False
  return jsonify({"ok": False, "error": "Not authorized"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout() -> object:
  session.pop("is_admin", None)
  return jsonify({"ok": True})


@app.route("/api/admin/site-state", methods=["GET"])
def api_admin_site_state() -> object:
  """Admin view of site settings and latest notice."""
  guard = require_admin()
  if guard is not None:
    return guard

  conn = get_db()
  cur = conn.cursor()

  cur.execute("SELECT maintenance_mode, maintenance_message FROM site_settings WHERE id = 1;")
  settings = cur.fetchone()

  cur.execute(
    """
    SELECT id, text, is_active, created_at
    FROM notices
    ORDER BY created_at DESC
    LIMIT 10;
    """
  )
  notices = cur.fetchall()

  cur.close()
  conn.close()

  return jsonify({"settings": settings, "notices": notices})


@app.route("/api/admin/maintenance", methods=["POST"])
def api_admin_maintenance() -> object:
  """
  Toggle maintenance mode.

  When enabling maintenance, the developer password must be supplied.
  Disabling does not require the developer password.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  enabled = bool(data.get("enabled"))
  message = data.get("message") or "Site is currently down due to maintenance. We will be back shortly."
  dev_password = data.get("dev_password")

  if enabled and dev_password != DEV_PASSWORD:
    return jsonify({"error": "Developer password required"}), 403

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    UPDATE site_settings
    SET maintenance_mode = %s,
        maintenance_message = %s
    WHERE id = 1;
    """,
    (enabled, message),
  )
  conn.commit()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "maintenance_mode": enabled, "maintenance_message": message})


@app.route("/api/admin/notices", methods=["POST"])
def api_admin_create_notice() -> object:
  """
  Create a new notice to appear below the logo on the main site.

  The client can choose to deactivate older notices or keep them stored.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  text = (data.get("text") or "").strip()
  make_active = bool(data.get("is_active", True))

  if not text:
    return jsonify({"error": "Notice text is required"}), 400

  conn = get_db()
  cur = conn.cursor()

  if make_active:
    # Deactivate all previous notices
    cur.execute("UPDATE notices SET is_active = FALSE WHERE is_active = TRUE;")

  cur.execute(
    "INSERT INTO notices (text, is_active) VALUES (%s, %s) RETURNING id, text, is_active, created_at;",
    (text, make_active),
  )
  notice = cur.fetchone()

  conn.commit()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "notice": notice})


@app.route("/api/admin/notices/<int:notice_id>", methods=["PATCH"])
def api_admin_update_notice(notice_id: int) -> object:
  """Update the active flag for a notice."""
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  is_active = data.get("is_active")
  if is_active is None:
    return jsonify({"error": "is_active field is required"}), 400

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    "UPDATE notices SET is_active = %s WHERE id = %s RETURNING id, text, is_active, created_at;",
    (bool(is_active), notice_id),
  )
  notice = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  if not notice:
    return jsonify({"error": "Notice not found"}), 404

  return jsonify({"ok": True, "notice": notice})


# ---------------------------------------------------------------------------
# Lexicon management APIs (admin)
# ---------------------------------------------------------------------------


@app.route("/api/admin/lexicons", methods=["GET"])
def api_admin_list_lexicons() -> object:
  guard = require_admin()
  if guard is not None:
    return guard

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    SELECT id, language, filename, content_type, uploaded_at
    FROM lexicon_files
    ORDER BY uploaded_at DESC;
    """
  )
  files = cur.fetchall()
  cur.close()
  conn.close()

  return jsonify({"files": files})


@app.route("/api/admin/lexicons/upload", methods=["POST"])
def api_admin_upload_lexicon() -> object:
  """
  Upload a new dictionary file (pdf or other structured file) for a language.

  Expected multipart form data:
    - language: "en", "es", or "pt"
    - file: the uploaded file
  """
  guard = require_admin()
  if guard is not None:
    return guard

  language = request.form.get("language", "").strip().lower()
  if language not in {"en", "es", "pt"}:
    return jsonify({"error": "language must be one of 'en', 'es', 'pt'"}), 400

  uploaded = request.files.get("file")
  if not uploaded:
    return jsonify({"error": "file is required"}), 400

  filename = secure_filename(uploaded.filename or "lexicon.dat")
  content_type = uploaded.mimetype or "application/octet-stream"
  data_bytes = uploaded.read()

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    INSERT INTO lexicon_files (language, filename, content_type, data)
    VALUES (%s, %s, %s, %s)
    RETURNING id, language, filename, content_type, uploaded_at;
    """,
    (language, filename, content_type, Binary(data_bytes)),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "file": row})


@app.route("/api/admin/lexicons/<int:file_id>", methods=["DELETE"])
def api_admin_delete_lexicon(file_id: int) -> object:
  guard = require_admin()
  if guard is not None:
    return guard

  conn = get_db()
  cur = conn.cursor()
  cur.execute("DELETE FROM lexicon_files WHERE id = %s RETURNING id;", (file_id,))
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  if not row:
    return jsonify({"error": "Lexicon file not found"}), 404

  return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# External lexicon expansion APIs (admin)
# ---------------------------------------------------------------------------


@app.route("/api/admin/lexicons/lookup", methods=["POST"])
def api_admin_lookup_word() -> object:
  """
  Look up a single word from external dictionary sources.

  Expected JSON body:
    - word: string (required)
    - language: "en", "es", or "pt" (default: "en")

  Returns definitions, examples, and extracted emotion weights.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  word = (data.get("word") or "").strip().lower()
  language = (data.get("language") or "en").strip().lower()

  if not word:
    return jsonify({"error": "word is required"}), 400

  if language not in {"en", "es", "pt"}:
    return jsonify({"error": "language must be one of 'en', 'es', 'pt'"}), 400

  try:
    result = lookup_word(word, language)
    return jsonify({"ok": True, "result": result})
  except Exception as e:
    return jsonify({"error": f"Lookup failed: {str(e)}"}), 500


@app.route("/api/admin/lexicons/expand", methods=["POST"])
def api_admin_expand_lexicon() -> object:
  """
  Expand the emotion lexicon by fetching words from external sources.

  Expected JSON body:
    - languages: list of language codes ["en", "es", "pt"] (default: all)
    - include_slang: boolean (default: true) - fetch from Urban Dictionary
    - include_vocabulary: boolean (default: true) - fetch vocabulary words
    - apply_immediately: boolean (default: true) - apply to detector immediately

  This fetches definitions from:
    - Urban Dictionary (English slang)
    - Free Dictionary API (English, Spanish, Portuguese)

  And extracts emotion weights from definitions to expand the lexicon.

  Note: This operation can take several minutes due to API rate limiting.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  languages = data.get("languages", ["en", "es", "pt"])
  include_slang = data.get("include_slang", True)
  include_vocabulary = data.get("include_vocabulary", True)
  apply_immediately = data.get("apply_immediately", True)

  # Validate languages
  valid_langs = {"en", "es", "pt"}
  languages = [l for l in languages if l in valid_langs]
  if not languages:
    return jsonify({"error": "At least one valid language is required"}), 400

  try:
    # Get current lexicon
    original_lexicon = dict(LEXICON_TOKEN)

    # Expand with external sources
    expanded_lexicon = expand_lexicon_from_external(
      original_lexicon,
      languages=languages,
      include_slang=include_slang,
      include_vocabulary=include_vocabulary
    )

    # Get expansion statistics
    stats = get_expansion_stats(original_lexicon, expanded_lexicon)

    # Apply to detector if requested
    if apply_immediately:
      set_lexicon_token(expanded_lexicon, expand_morphology=True)

    return jsonify({
      "ok": True,
      "stats": stats,
      "applied": apply_immediately,
      "message": f"Added {stats['total_new']} new words across {len(languages)} language(s)"
    })

  except Exception as e:
    return jsonify({"error": f"Expansion failed: {str(e)}"}), 500


@app.route("/api/admin/lexicons/stats", methods=["GET"])
def api_admin_lexicon_stats() -> object:
  """
  Get statistics about the current emotion lexicon.

  Returns word counts per language and available expansion options.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  stats = {
    "current_lexicon": {},
    "expansion_available": {
      "slang_words": len(SLANG_WORDS_TO_FETCH),
      "vocabulary_en": len(VOCABULARY_WORDS_EN),
      "vocabulary_es": len(VOCABULARY_WORDS_ES),
      "vocabulary_pt": len(VOCABULARY_WORDS_PT),
    },
    "total_current": 0,
    "total_expansion_available": 0
  }

  for lang, words in LEXICON_TOKEN.items():
    count = len(words)
    stats["current_lexicon"][lang] = count
    stats["total_current"] += count

  stats["total_expansion_available"] = (
    stats["expansion_available"]["slang_words"] +
    stats["expansion_available"]["vocabulary_en"] +
    stats["expansion_available"]["vocabulary_es"] +
    stats["expansion_available"]["vocabulary_pt"]
  )

  return jsonify({"ok": True, "stats": stats})


@app.route("/api/admin/lexicons/add-word", methods=["POST"])
def api_admin_add_word_to_lexicon() -> object:
  """
  Add a single word to the lexicon by fetching from external sources.

  Expected JSON body:
    - word: string (required)
    - language: "en", "es", or "pt" (default: "en")
    - include_slang: boolean (default: true for English)

  Returns the extracted emotion weights and adds to the active lexicon.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  word = (data.get("word") or "").strip().lower()
  language = (data.get("language") or "en").strip().lower()
  include_slang = data.get("include_slang", language == "en")

  if not word:
    return jsonify({"error": "word is required"}), 400

  if language not in {"en", "es", "pt"}:
    return jsonify({"error": "language must be one of 'en', 'es', 'pt'"}), 400

  try:
    # Fetch and extract emotion weights
    weights = fetch_and_extract_word(word, language, include_slang)

    if not weights:
      return jsonify({
        "ok": False,
        "error": "No emotion associations found for this word",
        "word": word,
        "language": language
      }), 404

    # Merge weights into a single emotion vector
    merged_emotions: Dict[str, float] = {}
    for w in weights:
      for emotion, score in w.emotions.items():
        if emotion not in merged_emotions:
          merged_emotions[emotion] = 0.0
        merged_emotions[emotion] = max(merged_emotions[emotion], score)

    # Add to lexicon
    if language not in LEXICON_TOKEN:
      LEXICON_TOKEN[language] = {}

    LEXICON_TOKEN[language][word] = merged_emotions

    # Rebuild detector indices
    set_lexicon_token(LEXICON_TOKEN, expand_morphology=True)

    return jsonify({
      "ok": True,
      "word": word,
      "language": language,
      "emotions": merged_emotions,
      "sources": list(set(w.source for w in weights))
    })

  except Exception as e:
    return jsonify({"error": f"Failed to add word: {str(e)}"}), 500


@app.route("/api/admin/lexicons/add-custom", methods=["POST"])
def api_admin_add_custom_word() -> object:
  """
  Add a word with custom emotion weights (no external lookup).

  Expected JSON body:
    - word: string (required)
    - language: "en", "es", or "pt" (default: "en")
    - emotions: dict of {emotion: weight} (required)

  Example:
    {
      "word": "yeet",
      "language": "en",
      "emotions": {"joy": 1.5, "surprise": 2.0}
    }
  """
  guard = require_admin()
  if guard is not None:
    return guard

  data = request.get_json(silent=True) or {}
  word = (data.get("word") or "").strip().lower()
  language = (data.get("language") or "en").strip().lower()
  emotions = data.get("emotions", {})

  if not word:
    return jsonify({"error": "word is required"}), 400

  if language not in {"en", "es", "pt"}:
    return jsonify({"error": "language must be one of 'en', 'es', 'pt'"}), 400

  if not emotions or not isinstance(emotions, dict):
    return jsonify({"error": "emotions dict is required"}), 400

  valid_emotions = {"anger", "disgust", "fear", "joy", "sadness", "passion", "surprise"}
  filtered_emotions = {}
  for emotion, weight in emotions.items():
    if emotion in valid_emotions:
      try:
        filtered_emotions[emotion] = float(weight)
      except (ValueError, TypeError):
        pass

  if not filtered_emotions:
    return jsonify({"error": "At least one valid emotion weight is required"}), 400

  # Add to lexicon
  if language not in LEXICON_TOKEN:
    LEXICON_TOKEN[language] = {}

  LEXICON_TOKEN[language][word] = filtered_emotions

  # Rebuild detector indices
  set_lexicon_token(LEXICON_TOKEN, expand_morphology=True)

  return jsonify({
    "ok": True,
    "word": word,
    "language": language,
    "emotions": filtered_emotions
  })


# ---------------------------------------------------------------------------
# Account and authentication APIs
# ---------------------------------------------------------------------------


@app.route("/api/auth/register", methods=["POST"])
def api_auth_register() -> object:
  conn = None
  try:
    data = request.get_json(silent=True) or {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not all([first_name, last_name, username, email, password]):
      return jsonify({"error": "All fields are required"}), 400

    password_hash = generate_password_hash(password)

    conn = get_db()
    cur = conn.cursor()

    # Check uniqueness
    cur.execute("SELECT 1 FROM users WHERE username = %s OR email = %s;", (username, email))
    exists = cur.fetchone()
    if exists:
      cur.close()
      conn.close()
      conn = None
      return jsonify({"error": "Username or email already in use"}), 400

    cur.execute(
      """
      INSERT INTO users (first_name, last_name, username, email, password_hash)
      VALUES (%s, %s, %s, %s, %s)
      RETURNING id, first_name, last_name, username, email, preferred_language, preferred_theme;
      """,
      (first_name, last_name, username, email, password_hash),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    conn = None

    # Build payload from the row we just inserted
    payload = user_to_payload(row)
    session["user_id"] = payload["id"]
    session.permanent = True
    return jsonify({"ok": True, "user": payload})
  except Exception as e:
    if conn:
      try:
        conn.rollback()
        conn.close()
      except Exception:
        pass
    app.logger.error(f"Registration error: {e}", exc_info=True)
    error_msg = str(e).lower()
    if "unique" in error_msg or "duplicate" in error_msg:
      return jsonify({"error": "Username or email already in use"}), 400
    return jsonify({"error": "Registration failed. Please try again."}), 500


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login() -> object:
  data = request.get_json(silent=True) or {}
  identifier = (data.get("identifier") or "").strip().lower()
  password = data.get("password") or ""

  if not identifier or not password:
    return jsonify({"error": "Email or username and password are required"}), 400

  conn = None
  try:
    conn = get_db()
    cur = conn.cursor()
    # Identifier can be email or username
    cur.execute(
      """
      SELECT *
      FROM users
      WHERE lower(email) = %s OR lower(username) = %s;
      """,
      (identifier, identifier),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    conn = None

    if not row or not check_password_hash(row["password_hash"], password):
      return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = row["id"]
    session.permanent = True
    return jsonify({"ok": True, "user": user_to_payload(row)})
  except Exception as e:
    if conn:
      try:
        conn.close()
      except Exception:
        pass
    app.logger.error(f"Login error: {e}", exc_info=True)
    return jsonify({"error": "Login failed. Please try again."}), 500


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout() -> object:
  session.pop("user_id", None)
  return jsonify({"ok": True})


@app.route("/api/auth/me", methods=["GET"])
def api_auth_me() -> object:
  uid = current_user_id()
  if uid is None:
    return jsonify({"user": None})

  conn = None
  try:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s;", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    conn = None

    if not row:
      session.pop("user_id", None)
      return jsonify({"user": None})

    return jsonify({"user": user_to_payload(row)})
  except Exception as e:
    if conn:
      try:
        conn.close()
      except Exception:
        pass
    app.logger.error(f"Auth me error: {e}", exc_info=True)
    return jsonify({"user": None})


@app.route("/api/auth/update-settings", methods=["POST"])
def api_auth_update_settings() -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  data = request.get_json(silent=True) or {}

  preferred_language = data.get("preferred_language")
  preferred_theme = data.get("preferred_theme")

  conn = None
  try:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
      """
      UPDATE users
      SET preferred_language = COALESCE(%s, preferred_language),
          preferred_theme = COALESCE(%s, preferred_theme),
          updated_at = NOW()
      WHERE id = %s
      RETURNING *;
      """,
      (preferred_language, preferred_theme, uid),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    conn = None

    return jsonify({"ok": True, "user": user_to_payload(row)})
  except Exception as e:
    if conn:
      try:
        conn.rollback()
        conn.close()
      except Exception:
        pass
    app.logger.error(f"Update settings error: {e}", exc_info=True)
    return jsonify({"error": "Failed to update settings. Please try again."}), 500


@app.route("/api/auth/reset-password", methods=["POST"])
def api_auth_reset_password() -> object:
  """
  Password reset flow without email.

  Expected JSON body:
    {
      "email": "...",
      "first_name": "...",
      "last_name": "...",
      "new_password": "...",
      "confirm_password": "..."
    }
  """
  data = request.get_json(silent=True) or {}
  email = (data.get("email") or "").strip().lower()
  first_name = (data.get("first_name") or "").strip()
  last_name = (data.get("last_name") or "").strip()
  new_password = data.get("new_password") or ""
  confirm_password = data.get("confirm_password") or ""

  if not all([email, first_name, last_name, new_password, confirm_password]):
    return jsonify({"error": "All fields are required"}), 400

  if new_password != confirm_password:
    return jsonify({"error": "Passwords do not match"}), 400

  conn = None
  try:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
      """
      SELECT *
      FROM users
      WHERE lower(email) = %s
        AND lower(first_name) = %s
        AND lower(last_name) = %s;
      """,
      (email, first_name.lower(), last_name.lower()),
    )
    row = cur.fetchone()
    if not row:
      cur.close()
      conn.close()
      return jsonify({"error": "User not found with provided details"}), 404

    password_hash = generate_password_hash(new_password)
    cur.execute(
      """
      UPDATE users
      SET password_hash = %s, updated_at = NOW()
      WHERE id = %s;
      """,
      (password_hash, row["id"]),
    )
    conn.commit()
    cur.close()
    conn.close()
    conn = None

    return jsonify({"ok": True})
  except Exception as e:
    if conn:
      try:
        conn.rollback()
        conn.close()
      except Exception:
        pass
    app.logger.error(f"Password reset error: {e}", exc_info=True)
    return jsonify({"error": "Password reset failed. Please try again."}), 500


@app.route("/api/users/account", methods=["DELETE"])
def api_delete_account() -> object:
  """Delete the current user's account after password verification."""
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  data = request.get_json(silent=True) or {}
  password = data.get("password") or ""
  confirmation = data.get("confirmation") or ""

  if not password:
    return jsonify({"error": "Password is required"}), 400

  if confirmation != "DELETE":
    return jsonify({"error": "Please confirm deletion"}), 400

  conn = None
  try:
    conn = get_db()
    cur = conn.cursor()

    # Verify password
    cur.execute("SELECT * FROM users WHERE id = %s;", (uid,))
    row = cur.fetchone()
    if not row:
      cur.close()
      conn.close()
      return jsonify({"error": "User not found"}), 404

    if not check_password_hash(row["password_hash"], password):
      cur.close()
      conn.close()
      return jsonify({"error": "Incorrect password"}), 401

    # Delete user (CASCADE will handle related records)
    cur.execute("DELETE FROM users WHERE id = %s;", (uid,))
    conn.commit()
    cur.close()
    conn.close()
    conn = None

    session.pop("user_id", None)
    return jsonify({"ok": True})
  except Exception as e:
    if conn:
      try:
        conn.rollback()
        conn.close()
      except Exception:
        pass
    app.logger.error(f"Account deletion error: {e}", exc_info=True)
    return jsonify({"error": "Failed to delete account. Please try again."}), 500


# ---------------------------------------------------------------------------
# Journals APIs
# ---------------------------------------------------------------------------


@app.route("/api/journals", methods=["GET"])
def api_list_journals() -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    SELECT id, title, created_at, updated_at,
           is_pinned, has_self_harm_flag
    FROM journals
    WHERE user_id = %s
    ORDER BY is_pinned DESC, created_at DESC;
    """,
    (uid,),
  )
  rows = cur.fetchall()
  cur.close()
  conn.close()

  return jsonify({"journals": rows})


@app.route("/api/journals/<int:journal_id>", methods=["GET"])
def api_get_journal(journal_id: int) -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    SELECT *
    FROM journals
    WHERE id = %s AND user_id = %s;
    """,
    (journal_id, uid),
  )
  row = cur.fetchone()
  cur.close()
  conn.close()

  if not row:
    return jsonify({"error": "Journal not found"}), 404

  return jsonify({"journal": row})


@app.route("/api/journals", methods=["POST"])
def api_create_journal() -> object:
  """
  Create a new journal entry.

  Expected JSON body:
    {
      "title": "...",
      "source_text": "...",     # optional, original analysis text
      "analysis_json": {...},   # optional, bar chart or analysis payload
      "journal_text": "..."     # optional, free form notes
    }
  """
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  data = request.get_json(silent=True) or {}
  title = (data.get("title") or "").strip()
  source_text = data.get("source_text")
  analysis_json = data.get("analysis_json")
  journal_text = data.get("journal_text") or ""

  if not title:
    return jsonify({"error": "Title is required"}), 400

  has_flag = detect_self_harm_flag(source_text or "") or detect_self_harm_flag(journal_text)

  json_payload = Jsonb(analysis_json) if analysis_json is not None else None

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    INSERT INTO journals (user_id, title, source_text, analysis_json,
                          journal_text, has_self_harm_flag)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, title, created_at, updated_at,
              is_pinned, has_self_harm_flag;
    """,
    (uid, title, source_text, json_payload, journal_text, has_flag),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "journal": row})


@app.route("/api/journals/<int:journal_id>", methods=["PUT"])
def api_update_journal(journal_id: int) -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  data = request.get_json(silent=True) or {}

  title = data.get("title")
  journal_text = data.get("journal_text")

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    UPDATE journals
    SET title = COALESCE(%s, title),
        journal_text = COALESCE(%s, journal_text),
        has_self_harm_flag = %s,
        updated_at = NOW()
    WHERE id = %s AND user_id = %s
    RETURNING *;
    """,
    (
      title,
      journal_text,
      detect_self_harm_flag(journal_text or ""),
      journal_id,
      uid,
    ),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  if not row:
    return jsonify({"error": "Journal not found"}), 404

  return jsonify({"ok": True, "journal": row})


@app.route("/api/journals/<int:journal_id>", methods=["DELETE"])
def api_delete_journal(journal_id: int) -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    "DELETE FROM journals WHERE id = %s AND user_id = %s RETURNING id;",
    (journal_id, uid),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  if not row:
    return jsonify({"error": "Journal not found"}), 404

  return jsonify({"ok": True})


@app.route("/api/journals/<int:journal_id>/pin", methods=["POST"])
def api_pin_journal(journal_id: int) -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  data = request.get_json(silent=True) or {}
  is_pinned = bool(data.get("is_pinned", True))

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    UPDATE journals
    SET is_pinned = %s, updated_at = NOW()
    WHERE id = %s AND user_id = %s
    RETURNING id, title, created_at, updated_at,
              is_pinned, has_self_harm_flag;
    """,
    (is_pinned, journal_id, uid),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  if not row:
    return jsonify({"error": "Journal not found"}), 404

  return jsonify({"ok": True, "journal": row})


# ---------------------------------------------------------------------------
# Feedback APIs (anonymous submission for analysis accuracy)
# ---------------------------------------------------------------------------


@app.route("/api/feedback", methods=["POST"])
def api_submit_feedback() -> object:
  """
  Submit anonymous feedback about analysis accuracy.

  Expected JSON body:
    {
      "entry_text": "...",          # Original analyzed text
      "analysis_json": {...},       # Full analysis data
      "feedback_text": "..."        # User's feedback (required)
    }

  Note: No user account is attached to feedback submissions.
  """
  data = request.get_json(silent=True) or {}
  entry_text = (data.get("entry_text") or "").strip()
  analysis_json = data.get("analysis_json")
  feedback_text = (data.get("feedback_text") or "").strip()

  if not entry_text:
    return jsonify({"error": "Entry text is required"}), 400

  if not feedback_text:
    return jsonify({"error": "Feedback is required"}), 400

  json_payload = Jsonb(analysis_json) if analysis_json is not None else None

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    INSERT INTO feedback (entry_text, analysis_json, feedback_text)
    VALUES (%s, %s, %s)
    RETURNING id, created_at;
    """,
    (entry_text, json_payload, feedback_text),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "feedback_id": row["id"]})


# ---------------------------------------------------------------------------
# Admin Feedback APIs
# ---------------------------------------------------------------------------


@app.route("/api/admin/feedback", methods=["GET"])
def api_admin_get_feedback() -> object:
  """
  Get all feedback entries for the admin to review.
  Returns feedback formatted as a document.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    SELECT id, entry_text, analysis_json, feedback_text, created_at
    FROM feedback
    ORDER BY created_at DESC;
    """
  )
  rows = cur.fetchall()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "feedback": rows, "count": len(rows)})


@app.route("/api/admin/feedback/download", methods=["GET"])
def api_admin_download_feedback() -> object:
  """
  Download all feedback as a formatted text document.
  Returns the feedback content as a downloadable text file.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    SELECT id, entry_text, analysis_json, feedback_text, created_at
    FROM feedback
    ORDER BY created_at DESC;
    """
  )
  rows = cur.fetchall()
  cur.close()
  conn.close()

  # Build the document content
  lines = []
  lines.append("=" * 60)
  lines.append("IN TUNED - FEEDBACK DOCUMENT")
  lines.append("=" * 60)
  lines.append(f"Generated: {__import__('datetime').datetime.now().isoformat()}")
  lines.append(f"Total Feedback Entries: {len(rows)}")
  lines.append("=" * 60)
  lines.append("")

  for idx, row in enumerate(rows, 1):
    lines.append("-" * 60)
    lines.append(f"FEEDBACK #{idx}")
    lines.append("-" * 60)
    lines.append(f"ID: {row['id']}")
    lines.append(f"Submitted: {row['created_at']}")
    lines.append("")
    lines.append("ENTRY TEXT:")
    lines.append(row["entry_text"] or "(empty)")
    lines.append("")

    analysis = row.get("analysis_json") or {}
    if analysis:
      results = analysis.get("results", {})
      dominant = results.get("dominant", {})
      current = results.get("current", {})

      dom_label = (
        dominant.get("labelLocalized")
        or dominant.get("nuancedLabel")
        or dominant.get("label")
        or "N/A"
      )
      cur_label = (
        current.get("labelLocalized")
        or current.get("nuancedLabel")
        or current.get("label")
        or "N/A"
      )

      lines.append("ANALYSIS SUMMARY:")
      lines.append(f"  Dominant: {dom_label}")
      lines.append(f"  Current: {cur_label}")

      core_mix = analysis.get("coreMixture", [])
      if core_mix:
        lines.append("  Core Mixture:")
        for em in core_mix:
          if em.get("percent", 0) > 0:
            lines.append(f"    - {em.get('label', em.get('id', 'Unknown'))}: {em.get('percent', 0):.1f}%")
      lines.append("")

    lines.append("USER FEEDBACK:")
    lines.append(row["feedback_text"] or "(empty)")
    lines.append("")
    lines.append("")

  lines.append("=" * 60)
  lines.append("END OF FEEDBACK DOCUMENT")
  lines.append("=" * 60)

  document_content = "\n".join(lines)

  from flask import Response

  response = Response(
    document_content,
    mimetype="text/plain",
    headers={"Content-Disposition": "attachment; filename=feedback_document.txt"}
  )

  return response


@app.route("/api/admin/feedback/delete", methods=["DELETE"])
def api_admin_delete_all_feedback() -> object:
  """
  Delete all feedback entries after download.
  This clears the feedback table to start fresh.
  """
  guard = require_admin()
  if guard is not None:
    return guard

  conn = get_db()
  cur = conn.cursor()
  cur.execute("DELETE FROM feedback;")
  deleted_count = cur.rowcount
  conn.commit()
  cur.close()
  conn.close()

  return jsonify({"ok": True, "deleted_count": deleted_count})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
  port = int(os.environ.get("PORT", "5000"))
  app.run(host="0.0.0.0", port=port)
