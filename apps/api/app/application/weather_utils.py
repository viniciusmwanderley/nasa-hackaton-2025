# ABOUTME: Weather data processing utilities for statistics and calculations
# ABOUTME: Contains functions for heat index, historical statistics, and temporal predictions

import logging
from datetime import datetime, date, timezone
from typing import Dict, List, Optional, Any
import numpy as np
from scipy.stats import percentileofscore
from sklearn.linear_model import LinearRegression
from ..domain.entities import WeatherStats
from ..domain.enums import Granularity


logger = logging.getLogger("outdoor_risk_api.weather_utils")


def calculate_heat_index(temp_c: Optional[float], rh_percent: Optional[float]) -> Optional[float]:
    """    
    Args:
        temp_c: Temperature in Celsius
        rh_percent: Relative humidity percentage
        
    Returns:
        Heat index in Celsius, or None if inputs are invalid
    """
    if temp_c is None or rh_percent is None or np.isnan(temp_c) or np.isnan(rh_percent):
        return None
    
    # Heat index only relevant for hot, humid conditions
    if temp_c < 26.7 or rh_percent < 40:
        return temp_c
    
    # Convert to Fahrenheit for calculation
    t_f = temp_c * 9/5 + 32
    
    # Heat index calculation (Rothfusz equation)
    hi_f = (
        -42.379 + 2.04901523*t_f + 10.14333127*rh_percent - 0.22475541*t_f*rh_percent 
        - 6.83783e-3*t_f**2 - 5.481717e-2*rh_percent**2 + 1.22874e-3*t_f**2*rh_percent 
        + 8.5282e-4*t_f*rh_percent**2 - 1.99e-6*t_f**2*rh_percent**2
    )
    
    # Convert back to Celsius
    return (hi_f - 32) * 5/9


def calculate_historical_stats(all_series: Dict[str, Dict[str, float]]) -> Dict[str, Optional[WeatherStats]]:
    """    
    Args:
        all_series: Dictionary mapping parameters to their time series
        
    Returns:
        Dictionary mapping parameters to their statistics
    """
    stats_results = {}
    
    for param, series in all_series.items():
        values = [v for v in series.values() if v is not None]
        
        if not values:
            stats_results[param] = None
            continue
        
        np_values = np.array(values, dtype=np.float64)
        
        stats_results[param] = WeatherStats(
            count=len(np_values),
            mean=float(np.mean(np_values)),
            median=float(np.median(np_values)),
            min=float(np.min(np_values)),
            max=float(np.max(np_values)),
            std=float(np.std(np_values))
        )
    
    return stats_results


def predict_with_temporal_regression(
    series: Dict[str, float], 
    target_dt: datetime, 
    granularity: Granularity, 
    window_days: int
) -> Optional[float]:
    """    
    Args:
        series: Historical data series
        target_dt: Target datetime for prediction
        granularity: Data granularity
        window_days: Window size for seasonal matching
        
    Returns:
        Predicted value or None if insufficient data
    """
    target_doy = target_dt.timetuple().tm_yday
    doy_range = {(target_doy - 1 + i) % 365 + 1 for i in range(-window_days, window_days + 1)}
    
    historical_points = []
    date_format = "%Y%m%d" if granularity == Granularity.DAILY else "%Y%m%d%H"
    
    for date_str, value in series.items():
        if value is None:
            continue
        
        try:
            d = datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
            is_in_day_window = d.timetuple().tm_yday in doy_range
            is_correct_hour = True if granularity == Granularity.DAILY else d.hour == target_dt.hour
            
            if is_in_day_window and is_correct_hour:
                historical_points.append((d.year, float(value)))
                
        except (ValueError, TypeError):
            continue
    
    if not historical_points:
        return None
    
    # Group by year and average multiple observations
    yearly_data = {}
    for year, value in historical_points:
        if year not in yearly_data:
            yearly_data[year] = []
        yearly_data[year].append(value)
    
    X_train_list, y_train_list = [], []
    for year, values in sorted(yearly_data.items()):
        X_train_list.append(year)
        y_train_list.append(np.mean(values))
    
    if len(X_train_list) < 2:
        return np.mean(y_train_list) if y_train_list else None
    
    # Fit linear regression model
    X_train = np.array(X_train_list).reshape(-1, 1)
    y_train = np.array(y_train_list)
    
    try:
        model = LinearRegression().fit(X_train, y_train)
        prediction = model.predict(np.array([[target_dt.year]]))[0]
        
        logger.debug(
            "Temporal regression prediction",
            extra={
                "target_year": target_dt.year,
                "prediction": float(prediction),
                "training_years": len(X_train_list)
            }
        )
        
        return float(prediction)
        
    except Exception as e:
        logger.warning(f"Linear regression failed, using mean: {e}")
        return float(np.mean(y_train))


def get_sanitized_series(all_series: Dict[str, Dict[str, float]], param: str) -> List[float]:
    """    
    Args:
        all_series: All parameter series
        param: Parameter name
        
    Returns:
        List of valid values
    """
    return [v for v in all_series.get(param, {}).values() if v is not None]