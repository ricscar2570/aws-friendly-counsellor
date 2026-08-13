from aws_friendly_counsellor.services.classifier import classify_use_case


def test_ecommerce_classification():
    result = classify_use_case(
        "An online store with product catalog, shopping cart, checkout and payments"
    )
    assert result["primary"] == "ecommerce"
    assert result["confidence"] >= 0.7
    assert "deterministic_rules" in result["classifier"]


def test_unknown_description_has_safe_default():
    result = classify_use_case(
        "A private experimental concept for internal staff workflows"
    )
    assert result["primary"] == "web_application"
    assert result["features"] == ["web_application"]
