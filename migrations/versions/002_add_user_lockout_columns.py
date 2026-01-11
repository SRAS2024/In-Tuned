"""Add missing columns to users table for account lockout

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

This migration adds columns required for the account lockout feature
to an existing users table that may have been created by the original
server.py.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to users table."""
    conn = op.get_bind()

    # Add columns if they don't exist (compatible with existing databases)
    columns_to_add = [
        ("is_active", "BOOLEAN DEFAULT TRUE"),
        ("role", "TEXT DEFAULT 'user'"),
        ("failed_login_attempts", "INTEGER DEFAULT 0"),
        ("last_failed_login", "TIMESTAMPTZ"),
        ("last_login", "TIMESTAMPTZ"),
        ("disabled_at", "TIMESTAMPTZ"),
        ("disabled_reason", "TEXT"),
    ]

    for column_name, column_def in columns_to_add:
        try:
            conn.execute(
                f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_def};"
            )
        except Exception:
            # Column may already exist or syntax not supported
            pass

    # Add audit_log table if it doesn't exist
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

    # Add indexes to journals table if they don't exist
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_journals_user_id ON journals(user_id);
        CREATE INDEX IF NOT EXISTS idx_journals_created_at ON journals(created_at);
        CREATE INDEX IF NOT EXISTS idx_journals_user_pinned ON journals(user_id, is_pinned);
        """
    )

    # Add index to feedback table if it doesn't exist
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
        """
    )

    # Add index to lexicon_files table if it doesn't exist
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_lexicon_files_language ON lexicon_files(language);
        """
    )


def downgrade() -> None:
    """Remove added columns (not recommended for production)."""
    conn = op.get_bind()

    # Note: We don't remove columns in downgrade as it could cause data loss
    # and the original server.py should work fine with extra columns
    pass
