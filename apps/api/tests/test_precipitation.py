"""
Test suite for precipitation client with IMERG + POWER fallback.

Tests cover:
- Unified precipitation client interface
- IMERG primary data source functionality
- POWER fallback mechanism
- Data source switching and error handling
- Availability checks
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.precipitation import (
    PrecipitationClient,
    PrecipitationData,
    create_precipitation_client,
)
from app.config import Settings


class TestPrecipitationClient:
    """Test unified precipitation client."""

    def test_precipitation_client_initialization(self):
        """Test precipitation client initialization."""
        client = PrecipitationClient()
        assert client.settings is not None
        assert hasattr(client, "imerg_client")
        assert hasattr(client, "power_client")

    def test_precipitation_client_custom_settings(self):
        """Test precipitation client with custom settings."""
        settings = Settings(enable_imerg=False, enable_precipitation_fallback=True)

        client = PrecipitationClient(settings)
        assert client.enable_imerg is False
        assert client.enable_fallback is True

    @pytest.mark.asyncio
    async def test_precipitation_client_context_manager(self):
        """Test precipitation client as async context manager."""
        async with PrecipitationClient() as client:
            assert client is not None

    def test_create_precipitation_client_factory(self):
        """Test precipitation client factory function."""
        client = create_precipitation_client()
        assert isinstance(client, PrecipitationClient)


class TestImergPrimarySource:
    """Test IMERG as primary precipitation source."""

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_imerg_success(self):
        """Test successful IMERG data retrieval."""
        settings = Settings(enable_imerg=True, enable_precipitation_fallback=True)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            # Mock IMERG client
            mock_imerg = AsyncMock()
            mock_imerg.get_hourly_precipitation.return_value = [
                MagicMock(
                    hour=14,
                    total_mm=3.5,
                    avg_rate_mm_hr=3.5,
                    data_points=2,
                    quality_score=0.9,
                    source="IMERG",
                )
            ]
            mock_create_imerg.return_value = mock_imerg

            # Mock POWER client
            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                mock_power = AsyncMock()
                mock_create_power.return_value = mock_power

                client = PrecipitationClient(settings)
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                result = await client.get_hourly_precipitation(
                    latitude=-3.7319,
                    longitude=-38.5267,
                    date=datetime(2024, 6, 15),
                    timezone="UTC",
                )

                assert len(result) == 1
                assert result[0].source == "IMERG"
                assert result[0].total_mm == 3.5

                # Should call IMERG, not POWER
                mock_imerg.get_hourly_precipitation.assert_called_once()
                mock_power.get_daily_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_imerg_disabled(self):
        """Test behavior when IMERG is disabled."""
        settings = Settings(enable_imerg=False, enable_precipitation_fallback=True)

        with patch(
            "app.clients.precipitation.create_power_client"
        ) as mock_create_power:
            # Mock POWER client
            mock_power = AsyncMock()
            mock_power_response = MagicMock()
            mock_power_response.data = [MagicMock(precipitation_mm=12.0)]
            mock_power.get_daily_data.return_value = mock_power_response
            mock_create_power.return_value = mock_power

            client = PrecipitationClient(settings)
            client.power_client = mock_power

            result = await client.get_hourly_precipitation(
                latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
            )

            assert len(result) == 24  # 24 hours from daily data
            assert all(r.source == "POWER_fallback" for r in result)
            assert all(r.total_mm == 0.5 for r in result)  # 12.0 / 24


class TestPowerFallback:
    """Test POWER fallback functionality."""

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_imerg_failure_power_success(self):
        """Test fallback to POWER when IMERG fails."""
        settings = Settings(enable_imerg=True, enable_precipitation_fallback=True)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            # Mock IMERG client to fail
            mock_imerg = AsyncMock()
            mock_imerg.get_hourly_precipitation.side_effect = Exception(
                "IMERG API error"
            )
            mock_create_imerg.return_value = mock_imerg

            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                # Mock POWER client to succeed
                mock_power = AsyncMock()
                mock_power_response = MagicMock()
                mock_power_response.data = [MagicMock(precipitation_mm=6.0)]
                mock_power.get_daily_data.return_value = mock_power_response
                mock_create_power.return_value = mock_power

                client = PrecipitationClient(settings)
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                result = await client.get_hourly_precipitation(
                    latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
                )

                assert len(result) == 24
                assert all(r.source == "POWER_fallback" for r in result)
                assert all(r.total_mm == 0.25 for r in result)  # 6.0 / 24

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_imerg_no_data_power_fallback(self):
        """Test fallback to POWER when IMERG returns no data."""
        settings = Settings(enable_imerg=True, enable_precipitation_fallback=True)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            # Mock IMERG client to return no data
            mock_imerg = AsyncMock()
            mock_imerg.get_hourly_precipitation.return_value = []
            mock_create_imerg.return_value = mock_imerg

            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                # Mock POWER client
                mock_power = AsyncMock()
                mock_power_response = MagicMock()
                mock_power_response.data = [MagicMock(precipitation_mm=3.6)]
                mock_power.get_daily_data.return_value = mock_power_response
                mock_create_power.return_value = mock_power

                client = PrecipitationClient(settings)
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                result = await client.get_hourly_precipitation(
                    latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
                )

                assert len(result) == 24
                assert all(r.source == "POWER_fallback" for r in result)
                assert all(r.total_mm == 0.15 for r in result)  # 3.6 / 24

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_both_sources_fail(self):
        """Test behavior when both IMERG and POWER fail."""
        settings = Settings(enable_imerg=True, enable_precipitation_fallback=True)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            mock_imerg = AsyncMock()
            mock_imerg.get_hourly_precipitation.side_effect = Exception("IMERG error")
            mock_create_imerg.return_value = mock_imerg

            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                mock_power = AsyncMock()
                mock_power.get_daily_data.side_effect = Exception("POWER error")
                mock_create_power.return_value = mock_power

                client = PrecipitationClient(settings)
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                result = await client.get_hourly_precipitation(
                    latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
                )

                assert result == []  # Empty list when both fail

    @pytest.mark.asyncio
    async def test_get_hourly_precipitation_fallback_disabled(self):
        """Test behavior when fallback is disabled."""
        settings = Settings(enable_imerg=True, enable_precipitation_fallback=False)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            mock_imerg = AsyncMock()
            mock_imerg.get_hourly_precipitation.return_value = []  # No IMERG data
            mock_create_imerg.return_value = mock_imerg

            client = PrecipitationClient(settings)
            client.imerg_client = mock_imerg

            result = await client.get_hourly_precipitation(
                latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
            )

            assert result == []  # Should not fall back to POWER


class TestSpecificHourRetrieval:
    """Test precipitation data for specific hours."""

    @pytest.mark.asyncio
    async def test_get_precipitation_for_hour_found(self):
        """Test retrieving precipitation for a specific hour when data exists."""
        client = PrecipitationClient()

        # Mock the get_hourly_precipitation method
        mock_hourly_data = [
            PrecipitationData(
                hour=10,
                total_mm=1.0,
                avg_rate_mm_hr=1.0,
                data_points=2,
                quality_score=0.9,
                source="IMERG",
            ),
            PrecipitationData(
                hour=14,
                total_mm=3.5,
                avg_rate_mm_hr=3.5,
                data_points=2,
                quality_score=0.9,
                source="IMERG",
            ),
        ]

        client.get_hourly_precipitation = AsyncMock(return_value=mock_hourly_data)

        result = await client.get_precipitation_for_hour(
            latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15), hour=14
        )

        assert result is not None
        assert result.hour == 14
        assert result.total_mm == 3.5

    @pytest.mark.asyncio
    async def test_get_precipitation_for_hour_not_found(self):
        """Test retrieving precipitation for hour when data doesn't exist."""
        client = PrecipitationClient()

        # Mock empty hourly data
        client.get_hourly_precipitation = AsyncMock(return_value=[])

        result = await client.get_precipitation_for_hour(
            latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15), hour=14
        )

        assert result is None


