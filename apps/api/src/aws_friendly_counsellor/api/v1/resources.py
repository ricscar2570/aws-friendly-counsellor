from __future__ import annotations

import re
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from aws_friendly_counsellor_contracts import (
    AnalysisVersionListResponse,
    AnalysisVersionResponse,
    AuditEventListResponse,
    IdentityResponse,
    ProjectAnalysisCreateRequest,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    TenantCreateRequest,
    TenantMembershipCreateRequest,
    TenantMembershipListResponse,
    TenantMembershipResponse,
    TenantMembershipUpdateRequest,
    TenantResponse,
)

from ...application.analysis_service import analysis_request_from_project, build_analysis_result
from ...domain.entities import AuditContext
from ...domain.exceptions import ConflictError
from ...domain.repositories import PersistenceStore
from ...infrastructure.persistence import get_store
from ...security.auth import Principal, authenticated_principal
from ...security.authorization import (
    TenantAccessContext,
    can_manage_membership,
    require_tenant_role,
)
from .common import ERROR_RESPONSES, ensure_tenant_match, request_id, response_metadata

resource_router = APIRouter(
    prefix="/api/v1", tags=["resources-v1"], responses=ERROR_RESPONSES
)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug[:63] or "tenant"


def _store() -> PersistenceStore:
    return get_store()


def _invalid_cursor(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


def _audit(
    request: Request,
    principal: Principal,
    action: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> AuditContext:
    return AuditContext(
        actor_subject=principal.subject,
        action=action,
        request_id=request_id(request),
        metadata=metadata,
    )


@resource_router.get(
    "/me",
    response_model=IdentityResponse,
    summary="Read the authenticated application identity",
)
def get_identity(
    request: Request,
    principal: Annotated[Principal, Depends(authenticated_principal)],
) -> dict[str, Any]:
    start_time = time.perf_counter()
    return {
        "subject": principal.subject,
        "username": principal.username,
        "metadata": response_metadata(start_time, request),
    }


@resource_router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a tenant and bind the creator as owner",
)
def create_tenant(
    payload: TenantCreateRequest,
    request: Request,
    principal: Annotated[Principal, Depends(authenticated_principal)],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    tenant = store.create_tenant(
        name=payload.name,
        slug=payload.slug or _slugify(payload.name),
        owner_subject=principal.subject,
        audit=_audit(request, principal, "tenant.created"),
    )
    return {"tenant": tenant.to_dict(), "metadata": response_metadata(start_time, request)}


@resource_router.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="Read the current tenant",
)
def get_tenant(
    tenant_id: str,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("viewer"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    ensure_tenant_match(tenant_id, access.tenant_id)
    tenant = store.get_tenant(tenant_id)
    return {"tenant": tenant.to_dict(), "metadata": response_metadata(start_time, request)}


@resource_router.get(
    "/tenants/{tenant_id}/memberships",
    response_model=TenantMembershipListResponse,
    summary="List tenant memberships",
)
def list_memberships(
    tenant_id: str,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("admin"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: str | None = None,
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    ensure_tenant_match(tenant_id, access.tenant_id)
    try:
        memberships, next_cursor = store.list_memberships(
            tenant_id=tenant_id, limit=limit, cursor=cursor
        )
    except ValueError as exc:
        raise _invalid_cursor(exc) from exc
    return {
        "memberships": [membership.to_dict() for membership in memberships],
        "next_cursor": next_cursor,
        "metadata": response_metadata(start_time, request),
    }


@resource_router.post(
    "/tenants/{tenant_id}/memberships",
    response_model=TenantMembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant a tenant membership",
)
def create_membership(
    tenant_id: str,
    payload: TenantMembershipCreateRequest,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("admin"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    ensure_tenant_match(tenant_id, access.tenant_id)
    if not can_manage_membership(
        actor_role=access.role, current_role=None, desired_role=payload.role
    ):
        raise HTTPException(status_code=403, detail="Role grant exceeds the actor's authority")
    membership = store.create_membership(
        tenant_id=tenant_id,
        subject=payload.subject,
        role=payload.role,
        audit=_audit(
            request,
            access.principal,
            "membership.created",
            metadata={"role": payload.role, "subject": payload.subject},
        ),
    )
    return {
        "membership": membership.to_dict(),
        "metadata": response_metadata(start_time, request),
    }


@resource_router.patch(
    "/tenants/{tenant_id}/memberships/{subject}",
    response_model=TenantMembershipResponse,
    summary="Change a tenant membership using optimistic concurrency",
)
def update_membership(
    tenant_id: str,
    subject: str,
    payload: TenantMembershipUpdateRequest,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("admin"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    ensure_tenant_match(tenant_id, access.tenant_id)
    current = store.get_membership(tenant_id=tenant_id, subject=subject)
    desired_role = payload.role or current.role
    if subject == access.principal.subject and current.role == "owner":
        raise ConflictError("Owners cannot change their own owner membership")
    if not can_manage_membership(
        actor_role=access.role,
        current_role=current.role,
        desired_role=desired_role,
    ):
        raise HTTPException(status_code=403, detail="Membership change exceeds the actor's authority")
    membership = store.update_membership(
        tenant_id=tenant_id,
        subject=subject,
        expected_revision=payload.expected_revision,
        role=payload.role,
        status=payload.status,
        audit=_audit(
            request,
            access.principal,
            "membership.updated",
            metadata={
                "subject": subject,
                "role": payload.role,
                "status": payload.status,
            },
        ),
    )
    return {
        "membership": membership.to_dict(),
        "metadata": response_metadata(start_time, request),
    }


@resource_router.get(
    "/tenants/{tenant_id}/audit",
    response_model=AuditEventListResponse,
    summary="Read the durable tenant audit trail",
)
def list_audit_events(
    tenant_id: str,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("admin"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: str | None = None,
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    ensure_tenant_match(tenant_id, access.tenant_id)
    try:
        events, next_cursor = store.list_audit_events(
            tenant_id=tenant_id, limit=limit, cursor=cursor
        )
    except ValueError as exc:
        raise _invalid_cursor(exc) from exc
    return {
        "audit_events": [event.to_dict() for event in events],
        "next_cursor": next_cursor,
        "metadata": response_metadata(start_time, request),
    }


@resource_router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tenant-scoped project",
)
def create_project(
    payload: ProjectCreateRequest,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("editor"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    project = store.create_project(
        tenant_id=access.tenant_id,
        **payload.model_dump(),
        audit=_audit(request, access.principal, "project.created"),
    )
    return {"project": project.to_dict(), "metadata": response_metadata(start_time, request)}


@resource_router.get(
    "/projects",
    response_model=ProjectListResponse,
    summary="List projects without crossing tenant boundaries",
)
def list_projects(
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("viewer"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: str | None = None,
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    try:
        projects, next_cursor = store.list_projects(
            tenant_id=access.tenant_id, limit=limit, cursor=cursor
        )
    except ValueError as exc:
        raise _invalid_cursor(exc) from exc
    return {
        "projects": [project.to_dict() for project in projects],
        "next_cursor": next_cursor,
        "metadata": response_metadata(start_time, request),
    }


@resource_router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Read a tenant-scoped project",
)
def get_project(
    project_id: str,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("viewer"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    project = store.get_project(tenant_id=access.tenant_id, project_id=project_id)
    return {"project": project.to_dict(), "metadata": response_metadata(start_time, request)}


@resource_router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project using optimistic concurrency",
)
def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("editor"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    changes = payload.model_dump(exclude={"expected_revision"}, exclude_none=True)
    project = store.update_project(
        tenant_id=access.tenant_id,
        project_id=project_id,
        expected_revision=payload.expected_revision,
        changes=changes,
        audit=_audit(request, access.principal, "project.updated"),
    )
    return {"project": project.to_dict(), "metadata": response_metadata(start_time, request)}


@resource_router.post(
    "/projects/{project_id}/analyses",
    response_model=AnalysisVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run and persist an immutable analysis version",
)
def create_project_analysis(
    project_id: str,
    payload: ProjectAnalysisCreateRequest,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("editor"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    project = store.get_project(tenant_id=access.tenant_id, project_id=project_id)
    if project.status == "archived":
        raise ConflictError("Archived projects cannot receive new analysis versions")
    analysis_request = analysis_request_from_project(project, **payload.model_dump())
    result = build_analysis_result(
        analysis_request,
        project_id=project.id,
        request_id=request_id(request),
        start_time=start_time,
    )
    version = store.create_analysis_version(
        tenant_id=access.tenant_id,
        project_id=project_id,
        request_payload=analysis_request.model_dump(mode="json"),
        result_payload=result.model_dump(mode="json", exclude_none=True),
        audit=_audit(request, access.principal, "analysis.created"),
    )
    return {
        "analysis_version": {
            "analysis_id": version.analysis_id,
            "tenant_id": version.tenant_id,
            "project_id": version.project_id,
            "version": version.version,
            "request": version.request_payload,
            "result": version.result_payload,
            "created_at": version.created_at,
        },
        "metadata": response_metadata(start_time, request),
    }


@resource_router.get(
    "/projects/{project_id}/analyses",
    response_model=AnalysisVersionListResponse,
    summary="List immutable analysis versions",
)
def list_project_analyses(
    project_id: str,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("viewer"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: str | None = None,
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    try:
        versions, next_cursor = store.list_analysis_versions(
            tenant_id=access.tenant_id,
            project_id=project_id,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise _invalid_cursor(exc) from exc
    summaries = []
    for version in versions:
        result = version.result_payload
        summaries.append(
            {
                "analysis_id": version.analysis_id,
                "project_id": version.project_id,
                "version": version.version,
                "project_type": result["analysis"]["project_type"],
                "typical_monthly_cost": result["cost_analysis"]["summary"]["typical"],
                "created_at": version.created_at,
            }
        )
    return {
        "analysis_versions": summaries,
        "next_cursor": next_cursor,
        "metadata": response_metadata(start_time, request),
    }


@resource_router.get(
    "/projects/{project_id}/analyses/{version}",
    response_model=AnalysisVersionResponse,
    summary="Read one immutable analysis version",
)
def get_project_analysis(
    project_id: str,
    version: int,
    request: Request,
    access: Annotated[TenantAccessContext, Depends(require_tenant_role("viewer"))],
    store: PersistenceStore = Depends(_store),
) -> dict[str, Any]:
    if version < 1:
        raise HTTPException(status_code=422, detail="Version must be at least 1")
    start_time = time.perf_counter()
    item = store.get_analysis_version(
        tenant_id=access.tenant_id, project_id=project_id, version=version
    )
    return {
        "analysis_version": {
            "analysis_id": item.analysis_id,
            "tenant_id": item.tenant_id,
            "project_id": item.project_id,
            "version": item.version,
            "request": item.request_payload,
            "result": item.result_payload,
            "created_at": item.created_at,
        },
        "metadata": response_metadata(start_time, request),
    }
