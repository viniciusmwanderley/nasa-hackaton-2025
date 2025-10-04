# ABOUTME: Request and response models for weather analysis endpoints
# ABOUTME: Defines Pydantic schemas for API input validation and output serialization

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class Granularity(str, Enum):
    DAILY = "daily"
    HOURLY = "hourly"


class AnalysisMode(str, Enum):
    OBSERVED = "observed"
    PROBABILISTIC = "probabilistic"


class WeatherCondition(str, Enum):
    VERY_HOT = "very_hot"
    VERY_COLD = "very_cold"
    VERY_WINDY = "very_windy"
    VERY_WET = "very_wet"
    VERY_UNCOMFORTABLE = "very_uncomfortable"


class WeatherAnalysisRequest(BaseModel):
    """Request model for weather analysis."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    target_datetime: datetime = Field(..., description="Target date and time for analysis")
    granularity: Granularity = Field(default=Granularity.DAILY, description="Data granularity")
    parameters: Optional[List[str]] = Field(default=None, description="Weather parameters to analyze")
    start_year: int = Field(default=2005, ge=1984, description="Starting year for historical data")
    window_days: int = Field(default=7, ge=1, le=30, description="Window size in days for probabilistic analysis")

    @validator('target_datetime')
    def validate_datetime(cls, v):
        if v.year < 1984:
            raise ValueError("Target datetime cannot be before 1984")
        return v

    class Config:
        schema_extra = {
            "example": {
                "latitude": -7.115,
                "longitude": -34.863,
                "target_datetime": "2025-12-25T14:00:00",
                "granularity": "hourly",
                "start_year": 2005,
                "window_days": 7
            }
        }


class ParameterStats(BaseModel):
    """Statistical analysis for a weather parameter."""
    count: int
    mean: float
    median: float
    min: float
    max: float
    std: float
    p10: float
    p25: float
    p75: float
    p90: float


class ParameterAnalysis(BaseModel):
    """Analysis result for a single weather parameter."""
    mode: AnalysisMode
    climatology_month_mean: Optional[float] = None
    observed_value: Optional[float] = None
    stats: Optional[ParameterStats] = None
    sample_size: Optional[int] = None


class HeatIndexInsights(BaseModel):
    """Heat index calculations."""
    observed_heat_index_c: Optional[float] = None
    mean_heat_index_c: Optional[float] = None
    p90_heat_index_c: Optional[float] = None
    note: str


class ClassificationThreshold(BaseModel):
    """Classification threshold for weather conditions."""
    condition: WeatherCondition
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability between 0 and 1")
    confidence: str = Field(..., description="Confidence level (low, medium, high)")
    threshold_value: Optional[float] = None
    parameter_used: Optional[str] = None
    description: str


class WeatherMetadata(BaseModel):
    """Metadata for weather analysis."""
    latitude: float
    longitude: float
    target_datetime: str
    granularity: str
    analysis_mode: str
    historical_data_range: List[str]
    window_days_used: int


class WeatherAnalysisResponse(BaseModel):
    """Complete weather analysis response."""
    meta: WeatherMetadata
    derived_insights: Dict[str, Any]
    parameters: Dict[str, ParameterAnalysis]
    classifications: List[ClassificationThreshold]
    request_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "meta": {
                    "latitude": -7.115,
                    "longitude": -34.863,
                    "target_datetime": "2025-12-25T14:00:00",
                    "granularity": "hourly",
                    "analysis_mode": "probabilistic",
                    "historical_data_range": ["2005-01-01", "2025-10-04"],
                    "window_days_used": 7
                },
                "derived_insights": {
                    "heat_index": {
                        "mean_heat_index_c": 28.5,
                        "p90_heat_index_c": 32.1,
                        "note": "Heat index calculated for T>=26.7C and RH>=40%."
                    }
                },
                "parameters": {
                    "T2M": {
                        "mode": "probabilistic",
                        "climatology_month_mean": 27.2,
                        "stats": {
                            "count": 150,
                            "mean": 28.1,
                            "median": 27.8,
                            "min": 24.5,
                            "max": 32.3,
                            "std": 2.1,
                            "p10": 25.8,
                            "p25": 26.7,
                            "p75": 29.4,
                            "p90": 31.2
                        },
                        "sample_size": 150
                    }
                },
                "classifications": [
                    {
                        "condition": "very_hot",
                        "probability": 0.75,
                        "confidence": "high",
                        "threshold_value": 35.0,
                        "parameter_used": "T2M",
                        "description": "High probability of very hot conditions based on temperature analysis"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    request_id: Optional[str] = None
    timestamp: str