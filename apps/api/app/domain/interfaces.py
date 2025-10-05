# ABOUTME: Domain interfaces for weather analysis system
# ABOUTME: Defines abstract contracts for external services and repositories

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from .entities import WeatherAnalysisRequest, WeatherAnalysisResult
from .enums import Granularity


class IWeatherDataRepository(ABC):
    """Interface for weather data repository."""
    
    @abstractmethod
    async def fetch_temporal_data(
        self,
        lat: float,
        lon: float,
        granularity: Granularity,
        start_date: date,
        end_date: date,
        parameters: List[str]
    ) -> Dict[str, Any]:
        """Fetch temporal weather data."""
        pass
    
    @abstractmethod
    async def fetch_climatology(
        self,
        lat: float,
        lon: float,
        parameters: List[str]
    ) -> Dict[str, Any]:
        """Fetch climatology data."""
        pass


class IWeatherAnalysisService(ABC):
    """Interface for weather analysis service."""
    
    @abstractmethod
    async def analyze_weather_range(
        self,
        request: WeatherAnalysisRequest
    ) -> WeatherAnalysisResult:
        """Perform weather analysis for a date range."""
        pass