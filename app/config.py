# app/config.py
"""
Application Configuration

This module defines configuration classes for different environments.
Uses sensible defaults for development while allowing environment variable overrides.
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

    # Secret key - defaults for development, should override in production
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Session settings
    SESSION_COOKIE_NAME: str = "intuned_session"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = False  # Set True in production with HTTPS
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST: bool = True

    # CSRF protection
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = 3600  # 1 hour

    # Rate limiting - disabled by default for compatibility
    RATELIMIT_ENABLED: bool = False
    RATELIMIT_DEFAULT: str = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL: str = "memory://"
    RATELIMIT_STRATEGY: str = "fixed-window"
    RATELIMIT_HEADERS_ENABLED: bool = True

    # Rate limits for specific endpoints
    RATELIMIT_LOGIN: str = "5 per minute, 20 per hour"
    RATELIMIT_PASSWORD_RESET: str = "3 per minute, 10 per hour"
    RATELIMIT_REGISTER: str = "3 per minute, 10 per hour"
    RATELIMIT_ANALYZE: str = "30 per minute, 200 per hour"

    # Security - relaxed defaults for backwards compatibility
    PASSWORD_MIN_LENGTH: int = 1  # Original had no min length
    PASSWORD_REQUIRE_UPPERCASE: bool = False
    PASSWORD_REQUIRE_LOWERCASE: bool = False
    PASSWORD_REQUIRE_DIGIT: bool = False
    PASSWORD_REQUIRE_SPECIAL: bool = False
    MAX_LOGIN_ATTEMPTS: int = 0  # 0 = no lockout
    LOCKOUT_DURATION_MINUTES: int = 15
    BCRYPT_LOG_ROUNDS: int = 12

    # File uploads
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER: str = "/tmp/uploads"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # text for development
    LOG_REDACT_SECRETS: bool = True

    # API
    API_TOKEN: str = ""
    API_PAGINATION_DEFAULT: int = 20
    API_PAGINATION_MAX: int = 100

    # Admin credentials - defaults matching original server.py
    # These can be overridden via environment variables for production
    ADMIN_USERNAME: str = "Ryan Simonds"
    ADMIN_PASSWORD: str = "Santidade"  # Plain text for backwards compatibility
    DEV_PASSWORD: str = "Meu Amor Maria"  # Plain text for backwards compatibility

    # CORS
    CORS_ORIGINS: List[str] = []

    # Security headers
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # Content Security Policy
    CSP_POLICY: Dict[str, List[str]] = {
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

    # Cache
    CACHE_TYPE: str = "simple"
    CACHE_DEFAULT_TIMEOUT: int = 300
    CACHE_KEY_PREFIX: str = "intuned_"

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Database URL - required
        self.DATABASE_URL = os.environ.get("DATABASE_URL", "")
        if not self.DATABASE_URL:
            raise ConfigurationError(
                "DATABASE_URL environment variable is not set. "
                "Set it in Railway to the provided Postgres connection URL."
            )

        # Secret key - use env var if set, otherwise use default
        self.SECRET_KEY = os.environ.get("SECRET_KEY", self.SECRET_KEY)

        # Admin credentials - can be overridden via env vars
        self.ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", self.ADMIN_USERNAME)
        self.ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", self.ADMIN_PASSWORD)
        self.DEV_PASSWORD = os.environ.get("DEV_PASSWORD", self.DEV_PASSWORD)

        # Optional overrides
        self.LOG_LEVEL = get_optional_env("LOG_LEVEL", self.LOG_LEVEL)
        self.DATABASE_POOL_SIZE = get_int_env("DATABASE_POOL_SIZE", self.DATABASE_POOL_SIZE)

        # Rate limiting - enable via env var
        self.RATELIMIT_ENABLED = get_bool_env("RATELIMIT_ENABLED", self.RATELIMIT_ENABLED)
        self.RATELIMIT_STORAGE_URL = get_optional_env("REDIS_URL", self.RATELIMIT_STORAGE_URL)

        # CORS origins
        self.CORS_ORIGINS = get_list_env("CORS_ORIGINS", self.CORS_ORIGINS)


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


class StagingConfig(BaseConfig):
    """Staging environment configuration."""

    ENV = "staging"
    DEBUG = False

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
    BCRYPT_LOG_ROUNDS = 14

    # Stronger password requirements in production
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    MAX_LOGIN_ATTEMPTS = 5

    LOG_LEVEL = "WARNING"
    LOG_FORMAT = "json"

    # HSTS settings
    SECURITY_HEADERS = {
        **BaseConfig.SECURITY_HEADERS,
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

    SESSION_COOKIE_SECURE = False

    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "text"

    def _load_from_env(self) -> None:
        """Testing config doesn't require DATABASE_URL from env."""
        self.DATABASE_URL = os.environ.get("DATABASE_URL", self.DATABASE_URL)
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")


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
        config_name = os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development"))

    config_name = config_name.lower()

    if config_name not in CONFIG_MAP:
        valid = ", ".join(CONFIG_MAP.keys())
        raise ConfigurationError(
            f"Invalid configuration environment '{config_name}'. "
            f"Valid options are: {valid}"
        )

    return CONFIG_MAP[config_name]()
