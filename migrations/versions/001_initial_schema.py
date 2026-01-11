"""Initial database schema

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

This migration creates the initial database schema for In-Tuned.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import psycopg

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    conn = op.get_bind()

    # Users table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            preferred_language TEXT DEFAULT 'en',
            preferred_theme TEXT DEFAULT 'dark',
            is_active BOOLEAN DEFAULT TRUE,
            role TEXT DEFAULT 'user',
            failed_login_attempts INTEGER DEFAULT 0,
            last_failed_login TIMESTAMPTZ,
            last_login TIMESTAMPTZ,
            disabled_at TIMESTAMPTZ,
            disabled_reason TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    # Journals table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS journals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            source_text TEXT,
            analysis_json JSONB,
            journal_text TEXT,
            is_pinned BOOLEAN DEFAULT FALSE,
            has_self_harm_flag BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_journals_user_id ON journals(user_id);
        CREATE INDEX IF NOT EXISTS idx_journals_created_at ON journals(created_at);
        CREATE INDEX IF NOT EXISTS idx_journals_user_pinned ON journals(user_id, is_pinned);
        """
    )

    # Notices table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    # Site settings table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            maintenance_mode BOOLEAN NOT NULL DEFAULT FALSE,
            maintenance_message TEXT,
            CONSTRAINT single_row CHECK (id = 1)
        );

        INSERT INTO site_settings (id, maintenance_mode, maintenance_message)
        VALUES (1, FALSE, NULL)
        ON CONFLICT (id) DO NOTHING;
        """
    )

    # Lexicon files table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lexicon_files (
            id SERIAL PRIMARY KEY,
            language TEXT NOT NULL,
            filename TEXT NOT NULL,
            content_type TEXT,
            data BYTEA,
            uploaded_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_lexicon_files_language ON lexicon_files(language);
        """
    )

    # Feedback table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            entry_text TEXT NOT NULL,
            analysis_json JSONB,
            feedback_text TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
        """
    )

    # Audit log table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            actor_id INTEGER,
            actor_type TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            before_state JSONB,
            after_state JSONB,
            ip_address TEXT,
            user_agent TEXT,
            request_id TEXT,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON audit_log(actor_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
        CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
        """
    )


def downgrade() -> None:
    """Drop all tables."""
    conn = op.get_bind()

    conn.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
    conn.execute("DROP TABLE IF EXISTS feedback CASCADE;")
    conn.execute("DROP TABLE IF EXISTS lexicon_files CASCADE;")
    conn.execute("DROP TABLE IF EXISTS site_settings CASCADE;")
    conn.execute("DROP TABLE IF EXISTS notices CASCADE;")
    conn.execute("DROP TABLE IF EXISTS journals CASCADE;")
    conn.execute("DROP TABLE IF EXISTS users CASCADE;")
