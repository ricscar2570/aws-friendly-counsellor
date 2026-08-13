from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, HTTPException

from ..domain.entities import Membership
from ..domain.exceptions import NotFoundError
from ..domain.repositories import PersistenceStore
from ..infrastructure.persistence import get_store
from .auth import Principal, authenticated_principal
from ..api.v1.common import resolve_tenant_header

TenantRole = Literal["viewer", "editor", "admin", "owner"]
_ROLE_RANK: dict[str, int] = {
    "viewer": 10,
    "editor": 20,
    "admin": 30,
    "owner": 40,
}


@dataclass(frozen=True, slots=True)
class TenantAccessContext:
    tenant_id: str
    principal: Principal
    membership: Membership

    @property
    def role(self) -> str:
        return self.membership.role


def role_at_least(actual: str, required: TenantRole) -> bool:
    return _ROLE_RANK.get(actual, -1) >= _ROLE_RANK[required]


def require_tenant_role(required: TenantRole):
    """Create a dependency that binds a verified subject to durable tenant membership.

    X-Tenant-ID is only a tenant selector. It grants no authority on its own.
    """

    def dependency(
        tenant_id: Annotated[str, Depends(resolve_tenant_header)],
        principal: Annotated[Principal, Depends(authenticated_principal)],
        store: Annotated[PersistenceStore, Depends(get_store)],
    ) -> TenantAccessContext:
        try:
            tenant = store.get_tenant(tenant_id)
            membership = store.get_membership(
                tenant_id=tenant_id, subject=principal.subject
            )
        except NotFoundError as exc:
            # Avoid confirming whether a tenant exists to an unrelated principal.
            raise NotFoundError("Tenant not found") from exc
        if tenant.status != "active":
            raise HTTPException(status_code=403, detail="Tenant is suspended")
        if membership.status != "active":
            raise HTTPException(status_code=403, detail="Tenant membership is suspended")
        if not role_at_least(membership.role, required):
            raise HTTPException(
                status_code=403,
                detail=f"Tenant role {required} or higher is required",
            )
        return TenantAccessContext(
            tenant_id=tenant_id,
            principal=principal,
            membership=membership,
        )

    return dependency


def can_manage_membership(
    *, actor_role: str, current_role: str | None, desired_role: str
) -> bool:
    """Enforce the role-management ceiling.

    Owners may manage every role. Admins may manage editor/viewer memberships only.
    Editors and viewers cannot manage memberships.
    """

    if actor_role == "owner":
        return True
    if actor_role != "admin":
        return False
    if desired_role in {"owner", "admin"}:
        return False
    if current_role in {"owner", "admin"}:
        return False
    return True
