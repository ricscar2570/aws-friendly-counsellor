from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Servizi con spiegazioni CONTESTUALI per ogni tipo di progetto
SERVICE_CATALOG = {
    "ecommerce": {
        "cognito": {
            "name": "Amazon Cognito",
            "category": "authentication",
            "why": "Manages customer accounts, login/signup, and secure authentication for shoppers",
            "use_case": "Customer registration, login, password reset, and session management"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores products, orders, shopping carts, and customer data with millisecond response times",
            "use_case": "Product catalog with search, order history, real-time inventory tracking"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Handles checkout logic, payment processing, order confirmation, and inventory updates",
            "use_case": "Process payments with Stripe/PayPal, calculate shipping, apply discounts"
        },
        "api-gateway": {
            "name": "Amazon API Gateway",
            "category": "api",
            "why": "Provides secure REST APIs for product browsing, cart operations, and checkout",
            "use_case": "API endpoints: /products, /cart, /checkout, /orders"
        },
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Stores product images, promotional banners, and invoices with 99.999999999% durability",
            "use_case": "Product photos, category images, downloadable receipts"
        },
        "ses": {
            "name": "Amazon SES",
            "category": "email",
            "why": "Sends order confirmations, shipping notifications, and promotional emails",
            "use_case": "Transactional emails: order confirmation, shipping updates, password reset"
        },
        "cloudfront": {
            "name": "Amazon CloudFront",
            "category": "cdn",
            "why": "Delivers product images and website assets globally with low latency",
            "use_case": "Fast image loading worldwide, reduced S3 costs"
        }
    },
    
    "social": {
        "cognito": {
            "name": "Amazon Cognito",
            "category": "authentication",
            "why": "Manages user profiles, authentication, and social login (Google, Facebook)",
            "use_case": "User signup/login, profile management, OAuth integration"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores posts, comments, likes, and follower relationships with fast queries",
            "use_case": "User posts with timestamps, comment threads, follower/following lists"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Generates personalized feeds, processes likes/comments, sends notifications",
            "use_case": "Feed algorithm, notification triggers, content moderation"
        },
        "api-gateway": {
            "name": "Amazon API Gateway",
            "category": "api",
            "why": "REST APIs for posting, commenting, liking, and following users",
            "use_case": "Endpoints: /posts, /comments, /likes, /follow"
        },
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Stores user-uploaded photos, videos, and profile pictures",
            "use_case": "Photo uploads, video hosting, profile avatars"
        },
        "cloudfront": {
            "name": "Amazon CloudFront",
            "category": "cdn",
            "why": "Delivers media content globally with low latency for better user experience",
            "use_case": "Fast photo/video loading, reduced bandwidth costs"
        }
    },
    
    "marketplace": {
        "cognito": {
            "name": "Amazon Cognito",
            "category": "authentication",
            "why": "Separate authentication for buyers and sellers with role-based access",
            "use_case": "Buyer/seller accounts, vendor verification, multi-role permissions"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores listings, bids, transactions, and seller profiles",
            "use_case": "Product listings, bidding history, escrow transactions, seller ratings"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Handles bidding logic, payment escrow, commission calculations, and notifications",
            "use_case": "Bid processing, payment splits, seller payouts, dispute resolution"
        },
        "api-gateway": {
            "name": "Amazon API Gateway",
            "category": "api",
            "why": "APIs for listings, bidding, messaging between buyers/sellers",
            "use_case": "Endpoints: /listings, /bids, /messages, /transactions"
        },
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Stores product images, seller documents, and transaction receipts",
            "use_case": "Listing photos, seller verification docs, invoices"
        },
        "ses": {
            "name": "Amazon SES",
            "category": "email",
            "why": "Sends bid notifications, transaction confirmations, and seller alerts",
            "use_case": "Bid updates, sale confirmations, payout notifications"
        }
    },
    
    "blog": {
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Hosts your static blog website (HTML, CSS, JS) with high availability",
            "use_case": "Static site hosting, article pages, images"
        },
        "cloudfront": {
            "name": "Amazon CloudFront",
            "category": "cdn",
            "why": "Delivers your blog globally with fast load times and HTTPS",
            "use_case": "Global content delivery, SSL certificate, DDoS protection"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Handles dynamic features like comments, contact forms, and search",
            "use_case": "Comment processing, email notifications, search indexing"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores comments, page views, and subscriber data",
            "use_case": "Comment storage, analytics tracking, email subscribers"
        }
    },
    
    "saas": {
        "cognito": {
            "name": "Amazon Cognito",
            "category": "authentication",
            "why": "Multi-tenant authentication with organization isolation and SSO support",
            "use_case": "Company accounts, team member access, SSO integration"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores tenant data, subscriptions, usage metrics with tenant isolation",
            "use_case": "Customer data, subscription plans, usage tracking, billing"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Handles business logic, API processing, and background jobs",
            "use_case": "Data processing, scheduled tasks, webhook integrations"
        },
        "api-gateway": {
            "name": "Amazon API Gateway",
            "category": "api",
            "why": "Provides REST/GraphQL APIs with rate limiting and API key management",
            "use_case": "Public API, webhook endpoints, third-party integrations"
        },
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Stores customer files, exports, and backups with encryption",
            "use_case": "File uploads, data exports, automated backups"
        }
    },
    
    "mobile_backend": {
        "cognito": {
            "name": "Amazon Cognito",
            "category": "authentication",
            "why": "Mobile-optimized authentication with social login and biometric support",
            "use_case": "App login, Face ID/fingerprint, Google/Apple sign-in"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores app data with offline sync capabilities via AWS AppSync",
            "use_case": "User preferences, app state, offline-first data"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Backend API logic for mobile app features",
            "use_case": "Data processing, push notification triggers, API logic"
        },
        "api-gateway": {
            "name": "Amazon API Gateway",
            "category": "api",
            "why": "RESTful APIs optimized for mobile with low latency",
            "use_case": "Mobile API endpoints with caching"
        },
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Stores user-generated content like photos and videos from mobile",
            "use_case": "Image uploads, video storage, app assets"
        }
    },
    
    "api": {
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Executes API logic without managing servers, auto-scales with traffic",
            "use_case": "API endpoints, data transformations, integrations"
        },
        "api-gateway": {
            "name": "Amazon API Gateway",
            "category": "api",
            "why": "Manages API versioning, rate limiting, API keys, and documentation",
            "use_case": "REST API with authentication, throttling, monitoring"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Fast NoSQL storage for API data with predictable performance",
            "use_case": "API data storage, caching, session management"
        }
    },
    
    "real_time": {
        "appsync": {
            "name": "AWS AppSync",
            "category": "api",
            "why": "Real-time GraphQL subscriptions for live updates",
            "use_case": "Live chat messages, real-time notifications, collaborative editing"
        },
        "lambda": {
            "name": "AWS Lambda",
            "category": "compute",
            "why": "Processes messages, broadcasts updates, and triggers notifications",
            "use_case": "Message routing, presence detection, notification logic"
        },
        "dynamodb": {
            "name": "Amazon DynamoDB",
            "category": "database",
            "why": "Stores chat history, user presence, and connection states",
            "use_case": "Message persistence, online/offline status, conversation threads"
        }
    }
}

