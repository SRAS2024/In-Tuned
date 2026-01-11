# wsgi.py
"""
WSGI entry point for production deployments.

Usage with Gunicorn:
    gunicorn wsgi:application -w 4 -b 0.0.0.0:8000

Usage with uWSGI:
    uwsgi --http :8000 --wsgi-file wsgi.py --callable application
"""

from app import create_app


# Create the application instance
application = create_app()

# Alias for compatibility with different WSGI servers
app = application


if __name__ == "__main__":
    # For development only - use gunicorn in production
    application.run()
