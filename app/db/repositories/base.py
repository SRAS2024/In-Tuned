# app/db/repositories/base.py
"""
Base Repository

This module provides the base repository class with common CRUD operations.
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, TypeVar, Tuple

from flask import g
import psycopg
from psycopg.types.json import Jsonb

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository class providing common CRUD operations.

    Subclasses should define:
        - table_name: The database table name
        - primary_key: The primary key column name (default: 'id')
    """

    table_name: str = ""
    primary_key: str = "id"

    def __init__(self, conn: Optional[psycopg.Connection] = None):
        """
        Initialize repository with optional connection.

        If no connection is provided, uses the request-scoped connection.
        """
        self._conn = conn

    @property
    def conn(self) -> psycopg.Connection:
        """Get the database connection."""
        if self._conn is not None:
            return self._conn
        # Lazily initialize connection if not already done
        if not hasattr(g, "db") or g.db is None:
            from app.db.connection import get_db_connection
            g.db = get_db_connection()
        return g.db

    def cursor(self) -> psycopg.Cursor:
        """Get a new cursor."""
        return self.conn.cursor()

    def find_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """Find a record by its primary key."""
        query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s"
        cur = self.cursor()
        try:
            cur.execute(query, (id,))
            return cur.fetchone()
        finally:
            cur.close()

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_dir: str = "ASC",
    ) -> List[Dict[str, Any]]:
        """Find all records with pagination."""
        order_clause = ""
        if order_by:
            # Validate order_dir to prevent SQL injection
            order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
            order_clause = f"ORDER BY {order_by} {order_dir}"

        query = f"""
            SELECT * FROM {self.table_name}
            {order_clause}
            LIMIT %s OFFSET %s
        """
        cur = self.cursor()
        try:
            cur.execute(query, (limit, offset))
            return cur.fetchall()
        finally:
            cur.close()

    def find_by(
        self,
        conditions: Dict[str, Any],
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_dir: str = "ASC",
    ) -> List[Dict[str, Any]]:
        """Find records matching the given conditions."""
        if not conditions:
            return self.find_all(limit=limit or 100, offset=offset)

        # Build WHERE clause
        where_parts = []
        values = []
        for key, value in conditions.items():
            if value is None:
                where_parts.append(f"{key} IS NULL")
            else:
                where_parts.append(f"{key} = %s")
                values.append(value)

        where_clause = " AND ".join(where_parts)

        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
            order_clause = f"ORDER BY {order_by} {order_dir}"

        # Build LIMIT/OFFSET clause
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT %s OFFSET %s"
            values.extend([limit, offset])

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            {order_clause}
            {limit_clause}
        """

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values))
            return cur.fetchall()
        finally:
            cur.close()

    def find_one_by(self, conditions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single record matching the given conditions."""
        results = self.find_by(conditions, limit=1)
        return results[0] if results else None

    def count(self, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Count records, optionally filtered by conditions."""
        if not conditions:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            values = ()
        else:
            where_parts = []
            values = []
            for key, value in conditions.items():
                if value is None:
                    where_parts.append(f"{key} IS NULL")
                else:
                    where_parts.append(f"{key} = %s")
                    values.append(value)
            where_clause = " AND ".join(where_parts)
            query = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE {where_clause}"
            values = tuple(values)

        cur = self.cursor()
        try:
            cur.execute(query, values)
            result = cur.fetchone()
            return result["count"] if result else 0
        finally:
            cur.close()

    def exists(self, conditions: Dict[str, Any]) -> bool:
        """Check if any record matches the given conditions."""
        return self.count(conditions) > 0

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        if not data:
            raise ValueError("Cannot create record with empty data")

        columns = list(data.keys())
        values = []
        placeholders = []

        for key, value in data.items():
            if isinstance(value, dict):
                values.append(Jsonb(value))
                placeholders.append("%s")
            else:
                values.append(value)
                placeholders.append("%s")

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its primary key."""
        if not data:
            return self.find_by_id(id)

        set_parts = []
        values = []

        for key, value in data.items():
            if isinstance(value, dict):
                set_parts.append(f"{key} = %s")
                values.append(Jsonb(value))
            else:
                set_parts.append(f"{key} = %s")
                values.append(value)

        values.append(id)

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_parts)}, updated_at = NOW()
            WHERE {self.primary_key} = %s
            RETURNING *
        """

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values))
            result = cur.fetchone()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def delete(self, id: Any) -> bool:
        """Delete a record by its primary key."""
        query = f"""
            DELETE FROM {self.table_name}
            WHERE {self.primary_key} = %s
            RETURNING {self.primary_key}
        """

        cur = self.cursor()
        try:
            cur.execute(query, (id,))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def delete_by(self, conditions: Dict[str, Any]) -> int:
        """Delete records matching the given conditions."""
        if not conditions:
            raise ValueError("Cannot delete without conditions")

        where_parts = []
        values = []
        for key, value in conditions.items():
            if value is None:
                where_parts.append(f"{key} IS NULL")
            else:
                where_parts.append(f"{key} = %s")
                values.append(value)

        where_clause = " AND ".join(where_parts)

        query = f"DELETE FROM {self.table_name} WHERE {where_clause}"

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values))
            count = cur.rowcount
            self.conn.commit()
            return count
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_dir: str = "DESC",
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Get paginated results.

        Returns:
            Tuple of (items, total_count, total_pages)
        """
        offset = (page - 1) * per_page
        total = self.count(conditions)
        total_pages = (total + per_page - 1) // per_page

        items = self.find_by(
            conditions or {},
            limit=per_page,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir,
        )

        return items, total, total_pages
