from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Tenant:
    id: str
    name: str
    slug: str
    status: str
    created_at: str
    updated_at: str
    revision: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Membership:
    tenant_id: str
    subject: str
    role: str
    status: str
    created_at: str
    updated_at: str
    revision: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    tenant_id: str
    name: str
    description: str
    estimated_users: int
    budget: str
    region: str
    status: str
    created_at: str
    updated_at: str
    revision: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AnalysisVersion:
    analysis_id: str
    tenant_id: str
    project_id: str
    version: int
    request_payload: dict[str, Any]
    result_payload: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: str
    tenant_id: str
    actor_subject: str
    action: str
    resource_type: str
    resource_id: str
    request_id: str
    occurred_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuditContext:
    actor_subject: str
    action: str
    request_id: str
    metadata: dict[str, Any] | None = None
