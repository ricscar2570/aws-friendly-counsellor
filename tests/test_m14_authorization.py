from __future__ import annotations

from fastapi.testclient import TestClient

from aws_friendly_counsellor.main import app

client = TestClient(app)

OWNER = "00000000-0000-4000-8000-000000000001"
ADMIN = "00000000-0000-4000-8000-000000000002"
EDITOR = "00000000-0000-4000-8000-000000000003"
VIEWER = "00000000-0000-4000-8000-000000000004"
OUTSIDER = "00000000-0000-4000-8000-000000000005"
SUSPENDED = "00000000-0000-4000-8000-000000000006"


def identity(subject: str, tenant_id: str | None = None) -> dict[str, str]:
    headers = {"X-Debug-Subject": subject}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    return headers


def provision_tenant() -> str:
    response = client.post(
        "/api/v1/tenants",
        json={"name": "Authorization Lab"},
        headers=identity(OWNER),
    )
    assert response.status_code == 201, response.text
    return response.json()["tenant"]["id"]


def grant(tenant_id: str, subject: str, role: str) -> dict:
    response = client.post(
        f"/api/v1/tenants/{tenant_id}/memberships",
        json={"subject": subject, "role": role},
        headers=identity(OWNER, tenant_id),
    )
    assert response.status_code == 201, response.text
    return response.json()["membership"]


def test_tenant_creator_is_owner_and_outsider_cannot_enumerate_tenant():
    tenant_id = provision_tenant()

    owner_read = client.get(
        f"/api/v1/tenants/{tenant_id}", headers=identity(OWNER, tenant_id)
    )
    assert owner_read.status_code == 200

    outsider = client.get(
        f"/api/v1/tenants/{tenant_id}", headers=identity(OUTSIDER, tenant_id)
    )
    assert outsider.status_code == 404
    assert outsider.json()["error"]["message"] == "Tenant not found"


def test_role_matrix_enforces_viewer_editor_admin_and_owner_boundaries():
    tenant_id = provision_tenant()
    grant(tenant_id, ADMIN, "admin")
    grant(tenant_id, EDITOR, "editor")
    grant(tenant_id, VIEWER, "viewer")

    viewer_read = client.get("/api/v1/projects", headers=identity(VIEWER, tenant_id))
    assert viewer_read.status_code == 200
    viewer_write = client.post(
        "/api/v1/projects",
        json={
            "name": "Blocked project",
            "description": "A sufficiently detailed project description for authorization testing",
            "estimated_users": 100,
            "budget": "low",
            "region": "eu-central-1",
            "status": "draft",
        },
        headers=identity(VIEWER, tenant_id),
    )
    assert viewer_write.status_code == 403

    editor_write = client.post(
        "/api/v1/projects",
        json={
            "name": "Editor project",
            "description": "A sufficiently detailed project description for authorization testing",
            "estimated_users": 100,
            "budget": "medium",
            "region": "eu-central-1",
            "status": "active",
        },
        headers=identity(EDITOR, tenant_id),
    )
    assert editor_write.status_code == 201, editor_write.text
    editor_members = client.get(
        f"/api/v1/tenants/{tenant_id}/memberships",
        headers=identity(EDITOR, tenant_id),
    )
    assert editor_members.status_code == 403

    admin_members = client.get(
        f"/api/v1/tenants/{tenant_id}/memberships",
        headers=identity(ADMIN, tenant_id),
    )
    assert admin_members.status_code == 200
    assert {item["role"] for item in admin_members.json()["memberships"]} >= {
        "owner",
        "admin",
        "editor",
        "viewer",
    }


def test_admin_role_ceiling_and_owner_lockout_protection():
    tenant_id = provision_tenant()
    grant(tenant_id, ADMIN, "admin")
    viewer = grant(tenant_id, VIEWER, "viewer")

    admin_promote_viewer = client.patch(
        f"/api/v1/tenants/{tenant_id}/memberships/{VIEWER}",
        json={"expected_revision": viewer["revision"], "role": "editor"},
        headers=identity(ADMIN, tenant_id),
    )
    assert admin_promote_viewer.status_code == 200
    assert admin_promote_viewer.json()["membership"]["role"] == "editor"

    admin_grant_admin = client.post(
        f"/api/v1/tenants/{tenant_id}/memberships",
        json={"subject": OUTSIDER, "role": "admin"},
        headers=identity(ADMIN, tenant_id),
    )
    assert admin_grant_admin.status_code == 403

    owner_self_change = client.patch(
        f"/api/v1/tenants/{tenant_id}/memberships/{OWNER}",
        json={"expected_revision": 1, "role": "admin"},
        headers=identity(OWNER, tenant_id),
    )
    assert owner_self_change.status_code == 409


def test_suspended_membership_is_denied_even_with_valid_identity():
    tenant_id = provision_tenant()
    membership = grant(tenant_id, SUSPENDED, "viewer")
    response = client.patch(
        f"/api/v1/tenants/{tenant_id}/memberships/{SUSPENDED}",
        json={"expected_revision": membership["revision"], "status": "suspended"},
        headers=identity(OWNER, tenant_id),
    )
    assert response.status_code == 200

    denied = client.get("/api/v1/projects", headers=identity(SUSPENDED, tenant_id))
    assert denied.status_code == 403
    assert "suspended" in denied.json()["error"]["message"].lower()


def test_mutations_emit_durable_tenant_audit_events():
    tenant_id = provision_tenant()
    grant(tenant_id, EDITOR, "editor")
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "Audited project",
            "description": "A sufficiently detailed audited project for the security milestone",
            "estimated_users": 250,
            "budget": "medium",
            "region": "eu-central-1",
            "status": "active",
        },
        headers=identity(EDITOR, tenant_id),
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["project"]["id"]

    analysis = client.post(
        f"/api/v1/projects/{project_id}/analyses",
        json={"advanced_guide": False},
        headers=identity(EDITOR, tenant_id),
    )
    assert analysis.status_code == 201, analysis.text

    audit = client.get(
        f"/api/v1/tenants/{tenant_id}/audit?limit=100",
        headers=identity(OWNER, tenant_id),
    )
    assert audit.status_code == 200, audit.text
    events = audit.json()["audit_events"]
    actions = {event["action"] for event in events}
    assert {
        "tenant.created",
        "membership.created",
        "project.created",
        "analysis.created",
    } <= actions
    assert all(event["request_id"] for event in events)
    assert any(event["actor_subject"] == EDITOR for event in events)


def test_tenant_selector_is_required_but_never_grants_authority():
    tenant_id = provision_tenant()
    missing_selector = client.get("/api/v1/projects", headers=identity(OWNER))
    assert missing_selector.status_code == 422

    outsider_with_selector = client.get(
        "/api/v1/projects", headers=identity(OUTSIDER, tenant_id)
    )
    assert outsider_with_selector.status_code == 404
