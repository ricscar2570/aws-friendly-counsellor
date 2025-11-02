"""
Dynamic Guide Generator - Creates personalized implementation guides
"""
from typing import List, Dict, Any

def generate_guide(services: List[str], classification: Dict, estimated_users: int) -> Dict[str, Any]:
    """Generate DYNAMIC implementation guide based on project specifics"""
    
    project_type = classification.get("primary", "application")
    features = classification.get("features", [])
    
    # DYNAMIC: Timeline based on complexity
    service_count = len(services)
    total_hours = 15 + (service_count * 5)
    days = max(3, total_hours // 8)
    
    # DYNAMIC: Difficulty
    complexity_score = 0
    for s in services:
        if "cognito" in s.lower():
            complexity_score += 2
        elif "dynamodb" in s.lower():
            complexity_score += 1
        elif "rds" in s.lower():
            complexity_score += 3
    difficulty = "Beginner" if complexity_score < 2 else "Intermediate" if complexity_score < 4 else "Advanced"
    
    # DYNAMIC: Cost estimate
    if estimated_users < 1000:
        cost_range = "$0-25"
        tier_message = "Entirely covered by AWS Free Tier for first 12 months"
    elif estimated_users < 10000:
        cost_range = "$25-100"
        tier_message = "Mostly covered by Free Tier, minimal costs expected"
    elif estimated_users < 100000:
        cost_range = "$100-500"
        tier_message = "Beyond Free Tier, budget for moderate usage costs"
    else:
        cost_range = "$500-2000"
        tier_message = "High-scale deployment, requires significant infrastructure budget"
    
    # DYNAMIC: Service instructions
    service_details = []
    for service in services:
        detail = get_service_detail(service, estimated_users, project_type)
        if detail:
            service_details.append(detail)
    
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
        
        "prerequisites": get_dynamic_prerequisites(services, estimated_users),
        
        "architecture": {
            "pattern": "Serverless" if any("lambda" in s.lower() for s in services) else "Traditional",
            "services_count": service_count,
            "scalability": f"Designed for {estimated_users:,} users",
            "services": services
        },
        
        "service_implementations": service_details,
        
        "implementation_phases": get_dynamic_phases(services, estimated_users),
        
        "best_practices": [
            "Use environment variables for configuration",
            "Enable CloudWatch logging for all services",
            "Implement proper error handling",
            "Use IAM roles instead of access keys",
            "Tag all resources for cost tracking",
            "Set up monitoring from day one",
            "Follow least privilege principle for IAM",
            "Enable versioning for critical resources"
        ],
        
        "cost_optimization": get_cost_tips(services, estimated_users),
        
        "monitoring_setup": {
            "cloudwatch_dashboard": "Set up dashboard with key metrics",
            "alarms": get_alarm_config(services, estimated_users),
            "logs_retention": "30 days for production, 7 days for dev"
        },
        
        "deployment_checklist": get_deployment_checklist(services, estimated_users),
        
        "troubleshooting": get_troubleshooting_guide(services),
        
        "next_steps": [
            f"1. Set up AWS account with budget alert for {cost_range}",
            "2. Review prerequisites and gather tools",
            "3. Follow implementation phases in order",
            f"4. Test with {min(100, estimated_users // 10)} concurrent users",
            "5. Monitor CloudWatch metrics closely",
            "6. Scale gradually based on actual usage"
        ]
    }
    
    return guide


