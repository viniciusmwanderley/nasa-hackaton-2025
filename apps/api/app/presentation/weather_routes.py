# ABOUTME: Weather analysis API routes with comprehensive error handling and logging
# ABOUTME: Provides RESTful endpoints for weather risk assessment and analysis

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import ValidationError
import httpx
from ..domain.entities import WeatherAnalysisRequest, WeatherAnalysisResult
from ..domain.interfaces import IWeatherAnalysisService
from .dependencies import get_container
from .models import APIResponse, ValidationException, ExternalServiceException


logger = logging.getLogger("outdoor_risk_api.weather_routes")
router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_service() -> IWeatherAnalysisService:
    """Dependency for weather analysis service."""
    container = get_container()
    return container.weather_service


@router.post("/analyze", response_model=WeatherAnalysisResult)
async def analyze_weather_range(
    request: WeatherAnalysisRequest,
    weather_service: IWeatherAnalysisService = Depends(get_weather_service),
    http_request: Request = None
) -> WeatherAnalysisResult:
    """
    Analyze weather conditions and risk factors for a date range around a center date.
    
    This endpoint provides comprehensive weather analysis including:
    - Historical weather data and statistics
    - Weather predictions using temporal regression
    - Risk classifications (heat, precipitation, wind, snow)
    - Percentile-based risk assessments
    
    Args:
        request: Weather analysis request parameters
        weather_service: Injected weather analysis service
        http_request: FastAPI request object for logging
        
    Returns:
        Complete weather analysis results with risk assessments
        
    Raises:
        HTTPException: For validation errors (400) or service errors (502)
    """
    request_id = getattr(http_request.state, 'request_id', 'unknown') if http_request else 'unknown'
    
    logger.info(
        "Weather analysis request received",
        extra={
            "request_id": request_id,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "center_datetime": request.center_datetime.isoformat(),
            "granularity": request.granularity.value
        }
    )
    
    try:
        result = await weather_service.analyze_weather_range(request)
        
        logger.info(
            "Weather analysis completed successfully",
            extra={
                "request_id": request_id,
                "results_count": len(result.results),
                "parameters_analyzed": len(result.results[0].parameters) if result.results else 0
            }
        )
        
        return result
        
    except ValueError as e:
        logger.error(
            "Validation error in weather analysis",
            extra={"request_id": request_id, "error": str(e)}
        )
        raise ValidationException(f"Invalid request parameters: {str(e)}")
        
    except httpx.HTTPError as e:
        logger.error(
            "External service error in weather analysis",
            extra={"request_id": request_id, "error": str(e)}
        )
        raise ExternalServiceException(f"External service error: {str(e)}")
        
    except Exception as e:
        logger.error(
            "Unexpected error in weather analysis",
            extra={"request_id": request_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def weather_health() -> Dict[str, Any]:
    """
    Health check endpoint for weather service.
    
    Returns:
        Service status and metadata
    """
    return {
        "service": "weather_analysis",
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/parameters")
async def get_available_parameters() -> Dict[str, Any]:
    """
    Get list of available weather parameters and their descriptions.
    
    Returns:
        Dictionary of available weather parameters with descriptions
    """
    from ..infrastructure.config import DEFAULT_PARAMS, CLIMATOLOGY_PARAMS, HOURLY_UNAVAILABLE_PARAMS
    
    parameter_descriptions = {
        "T2M": "Temperature at 2 Meters (°C)",
        "T2M_MAX": "Maximum Temperature at 2 Meters (°C) - Daily only",
        "T2M_MIN": "Minimum Temperature at 2 Meters (°C) - Daily only", 
        "PRECTOTCORR": "Precipitation Corrected (mm/day or mm/hour)",
        "IMERG_PRECTOT": "IMERG Precipitation Total (mm/day) - Daily only",
        "RH2M": "Relative Humidity at 2 Meters (%)",
        "WS10M": "Wind Speed at 10 Meters (m/s)",
        "CLOUD_AMT": "Cloud Amount (%) - Daily only",
        "FRSNO": "Snow Fraction (%)",
        "ALLSKY_SFC_SW_DWN": "All Sky Surface Shortwave Downward Irradiance (kW-hr/m²/day)"
    }
    
    return {
        "default_parameters": DEFAULT_PARAMS,
        "climatology_parameters": CLIMATOLOGY_PARAMS,
        "hourly_unavailable": list(HOURLY_UNAVAILABLE_PARAMS),
        "parameter_descriptions": parameter_descriptions,
        "granularity_options": ["daily", "hourly"]
    }