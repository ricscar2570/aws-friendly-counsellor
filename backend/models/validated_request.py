from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
import html
import re


class AnalysisRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Project description"
    )
    
    estimated_users: int = Field(
        ...,
        ge=1,
        le=100_000_000,
        description="Estimated number of users"
    )
    
    budget: Literal["low", "medium", "high"] = Field(
        ...,
        description="Budget constraint"
    )
    
    region: Optional[str] = Field(
        "us-east-1",
        description="AWS region"
    )
    
    advanced_guide: bool = Field(
        default=True,
        description="Generate advanced guide"
    )
    
    @validator('description')
    def sanitize_description(cls, v: str) -> str:
        v = v.strip()
        v = html.escape(v)
        v = ' '.join(v.split())
        
        if len(v.strip()) < 10:
            raise ValueError("Description too short")
        
        return v


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