def get_service_detail(service: str, users: int, project_type: str) -> Dict[str, str]:
    """Get dynamic service-specific setup instructions"""
    
    service_lower = service.lower().replace('amazon ', '').replace('aws ', '')
    
    # Scale-based configs
    if users < 1000:
        lambda_memory, lambda_timeout = 256, 10
    elif users < 10000:
        lambda_memory, lambda_timeout = 512, 30
    else:
        lambda_memory, lambda_timeout = 1024, 60
    
    configs = {
        "lambda": {
            "service": service,
            "configuration": f"Memory: {lambda_memory}MB, Timeout: {lambda_timeout}s, Concurrency: {max(10, users // 100)}",
            "setup_command": f"""
# Create Lambda function optimized for {users:,} users
aws lambda create-function \\
  --function-name {project_type}-api \\
  --runtime python3.11 \\
  --handler index.handler \\
  --memory-size {lambda_memory} \\
  --timeout {lambda_timeout} \\
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \\
  --zip-file fileb://function.zip
""",
            "why": f"Configured for {users:,} users with appropriate memory and timeout settings"
        },
        
        "dynamodb": {
            "service": service,
            "configuration": f"Billing: {'On-demand' if users < 10000 else 'Provisioned'}, Expected load: {users // 10} reads/sec",
            "setup_command": f"""
# Create DynamoDB table for {users:,} users
aws dynamodb create-table \\
  --table-name {project_type}-data \\
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \\
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \\
  --billing-mode {'PAY_PER_REQUEST' if users < 10000 else 'PROVISIONED'} \\
  --tags Key=Project,Value={project_type}
""",
            "why": f"{'On-demand billing is cost-effective for unpredictable traffic' if users < 10000 else 'Provisioned capacity optimizes costs at this scale'}"
        },
        
        "s3": {
            "service": service,
            "configuration": f"Versioning: Enabled, Lifecycle: {'Standard' if users < 10000 else 'Intelligent-Tiering'}",
            "setup_command": f"""
# Create S3 bucket for {project_type}
BUCKET_NAME="{project_type}-storage-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket $BUCKET_NAME --server-side-encryption-configuration '{{"Rules":[{{"ApplyServerSideEncryptionByDefault":{{"SSEAlgorithm":"AES256"}}}}]}}'
""",
            "why": "Versioning protects against accidental deletions, encryption secures data at rest"
        },
        
        "cognito": {
            "service": service,
            "configuration": "MFA: Optional, Password: 8+ chars with complexity",
            "setup_command": f"""
# Create Cognito User Pool
aws cognito-idp create-user-pool \\
  --pool-name {project_type}-users \\
  --policies "PasswordPolicy={{MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true}}" \\
  --auto-verified-attributes email \\
  --username-attributes email
""",
            "why": "Email-based authentication with strong password policy for security"
        },
        
        "apigateway": {
            "service": service,
            "configuration": f"Throttle: {users // 10} requests/sec, CORS: Enabled",
            "setup_command": f"""
# Create API Gateway REST API
aws apigateway create-rest-api \\
  --name {project_type}-api \\
  --description "API for {project_type}" \\
  --endpoint-configuration types=REGIONAL
""",
            "why": f"Regional endpoint with throttling configured for {users:,} users"
        }
    }
    
    for key in configs:
        if key in service_lower:
            return configs[key]
    
    return {
        "service": service,
        "configuration": "Standard AWS configuration",
        "setup_command": f"# Set up {service} following AWS best practices",
        "why": "Configured based on AWS recommendations"
    }


def get_dynamic_prerequisites(services: List[str], users: int) -> List[str]:
    """Dynamic prerequisites based on services and scale"""
    
    prereqs = [
        "✅ AWS Account with admin or PowerUser access",
        "✅ AWS CLI installed and configured: `aws configure`",
        "✅ Python 3.9+ installed",
        "✅ Git for version control",
        "✅ Code editor (VS Code recommended)"
    ]
    
    if any("lambda" in s.lower() for s in services):
        prereqs.append("✅ AWS SAM CLI: `sam --version`")
        prereqs.append("✅ Docker for local testing")
    
    if any("cognito" in s.lower() for s in services):
        prereqs.append("✅ Understanding of OAuth 2.0 / JWT tokens")
    
    if users > 10000:
        prereqs.append("⚠️  Budget alert: Set up billing alarm")
        prereqs.append("⚠️  Load testing tool: Artillery or JMeter")
    
    if users > 100000:
        prereqs.append("🚨 Consider AWS Enterprise Support")
    
    return prereqs


