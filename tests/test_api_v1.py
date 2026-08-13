from fastapi.testclient import TestClient

from aws_friendly_counsellor.main import app

client = TestClient(app)

PAYLOAD = {
    "description": "A web application with customer login, file uploads, and analytics dashboard",
    "estimated_users": 5_000,
    "budget": "medium",
    "region": "eu-central-1",
    "advanced_guide": True,
}


def test_health_and_root_publish_api_version():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert health.json()["api_version"] == "v1"
    assert health.headers["X-API-Version"] == "v1"

    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["docs"] == "/docs"


def test_analyze_v1_has_typed_nonzero_cost_breakdown():
    response = client.post(
        "/api/v1/analyze",
        json=PAYLOAD,
        headers={"X-Request-ID": "contract-test-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["classifier"] == "deterministic_rules_v1"
    assert data["cost_analysis"]["summary"]["maximum_value"] > 0
    assert data["cost_analysis"]["breakdown"]
    assert all("id" in service for service in data["services"])
    assert data["implementation_guide"]["project_context"]["region"] == "eu-central-1"
    assert data["metadata"]["request_id"] == "contract-test-001"
    assert data["metadata"]["contract_version"] == "1.3.0"
    assert response.headers["X-Request-ID"] == "contract-test-001"


def test_iac_v1_returns_connected_baseline():
    response = client.post("/api/v1/iac", json=PAYLOAD)
    assert response.status_code == 200
    main_tf = response.json()["terraform"]["files"]["main.tf"]
    assert "aws_api_gateway_integration" in main_tf
    assert "aws_lambda_permission" in main_tf


def test_narrative_v1_uses_dynamic_cost_model():
    response = client.post("/api/v1/narrative", json=PAYLOAD)
    assert response.status_code == 200
    narrative = response.json()["narrative_html"]
    assert "Cost planning" in narrative
    assert "not a live AWS quotation" in narrative
    assert "Amazon" in narrative or "AWS" in narrative


def test_legacy_routes_remain_compatible_but_are_not_in_openapi():
    legacy = client.post("/api/analyze", json=PAYLOAD)
    current = client.post("/api/v1/analyze", json=PAYLOAD)
    assert legacy.status_code == current.status_code == 200
    assert legacy.json()["analysis"] == current.json()["analysis"]
    assert legacy.headers["Deprecation"] == "true"
    assert "successor-version" in legacy.headers["Link"]
    assert "/api/analyze" not in app.openapi()["paths"]


def test_validation_errors_use_stable_error_envelope():
    response = client.post("/api/v1/analyze", json={**PAYLOAD, "region": "moon-1"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert error["details"]


def test_basic_guide_omits_null_advanced_operations():
    response = client.post(
        "/api/v1/analyze", json={**PAYLOAD, "advanced_guide": False}
    )
    assert response.status_code == 200
    guide = response.json()["implementation_guide"]
    assert guide["format"] == "essential"
    assert "operations" not in guide


def test_all_supported_use_case_profiles_satisfy_the_public_response_contract():
    scenarios = [
        ("An ecommerce online store with checkout, orders, and payments", "low"),
        ("A multi-vendor marketplace for sellers, buyers, and commissions", "medium"),
        ("A social network with followers, feeds, likes, and comments", "high"),
        ("A multi-tenant SaaS with subscriptions and organization workspaces", "medium"),
        ("An editorial blog and news site with articles and content management", "low"),
        ("A mobile app backend for iOS and Android with push notifications", "medium"),
        ("A REST API with webhooks and backend service endpoints", "high"),
        ("A realtime live chat application using WebSocket collaboration", "medium"),
        ("An analytics dashboard with reporting, metrics, and data pipelines", "high"),
        ("A file storage portal for document and photo uploads", "low"),
        ("A browser-based web application and customer portal", "medium"),
    ]
    for index, (description, budget) in enumerate(scenarios):
        response = client.post(
            "/api/v1/analyze",
            json={
                **PAYLOAD,
                "description": description,
                "budget": budget,
                "advanced_guide": index % 2 == 0,
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["services"]
        assert body["cost_analysis"]["summary"]["maximum_value"] >= 0
        assert body["metadata"]["contract_version"] == "1.3.0"


def test_authentication_errors_use_the_public_error_contract(monkeypatch):
    monkeypatch.setenv("ALLOW_LOCAL_IDENTITY", "false")
    response = client.post("/api/v1/analyze", json=PAYLOAD)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_invalid_external_request_id_is_replaced():
    invalid_id = "bad request id with spaces"
    response = client.get("/health", headers={"X-Request-ID": invalid_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != invalid_id
    assert " " not in response.headers["X-Request-ID"]


def test_all_legacy_routes_advertise_successor_versions():
    for legacy_path, successor in (
        ("/api/analyze", "/api/v1/analyze"),
        ("/api/iac", "/api/v1/iac"),
        ("/api/narrative", "/api/v1/narrative"),
    ):
        response = client.post(legacy_path, json=PAYLOAD)
        assert response.status_code == 200
        assert response.headers["Deprecation"] == "true"
        assert successor in response.headers["Link"]


def test_liveness_and_readiness_are_separate_and_publish_release_metadata():
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.status_code == ready.status_code == 200
    assert live.json()["check"] == "liveness"
    assert live.json()["persistence_backend"] is None
    assert ready.json()["check"] == "readiness"
    assert ready.json()["persistence_backend"] in {"sqlite", "dynamodb"}
    assert live.json()["release_version"] == "local"
    assert live.headers["X-App-Environment"] == "test"
    assert live.headers["X-Release-Version"] == "local"
