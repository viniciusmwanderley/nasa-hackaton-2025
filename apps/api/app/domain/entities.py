# ABOUTME: Domain entities for weather analysis system
# ABOUTME: Contains core business objects like WeatherData, AnalysisResult, and WeatherClassifications

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .enums import Granularity, AnalysisMode


class WeatherParameter(BaseModel):
    """Weather parameter with value and metadata."""
    value: Optional[float]
    mode: AnalysisMode
    climatology_month_mean: Optional[float] = None
    model_used: Optional[str] = None


class WeatherData(BaseModel):
    """Weather data for a specific datetime."""
    datetime: str
    parameters: Dict[str, WeatherParameter]
    derived_insights: Dict[str, Optional[float]] = {}


class WeatherStats(BaseModel):
    """Historical statistics for a weather parameter."""
    count: int
    mean: float
    median: float
    min: float
    max: float
    std: float


class WeatherClassifications(BaseModel):
    """Weather classifications and risk assessments."""
    precipitation_source: Optional[str] = None
    rain_probability: Optional[float] = None
    very_hot_temp_percentile: Optional[float] = None
    very_snowy_probability: Optional[float] = None
    very_hot_feels_like_percentile: Optional[float] = None
    very_windy_percentile: Optional[float] = None
    very_wet_probability: Optional[float] = None
    very_wet_precip_threshold: Optional[float] = None
    very_wet_wind_threshold: Optional[float] = None


class WeatherAnalysisMeta(BaseModel):
    """Metadata for weather analysis."""
    latitude: float
    longitude: float
    center_datetime_utc: str
    center_datetime_local: str
    target_timezone: str
    granularity: str
    historical_data_range: List[str]


class WeatherAnalysisResult(BaseModel):
    """Complete weather analysis result."""
    meta: WeatherAnalysisMeta
    stats: Dict[str, Optional[WeatherStats]]
    classifications: WeatherClassifications
    results: List[WeatherData]


class WeatherAnalysisRequest(BaseModel):
    """Request for weather analysis."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    center_datetime: datetime = Field(..., description="Center datetime for analysis")
    target_timezone: str = Field(..., description="Target timezone (e.g., 'America/Sao_Paulo')")
    days_before: int = Field(3, ge=0, le=30, description="Days before center date to include")
    days_after: int = Field(3, ge=0, le=30, description="Days after center date to include")
    granularity: Granularity = Field(Granularity.DAILY, description="Data granularity")
    parameters: Optional[List[str]] = Field(None, description="Weather parameters to include")
    start_year: int = Field(1984, ge=1984, le=2024, description="Historical data start year")
    window_days: int = Field(7, ge=1, le=30, description="Temporal regression window in days")
    hourly_chunk_years: int = Field(5, ge=1, le=10, description="Years per chunk for hourly data")
    debug_mode: bool = Field(False, description="Enable debug mode")