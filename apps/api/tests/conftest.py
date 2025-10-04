# ABOUTME: Test configuration and fixtures for the outdoor risk API
# ABOUTME: Provides shared test setup and mock data for comprehensive testing

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.weather import Granularity, WeatherCondition


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_request_data():
    """Sample request data for weather analysis."""
    return {
        "latitude": -7.115,
        "longitude": -34.863,
        "target_datetime": "2025-12-25T14:00:00",
        "granularity": "hourly",
        "start_year": 2005,
        "window_days": 7
    }


@pytest.fixture
def sample_nasa_response():
    """Mock NASA POWER API response."""
    return {
        "properties": {
            "parameter": {
                "T2M": {
                    "20251225": 28.5,
                    "20251224": 27.8,
                    "20251223": 29.2
                },
                "RH2M": {
                    "20251225": 65.0,
                    "20251224": 70.0,
                    "20251223": 60.0
                },
                "WS10M": {
                    "20251225": 12.0,
                    "20251224": 8.5,
                    "20251223": 15.2
                },
                "PRECTOTCORR": {
                    "20251225": 5.0,
                    "20251224": 0.0,
                    "20251223": 2.5
                }
            }
        }
    }


@pytest.fixture
def sample_climatology_response():
    """Mock climatology response."""
    return {
        "properties": {
            "parameter": {
                "T2M": {
                    "12": 27.2,  # December average
                    "ANN": 26.8
                },
                "RH2M": {
                    "12": 68.0,
                    "ANN": 65.0
                },
                "WS10M": {
                    "12": 10.5,
                    "ANN": 9.8
                },
                "PRECTOTCORR": {
                    "12": 15.2,
                    "ANN": 12.5
                }
            }
        }
    }


@pytest.fixture
def mock_weather_service():
    """Mock weather service for testing."""
    with patch('app.services.weather_service.WeatherDataService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        
        # Mock analysis result
        mock_instance.analyze_weather.return_value = {
            "meta": {
                "latitude": -7.115,
                "longitude": -34.863,
                "target_datetime": "2025-12-25T14:00:00",
                "granularity": "hourly",
                "analysis_mode": "probabilistic",
                "historical_data_range": ["2005-01-01", "2025-10-04"],
                "window_days_used": 7
            },
            "derived_insights": {
                "heat_index": {
                    "mean_heat_index_c": 30.2,
                    "p90_heat_index_c": 34.5,
                    "note": "Heat index calculated for T>=26.7C and RH>=40%."
                }
            },
            "parameters": {
                "T2M": {
                    "mode": "probabilistic",
                    "climatology_month_mean": 27.2,
                    "stats": {
                        "count": 150,
                        "mean": 28.1,
                        "median": 27.8,
                        "min": 24.5,
                        "max": 32.3,
                        "std": 2.1,
                        "p10": 25.8,
                        "p25": 26.7,
                        "p75": 29.4,
                        "p90": 31.2
                    },
                    "sample_size": 150
                },
                "RH2M": {
                    "mode": "probabilistic",
                    "climatology_month_mean": 68.0,
                    "stats": {
                        "count": 150,
                        "mean": 65.0,
                        "median": 65.5,
                        "min": 45.0,
                        "max": 85.0,
                        "std": 8.5,
                        "p10": 52.0,
                        "p25": 58.5,
                        "p75": 72.0,
                        "p90": 78.0
                    },
                    "sample_size": 150
                },
                "WS10M": {
                    "mode": "probabilistic",
                    "climatology_month_mean": 10.5,
                    "stats": {
                        "count": 150,
                        "mean": 11.2,
                        "median": 10.8,
                        "min": 3.2,
                        "max": 18.5,
                        "std": 3.8,
                        "p10": 6.5,
                        "p25": 8.2,
                        "p75": 14.1,
                        "p90": 16.8
                    },
                    "sample_size": 150
                },
                "PRECTOTCORR": {
                    "mode": "probabilistic",
                    "climatology_month_mean": 15.2,
                    "stats": {
                        "count": 120,
                        "mean": 8.5,
                        "median": 2.0,
                        "min": 0.0,
                        "max": 45.0,
                        "std": 12.8,
                        "p10": 0.0,
                        "p25": 0.0,
                        "p75": 12.0,
                        "p90": 28.0
                    },
                    "sample_size": 120
                }
            }
        }
        
        yield mock_instance