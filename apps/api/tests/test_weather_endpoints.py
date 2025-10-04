# ABOUTME: Unit tests for weather analysis endpoints and functionality
# ABOUTME: Comprehensive test coverage for weather data fetching, analysis, and classification

import pytest
from datetime import datetime
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.main import app


class TestWeatherAnalysisEndpoint:
    """Test suite for weather analysis endpoint."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_weather_analysis_success(self, sample_request_data, mock_weather_service):
        """Test successful weather analysis request."""
        with patch('app.controllers.weather_controller.WeatherDataService') as mock_service_class:
            mock_service_class.return_value = mock_weather_service
            
            with patch('app.controllers.weather_controller.WeatherClassificationService') as mock_class_service:
                mock_class_instance = Mock()
                mock_class_service.return_value = mock_class_instance
                mock_class_instance.classify_weather_conditions.return_value = [
                    {
                        "condition": "very_hot",
                        "probability": 0.15,
                        "confidence": "medium",
                        "threshold_value": 35.0,
                        "parameter_used": "T2M",
                        "description": "Temperature exceeds 35°C indicating very hot conditions"
                    }
                ]
                
                response = self.client.post("/weather/analyze", json=sample_request_data)
                
                assert response.status_code == 200
                data = response.json()
                
                # Check response structure
                assert "meta" in data
                assert "derived_insights" in data
                assert "parameters" in data
                assert "classifications" in data
                assert "request_id" in data
                
                # Check metadata
                meta = data["meta"]
                assert meta["latitude"] == sample_request_data["latitude"]
                assert meta["longitude"] == sample_request_data["longitude"]
                assert meta["granularity"] == sample_request_data["granularity"]
                
                # Check classifications
                classifications = data["classifications"]
                assert len(classifications) > 0
                assert classifications[0]["condition"] == "very_hot"
                assert "probability" in classifications[0]
                assert "confidence" in classifications[0]
    
    def test_weather_analysis_invalid_latitude(self, sample_request_data):
        """Test weather analysis with invalid latitude."""
        invalid_data = sample_request_data.copy()
        invalid_data["latitude"] = 95.0  # Invalid latitude > 90
        
        response = self.client.post("/weather/analyze", json=invalid_data)
        assert response.status_code == 422
    
    def test_weather_analysis_invalid_longitude(self, sample_request_data):
        """Test weather analysis with invalid longitude."""
        invalid_data = sample_request_data.copy()
        invalid_data["longitude"] = 185.0  # Invalid longitude > 180
        
        response = self.client.post("/weather/analyze", json=invalid_data)
        assert response.status_code == 422
    
    def test_weather_analysis_missing_required_fields(self):
        """Test weather analysis with missing required fields."""
        incomplete_data = {
            "latitude": -7.115
            # Missing longitude and target_datetime
        }
        
        response = self.client.post("/weather/analyze", json=incomplete_data)
        assert response.status_code == 422
    
    def test_weather_analysis_invalid_datetime(self, sample_request_data):
        """Test weather analysis with invalid datetime."""
        invalid_data = sample_request_data.copy()
        invalid_data["target_datetime"] = "1980-01-01T12:00:00"  # Before 1984
        
        response = self.client.post("/weather/analyze", json=invalid_data)
        assert response.status_code == 422
    
    def test_weather_analysis_server_error(self, sample_request_data):
        """Test weather analysis when service throws exception."""
        with patch('app.controllers.weather_controller.WeatherDataService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.analyze_weather.side_effect = Exception("API Error")
            
            response = self.client.post("/weather/analyze", json=sample_request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]
            assert "message" in data["detail"]
            assert "request_id" in data["detail"]


class TestWeatherParametersEndpoint:
    """Test suite for weather parameters endpoint."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_get_parameters_success(self):
        """Test successful retrieval of available parameters."""
        response = self.client.get("/weather/parameters")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "parameters" in data
        assert "default_parameters" in data
        assert "request_id" in data
        
        # Check that expected parameters are present
        parameters = data["parameters"]
        assert "T2M" in parameters
        assert "RH2M" in parameters
        assert "WS10M" in parameters
        assert "PRECTOTCORR" in parameters
        
        # Check parameter structure
        t2m_param = parameters["T2M"]
        assert "name" in t2m_param
        assert "unit" in t2m_param
        assert "description" in t2m_param


class TestWeatherThresholdsEndpoint:
    """Test suite for weather thresholds endpoint."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_get_thresholds_success(self):
        """Test successful retrieval of classification thresholds."""
        response = self.client.get("/weather/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "thresholds" in data
        assert "conditions" in data
        assert "request_id" in data
        
        # Check that expected conditions are present
        thresholds = data["thresholds"]
        conditions = data["conditions"]
        
        expected_conditions = ["very_hot", "very_cold", "very_windy", "very_wet", "very_uncomfortable"]
        for condition in expected_conditions:
            assert condition in conditions
            assert condition in thresholds
            
            threshold_data = thresholds[condition]
            assert "parameter" in threshold_data
            assert "threshold_value" in threshold_data
            assert "direction" in threshold_data
            assert "description" in threshold_data
            assert "unit" in threshold_data


class TestRequestIDMiddleware:
    """Test suite for request ID middleware functionality."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_request_id_added_when_missing(self):
        """Test that request ID is added when not provided."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
        
        # Should be a valid UUID format
        import uuid
        try:
            uuid.UUID(request_id)
            valid_uuid = True
        except ValueError:
            valid_uuid = False
        assert valid_uuid
    
    def test_existing_request_id_preserved(self):
        """Test that existing request ID is preserved."""
        custom_request_id = "test-123-456"
        headers = {"X-Request-ID": custom_request_id}
        
        response = self.client.get("/health", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == custom_request_id
    
    def test_request_id_in_response_body(self):
        """Test that request ID appears in response body."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        request_id_header = response.headers["X-Request-ID"]
        request_id_body = data["request_id"]
        
        assert request_id_header == request_id_body