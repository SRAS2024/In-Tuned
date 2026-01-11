# app/db/repositories/feedback_repository.py
"""
Feedback Repository

Provides data access methods for feedback submissions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from psycopg.types.json import Jsonb

from app.db.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository):
    """Repository for feedback data access."""

    table_name = "feedback"
    primary_key = "id"

    def create_feedback(
        self,
        entry_text: str,
        feedback_text: str,
        analysis_json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new feedback entry."""
        query = """
            INSERT INTO feedback (entry_text, analysis_json, feedback_text)
            VALUES (%s, %s, %s)
            RETURNING id, created_at
        """

        json_payload = Jsonb(analysis_json) if analysis_json else None

        cur = self.cursor()
        try:
            cur.execute(query, (entry_text, json_payload, feedback_text))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def get_all_feedback(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get all feedback entries ordered by creation date."""
        query = """
            SELECT id, entry_text, analysis_json, feedback_text, created_at
            FROM feedback
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (limit, offset))
            return cur.fetchall()
        finally:
            cur.close()

    def get_feedback_count(self) -> int:
        """Get total feedback count."""
        query = "SELECT COUNT(*) as count FROM feedback"
        cur = self.cursor()
        try:
            cur.execute(query)
            result = cur.fetchone()
            return result["count"] if result else 0
        finally:
            cur.close()

    def delete_all_feedback(self) -> int:
        """Delete all feedback entries and return count."""
        query = "DELETE FROM feedback RETURNING id"
        cur = self.cursor()
        try:
            cur.execute(query)
            count = cur.rowcount
            self.conn.commit()
            return count
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def get_feedback_for_export(self) -> List[Dict[str, Any]]:
        """Get all feedback for export."""
        query = """
            SELECT id, entry_text, analysis_json, feedback_text, created_at
            FROM feedback
            ORDER BY created_at DESC
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            return cur.fetchall()
        finally:
            cur.close()

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        query = """
            SELECT
                COUNT(*) as total,
                MIN(created_at) as earliest,
                MAX(created_at) as latest,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_week,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as last_month
            FROM feedback
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            return cur.fetchone() or {}
        finally:
            cur.close()
