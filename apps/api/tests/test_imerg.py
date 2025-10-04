"""
Test suite for IMERG client and precipitation aggregation.

Tests cover:
- IMERG client initialization and configuration
- Half-hourly data retrieval (simulated)
- Hourly aggregation with timezone handling
- Error handling and data validation
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.clients.imerg import (
    ImergClient,
    ImergDataPoint,
    ImergHourlyData,
    ImergResponse,
    create_imerg_client,
)
from app.config import Settings


class TestImergClient:
    """Test IMERG client functionality."""

    def test_imerg_client_initialization(self):
        """Test IMERG client initialization with default settings."""
        client = ImergClient()
        assert client.settings is not None
        assert hasattr(client, "client")

    def test_imerg_client_custom_settings(self):
        """Test IMERG client initialization with custom settings."""
        settings = Settings(enable_imerg=True, imerg_timeout_s=90, imerg_product="late")

        client = ImergClient(settings)
        assert client.settings.enable_imerg is True
        assert client.settings.imerg_timeout_s == 90
        assert client.settings.imerg_product == "late"

    @pytest.mark.asyncio
    async def test_imerg_client_context_manager(self):
        """Test IMERG client as async context manager."""
        async with ImergClient() as client:
            assert client is not None
            assert hasattr(client, "client")

    def test_create_imerg_client_factory(self):
        """Test IMERG client factory function."""
        client = create_imerg_client()
        assert isinstance(client, ImergClient)

        settings = Settings(enable_imerg=True)
        client_with_settings = create_imerg_client(settings)
        assert isinstance(client_with_settings, ImergClient)
        assert client_with_settings.settings == settings


class TestImergDataPoint:
    """Test IMERG data point model."""

    def test_imerg_data_point_creation(self):
        """Test creating IMERG data point."""
        timestamp = datetime(2024, 6, 15, 14, 30, tzinfo=ZoneInfo("UTC"))
        point = ImergDataPoint(
            timestamp=timestamp, precipitation_mm=2.5, quality_flag=95
        )

        assert point.timestamp == timestamp
        assert point.precipitation_mm == 2.5
        assert point.quality_flag == 95

    def test_imerg_data_point_negative_precipitation(self):
        """Test validation of negative precipitation values."""
        timestamp = datetime(2024, 6, 15, 14, 30, tzinfo=ZoneInfo("UTC"))

        # Negative values should be converted to 0.0
        point = ImergDataPoint(timestamp=timestamp, precipitation_mm=-1.0)
        assert point.precipitation_mm == 0.0

    def test_imerg_data_point_extreme_precipitation(self):
        """Test handling of extreme precipitation values."""
        timestamp = datetime(2024, 6, 15, 14, 30, tzinfo=ZoneInfo("UTC"))

        # Extreme values should be logged but preserved
        point = ImergDataPoint(
            timestamp=timestamp,
            precipitation_mm=1500.0,  # Very high but possible
        )
        assert point.precipitation_mm == 1500.0


class TestImergHourlyData:
    """Test IMERG hourly data model."""

    def test_imerg_hourly_data_creation(self):
        """Test creating IMERG hourly data."""
        hourly = ImergHourlyData(
            hour=14,
            total_mm=5.2,
            avg_rate_mm_hr=5.2,
            data_points=2,
            quality_score=0.95,
            source="IMERG",
        )

        assert hourly.hour == 14
        assert hourly.total_mm == 5.2
        assert hourly.avg_rate_mm_hr == 5.2
        assert hourly.data_points == 2
        assert hourly.quality_score == 0.95
        assert hourly.source == "IMERG"


class TestImergDataRetrieval:
    """Test IMERG data retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_half_hourly_data_basic(self):
        """Test basic half-hourly data retrieval."""
        client = ImergClient()

        result = await client.get_half_hourly_data(
            latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
        )

        assert result is not None
        assert isinstance(result, ImergResponse)
        assert result.latitude == -3.7319
        assert result.longitude == -38.5267
        assert len(result.data) == 48  # 48 half-hour periods per day
        assert all(isinstance(point, ImergDataPoint) for point in result.data)

    @pytest.mark.asyncio
    async def test_get_half_hourly_data_invalid_coordinates(self):
        """Test error handling for invalid coordinates."""
        client = ImergClient()

        with pytest.raises(ValueError, match="Latitude must be between"):
            await client.get_half_hourly_data(
                latitude=91.0,  # Invalid
                longitude=-38.5267,
                date=datetime(2024, 6, 15),
            )

        with pytest.raises(ValueError, match="Longitude must be between"):
            await client.get_half_hourly_data(
                latitude=-3.7319,
                longitude=181.0,  # Invalid
                date=datetime(2024, 6, 15),
            )

    @pytest.mark.asyncio
    async def test_get_half_hourly_data_different_products(self):
        """Test retrieving different IMERG product types."""
        client = ImergClient()

        for product in ["early", "late", "final"]:
            result = await client.get_half_hourly_data(
                latitude=-3.7319,
                longitude=-38.5267,
                date=datetime(2024, 6, 15),
                product=product,
            )

            assert result is not None
            assert result.metadata["product"] == product