# Servizi di default (fallback)
DEFAULT_SERVICES = {
    "lambda": {
        "name": "AWS Lambda",
        "category": "compute",
        "why": "Runs your application code without managing servers",
        "use_case": "Backend logic, API processing, scheduled tasks"
    },
    "api-gateway": {
        "name": "Amazon API Gateway",
        "category": "api",
        "why": "Creates and manages REST APIs for your application",
        "use_case": "API endpoints with authentication and monitoring"
    },
    "dynamodb": {
        "name": "Amazon DynamoDB",
        "category": "database",
        "why": "Stores your application data with fast, predictable performance",
        "use_case": "User data, application state, content storage"
    },
    "s3": {
        "name": "Amazon S3",
        "category": "storage",
        "why": "Stores files, images, and static assets with high durability",
        "use_case": "File uploads, static website hosting, backups"
    }
}

# Servizi aggiuntivi basati su features
FEATURE_SERVICES = {
    "authentication": {
        "cognito": {
            "name": "Amazon Cognito",
            "category": "authentication",
            "why": "Handles user authentication and authorization securely",
            "use_case": "User signup, login, password management, MFA"
        }
    },
    "email": {
        "ses": {
            "name": "Amazon SES",
            "category": "email",
            "why": "Sends transactional and marketing emails reliably",
            "use_case": "Email notifications, newsletters, alerts"
        }
    },
    "file_storage": {
        "s3": {
            "name": "Amazon S3",
            "category": "storage",
            "why": "Stores user-uploaded files with 99.999999999% durability",
            "use_case": "Document uploads, media storage, backups"
        }
    }
}

