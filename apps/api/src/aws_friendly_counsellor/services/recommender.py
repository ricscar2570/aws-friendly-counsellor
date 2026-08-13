from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Dict, List

try:
    from .cost_calculator import SERVICE_COST_MODELS, estimate_service_cost
except ImportError:  # pragma: no cover - SAM imports modules from CodeUri root
    from services.cost_calculator import SERVICE_COST_MODELS, estimate_service_cost

logger = logging.getLogger(__name__)

SERVICE_CATALOG: dict[str, dict[str, str]] = {
    "lambda": {"name": "AWS Lambda", "category": "compute", "why": "Runs event-driven application logic without persistent server management.", "use_case": "API handlers, background processing, scheduled jobs"},
    "api-gateway": {"name": "Amazon API Gateway", "category": "api", "why": "Publishes, secures, throttles, and observes HTTP APIs.", "use_case": "REST endpoints for web and mobile clients"},
    "dynamodb": {"name": "Amazon DynamoDB", "category": "database", "why": "Provides low-operations NoSQL storage with on-demand scaling.", "use_case": "Users, sessions, application records, carts, and events"},
    "s3": {"name": "Amazon S3", "category": "storage", "why": "Stores static assets and user-generated objects durably.", "use_case": "Uploads, media, exports, backups, and static files"},
    "cognito": {"name": "Amazon Cognito", "category": "authentication", "why": "Provides managed sign-up, sign-in, tokens, MFA, and federation.", "use_case": "Customer and workforce identity for applications"},
    "ses": {"name": "Amazon SES", "category": "messaging", "why": "Sends transactional email without operating a mail server.", "use_case": "Verification, password reset, receipts, and notifications"},
    "cloudfront": {"name": "Amazon CloudFront", "category": "cdn", "why": "Caches content near users and reduces origin load.", "use_case": "Global delivery of static assets and public content"},
    "appsync": {"name": "AWS AppSync", "category": "api", "why": "Supports managed GraphQL APIs and real-time subscriptions.", "use_case": "Live collaboration, chat, and synchronized clients"},
    "cloudwatch": {"name": "Amazon CloudWatch", "category": "observability", "why": "Centralizes logs, metrics, alarms, and operational dashboards.", "use_case": "Application monitoring and alerting"},
    "xray": {"name": "AWS X-Ray", "category": "observability", "why": "Traces distributed requests to diagnose latency and failures.", "use_case": "Production troubleshooting across APIs and functions"},
    "waf": {"name": "AWS WAF", "category": "security", "why": "Filters common web attacks and abusive request patterns.", "use_case": "Protection for public APIs and web applications"},
    "eventbridge": {"name": "Amazon EventBridge", "category": "integration", "why": "Routes domain and service events between decoupled components.", "use_case": "Order events, scheduled automation, and integrations"},
    "sqs": {"name": "Amazon SQS", "category": "messaging", "why": "Buffers asynchronous work and isolates transient failures.", "use_case": "Background jobs, retries, and traffic smoothing"},
    "athena": {"name": "Amazon Athena", "category": "analytics", "why": "Queries data in S3 without provisioning a database cluster.", "use_case": "Ad-hoc reporting and product analytics"},
    "glue": {"name": "AWS Glue", "category": "analytics", "why": "Catalogs and transforms analytical datasets.", "use_case": "ETL jobs and data catalog management"},
}

PROFILES: dict[str, list[str]] = {
    "web_application": ["lambda", "api-gateway", "dynamodb", "s3"],
    "ecommerce": ["cognito", "lambda", "api-gateway", "dynamodb", "s3", "eventbridge", "sqs"],
    "marketplace": ["cognito", "lambda", "api-gateway", "dynamodb", "s3", "eventbridge", "sqs"],
    "social": ["cognito", "lambda", "api-gateway", "dynamodb", "s3", "appsync"],
    "saas": ["cognito", "lambda", "api-gateway", "dynamodb", "s3", "eventbridge"],
    "blog": ["s3", "cloudfront", "lambda", "api-gateway", "dynamodb"],
    "mobile_backend": ["cognito", "lambda", "api-gateway", "dynamodb", "s3"],
    "api": ["lambda", "api-gateway", "dynamodb"],
    "real_time": ["cognito", "appsync", "lambda", "dynamodb"],
    "analytics": ["s3", "athena", "glue", "lambda", "eventbridge"],
    "file_storage": ["cognito", "s3", "lambda", "api-gateway", "dynamodb"],
}

FEATURE_ADDITIONS: dict[str, list[str]] = {
    "authentication": ["cognito"],
    "email": ["ses"],
    "file_storage": ["s3"],
    "real_time": ["appsync"],
    "analytics": ["s3", "athena"],
}

BUDGET_EXTRAS: dict[str, list[str]] = {
    "low": [],
    "medium": ["cloudwatch"],
    "high": ["cloudwatch", "xray", "waf"],
}


def _append_unique(target: list[str], additions: list[str]) -> None:
    for service_id in additions:
        if service_id not in target:
            target.append(service_id)


def recommend_services(
    classification: Dict[str, Any],
    estimated_users: int,
    budget: str = "medium",
    region: str = "us-east-1",
) -> List[Dict[str, Any]]:
    primary = classification.get("primary", "web_application")
    features = classification.get("features", [])
    selected = list(PROFILES.get(primary, PROFILES["web_application"]))
    core_services = set(selected)

    for feature in features:
        _append_unique(selected, FEATURE_ADDITIONS.get(feature, []))

    _append_unique(selected, BUDGET_EXTRAS.get(budget, BUDGET_EXTRAS["medium"]))

    if estimated_users > 10_000:
        _append_unique(selected, ["cloudfront", "cloudwatch"])
    if estimated_users > 100_000 and budget != "low":
        _append_unique(selected, ["waf"])

    result: list[dict[str, Any]] = []
    for service_id in selected:
        service = deepcopy(SERVICE_CATALOG[service_id])
        minimum, maximum = estimate_service_cost(service_id, estimated_users)
        cost_model = SERVICE_COST_MODELS.get(service_id, {})
        result.append({
            "id": service_id,
            "name": service["name"],
            "category": service["category"],
            "essential": service_id in core_services,
            "typical_monthly": f"${minimum:,.0f}-${maximum:,.0f}",
            "free_tier": cost_model.get("free_tier", "Check current AWS terms"),
            "why_needed": service["why"],
            "use_case_example": service["use_case"],
            "region": region,
        })

    logger.info(
        "Recommended %s services for primary=%s users=%s budget=%s",
        len(result), primary, estimated_users, budget,
    )
    return result
