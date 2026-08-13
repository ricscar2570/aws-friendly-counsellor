from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from aws_friendly_counsellor_contracts import HealthResponse, RootResponse

from .api.v1.resources import resource_router
from .api.v1.router import legacy_router, v1_router
from .core.config import settings
from .core.errors import install_exception_handlers
from .core.request_context import resolve_request_id
from .infrastructure.persistence import get_store


def create_app() -> FastAPI:
    logging.basicConfig(level=settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        description=(
            "Versioned, transparent AWS architecture planning API with tenant-scoped "
            "projects and immutable analysis history. The public contract is exported "
            "under packages/contracts."
        ),
        version=settings.app_version,
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID"],
        expose_headers=["X-Request-ID", "X-API-Version"],
    )

    @application.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request.state.request_id = resolve_request_id(request)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-API-Version"] = settings.api_version
        response.headers["X-App-Environment"] = settings.environment
        response.headers["X-Release-Version"] = settings.release_version
        legacy_successors = {
            "/api/analyze": "/api/v1/analyze",
            "/api/iac": "/api/v1/iac",
            "/api/narrative": "/api/v1/narrative",
        }
        successor = legacy_successors.get(request.url.path)
        if successor:
            response.headers["Deprecation"] = "true"
            response.headers["Link"] = f'<{successor}>; rel="successor-version"'
        return response

    install_exception_handlers(application)

    @application.get("/", response_model=RootResponse, tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "release_version": settings.release_version,
            "environment": settings.environment,
            "status": "healthy",
            "docs": "/docs",
            "api_version": settings.api_version,
        }

    def _health_payload(*, check: str, include_persistence: bool) -> dict[str, str | None]:
        payload: dict[str, str | None] = {
            "status": "healthy",
            "check": check,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.app_version,
            "release_version": settings.release_version,
            "git_sha": settings.git_sha,
            "environment": settings.environment,
            "api_version": settings.api_version,
            "persistence_backend": None,
            "persistence_status": None,
        }
        if include_persistence:
            store = get_store()
            store.health_check()
            payload["persistence_backend"] = store.backend_name
            payload["persistence_status"] = "available"
        return payload

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> dict[str, str | None]:
        return _health_payload(check="combined", include_persistence=True)

    @application.get("/health/live", response_model=HealthResponse, tags=["system"])
    async def health_live() -> dict[str, str | None]:
        return _health_payload(check="liveness", include_persistence=False)

    @application.get("/health/ready", response_model=HealthResponse, tags=["system"])
    async def health_ready() -> dict[str, str | None]:
        return _health_payload(check="readiness", include_persistence=True)

    application.include_router(v1_router)
    application.include_router(resource_router)
    application.include_router(legacy_router)
    return application


app = create_app()
