"""
Kita.dev Metrics Middleware
Prometheus metrics for monitoring
"""
import os
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Only import prometheus if metrics are enabled
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

if ENABLE_METRICS:
    try:
        from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
        PROMETHEUS_AVAILABLE = True
    except ImportError:
        PROMETHEUS_AVAILABLE = False
else:
    PROMETHEUS_AVAILABLE = False

# Metrics definitions (only if prometheus is available)
if PROMETHEUS_AVAILABLE:
    # Request metrics
    REQUEST_COUNT = Counter(
        "kita_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"]
    )
    
    REQUEST_LATENCY = Histogram(
        "kita_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    )
    
    # Task metrics
    TASK_COUNT = Counter(
        "kita_tasks_total",
        "Total tasks processed",
        ["status"]
    )
    
    TASK_DURATION = Histogram(
        "kita_task_duration_seconds",
        "Task processing duration",
        ["final_state"],
        buckets=[1, 5, 10, 30, 60, 120, 300, 600]
    )
    
    TOKEN_USAGE = Counter(
        "kita_tokens_total",
        "Total tokens used",
        ["model"]
    )
    
    ACTIVE_TASKS = Gauge(
        "kita_active_tasks",
        "Currently running tasks"
    )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)
        
        start_time = time.time()
        
        # Normalize endpoint for metrics (avoid high cardinality)
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code)
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize path to reduce cardinality."""
        # Replace UUIDs with placeholder
        import re
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{id}',
            path
        )
        return path


def get_metrics_response() -> Response:
    """Generate Prometheus metrics response."""
    if not PROMETHEUS_AVAILABLE:
        return Response(content="Metrics not available", status_code=503)
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions for task metrics
def record_task_started():
    """Record that a task has started."""
    if PROMETHEUS_AVAILABLE:
        ACTIVE_TASKS.inc()
        TASK_COUNT.labels(status="started").inc()


def record_task_completed(final_state: str, duration_seconds: float):
    """Record task completion."""
    if PROMETHEUS_AVAILABLE:
        ACTIVE_TASKS.dec()
        TASK_COUNT.labels(status=final_state).inc()
        TASK_DURATION.labels(final_state=final_state).observe(duration_seconds)


def record_token_usage(model: str, tokens: int):
    """Record token usage."""
    if PROMETHEUS_AVAILABLE:
        TOKEN_USAGE.labels(model=model).inc(tokens)
