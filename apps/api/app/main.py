# ABOUTME: Main FastAPI application with health endpoint and request ID middleware
# ABOUTME: Provides basic API structure with JSON logging and request tracking

import uuid
import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to inject X-Request-ID header if missing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state for logging
        request.state.request_id = request_id
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request details
        logger = logging.getLogger("outdoor_risk_api")
        logger.info(
            "Request processed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
            }
        )
        
        return response


def setup_logging():
    """Configure JSON structured logging."""
    # Create custom formatter
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logHandler.setFormatter(formatter)
    
    # Configure logger
    logger = logging.getLogger("outdoor_risk_api")
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    # Configure uvicorn logger to use JSON format
    uvicorn_logger = logging.getLogger("uvicorn.access")
    if uvicorn_logger.handlers:
        uvicorn_logger.handlers[0].setFormatter(formatter)


# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Outdoor Risk API",
    version="0.1.0",
    description="NASA Hackathon 2025 - Estimate odds of adverse weather conditions"
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": app.version
    }


def run_dev_server():
    """Entry point for development server using uv."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )