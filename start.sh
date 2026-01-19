#!/usr/bin/env bash
set -e

echo "Installing Python dependencies..."

if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  pip install flask gunicorn
fi

echo "Starting Gunicorn server..."

# Railway sets PORT in the environment, default to 5000 if not set
exec gunicorn wsgi:application --bind 0.0.0.0:${PORT:-5000}