class TestDataAvailabilityChecks:
    """Test data availability checking functionality."""

    @pytest.mark.asyncio
    async def test_check_data_availability_imerg_available(self):
        """Test availability check when IMERG data is available."""
        settings = Settings(enable_imerg=True)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            mock_imerg = AsyncMock()
            mock_imerg_response = MagicMock()
            mock_imerg_response.data = [MagicMock()]  # Non-empty data
            mock_imerg.get_half_hourly_data.return_value = mock_imerg_response
            mock_create_imerg.return_value = mock_imerg

            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                mock_power = AsyncMock()
                mock_power_response = MagicMock()
                mock_power_response.data = [MagicMock()]
                mock_power.get_daily_data.return_value = mock_power_response
                mock_create_power.return_value = mock_power

                client = PrecipitationClient(settings)
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                availability = await client.check_data_availability(
                    latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
                )

                assert availability["imerg"] is True
                assert availability["power"] is True
                assert availability["any_available"] is True

    @pytest.mark.asyncio
    async def test_check_data_availability_power_only(self):
        """Test availability check when only POWER data is available."""
        settings = Settings(enable_imerg=True)

        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            mock_imerg = AsyncMock()
            mock_imerg.get_half_hourly_data.side_effect = Exception("IMERG error")
            mock_create_imerg.return_value = mock_imerg

            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                mock_power = AsyncMock()
                mock_power_response = MagicMock()
                mock_power_response.data = [MagicMock()]
                mock_power.get_daily_data.return_value = mock_power_response
                mock_create_power.return_value = mock_power

                client = PrecipitationClient(settings)
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                availability = await client.check_data_availability(
                    latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
                )

                assert availability["imerg"] is False
                assert availability["power"] is True
                assert availability["any_available"] is True

    @pytest.mark.asyncio
    async def test_check_data_availability_none_available(self):
        """Test availability check when no data sources are available."""
        with patch(
            "app.clients.precipitation.create_imerg_client"
        ) as mock_create_imerg:
            mock_imerg = AsyncMock()
            mock_imerg.get_half_hourly_data.side_effect = Exception("IMERG error")
            mock_create_imerg.return_value = mock_imerg

            with patch(
                "app.clients.precipitation.create_power_client"
            ) as mock_create_power:
                mock_power = AsyncMock()
                mock_power.get_daily_data.side_effect = Exception("POWER error")
                mock_create_power.return_value = mock_power

                client = PrecipitationClient()
                client.imerg_client = mock_imerg
                client.power_client = mock_power

                availability = await client.check_data_availability(
                    latitude=-3.7319, longitude=-38.5267, date=datetime(2024, 6, 15)
                )

                assert availability["imerg"] is False
                assert availability["power"] is False
                assert availability["any_available"] is False


class TestPrecipitationDataModel:
    """Test precipitation data model."""

    def test_precipitation_data_creation(self):
        """Test creating precipitation data object."""
        data = PrecipitationData(
            hour=14,
            total_mm=5.2,
            avg_rate_mm_hr=5.2,
            data_points=2,
            quality_score=0.95,
            source="IMERG",
        )

        assert data.hour == 14
        assert data.total_mm == 5.2
        assert data.source == "IMERG"

    def test_precipitation_data_inheritance(self):
        """Test that PrecipitationData inherits from ImergHourlyData."""
        from app.clients.imerg import ImergHourlyData

        data = PrecipitationData(
            hour=14,
            total_mm=5.2,
            avg_rate_mm_hr=5.2,
            data_points=2,
            quality_score=0.95,
            source="POWER_fallback",
        )

        assert isinstance(data, ImergHourlyData)
        assert data.source == "POWER_fallback"
