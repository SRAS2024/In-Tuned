# app/db/repositories/journal_repository.py
"""
Journal Repository

Provides data access methods for journal entries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from psycopg.types.json import Jsonb

from app.db.repositories.base import BaseRepository


class JournalRepository(BaseRepository):
    """Repository for journal data access."""

    table_name = "journals"
    primary_key = "id"

    def find_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        include_content: bool = False,
    ) -> List[Dict[str, Any]]:
        """Find all journals for a user, ordered by pinned status and date."""
        if include_content:
            columns = "*"
        else:
            columns = """
                id, title, created_at, updated_at,
                is_pinned, has_self_harm_flag
            """

        query = f"""
            SELECT {columns}
            FROM journals
            WHERE user_id = %s
            ORDER BY is_pinned DESC, created_at DESC
            LIMIT %s OFFSET %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (user_id, limit, offset))
            return cur.fetchall()
        finally:
            cur.close()

    def find_by_user_and_id(
        self, user_id: int, journal_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find a specific journal by user and journal ID."""
        query = """
            SELECT * FROM journals
            WHERE id = %s AND user_id = %s
        """
        cur = self.cursor()
        try:
            cur.execute(query, (journal_id, user_id))
            return cur.fetchone()
        finally:
            cur.close()

    def create_journal(
        self,
        user_id: int,
        title: str,
        source_text: Optional[str] = None,
        analysis_json: Optional[Dict[str, Any]] = None,
        journal_text: Optional[str] = None,
        has_self_harm_flag: bool = False,
    ) -> Dict[str, Any]:
        """Create a new journal entry."""
        query = """
            INSERT INTO journals (
                user_id, title, source_text, analysis_json,
                journal_text, has_self_harm_flag
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        json_payload = Jsonb(analysis_json) if analysis_json else None

        cur = self.cursor()
        try:
            cur.execute(
                query,
                (
                    user_id,
                    title,
                    source_text,
                    json_payload,
                    journal_text or "",
                    has_self_harm_flag,
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

    def update_journal(
        self,
        user_id: int,
        journal_id: int,
        title: Optional[str] = None,
        journal_text: Optional[str] = None,
        has_self_harm_flag: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a journal entry."""
        query = """
            UPDATE journals
            SET title = COALESCE(%s, title),
                journal_text = COALESCE(%s, journal_text),
                has_self_harm_flag = COALESCE(%s, has_self_harm_flag),
                updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING *
        """

        cur = self.cursor()
        try:
            cur.execute(
                query,
                (title, journal_text, has_self_harm_flag, journal_id, user_id),
            )
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def delete_journal(self, user_id: int, journal_id: int) -> bool:
        """Delete a journal entry."""
        query = """
            DELETE FROM journals
            WHERE id = %s AND user_id = %s
            RETURNING id
        """

        cur = self.cursor()
        try:
            cur.execute(query, (journal_id, user_id))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def toggle_pin(
        self, user_id: int, journal_id: int, is_pinned: bool
    ) -> Optional[Dict[str, Any]]:
        """Toggle the pinned status of a journal."""
        query = """
            UPDATE journals
            SET is_pinned = %s, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id, title, created_at, updated_at, is_pinned, has_self_harm_flag
        """

        cur = self.cursor()
        try:
            cur.execute(query, (is_pinned, journal_id, user_id))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def count_by_user(self, user_id: int) -> int:
        """Count journals for a user."""
        query = "SELECT COUNT(*) as count FROM journals WHERE user_id = %s"
        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            return result["count"] if result else 0
        finally:
            cur.close()

    def search_journals(
        self,
        user_id: int,
        search_term: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search journals by title or content."""
        query = """
            SELECT id, title, created_at, updated_at, is_pinned, has_self_harm_flag
            FROM journals
            WHERE user_id = %s
              AND (title ILIKE %s OR journal_text ILIKE %s OR source_text ILIKE %s)
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """

        search_pattern = f"%{search_term}%"

        cur = self.cursor()
        try:
            cur.execute(
                query,
                (user_id, search_pattern, search_pattern, search_pattern, limit, offset),
            )
            return cur.fetchall()
        finally:
            cur.close()

    def get_journals_with_self_harm_flags(
        self, user_id: int
    ) -> List[Dict[str, Any]]:
        """Get all journals with self-harm flags for a user."""
        query = """
            SELECT id, title, created_at, updated_at, is_pinned, has_self_harm_flag
            FROM journals
            WHERE user_id = %s AND has_self_harm_flag = TRUE
            ORDER BY created_at DESC
        """

        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            return cur.fetchall()
        finally:
            cur.close()

    def get_date_range_journals(
        self,
        user_id: int,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Get journals within a date range."""
        query = """
            SELECT * FROM journals
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at <= %s
            ORDER BY created_at DESC
        """

        cur = self.cursor()
        try:
            cur.execute(query, (user_id, start_date, end_date))
            return cur.fetchall()
        finally:
            cur.close()

    def get_user_journal_stats(self, user_id: int) -> Dict[str, Any]:
        """Get journal statistics for a user."""
        query = """
            SELECT
                COUNT(*) as total_entries,
                COUNT(*) FILTER (WHERE is_pinned = TRUE) as pinned_count,
                COUNT(*) FILTER (WHERE has_self_harm_flag = TRUE) as flagged_count,
                MIN(created_at) as first_entry,
                MAX(created_at) as last_entry,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as entries_this_week,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as entries_this_month
            FROM journals
            WHERE user_id = %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            return cur.fetchone() or {}
        finally:
            cur.close()

    def export_journals(
        self,
        user_id: int,
        include_analysis: bool = True,
    ) -> List[Dict[str, Any]]:
        """Export all journals for a user."""
        if include_analysis:
            columns = "*"
        else:
            columns = """
                id, title, source_text, journal_text,
                is_pinned, has_self_harm_flag, created_at, updated_at
            """

        query = f"""
            SELECT {columns} FROM journals
            WHERE user_id = %s
            ORDER BY created_at ASC
        """

        cur = self.cursor()
        try:
            cur.execute(query, (user_id,))
            return cur.fetchall()
        finally:
            cur.close()
