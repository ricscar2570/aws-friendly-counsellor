from aws_friendly_counsellor.services.iac_generator import generate_iac


def test_iac_connects_api_gateway_to_lambda():
    services = [{"id": "lambda"}, {"id": "api-gateway"}, {"id": "dynamodb"}]
    output = generate_iac(
        services,
        {"primary": "api"},
        5_000,
        region="eu-central-1",
        budget="medium",
    )
    main_tf = output["files"]["main.tf"]
    assert 'resource "aws_api_gateway_integration" "proxy"' in main_tf
    assert 'resource "aws_lambda_permission" "api_gateway"' in main_tf
    assert 'billing_mode = "PAY_PER_REQUEST"' in main_tf
    assert 'default     = "eu-central-1"' in output["files"]["variables.tf"]
