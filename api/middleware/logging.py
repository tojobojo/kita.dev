"""
Kita.dev Logging Middleware
Structured JSON logging for production
"""
import logging
import json
import time
import os
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging format based on environment
JSON_LOGS = os.getenv("JSON_LOGS", "false").lower() == "true"

class JSONFormatter(logging.Formatter):
    """JSON log formatter for production."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_logging():
    """Configure logging based on environment."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler()
    
    if JSON_LOGS:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))
    
    root_logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(time.time_ns()))
        
        # Log request
        logger = logging.getLogger("api.request")
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={"request_id": request_id, "path": request.url.path}
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"← {request.method} {request.url.path} [{response.status_code}] {duration_ms:.2f}ms",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