def get_dynamic_phases(services: List[str], users: int) -> List[Dict]:
    """Generate implementation phases based on services"""
    
    phases = [
        {
            "phase": 1,
            "name": "Foundation Setup",
            "duration": "2-3 hours",
            "tasks": [
                "Create AWS account structure",
                "Set up IAM roles and policies",
                "Configure billing alerts",
                "Initialize Git repository"
            ]
        }
    ]
    
    if any(db in s.lower() for s in services for db in ["dynamodb", "rds"]):
        phases.append({
            "phase": len(phases) + 1,
            "name": "Database Setup",
            "duration": "4-6 hours",
            "tasks": [
                "Design database schema",
                "Create tables with indexes",
                "Set up backups",
                "Implement data access layer"
            ]
        })
    
    if any("lambda" in s.lower() for s in services):
        phases.append({
            "phase": len(phases) + 1,
            "name": "API Development",
            "duration": "6-8 hours",
            "tasks": [
                "Create Lambda functions",
                "Set up API Gateway",
                "Implement business logic",
                "Add error handling"
            ]
        })
    
    if any("cognito" in s.lower() for s in services):
        phases.append({
            "phase": len(phases) + 1,
            "name": "Authentication",
            "duration": "4-5 hours",
            "tasks": [
                "Configure Cognito",
                "Implement auth flows",
                "Add JWT validation",
                "Test authentication"
            ]
        })
    
    phases.extend([
        {
            "phase": len(phases) + 1,
            "name": "Testing & QA",
            "duration": f"{'6-8' if users > 10000 else '3-4'} hours",
            "tasks": [
                "Write unit tests",
                f"Load test with {min(users // 10, 1000)} users",
                "Security audit",
                "Performance tuning"
            ]
        },
        {
            "phase": len(phases) + 1,
            "name": "Deployment",
            "duration": "2-3 hours",
            "tasks": [
                "Set up CI/CD",
                "Configure monitoring",
                "Deploy to production",
                "Smoke test"
            ]
        }
    ])
    
    return phases


def get_cost_tips(services: List[str], users: int) -> List[str]:
    """Cost optimization tips based on scale"""
    
    tips = []
    
    if users < 10000:
        tips.append("💰 Stay within Free Tier limits")
        tips.append("💰 Use on-demand billing for DynamoDB")
    else:
        tips.append("💰 Consider Reserved Capacity for savings")
        tips.append("💰 Enable auto-scaling to optimize costs")
    
    if any("s3" in s.lower() for s in services):
        tips.append("💰 Set up S3 lifecycle policies")
    
    tips.extend([
        "💰 Set up AWS Budgets with alerts",
        "💰 Tag all resources for cost tracking",
        "💰 Review Cost Explorer weekly"
    ])
    
    return tips


def get_alarm_config(services: List[str], users: int) -> List[str]:
    """CloudWatch alarms based on services"""
    
    alarms = ["Set up billing alarm"]
    
    if any("lambda" in s.lower() for s in services):
        alarms.extend([
            "Lambda errors > 5 in 5 minutes",
            "Lambda duration > 5000ms"
        ])
    
    if any("dynamodb" in s.lower() for s in services):
        alarms.append("DynamoDB throttled requests > 10")
    
    if users > 10000:
        alarms.append("API Gateway 5XX errors > 1%")
    
    return alarms


def get_deployment_checklist(services: List[str], users: int) -> List[str]:
    """Deployment checklist based on services"""
    
    checklist = [
        "✅ All environment variables set",
        "✅ IAM roles have minimum permissions",
        "✅ CloudWatch logging enabled",
        "✅ Billing alerts configured",
        "✅ Backup strategy in place"
    ]
    
    if users > 10000:
        checklist.extend([
            "✅ Auto-scaling configured",
            "✅ Multi-AZ deployment"
        ])
    
    if any("s3" in s.lower() for s in services):
        checklist.append("✅ S3 versioning enabled")
    
    return checklist


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
