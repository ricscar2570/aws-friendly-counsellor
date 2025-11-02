from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

USE_CASE_KEYWORDS = {
    "web_application": ["web", "website", "blog", "cms", "portal"],
    "ecommerce": ["ecommerce", "store", "shop", "product", "cart", "checkout", "payment"],
    "marketplace": ["marketplace", "platform", "seller", "buyer", "vendor"],
    "social": ["social", "feed", "post", "follower", "like", "comment", "share"],
    "mobile_backend": ["mobile", "app", "ios", "android", "push notification"],
    "api": ["api", "endpoint", "rest", "graphql", "webhook"],
    "real_time": ["real-time", "realtime", "chat", "messaging", "live", "websocket"],
    "file_storage": ["file", "upload", "photo", "image", "video", "document", "storage"],
    "authentication": ["auth", "login", "signup", "user", "password", "oauth", "sso"],
    "analytics": ["analytics", "tracking", "metrics", "dashboard", "reporting"],
}

def classify_use_case(description: str) -> Dict[str, Any]:
    logger.info(f"Classifying: {description[:100]}...")
    
    description_lower = description.lower()
    scores = {}
    
    for category, keywords in USE_CASE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in description_lower)
        if score > 0:
            scores[category] = score
    
    if not scores:
        return {
            "primary": "web_application",
            "confidence": 0.5,
            "features": ["web_application"]
        }
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_scores[0][0]
    max_score = sorted_scores[0][1]
    
    confidence = min(max_score / 5.0, 1.0)
    if len(sorted_scores) > 1 and sorted_scores[1][1] >= max_score * 0.7:
        confidence *= 0.9
    
    features = [cat for cat, _ in sorted_scores[:4]]
    
    logger.info(f"Classification: {primary} (confidence: {confidence:.2f})")
    
    return {
        "primary": primary,
        "confidence": confidence,
        "features": features
    }
