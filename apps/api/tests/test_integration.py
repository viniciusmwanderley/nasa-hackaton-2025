# ABOUTME: End-to-end integration tests for the complete outdoor risk assessment API
# ABOUTME: Tests full workflow from API request to weather analysis and risk classification

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.main import app


class TestOutdoorRiskAPIIntegration:
    """Integration tests for the complete outdoor risk assessment workflow."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    @patch('app.services.weather_service.WeatherDataService.http_get')
    def test_complete_weather_analysis_workflow(self, mock_http_get):
        """Test the complete workflow from request to classification."""
        
        # Mock NASA POWER API responses
        temporal_response = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "2025122414": 36.5,  # Very hot
                        "2025122314": 35.2,
                        "2025122214": 34.8,
                        "2024122414": 37.1,
                        "2023122414": 33.9
                    },
                    "RH2M": {
                        "2025122414": 75.0,
                        "2025122314": 72.0,
                        "2025122214": 68.0,
                        "2024122414": 78.0,
                        "2023122414": 70.0
                    },
                    "WS10M": {
                        "2025122414": 18.5,  # Very windy
                        "2025122314": 16.2,
                        "2025122214": 14.8,
                        "2024122414": 19.1,
                        "2023122414": 12.3
                    },
                    "PRECTOTCORR": {
                        "2025122414": 35.0,  # Very wet
                        "2025122314": 28.0,
                        "2025122214": 15.0,
                        "2024122414": 42.0,
                        "2023122414": 8.0
                    }
                }
            }
        }
        
        climatology_response = {
            "properties": {
                "parameter": {
                    "T2M": {"12": 27.5},
                    "RH2M": {"12": 68.0},
                    "WS10M": {"12": 10.5},
                    "PRECTOTCORR": {"12": 15.2}
                }
            }
        }
        
        # Configure mock to return different responses based on URL
        def side_effect(url, params):
            if "climatology" in url:
                return climatology_response
            else:
                return temporal_response
        
        mock_http_get.side_effect = side_effect
        
        # Make request
        request_data = {
            "latitude": -7.115,
            "longitude": -34.863,
            "target_datetime": "2025-12-24T14:00:00",
            "granularity": "hourly",
            "start_year": 2020,
            "window_days": 5
        }
        
        response = self.client.post("/weather/analyze", json=request_data)
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        
        # Check basic structure
        assert "meta" in data
        assert "derived_insights" in data
        assert "parameters" in data
        assert "classifications" in data
        assert "request_id" in data
        
        # Verify metadata
        meta = data["meta"]
        assert meta["latitude"] == request_data["latitude"]
        assert meta["longitude"] == request_data["longitude"]
        assert meta["granularity"] == request_data["granularity"]
        assert meta["analysis_mode"] == "probabilistic"
        
        # Verify parameters analysis
        parameters = data["parameters"]
        assert "T2M" in parameters
        assert "RH2M" in parameters
        assert "WS10M" in parameters
        assert "PRECTOTCORR" in parameters
        
        # Check temperature analysis
        t2m_analysis = parameters["T2M"]
        assert t2m_analysis["mode"] == "probabilistic"
        assert "stats" in t2m_analysis
        assert t2m_analysis["climatology_month_mean"] == 27.5
        
        # Verify derived insights (heat index)
        derived_insights = data["derived_insights"]
        assert "heat_index" in derived_insights
        heat_index = derived_insights["heat_index"]
        assert "mean_heat_index_c" in heat_index or "p90_heat_index_c" in heat_index
        
        # Verify classifications
        classifications = data["classifications"]
        assert len(classifications) == 5  # All 5 weather conditions
        
        # Check that we have all expected conditions
        condition_names = {c["condition"] for c in classifications}
        expected_conditions = {"very_hot", "very_cold", "very_windy", "very_wet", "very_uncomfortable"}
        assert condition_names == expected_conditions
        
        # Verify high-risk conditions based on our mock data
        # Temperature mean should be high (around 35-36°C), so very_hot should have high probability
        very_hot_classification = next(c for c in classifications if c["condition"] == "very_hot")
        assert very_hot_classification["probability"] > 0.5
        assert very_hot_classification["threshold_value"] == 35.0
        assert very_hot_classification["parameter_used"] == "T2M"
        
        # Wind speed mean should be high (around 16-18 m/s), so very_windy should have high probability
        very_windy_classification = next(c for c in classifications if c["condition"] == "very_windy")
        assert very_windy_classification["probability"] > 0.5
        assert very_windy_classification["threshold_value"] == 15.0
        assert very_windy_classification["parameter_used"] == "WS10M"
        
        # Precipitation mean should be high (around 25-30mm), so very_wet should have high probability
        very_wet_classification = next(c for c in classifications if c["condition"] == "very_wet")
        assert very_wet_classification["probability"] > 0.5
        assert very_wet_classification["threshold_value"] == 25.0
        assert very_wet_classification["parameter_used"] == "PRECTOTCORR"
        
        # Very cold should have low probability (high temperatures)
        very_cold_classification = next(c for c in classifications if c["condition"] == "very_cold")
        assert very_cold_classification["probability"] < 0.1
        
        # Verify probability bounds and confidence levels
        for classification in classifications:
            assert 0.0 <= classification["probability"] <= 1.0
            assert classification["confidence"] in ["low", "medium", "high"]
            assert "description" in classification
    
    @patch('app.services.weather_service.WeatherDataService.http_get')
    def test_observed_mode_analysis(self, mock_http_get):
        """Test analysis in observed mode (historical date with available data)."""
        
        # Use a recent date that would have observed data
        past_date = datetime.now(timezone.utc) - timedelta(days=30)
        target_date_str = past_date.strftime("%Y%m%d")
        
        # Mock response with data for the specific date
        temporal_response = {
            "properties": {
                "parameter": {
                    "T2M": {
                        target_date_str: 31.5,  # Specific observed value
                        "20240101": 25.0,
                        "20240102": 27.0
                    },
                    "RH2M": {
                        target_date_str: 65.0,
                        "20240101": 70.0,
                        "20240102": 68.0
                    },
                    "WS10M": {
                        target_date_str: 8.5,
                        "20240101": 12.0,
                        "20240102": 10.0
                    },
                    "PRECTOTCORR": {
                        target_date_str: 5.0,
                        "20240101": 15.0,
                        "20240102": 0.0
                    }
                }
            }
        }
        
        climatology_response = {
            "properties": {
                "parameter": {
                    "T2M": {str(past_date.month): 28.0},
                    "RH2M": {str(past_date.month): 67.0},
                    "WS10M": {str(past_date.month): 9.5},
                    "PRECTOTCORR": {str(past_date.month): 12.0}
                }
            }
        }
        
        def side_effect(url, params):
            if "climatology" in url:
                return climatology_response
            else:
                return temporal_response
        
        mock_http_get.side_effect = side_effect
        
        # Make request for historical date
        request_data = {
            "latitude": -7.115,
            "longitude": -34.863,
            "target_datetime": past_date.strftime("%Y-%m-%dT12:00:00"),
            "granularity": "daily",
            "start_year": 2020,
            "window_days": 7
        }
        
        response = self.client.post("/weather/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be in observed mode
        assert data["meta"]["analysis_mode"] == "observed"
        
        # Parameters should have observed values
        parameters = data["parameters"]
        t2m_analysis = parameters["T2M"]
        assert t2m_analysis["mode"] == "observed"
        assert t2m_analysis["observed_value"] == 31.5
        assert "stats" not in t2m_analysis  # No stats in observed mode
        
        # Classifications should be deterministic (0.0 or 1.0 probabilities)
        classifications = data["classifications"]
        for classification in classifications:
            assert classification["probability"] in [0.0, 1.0]
            assert classification["confidence"] == "high"  # Observed data has high confidence
    
    def test_api_endpoints_availability(self):
        """Test that all expected endpoints are available."""
        
        # Test health endpoint
        response = self.client.get("/health")
        assert response.status_code == 200
        
        # Test parameters endpoint
        response = self.client.get("/weather/parameters")
        assert response.status_code == 200
        data = response.json()
        assert "parameters" in data
        assert "default_parameters" in data
        
        # Test thresholds endpoint
        response = self.client.get("/weather/thresholds")
        assert response.status_code == 200
        data = response.json()
        assert "thresholds" in data
        assert "conditions" in data
        
        # Test API documentation endpoints
        response = self.client.get("/docs")
        assert response.status_code == 200
        
        response = self.client.get("/redoc")
        assert response.status_code == 200
    
    def test_request_id_consistency(self):
        """Test that request IDs are consistent across response headers and body."""
        
        # Test with health endpoint
        response = self.client.get("/health")
        assert response.status_code == 200
        
        header_request_id = response.headers.get("X-Request-ID")
        body_data = response.json()
        body_request_id = body_data.get("request_id")
        
        assert header_request_id is not None
        assert body_request_id is not None
        assert header_request_id == body_request_id
        
        # Test with parameters endpoint
        response = self.client.get("/weather/parameters")
        assert response.status_code == 200
        
        header_request_id = response.headers.get("X-Request-ID")
        body_data = response.json()
        body_request_id = body_data.get("request_id")
        
        assert header_request_id == body_request_id
    
    def test_error_handling_with_request_id(self):
        """Test that error responses include request IDs."""
        
        # Test with invalid request data
        invalid_data = {
            "latitude": 95.0,  # Invalid latitude
            "longitude": -34.863,
            "target_datetime": "2025-12-25T14:00:00"
        }
        
        response = self.client.post("/weather/analyze", json=invalid_data)
        assert response.status_code == 422
        
        # Should have request ID in header
        assert "X-Request-ID" in response.headers
        
    @patch('app.services.weather_service.WeatherDataService.http_get')
    def test_edge_case_missing_parameters(self, mock_http_get):
        """Test behavior when some weather parameters are missing from API response."""
        
        # Mock incomplete response (missing some parameters)
        incomplete_response = {
            "properties": {
                "parameter": {
                    "T2M": {"20251225": 28.5},
                    "RH2M": {"20251225": 65.0}
                    # Missing WS10M and PRECTOTCORR
                }
            }
        }
        
        climatology_response = {
            "properties": {
                "parameter": {
                    "T2M": {"12": 27.5},
                    "RH2M": {"12": 68.0}
                }
            }
        }
        
        def side_effect(url, params):
            if "climatology" in url:
                return climatology_response
            else:
                return incomplete_response
        
        mock_http_get.side_effect = side_effect
        
        request_data = {
            "latitude": -7.115,
            "longitude": -34.863,
            "target_datetime": "2025-12-25T14:00:00",
            "granularity": "daily"
        }
        
        response = self.client.post("/weather/analyze", json=request_data)
        
        # Should still return successful response
        assert response.status_code == 200
        data = response.json()
        
        # Should have classifications for all conditions, even with missing parameters
        classifications = data["classifications"]
        assert len(classifications) == 5
        
        # Classifications for missing parameters should have low/zero probabilities
        very_windy = next(c for c in classifications if c["condition"] == "very_windy")
        very_wet = next(c for c in classifications if c["condition"] == "very_wet") 
        
        # These should have 0 probability due to missing data
        assert very_windy["probability"] == 0.0
        assert very_wet["probability"] == 0.0