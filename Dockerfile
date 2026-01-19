# Dockerfile
# Multi stage build for In Tuned application

# You can override this at build time with:
# docker build --build-arg PYTHON_VERSION=3.13-slim .
ARG PYTHON_VERSION=3.13-slim

# Stage 1: Build wheels
FROM python:${PYTHON_VERSION} AS builder

WORKDIR /app

# Build dependencies for compiling any wheels that need it
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
  && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Runtime image
FROM python:${PYTHON_VERSION} AS production

# Create non root user for security
RUN groupadd -r intuned && useradd -r -g intuned intuned

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install wheels built in the builder stage
COPY --from=builder /app/wheels /wheels
RUN python -m pip install --upgrade pip \
  && pip install --no-cache-dir /wheels/* \
  && rm -rf /wheels

# Copy application code
COPY --chown=intuned:intuned . .

# Copy and set up entrypoint script
COPY --chown=intuned:intuned entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment variables
# NOTE: Do not hardcode PORT here. Railway injects PORT at runtime.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Switch to non root user
USER intuned

# Expose a default port for local runs (platform routing does not rely on EXPOSE)
EXPOSE 8000

# Health check uses the runtime PORT if provided
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD ["sh", "-c", "curl -fsS http://localhost:${PORT:-8000}/api/health || exit 1"]

# Use entrypoint for runtime validation and startup
ENTRYPOINT ["/entrypoint.sh"]

# Default command
# IMPORTANT: Bind to the platform provided PORT (Railway sets this).
CMD ["sh", "-c", "gunicorn wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --worker-class gthread \
  --workers ${WEB_CONCURRENCY:-4} \
  --threads ${THREADS:-2} \
  --timeout ${TIMEOUT:-120} \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance"]
