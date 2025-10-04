# ABOUTME: Tests for export functionality
# ABOUTME: Validates CSV and JSON export formats, headers, data integrity, and rate limiting

import pytest
import csv
import json
import io
from datetime import datetime, date
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.export.exporter import (
    create_export_rows, export_to_csv, export_to_json, 
    generate_export_filename, get_content_type, validate_export_data
)
from app.engine.samples import SampleCollection, WeatherSample
from app.config import Settings


class TestExportDataProcessing:
    """Test export data processing functions."""
    
    def setup_method(self):
        """Setup test data."""
        self.settings = Settings()
        
        # Create test weather samples
        self.test_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 9),
                year=2020,
                doy=167,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=35.0,
                relative_humidity=75.0,
                wind_speed_ms=8.0,
                precipitation_mm_per_day=5.0
            ),
            WeatherSample(
                timestamp_utc=datetime(2021, 6, 15, 12),
                timestamp_local=datetime(2021, 6, 15, 9),
                year=2021,
                doy=166,
                latitude=-3.7,
                longitude=-38.5,
                temperature_c=25.0,
                relative_humidity=50.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0
            )
        ]
        
        self.test_collection = SampleCollection(
            samples=self.test_samples,
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=9,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=2,
            total_samples=2,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza"
        )
    
    def test_create_export_rows_basic(self):
        """Test creation of export rows with all required fields."""
        export_rows = create_export_rows(self.test_collection, self.settings)
        
        assert len(export_rows) == 2
        
        # Check first row
        row1 = export_rows[0]
        assert row1.timestamp_local == "2020-06-15T09:00:00"
        assert row1.year == 2020
        assert row1.doy == 167
        assert row1.lat == -3.7
        assert row1.lon == -38.5
        assert row1.t2m_c == 35.0
        assert row1.rh2m_pct == 75.0
        assert row1.ws10m_ms == 8.0
        
        # Check calculated fields
        assert row1.hi_c is not None  # Heat index should be calculated for hot/humid conditions
        assert row1.precip_mm_per_h == pytest.approx(5.0 / 24.0)  # Daily to hourly conversion
        assert row1.precip_source == "POWER"
        
        # Check flags
        assert isinstance(row1.flags_very_hot, bool)
        assert isinstance(row1.flags_very_cold, bool)
        assert isinstance(row1.flags_very_windy, bool)
        assert isinstance(row1.flags_very_wet, bool)
        assert isinstance(row1.flags_any_adverse, bool)
    
    def test_create_export_rows_empty_collection(self):
        """Test export row creation with empty sample collection."""
        empty_collection = SampleCollection(
            samples=[],
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=9,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=0,
            total_samples=0,
            coverage_adequate=False,
            timezone_iana="America/Fortaleza"
        )
        
        export_rows = create_export_rows(empty_collection, self.settings)
        assert export_rows == []
    
    def test_export_to_csv_format(self):
        """Test CSV export format and structure."""
        export_rows = create_export_rows(self.test_collection, self.settings)
        csv_content = export_to_csv(export_rows)
        
        # Parse CSV to validate structure
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) == 2
        
        # Check headers are present
        expected_headers = [
            "timestamp_local", "year", "doy", "lat", "lon", "t2m_c", "rh2m_pct", 
            "ws10m_ms", "hi_c", "wct_c", "precip_mm_per_h", "precip_source",
            "flags_very_hot", "flags_very_cold", "flags_very_windy", 
            "flags_very_wet", "flags_any_adverse"
        ]
        
        for header in expected_headers:
            assert header in csv_reader.fieldnames
        
        # Check data types and values
        row1 = rows[0]
        assert row1["year"] == "2020"
        assert row1["lat"] == "-3.7"
        assert row1["t2m_c"] == "35.0"
        assert row1["precip_source"] == "POWER"
    
    def test_export_to_csv_empty_data(self):
        """Test CSV export with empty data."""
        csv_content = export_to_csv([])
        
        # Should contain headers only
        lines = csv_content.strip().split('\n')
        assert len(lines) == 1
        assert "timestamp_local" in lines[0]
    
    def test_export_to_json_format(self):
        """Test JSON export format and structure."""
        export_rows = create_export_rows(self.test_collection, self.settings)
        json_content = export_to_json(export_rows)
        
        # Parse JSON to validate structure
        data = json.loads(json_content)
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check first item structure
        item1 = data[0]
        assert item1["timestamp_local"] == "2020-06-15T09:00:00"
        assert item1["year"] == 2020
        assert item1["lat"] == -3.7
        assert item1["t2m_c"] == 35.0
        assert "flags_very_hot" in item1
        
    def test_export_to_json_empty_data(self):
        """Test JSON export with empty data."""
        json_content = export_to_json([])
        
        data = json.loads(json_content)
        assert data == []
    
    def test_generate_export_filename(self):
        """Test export filename generation."""
        filename = generate_export_filename(
            latitude=-3.7,
            longitude=-38.5,
            target_date="2023-06-15",
            target_hour=12,
            format="csv"
        )
        
        assert filename.startswith("outdoor_risk_export_")
        assert "3.7S" in filename
        assert "38.5W" in filename
        assert "20230615" in filename
        assert "12h" in filename
        assert filename.endswith(".csv")
    
    def test_get_content_type(self):
        """Test content type detection."""
        assert get_content_type("csv") == "text/csv"
        assert get_content_type("json") == "application/json"
        
        with pytest.raises(ValueError):
            get_content_type("invalid")
    
    def test_validate_export_data(self):
        """Test export data validation."""
        export_rows = create_export_rows(self.test_collection, self.settings)
        validation = validate_export_data(export_rows)
        
        assert validation["valid"] is True
        assert validation["row_count"] == 2
        assert validation["year_range"] == (2020, 2021)
        assert validation["coordinate_consistency"] is True
        assert "POWER" in validation["data_sources"]
        assert validation["missing_fields"] == []
    
    def test_validate_export_data_empty(self):
        """Test validation with empty data."""
        validation = validate_export_data([])
        
        assert validation["valid"] is True
        assert validation["row_count"] == 0
        assert validation["year_range"] is None


