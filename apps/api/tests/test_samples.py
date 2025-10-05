# ABOUTME: Comprehensive test suite for weather sample collector
# ABOUTME: Tests sample collection logic, coverage validation, and integration with POWER API

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.config import Settings
from app.engine.samples import (
    InsufficientCoverageError,
    SampleCollection,
    WeatherSample,
    _collect_samples_for_year,
    _get_season,
    _is_leap_year,
    collect_samples,
    validate_sample_coverage,
)
from app.weather.power import PowerAPIError, PowerClient


class TestWeatherSample:
    """Test WeatherSample dataclass functionality."""

    def test_weather_sample_creation(self):
        """Test basic WeatherSample creation."""
        timestamp_utc = datetime(2023, 6, 15, 12, 0, 0)
        timestamp_local = datetime(2023, 6, 15, 9, 0, 0)

        sample = WeatherSample(
            timestamp_utc=timestamp_utc,
            timestamp_local=timestamp_local,
            year=2023,
            doy=166,
            latitude=-3.7319,
            longitude=-38.5267,
            temperature_c=28.5,
            relative_humidity=65.0,
            wind_speed_ms=5.2,
            precipitation_mm_per_day=2.1,
            data_source="POWER",
        )

        assert sample.timestamp_utc == timestamp_utc
        assert sample.timestamp_local == timestamp_local
        assert sample.year == 2023
        assert sample.doy == 166
        assert sample.latitude == -3.7319
        assert sample.longitude == -38.5267
        assert sample.temperature_c == 28.5
        assert sample.relative_humidity == 65.0
        assert sample.wind_speed_ms == 5.2
        assert sample.precipitation_mm_per_day == 2.1
        assert sample.data_source == "POWER"


class TestSampleCollection:
    """Test SampleCollection dataclass functionality."""

    def test_sample_collection_creation(self):
        """Test basic SampleCollection creation."""
        samples = [
            WeatherSample(
                timestamp_utc=datetime(2023, 6, 15, 12, 0, 0),
                timestamp_local=datetime(2023, 6, 15, 9, 0, 0),
                year=2023,
                doy=166,
                latitude=-3.7319,
                longitude=-38.5267,
                temperature_c=28.5,
                relative_humidity=65.0,
                wind_speed_ms=5.2,
                precipitation_mm_per_day=2.1,
            )
        ]

        collection = SampleCollection(
            samples=samples,
            target_latitude=-3.7319,
            target_longitude=-38.5267,
            target_date=date(2024, 6, 15),
            target_hour=14,
            window_days=15,
            baseline_years=(2001, 2023),
            total_years_requested=23,
            years_with_data=15,
            total_samples=150,
            coverage_adequate=True,
            timezone_iana="America/Fortaleza",
        )

        assert len(collection.samples) == 1
        assert collection.target_latitude == -3.7319
        assert collection.target_longitude == -38.5267
        assert collection.target_date == date(2024, 6, 15)
        assert collection.target_hour == 14
        assert collection.window_days == 15
        assert collection.baseline_years == (2001, 2023)
        assert collection.total_years_requested == 23
        assert collection.years_with_data == 15
        assert collection.total_samples == 150
        assert collection.coverage_adequate is True
        assert collection.timezone_iana == "America/Fortaleza"


