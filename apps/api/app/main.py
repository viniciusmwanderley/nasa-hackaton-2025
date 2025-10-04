# ABOUTME: Main FastAPI application with health endpoint and request ID middleware
# ABOUTME: Provides complete outdoor risk assessment API with weather analysis and classification

import uuid
import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger

from .controllers.weather_controller import router as weather_router
from .models.weather import HealthResponse
from fastapi.responses import JSONResponse
from datetime import datetime


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
    description="NASA Hackathon 2025 - Estimate odds of adverse weather conditions for outdoor activities",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Include routers
app.include_router(weather_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all routes."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger = logging.getLogger("outdoor_risk_api")
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "path": request.url.path
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing your request",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.get("/health", response_model=HealthResponse)
def health(request: Request):
    """Health check endpoint."""
    request_id = getattr(request.state, 'request_id', None)
    return HealthResponse(
        status="ok",
        version=app.version,
        request_id=request_id
    )


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