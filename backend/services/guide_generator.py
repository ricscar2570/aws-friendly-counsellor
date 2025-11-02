"""
Implementation Guide Generator - DYNAMIC & PERSONALIZED
Generates contextual implementation guides based on services and scale
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def generate_guide(services: List[str], classification: Dict, estimated_users: int) -> Dict[str, Any]:
    """Generate DYNAMIC implementation guide based on project specifics"""
    
    project_type = classification.get("primary", "application")
    features = classification.get("features", [])
    
    # Calculate complexity
    service_count = len(services)
    total_hours = 15 + (service_count * 5)
    days = max(3, total_hours // 8)
    
    # Determine difficulty
    complexity_score = sum([
        2 if "cognito" in s.lower() else
        3 if "rds" in s.lower() else
        1 if "dynamodb" in s.lower() else 0
        for s in services
    ])
    
    difficulty = "Beginner" if complexity_score < 2 else "Intermediate" if complexity_score < 4 else "Advanced"
    
    # Cost estimation
    if estimated_users < 1000:
        cost_range = "$0-50"
        tier_message = "Can run mostly on AWS Free Tier"
    elif estimated_users < 10000:
        cost_range = "$50-200"
        tier_message = "Some Free Tier benefits available"
    else:
        cost_range = "$200-1000"
        tier_message = "Production-grade costs"
    
    # Build comprehensive guide
    guide = {
        "format": "dynamic_personalized",
        "sections": len(services) + 6,
        
        "project_context": {
            "type": project_type,
            "estimated_users": estimated_users,
            "services_count": service_count,
            "complexity": difficulty
        },
        
        "introduction": {
            "title": f"Building Your {project_type.title()} Platform on AWS",
            "overview": f"Personalized implementation guide for a {project_type} application serving {estimated_users:,} users using {service_count} AWS services.",
            "timeline": f"{total_hours}-{total_hours + 10} hours over {days}-{days + 2} days",
            "difficulty": difficulty,
            "estimated_cost": f"{cost_range}/month",
            "cost_note": tier_message
        },
        
        "prerequisites": [
            "AWS account with admin access",
            "AWS CLI installed and configured",
            "Basic knowledge of cloud architecture",
            f"Understanding of {project_type} applications"
        ],
        
        "architecture": {
            "pattern": "Serverless" if any("lambda" in s.lower() for s in services) else "Traditional",
            "services_count": service_count,
            "scalability": f"Designed for {estimated_users:,} users",
            "services": services
        },
        
        "next_steps": [
            f"1. Set up AWS account with budget alert for {cost_range}",
            "2. Review prerequisites and gather tools",
            "3. Follow implementation phases in order",
            f"4. Test with {min(100, estimated_users // 10)} concurrent users",
            "5. Monitor CloudWatch metrics closely",
            "6. Scale gradually based on actual usage"
        ],
        
        # ✅ ADD PHASES HERE
        "phases": generate_implementation_phases(services, project_type, estimated_users)
    }
    
    return guide


def generate_implementation_phases(services: List[str], project_type: str, users: int) -> List[Dict]:
    """Generate implementation phases based on services"""
    
    phases = []
    
    # Phase 1: Foundation
    phase1_tasks = [
        "Create AWS account or use existing",
        "Set up IAM users with MFA",
        "Configure AWS CLI",
        "Set up billing alerts"
    ]
    
    phases.append({
        "name": "Foundation Setup",
        "duration": "2-3 hours",
        "description": "Set up AWS account and basic infrastructure",
        "steps": phase1_tasks
    })
    
    # Phase 2: Core Services
    phase2_tasks = []
    
    if any("cognito" in s.lower() for s in services):
        phase2_tasks.append("Set up Cognito user pool")
    
    if any("dynamodb" in s.lower() for s in services):
        phase2_tasks.append("Create DynamoDB tables")
    elif any("rds" in s.lower() for s in services):
        phase2_tasks.append("Set up RDS database")
    
    if any("s3" in s.lower() for s in services):
        phase2_tasks.append("Create S3 buckets with proper policies")
    
    if phase2_tasks:
        phases.append({
            "name": "Core Infrastructure",
            "duration": "4-6 hours",
            "description": "Set up database, storage, and authentication",
            "steps": phase2_tasks
        })
    
    # Phase 3: Compute & API
    phase3_tasks = []
    
    if any("lambda" in s.lower() for s in services):
        phase3_tasks.extend([
            "Create Lambda functions",
            "Set up environment variables",
            "Configure IAM roles"
        ])
    
    if any("apigateway" in s.lower() or "api gateway" in s.lower() for s in services):
        phase3_tasks.extend([
            "Create API Gateway",
            "Configure endpoints",
            "Set up CORS"
        ])
    
    if phase3_tasks:
        phases.append({
            "name": "Compute & API Layer",
            "duration": "6-8 hours",
            "description": "Implement business logic and API endpoints",
            "steps": phase3_tasks
        })
    
    # Phase 4: Integration & Testing
    phases.append({
        "name": "Integration & Testing",
        "duration": "4-6 hours",
        "description": "Connect all services and test end-to-end",
        "steps": [
            "Connect Lambda to database",
            "Test API endpoints",
            "Set up CloudWatch logging",
            "Configure error handling",
            "Test authentication flow"
        ]
    })
    
    # Phase 5: Optimization
    if users > 1000:
        phases.append({
            "name": "Performance Optimization",
            "duration": "3-4 hours",
            "description": "Optimize for scale and performance",
            "steps": [
                "Enable CloudFront CDN",
                "Configure caching",
                "Set up auto-scaling",
                "Optimize database queries",
                "Enable X-Ray tracing"
            ]
        })
    
    # Phase 6: Deployment
    phases.append({
        "name": "Production Deployment",
        "duration": "2-3 hours",
        "description": "Deploy to production environment",
        "steps": [
            "Set up CI/CD pipeline",
            "Configure monitoring dashboards",
            "Deploy to production",
            "Run smoke tests",
            "Monitor for 24 hours"
        ]
    })
    
    return phases


def get_troubleshooting_guide(services: List[str]) -> Dict[str, str]:
    """Troubleshooting tips for services"""
    
    guide = {
        "general": "Check CloudWatch Logs first. Enable X-Ray for tracing."
    }
    
    if any("lambda" in s.lower() for s in services):
        guide["lambda_timeout"] = "Increase timeout or optimize code"
        guide["lambda_errors"] = "Check CloudWatch Logs for stack traces"
    
    if any("dynamodb" in s.lower() for s in services):
        guide["dynamodb_throttling"] = "Increase capacity or enable auto-scaling"
    
    if any("apigateway" in s.lower() for s in services):
        guide["api_502"] = "Check Lambda integration and permissions"
    
    return guide