class TestCollectSamples:
    """Test main collect_samples function."""

    @pytest.fixture
    def mock_power_client(self):
        """Create mock PowerClient for testing."""
        client = Mock(spec=PowerClient)
        client.get_daily_data = AsyncMock()
        return client

    @pytest.fixture
    def sample_power_response(self):
        """Sample NASA POWER API response."""
        return {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20230601": 28.5,
                        "20230602": 29.1,
                        "20230603": 27.8,
                        "20230604": 30.2,
                        "20230605": 28.9,
                    },
                    "RH2M": {
                        "20230601": 65.0,
                        "20230602": 68.2,
                        "20230603": 62.1,
                        "20230604": 70.5,
                        "20230605": 66.8,
                    },
                    "WS10M": {
                        "20230601": 5.2,
                        "20230602": 4.8,
                        "20230603": 6.1,
                        "20230604": 3.9,
                        "20230605": 5.5,
                    },
                    "PRECTOTCORR": {
                        "20230601": 2.1,
                        "20230602": 0.0,
                        "20230603": 5.4,
                        "20230604": 0.8,
                        "20230605": 1.2,
                    },
                }
            }
        }

    @pytest.mark.asyncio
    async def test_collect_samples_basic(
        self, mock_power_client, sample_power_response
    ):
        """Test basic sample collection functionality."""
        # Setup mock responses
        mock_power_client.get_daily_data.return_value = sample_power_response

        # Mock timezone resolution
        with patch("app.engine.samples.tz_for_point") as mock_tz:
            mock_tz.return_value = "America/Fortaleza"

            # Mock DOY calculation
            with patch("app.engine.samples.get_day_of_year") as mock_doy:
                mock_doy.return_value = 166  # June 15th

                # Create custom settings with relaxed requirements for testing
                settings = Settings(
                    coverage_min_years=1, coverage_min_samples=1, coverage_enforce=False
                )

                collection = await collect_samples(
                    latitude=-3.7319,
                    longitude=-38.5267,
                    target_date_str="2024-06-15",
                    target_hour=14,
                    window_days=5,
                    baseline_start_year=2023,
                    baseline_end_year=2023,
                    settings=settings,
                    power_client=mock_power_client,
                )

        # Verify collection structure
        assert isinstance(collection, SampleCollection)
        assert len(collection.samples) == 5  # 5 days of data
        assert collection.target_latitude == -3.7319
        assert collection.target_longitude == -38.5267
        assert collection.target_hour == 14
        assert collection.window_days == 5
        assert collection.baseline_years == (2023, 2023)
        assert collection.timezone_iana == "America/Fortaleza"

        # Verify samples
        for sample in collection.samples:
            assert isinstance(sample, WeatherSample)
            assert sample.latitude == -3.7319
            assert sample.longitude == -38.5267
            assert sample.year == 2023
            assert sample.data_source == "POWER"
            assert 27.0 <= sample.temperature_c <= 31.0
            assert 60.0 <= sample.relative_humidity <= 75.0
            assert 3.0 <= sample.wind_speed_ms <= 7.0
            assert 0.0 <= sample.precipitation_mm_per_day <= 6.0

    @pytest.mark.asyncio
    async def test_collect_samples_input_validation(self, mock_power_client):
        """Test input validation for collect_samples."""
        settings = Settings(coverage_enforce=False)

        # Invalid latitude
        with pytest.raises(ValueError, match="Invalid latitude"):
            await collect_samples(
                latitude=91.0,  # Invalid
                longitude=-38.5267,
                target_date_str="2024-06-15",
                target_hour=14,
                settings=settings,
                power_client=mock_power_client,
            )

        # Invalid longitude
        with pytest.raises(ValueError, match="Invalid longitude"):
            await collect_samples(
                latitude=-3.7319,
                longitude=181.0,  # Invalid
                target_date_str="2024-06-15",
                target_hour=14,
                settings=settings,
                power_client=mock_power_client,
            )

        # Invalid hour
        with pytest.raises(ValueError, match="Invalid target_hour"):
            await collect_samples(
                latitude=-3.7319,
                longitude=-38.5267,
                target_date_str="2024-06-15",
                target_hour=25,  # Invalid
                settings=settings,
                power_client=mock_power_client,
            )

        # Invalid window_days
        with pytest.raises(ValueError, match="Invalid window_days"):
            await collect_samples(
                latitude=-3.7319,
                longitude=-38.5267,
                target_date_str="2024-06-15",
                target_hour=14,
                window_days=-1,  # Invalid
                settings=settings,
                power_client=mock_power_client,
            )

        # Invalid date string
        with pytest.raises(ValueError, match="Invalid target_date_str"):
            await collect_samples(
                latitude=-3.7319,
                longitude=-38.5267,
                target_date_str="invalid-date",  # Invalid
                target_hour=14,
                settings=settings,
                power_client=mock_power_client,
            )

    @pytest.mark.asyncio
    async def test_collect_samples_insufficient_coverage(self, mock_power_client):
        """Test insufficient coverage error handling."""
        # Setup minimal mock response
        mock_power_client.get_daily_data.return_value = {
            "properties": {
                "parameter": {"T2M": {}, "RH2M": {}, "WS10M": {}, "PRECTOTCORR": {}}
            }
        }

        with patch("app.engine.samples.tz_for_point") as mock_tz:
            mock_tz.return_value = "America/Fortaleza"

            with patch("app.engine.samples.get_day_of_year") as mock_doy:
                mock_doy.return_value = 166

                # Settings that enforce coverage
                settings = Settings(
                    coverage_min_years=15,
                    coverage_min_samples=100,
                    coverage_enforce=True,
                )

                with pytest.raises(
                    InsufficientCoverageError, match="Insufficient coverage"
                ):
                    await collect_samples(
                        latitude=-3.7319,
                        longitude=-38.5267,
                        target_date_str="2024-06-15",
                        target_hour=14,
                        baseline_start_year=2023,
                        baseline_end_year=2023,
                        settings=settings,
                        power_client=mock_power_client,
                    )

    @pytest.mark.asyncio
    async def test_collect_samples_power_api_error_handling(self, mock_power_client):
        """Test handling of POWER API errors."""
        # Setup mock to raise PowerAPIError
        mock_power_client.get_daily_data.side_effect = PowerAPIError("API unavailable")

        with patch("app.engine.samples.tz_for_point") as mock_tz:
            mock_tz.return_value = "America/Fortaleza"

            with patch("app.engine.samples.get_day_of_year") as mock_doy:
                mock_doy.return_value = 166

                settings = Settings(
                    coverage_min_years=1, coverage_min_samples=1, coverage_enforce=False
                )

                # Should not raise error, but return empty collection
                collection = await collect_samples(
                    latitude=-3.7319,
                    longitude=-38.5267,
                    target_date_str="2024-06-15",
                    target_hour=14,
                    baseline_start_year=2023,
                    baseline_end_year=2023,
                    settings=settings,
                    power_client=mock_power_client,
                )

                assert len(collection.samples) == 0
                assert collection.years_with_data == 0
                assert not collection.coverage_adequate

    @pytest.mark.asyncio
    async def test_collect_samples_multi_year(self, mock_power_client):
        """Test multi-year sample collection."""

        def mock_response_generator(*args, **kwargs):
            """Generate different responses for different years."""
            start_date = kwargs.get("start_date")
            if start_date and start_date.year == 2022:
                return {
                    "properties": {
                        "parameter": {
                            "T2M": {"20220601": 27.0, "20220602": 28.0},
                            "RH2M": {"20220601": 60.0, "20220602": 65.0},
                            "WS10M": {"20220601": 4.5, "20220602": 5.0},
                            "PRECTOTCORR": {"20220601": 1.0, "20220602": 2.0},
                        }
                    }
                }
            else:  # 2023
                return {
                    "properties": {
                        "parameter": {
                            "T2M": {"20230601": 28.5, "20230602": 29.1},
                            "RH2M": {"20230601": 65.0, "20230602": 68.2},
                            "WS10M": {"20230601": 5.2, "20230602": 4.8},
                            "PRECTOTCORR": {"20230601": 2.1, "20230602": 0.0},
                        }
                    }
                }

        mock_power_client.get_daily_data.side_effect = mock_response_generator

        with patch("app.engine.samples.tz_for_point") as mock_tz:
            mock_tz.return_value = "America/Fortaleza"

            with patch("app.engine.samples.get_day_of_year") as mock_doy:
                mock_doy.return_value = 153  # June 2nd (153rd day)

                settings = Settings(
                    coverage_min_years=2, coverage_min_samples=4, coverage_enforce=False
                )

                collection = await collect_samples(
                    latitude=-3.7319,
                    longitude=-38.5267,
                    target_date_str="2024-06-02",
                    target_hour=14,
                    window_days=1,  # Smaller window for this test
                    baseline_start_year=2022,
                    baseline_end_year=2023,
                    settings=settings,
                    power_client=mock_power_client,
                )

        assert collection.total_years_requested == 2
        assert len(collection.samples) == 4  # 2 samples per year × 2 years
        assert collection.years_with_data == 2

        # Verify years are represented
        years = {sample.year for sample in collection.samples}
        assert years == {2022, 2023}


