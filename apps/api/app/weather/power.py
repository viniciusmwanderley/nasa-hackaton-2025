# ABOUTME: NASA POWER API client with retry logic and error handling
# ABOUTME: Fetches meteorological data for outdoor risk assessment calculations

import asyncio
import logging
from datetime import date
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..config import Settings

logger = logging.getLogger(__name__)


class PowerAPIError(Exception):
    """Base exception for NASA POWER API errors."""
    pass


class PowerAPIRateLimitError(PowerAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class PowerAPIDataError(PowerAPIError):
    """Raised when API returns invalid or missing data."""
    pass


class PowerClient:
    """
    NASA POWER API client with automatic retries and error handling.
    
    Provides meteorological data for outdoor risk assessment including:
    - Temperature (T2M)
    - Relative humidity (RH2M) 
    - Wind speed (WS10M)
    - Precipitation (PRECTOTCORR)
    """
    
    # NASA POWER parameters we need for risk calculations
    REQUIRED_PARAMS = [
        "T2M",           # Temperature at 2m (°C)
        "RH2M",          # Relative humidity at 2m (%)
        "WS10M",         # Wind speed at 10m (m/s)
        "PRECTOTCORR",   # Precipitation corrected (mm/day)
    ]
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize POWER client with configuration."""
        self.settings = settings or Settings()
        self.base_url = self.settings.power_base_url
        
        # HTTP client with timeouts
        timeout = httpx.Timeout(
            connect=self.settings.timeout_connect_s,
            read=self.settings.timeout_read_s,
            write=30.0,  # Default write timeout
            pool=10.0    # Default pool timeout
        )
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "outdoor-risk-api/0.1.0 (NASA Hackathon 2025)"
            }
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request with automatic retries.
        
        Args:
            url: Full API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            PowerAPIRateLimitError: When rate limited
            PowerAPIError: For other API errors
        """
        try:
            logger.debug(f"Making POWER API request to {url} with params: {params}")
            response = await self.client.get(url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                raise PowerAPIRateLimitError("NASA POWER API rate limit exceeded")
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"POWER API response received: {len(str(data))} chars")
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"POWER API HTTP error {e.response.status_code}: {e.response.text}")
            raise PowerAPIError(f"POWER API request failed: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"POWER API request error: {e}")
            raise PowerAPIError(f"POWER API connection failed: {e}")
    
    def _validate_response_data(self, data: Dict[str, Any]) -> None:
        """
        Validate NASA POWER API response structure.
        
        Args:
            data: API response JSON
            
        Raises:
            PowerAPIDataError: If response is invalid
        """
        # Check for API error messages
        if "error" in data:
            raise PowerAPIDataError(f"POWER API error: {data['error']}")
        
        # Check required structure
        if "properties" not in data:
            raise PowerAPIDataError("Missing 'properties' in POWER API response")
        
        properties = data["properties"]
        if "parameter" not in properties:
            raise PowerAPIDataError("Missing 'parameter' data in POWER API response")
        
        # Don't validate required params if custom parameters were specified
        # (client may want subset of parameters)
        parameters = properties["parameter"]
    
    async def get_daily_data(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch daily meteorological data from NASA POWER API.
        
        Args:
            latitude: Latitude in decimal degrees (-90 to 90)
            longitude: Longitude in decimal degrees (-180 to 180)
            start_date: Start date for data range
            end_date: End date for data range  
            parameters: List of parameters to fetch (defaults to REQUIRED_PARAMS)
            
        Returns:
            NASA POWER API response with daily meteorological data
            
        Raises:
            PowerAPIError: For API errors
            PowerAPIDataError: For invalid response data
            ValueError: For invalid input parameters
        """
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude {latitude}: must be -90 to 90")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude {longitude}: must be -180 to 180")
        
        # Validate date range
        if start_date > end_date:
            raise ValueError(f"Start date {start_date} must be <= end date {end_date}")
        
        # Use default parameters if none specified
        if parameters is None:
            parameters = self.REQUIRED_PARAMS
        
        # Build API request
        url = urljoin(self.base_url, "/api/temporal/daily/point")
        params = {
            "parameters": ",".join(parameters),
            "community": "AG",  # Agroclimatology community
            "longitude": longitude,
            "latitude": latitude,
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "format": "JSON"
        }
        
        logger.info(
            f"Fetching POWER data for ({latitude}, {longitude}) "
            f"from {start_date} to {end_date}"
        )
        
        # Make request with retries
        data = await self._make_request(url, params)
        
        # Validate response
        self._validate_response_data(data)
        
        return data
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def create_power_client(settings: Optional[Settings] = None) -> PowerClient:
    """
    Factory function to create a POWER client.
    
    Args:
        settings: Optional settings override
        
    Returns:
        Configured PowerClient instance
    """
    return PowerClient(settings)