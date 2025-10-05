# ABOUTME: Domain interfaces for climate energy analysis system
# ABOUTME: Defines abstract contracts for NASA API services and climate analysis

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .climate_entities import ClimateEnergyAnalysisRequest, ClimateEnergyAnalysisResult


class INASAClimateRepository(ABC):
    """Interface for NASA POWER API climate data repository."""
    
    @abstractmethod
    async def fetch_climatology_data(
        self,
        lat: float,
        lon: float,
        params_list: List[str]
    ) -> Dict[str, Any]:
        """Fetch climatology data from NASA POWER API."""
        pass


class IClimateEnergyService(ABC):
    """Interface for climate energy analysis service."""
    
    @abstractmethod
    async def analyze_climate_energy_potential(
        self,
        request: ClimateEnergyAnalysisRequest
    ) -> ClimateEnergyAnalysisResult:
        """Perform climate energy analysis for multiple locations."""
        pass
    
    @abstractmethod
    async def analyze_single_location(
        self, 
        latitude: float, 
        longitude: float
    ) -> 'LocationResult':
        """Perform climate energy analysis for a single location."""
        pass