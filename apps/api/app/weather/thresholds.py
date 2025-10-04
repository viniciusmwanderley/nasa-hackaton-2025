# ABOUTME: Weather condition threshold helpers for outdoor risk assessment
# ABOUTME: Flags dangerous conditions (very hot, cold, windy, wet) per weather sample

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from .calculations import heat_index, wind_chill, feels_like_temperature
from ..config import Settings


@dataclass
class WeatherSample:
    """
    Represents a single weather observation with all meteorological parameters.
    
    This is the core data structure for weather risk assessment, containing
    all the meteorological parameters needed to evaluate outdoor conditions.
    """
    # Core meteorological parameters
    temperature_c: float                    # Air temperature in Celsius
    relative_humidity: float               # Relative humidity percentage (0-100)
    wind_speed_ms: float                   # Wind speed in meters per second
    precipitation_mm_per_day: float        # Daily precipitation in mm
    
    # Metadata
    timestamp: datetime                    # When this sample was observed
    latitude: float                        # Sample location latitude
    longitude: float                       # Sample location longitude
    
    # Optional calculated fields
    heat_index_c: Optional[float] = None   # Calculated heat index
    wind_chill_c: Optional[float] = None   # Calculated wind chill  
    feels_like_c: Optional[float] = None   # Calculated "feels like" temperature
    
    def __post_init__(self):
        """Calculate derived meteorological values after initialization."""
        # Calculate heat index if conditions apply
        self.heat_index_c = heat_index(self.temperature_c, self.relative_humidity)
        
        # Calculate wind chill if conditions apply
        self.wind_chill_c = wind_chill(self.temperature_c, self.wind_speed_ms)
        
        # Calculate feels-like temperature
        self.feels_like_c = feels_like_temperature(
            self.temperature_c, 
            self.relative_humidity, 
            self.wind_speed_ms
        )
    
    @classmethod
    def from_power_data(
        cls, 
        power_data: Dict[str, float], 
        date: datetime,
        latitude: float, 
        longitude: float
    ) -> "WeatherSample":
        """
        Create WeatherSample from NASA POWER API data.
        
        Args:
            power_data: Dictionary with keys T2M, RH2M, WS10M, PRECTOTCORR
            date: Date of the observation
            latitude: Sample location latitude
            longitude: Sample location longitude
            
        Returns:
            WeatherSample instance
            
        Raises:
            KeyError: If required parameters are missing from power_data
            ValueError: If parameter values are invalid
        """
        required_params = ["T2M", "RH2M", "WS10M", "PRECTOTCORR"]
        missing_params = [p for p in required_params if p not in power_data]
        if missing_params:
            raise KeyError(f"Missing required parameters: {missing_params}")
        
        return cls(
            temperature_c=float(power_data["T2M"]),
            relative_humidity=float(power_data["RH2M"]), 
            wind_speed_ms=float(power_data["WS10M"]),
            precipitation_mm_per_day=float(power_data["PRECTOTCORR"]),
            timestamp=date,
            latitude=latitude,
            longitude=longitude
        )


