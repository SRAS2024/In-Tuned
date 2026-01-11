# Architecture Overview

This document describes the architecture of the In-Tuned application.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Web UI     │  │ Admin Panel │  │  Future Mobile Apps     │ │
│  │  (Vanilla   │  │  (HTML/JS)  │  │  (React Native/Flutter) │ │
│  │   JS/HTML)  │  │             │  │                         │ │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘ │
└─────────┼────────────────┼─────────────────────────────────────┘
          │                │                      │
          ▼                ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Flask Application                       │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │              Rate Limiting (flask-limiter)           │  │ │
│  │  ├─────────────────────────────────────────────────────┤  │ │
│  │  │              CSRF Protection (flask-wtf)             │  │ │
│  │  ├─────────────────────────────────────────────────────┤  │ │
│  │  │              Security Headers                        │  │ │
│  │  ├─────────────────────────────────────────────────────┤  │ │
│  │  │              Request Logging & Tracing               │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Blueprints                          │   │
│  │  ┌─────┐ ┌─────┐ ┌───────┐ ┌────────┐ ┌───────┐        │   │
│  │  │Auth │ │Admin│ │Entries│ │Detector│ │Lexicon│ ...    │   │
│  │  └──┬──┘ └──┬──┘ └───┬───┘ └───┬────┘ └───┬───┘        │   │
│  └─────┼───────┼────────┼─────────┼──────────┼────────────┘   │
│        │       │        │         │          │                 │
│        ▼       ▼        ▼         ▼          ▼                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Service Layer                          │   │
│  │  ┌────────────────┐  ┌────────────────┐                 │   │
│  │  │DetectorService │  │ LexiconService │  ...            │   │
│  │  └───────┬────────┘  └───────┬────────┘                 │   │
│  └──────────┼───────────────────┼──────────────────────────┘   │
│             │                   │                              │
│             ▼                   ▼                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Repository Layer (DAL)                   │   │
│  │  ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌────────┐   │   │
│  │  │  User    │  │  Journal  │  │ Lexicon │  │ Audit  │   │   │
│  │  │Repository│  │Repository │  │Repository│  │Reposit│   │   │
│  │  └────┬─────┘  └─────┬─────┘  └────┬────┘  └───┬────┘   │   │
│  └───────┼──────────────┼─────────────┼───────────┼────────┘   │
└──────────┼──────────────┼─────────────┼───────────┼────────────┘
           │              │             │           │
           ▼              ▼             ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                PostgreSQL Database                        │  │
│  │  ┌───────┐ ┌────────┐ ┌───────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │ users │ │journals│ │lexicon│ │sessions │ │audit_log│  │  │
│  │  └───────┘ └────────┘ └───────┘ └─────────┘ └─────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Redis Cache (Optional)                   │  │
│  │  ┌──────────────┐  ┌───────────┐  ┌─────────────────┐    │  │
│  │  │ Rate Limits  │  │  Sessions │  │ Analysis Cache  │    │  │
│  │  └──────────────┘  └───────────┘  └─────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Client Layer
- **Web UI**: Vanilla JavaScript application for end users
- **Admin Panel**: Management interface for administrators
- Communicates with backend via REST API

### 2. API Gateway Layer
- **Rate Limiting**: Protects against abuse (30 req/min for analysis, 5/min for auth)
- **CSRF Protection**: Prevents cross-site request forgery
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Request Tracing**: Unique request IDs for debugging

### 3. Application Layer

#### Blueprints (Route Handlers)
Each blueprint handles a specific domain:
- `auth`: Registration, login, logout, password management
- `admin`: Admin panel, site maintenance, user management
- `entries`: Journal CRUD operations
- `detector`: Emotion analysis endpoints
- `lexicon`: Lexicon management and expansion
- `feedback`: User feedback collection
- `site`: Health checks, version info
- `users`: User profile management

#### Services (Business Logic)
- `DetectorService`: Wraps emotion detection engine
- `LexiconService`: Manages lexicon expansion from external APIs

### 4. Repository Layer (Data Access)
Implements the Repository pattern for clean data access:
- `UserRepository`: User CRUD, authentication, password management
- `JournalRepository`: Journal entries, search, export
- `LexiconRepository`: Lexicon word management
- `AuditRepository`: Audit log for security events
- `FeedbackRepository`: User feedback storage

### 5. Data Layer
- **PostgreSQL**: Primary data store with connection pooling
- **Redis**: Optional caching for rate limits and sessions

## Key Design Patterns

