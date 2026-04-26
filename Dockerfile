# Dockerfile
# Multi stage production-ready build for In Tuned.
#
# Stages:
#   1. base    - shared Python settings (env, system pip)
#   2. builder - compile wheels with build-essential + libpq-dev
#   3. runtime - slim runtime image with only libpq + curl + wheels
#
# Override the Python version at build time with:
#   docker build --build-arg PYTHON_VERSION=3.13-slim .

ARG PYTHON_VERSION=3.13-slim


# -----------------------------------------------------------------------------
# Stage 1: Base
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app


# -----------------------------------------------------------------------------
# Stage 2: Builder - compile wheels for the target platform
# -----------------------------------------------------------------------------
FROM base AS builder

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
  && pip wheel --no-deps --wheel-dir /wheels -r requirements.txt


# -----------------------------------------------------------------------------
# Stage 3: Runtime - production image
# -----------------------------------------------------------------------------
FROM base AS production

# Create non root user / group up front so COPY --chown works.
RUN groupadd -r intuned \
  && useradd -r -g intuned -m -d /home/intuned -s /bin/bash intuned

# Runtime dependencies only.
#   libpq5 - psycopg native client
#   curl   - container healthcheck
#   tini   - PID 1 signal handling so SIGTERM reaches gunicorn cleanly
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       libpq5 \
       curl \
       tini \
  && rm -rf /var/lib/apt/lists/*

# Install pre-built wheels.
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
  && rm -rf /wheels

# Copy application code with the right ownership in one layer.
COPY --chown=intuned:intuned . .

# Make the entrypoint executable.
RUN chmod +x /app/entrypoint.sh

ENV FLASK_ENV=production \
    PORT=8000

USER intuned

# Expose default port for local runs. Real port routing on Railway / Fly /
# similar platforms is handled via the PORT env var inside the CMD below.
EXPOSE 8000

# Healthcheck honors $PORT so it works wherever the platform places us.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/api/health" || exit 1

# tini is PID 1 so signals propagate and zombie children are reaped.
# entrypoint.sh runs runtime validation, then exec's the CMD.
ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]

# Default command.
# Binds to the platform provided PORT (Railway, Fly, Heroku, etc set this).
# WEB_CONCURRENCY, THREADS, TIMEOUT, GUNICORN_LOG_LEVEL are tunable.
CMD ["sh", "-c", "exec gunicorn wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --worker-class gthread \
  --workers ${WEB_CONCURRENCY:-4} \
  --threads ${THREADS:-2} \
  --timeout ${TIMEOUT:-120} \
  --graceful-timeout ${GRACEFUL_TIMEOUT:-30} \
  --keep-alive ${KEEPALIVE:-5} \
  --access-logfile - \
  --error-logfile - \
  --log-level ${GUNICORN_LOG_LEVEL:-info} \
  --capture-output \
  --enable-stdio-inheritance"]
