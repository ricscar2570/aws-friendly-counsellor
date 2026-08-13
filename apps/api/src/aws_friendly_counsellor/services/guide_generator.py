from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

try:
    from .cost_calculator import normalize_service_id
except ImportError:  # pragma: no cover
    from services.cost_calculator import normalize_service_id

logger = logging.getLogger(__name__)


def _service_ids(services: Iterable[Any]) -> list[str]:
    result: list[str] = []
    for service in services:
        service_id = normalize_service_id(service)
        if service_id and service_id not in result:
            result.append(service_id)
    return result


def generate_guide(
    services: Iterable[Any],
    classification: Dict[str, Any],
    estimated_users: int,
    budget: str = "medium",
    region: str = "us-east-1",
    advanced: bool = True,
    cost_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    ids = _service_ids(services)
    project_type = classification.get("primary", "web_application")
    complexity_points = len(ids) + (2 if "appsync" in ids else 0) + (2 if "glue" in ids else 0)
    difficulty = "Beginner" if complexity_points <= 4 else "Intermediate" if complexity_points <= 8 else "Advanced"
    total_hours = 8 + len(ids) * 4 + (8 if advanced else 0)
    typical_cost = (cost_analysis or {}).get("summary", {}).get("typical", "Not calculated")

    guide: dict[str, Any] = {
        "format": "advanced" if advanced else "essential",
        "project_context": {
            "type": project_type,
            "estimated_monthly_active_users": estimated_users,
            "budget": budget,
            "region": region,
            "services_count": len(ids),
            "complexity": difficulty,
        },
        "introduction": {
            "title": f"AWS implementation plan for {project_type.replace('_', ' ').title()}",
            "overview": f"A phased deployment plan for approximately {estimated_users:,} monthly active users.",
            "estimated_effort": f"{total_hours}-{total_hours + 12} engineering hours",
            "estimated_monthly_cost": typical_cost,
        },
        "prerequisites": [
            "AWS account with MFA-protected administrative access",
            "AWS CLI and SAM CLI installed",
            "A non-production AWS environment for initial validation",
            "A cost budget and alert configured before load testing",
        ],
        "phases": generate_implementation_phases(ids, estimated_users, advanced),
        "acceptance_checks": [
            "Authentication and authorization deny unauthorized requests",
            "Logs contain request identifiers but no credentials or secrets",
            "Infrastructure can be recreated from source control",
            "Cost alarms and operational alarms are active",
            "A rollback or destroy procedure has been tested outside production",
        ],
    }

    if advanced:
        guide["operations"] = {
            "security": [
                "Apply least-privilege IAM policies instead of wildcard permissions",
                "Store secrets in Secrets Manager or SSM Parameter Store",
                "Enable encryption and access logging where supported",
            ],
            "reliability": [
                "Use retries with bounded exponential backoff",
                "Configure dead-letter handling for asynchronous workloads",
                "Test quota and throttling behavior before launch",
            ],
            "cost_control": [
                "Tag resources consistently",
                "Review Cost Explorer after realistic load tests",
                "Set retention limits for logs and analytical data",
            ],
        }
    return guide


def generate_implementation_phases(service_ids: List[str], users: int, advanced: bool) -> List[Dict[str, Any]]:
    phases: list[dict[str, Any]] = [
        {
            "name": "Foundation and guardrails",
            "duration": "2-4 hours",
            "steps": [
                "Choose the AWS account and target region",
                "Enable MFA and create least-privilege deployment roles",
                "Create a monthly budget with email alerts",
                "Configure local AWS CLI and SAM credentials",
            ],
        }
    ]

    data_steps = []
    if "dynamodb" in service_ids:
        data_steps.append("Define DynamoDB access patterns before creating tables")
    if "s3" in service_ids:
        data_steps.append("Create private S3 buckets with public-access blocking and encryption")
    if "cognito" in service_ids:
        data_steps.append("Configure Cognito user pool, client, token lifetimes, and MFA policy")
    if data_steps:
        phases.append({"name": "Identity and data", "duration": "4-8 hours", "steps": data_steps})

    application_steps = []
    if "lambda" in service_ids:
        application_steps.extend(["Package Lambda dependencies reproducibly", "Configure environment variables and IAM permissions"])
    if "api-gateway" in service_ids:
        application_steps.extend(["Deploy API Gateway routes", "Configure CORS only for approved browser origins"])
    if "appsync" in service_ids:
        application_steps.append("Define GraphQL schema, resolvers, authorization modes, and subscription limits")
    if application_steps:
        phases.append({"name": "Application services", "duration": "6-12 hours", "steps": application_steps})

    phases.append({
        "name": "Verification",
        "duration": "4-8 hours",
        "steps": [
            "Run unit and API tests",
            f"Load-test a representative path for a target near {min(max(users // 20, 10), 5_000):,} concurrent sessions",
            "Verify authorization failures, throttling, retries, and alarms",
            "Review the generated cost range against measured usage",
        ],
    })

    if advanced:
        phases.append({
            "name": "Production readiness",
            "duration": "4-8 hours",
            "steps": [
                "Create CI/CD with separate validation and deployment roles",
                "Define log retention, dashboards, alarms, and incident ownership",
                "Document rollback, backup, restore, and disaster-recovery procedures",
                "Perform a final least-privilege and public-access review",
            ],
        })
    return phases
