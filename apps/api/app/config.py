# ABOUTME: Configuration module using Pydantic Settings for environment variable management
# ABOUTME: Defines all configurable thresholds, timeouts, CORS origins, and rate limits

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    # Weather condition thresholds
    thresholds_hi_hot_c: float = Field(default=41.0, description="Heat index threshold for very hot (°C)")
    thresholds_hi_uncomf_c: float = Field(default=32.0, description="Heat index threshold for uncomfortable (°C)")
    thresholds_wct_cold_c: float = Field(default=-10.0, description="Wind chill threshold for very cold (°C)")
    thresholds_wind_ms: float = Field(default=10.8, description="Wind speed threshold for very windy (m/s)")
    thresholds_rain_mm_per_h: float = Field(default=4.0, description="Precipitation threshold for very wet (mm/h)")
    
    # CORS configuration  
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:4173",
        description="Comma-separated allowed CORS origins for development"
    )
    
    # Rate limiting
    rate_limit_general: str = Field(default="30/minute;burst=10", description="General API rate limit")
    rate_limit_export: str = Field(default="6/minute;burst=6", description="Export endpoint rate limit")
    
    # Default query parameters
    default_baseline_start: int = Field(default=2001, description="Default baseline start year")
    default_baseline_end: str = Field(default="present", description="Default baseline end (present or year)")
    default_window_days: int = Field(default=7, description="Default DOY window size")
    default_hour_local: str = Field(default="10:00", description="Default local hour")
    
    # Coverage requirements
    coverage_min_years: int = Field(default=15, description="Minimum years for coverage")
    coverage_min_samples: int = Field(default=8, description="Minimum samples for coverage")
    
    # HTTP client timeouts
    timeout_connect_s: int = Field(default=10, description="Connection timeout (seconds)")
    timeout_read_s: int = Field(default=30, description="Read timeout (seconds)")
    retries: int = Field(default=3, description="Number of HTTP retries")
    
    # External API URLs
    power_base_url: str = Field(default="https://power.larc.nasa.gov", description="NASA POWER API base URL")
    
    # Cache configuration
    cache_dir: str = Field(default="/cache", description="Cache directory path")
    cache_max_gb: int = Field(default=5, description="Maximum cache size (GB)")
    cache_ttl_days: int = Field(default=30, description="Cache TTL (days)")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
        return []
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }