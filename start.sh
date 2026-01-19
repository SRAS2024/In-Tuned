#!/usr/bin/env bash
set -euo pipefail

echo "Starting In Tuned..."

# Railway and many other platforms inject PORT. Default to 8000 for safety.
PORT="${PORT:-8000}"

# Sensible production defaults, all overridable via env vars.
WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"
THREADS="${THREADS:-4}"
TIMEOUT="${TIMEOUT:-120}"
KEEP_ALIVE="${KEEP_ALIVE:-5}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Install deps only if needed (keeps startups reliable, avoids unnecessary work).
# If your build already installs requirements, you can set SKIP_PIP_INSTALL=1.
if [ "${SKIP_PIP_INSTALL:-0}" != "1" ]; then
  echo "Ensuring Python dependencies are installed..."
  if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
  else
    pip install --no-cache-dir flask gunicorn
  fi
fi

echo "Launching Gunicorn on 0.0.0.0:${PORT}..."

exec gunicorn "wsgi:application" \
  --bind "0.0.0.0:${PORT}" \
  --worker-class "gthread" \
  --workers "${WEB_CONCURRENCY}" \
  --threads "${THREADS}" \
  --timeout "${TIMEOUT}" \
  --keep-alive "${KEEP_ALIVE}" \
  --log-level "${LOG_LEVEL}" \
  --access-logfile "-" \
  --error-logfile "-"
