# ABOUTME: Main FastAPI application with weather analysis endpoints and middleware
# ABOUTME: Provides complete weather risk assessment API with clean architecture

import uuid
import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger
from .presentation import weather_router, WeatherAnalysisException


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
    version="1.0.0",
    description="NASA Hackathon 2025 - Weather Risk Assessment API using NASA POWER data for outdoor activity planning",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Include weather analysis routes
app.include_router(weather_router)


# Global exception handler for weather analysis exceptions
@app.exception_handler(WeatherAnalysisException)
async def weather_analysis_exception_handler(request: Request, exc: WeatherAnalysisException):
    """Handle weather analysis specific exceptions."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger = logging.getLogger("outdoor_risk_api")
    logger.error(
        "Weather analysis exception",
        extra={
            "request_id": request_id,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "request_id": request_id
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger = logging.getLogger("outdoor_risk_api")
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "path": request.url.path
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "request_id": request_id
        }
    )


@app.get("/health")
def health():
    """Health check endpoint for the main application."""
    return {
        "status": "ok",
        "service": "outdoor_risk_api",
        "version": app.version,
        "description": "Weather Risk Assessment API"
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