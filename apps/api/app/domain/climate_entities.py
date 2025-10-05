# ABOUTME: Domain entities for climate energy analysis system
# ABOUTME: Contains core business objects for renewable energy potential assessment

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    """Input model for location with coordinates."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class ClimateEnergyPotential(BaseModel):
    """Energy potential metrics for a location."""
    solar_kwh_per_m2: Dict[str, float] = Field(..., description="Solar energy density by month (kWh/m²)")
    wind_kwh_per_m2: Dict[str, float] = Field(..., description="Wind energy density by month (kWh/m²)")


class LocationResult(BaseModel):
    """Analysis result for a single location."""
    location: LocationInput
    climate_energy_potential: ClimateEnergyPotential
    raw_nasa_metrics_monthly: Dict[str, Dict[str, float]]


class AnalysisMeta(BaseModel):
    """Metadata for the analysis process."""
    timestamp_utc: str
    processing_time_seconds: float
    locations_processed: int
    locations_failed: int


class LocationError(BaseModel):
    """Error information for failed location processing."""
    location: LocationInput
    error: str


class ClimateEnergyAnalysisResult(BaseModel):
    """Complete climate energy analysis result."""
    meta: AnalysisMeta
    data: List[LocationResult]
    errors: List[LocationError]


class ClimateEnergyAnalysisRequest(BaseModel):
    """Request for climate energy analysis."""
    locations: List[LocationInput] = Field(..., min_items=1, max_items=5, description="List of locations to analyze")
    
    class Config:
        schema_extra = {
            "example": {
                "locations": [
                    {"latitude": -7.1195, "longitude": -34.8451},
                    {"latitude": 48.13, "longitude": 11.57}
                ]
            }
        }


class SingleLocationRequest(BaseModel):
    """Request for single location climate energy analysis."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    
    class Config:
        schema_extra = {
            "example": {
                "latitude": -7.1195,
                "longitude": -34.8451
            }
        }