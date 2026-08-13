from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from aws_friendly_counsellor.security.auth import authenticated_principal, reset_auth_cache


def _request(*, headers: dict[str, str] | None = None, event: dict | None = None) -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    scope = {"type": "http", "method": "GET", "path": "/", "headers": raw_headers}
    if event is not None:
        scope["aws.event"] = event
    return Request(scope)


def test_local_identity_is_disabled_outside_local_and_test(monkeypatch):
    reset_auth_cache()
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("ALLOW_LOCAL_IDENTITY", "true")
    monkeypatch.setenv("LOCAL_IDENTITY_SUBJECT", "debug-user")
    with pytest.raises(HTTPException) as exc:
        authenticated_principal(_request())
    assert exc.value.status_code == 401


def test_local_identity_is_available_only_when_explicitly_enabled(monkeypatch):
    reset_auth_cache()
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("ALLOW_LOCAL_IDENTITY", "true")
    monkeypatch.setenv("LOCAL_IDENTITY_SUBJECT", "test-user")
    principal = authenticated_principal(_request())
    assert principal.subject == "test-user"
    assert principal.token_use == "local"


def test_api_gateway_cognito_claims_override_local_identity(monkeypatch):
    reset_auth_cache()
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("ALLOW_LOCAL_IDENTITY", "true")
    monkeypatch.setenv("LOCAL_IDENTITY_SUBJECT", "local-user")
    request = _request(
        event={
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "11111111-1111-4111-8111-111111111111",
                        "cognito:username": "real-user",
                        "token_use": "id",
                        "iss": "https://cognito-idp.eu-central-1.amazonaws.com/pool",
                    }
                }
            }
        }
    )
    principal = authenticated_principal(request)
    assert principal.subject == "11111111-1111-4111-8111-111111111111"
    assert principal.username == "real-user"
    assert principal.token_use == "id"
