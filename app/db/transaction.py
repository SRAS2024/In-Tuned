# app/db/transaction.py
"""
Transaction Management

This module provides transaction decorators and context managers
for ensuring data integrity in multi-step database operations.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec

from flask import g

P = ParamSpec("P")
T = TypeVar("T")


def transactional(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator that wraps a function in a database transaction.

    If the function completes successfully, the transaction is committed.
    If an exception is raised, the transaction is rolled back.

    Usage:
        @transactional
        def create_user_with_profile(user_data, profile_data):
            user = user_repository.create(user_data)
            profile_repository.create(user.id, profile_data)
            return user
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        conn = g.db
        if conn is None:
            from app.db.connection import get_db_connection
            conn = get_db_connection()
            g.db = conn

        try:
            result = func(*args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise

    return wrapper


class Transaction:
    """
    Context manager for explicit transaction control.

    Usage:
        with Transaction() as txn:
            user = user_repository.create(user_data)
            profile_repository.create(user.id, profile_data)
            txn.commit()  # Explicit commit
    """

    def __init__(self):
        self.conn = None
        self._committed = False

    def __enter__(self) -> "Transaction":
        from app.db.connection import get_db_connection

        if hasattr(g, "db") and g.db is not None:
            self.conn = g.db
        else:
            self.conn = get_db_connection()
            g.db = self.conn
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            # Exception occurred, rollback
            self.conn.rollback()
            return False

        if not self._committed:
            # No exception but also no explicit commit, rollback
            self.conn.rollback()

        return False

    def commit(self) -> None:
        """Explicitly commit the transaction."""
        self.conn.commit()
        self._committed = True

    def rollback(self) -> None:
        """Explicitly rollback the transaction."""
        self.conn.rollback()
        self._committed = True  # Mark as handled


class Savepoint:
    """
    Context manager for savepoints within a transaction.

    Allows partial rollback within a larger transaction.

    Usage:
        with Transaction():
            user = user_repository.create(user_data)

            with Savepoint("create_profile"):
                try:
                    profile_repository.create(user.id, profile_data)
                except Exception:
                    pass  # Profile creation failed, but user still created
    """

    def __init__(self, name: str):
        self.name = name
        self.conn = None

    def __enter__(self) -> "Savepoint":
        self.conn = g.db
        if self.conn is None:
            raise RuntimeError("Savepoint requires an active transaction")

        self.conn.execute(f"SAVEPOINT {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            # Exception occurred, rollback to savepoint
            self.conn.execute(f"ROLLBACK TO SAVEPOINT {self.name}")
            return True  # Suppress the exception

        # Release savepoint on success
        self.conn.execute(f"RELEASE SAVEPOINT {self.name}")
        return False

    def rollback(self) -> None:
        """Explicitly rollback to this savepoint."""
        self.conn.execute(f"ROLLBACK TO SAVEPOINT {self.name}")
