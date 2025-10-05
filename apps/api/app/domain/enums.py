# ABOUTME: Domain enums for weather analysis system configuration
# ABOUTME: Defines granularity and analysis mode types used throughout the application

from enum import Enum


class Granularity(Enum):
    """Weather data granularity options."""
    DAILY = "daily"
    HOURLY = "hourly"


class AnalysisMode(Enum):
    """Analysis mode for weather data processing."""
    OBSERVED = "observed"
    PROBABILISTIC = "probabilistic"