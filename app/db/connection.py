# app/db/connection.py
"""
Database Connection Management

This module provides production-safe database connection management
with proper pooling, lifecycle handling, and error recovery.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from flask import current_app, g

# Global connection pool
_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool."""
    global _pool

    if _pool is None:
        database_url = current_app.config.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")

        pool_size = current_app.config.get("DATABASE_POOL_SIZE", 5)
        max_overflow = current_app.config.get("DATABASE_MAX_OVERFLOW", 10)
        timeout = current_app.config.get("DATABASE_POOL_TIMEOUT", 30)

        _pool = ConnectionPool(
            database_url,
            min_size=1,
            max_size=pool_size + max_overflow,
            timeout=timeout,
            kwargs={"row_factory": dict_row},
        )

    return _pool


def init_pool(app) -> None:
    """Initialize the connection pool with app context."""
    global _pool

    database_url = app.config.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    pool_size = app.config.get("DATABASE_POOL_SIZE", 5)
    max_overflow = app.config.get("DATABASE_MAX_OVERFLOW", 10)
    timeout = app.config.get("DATABASE_POOL_TIMEOUT", 30)

    _pool = ConnectionPool(
        database_url,
        min_size=1,
        max_size=pool_size + max_overflow,
        timeout=timeout,
        kwargs={"row_factory": dict_row},
    )


def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_db_connection() -> psycopg.Connection:
    """
    Get a database connection from the pool.

    In a request context, returns a connection that will be
    automatically returned to the pool at the end of the request.
    """
    try:
        pool = get_pool()
        conn = pool.getconn()
        return conn
    except Exception as e:
        current_app.logger.error(
            f"Failed to get database connection: {e}",
            extra={"request_id": getattr(g, "request_id", "unknown")},
        )
        raise


def close_db_connection() -> None:
    """Return the database connection to the pool."""
    global _pool

    conn = g.pop("db", None)
    if conn is not None and _pool is not None:
        try:
            # Rollback any uncommitted transaction
            if not conn.closed:
                conn.rollback()
            _pool.putconn(conn)
        except Exception as e:
            current_app.logger.warning(
                f"Error returning connection to pool: {e}",
                extra={"request_id": getattr(g, "request_id", "unknown")},
            )


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Context manager for database connections.

    Use this for operations outside of a request context,
    such as CLI commands or background jobs.
    """
    global _pool

    # For direct usage without app context
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    conn = psycopg.connect(database_url, row_factory=dict_row)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    """
    Execute a query and return results.

    This is a convenience function for simple queries.
    For complex operations, use the repository pattern.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)

        if query.strip().upper().startswith(("SELECT", "RETURNING")):
            if fetch_one:
                return cur.fetchone()
            return cur.fetchall()

        # For INSERT/UPDATE/DELETE with RETURNING
        if "RETURNING" in query.upper():
            if fetch_one:
                return cur.fetchone()
            return cur.fetchall()

        conn.commit()
        return cur.rowcount

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()


def check_database_health() -> bool:
    """Check if the database connection is healthy."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return True
    except Exception:
        return False
