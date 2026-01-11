# app/cli.py
"""
CLI Commands

This module provides command-line interface commands for:
- Database initialization and migrations
- User management
- Data seeding
- Maintenance tasks
"""

from __future__ import annotations

import click
from flask import Flask
from werkzeug.security import generate_password_hash

from app.db.connection import get_connection


def register_commands(app: Flask) -> None:
    """Register CLI commands with the Flask app."""

    @app.cli.command("init-db")
    def init_db():
        """Initialize the database schema."""
        click.echo("Initializing database...")

        with get_connection() as conn:
            cur = conn.cursor()

            # Users table with additional columns
            cur.execute(
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
            cur.execute(
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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notices (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )

            # Site settings table (single row)
            cur.execute(
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
            cur.execute(
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
            cur.execute(
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
            cur.execute(
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

            conn.commit()
            cur.close()

        click.echo("Database initialized successfully!")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True, help="Admin username")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username: str, password: str):
        """Generate password hash for admin credentials."""
        password_hash = generate_password_hash(password)

        click.echo("\nAdd these to your environment variables:\n")
        click.echo(f"ADMIN_USERNAME={username}")
        click.echo(f"ADMIN_PASSWORD_HASH={password_hash}")
        click.echo("\nKeep the password secure and don't commit it to version control!")

    @app.cli.command("create-dev-password")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_dev_password(password: str):
        """Generate password hash for developer/maintenance password."""
        password_hash = generate_password_hash(password)

        click.echo("\nAdd this to your environment variables:\n")
        click.echo(f"DEV_PASSWORD_HASH={password_hash}")

    @app.cli.command("seed-db")
    @click.option("--force", is_flag=True, help="Force seed even if data exists")
    def seed_db(force: bool):
        """Seed the database with initial data."""
        click.echo("Seeding database...")

        with get_connection() as conn:
            cur = conn.cursor()

            # Check if data exists
            cur.execute("SELECT COUNT(*) as count FROM users")
            result = cur.fetchone()

            if result and result["count"] > 0 and not force:
                click.echo("Database already contains data. Use --force to override.")
                return

            # Seed notices
            cur.execute(
                """
                INSERT INTO notices (text, is_active)
                VALUES ('Welcome to In-Tuned! Analyze your emotions with our AI-powered tool.', TRUE)
                ON CONFLICT DO NOTHING;
                """
            )

            conn.commit()
            cur.close()

        click.echo("Database seeded successfully!")

    @app.cli.command("cleanup-sessions")
    @click.option("--days", default=30, help="Delete sessions older than N days")
    def cleanup_sessions(days: int):
        """Clean up old session data."""
        click.echo(f"Cleaning up sessions older than {days} days...")
        # Note: Flask's default session handling doesn't store sessions in DB
        # This is a placeholder for custom session cleanup if needed
        click.echo("Session cleanup complete!")

    @app.cli.command("cleanup-audit-log")
    @click.option("--days", default=365, help="Delete audit logs older than N days")
    def cleanup_audit_log(days: int):
        """Clean up old audit log entries."""
        click.echo(f"Cleaning up audit logs older than {days} days...")

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM audit_log
                WHERE created_at < NOW() - INTERVAL '%s days'
                """,
                (days,),
            )
            deleted = cur.rowcount
            conn.commit()
            cur.close()

        click.echo(f"Deleted {deleted} old audit log entries.")

    @app.cli.command("show-stats")
    def show_stats():
        """Show database statistics."""
        with get_connection() as conn:
            cur = conn.cursor()

            # User stats
            cur.execute("SELECT COUNT(*) as count FROM users")
            users = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
            active_users = cur.fetchone()["count"]

            # Journal stats
            cur.execute("SELECT COUNT(*) as count FROM journals")
            journals = cur.fetchone()["count"]

            # Feedback stats
            cur.execute("SELECT COUNT(*) as count FROM feedback")
            feedback = cur.fetchone()["count"]

            # Audit log stats
            cur.execute("SELECT COUNT(*) as count FROM audit_log")
            audit_logs = cur.fetchone()["count"]

            cur.close()

        click.echo("\n=== Database Statistics ===")
        click.echo(f"Users: {users} (active: {active_users})")
        click.echo(f"Journals: {journals}")
        click.echo(f"Feedback entries: {feedback}")
        click.echo(f"Audit log entries: {audit_logs}")
        click.echo("")

    @app.cli.command("check-health")
    def check_health():
        """Check database connection health."""
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.close()
            click.echo("Database connection: OK")
        except Exception as e:
            click.echo(f"Database connection: FAILED - {e}")
            raise SystemExit(1)