def recommend_services(classification: Dict, estimated_users: int) -> List[Dict]:
    """
    Recommend AWS services with contextual explanations
    """
    primary = classification.get("primary", "web_application")
    features = classification.get("features", [])
    
    logger.info(f"Recommending services for: {primary}, users: {estimated_users}")
    
    services = {}
    
    # 1. Aggiungi servizi principali per il tipo di progetto
    if primary in SERVICE_CATALOG:
        services.update(SERVICE_CATALOG[primary])
        logger.info(f"Added {len(SERVICE_CATALOG[primary])} core services for {primary}")
    else:
        # Fallback: servizi di default
        services.update(DEFAULT_SERVICES)
        logger.info(f"Using default services (unknown project type: {primary})")
    
    # 2. Aggiungi servizi basati su features rilevate
    for feature in features:
        if feature != primary and feature in SERVICE_CATALOG:
            # Aggiungi solo servizi non già presenti
            for service_key, service_info in SERVICE_CATALOG[feature].items():
                if service_key not in services:
                    services[service_key] = service_info
                    logger.info(f"Added {service_key} for feature: {feature}")
    
    # 3. Aggiungi CloudFront per applicazioni ad alto traffico
    if estimated_users > 10000 and "cloudfront" not in services:
        services["cloudfront"] = {
            "name": "Amazon CloudFront",
            "category": "cdn",
            "why": f"Essential for {estimated_users:,} users - delivers content globally with low latency",
            "use_case": "Global CDN, caching, DDoS protection"
        }
        logger.info(f"Added CloudFront for high traffic ({estimated_users} users)")
    
    # 4. Converti in lista con informazioni complete
    result = []
    for service_key, service_info in services.items():
        result.append({
            "name": service_info["name"],
            "category": service_info["category"],
            "typical_monthly": get_cost_estimate(service_key, estimated_users),
            "free_tier": get_free_tier(service_key),
            "why_needed": service_info["why"],
            "use_case_example": service_info["use_case"]
        })
    
    logger.info(f"Recommended {len(result)} services total")
    
    return result


def get_cost_estimate(service_key: str, users: int) -> str:
    """Get cost estimate based on service and user count"""
    
    # Costs scale with users
    if users < 1000:
        multiplier = 0.5
    elif users < 10000:
        multiplier = 1.0
    elif users < 100000:
        multiplier = 2.0
    else:
        multiplier = 4.0
    
    base_costs = {
        "lambda": (10, 50),
        "api-gateway": (5, 30),
        "dynamodb": (5, 30),
        "s3": (5, 20),
        "cognito": (0, 25),
        "ses": (0, 10),
        "cloudfront": (10, 50),
        "appsync": (5, 40)
    }
    
    if service_key in base_costs:
        min_cost, max_cost = base_costs[service_key]
        scaled_min = int(min_cost * multiplier)
        scaled_max = int(max_cost * multiplier)
        return f"{scaled_min}-{scaled_max}"
    
    return "5-30"


def get_free_tier(service_key: str) -> str:
    """Get free tier information for service"""
    
    free_tiers = {
        "lambda": "1M requests + 400K GB-seconds",
        "api-gateway": "1M requests (12 months)",
        "dynamodb": "25GB + 25 WCU/RCU",
        "s3": "5GB storage",
        "cognito": "50K MAU",
        "ses": "62K emails/month",
        "cloudfront": "1TB data transfer",
        "appsync": "250K query/mutation"
    }
    
    return free_tiers.get(service_key, "Limited free tier")
