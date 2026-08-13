from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from aws_friendly_counsellor_contracts import (
    CONTRACT_VERSION,
    AnalysisRequest,
    AnalyzeResponse,
)

from ..core.config import settings
from .analysis_pipeline import run_analysis_pipeline


def build_analysis_result(
    payload: AnalysisRequest,
    *,
    project_id: str,
    request_id: str,
    start_time: float | None = None,
) -> AnalyzeResponse:
    started = start_time if start_time is not None else time.perf_counter()
    result = run_analysis_pipeline(payload)
    classification = result.classification
    return AnalyzeResponse.model_validate(
        {
            "project_id": project_id,
            "analysis": {
                "project_type": classification["primary"],
                "confidence": classification["confidence"],
                "detected_features": classification["features"],
                "classifier": classification["classifier"],
            },
            "services": result.services,
            "cost_analysis": result.cost_analysis,
            "implementation_guide": result.guide,
            "metadata": {
                "request_id": request_id,
                "processing_time_ms": max(
                    0, int((time.perf_counter() - started) * 1000)
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": settings.app_version,
                "contract_version": CONTRACT_VERSION,
            },
        }
    )


def analysis_request_from_project(
    project: Any,
    *,
    description: str | None,
    estimated_users: int | None,
    budget: str | None,
    region: str | None,
    advanced_guide: bool,
) -> AnalysisRequest:
    return AnalysisRequest(
        description=description or project.description,
        estimated_users=estimated_users or project.estimated_users,
        budget=budget or project.budget,
        region=region or project.region,
        advanced_guide=advanced_guide,
    )