@dataclass
class WeatherConditionFlags:
    """
    Flags indicating whether various dangerous weather conditions are present.
    
    These flags are used to identify outdoor risk scenarios based on 
    configurable thresholds for different meteorological hazards.
    """
    very_hot: bool = False      # Heat index or temperature exceeds hot threshold
    very_cold: bool = False     # Wind chill or temperature below cold threshold  
    very_windy: bool = False    # Wind speed exceeds windy threshold
    very_wet: bool = False      # Precipitation exceeds wet threshold
    
    def any_flagged(self) -> bool:
        """Return True if any dangerous condition is flagged."""
        return any([self.very_hot, self.very_cold, self.very_windy, self.very_wet])
    
    def count_flagged(self) -> int:
        """Return count of flagged conditions."""
        return sum([self.very_hot, self.very_cold, self.very_windy, self.very_wet])
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert flags to dictionary format."""
        return {
            "very_hot": self.very_hot,
            "very_cold": self.very_cold, 
            "very_windy": self.very_windy,
            "very_wet": self.very_wet
        }


def is_very_hot(sample: WeatherSample, settings: Optional[Settings] = None) -> bool:
    """
    Determine if weather conditions are dangerously hot.
    
    Uses heat index when available (hot + humid conditions), otherwise
    falls back to air temperature threshold.
    
    Args:
        sample: Weather sample to evaluate
        settings: Configuration with hot thresholds (optional)
        
    Returns:
        True if conditions are very hot, False otherwise
    """
    if settings is None:
        settings = Settings()
    
    # Use heat index if it applies (considers humidity)
    if sample.heat_index_c is not None:
        return sample.heat_index_c >= settings.thresholds_hi_hot_c
    
    # Fall back to air temperature for dry conditions
    return sample.temperature_c >= settings.thresholds_hi_hot_c


def is_very_cold(sample: WeatherSample, settings: Optional[Settings] = None) -> bool:
    """
    Determine if weather conditions are dangerously cold.
    
    Uses wind chill when available (cold + windy conditions), otherwise
    falls back to air temperature threshold.
    
    Args:
        sample: Weather sample to evaluate
        settings: Configuration with cold thresholds (optional)
        
    Returns:
        True if conditions are very cold, False otherwise
    """
    if settings is None:
        settings = Settings()
    
    # Use wind chill if it applies (considers wind)
    if sample.wind_chill_c is not None:
        return sample.wind_chill_c <= settings.thresholds_wct_cold_c
    
    # Fall back to air temperature for calm conditions
    return sample.temperature_c <= settings.thresholds_wct_cold_c


def is_very_windy(sample: WeatherSample, settings: Optional[Settings] = None) -> bool:
    """
    Determine if wind conditions are dangerous.
    
    Args:
        sample: Weather sample to evaluate
        settings: Configuration with wind threshold (optional)
        
    Returns:
        True if conditions are very windy, False otherwise
    """
    if settings is None:
        settings = Settings()
    
    return sample.wind_speed_ms >= settings.thresholds_wind_ms


def is_very_wet(sample: WeatherSample, settings: Optional[Settings] = None) -> bool:
    """
    Determine if precipitation conditions are dangerous.
    
    Converts daily precipitation to hourly rate for threshold comparison.
    
    Args:
        sample: Weather sample to evaluate  
        settings: Configuration with precipitation threshold (optional)
        
    Returns:
        True if conditions are very wet, False otherwise
    """
    if settings is None:
        settings = Settings()
    
    # Convert daily precipitation to hourly rate
    # Assumes precipitation is distributed over ~8 hours of daylight
    hourly_precip_mm = sample.precipitation_mm_per_day / 8.0
    
    return hourly_precip_mm >= settings.thresholds_rain_mm_per_h


def flag_weather_conditions(
    sample: WeatherSample, 
    settings: Optional[Settings] = None
) -> WeatherConditionFlags:
    """
    Evaluate all weather condition thresholds for a single sample.
    
    This is the main function for determining outdoor risk conditions.
    It evaluates temperature (hot/cold), wind, and precipitation thresholds
    using the appropriate meteorological calculations.
    
    Args:
        sample: Weather sample to evaluate
        settings: Configuration with all thresholds (optional)
        
    Returns:
        WeatherConditionFlags with all relevant flags set
        
    Example:
        >>> sample = WeatherSample(...)
        >>> flags = flag_weather_conditions(sample)
        >>> if flags.very_hot:
        ...     print("Dangerous heat conditions!")
        >>> if flags.any_flagged():
        ...     print(f"Warning: {flags.count_flagged()} dangerous conditions")
    """
    if settings is None:
        settings = Settings()
    
    return WeatherConditionFlags(
        very_hot=is_very_hot(sample, settings),
        very_cold=is_very_cold(sample, settings),
        very_windy=is_very_windy(sample, settings),
        very_wet=is_very_wet(sample, settings)
    )


def evaluate_sample_risk(
    sample: WeatherSample,
    settings: Optional[Settings] = None
) -> Dict[str, Any]:
    """
    Comprehensive risk evaluation for a weather sample.
    
    Provides detailed information about the sample including calculated
    meteorological values and all condition flags.
    
    Args:
        sample: Weather sample to evaluate
        settings: Configuration (optional)
        
    Returns:
        Dictionary with comprehensive risk information
    """
    if settings is None:
        settings = Settings()
    
    flags = flag_weather_conditions(sample, settings)
    
    return {
        # Raw meteorological data
        "temperature_c": sample.temperature_c,
        "relative_humidity": sample.relative_humidity,
        "wind_speed_ms": sample.wind_speed_ms,
        "precipitation_mm_per_day": sample.precipitation_mm_per_day,
        
        # Calculated comfort indices
        "heat_index_c": sample.heat_index_c,
        "wind_chill_c": sample.wind_chill_c,
        "feels_like_c": sample.feels_like_c,
        
        # Condition flags
        "flags": flags.to_dict(),
        "any_dangerous": flags.any_flagged(),
        "danger_count": flags.count_flagged(),
        
        # Metadata
        "timestamp": sample.timestamp.isoformat(),
        "location": {
            "latitude": sample.latitude,
            "longitude": sample.longitude
        }
    }