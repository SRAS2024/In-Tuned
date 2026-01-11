# app/config.py
"""
Application Configuration

This module defines configuration classes for different environments
and provides a strict configuration loader that fails fast if required
environment variables are missing.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional, Type


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


def get_required_env(name: str, description: str = "") -> str:
    """
    Get a required environment variable or raise ConfigurationError.

    Args:
        name: Environment variable name
        description: Human-readable description for error messages

    Returns:
        The environment variable value

    Raises:
        ConfigurationError: If the variable is not set
    """
    value = os.environ.get(name)
    if not value:
        desc = f" ({description})" if description else ""
        raise ConfigurationError(
            f"Required environment variable {name}{desc} is not set. "
            f"Please set it in your environment or .env file."
        )
    return value


def get_optional_env(name: str, default: str = "") -> str:
    """Get an optional environment variable with a default value."""
    return os.environ.get(name, default)


def get_bool_env(name: str, default: bool = False) -> bool:
    """Get a boolean environment variable."""
    value = os.environ.get(name, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def get_int_env(name: str, default: int = 0) -> int:
    """Get an integer environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_list_env(name: str, default: Optional[List[str]] = None, separator: str = ",") -> List[str]:
    """Get a list environment variable (comma-separated by default)."""
    value = os.environ.get(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


class BaseConfig:
    """Base configuration with common settings."""

    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    TESTING: bool = False

    # Application
    APP_NAME: str = "In-Tuned"
    APP_VERSION: str = "2.0.0"

    # Secret key - MUST be set in production
    SECRET_KEY: str = ""

    # Database
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Session settings
    SESSION_COOKIE_NAME: str = "intuned_session"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST: bool = True

    # CSRF protection
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = 3600  # 1 hour

    # Rate limiting
    RATELIMIT_ENABLED: bool = True
    RATELIMIT_DEFAULT: str = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL: str = "memory://"
    RATELIMIT_STRATEGY: str = "fixed-window"
    RATELIMIT_HEADERS_ENABLED: bool = True

    # Rate limits for specific endpoints
    RATELIMIT_LOGIN: str = "5 per minute, 20 per hour"
    RATELIMIT_PASSWORD_RESET: str = "3 per minute, 10 per hour"
    RATELIMIT_REGISTER: str = "3 per minute, 10 per hour"
    RATELIMIT_ANALYZE: str = "30 per minute, 200 per hour"

    # Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    BCRYPT_LOG_ROUNDS: int = 12

    # File uploads
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    UPLOAD_ALLOWED_EXTENSIONS: List[str] = field(
        default_factory=lambda: ["json", "csv", "txt"]
    )
    UPLOAD_FOLDER: str = "/tmp/uploads"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_REDACT_SECRETS: bool = True

    # API
    API_TOKEN: str = ""  # Token for API access
    API_PAGINATION_DEFAULT: int = 20
    API_PAGINATION_MAX: int = 100

    # Admin credentials (from environment)
    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD_HASH: str = ""  # Store hash, not plain text
    DEV_PASSWORD_HASH: str = ""  # For maintenance mode

    # CORS
    CORS_ORIGINS: List[str] = field(default_factory=list)

    # Security headers
    SECURITY_HEADERS: Dict[str, str] = field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
    )

    # Content Security Policy
    CSP_POLICY: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],
            "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "img-src": ["'self'", "data:", "https:"],
            "connect-src": ["'self'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
        }
    )

    # Cache
    CACHE_TYPE: str = "simple"
    CACHE_DEFAULT_TIMEOUT: int = 300
    CACHE_KEY_PREFIX: str = "intuned_"

    # Background jobs
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        self._load_from_env()
        self._validate()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Required in all environments
        self.DATABASE_URL = get_required_env(
            "DATABASE_URL", "PostgreSQL connection string"
        )

        # Secret key - required in production, generated for dev
        secret = os.environ.get("SECRET_KEY")
        if secret:
            self.SECRET_KEY = secret
        elif self.ENV == "production":
            raise ConfigurationError(
                "SECRET_KEY must be set in production environment"
            )
        else:
            # Generate a random key for development
            self.SECRET_KEY = secrets.token_hex(32)

        # Admin credentials from environment
        self.ADMIN_USERNAME = get_optional_env("ADMIN_USERNAME", "")
        self.ADMIN_PASSWORD_HASH = get_optional_env("ADMIN_PASSWORD_HASH", "")
        self.DEV_PASSWORD_HASH = get_optional_env("DEV_PASSWORD_HASH", "")

        # API token
        self.API_TOKEN = get_optional_env("API_TOKEN", "")

        # Optional overrides
        self.LOG_LEVEL = get_optional_env("LOG_LEVEL", self.LOG_LEVEL)
        self.DATABASE_POOL_SIZE = get_int_env("DATABASE_POOL_SIZE", self.DATABASE_POOL_SIZE)

        # Rate limiting storage
        self.RATELIMIT_STORAGE_URL = get_optional_env(
            "REDIS_URL", self.RATELIMIT_STORAGE_URL
        )

        # CORS origins
        self.CORS_ORIGINS = get_list_env("CORS_ORIGINS", self.CORS_ORIGINS)

    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.DATABASE_URL:
            raise ConfigurationError("DATABASE_URL is required")

        if self.ENV == "production":
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ConfigurationError(
                    "SECRET_KEY must be at least 32 characters in production"
                )
            if not self.ADMIN_USERNAME:
                raise ConfigurationError(
                    "ADMIN_USERNAME must be set in production"
                )
            if not self.ADMIN_PASSWORD_HASH:
                raise ConfigurationError(
                    "ADMIN_PASSWORD_HASH must be set in production"
                )


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    ENV = "development"
    DEBUG = True

    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False

    # More verbose logging
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "text"

    # Allow any origin in development
    CORS_ORIGINS = ["*"]

    def _validate(self) -> None:
        """Development has relaxed validation."""
        if not self.DATABASE_URL:
            raise ConfigurationError("DATABASE_URL is required even in development")


