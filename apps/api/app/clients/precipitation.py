"""
Precipitation data client with IMERG primary and POWER fallback.

This module provides a unified interface for precipitation data that tries
IMERG first and falls back to POWER data when IMERG is unavailable.
"""

import logging
from datetime import datetime
from typing import List, Optional, Union

from app.clients.imerg import ImergClient, ImergHourlyData, create_imerg_client
from app.weather.power import PowerClient, create_power_client
from app.config import Settings

logger = logging.getLogger(__name__)


class PrecipitationData(ImergHourlyData):
    """
    Unified precipitation data structure.
    
    Extends IMERG data structure to handle both IMERG and POWER sources.
    """
    pass


class PrecipitationClient:
    """
    Unified precipitation client with IMERG primary and POWER fallback.
    
    This client attempts to get precipitation data from IMERG first,
    and falls back to POWER data if IMERG is unavailable or fails.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize precipitation client."""
        self.settings = settings or Settings()
        self.imerg_client = create_imerg_client(settings)
        # Note: PowerClient will be created in __aenter__ since create_power_client is async
        self.power_client = None
        
        # Fallback configuration
        self.enable_imerg = getattr(settings, 'enable_imerg', True) if settings else True
        self.enable_fallback = getattr(settings, 'enable_precipitation_fallback', True) if settings else True
    
    async def _ensure_power_client(self):
        """Ensure power client is initialized."""
        if self.power_client is None:
            self.power_client = await create_power_client(self.settings)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.imerg_client.__aenter__()
        # Create PowerClient asynchronously
        self.power_client = await create_power_client(self.settings)
        await self.power_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.imerg_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.power_client:
            await self.power_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_hourly_precipitation(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        timezone: str = "UTC"
    ) -> List[PrecipitationData]:
        """
        Get hourly precipitation data with IMERG primary and POWER fallback.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date to retrieve data for  
            timezone: Target timezone for data
            
        Returns:
            List of hourly precipitation data
        """
        precipitation_data = []
        
        # Try IMERG first if enabled
        if self.enable_imerg:
            try:
                logger.info(f"Attempting IMERG data for {latitude:.2f}, {longitude:.2f}, {date.date()}")
                imerg_data = await self.imerg_client.get_hourly_precipitation(
                    latitude, longitude, date, timezone
                )
                
                if imerg_data:
                    logger.info(f"Successfully retrieved {len(imerg_data)} hourly IMERG data points")
                    # Convert to unified format
                    precipitation_data = [
                        PrecipitationData(
                            hour=data.hour,
                            total_mm=data.total_mm,
                            avg_rate_mm_hr=data.avg_rate_mm_hr,
                            data_points=data.data_points,
                            quality_score=data.quality_score,
                            source="IMERG"
                        ) for data in imerg_data
                    ]
                    return precipitation_data
                else:
                    logger.warning("IMERG returned no data")
                    
            except Exception as e:
                logger.error(f"IMERG data retrieval failed: {e}")
        
        # Fallback to POWER if IMERG failed or is disabled
        if self.enable_fallback:
            try:
                await self._ensure_power_client()
                logger.info(f"Falling back to POWER data for {latitude:.2f}, {longitude:.2f}, {date.date()}")
                power_data = await self.power_client.get_daily_data(
                    latitude, longitude, date, date
                )
                
                if power_data and power_data.data:
                    daily_precip = power_data.data[0].precipitation_mm or 0.0
                    
                    # Distribute daily precipitation across 24 hours
                    # Simple approach: assume uniform distribution for now
                    hourly_rate = daily_precip / 24.0
                    
                    precipitation_data = []
                    for hour in range(24):
                        precipitation_data.append(PrecipitationData(
                            hour=hour,
                            total_mm=hourly_rate,
                            avg_rate_mm_hr=hourly_rate,
                            data_points=1,
                            quality_score=0.8,  # Lower quality than IMERG
                            source="POWER_fallback"
                        ))
                    
                    logger.info(f"Successfully retrieved POWER fallback data: {daily_precip:.2f} mm/day")
                    return precipitation_data
                else:
                    logger.warning("POWER fallback returned no data")
                    
            except Exception as e:
                logger.error(f"POWER fallback failed: {e}")
        
        # If both sources failed, return empty list
        logger.error("Both IMERG and POWER precipitation sources failed")
        return []
    
    async def get_precipitation_for_hour(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        hour: int,
        timezone: str = "UTC"
    ) -> Optional[PrecipitationData]:
        """
        Get precipitation data for a specific hour.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date to retrieve data for
            hour: Hour of day (0-23) 
            timezone: Target timezone
            
        Returns:
            Precipitation data for the specified hour or None
        """
        hourly_data = await self.get_hourly_precipitation(
            latitude, longitude, date, timezone
        )
        
        for data in hourly_data:
            if data.hour == hour:
                return data
        
        return None
    
    async def check_data_availability(
        self,
        latitude: float,
        longitude: float,
        date: datetime
    ) -> dict:
        """
        Check availability of precipitation data from different sources.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date to check
            
        Returns:
            Dictionary with availability status for each source
        """
        availability = {
            'imerg': False,
            'power': False,
            'any_available': False
        }
        
        # Check IMERG availability
        if self.enable_imerg:
            try:
                imerg_data = await self.imerg_client.get_half_hourly_data(
                    latitude, longitude, date
                )
                availability['imerg'] = bool(imerg_data and imerg_data.data)
            except Exception as e:
                logger.debug(f"IMERG availability check failed: {e}")
        
        # Check POWER availability  
        try:
            await self._ensure_power_client()
            power_data = await self.power_client.get_daily_data(
                latitude, longitude, date, date
            )
            availability['power'] = bool(power_data and power_data.data)
        except Exception as e:
            logger.debug(f"POWER availability check failed: {e}")
        
        availability['any_available'] = availability['imerg'] or availability['power']
        
        return availability


def create_precipitation_client(settings: Optional[Settings] = None) -> PrecipitationClient:
    """Factory function to create precipitation client."""
    return PrecipitationClient(settings)