class TestCollectSamplesForYear:
    """Test _collect_samples_for_year helper function."""

    @pytest.fixture
    def mock_power_client(self):
        """Create mock PowerClient for testing."""
        client = Mock(spec=PowerClient)
        client.get_daily_data = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_collect_samples_for_year_basic(self, mock_power_client):
        """Test basic year sample collection."""
        power_response = {
            "properties": {
                "parameter": {
                    "T2M": {"20230615": 28.5, "20230616": 29.1},
                    "RH2M": {"20230615": 65.0, "20230616": 68.2},
                    "WS10M": {"20230615": 5.2, "20230616": 4.8},
                    "PRECTOTCORR": {"20230615": 2.1, "20230616": 0.0},
                }
            }
        }

        mock_power_client.get_daily_data.return_value = power_response

        samples = await _collect_samples_for_year(
            power_client=mock_power_client,
            latitude=-3.7319,
            longitude=-38.5267,
            year=2023,
            target_doy=166,  # June 15th
            target_hour=14,
            window_days=1,
            timezone_iana="America/Fortaleza",
        )

        assert len(samples) == 2

        for sample in samples:
            assert sample.year == 2023
            assert sample.latitude == -3.7319
            assert sample.longitude == -38.5267
            assert isinstance(sample.timestamp_utc, datetime)
            assert isinstance(sample.timestamp_local, datetime)

    @pytest.mark.asyncio
    async def test_collect_samples_for_year_missing_data(self, mock_power_client):
        """Test handling of missing data in year collection."""
        # Response with missing temperature data
        power_response = {
            "properties": {
                "parameter": {
                    "T2M": {"20230615": 28.5},  # Missing 20230616
                    "RH2M": {"20230615": 65.0, "20230616": 68.2},
                    "WS10M": {"20230615": 5.2, "20230616": 4.8},
                    "PRECTOTCORR": {"20230615": 2.1, "20230616": 0.0},
                }
            }
        }

        mock_power_client.get_daily_data.return_value = power_response

        samples = await _collect_samples_for_year(
            power_client=mock_power_client,
            latitude=-3.7319,
            longitude=-38.5267,
            year=2023,
            target_doy=166,
            target_hour=14,
            window_days=1,
            timezone_iana="America/Fortaleza",
        )

        # Should only include the day with complete data
        assert len(samples) == 1
        assert samples[0].timestamp_utc.day == 15

    @pytest.mark.asyncio
    async def test_collect_samples_for_year_leap_year(self, mock_power_client):
        """Test DOY calculation for leap years."""
        power_response = {
            "properties": {
                "parameter": {
                    "T2M": {"20240229": 25.0},  # Feb 29th in leap year
                    "RH2M": {"20240229": 70.0},
                    "WS10M": {"20240229": 3.5},
                    "PRECTOTCORR": {"20240229": 0.5},
                }
            }
        }

        mock_power_client.get_daily_data.return_value = power_response

        samples = await _collect_samples_for_year(
            power_client=mock_power_client,
            latitude=-3.7319,
            longitude=-38.5267,
            year=2024,  # Leap year
            target_doy=60,  # Feb 29th
            target_hour=14,
            window_days=0,
            timezone_iana="America/Fortaleza",
        )

        assert len(samples) == 1
        assert samples[0].doy == 60  # Feb 29th is 60th day in leap year


