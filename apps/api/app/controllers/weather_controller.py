# ABOUTME: Weather analysis API endpoint controllers with request handling and validation
# ABOUTME: Provides FastAPI route handlers for weather analysis and classification endpoints

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

from ..models.weather import (
    WeatherAnalysisRequest, 
    WeatherAnalysisResponse, 
    ErrorResponse,
    ParameterAnalysis,
    ParameterStats,
    WeatherMetadata
)
from ..services.weather_service import WeatherDataService
from ..services.classification_service import WeatherClassificationService


router = APIRouter(prefix="/weather", tags=["Weather Analysis"])
logger = logging.getLogger("outdoor_risk_api")


def get_weather_service() -> WeatherDataService:
    """Dependency to get weather service instance."""
    return WeatherDataService()


def get_classification_service() -> WeatherClassificationService:
    """Dependency to get classification service instance."""
    return WeatherClassificationService()


@router.post("/analyze", response_model=WeatherAnalysisResponse)
async def analyze_weather(
    request_data: WeatherAnalysisRequest,
    request: Request,
    weather_service: WeatherDataService = Depends(get_weather_service),
    classification_service: WeatherClassificationService = Depends(get_classification_service)
):
    """
    Analyze weather conditions for a specific location and time.
    
    This endpoint performs comprehensive weather analysis including:
    - Historical data retrieval from NASA POWER API
    - Statistical analysis and climatology comparison
    - Weather condition classification with probabilities
    - Risk assessment for outdoor activities
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    try:
        logger.info(
            "Starting weather analysis",
            extra={
                "request_id": request_id,
                "latitude": request_data.latitude,
                "longitude": request_data.longitude,
                "target_datetime": request_data.target_datetime.isoformat(),
                "granularity": request_data.granularity.value
            }
        )
        
        # Perform weather analysis
        analysis_result = weather_service.analyze_weather(
            lat=request_data.latitude,
            lon=request_data.longitude,
            target_dt=request_data.target_datetime,
            granularity=request_data.granularity,
            parameters=request_data.parameters,
            start_year=request_data.start_year,
            window_days=request_data.window_days
        )
        
        # Perform weather condition classification
        classifications = classification_service.classify_weather_conditions(analysis_result)
        
        # Convert analysis result to response model
        parameter_analyses = {}
        for param_name, param_data in analysis_result["parameters"].items():
            stats = None
            if param_data.get("stats"):
                stats = ParameterStats(**param_data["stats"])
            
            parameter_analyses[param_name] = ParameterAnalysis(
                mode=param_data["mode"],
                climatology_month_mean=param_data.get("climatology_month_mean"),
                observed_value=param_data.get("observed_value"),
                stats=stats,
                sample_size=param_data.get("sample_size")
            )
        
        # Create response
        response = WeatherAnalysisResponse(
            meta=WeatherMetadata(**analysis_result["meta"]),
            derived_insights=analysis_result["derived_insights"],
            parameters=parameter_analyses,
            classifications=classifications,
            request_id=request_id
        )
        
        logger.info(
            "Weather analysis completed successfully",
            extra={
                "request_id": request_id,
                "analysis_mode": analysis_result["meta"]["analysis_mode"],
                "parameter_count": len(parameter_analyses),
                "classification_count": len(classifications)
            }
        )
        
        return response
        
    except Exception as e:
        error_msg = f"Weather analysis failed: {str(e)}"
        logger.error(
            error_msg,
            extra={
                "request_id": request_id,
                "error_type": type(e).__name__,
                "latitude": request_data.latitude,
                "longitude": request_data.longitude
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "WeatherAnalysisError",
                "message": error_msg,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/parameters")
async def get_available_parameters(request: Request) -> Dict[str, Any]:
    """
    Get list of available weather parameters for analysis.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    parameters = {
        "T2M": {
            "name": "Temperature at 2 Meters",
            "unit": "°C",
            "description": "Temperature at 2 meters above ground level"
        },
        "T2M_MAX": {
            "name": "Maximum Temperature at 2 Meters",
            "unit": "°C", 
            "description": "Daily maximum temperature at 2 meters (daily granularity only)"
        },
        "T2M_MIN": {
            "name": "Minimum Temperature at 2 Meters",
            "unit": "°C",
            "description": "Daily minimum temperature at 2 meters (daily granularity only)"
        },
        "PRECTOTCORR": {
            "name": "Precipitation",
            "unit": "mm/day",
            "description": "Precipitation corrected for bias"
        },
        "RH2M": {
            "name": "Relative Humidity at 2 Meters",
            "unit": "%",
            "description": "Relative humidity at 2 meters above ground level"
        },
        "WS10M": {
            "name": "Wind Speed at 10 Meters", 
            "unit": "m/s",
            "description": "Wind speed at 10 meters above ground level"
        }
    }
    
    return {
        "parameters": parameters,
        "default_parameters": WeatherDataService.DEFAULT_PARAMS,
        "request_id": request_id
    }


@router.get("/thresholds")
async def get_classification_thresholds(request: Request) -> Dict[str, Any]:
    """
    Get weather condition classification thresholds.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Convert thresholds to a more readable format
    readable_thresholds = {}
    for condition, config in WeatherClassificationService.THRESHOLDS.items():
        readable_thresholds[condition.value] = {
            "parameter": config["parameter"],
            "threshold_value": config["threshold"],
            "direction": config["direction"],
            "description": config["description"],
            "unit": _get_parameter_unit(config["parameter"])
        }
    
    return {
        "thresholds": readable_thresholds,
        "conditions": [condition.value for condition in WeatherClassificationService.THRESHOLDS.keys()],
        "request_id": request_id
    }


def _get_parameter_unit(parameter: str) -> str:
    """Get unit for a parameter."""
    units = {
        "T2M": "°C",
        "WS10M": "m/s", 
        "PRECTOTCORR": "mm/day",
        "heat_index": "°C"
    }
    return units.get(parameter, "")