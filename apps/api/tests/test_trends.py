# ABOUTME: Tests for trend analysis functionality
# ABOUTME: Validates yearly trend calculation and statistical significance testing

import pytest
from datetime import datetime
from app.analysis.trends import (
    calculate_exceedance_rates_by_year, calculate_ols_slope_and_pvalue,
    calculate_trend, calculate_all_trends
)
from app.weather.thresholds import WeatherSample
from app.config import Settings


class TestExceedanceRatesByYear:
    """Test yearly exceedance rate calculation."""
    
    def test_calculate_exceedance_rates_basic(self):
        """Test basic yearly exceedance rate calculation."""
        settings = Settings()
        
        # Create samples with known conditions
        samples = [
            # 2020: 1 hot out of 2 samples = 50%
            WeatherSample(
                temperature_c=45.0, relative_humidity=80.0, wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 6, 15),
                latitude=-3.7, longitude=-38.5
            ),
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 6, 16),
                latitude=-3.7, longitude=-38.5
            ),
            # 2021: 0 hot out of 1 sample = 0%
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0, timestamp=datetime(2021, 6, 15),
                latitude=-3.7, longitude=-38.5
            )
        ]
        
        rates = calculate_exceedance_rates_by_year(samples, "hot", settings)
        
        assert 2020 in rates
        assert 2021 in rates
        assert rates[2020] == pytest.approx(0.5)  # 1/2 = 50%
        assert rates[2021] == pytest.approx(0.0)  # 0/1 = 0%
    
    def test_calculate_exceedance_rates_windy_condition(self):
        """Test exceedance rate calculation for windy conditions."""
        settings = Settings()
        
        samples = [
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=15.0,  # Very windy
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 1),
                latitude=-3.7, longitude=-38.5
            ),
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,   # Normal wind
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 2),
                latitude=-3.7, longitude=-38.5
            )
        ]
        
        rates = calculate_exceedance_rates_by_year(samples, "windy", settings)
        
        assert rates[2020] == pytest.approx(0.5)  # 1 windy out of 2
    
    def test_calculate_exceedance_rates_any_condition(self):
        """Test exceedance rate for any adverse condition."""
        settings = Settings()
        
        samples = [
            WeatherSample(
                temperature_c=45.0, relative_humidity=80.0, wind_speed_ms=5.0,   # Hot
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 1),
                latitude=-3.7, longitude=-38.5
            ),
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=15.0,  # Windy
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 2),
                latitude=-3.7, longitude=-38.5
            ),
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,   # Normal
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 3),
                latitude=-3.7, longitude=-38.5
            )
        ]
        
        rates = calculate_exceedance_rates_by_year(samples, "any", settings)
        
        assert rates[2020] == pytest.approx(2.0/3.0)  # 2 adverse out of 3
    
    def test_calculate_exceedance_rates_empty_samples(self):
        """Test exceedance rate calculation with empty samples."""
        settings = Settings()
        
        rates = calculate_exceedance_rates_by_year([], "hot", settings)
        
        assert rates == {}


class TestOLSRegression:
    """Test OLS slope and p-value calculation."""
    
    def test_calculate_ols_slope_increasing_trend(self):
        """Test OLS calculation for increasing trend."""
        x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_values = [1.0, 2.0, 3.0, 4.0, 5.0]  # Perfect positive correlation
        
        slope, p_value = calculate_ols_slope_and_pvalue(x_values, y_values)
        
        assert slope == pytest.approx(1.0)
        assert p_value < 0.05  # Should be significant
    
    def test_calculate_ols_slope_decreasing_trend(self):
        """Test OLS calculation for decreasing trend."""
        x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_values = [5.0, 4.0, 3.0, 2.0, 1.0]  # Perfect negative correlation
        
        slope, p_value = calculate_ols_slope_and_pvalue(x_values, y_values)
        
        assert slope == pytest.approx(-1.0)
        assert p_value < 0.05  # Should be significant
    
    def test_calculate_ols_slope_no_trend(self):
        """Test OLS calculation for no trend."""
        x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_values = [2.0, 2.0, 2.0, 2.0, 2.0]  # No variation
        
        slope, p_value = calculate_ols_slope_and_pvalue(x_values, y_values)
        
        assert slope == pytest.approx(0.0)
        assert p_value >= 0.05  # Should not be significant
    
    def test_calculate_ols_slope_insufficient_data(self):
        """Test OLS calculation with insufficient data points."""
        x_values = [1.0, 2.0]
        y_values = [1.0, 2.0]
        
        slope, p_value = calculate_ols_slope_and_pvalue(x_values, y_values)
        
        # With only 2 points, the function returns default values
        assert slope == 0.0  # Returns default slope for insufficient data
        assert p_value == 1.0  # Not enough data for significance


