# app/db/repositories/audit_repository.py
"""
Audit Repository

Provides data access methods for the audit log.
Tracks admin actions for security and compliance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from psycopg.types.json import Jsonb

from app.db.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    """Repository for audit log data access."""

    table_name = "audit_log"
    primary_key = "id"

    def log_action(
        self,
        actor_id: Optional[int],
        actor_type: str,  # 'user', 'admin', 'system'
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log an audit event.

        Args:
            actor_id: ID of the user/admin performing the action
            actor_type: Type of actor ('user', 'admin', 'system')
            action: Action performed (e.g., 'create', 'update', 'delete', 'login')
            resource_type: Type of resource affected (e.g., 'user', 'journal', 'lexicon')
            resource_id: ID of the affected resource
            before_state: State before the action (for updates)
            after_state: State after the action (for creates/updates)
            ip_address: Client IP address
            user_agent: Client user agent string
            request_id: Request ID for tracing
            metadata: Additional metadata about the action

        Returns:
            The created audit log entry
        """
        query = """
            INSERT INTO audit_log (
                actor_id, actor_type, action, resource_type, resource_id,
                before_state, after_state, ip_address, user_agent,
                request_id, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """

        before_json = Jsonb(before_state) if before_state else None
        after_json = Jsonb(after_state) if after_state else None
        metadata_json = Jsonb(metadata) if metadata else None

        cur = self.cursor()
        try:
            cur.execute(
                query,
                (
                    actor_id,
                    actor_type,
                    action,
                    resource_type,
                    resource_id,
                    before_json,
                    after_json,
                    ip_address,
                    user_agent,
                    request_id,
                    metadata_json,
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

    def get_logs(
        self,
        actor_id: Optional[int] = None,
        actor_type: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering."""
        conditions = []
        values = []

        if actor_id is not None:
            conditions.append("actor_id = %s")
            values.append(actor_id)

        if actor_type:
            conditions.append("actor_type = %s")
            values.append(actor_type)

        if action:
            conditions.append("action = %s")
            values.append(action)

        if resource_type:
            conditions.append("resource_type = %s")
            values.append(resource_type)

        if resource_id:
            conditions.append("resource_id = %s")
            values.append(resource_id)

        if start_date:
            conditions.append("created_at >= %s")
            values.append(start_date)

        if end_date:
            conditions.append("created_at <= %s")
            values.append(end_date)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT id, actor_id, actor_type, action, resource_type, resource_id,
                   before_state, after_state, ip_address, created_at, request_id
            FROM audit_log
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """

        values.extend([limit, offset])

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values))
            return cur.fetchall()
        finally:
            cur.close()

    def get_logs_for_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get audit history for a specific resource."""
        query = """
            SELECT id, actor_id, actor_type, action, before_state, after_state,
                   ip_address, created_at, request_id
            FROM audit_log
            WHERE resource_type = %s AND resource_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (resource_type, resource_id, limit))
            return cur.fetchall()
        finally:
            cur.close()

    def get_actor_activity(
        self,
        actor_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific actor."""
        query = """
            SELECT id, action, resource_type, resource_id, ip_address, created_at
            FROM audit_log
            WHERE actor_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """

        cur = self.cursor()
        try:
            cur.execute(query, (actor_id, limit))
            return cur.fetchall()
        finally:
            cur.close()

    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security-related audit events."""
        security_actions = [
            "login",
            "logout",
            "login_failed",
            "password_change",
            "password_reset",
            "account_disabled",
            "admin_login",
            "permission_change",
        ]

        placeholders = ", ".join(["%s"] * len(security_actions))

        query = f"""
            SELECT id, actor_id, actor_type, action, resource_type, resource_id,
                   ip_address, user_agent, created_at, metadata
            FROM audit_log
            WHERE action IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT %s
        """

        values = security_actions + [limit]

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values))
            return cur.fetchall()
        finally:
            cur.close()

    def get_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        conditions = []
        values = []

        if start_date:
            conditions.append("created_at >= %s")
            values.append(start_date)

        if end_date:
            conditions.append("created_at <= %s")
            values.append(end_date)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                COUNT(*) as total_events,
                COUNT(DISTINCT actor_id) as unique_actors,
                COUNT(*) FILTER (WHERE action = 'login') as login_count,
                COUNT(*) FILTER (WHERE action = 'login_failed') as failed_login_count,
                COUNT(*) FILTER (WHERE actor_type = 'admin') as admin_actions,
                jsonb_object_agg(
                    action,
                    action_count
                ) FILTER (WHERE action IS NOT NULL) as actions_breakdown
            FROM audit_log
            LEFT JOIN LATERAL (
                SELECT action, COUNT(*) as action_count
                FROM audit_log sub
                {where_clause}
                GROUP BY action
            ) action_counts ON TRUE
            {where_clause}
        """

        cur = self.cursor()
        try:
            cur.execute(query, tuple(values * 2))  # Used twice in query
            result = cur.fetchone()
            return result or {}
        except Exception:
            # Fallback to simpler query if the complex one fails
            simple_query = f"""
                SELECT
                    COUNT(*) as total_events,
                    COUNT(DISTINCT actor_id) as unique_actors
                FROM audit_log
                {where_clause}
            """
            cur.execute(simple_query, tuple(values))
            return cur.fetchone() or {}
        finally:
            cur.close()

    def cleanup_old_logs(self, days_to_keep: int = 365) -> int:
        """Delete audit logs older than the specified number of days."""
        query = """
            DELETE FROM audit_log
            WHERE created_at < NOW() - INTERVAL '%s days'
            RETURNING id
        """

        cur = self.cursor()
        try:
            cur.execute(query, (days_to_keep,))
            count = cur.rowcount
            self.conn.commit()
            return count
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()
