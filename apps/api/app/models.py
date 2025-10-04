# ABOUTME: Pydantic models for API request/response schemas
# ABOUTME: Defines data structures for the /risk endpoint and related API interactions

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RiskRequest(BaseModel):
    """Request model for outdoor risk assessment."""

    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude in decimal degrees (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude in decimal degrees (-180 to 180)"
    )
    target_date: str = Field(..., description="Target date in YYYY-MM-DD format")
    target_hour: int = Field(..., ge=0, le=23, description="Target local hour (0-23)")
    window_days: int = Field(
        default=15,
        ge=1,
        le=30,
        description="Days before/after target DOY to include (1-30)",
    )
    detail: str = Field(
        default="lean", description="Response detail level: 'lean' or 'full'"
    )

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: str) -> str:
        """Validate target_date is in correct format and is a valid date."""
        try:
            # This will raise ValueError if format is wrong
            parsed_date = date.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValueError(f"target_date must be in YYYY-MM-DD format: {e}")

    @field_validator("detail")
    @classmethod
    def validate_detail(cls, v: str) -> str:
        """Validate detail level is supported."""
        if v not in {"lean", "full"}:
            raise ValueError("detail must be 'lean' or 'full'")
        return v


class ConfidenceInterval(BaseModel):
    """Confidence interval for probability estimates."""

    lower: float = Field(description="Lower bound of confidence interval")
    upper: float = Field(description="Upper bound of confidence interval")
    level: float = Field(default=0.95, description="Confidence level (default 95%)")
    width: float = Field(description="Width of confidence interval")


class ConditionProbability(BaseModel):
    """Probability result for a specific weather condition."""

    probability: float = Field(description="Point estimate probability (0-1)")
    confidence_interval: ConfidenceInterval = Field(
        description="95% confidence interval"
    )
    positive_samples: int = Field(
        description="Number of samples with flagged conditions"
    )


class SampleStatistics(BaseModel):
    """Statistics about the sample collection."""

    total_samples: int = Field(description="Total number of weather samples analyzed")
    years_with_data: int = Field(description="Number of years with data coverage")
    coverage_adequate: bool = Field(
        description="Whether coverage meets minimum requirements"
    )
    timezone_iana: str = Field(description="IANA timezone identifier for the location")


class ConditionThresholds(BaseModel):
    """Threshold values used for condition flagging."""

    very_hot_c: float = Field(
        description="Heat index threshold for very hot conditions (°C)"
    )
    very_cold_c: float = Field(
        description="Wind chill threshold for very cold conditions (°C)"
    )
    very_windy_ms: float = Field(
        description="Wind speed threshold for very windy conditions (m/s)"
    )
    very_wet_mm_per_h: float = Field(
        description="Precipitation rate threshold for very wet conditions (mm/h)"
    )


class RiskResponseLean(BaseModel):
    """Lean response model for outdoor risk assessment."""

    # Location and request info
    latitude: float = Field(description="Requested latitude")
    longitude: float = Field(description="Requested longitude")
    target_date: str = Field(description="Requested target date (YYYY-MM-DD)")
    target_hour: int = Field(description="Requested target local hour (0-23)")

    # Probability results for each condition
    very_hot: ConditionProbability = Field(
        description="Probability of very hot conditions"
    )
    very_cold: ConditionProbability = Field(
        description="Probability of very cold conditions"
    )
    very_windy: ConditionProbability = Field(
        description="Probability of very windy conditions"
    )
    very_wet: ConditionProbability = Field(
        description="Probability of very wet conditions"
    )
    any_adverse: ConditionProbability = Field(
        description="Probability of any adverse conditions"
    )

    # Sample metadata
    sample_statistics: SampleStatistics = Field(
        description="Statistics about the sample collection"
    )
    thresholds: ConditionThresholds = Field(description="Threshold values used")


class HistogramBin(BaseModel):
    """Single bin in a histogram distribution."""

    lower_bound: float = Field(description="Lower bound of bin (inclusive)")
    upper_bound: float = Field(
        description="Upper bound of bin (exclusive, except for last bin)"
    )
    count: int = Field(description="Number of samples in this bin")
    frequency: float = Field(description="Relative frequency (count / total_samples)")


class Distribution(BaseModel):
    """Distribution data for a meteorological parameter."""

    parameter: str = Field(description="Parameter name")
    unit: str = Field(description="Unit of measurement")
    bins: list[HistogramBin] = Field(description="Histogram bins")
    mean: float = Field(description="Mean value")
    median: float = Field(description="Median value")
    std_dev: float = Field(description="Standard deviation")
    threshold_value: float | None = Field(
        None, description="Threshold value for this parameter (if applicable)"
    )


class TrendPoint(BaseModel):
    """Single point in a trend series."""

    year: int = Field(description="Year")
    exceedance_rate: float = Field(description="Exceedance rate for this year")


class Trend(BaseModel):
    """Trend analysis for a specific condition."""

    condition: str = Field(description="Condition name")
    points: list[TrendPoint] = Field(description="Yearly trend points")
    slope: float = Field(description="OLS slope (change per year)")
    p_value: float = Field(description="Statistical significance (p-value)")
    significant: bool = Field(
        description="Whether trend is statistically significant (p < 0.05)"
    )


class RiskResponseFull(RiskResponseLean):
    """Full response model with distributions and trends."""

    distributions: list[Distribution] = Field(description="Parameter distributions")
    trends: list[Trend] = Field(description="Annual exceedance trends")


class ExportRequest(BaseModel):
    """Request model for data export."""

    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude in decimal degrees (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude in decimal degrees (-180 to 180)"
    )
    target_date: str = Field(..., description="Target date in YYYY-MM-DD format")
    target_hour: int = Field(..., ge=0, le=23, description="Target local hour (0-23)")
    window_days: int = Field(
        default=15,
        ge=1,
        le=30,
        description="Days before/after target DOY to include (1-30)",
    )
    format: str = Field(default="csv", description="Export format: 'csv' or 'json'")

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: str) -> str:
        """Validate target_date is in correct format and is a valid date."""
        try:
            # This will raise ValueError if format is wrong
            parsed_date = date.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValueError(f"target_date must be in YYYY-MM-DD format: {e}")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format is supported."""
        if v not in {"csv", "json"}:
            raise ValueError("format must be 'csv' or 'json'")
        return v


class ExportSampleRow(BaseModel):
    """Single row in export data."""

    timestamp_local: str = Field(description="Local timestamp (ISO format)")
    year: int = Field(description="Year")
    doy: int = Field(description="Day of year")
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    t2m_c: float = Field(description="Temperature (°C)")
    rh2m_pct: float = Field(description="Relative humidity (%)")
    ws10m_ms: float = Field(description="Wind speed (m/s)")
    hi_c: float | None = Field(description="Heat index (°C)")
    wct_c: float | None = Field(description="Wind chill (°C)")
    precip_mm_per_h: float = Field(description="Precipitation rate (mm/h)")
    precip_source: str = Field(description="Precipitation data source")
    flags_very_hot: bool = Field(description="Very hot conditions flag")
    flags_very_cold: bool = Field(description="Very cold conditions flag")
    flags_very_windy: bool = Field(description="Very windy conditions flag")
    flags_very_wet: bool = Field(description="Very wet conditions flag")
    flags_any_adverse: bool = Field(description="Any adverse conditions flag")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    request_id: str | None = Field(None, description="Request ID for tracking")
