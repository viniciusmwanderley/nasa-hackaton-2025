# ABOUTME: Trend analysis for weather condition exceedances
# ABOUTME: Computes yearly trends and statistical significance using OLS regression

from datetime import datetime
from typing import List, Dict, Tuple
import math
from app.models import TrendPoint, Trend
from app.weather.thresholds import WeatherSample, flag_weather_conditions
from app.config import Settings


def calculate_exceedance_rates_by_year(
    samples: List[WeatherSample], 
    condition_type: str,
    settings: Settings
) -> Dict[int, float]:
    """
    Calculate yearly exceedance rates for a specific condition.
    
    Args:
        samples: List of weather samples
        condition_type: Type of condition ('hot', 'cold', 'windy', 'wet', 'any')
        settings: Configuration settings
        
    Returns:
        Dictionary mapping year to exceedance rate (0.0 to 1.0)
    """
    if not samples:
        return {}
    
    # Group samples by year
    yearly_samples = {}
    for sample in samples:
        year = sample.timestamp.year
        if year not in yearly_samples:
            yearly_samples[year] = []
        yearly_samples[year].append(sample)
    
    # Calculate exceedance rate for each year
    yearly_rates = {}
    
    for year, year_samples in yearly_samples.items():
        if not year_samples:
            continue
            
        # Count exceedances for this year
        exceedances = 0
        total = len(year_samples)
        
        for sample in year_samples:
            flags = flag_weather_conditions(sample, settings)
            
            condition_exceeded = False
            if condition_type == 'hot':
                condition_exceeded = flags.very_hot
            elif condition_type == 'cold': 
                condition_exceeded = flags.very_cold
            elif condition_type == 'windy':
                condition_exceeded = flags.very_windy
            elif condition_type == 'wet':
                condition_exceeded = flags.very_wet
            elif condition_type == 'any':
                condition_exceeded = (flags.very_hot or flags.very_cold or 
                                    flags.very_windy or flags.very_wet)
            
            if condition_exceeded:
                exceedances += 1
        
        yearly_rates[year] = exceedances / total if total > 0 else 0.0
    
    return yearly_rates


def calculate_ols_slope_and_pvalue(x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
    """
    Calculate OLS slope and p-value for linear regression.
    
    Args:
        x_values: Independent variable values (years)
        y_values: Dependent variable values (exceedance rates)
        
    Returns:
        Tuple of (slope, p_value)
    """
    n = len(x_values)
    if n < 3:  # Need at least 3 points for meaningful regression
        return 0.0, 1.0
    
    # Convert to arrays for calculations
    x = x_values
    y = y_values
    
    # Calculate means
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    
    # Calculate slope using least squares
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0, 1.0
    
    slope = numerator / denominator
    
    # Calculate residuals and standard error
    y_pred = [slope * (x[i] - x_mean) + y_mean for i in range(n)]
    residuals = [y[i] - y_pred[i] for i in range(n)]
    sse = sum(r ** 2 for r in residuals)
    
    # Degrees of freedom
    df = n - 2
    if df <= 0:
        return slope, 1.0
    
    # Mean squared error
    mse = sse / df
    
    # Standard error of slope
    se_slope = math.sqrt(mse / denominator)
    
    if se_slope == 0:
        return slope, 1.0 if slope == 0 else 0.0
    
    # t-statistic
    t_stat = slope / se_slope
    
    # Approximate p-value using t-distribution
    # For simplicity, use a conservative approximation
    # In production, would use scipy.stats.t.sf()
    abs_t = abs(t_stat)
    
    # Very rough approximation for p-value
    if abs_t > 2.576:  # ~99% confidence
        p_value = 0.01
    elif abs_t > 1.96:  # ~95% confidence  
        p_value = 0.05
    elif abs_t > 1.645:  # ~90% confidence
        p_value = 0.1
    else:
        p_value = 0.5  # Not significant
    
    return slope, p_value


def calculate_trend(
    samples: List[WeatherSample],
    condition_type: str,
    settings: Settings
) -> Trend:
    """
    Calculate trend analysis for a specific condition.
    
    Args:
        samples: List of weather samples
        condition_type: Type of condition ('hot', 'cold', 'windy', 'wet', 'any')
        settings: Configuration settings
        
    Returns:
        Trend object with yearly data and regression analysis
    """
    # Calculate yearly exceedance rates
    yearly_rates = calculate_exceedance_rates_by_year(samples, condition_type, settings)
    
    if len(yearly_rates) < 2:
        # Not enough data for trend analysis
        return Trend(
            condition=condition_type,
            points=[],
            slope=0.0,
            p_value=1.0,
            significant=False
        )
    
    # Sort by year
    sorted_years = sorted(yearly_rates.keys())
    
    # Create trend points
    points = []
    for year in sorted_years:
        points.append(TrendPoint(
            year=year,
            exceedance_rate=yearly_rates[year]
        ))
    
    # Calculate OLS regression
    x_values = [float(year) for year in sorted_years]
    y_values = [yearly_rates[year] for year in sorted_years]
    
    slope, p_value = calculate_ols_slope_and_pvalue(x_values, y_values)
    
    return Trend(
        condition=condition_type,
        points=points,
        slope=slope,
        p_value=p_value,
        significant=p_value < 0.05
    )


def calculate_all_trends(
    samples: List[WeatherSample],
    settings: Settings
) -> List[Trend]:
    """
    Calculate trends for all weather conditions.
    
    Args:
        samples: List of weather samples
        settings: Configuration settings
        
    Returns:
        List of Trend objects for each condition type
    """
    conditions = ['hot', 'cold', 'windy', 'wet', 'any']
    trends = []
    
    for condition in conditions:
        trend = calculate_trend(samples, condition, settings)
        trends.append(trend)
    
    return trends