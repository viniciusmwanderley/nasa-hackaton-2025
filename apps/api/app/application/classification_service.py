# ABOUTME: Weather classification service for risk assessment and percentile calculations
# ABOUTME: Handles precipitation, temperature, wind, and snow probability classifications

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import numpy as np
from scipy.stats import percentileofscore
from ..domain.entities import WeatherClassifications
from ..domain.enums import Granularity
from .weather_utils import calculate_heat_index, get_sanitized_series


logger = logging.getLogger("outdoor_risk_api.classification_service")


class WeatherClassificationService:
    """Service for calculating weather classifications and risk assessments."""
    
    def calculate_classifications(
        self,
        target_dt_utc: datetime,
        daily_values: Dict[str, Any],
        all_historical_series: Dict[str, Dict[str, float]],
        granularity: Granularity
    ) -> WeatherClassifications:
        """
        Calculate weather classifications for risk assessment.
        
        Args:
            target_dt_utc: Target datetime in UTC
            daily_values: Current day weather values
            all_historical_series: Historical weather data
            granularity: Data granularity
            
        Returns:
            Weather classifications with risk percentiles and probabilities
        """
        classifications = WeatherClassifications()
        
        # Determine precipitation source
        has_imerg = "IMERG_PRECTOT" in all_historical_series and any(all_historical_series["IMERG_PRECTOT"].values())
        precip_param = "IMERG_PRECTOT" if has_imerg else "PRECTOTCORR"
        if precip_param in all_historical_series:
            classifications.precipitation_source = precip_param
        
        # Calculate rain probability using seasonal window
        classifications.rain_probability = self._calculate_rain_probability(
            target_dt_utc, all_historical_series, precip_param, granularity
        )
        
        # Temperature classifications
        predicted_t_avg = daily_values.get("T2M", {}).get("value")
        predicted_rh2m = daily_values.get("RH2M", {}).get("value")
        
        if granularity == Granularity.DAILY:
            # Hot temperature percentile
            predicted_t_max = daily_values.get("T2M_MAX", {}).get("value")
            hist_t_max = get_sanitized_series(all_historical_series, "T2M_MAX")
            if hist_t_max and predicted_t_max is not None:
                classifications.very_hot_temp_percentile = percentileofscore(
                    hist_t_max, predicted_t_max, kind='rank'
                )
            
            # Snow probability
            classifications.very_snowy_probability = self._calculate_snow_probability(
                predicted_t_avg, all_historical_series
            )
        
        # Heat index percentile
        if predicted_t_avg is not None and predicted_rh2m is not None:
            classifications.very_hot_feels_like_percentile = self._calculate_heat_index_percentile(
                predicted_t_avg, predicted_rh2m, all_historical_series
            )
        
        # Wind percentile
        predicted_wind = daily_values.get("WS10M", {}).get("value")
        hist_wind = get_sanitized_series(all_historical_series, "WS10M")
        if hist_wind and predicted_wind is not None:
            classifications.very_windy_percentile = percentileofscore(
                hist_wind, predicted_wind, kind='rank'
            )
        
        # Stormy weather probability
        wet_classifications = self._calculate_wet_probability(
            all_historical_series, precip_param
        )
        classifications.very_wet_probability = wet_classifications.get("probability")
        classifications.very_wet_precip_threshold = wet_classifications.get("precip_threshold")
        classifications.very_wet_wind_threshold = wet_classifications.get("wind_threshold")
        
        return classifications
    
    def _calculate_rain_probability(
        self,
        target_dt_utc: datetime,
        all_historical_series: Dict[str, Dict[str, float]],
        precip_param: str,
        granularity: Granularity,
        window_days: int = 15
    ) -> Optional[float]:
        """Calculate probability of rain based on historical seasonal data."""
        target_doy = target_dt_utc.timetuple().tm_yday
        doy_range = {(target_doy - 1 + i) % 365 + 1 for i in range(-window_days, window_days + 1)}
        
        seasonal_precip = []
        historical_precip_series = all_historical_series.get(precip_param, {})
        
        for date_str, value in historical_precip_series.items():
            try:
                date_format = "%Y%m%d%H" if granularity == Granularity.HOURLY else "%Y%m%d"
                d = datetime.strptime(date_str, date_format)
                
                if d.timetuple().tm_yday in doy_range and value is not None:
                    seasonal_precip.append(value)
                    
            except (ValueError, TypeError):
                continue
        
        if seasonal_precip:
            rainy_events = sum(1 for p in seasonal_precip if p > 0.1)
            return rainy_events / len(seasonal_precip)
        
        return None
    
    def _calculate_snow_probability(
        self,
        predicted_t_avg: Optional[float],
        all_historical_series: Dict[str, Dict[str, float]]
    ) -> Optional[float]:
        """Calculate probability of snow based on temperature and historical data."""
        if predicted_t_avg is not None and predicted_t_avg > 2.0:
            return 0.0
        
        hist_snow = get_sanitized_series(all_historical_series, "FRSNO")
        if hist_snow:
            snowy_days = sum(1 for s in hist_snow if s > 0)
            return snowy_days / len(hist_snow)
        
        return 0.0
    
    def _calculate_heat_index_percentile(
        self,
        predicted_t_avg: float,
        predicted_rh2m: float,
        all_historical_series: Dict[str, Dict[str, float]]
    ) -> Optional[float]:
        """Calculate heat index percentile for feels-like temperature assessment."""
        hist_t_avg_series = all_historical_series.get("T2M", {})
        hist_rh2m_series = all_historical_series.get("RH2M", {})
        
        historical_heat_index = []
        
        for date_key, t_avg in hist_t_avg_series.items():
            rh = hist_rh2m_series.get(date_key)
            if t_avg is not None and rh is not None:
                hi = calculate_heat_index(t_avg, rh)
                if hi is not None:
                    historical_heat_index.append(hi)
        
        if historical_heat_index:
            predicted_heat_index = calculate_heat_index(predicted_t_avg, predicted_rh2m)
            if predicted_heat_index is not None:
                return percentileofscore(historical_heat_index, predicted_heat_index, kind='rank')
        
        return None
    
    def _calculate_wet_probability(
        self,
        all_historical_series: Dict[str, Dict[str, float]],
        precip_param: str
    ) -> Dict[str, Optional[float]]:
        """Calculate probability of very wet/stormy conditions."""
        hist_precip_full = get_sanitized_series(all_historical_series, precip_param)
        hist_wind = get_sanitized_series(all_historical_series, "WS10M")
        
        if not hist_precip_full or not hist_wind:
            return {"probability": None, "precip_threshold": None, "wind_threshold": None}
        
        precip_threshold = np.percentile(hist_precip_full, 90)
        wind_threshold = np.percentile(hist_wind, 75)
        
        stormy_events = 0
        total_events = len(all_historical_series.get("T2M", {}))
        
        hist_precip_series = all_historical_series.get(precip_param, {})
        hist_wind_series = all_historical_series.get("WS10M", {})
        
        for date_key, precip_val in hist_precip_series.items():
            wind_val = hist_wind_series.get(date_key)
            if (precip_val is not None and wind_val is not None and 
                precip_val > precip_threshold and wind_val > wind_threshold):
                stormy_events += 1
        
        probability = stormy_events / total_events if total_events > 0 else 0.0
        
        return {
            "probability": probability,
            "precip_threshold": float(precip_threshold),
            "wind_threshold": float(wind_threshold)
        }