class TestCalculateTrend:
    """Test trend calculation for individual conditions."""
    
    def test_calculate_trend_with_data(self):
        """Test trend calculation with sufficient data.""" 
        settings = Settings()
        
        # Create samples with increasing hot conditions over years
        samples = []
        for year in range(2015, 2025):
            # More hot conditions in later years
            n_hot = min(year - 2015, 5)  # 0 to 5 hot days
            n_normal = 5 - n_hot
            
            # Add hot samples
            for i in range(n_hot):
                samples.append(WeatherSample(
                    temperature_c=45.0, relative_humidity=80.0, wind_speed_ms=5.0,
                    precipitation_mm_per_day=1.0, timestamp=datetime(year, 6, 1 + i),
                    latitude=-3.7, longitude=-38.5
                ))
            
            # Add normal samples
            for i in range(n_normal):
                samples.append(WeatherSample(
                    temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,
                    precipitation_mm_per_day=1.0, timestamp=datetime(year, 6, 10 + i),
                    latitude=-3.7, longitude=-38.5
                ))
        
        trend = calculate_trend(samples, "hot", settings)
        
        assert trend.condition == "hot"
        assert len(trend.points) == 10  # 2015-2024
        assert trend.slope > 0  # Increasing trend
        assert trend.significant  # Should be statistically significant
    
    def test_calculate_trend_insufficient_data(self):
        """Test trend calculation with insufficient data."""
        settings = Settings()
        
        # Only one year of data
        samples = [
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 1),
                latitude=-3.7, longitude=-38.5
            )
        ]
        
        trend = calculate_trend(samples, "hot", settings)
        
        assert trend.condition == "hot"
        assert trend.points == []
        assert trend.slope == 0.0
        assert trend.p_value == 1.0
        assert not trend.significant
    
    def test_calculate_trend_stable_conditions(self):
        """Test trend calculation with stable conditions over time."""
        settings = Settings()
        
        # Same rate each year
        samples = []
        for year in range(2020, 2025):
            # Always 1 hot out of 3 samples each year
            samples.append(WeatherSample(
                temperature_c=45.0, relative_humidity=80.0, wind_speed_ms=5.0,  # Hot
                precipitation_mm_per_day=1.0, timestamp=datetime(year, 6, 1),
                latitude=-3.7, longitude=-38.5
            ))
            for i in range(2):
                samples.append(WeatherSample(
                    temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,  # Normal
                    precipitation_mm_per_day=1.0, timestamp=datetime(year, 6, 2 + i),
                    latitude=-3.7, longitude=-38.5
                ))
        
        trend = calculate_trend(samples, "hot", settings)
        
        assert abs(trend.slope) < 0.1  # Nearly zero slope
        assert not trend.significant  # No significant trend


class TestCalculateAllTrends:
    """Test calculation of trends for all conditions."""
    
    def test_calculate_all_trends_basic(self):
        """Test calculating trends for all condition types."""
        settings = Settings()
        
        samples = [
            WeatherSample(
                temperature_c=25.0, relative_humidity=50.0, wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0, timestamp=datetime(2020, 1, 1),
                latitude=-3.7, longitude=-38.5
            )
        ]
        
        trends = calculate_all_trends(samples, settings)
        
        # Should have trends for all condition types
        condition_types = [t.condition for t in trends]
        expected_conditions = ['hot', 'cold', 'windy', 'wet', 'any']
        
        assert len(trends) == len(expected_conditions)
        for condition in expected_conditions:
            assert condition in condition_types
    
    def test_calculate_all_trends_empty_samples(self):
        """Test calculating trends with empty samples."""
        settings = Settings()
        
        trends = calculate_all_trends([], settings)
        
        # Should still return trends for all conditions (with no data)
        assert len(trends) == 5
        for trend in trends:
            assert trend.points == []
            assert trend.slope == 0.0
            assert not trend.significant