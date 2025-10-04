# ABOUTME: Test for the /risk endpoint implementation
# ABOUTME: Validates the main outdoor risk assessment API functionality

from datetime import UTC
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TestRiskEndpoint:
    """Test the /risk endpoint implementation."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_risk_endpoint_basic_request(self):
        """Test basic risk assessment request."""
        request_data = {
            "latitude": -3.7319,
            "longitude": -38.5267,
            "target_date": "2024-06-15",
            "target_hour": 14,
            "window_days": 15,
            "detail": "lean",
        }

        # Mock the collect_samples function to return a small mock result
        with (
            patch("app.main.collect_samples") as mock_collect_samples,
            patch("app.main.calculate_probability") as mock_calculate_probability,
        ):
            # Mock sample collection
            from datetime import date, datetime

            from app.engine.samples import SampleCollection, WeatherSample

            mock_samples = [
                WeatherSample(
                    timestamp_utc=datetime(2020, 6, 15, 14, 0, tzinfo=UTC),
                    timestamp_local=datetime(2020, 6, 15, 11, 0),
                    year=2020,
                    doy=167,
                    latitude=-3.7319,
                    longitude=-38.5267,
                    temperature_c=30.0,
                    relative_humidity=65.0,
                    wind_speed_ms=5.0,
                    precipitation_mm_per_day=0.0,
                    precipitation_mm_hourly=0.0,
                    precipitation_source="POWER",
                    data_source="POWER",
                )
            ]

            mock_collection = SampleCollection(
                samples=mock_samples,
                target_latitude=-3.7319,
                target_longitude=-38.5267,
                target_date=date(2024, 6, 15),
                target_hour=14,
                window_days=15,
                baseline_years=(2001, 2023),
                total_years_requested=23,
                years_with_data=23,
                total_samples=1,
                coverage_adequate=True,
                timezone_iana="America/Fortaleza",
            )

            mock_collect_samples.return_value = mock_collection

            # Mock probability calculation
            from app.analysis.probability import ProbabilityResult

            mock_prob_result = ProbabilityResult(
                probability=0.10,
                confidence_interval_lower=0.05,
                confidence_interval_upper=0.18,
                total_samples=100,
                positive_samples=10,
                coverage_years=20,
                coverage_adequate=True,
                condition_type="hot",
            )

            mock_calculate_probability.return_value = mock_prob_result

            # Make request
            response = self.client.post("/risk", json=request_data)

            # Check response
            assert response.status_code == 200

            data = response.json()
            assert "latitude" in data
            assert "longitude" in data
            assert "target_date" in data
            assert "target_hour" in data
            assert "very_hot" in data
            assert "very_cold" in data
            assert "very_windy" in data
            assert "very_wet" in data
            assert "any_adverse" in data
            assert "sample_statistics" in data
            assert "thresholds" in data

            # Check probability structure
            assert "probability" in data["very_hot"]
            assert "confidence_interval" in data["very_hot"]
            assert "positive_samples" in data["very_hot"]

    def test_risk_endpoint_validation(self):
        """Test request validation."""
        # Invalid latitude
        response = self.client.post(
            "/risk",
            json={
                "latitude": 95.0,  # Invalid
                "longitude": -38.5267,
                "target_date": "2024-06-15",
                "target_hour": 14,
            },
        )
        assert response.status_code == 422

        # Invalid target_date format
        response = self.client.post(
            "/risk",
            json={
                "latitude": -3.7319,
                "longitude": -38.5267,
                "target_date": "invalid-date",
                "target_hour": 14,
            },
        )
        assert response.status_code == 422

        # Invalid target_hour
        response = self.client.post(
            "/risk",
            json={
                "latitude": -3.7319,
                "longitude": -38.5267,
                "target_date": "2024-06-15",
                "target_hour": 25,  # Invalid
            },
        )
        assert response.status_code == 422