class TestImergHourlyAggregation:
    """Test IMERG hourly aggregation functionality."""

    @pytest.mark.asyncio
    async def test_aggregate_to_hourly_basic(self):
        """Test basic hourly aggregation."""
        client = ImergClient()

        # Get half-hourly data first
        half_hourly = await client.get_half_hourly_data(
            latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
        )

        # Aggregate to hourly
        hourly_data = await client.aggregate_to_hourly(half_hourly, "UTC")

        assert len(hourly_data) == 24  # 24 hours
        assert all(isinstance(data, ImergHourlyData) for data in hourly_data)
        assert all(data.source == "IMERG" for data in hourly_data)

        # Check hour sequence
        hours = [data.hour for data in hourly_data]
        assert hours == list(range(24))

    @pytest.mark.asyncio
    async def test_aggregate_to_hourly_timezone_conversion(self):
        """Test hourly aggregation with timezone conversion."""
        client = ImergClient()

        half_hourly = await client.get_half_hourly_data(
            latitude=-3.7319,  # Fortaleza, Brazil
            longitude=-38.5267,
            date=datetime(2024, 6, 15),
        )

        # Aggregate to local timezone
        hourly_data = await client.aggregate_to_hourly(half_hourly, "America/Fortaleza")

        assert len(hourly_data) <= 24  # Could be fewer due to timezone conversion
        assert all(isinstance(data, ImergHourlyData) for data in hourly_data)

    @pytest.mark.asyncio
    async def test_aggregate_to_hourly_empty_data(self):
        """Test aggregation with empty input data."""
        client = ImergClient()

        # Create empty response
        empty_response = ImergResponse(
            latitude=-3.7319, longitude=-38.5267, date="2024-06-15", data=[]
        )

        hourly_data = await client.aggregate_to_hourly(empty_response, "UTC")
        assert len(hourly_data) == 0

    @pytest.mark.asyncio
    async def test_aggregate_to_hourly_data_consistency(self):
        """Test that aggregated data maintains consistency."""
        client = ImergClient()

        half_hourly = await client.get_half_hourly_data(
            latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
        )

        hourly_data = await client.aggregate_to_hourly(half_hourly, "UTC")

        for data in hourly_data:
            assert data.data_points > 0  # Should have at least one data point
            assert data.total_mm >= 0  # Non-negative precipitation
            assert data.avg_rate_mm_hr >= 0  # Non-negative rate
            assert 0 <= data.quality_score <= 1  # Quality score in valid range


class TestImergMainInterface:
    """Test IMERG main interface methods."""

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_complete_workflow(self):
        """Test complete workflow from raw data to hourly precipitation."""
        client = ImergClient()

        hourly_data = await client.get_hourly_precipitation(
            latitude=-3.7319,
            longitude=-38.5267,
            date=datetime(2024, 6, 15),
            timezone="America/Fortaleza",
            product="early",
        )

        assert isinstance(hourly_data, list)
        assert len(hourly_data) <= 24
        assert all(isinstance(data, ImergHourlyData) for data in hourly_data)
        assert all(data.source == "IMERG" for data in hourly_data)

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_error_handling(self):
        """Test error handling in main interface."""
        client = ImergClient()

        # Test with invalid coordinates
        result = await client.get_hourly_precipitation(
            latitude=91.0,  # Invalid
            longitude=-38.5267,
            date=datetime(2024, 6, 15),
        )

        # Should return empty list on error
        assert result == []


class TestImergValidation:
    """Test IMERG validation and error handling."""

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid values."""
        client = ImergClient()

        # Should not raise exception
        client._validate_coordinates(0, 0)
        client._validate_coordinates(-90, -180)
        client._validate_coordinates(90, 180)
        client._validate_coordinates(-3.7319, -38.5267)

    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid values."""
        client = ImergClient()

        with pytest.raises(ValueError):
            client._validate_coordinates(-91, 0)

        with pytest.raises(ValueError):
            client._validate_coordinates(91, 0)

        with pytest.raises(ValueError):
            client._validate_coordinates(0, -181)

        with pytest.raises(ValueError):
            client._validate_coordinates(0, 181)
