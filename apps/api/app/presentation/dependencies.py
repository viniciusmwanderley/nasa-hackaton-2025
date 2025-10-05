# ABOUTME: Dependency injection container for application services and repositories
# ABOUTME: Provides singleton instances and proper dependency wiring for clean architecture

from functools import lru_cache
from ..domain.interfaces import IWeatherDataRepository, IWeatherAnalysisService
from ..domain.climate_interfaces import INASAClimateRepository, IClimateEnergyService
from ..infrastructure import HTTPClient, NASAWeatherDataRepository
from ..infrastructure.nasa_climate_repository import NASAClimateRepository
from ..application import WeatherAnalysisService
from ..application.climate_energy_service import ClimateEnergyService


class Container:
    """Dependency injection container for application services."""
    
    def __init__(self):
        self._http_client = None
        self._weather_repo = None
        self._weather_service = None
    
    @property
    def http_client(self) -> HTTPClient:
        """Get HTTP client instance."""
        if self._http_client is None:
            self._http_client = HTTPClient()
        return self._http_client
    
    @property
    def weather_repository(self) -> IWeatherDataRepository:
        """Get weather data repository instance."""
        if self._weather_repo is None:
            self._weather_repo = NASAWeatherDataRepository(self.http_client)
        return self._weather_repo
    
    @property
    def weather_service(self) -> IWeatherAnalysisService:
        """Get weather analysis service instance."""
        if self._weather_service is None:
            self._weather_service = WeatherAnalysisService(self.weather_repository)
        return self._weather_service


class ClimateContainer:
    """Dependency injection container for climate energy analysis services."""
    
    def __init__(self):
        self._nasa_climate_repo = None
        self._climate_service = None
    
    @property
    def nasa_climate_repository(self) -> INASAClimateRepository:
        """Get NASA climate repository instance."""
        if self._nasa_climate_repo is None:
            self._nasa_climate_repo = NASAClimateRepository()
        return self._nasa_climate_repo
    
    @property
    def climate_service(self) -> IClimateEnergyService:
        """Get climate energy analysis service instance."""
        if self._climate_service is None:
            self._climate_service = ClimateEnergyService(self.nasa_climate_repository)
        return self._climate_service


@lru_cache()
def get_container() -> Container:
    """Get singleton container instance."""
    return Container()


@lru_cache()
def get_climate_container() -> ClimateContainer:
    """Get singleton climate container instance."""
    return ClimateContainer()