from __future__ import annotations

from typing import Any, Protocol

from .entities import AnalysisVersion, AuditContext, AuditEvent, Membership, Project, Tenant


class PersistenceStore(Protocol):
    backend_name: str

    def initialize(self) -> None: ...

    def health_check(self) -> bool: ...

    def close(self) -> None: ...

    def create_tenant(
        self,
        *,
        name: str,
        slug: str,
        owner_subject: str | None = None,
        audit: AuditContext | None = None,
    ) -> Tenant: ...

    def get_tenant(self, tenant_id: str) -> Tenant: ...

    def create_membership(
        self,
        *,
        tenant_id: str,
        subject: str,
        role: str,
        status: str = "active",
        audit: AuditContext | None = None,
    ) -> Membership: ...

    def get_membership(self, *, tenant_id: str, subject: str) -> Membership: ...

    def list_memberships(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[Membership], str | None]: ...

    def update_membership(
        self,
        *,
        tenant_id: str,
        subject: str,
        expected_revision: int,
        role: str | None,
        status: str | None,
        audit: AuditContext | None = None,
    ) -> Membership: ...

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
    ) -> Project: ...

    def list_projects(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[Project], str | None]: ...

    def get_project(self, *, tenant_id: str, project_id: str) -> Project: ...

    def update_project(
        self,
        *,
        tenant_id: str,
        project_id: str,
        expected_revision: int,
        changes: dict[str, Any],
        audit: AuditContext | None = None,
    ) -> Project: ...

    def create_analysis_version(
        self,
        *,
        tenant_id: str,
        project_id: str,
        request_payload: dict[str, Any],
        result_payload: dict[str, Any],
        audit: AuditContext | None = None,
    ) -> AnalysisVersion: ...

    def list_analysis_versions(
        self, *, tenant_id: str, project_id: str, limit: int, cursor: str | None
    ) -> tuple[list[AnalysisVersion], str | None]: ...

    def get_analysis_version(
        self, *, tenant_id: str, project_id: str, version: int
    ) -> AnalysisVersion: ...

    def list_audit_events(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[AuditEvent], str | None]: ...
