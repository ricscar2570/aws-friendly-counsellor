from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ...domain.entities import (
    AnalysisVersion,
    AuditContext,
    AuditEvent,
    Membership,
    Project,
    Tenant,
)
from ...domain.exceptions import ConflictError, NotFoundError, RevisionConflictError
from .common import decode_cursor, encode_cursor, new_id, utc_now


class SQLiteStore:
    backend_name = "sqlite"

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._lock = threading.RLock()
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        if self.database_path != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            if self.database_path != ":memory:":
                Path(self.database_path).expanduser().resolve().parent.mkdir(
                    parents=True, exist_ok=True
                )
            with self._connection() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS tenants (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        slug TEXT NOT NULL UNIQUE,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        revision INTEGER NOT NULL CHECK (revision >= 1)
                    );

                    CREATE TABLE IF NOT EXISTS memberships (
                        tenant_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('viewer', 'editor', 'admin', 'owner')),
                        status TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        revision INTEGER NOT NULL CHECK (revision >= 1),
                        PRIMARY KEY (tenant_id, subject),
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_memberships_tenant_subject
                    ON memberships (tenant_id, subject);

                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        estimated_users INTEGER NOT NULL CHECK (estimated_users >= 1),
                        budget TEXT NOT NULL,
                        region TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        revision INTEGER NOT NULL CHECK (revision >= 1),
                        analysis_version_counter INTEGER NOT NULL DEFAULT 0,
                        UNIQUE (tenant_id, id),
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_projects_tenant_created
                    ON projects (tenant_id, created_at, id);

                    CREATE TABLE IF NOT EXISTS analysis_versions (
                        tenant_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        version INTEGER NOT NULL CHECK (version >= 1),
                        analysis_id TEXT NOT NULL UNIQUE,
                        request_json TEXT NOT NULL,
                        result_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (tenant_id, project_id, version),
                        FOREIGN KEY (tenant_id, project_id)
                            REFERENCES projects(tenant_id, id) ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_analysis_project_version
                    ON analysis_versions (tenant_id, project_id, version);

                    CREATE TABLE IF NOT EXISTS audit_events (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        actor_subject TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        request_id TEXT NOT NULL,
                        occurred_at TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_audit_tenant_time
                    ON audit_events (tenant_id, occurred_at, id);
                    """
                )
                connection.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (1, ?)",
                    (utc_now(),),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (2, ?)",
                    (utc_now(),),
                )
            self._initialized = True

    def health_check(self) -> bool:
        self.initialize()
        with self._connection() as connection:
            value = connection.execute("SELECT 1").fetchone()[0]
        return value == 1

    def close(self) -> None:
        return None

    @staticmethod
    def _tenant(row: sqlite3.Row) -> Tenant:
        return Tenant(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            revision=int(row["revision"]),
        )

    @staticmethod
    def _membership(row: sqlite3.Row) -> Membership:
        return Membership(
            tenant_id=row["tenant_id"],
            subject=row["subject"],
            role=row["role"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            revision=int(row["revision"]),
        )

    @staticmethod
    def _project(row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            estimated_users=int(row["estimated_users"]),
            budget=row["budget"],
            region=row["region"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            revision=int(row["revision"]),
        )

    @staticmethod
    def _analysis(row: sqlite3.Row) -> AnalysisVersion:
        return AnalysisVersion(
            analysis_id=row["analysis_id"],
            tenant_id=row["tenant_id"],
            project_id=row["project_id"],
            version=int(row["version"]),
            request_payload=json.loads(row["request_json"]),
            result_payload=json.loads(row["result_json"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _audit(row: sqlite3.Row) -> AuditEvent:
        return AuditEvent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            actor_subject=row["actor_subject"],
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            request_id=row["request_id"],
            occurred_at=row["occurred_at"],
            metadata=json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _insert_audit(
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        audit: AuditContext | None,
    ) -> None:
        if audit is None:
            return
        connection.execute(
            """
            INSERT INTO audit_events
            (id, tenant_id, actor_subject, action, resource_type, resource_id,
             request_id, occurred_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("aud"),
                tenant_id,
                audit.actor_subject,
                audit.action,
                resource_type,
                resource_id,
                audit.request_id,
                utc_now(),
                json.dumps(audit.metadata or {}, separators=(",", ":"), sort_keys=True),
            ),
        )

    def create_tenant(
        self,
        *,
        name: str,
        slug: str,
        owner_subject: str | None = None,
        audit: AuditContext | None = None,
    ) -> Tenant:
        self.initialize()
        now = utc_now()
        tenant = Tenant(
            id=new_id("ten"),
            name=name,
            slug=slug,
            status="active",
            created_at=now,
            updated_at=now,
            revision=1,
        )
        try:
            with self._lock, self._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        """
                        INSERT INTO tenants
                        (id, name, slug, status, created_at, updated_at, revision)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tenant.id,
                            tenant.name,
                            tenant.slug,
                            tenant.status,
                            tenant.created_at,
                            tenant.updated_at,
                            tenant.revision,
                        ),
                    )
                    if owner_subject is not None:
                        connection.execute(
                            """
                            INSERT INTO memberships
                            (tenant_id, subject, role, status, created_at, updated_at, revision)
                            VALUES (?, ?, 'owner', 'active', ?, ?, 1)
                            """,
                            (tenant.id, owner_subject, now, now),
                        )
                    self._insert_audit(
                        connection,
                        tenant_id=tenant.id,
                        resource_type="tenant",
                        resource_id=tenant.id,
                        audit=audit,
                    )
                    connection.execute("COMMIT")
                except Exception:
                    connection.execute("ROLLBACK")
                    raise
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Tenant slug already exists") from exc
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM tenants WHERE id = ?", (tenant_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError("Tenant not found")
        return self._tenant(row)

    def create_membership(
        self,
        *,
        tenant_id: str,
        subject: str,
        role: str,
        status: str = "active",
        audit: AuditContext | None = None,
    ) -> Membership:
        self.initialize()
        self.get_tenant(tenant_id)
        now = utc_now()
        membership = Membership(
            tenant_id=tenant_id,
            subject=subject,
            role=role,
            status=status,
            created_at=now,
            updated_at=now,
            revision=1,
        )
        try:
            with self._lock, self._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        """
                        INSERT INTO memberships
                        (tenant_id, subject, role, status, created_at, updated_at, revision)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tenant_id,
                            subject,
                            role,
                            status,
                            now,
                            now,
                            1,
                        ),
                    )
                    self._insert_audit(
                        connection,
                        tenant_id=tenant_id,
                        resource_type="membership",
                        resource_id=subject,
                        audit=audit,
                    )
                    connection.execute("COMMIT")
                except Exception:
                    connection.execute("ROLLBACK")
                    raise
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Tenant membership already exists") from exc
        return membership

    def get_membership(self, *, tenant_id: str, subject: str) -> Membership:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM memberships WHERE tenant_id = ? AND subject = ?",
                (tenant_id, subject),
            ).fetchone()
        if row is None:
            raise NotFoundError("Tenant membership not found")
        return self._membership(row)

    def list_memberships(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[Membership], str | None]:
        self.initialize()
        self.get_tenant(tenant_id)
        after_subject = ""
        if cursor:
            decoded = decode_cursor(cursor)
            value = decoded.get("subject")
            if not isinstance(value, str):
                raise ValueError("Invalid pagination cursor")
            after_subject = value
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memberships
                WHERE tenant_id = ? AND subject > ?
                ORDER BY subject ASC
                LIMIT ?
                """,
                (tenant_id, after_subject, limit + 1),
            ).fetchall()
        has_more = len(rows) > limit
        visible = rows[:limit]
        next_cursor = (
            encode_cursor({"subject": visible[-1]["subject"]})
            if has_more and visible
            else None
        )
        return [self._membership(row) for row in visible], next_cursor

    def update_membership(
        self,
        *,
        tenant_id: str,
        subject: str,
        expected_revision: int,
        role: str | None,
        status: str | None,
        audit: AuditContext | None = None,
    ) -> Membership:
        self.initialize()
        if role is None and status is None:
            return self.get_membership(tenant_id=tenant_id, subject=subject)
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                current = connection.execute(
                    "SELECT * FROM memberships WHERE tenant_id = ? AND subject = ?",
                    (tenant_id, subject),
                ).fetchone()
                if current is None:
                    raise NotFoundError("Tenant membership not found")
                if int(current["revision"]) != expected_revision:
                    raise RevisionConflictError(
                        f"Membership revision changed; current revision is {current['revision']}"
                    )
                next_role = role or current["role"]
                next_status = status or current["status"]
                now = utc_now()
                connection.execute(
                    """
                    UPDATE memberships
                    SET role = ?, status = ?, updated_at = ?, revision = revision + 1
                    WHERE tenant_id = ? AND subject = ? AND revision = ?
                    """,
                    (
                        next_role,
                        next_status,
                        now,
                        tenant_id,
                        subject,
                        expected_revision,
                    ),
                )
                self._insert_audit(
                    connection,
                    tenant_id=tenant_id,
                    resource_type="membership",
                    resource_id=subject,
                    audit=audit,
                )
                row = connection.execute(
                    "SELECT * FROM memberships WHERE tenant_id = ? AND subject = ?",
                    (tenant_id, subject),
                ).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        assert row is not None
        return self._membership(row)

    def create_project(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str,
        estimated_users: int,
        budget: str,
        region: str,
        status: str,
        audit: AuditContext | None = None,
    ) -> Project:
        self.initialize()
        self.get_tenant(tenant_id)
        now = utc_now()
        project = Project(
            id=new_id("prj"),
            tenant_id=tenant_id,
            name=name,
            description=description,
            estimated_users=estimated_users,
            budget=budget,
            region=region,
            status=status,
            created_at=now,
            updated_at=now,
            revision=1,
        )
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO projects
                    (id, tenant_id, name, description, estimated_users, budget, region,
                     status, created_at, updated_at, revision, analysis_version_counter)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        project.id,
                        project.tenant_id,
                        project.name,
                        project.description,
                        project.estimated_users,
                        project.budget,
                        project.region,
                        project.status,
                        project.created_at,
                        project.updated_at,
                        project.revision,
                    ),
                )
                self._insert_audit(
                    connection,
                    tenant_id=tenant_id,
                    resource_type="project",
                    resource_id=project.id,
                    audit=audit,
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return project

    def list_projects(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[Project], str | None]:
        self.initialize()
        self.get_tenant(tenant_id)
        params: list[Any] = [tenant_id]
        where = "tenant_id = ?"
        if cursor:
            decoded = decode_cursor(cursor)
            created_at = decoded.get("created_at")
            project_id = decoded.get("id")
            if not isinstance(created_at, str) or not isinstance(project_id, str):
                raise ValueError("Invalid pagination cursor")
            where += " AND (created_at > ? OR (created_at = ? AND id > ?))"
            params.extend([created_at, created_at, project_id])
        params.append(limit + 1)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM projects
                WHERE {where}
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                params,
            ).fetchall()
        has_more = len(rows) > limit
        visible = rows[:limit]
        next_cursor = None
        if has_more and visible:
            last = visible[-1]
            next_cursor = encode_cursor(
                {"created_at": last["created_at"], "id": last["id"]}
            )
        return [self._project(row) for row in visible], next_cursor

    def get_project(self, *, tenant_id: str, project_id: str) -> Project:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE tenant_id = ? AND id = ?",
                (tenant_id, project_id),
            ).fetchone()
        if row is None:
            raise NotFoundError("Project not found")
        return self._project(row)

    def update_project(
        self,
        *,
        tenant_id: str,
        project_id: str,
        expected_revision: int,
        changes: dict[str, Any],
        audit: AuditContext | None = None,
    ) -> Project:
        self.initialize()
        if not changes:
            return self.get_project(tenant_id=tenant_id, project_id=project_id)
        allowed = {
            "name",
            "description",
            "estimated_users",
            "budget",
            "region",
            "status",
        }
        invalid = set(changes) - allowed
        if invalid:
            raise ValueError(f"Unsupported project fields: {sorted(invalid)}")
        assignments = [f"{field} = ?" for field in changes]
        now = utc_now()
        assignments.extend(["updated_at = ?", "revision = revision + 1"])
        values = list(changes.values()) + [now, tenant_id, project_id, expected_revision]
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    f"""
                    UPDATE projects
                    SET {', '.join(assignments)}
                    WHERE tenant_id = ? AND id = ? AND revision = ?
                    """,
                    values,
                )
                if cursor.rowcount == 0:
                    existing = connection.execute(
                        "SELECT revision FROM projects WHERE tenant_id = ? AND id = ?",
                        (tenant_id, project_id),
                    ).fetchone()
                    if existing is None:
                        raise NotFoundError("Project not found")
                    raise RevisionConflictError(
                        f"Project revision changed; current revision is {existing['revision']}"
                    )
                self._insert_audit(
                    connection,
                    tenant_id=tenant_id,
                    resource_type="project",
                    resource_id=project_id,
                    audit=audit,
                )
                row = connection.execute(
                    "SELECT * FROM projects WHERE tenant_id = ? AND id = ?",
                    (tenant_id, project_id),
                ).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        assert row is not None
        return self._project(row)

    def create_analysis_version(
        self,
        *,
        tenant_id: str,
        project_id: str,
        request_payload: dict[str, Any],
        result_payload: dict[str, Any],
        audit: AuditContext | None = None,
    ) -> AnalysisVersion:
        self.initialize()
        now = utc_now()
        analysis_id = new_id("ana")
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                project = connection.execute(
                    """
                    SELECT analysis_version_counter FROM projects
                    WHERE tenant_id = ? AND id = ?
                    """,
                    (tenant_id, project_id),
                ).fetchone()
                if project is None:
                    raise NotFoundError("Project not found")
                version = int(project["analysis_version_counter"]) + 1
                connection.execute(
                    """
                    UPDATE projects SET analysis_version_counter = ?
                    WHERE tenant_id = ? AND id = ?
                    """,
                    (version, tenant_id, project_id),
                )
                connection.execute(
                    """
                    INSERT INTO analysis_versions
                    (tenant_id, project_id, version, analysis_id, request_json,
                     result_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tenant_id,
                        project_id,
                        version,
                        analysis_id,
                        json.dumps(request_payload, separators=(",", ":"), sort_keys=True),
                        json.dumps(result_payload, separators=(",", ":"), sort_keys=True),
                        now,
                    ),
                )
                self._insert_audit(
                    connection,
                    tenant_id=tenant_id,
                    resource_type="analysis",
                    resource_id=analysis_id,
                    audit=audit,
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return AnalysisVersion(
            analysis_id=analysis_id,
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            request_payload=request_payload,
            result_payload=result_payload,
            created_at=now,
        )

    def list_analysis_versions(
        self, *, tenant_id: str, project_id: str, limit: int, cursor: str | None
    ) -> tuple[list[AnalysisVersion], str | None]:
        self.initialize()
        self.get_project(tenant_id=tenant_id, project_id=project_id)
        last_version = 0
        if cursor:
            decoded = decode_cursor(cursor)
            value = decoded.get("version")
            if not isinstance(value, int) or value < 0:
                raise ValueError("Invalid pagination cursor")
            last_version = value
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM analysis_versions
                WHERE tenant_id = ? AND project_id = ? AND version > ?
                ORDER BY version ASC
                LIMIT ?
                """,
                (tenant_id, project_id, last_version, limit + 1),
            ).fetchall()
        has_more = len(rows) > limit
        visible = rows[:limit]
        next_cursor = None
        if has_more and visible:
            next_cursor = encode_cursor({"version": int(visible[-1]["version"])})
        return [self._analysis(row) for row in visible], next_cursor

    def get_analysis_version(
        self, *, tenant_id: str, project_id: str, version: int
    ) -> AnalysisVersion:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM analysis_versions
                WHERE tenant_id = ? AND project_id = ? AND version = ?
                """,
                (tenant_id, project_id, version),
            ).fetchone()
        if row is None:
            raise NotFoundError("Analysis version not found")
        return self._analysis(row)

    def list_audit_events(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[AuditEvent], str | None]:
        self.initialize()
        self.get_tenant(tenant_id)
        params: list[Any] = [tenant_id]
        where = "tenant_id = ?"
        if cursor:
            decoded = decode_cursor(cursor)
            occurred_at = decoded.get("occurred_at")
            event_id = decoded.get("id")
            if not isinstance(occurred_at, str) or not isinstance(event_id, str):
                raise ValueError("Invalid pagination cursor")
            where += " AND (occurred_at < ? OR (occurred_at = ? AND id < ?))"
            params.extend([occurred_at, occurred_at, event_id])
        params.append(limit + 1)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM audit_events
                WHERE {where}
                ORDER BY occurred_at DESC, id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        has_more = len(rows) > limit
        visible = rows[:limit]
        next_cursor = None
        if has_more and visible:
            last = visible[-1]
            next_cursor = encode_cursor(
                {"occurred_at": last["occurred_at"], "id": last["id"]}
            )
        return [self._audit(row) for row in visible], next_cursor
