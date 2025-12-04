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
from detector.detector import InvalidTextError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Admin credentials (for /admin portal and admin APIs)
ADMIN_USERNAME = "Ryan Simonds"
ADMIN_PASSWORD = "Santidade"
DEV_PASSWORD = "Meu Amor Maria"

# Database URL (set this in Railway as an env var, typically using
# the Postgres.DATABASE_URL value)
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
  # For production you should set DATABASE_URL in the environment.
  raise RuntimeError(
    "DATABASE_URL environment variable is not set. "
    "Set it in Railway to the provided Postgres connection URL."
  )

# Create Flask app
app = Flask(__name__, static_folder="client", static_url_path="")

# Secret key for signed sessions
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")


# ---------------------------------------------------------------------------
# Database helpers and schema
# ---------------------------------------------------------------------------


def get_db() -> psycopg.Connection:
  """
  Open a new database connection.

  For this app we keep it simple and open a connection per request.
  Railway Postgres can handle this level of traffic.
  """
  conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
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

  conn.commit()
  cur.close()
  conn.close()


# Initialize schema when module is imported
init_db()


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

  if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
    session["is_admin"] = True
    return jsonify({"ok": True, "message": "Welcome, Ryan!"})
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
# Account and authentication APIs
# ---------------------------------------------------------------------------


@app.route("/api/auth/register", methods=["POST"])
def api_auth_register() -> object:
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
    return jsonify({"error": "Username or email already in use"}), 400

  cur.execute(
    """
    INSERT INTO users (first_name, last_name, username, email, password_hash)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING *;
    """,
    (first_name, last_name, username, email, password_hash),
  )
  row = cur.fetchone()
  conn.commit()
  cur.close()
  conn.close()

  session["user_id"] = row["id"]
  return jsonify({"ok": True, "user": user_to_payload(row)})


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login() -> object:
  data = request.get_json(silent=True) or {}
  identifier = (data.get("identifier") or "").strip().lower()
  password = data.get("password") or ""

  if not identifier or not password:
    return jsonify({"error": "Email or username and password are required"}), 400

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

  if not row or not check_password_hash(row["password_hash"], password):
    return jsonify({"error": "Invalid credentials"}), 401

  session["user_id"] = row["id"]
  return jsonify({"ok": True, "user": user_to_payload(row)})


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout() -> object:
  session.pop("user_id", None)
  return jsonify({"ok": True})


@app.route("/api/auth/me", methods=["GET"])
def api_auth_me() -> object:
  uid = current_user_id()
  if uid is None:
    return jsonify({"user": None})

  conn = get_db()
  cur = conn.cursor()
  cur.execute("SELECT * FROM users WHERE id = %s;", (uid,))
  row = cur.fetchone()
  cur.close()
  conn.close()

  if not row:
    session.pop("user_id", None)
    return jsonify({"user": None})

  return jsonify({"user": user_to_payload(row)})


@app.route("/api/auth/update-settings", methods=["POST"])
def api_auth_update_settings() -> object:
  guard = require_login()
  if guard is not None:
    return guard

  uid = current_user_id()
  data = request.get_json(silent=True) or {}

  preferred_language = data.get("preferred_language")
  preferred_theme = data.get("preferred_theme")

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

  return jsonify({"ok": True, "user": user_to_payload(row)})


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

  conn = get_db()
  cur = conn.cursor()
  cur.execute(
    """
    SELECT *
    FROM users
    WHERE lower(email) = %s
      AND first_name = %s
      AND last_name = %s;
    """,
    (email, first_name, last_name),
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

  return jsonify({"ok": True})


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
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
  port = int(os.environ.get("PORT", "5000"))
  app.run(host="0.0.0.0", port=port)
