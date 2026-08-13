from fastapi.testclient import TestClient

from aws_friendly_counsellor.infrastructure.persistence import reset_store
from aws_friendly_counsellor.main import app

client = TestClient(app)


def create_tenant(name: str = "Acme Cloud") -> str:
    response = client.post("/api/v1/tenants", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["tenant"]["id"]


def create_project(tenant_id: str, name: str = "Customer Portal") -> dict:
    response = client.post(
        "/api/v1/projects",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "name": name,
            "description": "A customer web portal with login, files, and analytics",
            "estimated_users": 5000,
            "budget": "medium",
            "region": "eu-central-1",
            "status": "active",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project"]


def test_tenant_project_crud_and_health_report_persistence():
    tenant_id = create_tenant()
    project = create_project(tenant_id)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["persistence_backend"] == "sqlite"
    assert health.json()["persistence_status"] == "available"

    fetched = client.get(
        f"/api/v1/projects/{project['id']}", headers={"X-Tenant-ID": tenant_id}
    )
    assert fetched.status_code == 200
    assert fetched.json()["project"] == project


def test_tenant_boundary_prevents_cross_tenant_reads_and_lists():
    tenant_a = create_tenant("Tenant Alpha")
    tenant_b = create_tenant("Tenant Beta")
    project_a = create_project(tenant_a, "Alpha Project")
    create_project(tenant_b, "Beta Project")

    hidden = client.get(
        f"/api/v1/projects/{project_a['id']}", headers={"X-Tenant-ID": tenant_b}
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "NOT_FOUND"

    projects_b = client.get("/api/v1/projects", headers={"X-Tenant-ID": tenant_b})
    assert projects_b.status_code == 200
    assert [item["name"] for item in projects_b.json()["projects"]] == ["Beta Project"]


def test_project_update_uses_optimistic_concurrency():
    tenant_id = create_tenant()
    project = create_project(tenant_id)

    updated = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers={"X-Tenant-ID": tenant_id},
        json={"expected_revision": 1, "name": "Renamed Portal"},
    )
    assert updated.status_code == 200
    assert updated.json()["project"]["revision"] == 2

    stale = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers={"X-Tenant-ID": tenant_id},
        json={"expected_revision": 1, "name": "Lost Update"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "REVISION_CONFLICT"


def test_analysis_versions_are_sequential_and_immutable():
    tenant_id = create_tenant()
    project = create_project(tenant_id)
    endpoint = f"/api/v1/projects/{project['id']}/analyses"
    headers = {"X-Tenant-ID": tenant_id}

    first = client.post(endpoint, headers=headers, json={"advanced_guide": False})
    assert first.status_code == 201, first.text
    first_record = first.json()["analysis_version"]
    assert first_record["version"] == 1
    assert first_record["request"]["description"] == project["description"]
    assert first_record["result"]["project_id"] == project["id"]

    update = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=headers,
        json={
            "expected_revision": 1,
            "description": "A realtime collaboration platform with chat and WebSockets",
        },
    )
    assert update.status_code == 200

    second = client.post(endpoint, headers=headers, json={"advanced_guide": True})
    assert second.status_code == 201
    assert second.json()["analysis_version"]["version"] == 2

    historical = client.get(f"{endpoint}/1", headers=headers)
    assert historical.status_code == 200
    historical_record = historical.json()["analysis_version"]
    assert historical_record["request"] == first_record["request"]
    assert historical_record["result"] == first_record["result"]

    listing = client.get(endpoint, headers=headers)
    assert listing.status_code == 200
    assert [item["version"] for item in listing.json()["analysis_versions"]] == [1, 2]


def test_project_and_analysis_pagination_use_opaque_cursors():
    tenant_id = create_tenant()
    for index in range(3):
        create_project(tenant_id, f"Project {index}")

    first_page = client.get(
        "/api/v1/projects?limit=2", headers={"X-Tenant-ID": tenant_id}
    )
    assert first_page.status_code == 200
    body = first_page.json()
    assert len(body["projects"]) == 2
    assert body["next_cursor"]

    second_page = client.get(
        "/api/v1/projects",
        headers={"X-Tenant-ID": tenant_id},
        params={"limit": 2, "cursor": body["next_cursor"]},
    )
    assert second_page.status_code == 200
    assert len(second_page.json()["projects"]) == 1
    assert second_page.json()["next_cursor"] is None


def test_sqlite_data_survives_store_recreation(monkeypatch, tmp_path):
    database = tmp_path / "durable.db"
    monkeypatch.setenv("SQLITE_PATH", str(database))
    reset_store()
    tenant_id = create_tenant("Durable Tenant")
    project = create_project(tenant_id, "Durable Project")

    reset_store()
    response = client.get(
        f"/api/v1/projects/{project['id']}", headers={"X-Tenant-ID": tenant_id}
    )
    assert response.status_code == 200
    assert response.json()["project"]["name"] == "Durable Project"


def test_tenant_header_is_required_and_validated():
    missing = client.get("/api/v1/projects")
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "TENANT_CONTEXT_INVALID"

    invalid = client.get("/api/v1/projects", headers={"X-Tenant-ID": "tenant-1"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "TENANT_CONTEXT_INVALID"


def test_invalid_cursor_uses_stable_validation_error():
    tenant_id = create_tenant()
    response = client.get(
        "/api/v1/projects",
        headers={"X-Tenant-ID": tenant_id},
        params={"cursor": "not-a-valid-cursor"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_tenant_slug_and_tenant_path_mismatch_are_hidden():
    tenant_a = create_tenant("Shared Name")
    duplicate = client.post("/api/v1/tenants", json={"name": "Shared Name"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    tenant_b = create_tenant("Different Name")
    mismatch = client.get(
        f"/api/v1/tenants/{tenant_a}", headers={"X-Tenant-ID": tenant_b}
    )
    assert mismatch.status_code == 404


def test_archived_project_rejects_new_analysis_versions():
    tenant_id = create_tenant()
    project = create_project(tenant_id)
    archived = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers={"X-Tenant-ID": tenant_id},
        json={"expected_revision": 1, "status": "archived"},
    )
    assert archived.status_code == 200
    response = client.post(
        f"/api/v1/projects/{project['id']}/analyses",
        headers={"X-Tenant-ID": tenant_id},
        json={},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_analysis_history_pagination():
    tenant_id = create_tenant()
    project = create_project(tenant_id)
    endpoint = f"/api/v1/projects/{project['id']}/analyses"
    headers = {"X-Tenant-ID": tenant_id}
    for _ in range(3):
        assert client.post(endpoint, headers=headers, json={}).status_code == 201

    first = client.get(endpoint, headers=headers, params={"limit": 2})
    assert first.status_code == 200
    first_body = first.json()
    assert [item["version"] for item in first_body["analysis_versions"]] == [1, 2]
    assert first_body["next_cursor"]

    second = client.get(
        endpoint,
        headers=headers,
        params={"limit": 2, "cursor": first_body["next_cursor"]},
    )
    assert second.status_code == 200
    assert [item["version"] for item in second.json()["analysis_versions"]] == [3]


def test_sqlite_schema_records_migration_and_composite_foreign_key(monkeypatch, tmp_path):
    import sqlite3

    database = tmp_path / "schema.db"
    monkeypatch.setenv("SQLITE_PATH", str(database))
    reset_store()
    create_tenant("Schema Tenant")

    connection = sqlite3.connect(database)
    try:
        migration = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        ).fetchone()
        foreign_keys = connection.execute("PRAGMA foreign_key_list(analysis_versions)").fetchall()
    finally:
        connection.close()
    assert migration == (2,)
    assert {row[3] for row in foreign_keys} == {"tenant_id", "project_id"}
