import time
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # Stores client_key -> list of timestamps
        self.history: Dict[str, List[float]] = {}

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        # Filter timestamps outside the window
        cutoff = now - self.window_seconds
        timestamps = self.history.get(key, [])
        timestamps = [t for t in timestamps if t > cutoff]
        self.history[key] = timestamps

        if len(timestamps) >= self.requests_limit:
            return True

        self.history[key].append(now)
        return False

# Limiters configuration
login_limiter = RateLimiter(requests_limit=10, window_seconds=60)
ai_limiter = RateLimiter(requests_limit=5, window_seconds=60)
request_limiter = RateLimiter(requests_limit=10, window_seconds=60)
event_limiter = RateLimiter(requests_limit=15, window_seconds=60)

def rate_limit_login(request: Request):
    key = request.client.host
    if login_limiter.is_rate_limited(key):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again in a minute.")

def rate_limit_ai(request: Request):
    # Try to key by user id if authenticated, fallback to IP
    key = request.client.host
    if hasattr(request.state, "user") and request.state.user:
        key = f"user_{request.state.user.id}"
    
    if ai_limiter.is_rate_limited(key):
        raise HTTPException(status_code=429, detail="AI query limit exceeded. Limit is 5 requests per minute.")

def rate_limit_requests(request: Request):
    key = request.client.host
    if request_limiter.is_rate_limited(key):
        raise HTTPException(status_code=429, detail="Too many request submissions. Limit is 10 requests per minute.")

def rate_limit_events(request: Request):
    key = request.client.host
    if event_limiter.is_rate_limited(key):
        raise HTTPException(status_code=429, detail="Too many event registration changes. Limit is 15 requests per minute.")