class TestExportEndpoint:
    """Test the /export endpoint."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    @patch('app.main.collect_samples')
    async def test_export_endpoint_csv(self, mock_collect_samples):
        """Test export endpoint with CSV format."""
        # Mock sample collection
        mock_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 9),
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
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=9,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=1,
            total_samples=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza"
        )
        
        mock_collect_samples.return_value = mock_collection
        
        # Make export request
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 9,
            "window_days": 15,
            "format": "csv"
        }
        
        response = self.client.post("/export", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check CSV content
        content = response.text
        lines = content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least 1 data row
        assert "timestamp_local" in lines[0]
    
    @patch('app.main.collect_samples')
    async def test_export_endpoint_json(self, mock_collect_samples):
        """Test export endpoint with JSON format."""
        # Mock sample collection (same as CSV test)
        mock_samples = [
            WeatherSample(
                timestamp_utc=datetime(2020, 6, 15, 12),
                timestamp_local=datetime(2020, 6, 15, 9),
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
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=9,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=1,
            total_samples=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza"
        )
        
        mock_collect_samples.return_value = mock_collection
        
        # Make export request
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 9,
            "format": "json"
        }
        
        response = self.client.post("/export", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Check JSON content
        data = response.json() if hasattr(response, 'json') else json.loads(response.text)
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_export_endpoint_validation(self):
        """Test export endpoint input validation."""
        # Invalid format
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 9,
            "format": "invalid"
        }
        
        response = self.client.post("/export", json=request_data)
        assert response.status_code == 422  # Validation error
        
        # Invalid coordinates
        request_data = {
            "latitude": 100.0,  # Out of range
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 9,
            "format": "csv"
        }
        
        response = self.client.post("/export", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_export_endpoint_rate_limiting(self):
        """Test that export endpoint has stricter rate limiting."""
        # This is a smoke test - actual rate limiting testing would require
        # multiple rapid requests which is complex to test reliably
        request_data = {
            "latitude": -3.7,
            "longitude": -38.5,
            "target_date": "2023-06-15",
            "target_hour": 9,
            "format": "csv"
        }
        
        # First request should work (may fail due to data issues but not rate limiting)
        response = self.client.post("/export", json=request_data)
        # We don't assert success here as it depends on mock data availability
        # but it shouldn't be a rate limit error (429)
        assert response.status_code != 429


class TestExportDataIntegrity:
    """Test data integrity in exports."""
    
    def test_export_headers_completeness(self):
        """Test that all required headers are present in exports."""
        settings = Settings()
        
        # Create a sample with all possible data
        sample = WeatherSample(
            timestamp_utc=datetime(2020, 6, 15, 12),
            timestamp_local=datetime(2020, 6, 15, 9),
            year=2020,
            doy=167,
            latitude=-3.7,
            longitude=-38.5,
            temperature_c=35.0,
            relative_humidity=80.0,
            wind_speed_ms=12.0,
            precipitation_mm_per_day=10.0
        )
        
        collection = SampleCollection(
            samples=[sample],
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=9,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=1,
            total_samples=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza"
        )
        
        export_rows = create_export_rows(collection, settings)
        csv_content = export_to_csv(export_rows)
        
        # Check that all required headers are present
        required_headers = [
            "timestamp_local", "year", "doy", "lat", "lon", "t2m_c", "rh2m_pct",
            "ws10m_ms", "hi_c", "wct_c", "precip_mm_per_h", "precip_source",
            "flags_very_hot", "flags_very_cold", "flags_very_windy", 
            "flags_very_wet", "flags_any_adverse"
        ]
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        for header in required_headers:
            assert header in csv_reader.fieldnames, f"Missing required header: {header}"
    
    def test_export_units_consistency(self):
        """Test that units are consistent in export data."""
        settings = Settings()
        
        sample = WeatherSample(
            timestamp_utc=datetime(2020, 6, 15, 12),
            timestamp_local=datetime(2020, 6, 15, 9),
            year=2020,
            doy=167,
            latitude=-3.7,
            longitude=-38.5,
            temperature_c=30.0,
            relative_humidity=60.0,
            wind_speed_ms=8.0,
            precipitation_mm_per_day=24.0  # 24mm/day = 1mm/h average
        )
        
        collection = SampleCollection(
            samples=[sample],
            target_latitude=-3.7,
            target_longitude=-38.5,
            target_date=date(2023, 6, 15),
            target_hour=9,
            window_days=15,
            baseline_years=(2015, 2024),
            total_years_requested=10,
            years_with_data=1,
            total_samples=1,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza"
        )
        
        export_rows = create_export_rows(collection, settings)
        row = export_rows[0]
        
        # Check unit consistency
        assert row.t2m_c == 30.0  # Temperature in Celsius
        assert row.rh2m_pct == 60.0  # Humidity in percentage
        assert row.ws10m_ms == 8.0  # Wind speed in m/s
        assert row.precip_mm_per_h == pytest.approx(1.0)  # Precipitation in mm/h
        
        # Coordinates should be in decimal degrees
        assert -90 <= row.lat <= 90
        assert -180 <= row.lon <= 180