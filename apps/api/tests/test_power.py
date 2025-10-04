# ABOUTME: Comprehensive test suite for NASA POWER API client
# ABOUTME: Uses VCR for HTTP request recording/replay and offline testing

import asyncio
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
from pathlib import Path

import httpx
import vcr
from vcr.cassette import Cassette

from app.weather.power import (
    PowerClient,
    PowerAPIError,
    PowerAPIRateLimitError, 
    PowerAPIDataError,
    create_power_client
)
from app.config import Settings


# VCR configuration for recording/replaying HTTP requests
vcr_config = vcr.VCR(
    serializer="yaml",
    cassette_library_dir=str(Path(__file__).parent / "cassettes"),
    record_mode="once",  # Record once, then replay
    match_on=["uri", "method"],
    filter_headers=["authorization", "user-agent"],
    decode_compressed_response=True
)


class TestPowerClientInit:
    """Test PowerClient initialization and configuration."""
    
    def test_power_client_default_settings(self):
        """Test PowerClient uses default settings when none provided."""
        client = PowerClient()
        assert client.settings is not None
        assert client.base_url == "https://power.larc.nasa.gov"
        assert client.client is not None
    
    def test_power_client_custom_settings(self):
        """Test PowerClient uses provided settings."""
        settings = Settings(power_base_url="https://custom.api.url")
        client = PowerClient(settings)
        assert client.settings == settings
        assert client.base_url == "https://custom.api.url"
    
    def test_power_client_http_timeout_config(self):
        """Test HTTP client timeout configuration."""
        settings = Settings(timeout_connect_s=5, timeout_read_s=15)
        client = PowerClient(settings)
        timeout = client.client.timeout
        assert timeout.connect == 5
        assert timeout.read == 15
    
    async def test_power_client_context_manager(self):
        """Test PowerClient can be used as async context manager."""
        settings = Settings()
        async with PowerClient(settings) as client:
            assert isinstance(client, PowerClient)
            assert client.client is not None


class TestPowerClientValidation:
    """Test input validation methods."""
    
    @pytest.fixture
    def client(self):
        """Fixture for PowerClient instance."""
        return PowerClient()
    
    @pytest.mark.asyncio
    async def test_get_daily_data_invalid_latitude(self, client):
        """Test validation of latitude bounds."""
        with pytest.raises(ValueError, match="Invalid latitude -91"):
            await client.get_daily_data(-91, 0, date(2023, 1, 1), date(2023, 1, 2))
        
        with pytest.raises(ValueError, match="Invalid latitude 91"):
            await client.get_daily_data(91, 0, date(2023, 1, 1), date(2023, 1, 2))
    
    @pytest.mark.asyncio
    async def test_get_daily_data_invalid_longitude(self, client):
        """Test validation of longitude bounds.""" 
        with pytest.raises(ValueError, match="Invalid longitude -181"):
            await client.get_daily_data(0, -181, date(2023, 1, 1), date(2023, 1, 2))
        
        with pytest.raises(ValueError, match="Invalid longitude 181"):
            await client.get_daily_data(0, 181, date(2023, 1, 1), date(2023, 1, 2))
    
    @pytest.mark.asyncio
    async def test_get_daily_data_invalid_date_range(self, client):
        """Test validation of date range."""
        start = date(2023, 12, 31)
        end = date(2023, 1, 1)
        with pytest.raises(ValueError, match="Start date .* must be <= end date"):
            await client.get_daily_data(0, 0, start, end)
    
    def test_validate_response_data_missing_properties(self, client):
        """Test validation fails when properties missing."""
        invalid_data = {"some": "other_data"}
        with pytest.raises(PowerAPIDataError, match="Missing 'properties'"):
            client._validate_response_data(invalid_data)
    
    def test_validate_response_data_missing_parameter(self, client):
        """Test validation fails when parameter data missing."""
        invalid_data = {"properties": {"other": "data"}}
        with pytest.raises(PowerAPIDataError, match="Missing 'parameter' data"):
            client._validate_response_data(invalid_data)
    
    def test_validate_response_data_accepts_any_parameters(self, client):
        """Test validation accepts any parameters (allows custom parameter requests)."""
        data_with_subset = {
            "properties": {
                "parameter": {
                    "T2M": {"20230101": 25.5}  # Only T2M, which is valid for custom requests
                }
            }
        }
        # Should not raise any exception
        client._validate_response_data(data_with_subset)
    
    def test_validate_response_data_api_error(self, client):
        """Test validation fails when API returns error."""
        error_data = {"error": "Invalid request parameters"}
        with pytest.raises(PowerAPIDataError, match="POWER API error: Invalid request"):
            client._validate_response_data(error_data)


class TestPowerClientHTTPRequests:
    """Test HTTP request handling and error scenarios."""
    
    @pytest.fixture
    def client(self):
        """Fixture for PowerClient instance."""
        return PowerClient()
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self, client):
        """Test handling of 429 rate limit errors."""
        # Create mock for rate limit response
        mock_response = AsyncMock()
        mock_response.status_code = 429
        
        async def mock_get(*args, **kwargs):
            return mock_response
        
        with patch.object(client.client, "get", side_effect=mock_get):
            with pytest.raises(PowerAPIRateLimitError, match="rate limit exceeded"):
                await client._make_request("http://test.com", {})
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, client):
        """Test handling of other HTTP errors."""
        # Create mock request and response objects  
        mock_request = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        
        # Mock the get method to raise HTTPStatusError
        async def mock_get(*args, **kwargs):
            raise httpx.HTTPStatusError("Server error", request=mock_request, response=mock_response)
        
        with patch.object(client.client, "get", side_effect=mock_get):
            with pytest.raises(PowerAPIError, match="POWER API request failed: 500"):
                await client._make_request("http://test.com", {})
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, client):
        """Test handling of connection errors."""
        async def mock_get(*args, **kwargs):
            raise httpx.ConnectError("Connection failed")
        
        with patch.object(client.client, "get", side_effect=mock_get):
            with pytest.raises(PowerAPIError, match="POWER API connection failed"):
                await client._make_request("http://test.com", {})