class TestHelperFunctions:
    """Test helper functions."""

    def test_is_leap_year(self):
        """Test leap year detection."""
        assert _is_leap_year(2024) is True  # Divisible by 4
        assert _is_leap_year(2023) is False  # Not divisible by 4
        assert _is_leap_year(2000) is True  # Divisible by 400
        assert _is_leap_year(1900) is False  # Divisible by 100 but not 400

    def test_get_season(self):
        """Test season calculation from month."""
        assert _get_season(12) == "winter"
        assert _get_season(1) == "winter"
        assert _get_season(2) == "winter"
        assert _get_season(3) == "spring"
        assert _get_season(4) == "spring"
        assert _get_season(5) == "spring"
        assert _get_season(6) == "summer"
        assert _get_season(7) == "summer"
        assert _get_season(8) == "summer"
        assert _get_season(9) == "autumn"
        assert _get_season(10) == "autumn"
        assert _get_season(11) == "autumn"


class TestValidateSampleCoverage:
    """Test sample coverage validation function."""

    def test_validate_sample_coverage_adequate(self):
        """Test validation with adequate coverage."""
        # Create sample collection with good coverage
        samples = []
        for year in range(2010, 2025):  # 15 years
            for month in range(1, 13):  # All months
                sample = WeatherSample(
                    timestamp_utc=datetime(year, month, 15, 12, 0, 0),
                    timestamp_local=datetime(year, month, 15, 9, 0, 0),
                    year=year,
                    doy=15 + (month - 1) * 30,  # Approximate DOY
                    latitude=-3.7319,
                    longitude=-38.5267,
                    temperature_c=25.0,
                    relative_humidity=70.0,
                    wind_speed_ms=5.0,
                    precipitation_mm_per_day=1.0,
                )
                samples.append(sample)

        collection = SampleCollection(
            samples=samples,
            target_latitude=-3.7319,
            target_longitude=-38.5267,
            target_date=date(2024, 6, 15),
            target_hour=14,
            window_days=15,
            baseline_years=(2010, 2024),
            total_years_requested=15,
            years_with_data=15,
            total_samples=len(samples),
            coverage_adequate=True,
            timezone_iana="America/Fortaleza",
        )

        result = validate_sample_coverage(collection)

        assert result["coverage_adequate"] is True
        assert result["meets_requirements"]["years"] is True
        assert result["meets_requirements"]["samples"] is True
        assert result["meets_requirements"]["overall"] is True
        assert result["years_coverage_ratio"] == 1.0
        assert len(result["seasonal_distribution"]) == 4
        assert len(result["yearly_distribution"]) == 15

    def test_validate_sample_coverage_inadequate(self):
        """Test validation with inadequate coverage."""
        # Create minimal collection
        samples = [
            WeatherSample(
                timestamp_utc=datetime(2023, 6, 15, 12, 0, 0),
                timestamp_local=datetime(2023, 6, 15, 9, 0, 0),
                year=2023,
                doy=166,
                latitude=-3.7319,
                longitude=-38.5267,
                temperature_c=25.0,
                relative_humidity=70.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0,
            )
        ]

        collection = SampleCollection(
            samples=samples,
            target_latitude=-3.7319,
            target_longitude=-38.5267,
            target_date=date(2024, 6, 15),
            target_hour=14,
            window_days=15,
            baseline_years=(2023, 2023),
            total_years_requested=1,
            years_with_data=1,
            total_samples=1,
            coverage_adequate=False,
            timezone_iana="America/Fortaleza",
        )

        result = validate_sample_coverage(collection)

        assert result["coverage_adequate"] is False
        assert result["meets_requirements"]["years"] is False  # Need 15 years
        assert result["meets_requirements"]["samples"] is False  # Need 8 samples
        assert result["meets_requirements"]["overall"] is False
        assert (
            result["years_coverage_ratio"] == 1.0
        )  # 1 year requested, 1 year received
        assert result["sample_adequacy_ratio"] < 1.0  # 1 sample received, need 8

    def test_validate_sample_coverage_seasonal_distribution(self):
        """Test seasonal distribution calculation."""
        samples = []
        # Add samples for different seasons
        for month in [1, 4, 7, 10]:  # Winter, Spring, Summer, Autumn
            sample = WeatherSample(
                timestamp_utc=datetime(2023, month, 15, 12, 0, 0),
                timestamp_local=datetime(2023, month, 15, 9, 0, 0),
                year=2023,
                doy=15 + (month - 1) * 30,
                latitude=-3.7319,
                longitude=-38.5267,
                temperature_c=25.0,
                relative_humidity=70.0,
                wind_speed_ms=5.0,
                precipitation_mm_per_day=1.0,
            )
            samples.append(sample)

        collection = SampleCollection(
            samples=samples,
            target_latitude=-3.7319,
            target_longitude=-38.5267,
            target_date=date(2024, 6, 15),
            target_hour=14,
            window_days=15,
            baseline_years=(2023, 2023),
            total_years_requested=1,
            years_with_data=1,
            total_samples=4,
            coverage_adequate=False,
            timezone_iana="America/Fortaleza",
        )

        result = validate_sample_coverage(collection)

        seasonal = result["seasonal_distribution"]
        assert seasonal["winter"] == 1
        assert seasonal["spring"] == 1
        assert seasonal["summer"] == 1
        assert seasonal["autumn"] == 1
        assert sum(seasonal.values()) == 4
