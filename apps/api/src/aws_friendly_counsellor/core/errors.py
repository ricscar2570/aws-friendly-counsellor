from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from aws_friendly_counsellor_contracts import ErrorResponse
from aws_friendly_counsellor_contracts.models import ErrorItem

from ..domain.exceptions import DomainError


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _payload(
    request: Request,
    *,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return ErrorResponse(
        error=ErrorItem(
            code=code,
            message=message,
            request_id=_request_id(request),
            details=details,
        )
    ).model_dump(exclude_none=True)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "location": list(error.get("loc", ())),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "validation_error"),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_payload(
                request,
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details=details,
            ),
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(request, code=exc.code, message=exc.message),
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        status_codes = {
            401: "AUTHENTICATION_REQUIRED",
            403: "ACCESS_DENIED",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
            503: "SERVICE_NOT_CONFIGURED",
        }
        code = status_codes.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(request, code=code, message=message),
            headers=exc.headers,
        )
