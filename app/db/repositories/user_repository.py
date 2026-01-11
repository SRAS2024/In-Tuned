# app/db/repositories/user_repository.py
"""
User Repository

Provides data access methods for user management.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from werkzeug.security import generate_password_hash, check_password_hash

from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user data access."""

    table_name = "users"
    primary_key = "id"

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email address."""
        query = "SELECT * FROM users WHERE lower(email) = lower(%s)"
        cur = self.cursor()
        try:
            cur.execute(query, (email,))
            return cur.fetchone()
        finally:
            cur.close()

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find a user by username."""
        query = "SELECT * FROM users WHERE lower(username) = lower(%s)"
        cur = self.cursor()
        try:
            cur.execute(query, (username,))
            return cur.fetchone()
        finally:
            cur.close()

    def find_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find a user by email or username."""
        query = """
            SELECT * FROM users
            WHERE lower(email) = lower(%s) OR lower(username) = lower(%s)
        """
        cur = self.cursor()
        try:
            cur.execute(query, (identifier, identifier))
            return cur.fetchone()
        finally:
            cur.close()

    def create_user(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
        preferred_language: str = "en",
        preferred_theme: str = "dark",
    ) -> Dict[str, Any]:
        """Create a new user with hashed password."""
        password_hash = generate_password_hash(password)

        query = """
            INSERT INTO users (
                first_name, last_name, username, email, password_hash,
                preferred_language, preferred_theme
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        cur = self.cursor()
        try:
            cur.execute(
                query,
                (
                    first_name,
                    last_name,
                    username,
                    email.lower(),
                    password_hash,
                    preferred_language,
                    preferred_theme,
                ),
            )
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def verify_password(self, user: Dict[str, Any], password: str) -> bool:
        """Verify a user's password."""
        if not user or not user.get("password_hash"):
            return False
        return check_password_hash(user["password_hash"], password)

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update a user's password."""
        password_hash = generate_password_hash(new_password)

        query = """
            UPDATE users
            SET password_hash = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """

        cur = self.cursor()
        try:
            cur.execute(query, (password_hash, user_id))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def update_preferences(
        self,
        user_id: int,
        preferred_language: Optional[str] = None,
        preferred_theme: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update user preferences."""
        query = """
            UPDATE users
            SET preferred_language = COALESCE(%s, preferred_language),
                preferred_theme = COALESCE(%s, preferred_theme),
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """

        cur = self.cursor()
        try:
            cur.execute(query, (preferred_language, preferred_theme, user_id))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def email_or_username_exists(self, email: str, username: str) -> bool:
        """Check if email or username already exists."""
        query = """
            SELECT 1 FROM users
            WHERE lower(email) = lower(%s) OR lower(username) = lower(%s)
        """
        cur = self.cursor()
        try:
            cur.execute(query, (email, username))
            return cur.fetchone() is not None
        finally:
            cur.close()

    def find_by_identity_verification(
        self, email: str, first_name: str, last_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find user by email and name for password reset verification."""
        query = """
            SELECT * FROM users
            WHERE lower(email) = lower(%s)
              AND lower(first_name) = lower(%s)
              AND lower(last_name) = lower(%s)
        """
        cur = self.cursor()
        try:
            cur.execute(query, (email, first_name, last_name))
            return cur.fetchone()
        finally:
            cur.close()

    def increment_failed_login(self, user_id: int) -> int:
        """Increment failed login count and return new count."""
        query = """
            UPDATE users
            SET failed_login_attempts = COALESCE(failed_login_attempts, 0) + 1,
                last_failed_login = NOW()
            WHERE id = %s
            RETURNING failed_login_attempts
        """
        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            self.conn.commit()
            return result["failed_login_attempts"] if result else 0
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def reset_failed_login(self, user_id: int) -> None:
        """Reset failed login attempts after successful login."""
        query = """
            UPDATE users
            SET failed_login_attempts = 0,
                last_failed_login = NULL,
                last_login = NOW()
            WHERE id = %s
        """
        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def is_locked_out(self, user_id: int, lockout_minutes: int = 15) -> bool:
        """Check if user is locked out due to failed login attempts."""
        query = """
            SELECT failed_login_attempts, last_failed_login
            FROM users
            WHERE id = %s
        """
        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            if not result:
                return False

            attempts = result.get("failed_login_attempts", 0)
            last_failed = result.get("last_failed_login")

            if attempts < 5:  # Max attempts before lockout
                return False

            if last_failed is None:
                return False

            # Check if lockout period has passed
            lockout_until = last_failed + timedelta(minutes=lockout_minutes)
            return datetime.now(last_failed.tzinfo) < lockout_until
        finally:
            cur.close()

    def update_email(self, user_id: int, new_email: str) -> Optional[Dict[str, Any]]:
        """Update user's email address."""
        query = """
            UPDATE users
            SET email = lower(%s), updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        cur = self.cursor()
        try:
            cur.execute(query, (new_email, user_id))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def disable_user(self, user_id: int, reason: str = "") -> bool:
        """Disable a user account."""
        query = """
            UPDATE users
            SET is_active = FALSE,
                disabled_at = NOW(),
                disabled_reason = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        cur = self.cursor()
        try:
            cur.execute(query, (reason, user_id))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def enable_user(self, user_id: int) -> bool:
        """Enable a disabled user account."""
        query = """
            UPDATE users
            SET is_active = TRUE,
                disabled_at = NULL,
                disabled_reason = NULL,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics."""
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_active = TRUE) as active,
                COUNT(*) FILTER (WHERE is_active = FALSE) as disabled,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_this_week,
                COUNT(*) FILTER (WHERE last_login > NOW() - INTERVAL '7 days') as active_this_week
            FROM users
        """
        cur = self.cursor()
        try:
            cur.execute(query)
            return cur.fetchone() or {}
        finally:
            cur.close()

    @staticmethod
    def to_safe_payload(user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert user record to safe payload (without sensitive fields)."""
        if not user:
            return {}

        return {
            "id": user.get("id"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "username": user.get("username"),
            "email": user.get("email"),
            "preferred_language": user.get("preferred_language", "en"),
            "preferred_theme": user.get("preferred_theme", "dark"),
            "created_at": user.get("created_at"),
            "is_active": user.get("is_active", True),
        }
