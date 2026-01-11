# app/db/repositories/__init__.py
"""
Repository Pattern Implementation

This package provides data access layer using the repository pattern.
All SQL queries are encapsulated in repository classes, keeping them
out of route handlers and service code.
"""

from app.db.repositories.base import BaseRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.journal_repository import JournalRepository
from app.db.repositories.feedback_repository import FeedbackRepository
from app.db.repositories.lexicon_repository import LexiconRepository
from app.db.repositories.site_repository import SiteRepository
from app.db.repositories.audit_repository import AuditRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "JournalRepository",
    "FeedbackRepository",
    "LexiconRepository",
    "SiteRepository",
    "AuditRepository",
]
