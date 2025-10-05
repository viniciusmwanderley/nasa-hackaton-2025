# ABOUTME: Presentation layer package initialization
# ABOUTME: Exports API routes and dependencies for the FastAPI application

from .weather_routes import router as weather_router
from .climate_routes import router as climate_router
from .dependencies import get_container, get_climate_container
from .models import APIResponse, ErrorResponse, WeatherAnalysisException

__all__ = [
    "weather_router",
    "climate_router",
    "get_container",
    "get_climate_container",
    "APIResponse",
    "ErrorResponse",
    "WeatherAnalysisException",
]