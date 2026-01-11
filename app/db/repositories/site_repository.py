# app/db/repositories/site_repository.py
"""
Site Repository

Provides data access methods for site settings and notices.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.db.repositories.base import BaseRepository


class SiteRepository(BaseRepository):
    """Repository for site settings and notices."""

    table_name = "site_settings"
    primary_key = "id"

    def get_settings(self) -> Dict[str, Any]:
        """Get the site settings (single row, id=1)."""
        query = """
            SELECT maintenance_mode, maintenance_message
            FROM site_settings
            WHERE id = 1
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            result = cur.fetchone()
            if not result:
                # Initialize if not exists
                return self._initialize_settings()
            return result
        finally:
            cur.close()

    def _initialize_settings(self) -> Dict[str, Any]:
        """Initialize the site settings row if it doesn't exist."""
        query = """
            INSERT INTO site_settings (id, maintenance_mode, maintenance_message)
            VALUES (1, FALSE, NULL)
            ON CONFLICT (id) DO NOTHING
            RETURNING maintenance_mode, maintenance_message
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            result = cur.fetchone()
            self.conn.commit()
            return result or {"maintenance_mode": False, "maintenance_message": None}
        except Exception:
            self.conn.rollback()
            return {"maintenance_mode": False, "maintenance_message": None}
        finally:
            cur.close()

    def update_maintenance(
        self, enabled: bool, message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update maintenance mode settings."""
        default_message = "Site is currently down due to maintenance. We will be back shortly."

        query = """
            UPDATE site_settings
            SET maintenance_mode = %s,
                maintenance_message = %s
            WHERE id = 1
            RETURNING maintenance_mode, maintenance_message
        """

        cur = self.cursor()
        try:
            cur.execute(query, (enabled, message or default_message))
            result = cur.fetchone()
            self.conn.commit()
            return result or {}
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def get_active_notice(self) -> Optional[Dict[str, Any]]:
        """Get the currently active notice."""
        query = """
            SELECT id, text
            FROM notices
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            return cur.fetchone()
        finally:
            cur.close()

    def get_all_notices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all notices ordered by creation date."""
        query = """
            SELECT id, text, is_active, created_at
            FROM notices
            ORDER BY created_at DESC
            LIMIT %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (limit,))
            return cur.fetchall()
        finally:
            cur.close()

    def create_notice(self, text: str, is_active: bool = True) -> Dict[str, Any]:
        """Create a new notice."""
        # If this notice is active, deactivate all others first
        if is_active:
            deactivate_query = """
                UPDATE notices
                SET is_active = FALSE
                WHERE is_active = TRUE
            """
            cur = self.cursor()
            try:
                cur.execute(deactivate_query)
            finally:
                cur.close()

        query = """
            INSERT INTO notices (text, is_active)
            VALUES (%s, %s)
            RETURNING id, text, is_active, created_at
        """

        cur = self.cursor()
        try:
            cur.execute(query, (text, is_active))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def update_notice(self, notice_id: int, is_active: bool) -> Optional[Dict[str, Any]]:
        """Update notice active status."""
        query = """
            UPDATE notices
            SET is_active = %s
            WHERE id = %s
            RETURNING id, text, is_active, created_at
        """

        cur = self.cursor()
        try:
            cur.execute(query, (is_active, notice_id))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def delete_notice(self, notice_id: int) -> bool:
        """Delete a notice."""
        query = "DELETE FROM notices WHERE id = %s RETURNING id"

        cur = self.cursor()
        try:
            cur.execute(query, (notice_id,))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def get_site_state(self) -> Dict[str, Any]:
        """Get combined site state including maintenance mode and active notice."""
        settings = self.get_settings()
        notice = self.get_active_notice()

        return {
            "maintenance_mode": settings.get("maintenance_mode", False),
            "maintenance_message": settings.get("maintenance_message"),
            "notice": notice,
        }