class StagingConfig(BaseConfig):
    """Staging environment configuration."""

    ENV = "staging"
    DEBUG = False

    # Secure but with some relaxations for testing
    SESSION_COOKIE_SECURE = True
    RATELIMIT_ENABLED = True

    LOG_LEVEL = "INFO"
    LOG_FORMAT = "json"


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    ENV = "production"
    DEBUG = False

    # Strict security
    SESSION_COOKIE_SECURE = True
    RATELIMIT_ENABLED = True
    BCRYPT_LOG_ROUNDS = 14  # Higher for production

    LOG_LEVEL = "WARNING"
    LOG_FORMAT = "json"

    # HSTS settings
    SECURITY_HEADERS = {
        **BaseConfig.SECURITY_HEADERS.__func__(None),  # type: ignore
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    }


class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    ENV = "testing"
    DEBUG = True
    TESTING = True

    # Use test database
    DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/intuned_test")

    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False

    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

    # Don't require HTTPS
    SESSION_COOKIE_SECURE = False

    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "text"

    def _validate(self) -> None:
        """Testing has minimal validation."""
        pass


# Configuration mapping
CONFIG_MAP: Dict[str, Type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(config_name: Optional[str] = None) -> BaseConfig:
    """
    Get configuration instance for the specified environment.

    Args:
        config_name: Environment name. If None, uses APP_ENV env var or 'development'.

    Returns:
        Configuration instance for the specified environment.

    Raises:
        ConfigurationError: If the specified environment is invalid.
    """
    if config_name is None:
        config_name = os.environ.get("APP_ENV", "development")

    config_name = config_name.lower()

    if config_name not in CONFIG_MAP:
        valid = ", ".join(CONFIG_MAP.keys())
        raise ConfigurationError(
            f"Invalid configuration environment '{config_name}'. "
            f"Valid options are: {valid}"
        )

    return CONFIG_MAP[config_name]()
