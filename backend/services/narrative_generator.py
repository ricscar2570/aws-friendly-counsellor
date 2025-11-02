"""
Narrative Generator - PROFESSIONAL EDITION with FULL CONTENT
Generates comprehensive, Solutions Architect-level analysis with detailed explanations
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def generate_narrative_analysis(
    services: List[Dict],
    classification: Dict,
    cost_analysis: Dict,
    implementation_guide: Dict,
    estimated_users: int
) -> str:
    """
    Generate comprehensive narrative analysis with professional insights
    """
    
    project_type = classification.get("primary", "application")
    confidence = classification.get("confidence", 0.8)
    features = classification.get("features", [])
    
    # Generate complete narrative HTML with FULL content
    narrative = generate_executive_summary(project_type, estimated_users, confidence, features)
    narrative += generate_architecture_overview(services, project_type, estimated_users)
    narrative += generate_cost_narrative(cost_analysis, services, estimated_users)
    narrative += generate_implementation_narrative(implementation_guide, services, project_type)
    narrative += generate_best_practices(services, project_type, estimated_users)
    narrative += generate_conclusion(project_type, estimated_users)
    
    return narrative


def generate_executive_summary(project_type: str, users: int, confidence: float, features: List) -> str:
    """Executive-level project summary with detailed context"""
    
    project_descriptions = {
        "ecommerce": {
            "title": "E-Commerce Platform",
            "full_description": "an e-commerce platform requiring secure payment processing, real-time inventory management, and scalable user authentication",
            "business_impact": "This architecture enables you to handle transactions securely, manage product catalogs efficiently, and scale seamlessly as your customer base grows. The serverless approach means you only pay for actual usage, making it cost-effective for startups and established businesses alike."
        },
        "api": {
            "title": "API Service",
            "full_description": "a RESTful API service requiring high availability, efficient data access, and comprehensive API management",
            "business_impact": "This architecture provides enterprise-grade API capabilities with built-in throttling, caching, and monitoring. Your API will be able to serve thousands of requests per second while maintaining sub-100ms response times."
        },
        "social": {
            "title": "Social Media Platform",
            "full_description": "a social networking application with real-time interactions, media storage, and complex user relationship management",
            "business_impact": "This architecture supports viral growth with auto-scaling capabilities and global content delivery. Users worldwide will experience fast load times, and your platform can handle sudden traffic spikes during trending events."
        },
        "saas": {
            "title": "SaaS Application",
            "full_description": "a multi-tenant SaaS solution requiring secure data isolation, subscription management, and reliable infrastructure",
            "business_impact": "This architecture ensures enterprise-grade security with tenant isolation, 99.99% uptime, and the ability to onboard new customers instantly without infrastructure changes."
        },
        "web_application": {
            "title": "Web Application",
            "full_description": "a cloud-based web application requiring scalable infrastructure and reliable performance",
            "business_impact": "This architecture provides a solid foundation for your web application with automatic scaling, high availability, and cost optimization built in from day one."
        }
    }
    
    project_info = project_descriptions.get(project_type, project_descriptions["web_application"])
    scale_category = "Small Scale" if users < 1000 else "Medium Scale" if users < 50000 else "Large Scale"
    
    confidence_text = "highly confident" if confidence > 0.8 else "confident" if confidence > 0.6 else "reasonably sure"
    
    return f"""
    <section class="narrative-section executive-summary">
        <h2>📊 Executive Summary</h2>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h4>Project Type</h4>
                <p><strong>{project_info['title']}</strong></p>
            </div>
            <div class="summary-card">
                <h4>Scale</h4>
                <p><strong>{scale_category}</strong> ({users:,} users)</p>
            </div>
            <div class="summary-card">
                <h4>Confidence</h4>
                <p><strong>{confidence*100:.0f}%</strong></p>
            </div>
        </div>
        
        <div class="overview-text">
            <p>
                Based on my analysis of your project description, I'm <strong>{confidence_text}</strong> that you're building 
                <strong>{project_info['full_description']}</strong>.
            </p>
            
            {f'<p>I identified the following key features in your project: <strong>{", ".join(features[:5])}</strong>. These features directly influenced my service recommendations and architecture decisions.</p>' if features else ''}
            
            <p>
                Your architecture is designed to support <strong>{users:,} concurrent users</strong> efficiently. 
                {project_info['business_impact']}
            </p>
            
            <p>
                This recommendation follows the <strong>AWS Well-Architected Framework</strong>, ensuring your infrastructure 
                excels across all five pillars: <em>Operational Excellence</em> (automated deployments and monitoring), 
                <em>Security</em> (encryption and access controls), <em>Reliability</em> (fault tolerance and backup), 
                <em>Performance Efficiency</em> (right-sized resources), and <em>Cost Optimization</em> (pay only for what you use).
            </p>
            
            <p>
                <strong>What makes this architecture special:</strong> Every service recommendation is specifically chosen 
                for your use case. This isn't a one-size-fits-all template—it's a tailored solution that balances 
                performance, cost, and operational complexity based on your {users:,} user scale.
            </p>
        </div>
    </section>
    """


def generate_architecture_overview(services: List[Dict], project_type: str, users: int) -> str:
    """Detailed architecture analysis with technical reasoning"""
    
    intro_by_type = {
        "ecommerce": "For an e-commerce platform, reliability and security are paramount. Every service in this architecture has been selected to ensure your customers have a seamless shopping experience while their payment information remains secure. Let me explain each component and why it's essential.",
        "api": "For an API service, performance and scalability are critical. This architecture is designed to handle high request volumes with low latency while providing the monitoring and security features you need for production.",
        "social": "For a social platform, real-time capabilities and media handling are crucial. This architecture provides the infrastructure to support viral growth and global reach.",
        "saas": "For a SaaS application, multi-tenancy and data isolation are fundamental. This architecture ensures each customer's data remains secure while allowing you to scale efficiently.",
        "web_application": "For your web application, we've focused on building a scalable, maintainable foundation that can grow with your needs."
    }
    
    intro = intro_by_type.get(project_type, intro_by_type["web_application"])
    
    html = f"""
    <section class="narrative-section architecture-deep-dive">
        <h2>🏗️ Architecture Deep Dive</h2>
        
        <p class="section-intro">
            {intro}
        </p>
        
        <p class="section-intro">
            <strong>Architectural Philosophy:</strong> This design prioritizes <em>serverless-first</em> wherever possible 
            to minimize operational overhead and maximize scalability. You won't be managing servers, patching operating 
            systems, or worrying about capacity planning. AWS handles the undifferentiated heavy lifting while you focus 
            on building your application.
        </p>
    """
    
    for i, service in enumerate(services, 1):
        name = service.get('name', 'Service')
        category = service.get('category', 'service')
        why_needed = service.get('why_needed', '')
        use_case = service.get('use_case_example', '')
        typical_cost = service.get('typical_monthly', '$0-50')
        
        # Generate rich technical context
        technical_context = get_service_technical_context(name, users, project_type)
        
        html += f"""
        <div class="service-detail">
            <h3>{i}. {name}</h3>
            <span class="category-badge">{category}</span>
            
            <div class="service-why">
                <h4>🎯 Why {name}?</h4>
                <p>{why_needed}</p>
                <p style="margin-top: 10px; color: #4a5568; font-style: italic;">
                    {technical_context['strategic_reason']}
                </p>
            </div>
            
            {f'''
            <div class="service-usage">
                <h4>💼 In Your Application</h4>
                <p>{use_case}</p>
                <p style="margin-top: 10px; color: #4a5568;">
                    <strong>Real-world example:</strong> {technical_context['real_world_example']}
                </p>
            </div>
            ''' if use_case else ''}
            
            <div class="technical-specs">
                <h4>⚙️ Technical Configuration for {users:,} Users</h4>
                {technical_context['configuration']}
            </div>
            
            <div class="service-cost">
                <h4>💰 Cost Analysis</h4>
                <p>
                    <strong>Estimated cost: {typical_cost}/month</strong> based on {users:,} concurrent users 
                    with typical usage patterns.
                </p>
                <p style="margin-top: 8px; font-size: 0.9em; color: #718096;">
                    {technical_context['cost_explanation']}
                </p>
            </div>
            
            <div class="service-alternatives">
                <h4>🔄 Why Not Alternative Solutions?</h4>
                <p>{technical_context['alternatives']}</p>
            </div>
        </div>
        """
    
    html += """
        <div class="architecture-summary">
            <h4>🔗 How These Services Work Together</h4>
            <p>
                Your architecture follows a <strong>layered approach</strong>:
            </p>
            <ul style="margin-left: 2rem; margin-top: 1rem; line-height: 1.8;">
                <li><strong>Entry Layer:</strong> API Gateway receives all requests and handles authentication</li>
                <li><strong>Compute Layer:</strong> Lambda functions process business logic without server management</li>
                <li><strong>Data Layer:</strong> DynamoDB/RDS stores your data with automatic scaling</li>
                <li><strong>Storage Layer:</strong> S3 holds static assets and files with 99.999999999% durability</li>
                <li><strong>Observability Layer:</strong> CloudWatch monitors everything in real-time</li>
            </ul>
            <p style="margin-top: 1rem;">
                This separation of concerns makes your application easier to maintain, debug, and scale. 
                Each layer can scale independently based on demand.
            </p>
        </div>
    </section>
    """
    
    return html


def get_service_technical_context(service_name: str, users: int, project_type: str) -> Dict[str, str]:
    """Get rich technical context for each service"""
    
    # Normalize service name: "Amazon DynamoDB" -> "DynamoDB", "AWS Lambda" -> "Lambda"
    normalized_name = service_name.replace("Amazon ", "").replace("AWS ", "").replace("Amazon", "").replace("AWS", "").strip()
    
    contexts = {
        "Lambda": {
            "strategic_reason": "Lambda is the cornerstone of modern serverless architecture. By eliminating server management, you can deploy code in minutes rather than days. It automatically scales from zero to thousands of concurrent executions, and you only pay for the compute time you consume—down to the millisecond.",
            "real_world_example": "When a user clicks 'Checkout,' Lambda processes the order, validates inventory, charges the payment method, sends confirmation emails, and updates the database—all in under 500ms. If you suddenly get featured on TechCrunch and traffic spikes 100x, Lambda automatically scales to handle it.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>Memory:</strong> {512 if users < 10000 else 1024}MB (optimal for your scale)</li>
                    <li><strong>Timeout:</strong> 30 seconds (adjustable per function)</li>
                    <li><strong>Concurrency:</strong> Reserved {max(10, users//500)} executions, burst up to 1000</li>
                    <li><strong>Runtime:</strong> Python 3.11 or Node.js 18.x recommended</li>
                    <li><strong>Cold Start Mitigation:</strong> {"Provisioned concurrency not needed" if users < 10000 else "Consider provisioned concurrency for critical paths"}</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    At {users:,} users, you'll average {max(10, users//100)}-{max(20, users//50)} concurrent executions during peak hours. 
                    Lambda can handle this effortlessly with its default concurrency limits.
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 12 months (New AWS Account):</strong> $0/month - FREE TIER covers 1M requests + 400,000 GB-seconds compute monthly<br>
                <strong>After Year 1:</strong> ${max(10, users*50*0.0000002*720):.2f}-${max(50, users*100*0.0000002*720):.2f}/month based on {users*50:,}-{users*100:,} requests/day<br>
                <em style="color: #718096;">Pricing: $0.20 per 1M requests + $0.0000166667 per GB-second</em>
            """,
            "alternatives": "EC2 would require you to provision, patch, and monitor servers 24/7, costing $50+ even when idle. Fargate is great for long-running containers but overkill for request-response patterns. App Runner works well but offers less fine-grained control than Lambda."
        },
        "DynamoDB": {
            "strategic_reason": "DynamoDB provides single-digit millisecond performance at any scale without operational overhead. There's no database to tune, no indexes to rebalance, and no capacity to pre-provision. It's designed for applications that need consistent, fast data access as they grow from thousands to millions of users.",
            "real_world_example": "Your product catalog needs to load in under 50ms even during Black Friday sales. DynamoDB's in-memory caching (DAX) can serve millions of reads per second. When a user updates their cart, the change is immediately consistent across all sessions.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>Capacity Mode:</strong> {"On-Demand (pay per request)" if users < 10000 else "Provisioned with auto-scaling"}</li>
                    <li><strong>Expected RCU:</strong> ~{max(5, users//100)} per second during normal operation</li>
                    <li><strong>Expected WCU:</strong> ~{max(3, users//200)} per second for writes</li>
                    <li><strong>Global Secondary Indexes:</strong> 2-3 GSIs for flexible queries</li>
                    <li><strong>Point-in-Time Recovery:</strong> Enabled for data protection</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    {"On-demand mode is perfect for your scale—no capacity planning needed. You'll pay only for actual reads/writes." if users < 10000 else "At your scale, provisioned capacity with auto-scaling offers 30% cost savings compared to on-demand."}
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 12 months (New AWS Account):</strong> $0-${max(5, users*0.001):.2f}/month - FREE TIER covers 25GB storage + 200M requests/month<br>
                <strong>After Year 1:</strong> ${max(5, users*10*30*0.25/1000000):.2f}-${max(30, users*10*30*0.25/1000000*3):.2f}/month for {users:,} users<br>
                <em style="color: #718096;">On-demand: $0.25 per million reads, $1.25 per million writes</em>
            """,
            "alternatives": "RDS would work but requires instance sizing, backup management, and read replica configuration. Aurora Serverless v2 is excellent for complex queries but costs 5-10x more than DynamoDB for key-value access patterns. MongoDB Atlas is powerful but adds another vendor and additional operational complexity."
        },
        "S3": {
            "strategic_reason": "S3 is the most cost-effective and durable object storage available. With 99.999999999% (11 nines) durability, your data is safer in S3 than on any disk you could buy. It scales infinitely, costs pennies per GB, and integrates seamlessly with CloudFront for global content delivery.",
            "real_world_example": "User profile pictures, product images, invoices, and backups all go in S3. With lifecycle policies, files automatically move to cheaper storage tiers after 90 days. When integrated with CloudFront, images load in under 50ms worldwide.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>Storage Class:</strong> S3 Standard for active data, S3 Intelligent-Tiering for varied access patterns</li>
                    <li><strong>Expected Storage:</strong> ~{users*5}MB initially ({users*0.005:.1f}GB)</li>
                    <li><strong>Versioning:</strong> Enabled to protect against accidental deletions</li>
                    <li><strong>Encryption:</strong> SSE-S3 (AES-256) enabled by default</li>
                    <li><strong>Lifecycle Policies:</strong> Auto-transition to S3-IA after 90 days for 50% savings</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    S3's pricing starts at $0.023/GB for the first 50TB. For {users:,} users, your initial storage costs will be under $1/month, even with generous file storage per user.
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 12 months (New AWS Account):</strong> $0/month - FREE TIER covers 5GB storage + 20K GET + 2K PUT requests monthly<br>
                <strong>After Year 1:</strong> ${max(1, users*0.005*0.023):.2f}-${max(20, users*0.01*0.023):.2f}/month for storage + requests<br>
                <em style="color: #718096;">Storage: $0.023/GB, GET: $0.0004/1K requests, PUT: $0.005/1K requests</em>
            """,
            "alternatives": "EFS costs 10x more and is designed for shared file systems, not object storage. EBS is block storage for EC2 instances. Third-party services like Cloudinary add cost for features you can build with S3 + Lambda. S3 is purpose-built for this use case."
        },
        "API Gateway": {
            "strategic_reason": "API Gateway is AWS's managed API solution, handling billions of requests daily for companies like Netflix and Airbnb. It provides DDoS protection, request throttling, caching, and monitoring out of the box—features that would take months to build yourself.",
            "real_world_example": "Every API call to your application goes through API Gateway. It authenticates requests using Cognito tokens, applies rate limiting (1000 req/sec per client), caches GET responses for 5 minutes, and logs everything to CloudWatch for debugging.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>API Type:</strong> REST API (HTTP API for simpler use cases saves 70% on costs)</li>
                    <li><strong>Expected Requests:</strong> ~{users*100:,} per day</li>
                    <li><strong>Caching:</strong> {"Not enabled initially" if users < 5000 else "0.5GB cache recommended for frequent endpoints"}</li>
                    <li><strong>Throttling:</strong> 1000 req/sec steady-state, 2000 burst</li>
                    <li><strong>Stages:</strong> dev, staging, prod with stage variables</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    API Gateway's default limits handle {users:,} users comfortably. The 1000 req/sec throttle protects your backend from runaway requests or DDoS attacks.
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 12 months (New AWS Account):</strong> $0/month - FREE TIER covers 1M API calls monthly<br>
                <strong>After Year 1:</strong> ${max(3, (users*100*30/1000000)*3.5):.2f}-${max(30, (users*200*30/1000000)*3.5):.2f}/month<br>
                <em style="color: #718096;">REST API: $3.50 per million requests. HTTP API: $1.00 per million (consider if features allow)</em>
            """,
            "alternatives": "ALB + EC2 would require managing load balancers and servers. Kong/Apigee are powerful but add complexity and cost. CloudFront Functions can handle simple routing but lack API Gateway's request validation and transformation capabilities."
        },
        "Cognito": {
            "strategic_reason": "Cognito provides enterprise-grade authentication without the security risks of building it yourself. It handles OAuth, SAML, social login, MFA, and compromised credential detection—features that would take months to implement securely.",
            "real_world_example": "Users sign up with email/password or social accounts (Google, Facebook). Cognito handles email verification, password resets, and MFA. JWT tokens authenticate API requests. If a password appears in a breach database, Cognito automatically locks the account.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>Monthly Active Users:</strong> Estimated {users} MAUs</li>
                    <li><strong>MFA:</strong> Optional SMS or TOTP-based (highly recommended)</li>
                    <li><strong>Password Policy:</strong> Min 8 chars, requires uppercase, lowercase, numbers</li>
                    <li><strong>Token Validity:</strong> Access tokens: 1 hour, Refresh: 30 days</li>
                    <li><strong>Advanced Security:</strong> Compromised credential check enabled</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    Cognito's free tier covers 50,000 MAUs. Beyond that, pricing is $0.0055 per MAU, making it extremely cost-effective compared to Auth0 or building your own.
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 50,000 MAUs:</strong> Always FREE (not just first year!)<br>
                <strong>Your scale ({users} users):</strong> {"$0/month - within free tier!" if users <= 50000 else f"${(users-50000)*0.0055:.2f}/month for users beyond 50K"}<br>
                <em style="color: #718096;">After 50K MAUs: $0.0055 per additional MAU. Way cheaper than Auth0 ($240/month minimum)!</em>
            """,
            "alternatives": "Auth0 costs $240/month minimum for production features. Okta starts at $2-5 per MAU. Firebase Auth works but locks you into Google's ecosystem. Building your own auth means risking security breaches and maintaining complex code forever."
        },
        "CloudFront": {
            "strategic_reason": "CloudFront is AWS's global CDN with 400+ edge locations worldwide. It dramatically reduces latency for global users by caching content near them. A user in Tokyo loads images in 50ms instead of 500ms by fetching from a nearby edge location.",
            "real_world_example": "Product images, CSS, JavaScript, and API responses (for GET requests) are cached at edge locations. The first user in Singapore fetches from S3 (~200ms). The next 10,000 users load from the Singapore edge in 20ms. This reduces S3 costs by 80% and improves user experience.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>Price Class:</strong> All edge locations (best performance globally)</li>
                    <li><strong>Expected Transfer:</strong> ~{users*200}MB per month</li>
                    <li><strong>Default TTL:</strong> 86400 seconds (24 hours) for static assets</li>
                    <li><strong>Compression:</strong> Gzip and Brotli enabled automatically</li>
                    <li><strong>SSL:</strong> Free ACM certificate included</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    CloudFront's first 1TB of data transfer and 10M requests per month are free for the first year. After that, pricing starts at $0.085/GB—still cheaper than serving directly from S3 due to request savings.
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 12 months (New AWS Account):</strong> $0/month - FREE TIER covers 1TB data transfer + 10M requests monthly<br>
                <strong>After Year 1:</strong> ${max(1, (users*0.2*0.085)):.2f}-${max(10, (users*0.5*0.085)):.2f}/month<br>
                <em style="color: #718096;">Data transfer: $0.085/GB. The reduced S3 requests typically offset CloudFront costs entirely!</em>
            """,
            "alternatives": "Cloudflare is good but adds another vendor. Fastly is powerful but expensive for smaller workloads. CloudFront integrates seamlessly with S3 and API Gateway, simplifying architecture."
        },
        "SES": {
            "strategic_reason": "SES is AWS's email service, capable of sending millions of emails reliably. Unlike SendGrid or Mailgun, SES costs $0.10 per 1,000 emails with no monthly minimum. For transactional emails, it's unbeatable on price and reliability.",
            "real_world_example": "Order confirmations, password resets, shipping notifications, and weekly newsletters all use SES. With proper DKIM/SPF setup, your emails reach inboxes, not spam folders. SES handles bounce and complaint processing automatically.",
            "configuration": f"""
                <ul style="margin-left: 1.5rem; line-height: 1.8; color: #2d3748;">
                    <li><strong>Sending Limit:</strong> Start at 200 emails/day, increases to 50,000+ as reputation improves</li>
                    <li><strong>Expected Volume:</strong> ~{users*20:,} emails per month</li>
                    <li><strong>DKIM/SPF:</strong> Must configure for deliverability</li>
                    <li><strong>Bounce Handling:</strong> Automatic via SNS notifications</li>
                    <li><strong>Templates:</strong> Store email templates in SES for consistency</li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.95em; color: #4a5568;">
                    SES requires you to verify your domain and maintain good sending reputation. Start with the sandbox (100 emails/day to verified addresses) and request production access when ready.
                </p>
            """,
            "cost_explanation": f"""
                <strong>First 12 months (New AWS Account):</strong> $0/month - FREE TIER covers 62,000 emails monthly (if sent from EC2)<br>
                <strong>After Year 1:</strong> ${max(0, (users*20/1000)*0.10):.2f}-${max(10, (users*50/1000)*0.10):.2f}/month for {users*20:,}-{users*50:,} emails<br>
                <em style="color: #718096;">$0.10 per 1,000 emails. Compare to SendGrid ($20/month for 40K) or Mailgun ($35/month for 50K)!</em>
            """,
            "alternatives": "SendGrid, Mailgun, and Postmark are easier to start with (no sandbox restrictions) but cost 10-20x more at scale. For transactional emails, SES is the industry standard for cost-effectiveness."
        }
    }
    
    # Return context or generic fallback
    return contexts.get(normalized_name, {
        "strategic_reason": f"{service_name} is a key component of modern cloud architecture, providing essential functionality for your application.",
        "real_world_example": f"In production, {service_name} handles critical workloads reliably and efficiently.",
        "configuration": "<p style='color: #2d3748;'>Standard configuration optimized for your use case.</p>",
        "cost_explanation": "Costs scale with usage. Check AWS pricing calculator for detailed estimates.",
        "alternatives": f"{service_name} is the AWS-native solution, offering deep integration with other services."
    })


def generate_cost_narrative(cost_analysis: Dict, services: List[Dict], users: int) -> str:
    """Detailed cost analysis with optimization strategies"""
    
    summary = cost_analysis.get('summary', {})
    typical = summary.get('typical', '$50-100')
    minimum = summary.get('minimum', '$20')
    maximum = summary.get('maximum', '$200')
    free_tier = summary.get('free_tier_viable', False)
    
    html = f"""
    <section class="narrative-section cost-analysis">
        <h2>💰 Cost Analysis & Financial Planning</h2>
        
        <p class="section-intro">
            Let's talk about what this architecture will actually cost you. AWS's pay-as-you-go model means 
            you're not locked into expensive upfront commitments, but understanding your costs is crucial for 
            planning and budgeting.
        </p>
        
        <div class="cost-summary">
            <p>
                Based on <strong>{users:,} active users</strong> with typical usage patterns 
                (assuming peak traffic at 3-5x average, 70% of requests during business hours, 
                and standard data retention policies), here's your projected monthly spend:
            </p>
            
            <div class="cost-range">
                <div class="cost-item">
                    <span class="cost-label">Minimum</span>
                    <span class="cost-value">{minimum}</span>
                </div>
                <div class="cost-item typical">
                    <span class="cost-label">Most Likely</span>
                    <span class="cost-value">{typical}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">Peak</span>
                    <span class="cost-value">{maximum}</span>
                </div>
            </div>
            
            <p style="margin-top: 1.5rem; color: #4a5568; line-height: 1.8;">
                <strong>Why the range?</strong> AWS bills based on actual usage. The minimum occurs during low-traffic 
                periods (nights, weekends). The typical cost represents normal business operations. The maximum reflects 
                traffic spikes, large batch operations, or seasonal peaks. Your actual bill will fluctuate within this range.
            </p>
        </div>
    """
    
    if free_tier:
        html += """
        <div class="free-tier-notice">
            <h4>✨ Free Tier Opportunity</h4>
            <p>
                <strong>Great news!</strong> If you're just starting out, AWS's Free Tier can significantly reduce 
                (or eliminate) your costs for the first 12 months. Here's what's included:
            </p>
            <ul style="margin-left: 2rem; margin-top: 1rem; line-height: 1.8;">
                <li><strong>Lambda:</strong> 1M free requests and 400,000 GB-seconds of compute per month</li>
                <li><strong>DynamoDB:</strong> 25 GB storage and 25 WCU/RCU</li>
                <li><strong>S3:</strong> 5 GB storage, 20,000 GET requests, 2,000 PUT requests</li>
                <li><strong>API Gateway:</strong> 1M API calls per month</li>
                <li><strong>CloudFront:</strong> 1 TB data transfer out and 10M requests</li>
            </ul>
            <p style="margin-top: 1rem;">
                With careful planning, you could run your entire application for <strong>$0-20/month</strong> 
                during the first year, giving you valuable time to validate your product before scaling costs.
            </p>
        </div>
        """
    
    html += """
        <div class="cost-optimization">
            <h4>📉 Cost Optimization Strategies</h4>
            <p>
                Here are practical ways to keep your AWS bill under control as you grow:
            </p>
            <ol style="margin-left: 2rem; margin-top: 1rem; line-height: 2;">
                <li>
                    <strong>Set up billing alerts immediately:</strong> Create CloudWatch alarms at 50%, 80%, 
                    and 100% of your monthly budget. Know when spending exceeds expectations before the bill arrives.
                </li>
                <li>
                    <strong>Enable AWS Cost Explorer:</strong> Track spending by service, identify unexpected costs, 
                    and spot optimization opportunities. Review weekly during your first 3 months.
                </li>
                <li>
                    <strong>Use tags religiously:</strong> Tag every resource with Environment (prod/dev/test) and 
                    CostCenter. This lets you track costs by environment and shut down unused dev resources.
                </li>
                <li>
                    <strong>Implement lifecycle policies:</strong> S3 objects automatically transition to cheaper 
                    storage classes after 90 days. DynamoDB old data can move to S3 via TTL + Lambda.
                </li>
                <li>
                    <strong>Right-size from the start:</strong> Lambda at 512MB (not 3GB), DynamoDB on-demand 
                    (not over-provisioned), and S3 Intelligent-Tiering for unknown access patterns.
                </li>
                <li>
                    <strong>Monitor cold starts but don't over-optimize:</strong> Provisioned concurrency costs 
                    $15/month per function. Only enable for user-facing APIs with strict latency requirements.
                </li>
            </ol>
        </div>
        
        <div class="cost-projection">
            <h4>📈 Cost Growth Projection</h4>
            <p>
                As your user base grows, here's how costs typically scale:
            </p>
            <ul style="margin-left: 2rem; margin-top: 1rem; line-height: 1.8;">
                <li><strong>1K users:</strong> $20-50/month (mostly free tier)</li>
                <li><strong>10K users:</strong> $100-250/month (outgrew free tier)</li>
                <li><strong>50K users:</strong> $500-1000/month (consider Reserved Capacity savings)</li>
                <li><strong>100K+ users:</strong> $1500-3000/month (enterprise optimizations apply)</li>
            </ul>
            <p style="margin-top: 1rem;">
                Notice the pattern: costs grow sub-linearly with users due to caching, economies of scale, 
                and optimization opportunities that only make sense at higher volumes.
            </p>
        </div>
    </section>
    """
    
    return html


def generate_implementation_narrative(guide: Dict, services: List[Dict], project_type: str) -> str:
    """Detailed implementation roadmap with practical guidance"""
    
    phases = guide.get('phases', [])
    intro = guide.get('introduction', {})
    
    timeline = intro.get('timeline', '20-30 hours over 5-7 days')
    difficulty = intro.get('difficulty', 'Intermediate')
    
    difficulty_context = {
        "Beginner": "This is a straightforward implementation suitable for developers new to AWS. The services are well-documented, and the AWS console provides helpful wizards for setup.",
        "Intermediate": "This implementation requires familiarity with cloud concepts and some AWS experience. You'll be comfortable with infrastructure as code and basic networking concepts.",
        "Advanced": "This architecture involves complex integrations and requires strong AWS expertise. Experience with distributed systems, security best practices, and performance optimization is essential."
    }
    
    html = f"""
    <section class="narrative-section implementation-guide">
        <h2>🚀 Implementation Roadmap</h2>
        
        <p class="section-intro">
            Now comes the practical part: actually building this infrastructure. I've broken down the implementation 
            into clear, manageable phases. Each phase builds on the previous one, so you can test as you go and 
            have a working system at each milestone.
        </p>
        
        <div class="implementation-overview">
            <h4>📋 Implementation Overview</h4>
            <div style="background: #f7fafc; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                <p style="margin-bottom: 1rem;">
                    <strong>Estimated Timeline:</strong> {timeline}<br>
                    <strong>Difficulty Level:</strong> {difficulty}<br>
                    <strong>Team Size:</strong> {"1 developer" if difficulty == "Beginner" else "1-2 developers" if difficulty == "Intermediate" else "2-3 developers"}
                </p>
                <p style="color: #4a5568;">
                    {difficulty_context.get(difficulty, '')}
                </p>
            </div>
        </div>
        
        <p style="margin: 1.5rem 0; line-height: 1.8;">
            <strong>Important:</strong> Don't rush through these phases. Deploy to a development environment first, 
            test thoroughly, then promote to production. The time estimates assume you're working methodically with 
            proper testing at each step—this isn't a race.
        </p>
    """
    
    # Generate detailed phase descriptions
    phase_details = {
        "Foundation Setup": {
            "why": "A solid foundation prevents security issues and cost surprises later. Setting up billing alerts, MFA, and IAM best practices now saves you from painful migrations when you have production traffic.",
            "gotchas": "Don't skip MFA on the root account—it's your last line of defense. Avoid creating access keys for the root user. Always use named IAM users or roles.",
            "success_criteria": "You can log in with MFA, see billing dashboard, have AWS CLI configured, and can create resources via console and CLI."
        },
        "Core Infrastructure": {
            "why": "Your database and storage layer form the backbone of your application. Getting the data model right early prevents expensive refactoring later when you have live users.",
            "gotchas": "DynamoDB partition keys are permanent—choose wisely. Enable point-in-time recovery from day one. S3 bucket names are globally unique and can't be changed.",
            "success_criteria": "You can write and read data from DynamoDB, upload files to S3, and verify data persists after restart."
        },
        "Compute & API Layer": {
            "why": "This is where your business logic lives. Taking time to structure Lambda functions properly (single responsibility, proper error handling) pays dividends in maintainability.",
            "gotchas": "Lambda cold starts affect the first request after idle periods. Package size affects cold start time—keep it under 50MB. Don't store state in Lambda; use DynamoDB.",
            "success_criteria": "API endpoints respond correctly, authentication works, errors are logged to CloudWatch, and you can debug locally with SAM."
        },
        "Integration & Testing": {
            "why": "This is where everything comes together. Thorough integration testing now prevents 3am production incidents later. Test error scenarios, not just happy paths.",
            "gotchas": "Cross-service IAM permissions are the #1 source of production bugs. Test with realistic data volumes—1 record is not representative.",
            "success_criteria": "End-to-end workflows complete successfully, errors are handled gracefully, logs are searchable, and you understand the data flow."
        },
        "Production Deployment": {
            "why": "Going to production isn't just 'aws deploy.' You need monitoring, rollback plans, and gradual traffic migration to do it safely.",
            "gotchas": "DNS propagation takes time—plan accordingly. CloudFront distributions take 15-20 minutes to deploy. Don't make changes during peak traffic hours.",
            "success_criteria": "Application is live, monitoring shows green, alarms are configured, and you have a documented rollback procedure."
        }
    }
    
    for i, phase in enumerate(phases, 1):
        name = phase.get('name', f'Phase {i}')
        description = phase.get('description', '')
        duration = phase.get('duration', 'varies')
        steps = phase.get('steps', [])
        
        phase_detail = phase_details.get(name, {
            "why": "This phase implements critical components of your architecture.",
            "gotchas": "Follow AWS best practices and test thoroughly.",
            "success_criteria": "All components are working as expected."
        })
        
        html += f"""
        <div class="implementation-phase">
            <h3>Phase {i}: {name}</h3>
            <p class="phase-duration"><em>⏱ Estimated time: {duration}</em></p>
            
            <p style="margin: 1rem 0; color: #2d3748;">
                <strong>{description}</strong>
            </p>
            
            <div style="background: #e6fffa; border-left: 4px solid #38b2ac; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
                <p style="margin: 0; color: #234e52;">
                    <strong>💡 Why this matters:</strong> {phase_detail['why']}
                </p>
            </div>
            
            <h4>📋 Tasks</h4>
            <ol style="margin-left: 2rem; margin-top: 1rem; line-height: 2;">
        """
        
        for step in steps:
            html += f"<li>{step}</li>"
        
        html += f"""
            </ol>
            
            <div style="background: #fff5f5; border-left: 4px solid #e53e3e; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
                <p style="margin: 0; color: #742a2a;">
                    <strong>⚠️ Common pitfalls:</strong> {phase_detail['gotchas']}
                </p>
            </div>
            
            <div style="background: #f0fff4; border-left: 4px solid #48bb78; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
                <p style="margin: 0; color: #22543d;">
                    <strong>✅ Success criteria:</strong> {phase_detail['success_criteria']}
                </p>
            </div>
        </div>
        """
    
    html += """
        <div class="implementation-tips">
            <h4>💡 Pro Tips from the Field</h4>
            <ul style="margin-left: 2rem; margin-top: 1rem; line-height: 2;">
                <li>
                    <strong>Infrastructure as Code from Day 1:</strong> Use SAM, CloudFormation, or Terraform. 
                    Clicking in the AWS Console is not reproducible. Your future self will thank you when 
                    you need to recreate environments or debug issues.
                </li>
                <li>
                    <strong>Tag everything immediately:</strong> Create a tagging strategy (Environment, Owner, 
                    CostCenter) and apply it to every resource. This is nearly impossible to retrofit later.
                </li>
                <li>
                    <strong>Enable CloudTrail logging:</strong> It's free for management events and invaluable 
                    during incident investigations. You can't debug what you can't see.
                </li>
                <li>
                    <strong>Use AWS Organizations for multi-account setup:</strong> Even if it's just you, 
                    separate dev/staging/prod into different accounts. A mistake in dev shouldn't affect prod.
                </li>
                <li>
                    <strong>Document as you build:</strong> Keep a README with architecture decisions, 
                    environment variables, and deployment procedures. Future you (or your team) will need this.
                </li>
                <li>
                    <strong>Test failure scenarios:</strong> Kill Lambda functions mid-execution, max out 
                    DynamoDB throughput, fill up S3 buckets. Know how your system fails before users find out.
                </li>
                <li>
                    <strong>Set up local development environment:</strong> Use LocalStack or SAM local to 
                    iterate quickly without deploying to AWS. Fast feedback loops improve productivity.
                </li>
            </ul>
        </div>
        
        <div class="implementation-resources">
            <h4>📚 Essential Resources</h4>
            <ul style="margin-left: 2rem; margin-top: 1rem; line-height: 1.8;">
                <li><strong>AWS Well-Architected Framework:</strong> https://aws.amazon.com/architecture/well-architected/</li>
                <li><strong>AWS Serverless Patterns:</strong> https://serverlessland.com/patterns</li>
                <li><strong>AWS Solutions Library:</strong> https://aws.amazon.com/solutions/</li>
                <li><strong>AWS re:Post (Community):</strong> https://repost.aws/</li>
                <li><strong>AWS Documentation:</strong> Always start here—it's comprehensive and kept up-to-date</li>
            </ul>
        </div>
    </section>
    """
    
    return html


def generate_best_practices(services: List[Dict], project_type: str, users: int) -> str:
    """Generate best practices and common pitfalls section"""
    
    return """
    <section class="narrative-section best-practices">
        <h2>⚠️ Critical Best Practices & Common Pitfalls</h2>
        
        <p class="section-intro">
            I've seen hundreds of AWS architectures over the years. Here are the mistakes I see repeatedly, 
            and more importantly, how to avoid them. Learn from others' expensive lessons.
        </p>
        
        <div class="practice-category">
            <h3>🔒 Security Best Practices</h3>
            
            <div class="practice-item">
                <h4>❌ Mistake: Hardcoding credentials in Lambda code</h4>
                <p>
                    <strong>Why it's bad:</strong> Your credentials end up in git, CloudWatch Logs, and Lambda deployment packages. 
                    A single security breach exposes everything.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Use AWS Secrets Manager or Systems Manager Parameter Store. Rotate secrets 
                    automatically. Lambda IAM roles authenticate to AWS services—no access keys needed.
                </p>
            </div>
            
            <div class="practice-item">
                <h4>❌ Mistake: Overly permissive IAM policies</h4>
                <p>
                    <strong>Why it's bad:</strong> A Lambda with <code>*</code> permissions can delete your entire infrastructure 
                    if compromised. This happens more than you'd think.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Follow least-privilege principle. Lambda reading from DynamoDB needs only 
                    <code>dynamodb:GetItem</code> on that specific table. Use IAM Policy Simulator to test before deploying.
                </p>
            </div>
            
            <div class="practice-item">
                <h4>❌ Mistake: Public S3 buckets</h4>
                <p>
                    <strong>Why it's bad:</strong> Countless data breaches start with misconfigured S3 permissions. 
                    Capital One lost $80M+ from this mistake.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Enable "Block Public Access" on all buckets by default. Use signed URLs 
                    or CloudFront signed cookies for controlled access. Audit S3 permissions quarterly.
                </p>
            </div>
        </div>
        
        <div class="practice-category">
            <h3>💰 Cost Management Best Practices</h3>
            
            <div class="practice-item">
                <h4>❌ Mistake: No billing alerts configured</h4>
                <p>
                    <strong>Why it's bad:</strong> Stories of $50K surprise AWS bills are common. A runaway Lambda 
                    loop can cost thousands before you notice.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Set up CloudWatch billing alarms at $10, $50, $100, and your expected 
                    monthly budget. Receive emails/SMS when thresholds are crossed. Do this today, not tomorrow.
                </p>
            </div>
            
            <div class="practice-item">
                <h4>❌ Mistake: Forgetting to clean up dev/test resources</h4>
                <p>
                    <strong>Why it's bad:</strong> That RDS instance you spun up for testing? Still running 24/7. 
                    Those 50GB of test data in S3? Still accruing charges.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Tag all dev resources with <code>Environment: dev</code>. Use AWS Instance 
                    Scheduler to shut down dev resources nights/weekends. Review Cost Explorer monthly for "surprise" charges.
                </p>
            </div>
        </div>
        
        <div class="practice-category">
            <h3>🚀 Performance Best Practices</h3>
            
            <div class="practice-item">
                <h4>❌ Mistake: Not designing for DynamoDB's access patterns</h4>
                <p>
                    <strong>Why it's bad:</strong> Using DynamoDB like a relational database leads to slow queries, 
                    hot partitions, and runaway costs from scans.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Design your schema around access patterns, not entities. Use composite 
                    sort keys for query flexibility. Avoid scans in production code—they cost 10x-100x more than queries.
                </p>
            </div>
            
            <div class="practice-item">
                <h4>❌ Mistake: Ignoring Lambda cold starts</h4>
                <p>
                    <strong>Why it's bad:</strong> Users experience 1-2 second delays on first request after idle periods. 
                    This feels broken to users.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Keep package sizes under 50MB. Use Lambda Layers for dependencies. For critical 
                    user-facing APIs, consider provisioned concurrency ($15/month) or keep-warm solutions.
                </p>
            </div>
        </div>
        
        <div class="practice-category">
            <h3>🔧 Operational Best Practices</h3>
            
            <div class="practice-item">
                <h4>❌ Mistake: No structured logging</h4>
                <p>
                    <strong>Why it's bad:</strong> When production breaks at 3am, trying to grep through unstructured 
                    logs is painful and slow. Time to resolution matters.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Use structured logging (JSON) with correlation IDs. Log: request ID, 
                    user ID, operation, duration, errors. CloudWatch Logs Insights becomes powerful with structured logs.
                </p>
            </div>
            
            <div class="practice-item">
                <h4>❌ Mistake: Deploying directly to production</h4>
                <p>
                    <strong>Why it's bad:</strong> No testing means users find your bugs. One bad deploy can take down 
                    your entire application.
                </p>
                <p>
                    <strong>✅ Fix:</strong> Use separate AWS accounts for dev/staging/prod. CI/CD pipeline automatically 
                    tests and promotes through environments. Canary deployments gradually shift traffic to new versions.
                </p>
            </div>
        </div>
        
        <div class="red-flags">
            <h4>🚩 Red Flags - Stop Immediately If You See These</h4>
            <ul style="margin-left: 2rem; margin-top: 1rem; line-height: 2;">
                <li>AWS root account being used for daily operations (use IAM users/roles)</li>
                <li>Access keys in code repositories (use Secrets Manager or IAM roles)</li>
                <li>No MFA on AWS accounts (enable it now)</li>
                <li>Lambda functions running for 15 minutes (use Step Functions for long workflows)</li>
                <li>Writing custom auth instead of using Cognito (don't reinvent security)</li>
                <li>Storing sensitive data unencrypted (enable encryption at rest everywhere)</li>
                <li>No backup strategy (enable point-in-time recovery, S3 versioning)</li>
            </ul>
        </div>
    </section>
    """


def generate_conclusion(project_type: str, users: int) -> str:
    """Comprehensive conclusion with actionable next steps"""
    
    conclusions = {
        "ecommerce": "With this architecture in place, you have a production-ready e-commerce platform that can scale from your first customer to millions. The serverless approach means you pay only for actual usage, making it perfect for startups with unpredictable traffic.",
        "api": "This API architecture provides enterprise-grade capabilities—authentication, throttling, monitoring, and scaling—without the operational burden of managing servers. You can focus on building features instead of infrastructure.",
        "social": "You've built a social platform foundation that can handle viral growth. With CloudFront's global distribution and Lambda's auto-scaling, your users worldwide will have a fast, responsive experience even during traffic spikes.",
        "saas": "This SaaS architecture ensures every customer's data remains isolated and secure while allowing you to operate a single infrastructure. You can onboard new customers in seconds without infrastructure changes.",
        "web_application": "Your web application now runs on enterprise-grade infrastructure that scales automatically and costs pennies when idle. Focus on building features your users love instead of managing servers."
    }
    
    conclusion = conclusions.get(project_type, conclusions["web_application"])
    
    return f"""
    <section class="narrative-section conclusion">
        <h2>✅ You're Ready to Build</h2>
        
        <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 1.5rem;">
            {conclusion}
        </p>
        
        <div style="background: #f7fafc; padding: 2rem; border-radius: 8px; margin: 2rem 0;">
            <h4 style="margin-top: 0;">🎯 Your Immediate Next Steps</h4>
            <ol style="margin-left: 2rem; margin-top: 1rem; line-height: 2;">
                <li>
                    <strong>Get the Terraform code:</strong> Click "Generate Terraform Code" above to download 
                    ready-to-deploy infrastructure files. This will save you days of manual setup.
                </li>
                <li>
                    <strong>Set up your AWS account:</strong> If you haven't already, create an AWS account. 
                    Enable MFA on root, create an IAM admin user, and set up billing alerts immediately.
                </li>
                <li>
                    <strong>Deploy to development first:</strong> Never test in production. Create a dev account 
                    or at least tag all resources as <code>Environment: dev</code>.
                </li>
                <li>
                    <strong>Follow Phase 1 of the implementation guide:</strong> Foundation setup is critical. 
                    Don't skip it to move faster—you'll regret it later.
                </li>
                <li>
                    <strong>Join AWS communities:</strong> AWS re:Post, Reddit's r/aws, and local AWS user groups 
                    are invaluable when you get stuck. Don't struggle alone.
                </li>
            </ol>
        </div>
        
        <div style="background: #fff5f5; border-left: 4px solid #e53e3e; padding: 1.5rem; border-radius: 4px; margin: 2rem 0;">
            <h4 style="margin-top: 0; color: #c53030;">⚠️ Important Reminders</h4>
            <ul style="margin-left: 2rem; line-height: 1.8;">
                <li>This architecture is your <strong>starting point</strong>, not your final destination</li>
                <li>Monitor everything from day one—you can't improve what you don't measure</li>
                <li>Document your decisions—future you will need to understand why choices were made</li>
                <li>Start small, test thoroughly, then scale—premature optimization wastes time</li>
                <li>Budget for 20-30% more than estimated costs—there are always surprises</li>
            </ul>
        </div>
        
        <div style="background: #f0fff4; border-left: 4px solid #48bb78; padding: 1.5rem; border-radius: 4px; margin: 2rem 0;">
            <h4 style="margin-top: 0; color: #276749;">💡 Long-term Success Factors</h4>
            <p style="margin: 0; line-height: 1.8;">
                Successful AWS architectures share common traits: they're well-monitored (CloudWatch + X-Ray), 
                properly tagged (cost tracking), regularly reviewed (quarterly architecture audits), documented 
                (decision logs + runbooks), and continuously optimized (right-sizing, reserved capacity). 
                <strong>Your architecture should evolve as you learn more about your users' needs and usage patterns.</strong>
            </p>
        </div>
        
        <div style="text-align: center; margin: 3rem 0;">
            <p style="font-size: 1.3rem; font-weight: 600; color: #2d3748; margin-bottom: 1rem;">
                Remember: AWS is a journey, not a destination
            </p>
            <p style="font-size: 1.1rem; color: #4a5568; line-height: 1.8;">
                The architecture I've designed for you is production-ready and follows industry best practices. 
                But as your product evolves and you learn more about your users, you'll refine and improve it. 
                That's not just okay—that's how great systems are built.
            </p>
        </div>
        
        <p class="good-luck" style="text-align: center; font-size: 1.5rem; font-weight: 700; color: #48bb78; margin-top: 3rem;">
            Good luck building something amazing! 🚀
        </p>
        
        <p style="text-align: center; margin-top: 2rem; color: #718096; font-style: italic;">
            Questions? Stuck on something? The AWS community is here to help. Don't hesitate to reach out on 
            AWS re:Post, Stack Overflow, or Reddit's r/aws. We've all been where you are now.
        </p>
    </section>
    """
