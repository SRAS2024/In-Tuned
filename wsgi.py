# wsgi.py
"""
WSGI entry point for production deployments.

This module creates the Flask application instance for WSGI servers.
Environment validation is handled by the entrypoint.sh script at container
startup, not at import time.

Usage with Gunicorn:
    gunicorn wsgi:application -w 4 -b 0.0.0.0:8000

Usage with uWSGI:
    uwsgi --http :8000 --wsgi-file wsgi.py --callable application
"""

from app import create_app

# Create the application instance
# Configuration is loaded from environment variables
# Required variables are validated by entrypoint.sh at container start
application = create_app()

# Alias for compatibility with different WSGI servers
app = application


if __name__ == "__main__":
    # For development only - use gunicorn in production
    application.run(host="0.0.0.0", port=8000, debug=True)
