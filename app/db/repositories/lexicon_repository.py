# app/db/repositories/lexicon_repository.py
"""
Lexicon Repository

Provides data access methods for lexicon file management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from psycopg import Binary

from app.db.repositories.base import BaseRepository


class LexiconRepository(BaseRepository):
    """Repository for lexicon data access."""

    table_name = "lexicon_files"
    primary_key = "id"

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all lexicon files (metadata only, no content)."""
        query = """
            SELECT id, language, filename, content_type, uploaded_at
            FROM lexicon_files
            ORDER BY uploaded_at DESC
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            return cur.fetchall()
        finally:
            cur.close()

    def get_files_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get all lexicon files for a specific language."""
        query = """
            SELECT id, language, filename, content_type, uploaded_at
            FROM lexicon_files
            WHERE language = %s
            ORDER BY uploaded_at DESC
        """

        cur = self.cursor()
        try:
            cur.execute(query, (language,))
            return cur.fetchall()
        finally:
            cur.close()

    def get_file_with_content(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get a lexicon file including its binary content."""
        query = """
            SELECT id, language, filename, content_type, data, uploaded_at
            FROM lexicon_files
            WHERE id = %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (file_id,))
            return cur.fetchone()
        finally:
            cur.close()

    def upload_file(
        self,
        language: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> Dict[str, Any]:
        """Upload a new lexicon file."""
        query = """
            INSERT INTO lexicon_files (language, filename, content_type, data)
            VALUES (%s, %s, %s, %s)
            RETURNING id, language, filename, content_type, uploaded_at
        """

        cur = self.cursor()
        try:
            cur.execute(query, (language, filename, content_type, Binary(data)))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def delete_file(self, file_id: int) -> bool:
        """Delete a lexicon file."""
        query = "DELETE FROM lexicon_files WHERE id = %s RETURNING id"

        cur = self.cursor()
        try:
            cur.execute(query, (file_id,))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get lexicon file statistics."""
        query = """
            SELECT
                COUNT(*) as total_files,
                COUNT(*) FILTER (WHERE language = 'en') as english_files,
                COUNT(*) FILTER (WHERE language = 'es') as spanish_files,
                COUNT(*) FILTER (WHERE language = 'pt') as portuguese_files,
                SUM(LENGTH(data)) as total_size_bytes
            FROM lexicon_files
        """

        cur = self.cursor()
        try:
            cur.execute(query)
            return cur.fetchone() or {}
        finally:
            cur.close()
