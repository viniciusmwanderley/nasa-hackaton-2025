# ABOUTME: NASA POWER API repository implementation
# ABOUTME: Handles data fetching from NASA POWER API with proper error handling and data extraction

import logging
from datetime import date
from typing import Dict, List, Any, Optional
from ..domain.interfaces import IWeatherDataRepository
from ..domain.enums import Granularity
from .config import BASE_URL, API_PATHS, DEFAULT_COMMUNITY
from .http_client import HTTPClient


logger = logging.getLogger("outdoor_risk_api.nasa_repository")


class NASAWeatherDataRepository(IWeatherDataRepository):    
    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
    
    async def fetch_temporal_data(
        self,
        lat: float,
        lon: float,
        granularity: Granularity,
        start_date: date,
        end_date: date,
        parameters: List[str]
    ) -> Dict[str, Any]:
        """        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            granularity: Data granularity (daily/hourly)
            start_date: Start date for data
            end_date: End date for data
            parameters: List of weather parameters to fetch
            
        Returns:
            Raw API response as dictionary
        """
        if not parameters:
            logger.warning("No parameters provided for temporal data fetch")
            return {}
            
        path = API_PATHS[granularity]
        url = f"{BASE_URL}/{path}"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "parameters": ",".join(parameters),
            "community": DEFAULT_COMMUNITY,
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "format": "JSON",
            "time-standard": "UTC"
        }
        
        logger.info(
            "Fetching temporal data from NASA API",
            extra={
                "lat": lat,
                "lon": lon,
                "granularity": granularity.value,
                "date_range": f"{start_date} to {end_date}",
                "parameters": parameters
            }
        )
        
        return await self.http_client.get(url, params)
    
    async def fetch_climatology(
        self,
        lat: float,
        lon: float,
        parameters: List[str]
    ) -> Dict[str, Any]:
        """        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            parameters: List of weather parameters to fetch
            
        Returns:
            Raw API response as dictionary
        """
        path = API_PATHS["climatology"]
        url = f"{BASE_URL}/{path}"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "parameters": ",".join(parameters),
            "community": DEFAULT_COMMUNITY,
            "format": "JSON"
        }
        
        logger.info(
            "Fetching climatology data from NASA API",
            extra={
                "lat": lat,
                "lon": lon,
                "parameters": parameters
            }
        )
        
        return await self.http_client.get(url, params)
    
    def extract_param_series(self, json_obj: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """        
        Args:
            json_obj: Raw API response
            
        Returns:
            Dictionary mapping parameters to their time series data
        """
        try:
            params = json_obj.get("properties", {}).get("parameter", {})
            for param, series in params.items():
                for date_key, value in series.items():
                    if value == -999:
                        series[date_key] = None
            return params
        except KeyError as e:
            logger.error(f"Error extracting parameter series: {e}")
            return {}
    
    def extract_climatology_monthly(self, json_obj: Dict[str, Any]) -> Dict[str, Dict[int, float]]:
        """        
        Args:
            json_obj: Raw API response
            
        Returns:
            Dictionary mapping parameters to monthly averages
        """
        import datetime as dt
        
        param_series = self.extract_param_series(json_obj)
        result = {}
        
        for param, monthly_data in param_series.items():
            month_map = {}
            for month_key, value in monthly_data.items():
                if month_key.isdigit() and 1 <= int(month_key) <= 12:
                    month_num = int(month_key)
                elif len(month_key) == 3 and month_key.isalpha() and month_key != "ANN":
                    try:
                        month_num = dt.datetime.strptime(month_key, "%b").month
                    except ValueError:
                        continue
                else:
                    continue
                
                if value is not None:
                    month_map[month_num] = float(value)
            
            result[param] = month_map
        
        return result