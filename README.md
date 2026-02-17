# In-Tuned

**Multi-lingual emotion detection and journaling platform for enhanced self-awareness and mental well-being.**

**Live Site**: [https://intunedreflection.com](https://intunedreflection.com)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Emotion Detection Engine](#emotion-detection-engine)
- [Development](#development)
- [Deployment](#deployment)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

In-Tuned is a Flask-based web application that analyzes emotions in text across multiple languages and provides users with a personal journaling experience enriched by emotional insights. Whether you're reflecting on your day or exploring how your words carry emotional weight, In-Tuned offers real-time feedback across seven core emotions.

The platform also includes built-in safety features that detect crisis-related language and surface region-specific helpline resources when needed.

**Try it now**: [https://intunedreflection.com](https://intunedreflection.com)

---

## Features

### Emotion Analysis
- **7 Core Emotions**: Anger, disgust, fear, joy, sadness, passion, and surprise
- **Multi-Language Support**: Emotion detection in English, Spanish, and Portuguese
- **Real-Time Analysis**: Instant emotional breakdown with intensity levels and nuanced labels
- **Arousal & Confidence Metrics**: Quantified emotional intensity and analysis reliability scores
- **Typographic Emphasis Detection**: Recognizes ALL CAPS, punctuation patterns (!!!, ???), and other emphasis cues

### Journaling
- **Personal Journal**: Create, edit, search, and organize journal entries
- **Emotion Snapshots**: Each entry captures the full emotional analysis at time of writing
- **Pinned Entries**: Mark important entries for quick access
- **Pagination & Search**: Navigate large collections of entries efficiently

### Safety & Crisis Support
- **Self-Harm Detection**: Automatic keyword flagging in English, Spanish, and Portuguese — including modern slang variants (e.g., "unalive", "sewerslide")
- **Crisis Severity Levels**: None, possible, likely, and severe
- **Regional Hotlines**: Context-aware crisis resource links based on user region

### User Experience
- **Dark / Light Theme**: Toggle between themes with persistent preference
- **Responsive Design**: Full support for desktop, tablet, and mobile
- **Multi-Language UI**: Interface available in English, Spanish, and Portuguese
- **Per-Tab Sessions**: Independent session storage across browser tabs

### Administration
- **Admin Dashboard**: System monitoring, user management, and audit logs
- **Maintenance Mode**: Pause the application with custom messages
- **System Notices**: Display announcements to all users
- **Lexicon Management**: Upload, expand, and manage emotion detection lexicons
- **Feedback Review**: View and manage user-submitted feedback on analyses

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.10+, Flask 3.0, Gunicorn |
| **Database** | PostgreSQL 13+ (SQLite for development) |
| **Migrations** | Alembic 1.13 |
| **Frontend** | Vanilla JavaScript, HTML5, CSS3 |
| **Caching** | Flask-Caching (in-memory, Redis, or filesystem) |
| **Security** | bcrypt, Flask-WTF (CSRF), Flask-Limiter (rate limiting) |
| **Testing** | pytest, httpx, coverage |
| **Code Quality** | Black, Ruff, mypy, Bandit |
| **Containerization** | Docker, Docker Compose |
| **Deployment** | Railway |
| **Error Tracking** | Sentry (optional) |

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 13 or higher
- Redis (optional, for production caching and rate limiting)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SRAS2024/In-Tuned.git
   cd In-Tuned
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   alembic upgrade head
   flask --app wsgi:application create-admin
   ```

6. **Run the development server**
   ```bash
   flask --app wsgi:application run --debug
   ```

   Or using Make:
   ```bash
   make run
   ```

7. **Access the application**
   - Web UI: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

### Using Docker

```bash
# Build and start all services
docker-compose up -d

# Run migrations
docker-compose --profile migrate run --rm migrate

# View logs
docker-compose logs -f app
```

---

## Configuration

All configuration is managed through environment variables. See `.env.example` for the full list.

### Required Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret (min 32 chars) |
| `ADMIN_USERNAME` | Admin panel username |
| `ADMIN_PASSWORD_HASH` | Bcrypt hash of admin password |
| `DEV_PASSWORD_HASH` | Bcrypt hash for dev/maintenance mode |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Environment (`development` / `staging` / `production`) |
| `RATELIMIT_ENABLED` | `true` | Enable rate limiting |
| `SESSION_LIFETIME_MINUTES` | `60` | Session timeout |
| `BCRYPT_LOG_ROUNDS` | `12` | Password hashing strength |
| `REDIS_URL` | — | Redis connection string for caching/rate limiting |
| `RAPIDAPI_KEY` | — | API key for external dictionary expansion |
| `SENTRY_DSN` | — | Sentry error tracking DSN |
| `DATABASE_POOL_SIZE` | `5` | Database connection pool size |
| `PASSWORD_MIN_LENGTH` | `8` | Minimum password length |
| `MAX_LOGIN_ATTEMPTS` | `5` | Max failed logins before lockout |

---

## Project Structure

```
In-Tuned/
├── app/                          # Application package
│   ├── __init__.py              # App factory (create_app)
│   ├── config.py                # Configuration classes
│   ├── extensions.py            # Flask extensions
│   ├── logging_config.py        # Logging setup
│   ├── cli.py                   # CLI commands
│   ├── blueprints/              # Route handlers
│   │   ├── auth.py              # Authentication routes
│   │   ├── admin.py             # Admin panel routes
│   │   ├── entries.py           # Journal entry routes
│   │   ├── detector.py          # Emotion analysis routes
│   │   ├── lexicon.py           # Lexicon management routes
│   │   ├── feedback.py          # User feedback routes
│   │   ├── analytics.py         # Usage statistics routes
│   │   ├── site.py              # Site status routes
│   │   └── users.py             # User management routes
│   ├── db/                      # Database layer
│   │   ├── connection.py        # Connection pooling
│   │   ├── transaction.py       # Transaction management
│   │   └── repositories/        # Data access objects
│   ├── services/                # Business logic
│   │   ├── detector_service.py  # Emotion detection orchestration
│   │   └── lexicon_service.py   # External lexicon integration
│   └── utils/                   # Utilities
│       ├── errors.py            # Custom exceptions
│       ├── responses.py         # API response helpers
│       ├── validation.py        # Input validation
│       └── security.py          # Security utilities
├── detector/                    # Emotion detection engine
│   ├── detector.py              # Core detector (v31-espt-meta-db)
│   ├── formatter.py             # Output formatting for client
│   ├── external_lexicon.py      # Urban Dictionary & Free Dictionary APIs
│   ├── lexicon_loader.py        # Lexicon file loading
│   └── lexicons/                # Emotion lexicon data
│       ├── english.py           # English emotion keywords
│       ├── spanish.py           # Spanish emotion keywords
│       ├── portuguese.py        # Portuguese emotion keywords
│       └── safety.py            # Self-harm detection keywords
├── client/                      # Frontend files
│   ├── index.html               # Main application page
│   ├── admin.html               # Admin dashboard
│   ├── main.js                  # Core application logic
│   ├── admin.js                 # Admin panel logic
│   ├── styles.css               # Main styles
│   ├── css/                     # Additional stylesheets
│   └── js/                      # Additional JavaScript modules
├── migrations/                  # Alembic database migrations
├── tests/                       # Test suite
├── docs/                        # Documentation
├── .env.example                 # Environment template
├── alembic.ini                  # Alembic configuration
├── docker-compose.yml           # Docker setup
├── Dockerfile                   # Container definition
├── Makefile                     # Development tasks
├── pyproject.toml               # Project configuration
├── requirements.txt             # Python dependencies
└── wsgi.py                      # WSGI entry point
```

---

## API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register a new user |
| `/api/auth/login` | POST | Login with email or username |
| `/api/auth/logout` | POST | End the current session |
| `/api/auth/me` | GET | Get current user profile |
| `/api/auth/update-settings` | POST | Update user preferences |

### Journal Entries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/journals` | GET | List user's entries (paginated, searchable) |
| `/api/journals` | POST | Create a new entry |
| `/api/journals/<id>` | GET | Get a specific entry |
| `/api/journals/<id>` | PUT | Update an entry |
| `/api/journals/<id>` | DELETE | Delete an entry |
| `/api/journals/<id>/pin` | POST | Toggle pin status |

### Emotion Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze text for emotions (1–250 words) |

**Request body:**
```json
{
  "text": "I feel great today!",
  "locale": "en",
  "region": "US"
}
```

### Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/login` | POST | Admin authentication |
| `/api/admin/maintenance` | GET/POST | Maintenance mode control |
| `/api/admin/notices` | GET/POST | System notices management |
| `/api/admin/feedback` | GET | View user feedback |
| `/api/admin/lexicons/lookup` | POST | Look up word emotions |
| `/api/admin/lexicons/expand` | POST | Expand lexicon via external APIs |
| `/api/admin/lexicons/add-word` | POST | Add word to lexicon |

### Site

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/site-state` | GET | Site status, maintenance mode, notices |

### Response Format

All endpoints return JSON:

```json
{
  "ok": true,
  "data": { ... }
}
```

Error responses:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format"
  }
}
```

---

## Emotion Detection Engine

The core detection engine (`detector/detector.py`, version v31-espt-meta-db) processes text input and produces a mixture vector across seven emotions:

| Emotion | Example Intensity Labels |
|---------|--------------------------|
| **Anger** | Slightly irritated → Furious |
| **Disgust** | Mildly put off → Revolted |
| **Fear** | Slightly uneasy → Terrified |
| **Joy** | Mildly pleased → Ecstatic |
| **Sadness** | A bit down → Grief-stricken |
| **Passion** | Mildly interested → Deeply passionate |
| **Surprise** | Mildly surprised → Astonished |

### How It Works

1. **Language Detection**: Identifies whether the input is English, Spanish, or Portuguese
2. **Lexicon Matching**: Matches words against comprehensive emotion lexicons
3. **Emphasis Analysis**: Accounts for ALL CAPS, punctuation patterns, and typographic cues
4. **Mixture Calculation**: Produces weighted intensity scores (not probabilities) for each emotion
5. **Metrics**: Computes arousal, confidence, sarcasm, and humor scores
6. **Safety Check**: Scans for self-harm keywords and assigns a risk level

### External Lexicon Expansion

The engine can dynamically expand its vocabulary using:
- **Urban Dictionary API** — modern slang and colloquial terms (English)
- **Free Dictionary API** — standard definitions for English, Spanish, and Portuguese

---

## Development

### Server Architecture

This project uses the modular blueprint approach with `wsgi:application` as the entry point.

```bash
# Development
flask --app wsgi:application run --debug

# Production
gunicorn wsgi:application --bind 0.0.0.0:8000
```

### Running Tests

```bash
make test          # Run all tests
make test-cov      # Run with coverage
make test-fast     # Run in parallel
```

### Code Quality

```bash
make format        # Format code (Black + Ruff)
make lint          # Run linter (Ruff)
make typecheck     # Type checking (mypy)
make security      # Security scan (Bandit)
make check         # All checks at once
```

### Database Migrations

```bash
make migrate       # Apply migrations
make migrate-new   # Create a new migration
make db-reset      # Reset database (DESTRUCTIVE)
```

---

## Deployment

In-Tuned is deployed on [Railway](https://railway.app) at [https://intunedreflection.com](https://intunedreflection.com).

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Generate a strong `SECRET_KEY` (32+ random characters)
- [ ] Create secure admin password hashes
- [ ] Enable HTTPS with valid certificates
- [ ] Configure a reverse proxy (nginx) if not using a PaaS
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Enable monitoring and alerting

### Using Gunicorn

```bash
gunicorn wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

### Using Docker

```bash
# Build production image
docker build -t intuned:latest .

# Run container
docker run -d \
    --name intuned \
    -p 8000:8000 \
    --env-file .env \
    intuned:latest
```

---

## Security

- **Password Hashing**: bcrypt with configurable rounds (12 default, 14 in production)
- **CSRF Protection**: Tokens on all state-changing endpoints
- **Rate Limiting**: Configurable per-endpoint limits (e.g., 5 logins/min, 30 analyses/min)
- **Session Security**: HttpOnly, SameSite=Lax cookies with configurable timeout
- **Account Lockout**: Automatic lockout after repeated failed login attempts
- **Input Validation**: Strict schemas on all user input
- **SQL Injection Prevention**: Parameterized queries throughout
- **XSS Prevention**: Output encoding and Content Security Policy headers
- **Security Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Audit Logging**: All sensitive operations are tracked

### Reporting Vulnerabilities

Please report security issues privately to the maintainers.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) framework and extensions
- [PostgreSQL](https://www.postgresql.org/) database
- [Railway](https://railway.app/) for hosting
- The emotion detection research community