### Application Factory
```python
def create_app(config_name: Optional[str] = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app
```

### Repository Pattern
```python
class BaseRepository:
    def find_by_id(self, id: int) -> Optional[Dict]
    def find_all(self) -> List[Dict]
    def create(self, data: Dict) -> Dict
    def update(self, id: int, data: Dict) -> Optional[Dict]
    def delete(self, id: int) -> bool
    def paginate(self, page: int, per_page: int) -> Tuple[List, int, int]
```

### Transaction Management
```python
@transactional
def create_journal_with_analysis(user_id: int, data: Dict) -> Dict:
    journal = journal_repo.create(data)
    audit_repo.log_action(user_id, "create_journal", journal)
    return journal
```

### Validation Schema
```python
CREATE_JOURNAL_SCHEMA = ValidationSchema([
    FieldValidator(name="title", field_type=str, required=True, max_length=200),
    FieldValidator(name="journal_text", field_type=str, required=False),
    FieldValidator(name="source_text", field_type=str, required=False),
])

@bp.route("/", methods=["POST"])
@validate_request(CREATE_JOURNAL_SCHEMA)
def create_journal():
    # Request is already validated
    ...
```

## Security Architecture

### Authentication Flow
```
1. User submits credentials
2. Rate limit check (5 attempts/minute)
3. Account lockout check (5 failed attempts = 15 min lockout)
4. Password verification with bcrypt
5. Session creation with secure cookies
6. Audit log entry
```

### Authorization Model (RBAC)
```python
ROLES = {
    "user": [Permission.READ_OWN, Permission.WRITE_OWN],
    "moderator": [Permission.READ_ANY, Permission.FLAG_CONTENT],
    "admin": [Permission.READ_ANY, Permission.WRITE_ANY, Permission.MANAGE_USERS],
}
```

### Security Headers
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## Emotion Detection Engine

The emotion detector analyzes text using:
1. **Lexicon-based analysis**: Core emotion word matching
2. **Multi-language support**: English, Spanish, Portuguese
3. **External expansion**: Urban Dictionary, Free Dictionary APIs
4. **Self-harm detection**: Keyword-based crisis detection

Output format:
```json
{
  "coreMixture": {
    "joy": 0.45,
    "sadness": 0.15,
    "anger": 0.05,
    "fear": 0.10,
    "disgust": 0.05,
    "surprise": 0.10,
    "passion": 0.10
  },
  "results": {
    "dominant": "joy",
    "current": "happy",
    "confidence": 0.85
  },
  "selfHarmFlag": false
}
```

## Database Schema

### Core Tables
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en',
    preferred_theme VARCHAR(20) DEFAULT 'dark',
    role VARCHAR(20) DEFAULT 'user',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Journals table
CREATE TABLE journals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    journal_text TEXT,
    source_text TEXT,
    analysis_json JSONB,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration Management

### Environment-Specific Configs
```
BaseConfig          # Shared settings
├── DevelopmentConfig   # Debug mode, relaxed security
├── StagingConfig       # Production-like with debug tools
├── ProductionConfig    # Full security, optimized
└── TestingConfig       # In-memory DB, fast tests
```

### Required Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=<32+ random characters>
ADMIN_USERNAME=<admin username>
ADMIN_PASSWORD_HASH=<bcrypt hash>
DEV_PASSWORD_HASH=<bcrypt hash>
```

## Deployment Architecture

### Production Setup
```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   Nginx     │────▶│   Gunicorn   │────▶│  PostgreSQL    │
│  (Reverse   │     │  (4 workers) │     │  (Primary)     │
│   Proxy)    │     │              │     │                │
└─────────────┘     └──────────────┘     └────────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌────────────────┐
                    │    Redis     │     │  PostgreSQL    │
                    │   (Cache)    │     │  (Replica)     │
                    └──────────────┘     └────────────────┘
```

### Scaling Considerations
- **Horizontal scaling**: Multiple Gunicorn instances behind load balancer
- **Database**: Read replicas for query offloading
- **Caching**: Redis for session storage and rate limits
- **Static assets**: CDN for frontend files

## Monitoring & Observability

### Logging
- Structured JSON logs in production
- Request ID tracing across all log entries
- Sensitive data redaction (passwords, tokens)

### Health Checks
```
GET /api/health
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "uptime": "12h 34m"
}
```

### Metrics (Future)
- Request latency (p50, p95, p99)
- Error rates by endpoint
- Database query times
- Cache hit rates
