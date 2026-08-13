from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, Iterable

try:
    from .cost_calculator import normalize_service_id
except ImportError:  # pragma: no cover
    from services.cost_calculator import normalize_service_id

logger = logging.getLogger(__name__)

SUPPORTED_TERRAFORM_SERVICES = {"lambda", "api-gateway", "dynamodb", "s3", "cognito", "cloudwatch"}


def _service_ids(services: Iterable[Any]) -> list[str]:
    ids: list[str] = []
    for service in services:
        service_id = normalize_service_id(service)
        if service_id and service_id not in ids:
            ids.append(service_id)
    return ids


def _safe_project_name(project_type: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", project_type.lower().replace("_", "-"))
    return value.strip("-") or "application"


def generate_iac(
    services: Iterable[Any],
    classification: Dict[str, Any],
    estimated_users: int,
    region: str = "us-east-1",
    budget: str = "medium",
) -> Dict[str, Any]:
    project_type = classification.get("primary", "web_application")
    service_ids = _service_ids(services)
    return generate_terraform(service_ids, project_type, estimated_users, region, budget)


def generate_terraform(
    service_ids: list[str],
    project_type: str,
    users: int,
    region: str,
    budget: str,
) -> Dict[str, Any]:
    project_name = _safe_project_name(project_type)
    supported = [service for service in service_ids if service in SUPPORTED_TERRAFORM_SERVICES]
    deferred = [service for service in service_ids if service not in SUPPORTED_TERRAFORM_SERVICES]

    # API Gateway requires a compute integration in this baseline module.
    if "api-gateway" in supported and "lambda" not in supported:
        supported.append("lambda")

    main_parts = [_terraform_header()]
    if "lambda" in supported:
        main_parts.append(_lambda_resources(users))
    if "dynamodb" in supported:
        main_parts.append(_dynamodb_resources())
    if "s3" in supported:
        main_parts.append(_s3_resources())
    if "cognito" in supported:
        main_parts.append(_cognito_resources())
    if "api-gateway" in supported:
        main_parts.append(_api_gateway_resources())

    variables_tf = _variables(project_name, region)
    outputs_tf = _outputs(supported)
    versions_lock_note = hashlib.sha256("|".join(sorted(supported)).encode()).hexdigest()[:12]
    readme = _terraform_readme(project_type, users, region, budget, deferred, versions_lock_note)

    logger.info("Generated Terraform baseline for %s supported services", len(supported))
    return {
        "format": "terraform",
        "status": "baseline_ready",
        "supported_services": supported,
        "deferred_services": deferred,
        "files": {
            "main.tf": "\n\n".join(main_parts).strip() + "\n",
            "variables.tf": variables_tf,
            "outputs.tf": outputs_tf,
            "README.md": readme,
        },
        "instructions": [
            "Create a deployable Lambda zip at the path supplied by lambda_zip_path.",
            "Run terraform fmt -check and terraform validate.",
            "Run terraform plan and review security, names, quotas, and cost impact.",
            "Apply first in a non-production AWS account.",
        ],
    }


def _terraform_header() -> str:
    return '''terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}'''


def _variables(project_name: str, region: str) -> str:
    return f'''variable "aws_region" {{
  description = "AWS region"
  type        = string
  default     = "{region}"
}}

variable "environment" {{
  description = "Deployment environment"
  type        = string
  default     = "dev"
}}

variable "project_name" {{
  description = "Lowercase project name used in resource names"
  type        = string
  default     = "{project_name}"
}}

variable "lambda_zip_path" {{
  description = "Path to a deployment zip containing index.handler"
  type        = string
  default     = "lambda.zip"
}}
'''


def _lambda_resources(users: int) -> str:
    memory = 256 if users <= 10_000 else 512 if users <= 100_000 else 1024
    return f'''resource "aws_iam_role" "lambda" {{
  name = "${{var.project_name}}-${{var.environment}}-lambda-role"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{ Service = "lambda.amazonaws.com" }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "lambda_basic" {{
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}}

resource "aws_cloudwatch_log_group" "lambda" {{
  name              = "/aws/lambda/${{var.project_name}}-${{var.environment}}-api"
  retention_in_days = 30
}}

resource "aws_lambda_function" "api" {{
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  function_name    = "${{var.project_name}}-${{var.environment}}-api"
  role             = aws_iam_role.lambda.arn
  handler          = "index.handler"
  runtime          = "python3.12"
  memory_size      = {memory}
  timeout          = 30

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda,
  ]
}}'''


def _dynamodb_resources() -> str:
    return '''resource "aws_dynamodb_table" "main" {
  name         = "${var.project_name}-${var.environment}-data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}'''


def _s3_resources() -> str:
    return '''resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}'''


def _cognito_resources() -> str:
    return '''resource "aws_cognito_user_pool" "main" {
  name                     = "${var.project_name}-${var.environment}-users"
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OPTIONAL"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }
}

resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project_name}-${var.environment}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  explicit_auth_flows                  = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  supported_identity_providers         = ["COGNITO"]
}'''


def _api_gateway_resources() -> str:
    return '''resource "aws_api_gateway_rest_api" "main" {
  name = "${var.project_name}-${var.environment}-api"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_method" "root" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_rest_api.main.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_rest_api.main.root_resource_id
  http_method             = aws_api_gateway_method.root.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_method.proxy.id,
      aws_api_gateway_integration.proxy.id,
      aws_api_gateway_method.root.id,
      aws_api_gateway_integration.root.id,
    ]))
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}'''


def _outputs(supported: list[str]) -> str:
    outputs = []
    if "api-gateway" in supported:
        outputs.append('''output "api_endpoint" {
  description = "API Gateway base URL"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.main.stage_name}"
}''')
    if "lambda" in supported:
        outputs.append('''output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}''')
    if "dynamodb" in supported:
        outputs.append('''output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.main.name
}''')
    if "s3" in supported:
        outputs.append('''output "s3_bucket_name" {
  description = "Private S3 bucket name"
  value       = aws_s3_bucket.main.id
}''')
    if "cognito" in supported:
        outputs.append('''output "cognito_user_pool_id" {
  description = "Cognito user pool ID"
  value       = aws_cognito_user_pool.main.id
}''')
    return "\n\n".join(outputs).strip() + "\n"


def _terraform_readme(project_type: str, users: int, region: str, budget: str, deferred: list[str], note: str) -> str:
    deferred_text = ", ".join(deferred) if deferred else "None"
    return f'''# Generated Terraform baseline

Project type: {project_type}
Estimated monthly active users: {users:,}
Region: {region}
Budget profile: {budget}
Generation fingerprint: {note}

## Before deployment

1. Replace the sample Lambda artifact with application code exposing `index.handler`.
2. Run `terraform fmt -check` and `terraform validate`.
3. Review IAM permissions, data retention, authentication, and public exposure.
4. Deploy first to a non-production account.

## Commands

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
```

## Deferred recommendations

The following recommended services require workload-specific configuration and are not emitted automatically by this safe baseline: {deferred_text}.

This output is a starting point, not an unattended production deployment.
'''
