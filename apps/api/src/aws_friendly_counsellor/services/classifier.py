from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any, Dict

logger = logging.getLogger(__name__)

# The classifier is deliberately transparent and deterministic. It is a rules engine,
# not a trained machine-learning model; the API reports that fact in its metadata.
USE_CASE_KEYWORDS = {
    "ecommerce": (
        "ecommerce", "e-commerce", "online store", "shop", "shopping cart",
        "checkout", "product catalog", "orders", "payments",
    ),
    "marketplace": (
        "marketplace", "seller", "buyer", "vendor", "multi-vendor",
        "listings", "commissions",
    ),
    "social": (
        "social network", "social media", "feed", "followers", "likes",
        "comments", "community", "user posts",
    ),
    "saas": (
        "saas", "software as a service", "multi-tenant", "subscription",
        "tenant", "workspace", "organization accounts",
    ),
    "blog": (
        "blog", "publishing site", "articles", "editorial site", "news site",
        "content management",
    ),
    "mobile_backend": (
        "mobile app", "ios", "android", "push notification", "mobile backend",
        "app store",
    ),
    "api": (
        "api", "rest", "graphql", "webhook", "endpoint", "backend service",
        "microservice",
    ),
    "real_time": (
        "real-time", "realtime", "websocket", "live chat", "messaging",
        "collaboration", "live updates",
    ),
    "analytics": (
        "analytics", "dashboard", "business intelligence", "reporting",
        "metrics", "event tracking", "data pipeline",
    ),
    "file_storage": (
        "file storage", "file upload", "document storage", "photo upload",
        "image upload", "video upload", "media library",
    ),
    "web_application": (
        "web application", "web app", "website", "portal", "browser-based",
        "customer portal", "admin portal",
    ),
}

FEATURE_KEYWORDS = {
    "authentication": (
        "authentication", "login", "sign up", "signup", "oauth", "sso",
        "multi-factor", "mfa", "user accounts",
    ),
    "email": (
        "email", "newsletter", "transactional messages", "mail notification",
    ),
    "file_storage": USE_CASE_KEYWORDS["file_storage"],
    "real_time": USE_CASE_KEYWORDS["real_time"],
    "analytics": USE_CASE_KEYWORDS["analytics"],
}

CATEGORY_PRIORITY = (
    "ecommerce", "marketplace", "saas", "social", "mobile_backend", "real_time",
    "analytics", "api", "blog", "file_storage", "web_application",
)


def _phrase_present(text: str, phrase: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify_use_case(description: str) -> Dict[str, Any]:
    normalized = " ".join(description.lower().split())
    scores: dict[str, int] = defaultdict(int)
    matches: dict[str, list[str]] = defaultdict(list)

    for category, keywords in USE_CASE_KEYWORDS.items():
        for keyword in keywords:
            if _phrase_present(normalized, keyword):
                weight = 3 if " " in keyword or "-" in keyword else 1
                scores[category] += weight
                matches[category].append(keyword)

    if not scores:
        primary = "web_application"
        confidence = 0.45
    else:
        ranked = sorted(
            scores,
            key=lambda category: (scores[category], -CATEGORY_PRIORITY.index(category)),
            reverse=True,
        )
        primary = ranked[0]
        top_score = scores[primary]
        second_score = scores[ranked[1]] if len(ranked) > 1 else 0
        separation = max(0, top_score - second_score)
        confidence = min(0.55 + (top_score * 0.07) + (separation * 0.04), 0.96)

    feature_scores: dict[str, int] = defaultdict(int)
    for feature, keywords in FEATURE_KEYWORDS.items():
        for keyword in keywords:
            if _phrase_present(normalized, keyword):
                feature_scores[feature] += 1

    ranked_categories = sorted(scores, key=scores.get, reverse=True)
    features = [primary]
    features.extend(category for category in ranked_categories if category != primary and scores[category] >= 2)
    features.extend(feature for feature in feature_scores if feature not in features)
    features = features[:6]

    logger.info("Classification completed: primary=%s confidence=%.2f", primary, confidence)
    return {
        "primary": primary,
        "confidence": round(confidence, 2),
        "features": features,
        "matched_keywords": matches.get(primary, []),
        "classifier": "deterministic_rules_v1",
    }
