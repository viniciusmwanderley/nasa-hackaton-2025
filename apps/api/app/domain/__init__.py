# ABOUTME: Domain package initialization
# ABOUTME: Exports domain entities, enums, and interfaces for clean architecture

from .entities import (
    WeatherParameter,
    WeatherData,
    WeatherStats,
    WeatherClassifications,
    WeatherAnalysisMeta,
    WeatherAnalysisResult,
    WeatherAnalysisRequest,
)
from .enums import Granularity, AnalysisMode
from .interfaces import IWeatherDataRepository, IWeatherAnalysisService

__all__ = [
    "WeatherParameter",
    "WeatherData", 
    "WeatherStats",
    "WeatherClassifications",
    "WeatherAnalysisMeta",
    "WeatherAnalysisResult",
    "WeatherAnalysisRequest",
    "Granularity",
    "AnalysisMode",
    "IWeatherDataRepository",
    "IWeatherAnalysisService",
]