from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aws_friendly_counsellor_contracts import AnalysisRequest

from ..services.classifier import classify_use_case
from ..services.cost_calculator import calculate_costs
from ..services.guide_generator import generate_guide
from ..services.recommender import recommend_services


@dataclass(frozen=True, slots=True)
class AnalysisPipelineResult:
    classification: dict[str, Any]
    services: list[dict[str, Any]]
    cost_analysis: dict[str, Any]
    guide: dict[str, Any]


def run_analysis_pipeline(request: AnalysisRequest) -> AnalysisPipelineResult:
    classification = classify_use_case(request.description)
    services = recommend_services(
        classification,
        request.estimated_users,
        budget=request.budget,
        region=request.region,
    )
    cost_analysis = calculate_costs(
        services,
        request.estimated_users,
        region=request.region,
        budget=request.budget,
    )
    guide = generate_guide(
        services,
        classification,
        request.estimated_users,
        budget=request.budget,
        region=request.region,
        advanced=request.advanced_guide,
        cost_analysis=cost_analysis,
    )
    return AnalysisPipelineResult(
        classification=classification,
        services=services,
        cost_analysis=cost_analysis,
        guide=guide,
    )
