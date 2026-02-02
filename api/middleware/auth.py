"""
Kita.dev Security Middleware
Authentication, rate limiting, and CORS
"""

import os
import time
import logging
from typing import Callable, Dict, Optional
from collections import defaultdict

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Configuration from environment
API_KEY = os.getenv("API_KEY", "")  # Empty = disabled
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key authentication middleware.
    Requires X-API-Key header for protected endpoints.
    """

    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = [
        "/health",
        "/api/health",
        "/",
        "/dashboard",
        "/static",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip if API key is not configured
        if not API_KEY:
            return await call_next(request)

        # Skip public endpoints
        path = request.url.path
        if any(path.startswith(ep) for ep in self.PUBLIC_ENDPOINTS):
            return await call_next(request)

        # Check API key
        provided_key = request.headers.get("X-API-Key")

        if not provided_key:
            logger.warning(f"Missing API key for {path}")
            raise HTTPException(status_code=401, detail="API key required")

        if provided_key != API_KEY:
            logger.warning(f"Invalid API key for {path}")
            raise HTTPException(status_code=403, detail="Invalid API key")

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    Limits requests per minute per IP.
    """

    def __init__(self, app, rpm: int = 60):
        super().__init__(app)
        self.rpm = rpm
        self.requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Clean old requests
        current_time = time.time()
        minute_ago = current_time - 60
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.rpm:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )

        # Record request
        self.requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.rpm - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP, handling proxies."""
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"


def get_cors_origins() -> list:
    """Get allowed CORS origins from environment."""
    origins = os.getenv("CORS_ORIGINS", "")
    if not origins:
        return ["*"]
    return [o.strip() for o in origins.split(",") if o.strip()]


# Security headers to add to all responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response