class TestPowerClientRealAPI:
    """Test PowerClient with real NASA POWER API (recorded with VCR)."""
    
    @vcr_config.use_cassette("power_api_fortaleza_sample.yaml")
    @pytest.mark.asyncio
    async def test_get_daily_data_fortaleza_week(self):
        """Test fetching a week of data for Fortaleza, Brazil."""
        client = PowerClient()
        
        # Fortaleza coordinates
        latitude = -3.7275
        longitude = -38.5275
        start_date = date(2023, 6, 1)
        end_date = date(2023, 6, 7)
        
        try:
            data = await client.get_daily_data(latitude, longitude, start_date, end_date)
            
            # Validate response structure
            assert "properties" in data
            assert "parameter" in data["properties"]
            
            parameters = data["properties"]["parameter"]
            
            # Check all required parameters are present
            for param in PowerClient.REQUIRED_PARAMS:
                assert param in parameters, f"Missing parameter: {param}"
                
                # Check we have data for the date range
                param_data = parameters[param]
                assert len(param_data) == 7, f"Expected 7 days of {param} data"
                
                # Check data values are reasonable
                for date_str, value in param_data.items():
                    assert isinstance(value, (int, float)), f"Invalid {param} value type: {type(value)}"
                    
                    # Basic sanity checks for parameter ranges
                    if param == "T2M":  # Temperature
                        assert -50 <= value <= 60, f"Temperature {value}°C seems unrealistic"
                    elif param == "RH2M":  # Humidity
                        assert 0 <= value <= 100, f"Humidity {value}% out of valid range"
                    elif param == "WS10M":  # Wind speed
                        assert 0 <= value <= 100, f"Wind speed {value} m/s seems unrealistic"
                    elif param == "PRECTOTCORR":  # Precipitation
                        assert value >= 0, f"Negative precipitation {value} mm/day invalid"
        
        finally:
            await client.close()
    
    @vcr_config.use_cassette("power_api_custom_params.yaml")
    @pytest.mark.asyncio
    async def test_get_daily_data_custom_parameters(self):
        """Test fetching data with custom parameter subset."""
        client = PowerClient()
        
        # Only temperature and humidity
        custom_params = ["T2M", "RH2M"]
        
        try:
            data = await client.get_daily_data(
                -3.7275, -38.5275,
                date(2023, 6, 1), date(2023, 6, 2),
                parameters=custom_params
            )
            
            parameters = data["properties"]["parameter"]
            
            # Should only have the requested parameters
            assert set(parameters.keys()) == set(custom_params)
            
            # Validate we have data
            assert "T2M" in parameters
            assert "RH2M" in parameters
            assert len(parameters["T2M"]) == 2  # 2 days
            assert len(parameters["RH2M"]) == 2  # 2 days
            
        finally:
            await client.close()


class TestPowerClientFactory:
    """Test factory function for creating PowerClient instances."""
    
    @pytest.mark.asyncio
    async def test_create_power_client_default(self):
        """Test factory creates client with default settings."""
        client = await create_power_client()
        assert isinstance(client, PowerClient)
        assert client.settings is not None
    
    @pytest.mark.asyncio
    async def test_create_power_client_custom_settings(self):
        """Test factory creates client with custom settings."""
        settings = Settings(power_base_url="https://custom.url")
        client = await create_power_client(settings)
        assert isinstance(client, PowerClient)
        assert client.settings == settings
        assert client.base_url == "https://custom.url"


class TestPowerClientEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def client(self):
        return PowerClient()
    
    @pytest.mark.asyncio
    async def test_single_day_request(self, client):
        """Test requesting data for a single day."""
        # Mock successful response for single day
        mock_data = {
            "properties": {
                "parameter": {
                    "T2M": {"20230601": 28.5},
                    "RH2M": {"20230601": 75.2},
                    "WS10M": {"20230601": 3.1},
                    "PRECTOTCORR": {"20230601": 0.0}
                }
            }
        }
        
        with patch.object(client, "_make_request", return_value=mock_data):
            data = await client.get_daily_data(
                0, 0, date(2023, 6, 1), date(2023, 6, 1)
            )
            assert "properties" in data
            assert len(data["properties"]["parameter"]["T2M"]) == 1
    
    @pytest.mark.asyncio  
    async def test_boundary_coordinates(self, client):
        """Test requests at coordinate boundaries."""
        mock_data = {
            "properties": {
                "parameter": {
                    "T2M": {"20230601": 25.0},
                    "RH2M": {"20230601": 80.0},
                    "WS10M": {"20230601": 2.0},
                    "PRECTOTCORR": {"20230601": 1.5}
                }
            }
        }
        
        with patch.object(client, "_make_request", return_value=mock_data):
            # Test extreme coordinates
            await client.get_daily_data(90, 180, date(2023, 6, 1), date(2023, 6, 1))
            await client.get_daily_data(-90, -180, date(2023, 6, 1), date(2023, 6, 1))
            await client.get_daily_data(0, 0, date(2023, 6, 1), date(2023, 6, 1))