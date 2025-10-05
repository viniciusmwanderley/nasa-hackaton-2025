# ABOUTME: NASA POWER API repository implementation for climate data
# ABOUTME: Handles HTTP requests to NASA POWER API with retry logic and error handling

import asyncio
import random
import time
from typing import List, Dict, Any
import httpx
from ..domain.climate_interfaces import INASAClimateRepository


class NASAClimateRepository(INASAClimateRepository):
    """Repository for fetching climate data from NASA POWER API."""
    
    def __init__(self):
        self.base_url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
        self.community = "RE"
        self.start_year = "2010"
        self.end_year = "2024"
        self.timeout = 45
        self.retries = 4
    
    async def fetch_climatology_data(
        self,
        lat: float,
        lon: float,
        params_list: List[str]
    ) -> Dict[str, Any]:
        """
        Fetch climatology data from NASA POWER API for a single coordinate.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            params_list: List of parameters to request from the API
            
        Returns:
            Dictionary containing the parameter data
            
        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        payload = {
            "start": self.start_year,
            "end": self.end_year,
            "latitude": lat,
            "longitude": lon,
            "community": self.community,
            "parameters": ",".join(params_list),
            "units": "metric",
            "header": "true",
        }
        
        data = await self._http_get_async(self.base_url, params=payload)
        return data.get("properties", {}).get("parameter", {})
    
    async def _http_get_async(self, url: str, params: dict) -> Dict[str, Any]:
        """
        Performs async HTTP GET request with robust error handling and retries.
        
        Args:
            url: The URL to make the request to
            params: Query parameters for the request
            
        Returns:
            JSON response as dictionary
            
        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        async with httpx.AsyncClient() as client:
            for attempt in range(self.retries):
                try:
                    response = await client.get(url, params=params, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    status_code = e.response.status_code if e.response else 'N/A'
                    is_retryable = status_code in (429, 500, 502, 503, 504)
                    if not is_retryable or attempt == self.retries - 1:
                        raise e
                    await asyncio.sleep((2 ** attempt) * random.uniform(0.8, 1.2))
            
            raise RuntimeError("Maximum request attempts exceeded.")