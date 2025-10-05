# ABOUTME: Climate energy analysis API routes with comprehensive error handling
# ABOUTME: Provides RESTful endpoints for renewable energy potential assessment

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
import httpx
from ..domain.climate_entities import (
    ClimateEnergyAnalysisRequest, 
    ClimateEnergyAnalysisResult,
    SingleLocationRequest,
    LocationResult
)
from ..domain.climate_interfaces import IClimateEnergyService
from .dependencies import get_climate_container
from .models import ValidationException, ExternalServiceException


logger = logging.getLogger("outdoor_risk_api.climate_routes")
router = APIRouter(prefix="/climate-energy", tags=["climate-energy"])


def get_climate_service() -> IClimateEnergyService:
    container = get_climate_container()
    return container.climate_service


@router.post("/analyze", response_model=LocationResult)
async def analyze_single_location(
    request: SingleLocationRequest,
    climate_service: IClimateEnergyService = Depends(get_climate_service),
    http_request: Request = None
) -> LocationResult:
    """
    Args:
        request: Single location request with latitude and longitude
        climate_service: Injected climate energy analysis service
        http_request: FastAPI request object for logging
        
    Returns:
        Complete climate energy analysis result for the location
        
    Raises:
        HTTPException: For validation errors (400) or service errors (502)
    """
    request_id = getattr(http_request.state, 'request_id', 'unknown') if http_request else 'unknown'
    
    logger.info(
        "Single location climate energy analysis request received",
        extra={
            "request_id": request_id,
            "latitude": request.latitude,
            "longitude": request.longitude
        }
    )
    
    try:
        result = await climate_service.analyze_single_location(
            request.latitude, 
            request.longitude
        )
        
        logger.info(
            "Single location climate energy analysis completed successfully",
            extra={
                "request_id": request_id,
                "latitude": request.latitude,
                "longitude": request.longitude
            }
        )
        
        return result
        
    except ValueError as e:
        logger.error(
            "Validation error in climate energy analysis",
            extra={"request_id": request_id, "error": str(e)}
        )
        raise ValidationException(f"Invalid request parameters: {str(e)}")
        
    except httpx.HTTPError as e:
        logger.error(
            "External service error in climate energy analysis",
            extra={"request_id": request_id, "error": str(e)}
        )
        raise ExternalServiceException(f"NASA API error: {str(e)}")
        
    except Exception as e:
        logger.error(
            "Unexpected error in climate energy analysis",
            extra={"request_id": request_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def climate_health() -> Dict[str, Any]:
    """
    Health check endpoint for climate energy service.
    
    Returns:
        Service status and metadata
    """
    return {
        "service": "climate_energy_analysis",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/parameters")
async def get_climate_parameters() -> Dict[str, Any]:
    """
    Get information about climate energy analysis parameters and calculations.
    
    Returns:
        Dictionary with parameter descriptions and calculation details
    """
    from ..application.climate_energy_service import ClimateEnergyService
    
    return {
        "nasa_parameters": {
            "SI_TILTED_AVG_OPTIMAL": "Solar Irradiance on Tilted Surface at Optimal Angle (kWh/m²/day)",
            "SI_TILTED_AVG_OPTIMAL_ANG": "Optimal Tilt Angle for Solar Panels (degrees)",
            "RHOA": "Air Density at Surface (kg/m³)",
            "WS50M": "Wind Speed at 50 Meters (m/s)",
            "WD50M": "Wind Direction at 50 Meters (degrees)"
        },
        "calculation_parameters": {
            "solar_loss_factor": ClimateEnergyService.SOLAR_LOSS_FACTOR,
            "turbine_swept_area_m2": ClimateEnergyService.TURBINE_SWEPT_AREA_M2,
            "turbine_power_coefficient": ClimateEnergyService.TURBINE_CP
        },
        "data_source": {
            "api": "NASA POWER",
            "community": "Renewable Energy",
            "temporal_coverage": "2010-2024",
            "spatial_resolution": "0.5° x 0.625°"
        },
        "output_metrics": {
            "solar_kwh_per_m2": "Solar energy density by month (kWh/m²/month)",
            "wind_kwh_per_m2": "Wind energy density by month (kWh/m²/month)",
            "ANN": "Annual total energy density (kWh/m²/year)"
        }
    }


@router.get("/analyze/{latitude}/{longitude}", response_model=LocationResult)
async def analyze_location_by_coordinates(
    latitude: float,
    longitude: float,
    climate_service: IClimateEnergyService = Depends(get_climate_service),
    http_request: Request = None
) -> LocationResult:
    """    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
        climate_service: Injected climate energy analysis service
        http_request: FastAPI request object for logging
        
    Returns:
        Climate energy analysis result for the location
    """
    if not (-90 <= latitude <= 90):
        raise ValidationException("Latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise ValidationException("Longitude must be between -180 and 180")
    
    request = SingleLocationRequest(latitude=latitude, longitude=longitude)
    
    return await analyze_single_location(request, climate_service, http_request)