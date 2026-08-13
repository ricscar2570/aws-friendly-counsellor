from __future__ import annotations

import logging
from typing import Any, Dict, Iterable

logger = logging.getLogger(__name__)

# Planning ranges, not quotations. They intentionally favor understandable,
# conservative monthly ranges over false precision.
SERVICE_COST_MODELS: dict[str, dict[str, Any]] = {
    "lambda": {"name": "AWS Lambda", "minimum": 0, "maximum": 50, "free_tier": "1M requests and 400,000 GB-seconds"},
    "api-gateway": {"name": "Amazon API Gateway", "minimum": 0, "maximum": 35, "free_tier": "Limited introductory request allowance"},
    "dynamodb": {"name": "Amazon DynamoDB", "minimum": 0, "maximum": 40, "free_tier": "Storage and throughput allowance"},
    "s3": {"name": "Amazon S3", "minimum": 0, "maximum": 25, "free_tier": "Limited introductory storage allowance"},
    "cognito": {"name": "Amazon Cognito", "minimum": 0, "maximum": 30, "free_tier": "Monthly active-user allowance varies by authentication mode"},
    "ses": {"name": "Amazon SES", "minimum": 0, "maximum": 15, "free_tier": "Eligibility depends on sending source and current AWS terms"},
    "cloudfront": {"name": "Amazon CloudFront", "minimum": 0, "maximum": 60, "free_tier": "Usage allowance subject to current AWS terms"},
    "appsync": {"name": "AWS AppSync", "minimum": 0, "maximum": 50, "free_tier": "Introductory query and real-time operation allowance"},
    "cloudwatch": {"name": "Amazon CloudWatch", "minimum": 0, "maximum": 35, "free_tier": "Basic metrics and limited logs"},
    "xray": {"name": "AWS X-Ray", "minimum": 0, "maximum": 20, "free_tier": "Limited traces and retrievals"},
    "waf": {"name": "AWS WAF", "minimum": 8, "maximum": 45, "free_tier": "No broad always-free allowance assumed"},
    "eventbridge": {"name": "Amazon EventBridge", "minimum": 0, "maximum": 20, "free_tier": "AWS service events are generally not charged"},
    "sqs": {"name": "Amazon SQS", "minimum": 0, "maximum": 15, "free_tier": "Monthly request allowance"},
    "athena": {"name": "Amazon Athena", "minimum": 0, "maximum": 60, "free_tier": "No broad always-free allowance assumed"},
    "glue": {"name": "AWS Glue", "minimum": 0, "maximum": 90, "free_tier": "Limited Data Catalog allowance"},
}

NAME_TO_ID = {model["name"].lower(): service_id for service_id, model in SERVICE_COST_MODELS.items()}
BUDGET_TARGETS = {"low": 100, "medium": 500, "high": float("inf")}


def _scale_factor(users: int) -> float:
    if users <= 1_000:
        return 0.45
    if users <= 10_000:
        return 1.0
    if users <= 100_000:
        return 2.5
    if users <= 1_000_000:
        return 5.0
    return 10.0


def normalize_service_id(service: Any) -> str | None:
    if isinstance(service, dict):
        candidate = service.get("id") or service.get("name")
    else:
        candidate = service
    if not isinstance(candidate, str):
        return None
    normalized = candidate.strip().lower()
    if normalized in SERVICE_COST_MODELS:
        return normalized
    return NAME_TO_ID.get(normalized)


def estimate_service_cost(service_id: str, users: int) -> tuple[float, float]:
    model = SERVICE_COST_MODELS.get(service_id)
    if not model:
        return (0.0, 0.0)
    factor = _scale_factor(users)
    minimum = float(model["minimum"])
    maximum = float(model["maximum"]) * factor
    if minimum == 0 and factor > 1:
        minimum = round(maximum * 0.08, 2)
    return (round(minimum, 2), round(maximum, 2))


def calculate_costs(
    services: Iterable[Any],
    users: int,
    region: str = "us-east-1",
    budget: str = "medium",
) -> Dict[str, Any]:
    service_ids = []
    for service in services:
        service_id = normalize_service_id(service)
        if service_id and service_id not in service_ids:
            service_ids.append(service_id)

    total_minimum = 0.0
    total_maximum = 0.0
    breakdown: dict[str, Any] = {}

    for service_id in service_ids:
        model = SERVICE_COST_MODELS[service_id]
        minimum, maximum = estimate_service_cost(service_id, users)
        total_minimum += minimum
        total_maximum += maximum
        breakdown[service_id] = {
            "name": model["name"],
            "minimum": round(minimum, 2),
            "maximum": round(maximum, 2),
            "display": f"${minimum:,.0f}-${maximum:,.0f}",
            "free_tier": model["free_tier"],
        }

    typical = round((total_minimum + total_maximum) / 2, 2)
    target = BUDGET_TARGETS.get(budget, BUDGET_TARGETS["medium"])
    budget_alignment = "within_target" if typical <= target else "above_target"
    free_tier_viable = users <= 1_000 and total_minimum <= 10

    logger.info(
        "Cost model completed: services=%s users=%s typical=%s",
        len(service_ids), users, typical,
    )
    return {
        "currency": "USD",
        "period": "monthly",
        "region": region,
        "summary": {
            "free_tier_viable": free_tier_viable,
            "minimum": f"${total_minimum:,.0f}",
            "typical": f"${typical:,.0f}",
            "maximum": f"${total_maximum:,.0f}",
            "minimum_value": round(total_minimum, 2),
            "typical_value": typical,
            "maximum_value": round(total_maximum, 2),
            "budget_alignment": budget_alignment,
        },
        "breakdown": breakdown,
        "assumptions": [
            "Estimates are planning ranges, not AWS quotations.",
            "Traffic, data transfer, payload size, retention, and request patterns can materially change costs.",
            "Region is recorded for the deployment plan; this baseline model does not claim live regional pricing.",
            "Verify the final architecture with the official AWS Pricing Calculator before deployment.",
        ],
    }
