import json
import subprocess
import sys
from pathlib import Path

from aws_friendly_counsellor.main import app
from aws_friendly_counsellor_contracts import AnalysisRequest, ProjectUpdateRequest

ROOT = Path(__file__).resolve().parents[1]


def test_openapi_exposes_versioned_planning_and_persistence_paths():
    schema = app.openapi()
    planning_paths = {path for path in schema["paths"] if path.startswith("/api/")}
    assert planning_paths == {
        "/api/v1/analyze",
        "/api/v1/iac",
        "/api/v1/narrative",
        "/api/v1/tenants",
        "/api/v1/tenants/{tenant_id}",
        "/api/v1/tenants/{tenant_id}/memberships",
        "/api/v1/tenants/{tenant_id}/memberships/{subject}",
        "/api/v1/tenants/{tenant_id}/audit",
        "/api/v1/me",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}",
        "/api/v1/projects/{project_id}/analyses",
        "/api/v1/projects/{project_id}/analyses/{version}",
    }


def test_openapi_declares_shared_error_contract():
    schema = app.openapi()
    responses = schema["paths"]["/api/v1/analyze"]["post"]["responses"]
    assert "422" in responses
    serialized = json.dumps(responses["422"])
    assert "ErrorResponse" in serialized


def test_extra_request_fields_are_rejected_by_contract():
    payload = {
        "description": "A sufficiently detailed web application",
        "estimated_users": 100,
        "budget": "low",
        "region": "eu-west-1",
        "unexpected": True,
    }
    try:
        AnalysisRequest.model_validate(payload)
    except Exception as exc:
        assert "extra_forbidden" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Extra fields must be rejected")


def test_project_update_requires_a_real_change():
    try:
        ProjectUpdateRequest.model_validate({"expected_revision": 1})
    except Exception as exc:
        assert "At least one project field" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("An empty update must be rejected")


def test_committed_contract_snapshots_are_current():
    completed = subprocess.run(
        [sys.executable, "scripts/export_contracts.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
