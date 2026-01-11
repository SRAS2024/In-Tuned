# In-Tuned

Multi-lingual emotion detection and journaling platform for enhanced self-awareness and mental processing.

## Overview

In-Tuned is a Flask-based web application that helps users:
- Analyze emotions in text entries (English, Spanish, Portuguese)
- Keep a personal journal with emotion tracking
- Receive insights about emotional patterns over time
- Access crisis resources when needed

## Features

- **Multi-language Support**: Emotion detection in English, Spanish, and Portuguese
- **Personal Journaling**: Create, edit, and organize journal entries
- **Emotion Analysis**: Real-time emotion detection with detailed breakdowns
- **Self-harm Detection**: Automatic flagging with crisis resources
- **User Authentication**: Secure registration, login, and session management
- **Admin Dashboard**: System monitoring, user management, and maintenance tools
- **External Lexicon Expansion**: Integration with Urban Dictionary and Free Dictionary APIs

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 13 or higher
- Redis (optional, for caching)

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
   # Run migrations
   alembic upgrade head

   # Create admin credentials (follow prompts)
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

## Configuration

All configuration is done through environment variables. See `.env.example` for a complete list.

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
| `FLASK_ENV` | `development` | Environment (development/staging/production) |
| `RATELIMIT_ENABLED` | `true` | Enable rate limiting |
| `SESSION_LIFETIME_MINUTES` | `60` | Session timeout |
| `BCRYPT_LOG_ROUNDS` | `12` | Password hashing strength |

## Project Structure

```
In-Tuned/
├── app/                      # Application package
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions
│   ├── logging_config.py    # Logging setup
│   ├── cli.py               # CLI commands
│   ├── blueprints/          # Route handlers
│   │   ├── auth.py          # Authentication routes
│   │   ├── admin.py         # Admin panel routes
│   │   ├── entries.py       # Journal entry routes
│   │   ├── detector.py      # Emotion analysis routes
│   │   ├── lexicon.py       # Lexicon management routes
│   │   ├── feedback.py      # User feedback routes
│   │   ├── site.py          # Site status routes
│   │   └── users.py         # User management routes
│   ├── db/                  # Database layer
│   │   ├── connection.py    # Connection pooling
│   │   ├── transaction.py   # Transaction management
│   │   └── repositories/    # Data access objects
│   ├── services/            # Business logic
│   │   ├── detector_service.py
│   │   └── lexicon_service.py
│   └── utils/               # Utilities
│       ├── errors.py        # Error handling
│       ├── responses.py     # API response helpers
│       ├── validation.py    # Input validation
│       └── security.py      # Security utilities
├── client/                  # Frontend files
├── detector/                # Emotion detection engine
├── migrations/              # Alembic migrations
├── tests/                   # Test suite
├── .env.example            # Environment template
├── alembic.ini             # Alembic configuration
├── docker-compose.yml      # Docker setup
├── Dockerfile              # Container definition
├── Makefile                # Development tasks
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
└── wsgi.py                 # WSGI entry point
```

## API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login with email/username |
| `/api/auth/logout` | POST | End session |
| `/api/auth/me` | GET | Get current user |
| `/api/auth/update-settings` | POST | Update preferences |

### Journal Entries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/journals` | GET | List user's entries |
| `/api/journals` | POST | Create new entry |
| `/api/journals/<id>` | GET | Get specific entry |
| `/api/journals/<id>` | PUT | Update entry |
| `/api/journals/<id>` | DELETE | Delete entry |
| `/api/journals/<id>/pin` | POST | Toggle pin status |

### Emotion Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze text emotions |

### Response Format

All API endpoints return JSON in this format:

```json
{
  "ok": true,
  "data": { ... }
}
```

Or on error:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format"
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run in parallel
make test-fast
```

### Code Quality

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make typecheck

# Security scan
make security

# All checks
make check
```

### Database Migrations

```bash
# Apply migrations
make migrate

# Create new migration
make migrate-new

# Reset database (DESTRUCTIVE)
make db-reset
```

## Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Generate strong `SECRET_KEY` (32+ random chars)
- [ ] Create secure admin password hashes
- [ ] Enable HTTPS with valid certificates
- [ ] Configure reverse proxy (nginx)
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Enable monitoring/alerting

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

## Security

- Passwords hashed with bcrypt
- CSRF protection on all state-changing endpoints
- Rate limiting on authentication endpoints
- Session timeout and secure cookie settings
- Input validation and sanitization
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding
- Security headers (CSP, HSTS, X-Frame-Options)
- Audit logging for sensitive operations

### Reporting Vulnerabilities

Please report security issues privately to the maintainers.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Acknowledgments

- Flask framework and extensions
- PostgreSQL database
- The emotion detection research community
