from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from aws_friendly_counsellor_contracts import (
    AnalysisRequest,
    AnalyzeResponse,
    IaCResponse,
    NarrativeResponse,
)

from ...application.analysis_pipeline import run_analysis_pipeline
from ...application.analysis_service import build_analysis_result
from ...security.auth import authorize_request
from ...services.iac_generator import generate_iac
from ...services.narrative_generator import generate_narrative_analysis
from .common import ERROR_RESPONSES, request_id, response_metadata

logger = logging.getLogger(__name__)

v1_router = APIRouter(prefix="/api/v1", tags=["planning-v1"])
legacy_router = APIRouter(prefix="/api", include_in_schema=False)


@v1_router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
    summary="Analyze a project and recommend an AWS baseline",
)
@legacy_router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    response_model_exclude_none=True,
    deprecated=True,
)
async def analyze(
    payload: AnalysisRequest,
    request: Request,
    _: str = Depends(authorize_request),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    try:
        result = build_analysis_result(
            payload,
            project_id=f"proj_{request_id(request)}",
            request_id=request_id(request),
            start_time=start_time,
        )
        data = result.model_dump(mode="json", exclude_none=True)
        data["metadata"] = response_metadata(start_time, request)
        return data
    except HTTPException:
        raise
    except Exception:
        logger.exception("Analyze request failed request_id=%s", request_id(request))
        raise HTTPException(status_code=500, detail="Analysis failed")


@v1_router.post(
    "/iac",
    response_model=IaCResponse,
    responses=ERROR_RESPONSES,
    summary="Generate a Terraform baseline from a project description",
)
@legacy_router.post(
    "/iac",
    response_model=IaCResponse,
    deprecated=True,
)
async def generate_infrastructure_code(
    payload: AnalysisRequest,
    request: Request,
    _: str = Depends(authorize_request),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    try:
        result = run_analysis_pipeline(payload)
        iac_output = generate_iac(
            result.services,
            result.classification,
            payload.estimated_users,
            region=payload.region,
            budget=payload.budget,
        )
        return {
            "project_id": f"iac_{request_id(request)}",
            "analysis": {
                "project_type": result.classification["primary"],
                "services_count": len(result.services),
                "region": payload.region,
            },
            "terraform": iac_output,
            "metadata": response_metadata(start_time, request),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("IaC request failed request_id=%s", request_id(request))
        raise HTTPException(status_code=500, detail="Infrastructure generation failed")


@v1_router.post(
    "/narrative",
    response_model=NarrativeResponse,
    responses=ERROR_RESPONSES,
    summary="Generate a human-readable HTML architecture report",
)
@legacy_router.post(
    "/narrative",
    response_model=NarrativeResponse,
    deprecated=True,
)
async def generate_narrative(
    payload: AnalysisRequest,
    request: Request,
    _: str = Depends(authorize_request),
) -> dict[str, Any]:
    start_time = time.perf_counter()
    try:
        result = run_analysis_pipeline(payload)
        narrative_html = generate_narrative_analysis(
            services=result.services,
            classification=result.classification,
            cost_analysis=result.cost_analysis,
            implementation_guide=result.guide,
            estimated_users=payload.estimated_users,
        )
        return {
            "project_id": f"narrative_{request_id(request)}",
            "narrative_html": narrative_html,
            "metadata": response_metadata(start_time, request),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Narrative request failed request_id=%s", request_id(request))
        raise HTTPException(status_code=500, detail="Narrative generation failed")
