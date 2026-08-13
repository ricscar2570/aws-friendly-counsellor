from __future__ import annotations

import os
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request

_SUBJECT_PATTERN = re.compile(r"^[A-Za-z0-9._:@+\-/=]{1,256}$")
_rate_limit_storage: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = threading.Lock()


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated application identity derived from a verified Cognito token."""

    subject: str
    username: str | None = None
    token_use: str | None = None
    issuer: str | None = None


def _claims_from_aws_event(request: Request) -> dict[str, Any]:
    """Extract API Gateway authorizer claims exposed by Mangum in the ASGI scope."""

    event = request.scope.get("aws.event")
    if not isinstance(event, dict):
        return {}
    request_context = event.get("requestContext")
    if not isinstance(request_context, dict):
        return {}
    authorizer = request_context.get("authorizer")
    if not isinstance(authorizer, dict):
        return {}

    # REST API + COGNITO_USER_POOLS authorizer.
    claims = authorizer.get("claims")
    if isinstance(claims, dict):
        return claims

    # Defensive compatibility with API Gateway HTTP API JWT-shaped events.
    jwt = authorizer.get("jwt")
    if isinstance(jwt, dict) and isinstance(jwt.get("claims"), dict):
        return jwt["claims"]
    return {}


def _local_identity_enabled() -> bool:
    environment = os.getenv("APP_ENVIRONMENT", "local").strip().lower()
    if environment not in {"local", "test"}:
        return False
    return os.getenv("ALLOW_LOCAL_IDENTITY", "false").strip().lower() == "true"


def _claims_from_local_identity(request: Request) -> dict[str, str]:
    if not _local_identity_enabled():
        return {}
    subject = request.headers.get("X-Debug-Subject", "").strip() or os.getenv(
        "LOCAL_IDENTITY_SUBJECT", ""
    ).strip()
    if not subject:
        return {}
    username = request.headers.get("X-Debug-Username", "").strip() or os.getenv(
        "LOCAL_IDENTITY_USERNAME", ""
    ).strip()
    return {
        "sub": subject,
        "cognito:username": username or subject,
        "token_use": "local",
        "iss": "local-development",
    }


def _principal_from_claims(claims: dict[str, Any]) -> Principal:
    subject = str(claims.get("sub", "")).strip()
    if not subject or not _SUBJECT_PATTERN.fullmatch(subject):
        raise HTTPException(
            status_code=401,
            detail="Authenticated token is missing a valid subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username_value = claims.get("cognito:username") or claims.get("username")
    username = str(username_value).strip() if username_value is not None else None
    token_use_value = claims.get("token_use")
    issuer_value = claims.get("iss")
    return Principal(
        subject=subject,
        username=username or None,
        token_use=str(token_use_value).strip() if token_use_value is not None else None,
        issuer=str(issuer_value).strip() if issuer_value is not None else None,
    )


def check_rate_limit(principal_key: str) -> None:
    """Process-local defense in depth; API Gateway provides the distributed throttle."""

    request_limit = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    if request_limit < 1 or window_seconds < 1:
        raise RuntimeError("Rate limit settings must be positive integers")
    now = time.monotonic()
    cutoff = now - window_seconds
    with _rate_limit_lock:
        requests = _rate_limit_storage[principal_key]
        while requests and requests[0] <= cutoff:
            requests.popleft()
        if len(requests) >= request_limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
        requests.append(now)


def reset_auth_cache() -> None:
    with _rate_limit_lock:
        _rate_limit_storage.clear()


def authenticated_principal(request: Request) -> Principal:
    claims = _claims_from_aws_event(request)
    if not claims:
        claims = _claims_from_local_identity(request)
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Bearer authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    principal = _principal_from_claims(claims)
    check_rate_limit(f"subject:{principal.subject}")
    return principal


def authorize_request(
    principal: Principal = Depends(authenticated_principal),
) -> Principal:
    """Compatibility dependency for authenticated, non-tenant-specific routes."""

    return principal
