from aws_friendly_counsellor.services.recommender import recommend_services


def test_web_application_profile_uses_canonical_ids():
    services = recommend_services(
        {
            "primary": "web_application",
            "features": ["web_application", "authentication"],
        },
        5_000,
        budget="medium",
        region="eu-central-1",
    )
    ids = {service["id"] for service in services}
    assert {"lambda", "api-gateway", "dynamodb", "s3", "cognito"}.issubset(ids)
    assert all(service["region"] == "eu-central-1" for service in services)


def test_budget_changes_optional_controls():
    classification = {"primary": "api", "features": ["api"]}
    low_ids = {
        service["id"]
        for service in recommend_services(classification, 1_000, budget="low")
    }
    high_ids = {
        service["id"]
        for service in recommend_services(classification, 1_000, budget="high")
    }
    assert "xray" not in low_ids
    assert {"cloudwatch", "xray", "waf"}.issubset(high_ids)
