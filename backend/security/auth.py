from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from collections import defaultdict
import os
import time
import logging

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory storage
rate_limit_storage = defaultdict(list)
request_cache = {}

VALID_API_KEYS = set(os.getenv("VALID_API_KEYS", "demo-key-12345").split(","))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key:
        if os.getenv("ALLOW_ANONYMOUS", "true").lower() == "true":
            logger.warning("Anonymous request allowed")
            return "anonymous"
        raise HTTPException(status_code=401, detail="API key required")
    
    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key: {api_key[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return api_key


def check_rate_limit(api_key: str) -> None:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    requests = [r for r in rate_limit_storage[api_key] if r > window_start]
    rate_limit_storage[api_key] = requests
    
    if len(requests) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again later."
        )
    
    requests.append(now)
    logger.info(f"Rate limit: {len(requests)}/{RATE_LIMIT_REQUESTS}")
