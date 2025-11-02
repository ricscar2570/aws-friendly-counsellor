from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

AWS_SERVICES_DB = {
    "lambda": {
        "name": "AWS Lambda",
        "category": "compute",
        "typical_monthly": "10-50",
        "free_tier": "1M requests + 400K GB-seconds"
    },
    "dynamodb": {
        "name": "Amazon DynamoDB",
        "category": "database",
        "typical_monthly": "5-30",
        "free_tier": "25GB + 25 WCU/RCU"
    },
    "s3": {
        "name": "Amazon S3",
        "category": "storage",
        "typical_monthly": "5-20",
        "free_tier": "5GB storage"
    },
    "cognito": {
        "name": "Amazon Cognito",
        "category": "authentication",
        "typical_monthly": "0-25",
        "free_tier": "50K MAU"
    },
    "api-gateway": {
        "name": "Amazon API Gateway",
        "category": "api",
        "typical_monthly": "5-30",
        "free_tier": "1M requests (12 months)"
    },
}

def calculate_costs(services: List[str], users: int) -> Dict:
    logger.info(f"Calculating costs for {len(services)} services, {users} users")
    
    total_min = 0
    total_max = 0
    breakdown = {}
    
    for service_id in services:
        if service_id not in AWS_SERVICES_DB:
            continue
        
        service = AWS_SERVICES_DB[service_id]
        typical = service["typical_monthly"]
        
        parts = typical.split("-")
        min_cost = float(parts[0])
        max_cost = float(parts[1]) if len(parts) > 1 else min_cost * 2
        
        total_min += min_cost
        total_max += max_cost
        breakdown[service["name"]] = f"${min_cost}-{max_cost}"
    
    typical = (total_min + total_max) / 2
    
    return {
        "summary": {
            "free_tier_viable": True,
            "minimum": f"${total_min:.0f}",
            "typical": f"${typical:.0f}",
            "maximum": f"${total_max:.0f}"
        },
        "breakdown": breakdown
    }
