# ABOUTME: Unit tests for weather data service functionality
# ABOUTME: Tests NASA POWER API integration, data processing, and statistical calculations

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
import numpy as np

from app.services.weather_service import WeatherDataService
from app.models.weather import Granularity


class TestWeatherDataService:
    """Test suite for WeatherDataService."""
    
    def setup_method(self):
        """Set up test instance."""
        self.service = WeatherDataService()
    
    def test_extract_param_series_valid_data(self):
        """Test extraction of parameter series from API response."""
        api_response = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20251225": 28.5,
                        "20251224": -999,  # Should be converted to None
                        "20251223": 29.2
                    }
                }
            }
        }
        
        result = self.service.extract_param_series(api_response)
        
        assert "T2M" in result
        t2m_data = result["T2M"]
        assert t2m_data["20251225"] == 28.5
        assert t2m_data["20251224"] is None  # -999 converted to None
        assert t2m_data["20251223"] == 29.2
    
    def test_extract_param_series_empty_response(self):
        """Test extraction with empty or malformed response."""
        empty_response = {}
        result = self.service.extract_param_series(empty_response)
        assert result == {}
        
        malformed_response = {"properties": {}}
        result = self.service.extract_param_series(malformed_response)
        assert result == {}
    
    def test_basic_stats_valid_values(self):
        """Test basic statistics calculation with valid values."""
        values = [25.0, 27.5, 30.0, 28.0, 26.5]
        stats = self.service.basic_stats(values)
        
        assert stats["count"] == 5
        assert abs(stats["mean"] - 27.4) < 0.1
        assert stats["min"] == 25.0
        assert stats["max"] == 30.0
        assert stats["std"] > 0
        assert stats["median"] == 27.5
    
    def test_basic_stats_with_none_values(self):
        """Test basic statistics with None and NaN values."""
        values = [25.0, None, 30.0, float('nan'), 28.0]
        stats = self.service.basic_stats(values)
        
        assert stats["count"] == 3  # Only valid values counted
        expected_mean = (25.0 + 30.0 + 28.0) / 3
        assert abs(stats["mean"] - expected_mean) < 0.1
    
    def test_basic_stats_empty_values(self):
        """Test basic statistics with empty list."""
        values = []
        stats = self.service.basic_stats(values)
        
        for key in ["count", "mean", "median", "min", "max", "std"]:
            assert np.isnan(stats[key])
    
    def test_calculate_heat_index_valid_conditions(self):
        """Test heat index calculation under valid conditions."""
        temp_c = 35.0
        rh_percent = 70.0
        
        heat_index = self.service.calculate_heat_index(temp_c, rh_percent)
        
        assert heat_index is not None
        assert heat_index > temp_c  # Heat index should be higher than actual temp
    
    def test_calculate_heat_index_low_temp(self):
        """Test heat index calculation with low temperature."""
        temp_c = 20.0  # Below 26.7C threshold
        rh_percent = 70.0
        
        heat_index = self.service.calculate_heat_index(temp_c, rh_percent)
        
        assert heat_index == temp_c  # Should return actual temperature
    
    def test_calculate_heat_index_low_humidity(self):
        """Test heat index calculation with low humidity."""
        temp_c = 30.0
        rh_percent = 30.0  # Below 40% threshold
        
        heat_index = self.service.calculate_heat_index(temp_c, rh_percent)
        
        assert heat_index == temp_c  # Should return actual temperature
    
    def test_calculate_heat_index_invalid_inputs(self):
        """Test heat index calculation with invalid inputs."""
        # None values
        assert self.service.calculate_heat_index(None, 70.0) is None
        assert self.service.calculate_heat_index(30.0, None) is None
        
        # NaN values
        assert self.service.calculate_heat_index(float('nan'), 70.0) is None
        assert self.service.calculate_heat_index(30.0, float('nan')) is None
    
    def test_filter_series_by_datetime_daily(self):
        """Test filtering time series for daily granularity."""
        target_dt = datetime(2025, 12, 25, 14, 0)  # Day of year: 359
        window_days = 1
        
        series = {
            "20251224": 25.0,  # Day 358 - should be included
            "20251225": 28.0,  # Day 359 - should be included
            "20251226": 30.0,  # Day 360 - should be included
            "20251220": 22.0,  # Day 354 - should not be included
        }
        
        values = self.service.filter_series_by_datetime(
            series, target_dt, Granularity.DAILY, window_days
        )
        
        assert len(values) == 3
        assert 25.0 in values
        assert 28.0 in values
        assert 30.0 in values
        assert 22.0 not in values
    
    def test_filter_series_by_datetime_hourly(self):
        """Test filtering time series for hourly granularity."""
        target_dt = datetime(2025, 12, 25, 14, 0)  # Hour 14
        window_days = 1
        
        series = {
            "2025122414": 28.0,  # Same day, same hour - should be included
            "2025122414": 27.5,  # Same day, same hour - should be included
            "2025122413": 26.0,  # Same day, different hour - should not be included
            "2025122514": 29.0,  # Next day, same hour - should be included
        }
        
        values = self.service.filter_series_by_datetime(
            series, target_dt, Granularity.HOURLY, window_days
        )
        
        # Should only include values from hour 14
        assert all(v in [27.5, 28.0, 29.0] for v in values)
        assert 26.0 not in values
    
    @patch('app.services.weather_service.requests.Session.get')
    def test_http_get_success(self, mock_get):
        """Test successful HTTP GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.url = "https://test.com"
        mock_get.return_value = mock_response
        
        result = self.service.http_get("https://test.com", {"param": "value"})
        
        assert result == {"test": "data"}
        mock_get.assert_called_once()
    
    @patch('app.services.weather_service.requests.Session.get')
    def test_http_get_retry_on_server_error(self, mock_get):
        """Test HTTP GET retry on server error."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server Error"
        mock_response_fail.raise_for_status.side_effect = Exception("Server Error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"test": "data"}
        mock_response_success.url = "https://test.com"
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.service.http_get("https://test.com", {"param": "value"})
        
        assert result == {"test": "data"}
        assert mock_get.call_count == 2
    
    @patch('app.services.weather_service.requests.Session.get')
    def test_http_get_max_retries_exceeded(self, mock_get):
        """Test HTTP GET when max retries are exceeded."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_response.raise_for_status.side_effect = Exception("Server Error")
        mock_get.return_value = mock_response
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(Exception, match="Server Error"):
                self.service.http_get("https://test.com", {"param": "value"}, retries=2)
        
        assert mock_get.call_count == 2


class TestWeatherDataServiceIntegration:
    """Integration tests for WeatherDataService."""
    
    def setup_method(self):
        """Set up test instance."""
        self.service = WeatherDataService()
    
    @patch('app.services.weather_service.WeatherDataService.http_get')
    def test_fetch_temporal_data_daily(self, mock_http_get):
        """Test fetching daily temporal data."""
        mock_response = {
            "properties": {
                "parameter": {
                    "T2M": {"20251225": 28.5}
                }
            }
        }
        mock_http_get.return_value = mock_response
        
        result = self.service.fetch_temporal_data(
            lat=-7.115,
            lon=-34.863,
            granularity=Granularity.DAILY,
            start_date=date(2025, 12, 25),
            end_date=date(2025, 12, 25),
            parameters=["T2M"]
        )
        
        assert result == mock_response
        mock_http_get.assert_called_once()
        
        # Check that correct URL was called
        args, kwargs = mock_http_get.call_args
        assert "daily/point" in args[0]
    
    @patch('app.services.weather_service.WeatherDataService.http_get')
    def test_fetch_climatology(self, mock_http_get):
        """Test fetching climatology data."""
        mock_response = {
            "properties": {
                "parameter": {
                    "T2M": {"12": 27.2}
                }
            }
        }
        mock_http_get.return_value = mock_response
        
        result = self.service.fetch_climatology(
            lat=-7.115,
            lon=-34.863,
            parameters=["T2M"]
        )
        
        assert result == mock_response
        mock_http_get.assert_called_once()
        
        # Check that correct URL was called
        args, kwargs = mock_http_get.call_args
        assert "climatology/point" in args[0]