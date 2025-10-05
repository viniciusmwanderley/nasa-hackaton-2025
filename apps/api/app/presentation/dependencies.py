# ABOUTME: Dependency injection container for application services and repositories
# ABOUTME: Provides singleton instances and proper dependency wiring for clean architecture

from functools import lru_cache
from ..domain.interfaces import IWeatherDataRepository, IWeatherAnalysisService
from ..infrastructure import HTTPClient, NASAWeatherDataRepository
from ..application import WeatherAnalysisService


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


@lru_cache()
def get_container() -> Container:
    """Get singleton container instance."""
    return Container()