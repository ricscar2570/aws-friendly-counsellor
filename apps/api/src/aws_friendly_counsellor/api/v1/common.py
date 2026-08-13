from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Annotated

from fastapi import Header

from aws_friendly_counsellor_contracts import CONTRACT_VERSION, ErrorResponse

from ...core.config import settings
from ...domain.exceptions import DomainError

_TENANT_ID_RE = re.compile(r"^ten_[a-f0-9]{24}$")

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Bearer authentication is required."},
    403: {"model": ErrorResponse, "description": "Authenticated identity lacks permission."},
    404: {"model": ErrorResponse, "description": "Resource was not found."},
    409: {"model": ErrorResponse, "description": "Resource state conflict."},
    422: {"model": ErrorResponse, "description": "Request validation failed."},
    429: {"model": ErrorResponse, "description": "Rate limit exceeded."},
    500: {"model": ErrorResponse, "description": "Unexpected processing failure."},
    503: {"model": ErrorResponse, "description": "Service is not configured."},
}


class TenantContextError(DomainError):
    code = "TENANT_CONTEXT_INVALID"
    status_code = 422


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_id(request: Any) -> str:
    return request.state.request_id


def response_metadata(start_time: float, request: Any) -> dict[str, Any]:
    return {
        "request_id": request_id(request),
        "processing_time_ms": max(0, int((time.perf_counter() - start_time) * 1000)),
        "timestamp": utc_now(),
        "version": settings.app_version,
        "contract_version": CONTRACT_VERSION,
    }


def resolve_tenant_header(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> str:
    if x_tenant_id is None:
        raise TenantContextError("X-Tenant-ID header is required")
    normalized = x_tenant_id.strip().lower()
    if not _TENANT_ID_RE.fullmatch(normalized):
        raise TenantContextError("X-Tenant-ID has an invalid resource identifier")
    return normalized


def ensure_tenant_match(tenant_id: str, scoped_tenant_id: str) -> None:
    if tenant_id != scoped_tenant_id:
        from ...domain.exceptions import NotFoundError

        raise NotFoundError("Tenant not found")
