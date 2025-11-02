"""
Infrastructure as Code Generator
Generates Terraform code WITHOUT modifying existing modules
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def generate_iac(services: List[Dict], classification: Dict, estimated_users: int) -> Dict[str, Any]:
    """Generate Terraform configuration for recommended architecture"""
    
    project_type = classification.get("primary", "application")
    logger.info(f"Generating Terraform for {project_type}")
    
    return generate_terraform(services, project_type, estimated_users)


def generate_terraform(services: List[Dict], project_type: str, users: int) -> Dict[str, Any]:
    """Generate complete Terraform configuration"""
    
    # Main configuration
    main_tf = f"""# Terraform configuration for {project_type}
# Estimated users: {users:,}

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
  default_tags {{
    tags = {{
      Project     = "{project_type}"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }}
  }}
}}
"""

    # Variables
    variables_tf = f"""variable "aws_region" {{
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}}

variable "environment" {{
  description = "Environment name"
  type        = string
  default     = "prod"
}}

variable "project_name" {{
  description = "Project name"
  type        = string
  default     = "{project_type}"
}}
"""

    # Generate resources for each service
    resources = []
    
    for service in services:
        service_lower = service["name"].lower()
        
        if "lambda" in service_lower:
            resources.append(get_lambda_terraform(project_type, users))
        elif "dynamodb" in service_lower:
            resources.append(get_dynamodb_terraform(project_type, users))
        elif "s3" in service_lower:
            resources.append(get_s3_terraform(project_type))
        elif "cognito" in service_lower:
            resources.append(get_cognito_terraform(project_type))
        elif "api gateway" in service_lower:
            resources.append(get_apigateway_terraform(project_type))
    
    resources_tf = "\n\n".join(resources)
    
    # Outputs
    outputs_tf = """output "api_endpoint" {
  description = "API Gateway URL"
  value       = try(aws_api_gateway_deployment.main.invoke_url, "N/A")
}

output "lambda_function" {
  description = "Lambda function name"
  value       = try(aws_lambda_function.api.function_name, "N/A")
}
"""

    # Deployment instructions
    readme = f"""# Terraform Deployment

## Prerequisites
- Install Terraform: https://www.terraform.io/downloads
- Configure AWS: aws configure

## Deploy

1. Initialize:
   terraform init

2. Plan:
   terraform plan

3. Apply:
   terraform apply

4. Get outputs:
   terraform output

## Cost
Estimated: ${get_monthly_cost(users)}/month for {users:,} users

## Cleanup
terraform destroy
"""

    return {
        "format": "terraform",
        "files": {
            "main.tf": main_tf + "\n\n" + resources_tf,
            "variables.tf": variables_tf,
            "outputs.tf": outputs_tf,
            "README.md": readme
        },
        "instructions": [
            "1. Install Terraform",
            "2. Run: terraform init",
            "3. Run: terraform plan",
            "4. Run: terraform apply"
        ]
    }


def get_lambda_terraform(project: str, users: int) -> str:
    """Generate Lambda Terraform"""
    memory = 256 if users < 1000 else 512 if users < 10000 else 1024
    timeout = 10 if users < 1000 else 30 if users < 10000 else 60
    
    return f"""resource "aws_lambda_function" "api" {{
  filename      = "lambda.zip"
  function_name = "${{var.project_name}}-api"
  role          = aws_iam_role.lambda.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  memory_size   = {memory}
  timeout       = {timeout}
}}

resource "aws_iam_role" "lambda" {{
  name = "${{var.project_name}}-lambda-role"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{ Service = "lambda.amazonaws.com" }}
    }}]
  }})
}}"""


def get_dynamodb_terraform(project: str, users: int) -> str:
    """Generate DynamoDB Terraform"""
    billing = "PAY_PER_REQUEST" if users < 10000 else "PROVISIONED"
    
    return f"""resource "aws_dynamodb_table" "main" {{
  name         = "${{var.project_name}}-data"
  billing_mode = "{billing}"
  hash_key     = "pk"
  range_key    = "sk"
  
  attribute {{
    name = "pk"
    type = "S"
  }}
  attribute {{
    name = "sk"
    type = "S"
  }}
  
  server_side_encryption {{
    enabled = true
  }}
}}"""


def get_s3_terraform(project: str) -> str:
    """Generate S3 Terraform"""
    return """resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-storage"
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}"""


def get_cognito_terraform(project: str) -> str:
    """Generate Cognito Terraform"""
    return """resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"
  
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
  }
}"""


def get_apigateway_terraform(project: str) -> str:
    """Generate API Gateway Terraform"""
    return """resource "aws_api_gateway_rest_api" "main" {
  name = "${var.project_name}-api"
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.environment
}"""


def get_monthly_cost(users: int) -> str:
    """Estimate cost"""
    if users < 1000:
        return "$0-25"
    elif users < 10000:
        return "$25-100"
    else:
        return "$100-500"
