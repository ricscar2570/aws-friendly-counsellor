from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from datetime import datetime
import logging
import time
import os

from services.narrative_generator import generate_narrative_analysis
from models.validated_request import AnalysisRequest
from security.auth import verify_api_key, check_rate_limit
from services.classifier import classify_use_case
from services.recommender import recommend_services
from services.cost_calculator import calculate_costs
from services.guide_generator import generate_guide
from services.iac_generator import generate_iac

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AWS Friendly Counsellor v3.0",
    description="Production-ready AWS architecture advisor",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "AWS Friendly Counsellor",
        "version": "3.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest, api_key: str = Depends(verify_api_key)):
    start_time = time.time()
    try:
        if api_key != "anonymous":
            check_rate_limit(api_key)
        
        classification = classify_use_case(request.description)
        services = recommend_services(classification, request.estimated_users)
        service_names = [s["name"] for s in services]
        cost_analysis = calculate_costs(service_names, request.estimated_users)
        guide = generate_guide(service_names, classification, request.estimated_users)
        
        return {
            "project_id": f"proj_{int(time.time())}",
            "analysis": {
                "project_type": classification["primary"],
                "confidence": classification["confidence"],
                "detected_features": classification["features"]
            },
            "services": services,
            "cost_analysis": cost_analysis,
            "implementation_guide": guide,
            "metadata": {
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/iac")
async def generate_infrastructure_code(request: AnalysisRequest, api_key: str = Depends(verify_api_key)):
    start_time = time.time()
    try:
        classification = classify_use_case(request.description)
        services = recommend_services(classification, request.estimated_users)
        iac_output = generate_iac(services, classification, request.estimated_users)
        
        return {
            "project_id": f"iac_{int(time.time())}",
            "analysis": {
                "project_type": classification["primary"],
                "services_count": len(services)
            },
            "terraform": iac_output,
            "metadata": {
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/narrative")
async def generate_narrative(request: AnalysisRequest, api_key: str = Depends(verify_api_key)):
    """Generate comprehensive narrative analysis"""
    start_time = time.time()
    try:
        classification = classify_use_case(request.description)
        services = recommend_services(classification, request.estimated_users)
        service_names = [s["name"] for s in services]
        cost_analysis = calculate_costs(service_names, request.estimated_users)
        guide = generate_guide(service_names, classification, request.estimated_users)
        
        narrative_html = generate_narrative_analysis(
            services=services,
            classification=classification,
            cost_analysis=cost_analysis,
            implementation_guide=guide,
            estimated_users=request.estimated_users
        )
        
        response_data = {
            "project_id": f"narrative_{int(time.time())}",
            "narrative_html": narrative_html,
            "metadata": {
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        processing_time = response_data['metadata']['processing_time_ms']
        logger.info(f"Narrative generated in {processing_time}ms")
        
        return response_data
        
    except Exception as e:
        logger.exception(f"Error generating narrative: {e}")
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app, lifespan="off")
