# ABOUTME: Tests for full risk endpoint functionality
# ABOUTME: Validates distributions and trends in full response detail

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, date
from app.main import app
from app.engine.samples import SampleCollection, WeatherSample


class TestRiskEndpointFull:
    """Test the full risk endpoint with distributions and trends."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
from app.main import app
from app.engine.samples import SampleCollection
from datetime import datetime


class TestRiskEndpointFull:
    """Test the full risk endpoint with distributions and trends."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    @patch('app.main.collect_samples')
    async def test_risk_endpoint_full_detail(self, mock_collect_samples):
        """Test risk endpoint with detail=full parameter."""
        # Mock sample collection
        from app.engine.samples import WeatherSample
        
        mock_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 12),
                year=2020,
                doy=167,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=35.0,
                relative_humidity=70.0,
                wind_speed_ms=8.0,
                precipitation_mm_per_day=5.0
            ),
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 16, 12),
                timestamp_local=datetime(2020, 6, 16, 12),
                year=2020,
                doy=168,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=25.0,
                relative_humidity=50.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0
            ),
            WeatherSample(
                timestamp_utc=datetime(2021, 6, 15, 12),
                timestamp_local=datetime(2021, 6, 15, 12),
                year=2021,
                doy=166,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=40.0,
                relative_humidity=80.0,
                wind_speed_ms=12.0,
                precipitation_mm_per_day=20.0
            )
        ]
        
        mock_collection = SampleCollection(
            samples=mock_samples,
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=datetime(2023, 6, 15).date(),
            target_hour=12,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=2,
            total_samples=3,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza"
        )
        
        mock_collect_samples.return_value = mock_collection
        
        # Make request with full detail
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 12,
            "window_days": 15,
            "detail": "full"
        }
        
        response = self.client.post("/risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic response structure
        assert "latitude" in data
        assert "longitude" in data
        assert "very_hot" in data
        assert "very_cold" in data
        assert "very_windy" in data
        assert "very_wet" in data
        assert "any_adverse" in data
        
        # Check full detail components
        assert "distributions" in data
        assert "trends" in data
        
        # Check distributions structure
        distributions = data["distributions"]
        assert len(distributions) > 0
        
        for dist in distributions:
            assert "parameter" in dist
            assert "unit" in dist
            assert "bins" in dist
            assert "mean" in dist
            assert "median" in dist
            assert "std_dev" in dist
            
            # Check bins structure
            for bin in dist["bins"]:
                assert "lower_bound" in bin
                assert "upper_bound" in bin
                assert "count" in bin
                assert "frequency" in bin
        
        # Check trends structure
        trends = data["trends"]
        assert len(trends) == 5  # hot, cold, windy, wet, any
        
        for trend in trends:
            assert "condition" in trend
            assert "points" in trend
            assert "slope" in trend
            assert "p_value" in trend
            assert "significant" in trend
            
            # Check trend points
            for point in trend["points"]:
                assert "year" in point
                assert "exceedance_rate" in point
    
    @patch('app.main.collect_samples')
    async def test_risk_endpoint_lean_detail_default(self, mock_collect_samples):
        """Test that lean detail is the default."""
        # Mock sample collection
        from app.engine.samples import WeatherSample
        
        mock_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 12),
                year=2020,
                doy=167,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=25.0,
                relative_humidity=50.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0
            )
        ]
        
        mock_collection = SampleCollection(
            samples=mock_samples,
            total_samples=1,
            years_with_data=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza",
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=12,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10
        )
        
        mock_collect_samples.return_value = mock_collection
        
        # Make request without detail parameter (should default to lean)
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 12,
            "window_days": 15
        }
        
        response = self.client.post("/risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should NOT have distributions and trends
        assert "distributions" not in data
        assert "trends" not in data
        
        # Should have basic response structure
        assert "very_hot" in data
        assert "sample_statistics" in data
        assert "thresholds" in data
    
    @patch('app.main.collect_samples')
    async def test_risk_endpoint_explicit_lean_detail(self, mock_collect_samples):
        """Test explicit lean detail parameter."""
        # Mock sample collection
        from app.engine.samples import WeatherSample
        
        mock_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 12),
                year=2020,
                doy=167,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=25.0,
                relative_humidity=50.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0
            )
        ]
        
        mock_collection = SampleCollection(
            samples=mock_samples,
            total_samples=1,
            years_with_data=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza",
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=12,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10
        )
        
        mock_collect_samples.return_value = mock_collection
        
        # Make request with explicit lean detail
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 12,
            "window_days": 15,
            "detail": "lean"
        }
        
        response = self.client.post("/risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should NOT have distributions and trends
        assert "distributions" not in data
        assert "trends" not in data
    
    def test_risk_endpoint_invalid_detail_parameter(self):
        """Test validation of detail parameter."""
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 12,
            "window_days": 15,
            "detail": "invalid"  # Invalid detail level
        }
        
        response = self.client.post("/risk", json=request_data)
        
        assert response.status_code == 422  # Validation error


class TestDistributionsAndTrendsIntegration:
    """Test integration of distributions and trends with the risk endpoint."""
    
    def setup_method(self):
        """Setup test client.""" 
        self.client = TestClient(app)
    
    @patch('app.main.collect_samples')
    @patch('app.main.calculate_distributions')
    @patch('app.main.calculate_all_trends')
    async def test_full_response_fallback_on_error(
        self, mock_trends, mock_distributions, mock_collect_samples
    ):
        """Test that full response falls back to lean if distributions/trends fail."""
        # Mock sample collection
        from app.engine.samples import WeatherSample, SampleCollection
        
        mock_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 12),
                year=2020,
                doy=167,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=25.0,
                relative_humidity=50.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0
            )
        ]
        
        mock_collection = SampleCollection(
            samples=mock_samples,
            total_samples=1,
            years_with_data=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza",
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=12,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10
        )
        
        mock_collect_samples.return_value = mock_collection
        
        # Make distributions calculation fail
        mock_distributions.side_effect = Exception("Distribution calculation failed")
        mock_trends.return_value = []
        
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 12,
            "detail": "full"
        }
        
        response = self.client.post("/risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should fall back to lean response (no distributions/trends)
        assert "distributions" not in data
        assert "trends" not in data
        
        # But should still have basic response
        assert "very_hot" in data
        assert "sample_statistics" in data