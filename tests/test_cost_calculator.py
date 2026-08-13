from aws_friendly_counsellor.services.cost_calculator import calculate_costs


def test_costs_accept_recommended_service_objects_and_are_nonzero():
    services = [
        {"id": "lambda", "name": "AWS Lambda"},
        {"id": "api-gateway", "name": "Amazon API Gateway"},
        {"id": "dynamodb", "name": "Amazon DynamoDB"},
    ]
    result = calculate_costs(services, 5_000, region="eu-west-1", budget="low")
    assert result["summary"]["maximum_value"] > 0
    assert set(result["breakdown"]) == {"lambda", "api-gateway", "dynamodb"}
    assert result["region"] == "eu-west-1"


def test_legacy_display_names_are_normalized():
    result = calculate_costs(["AWS Lambda", "Amazon S3"], 500)
    assert set(result["breakdown"]) == {"lambda", "s3"}
