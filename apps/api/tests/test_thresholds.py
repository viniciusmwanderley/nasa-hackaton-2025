# ABOUTME: Comprehensive test suite for weather threshold helpers
# ABOUTME: Tests WeatherSample, condition flagging, and threshold evaluation

from datetime import UTC, datetime

import pytest

from app.config import Settings
from app.weather.thresholds import (
    WeatherConditionFlags,
    WeatherSample,
    evaluate_sample_risk,
    flag_weather_conditions,
    is_very_cold,
    is_very_hot,
    is_very_wet,
    is_very_windy,
)


class TestWeatherSample:
    """Test WeatherSample dataclass and its methods."""

    def test_weather_sample_creation(self):
        """Test basic WeatherSample creation and derived calculations."""
        sample = WeatherSample(
            temperature_c=35.0,
            relative_humidity=70.0,
            wind_speed_ms=5.0,
            precipitation_mm_per_day=10.0,
            timestamp=datetime(2023, 6, 15, 10, 0, tzinfo=UTC),
            latitude=-3.7275,
            longitude=-38.5275,
        )

        # Check basic attributes
        assert sample.temperature_c == 35.0
        assert sample.relative_humidity == 70.0
        assert sample.wind_speed_ms == 5.0
        assert sample.precipitation_mm_per_day == 10.0

        # Check derived calculations
        assert sample.heat_index_c is not None  # Should be calculated for hot+humid
        assert sample.heat_index_c > sample.temperature_c  # Should feel hotter
        assert sample.wind_chill_c is None  # Too warm for wind chill
        assert sample.feels_like_c == sample.heat_index_c  # Should use heat index

    def test_weather_sample_cold_conditions(self):
        """Test WeatherSample with cold and windy conditions."""
        sample = WeatherSample(
            temperature_c=-5.0,
            relative_humidity=80.0,
            wind_speed_ms=10.0,
            precipitation_mm_per_day=0.0,
            timestamp=datetime(2023, 12, 15, 10, 0, tzinfo=UTC),
            latitude=45.0,
            longitude=-75.0,
        )

        # Check derived calculations for cold conditions
        assert sample.heat_index_c is None  # Too cold for heat index
        assert sample.wind_chill_c is not None  # Should be calculated for cold+windy
        assert sample.wind_chill_c < sample.temperature_c  # Should feel colder
        assert sample.feels_like_c == sample.wind_chill_c  # Should use wind chill

    def test_weather_sample_moderate_conditions(self):
        """Test WeatherSample with moderate conditions (no heat index or wind chill)."""
        sample = WeatherSample(
            temperature_c=20.0,
            relative_humidity=50.0,
            wind_speed_ms=2.0,
            precipitation_mm_per_day=5.0,
            timestamp=datetime(2023, 9, 15, 10, 0, tzinfo=UTC),
            latitude=40.7128,
            longitude=-74.0060,
        )

        # Check that no special calculations apply
        assert sample.heat_index_c is None  # Too cool/dry for heat index
        assert sample.wind_chill_c is None  # Too warm/calm for wind chill
        assert (
            sample.feels_like_c == sample.temperature_c
        )  # Should use actual temperature

    def test_from_power_data(self):
        """Test creating WeatherSample from NASA POWER data format."""
        power_data = {"T2M": 32.5, "RH2M": 85.0, "WS10M": 3.5, "PRECTOTCORR": 15.2}

        date = datetime(2023, 7, 4, 12, 0, tzinfo=UTC)
        lat, lon = 25.7617, -80.1918  # Miami coordinates

        sample = WeatherSample.from_power_data(power_data, date, lat, lon)

        # Check that data was mapped correctly
        assert sample.temperature_c == 32.5
        assert sample.relative_humidity == 85.0
        assert sample.wind_speed_ms == 3.5
        assert sample.precipitation_mm_per_day == 15.2
        assert sample.timestamp == date
        assert sample.latitude == lat
        assert sample.longitude == lon

        # Should have calculated heat index for these conditions
        assert sample.heat_index_c is not None
        assert sample.heat_index_c > sample.temperature_c

    def test_from_power_data_missing_parameters(self):
        """Test error handling when POWER data is missing parameters."""
        incomplete_data = {
            "T2M": 25.0,
            "RH2M": 60.0,
            # Missing WS10M and PRECTOTCORR
        }

        date = datetime(2023, 6, 1, 12, 0, tzinfo=UTC)

        with pytest.raises(KeyError, match="Missing required parameters"):
            WeatherSample.from_power_data(incomplete_data, date, 0.0, 0.0)


class TestWeatherConditionFlags:
    """Test WeatherConditionFlags functionality."""

    def test_flags_creation_and_methods(self):
        """Test WeatherConditionFlags creation and utility methods."""
        # No flags set
        flags = WeatherConditionFlags()
        assert not flags.any_flagged()
        assert flags.count_flagged() == 0
        assert flags.to_dict() == {
            "very_hot": False,
            "very_cold": False,
            "very_windy": False,
            "very_wet": False,
        }

        # Multiple flags set
        flags = WeatherConditionFlags(very_hot=True, very_windy=True)
        assert flags.any_flagged()
        assert flags.count_flagged() == 2
        assert flags.to_dict()["very_hot"] is True
        assert flags.to_dict()["very_windy"] is True
        assert flags.to_dict()["very_cold"] is False


class TestThresholdFunctions:
    """Test individual threshold functions."""

    @pytest.fixture
    def settings(self):
        """Fixture providing test settings."""
        return Settings(
            thresholds_hi_hot_c=35.0,
            thresholds_wct_cold_c=-15.0,
            thresholds_wind_ms=12.0,
            thresholds_rain_mm_per_h=5.0,
        )

    def test_is_very_hot_with_heat_index(self, settings):
        """Test hot condition detection using heat index."""
        # Create sample with conditions that trigger heat index
        sample = WeatherSample(
            temperature_c=33.0,  # Below hot threshold
            relative_humidity=80.0,  # High humidity
            wind_speed_ms=2.0,
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        # Heat index should push it over the threshold
        assert sample.heat_index_c is not None
        assert sample.heat_index_c > 35.0  # Above threshold
        assert is_very_hot(sample, settings)

    def test_is_very_hot_without_heat_index(self, settings):
        """Test hot condition detection using air temperature."""
        # Create sample with hot but dry conditions (no heat index)
        sample = WeatherSample(
            temperature_c=36.0,  # Above hot threshold
            relative_humidity=30.0,  # Too low for heat index
            wind_speed_ms=2.0,
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        # Should fall back to air temperature
        assert sample.heat_index_c is None
        assert is_very_hot(sample, settings)

        # Test just below threshold
        sample.temperature_c = 34.5
        assert not is_very_hot(sample, settings)

    def test_is_very_cold_with_wind_chill(self, settings):
        """Test cold condition detection using wind chill."""
        # Create sample with conditions that trigger wind chill
        sample = WeatherSample(
            temperature_c=-5.0,  # Above cold threshold
            relative_humidity=70.0,
            wind_speed_ms=15.0,  # Strong wind
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        # Wind chill should push it below the threshold
        assert sample.wind_chill_c is not None
        assert sample.wind_chill_c < -15.0  # Below threshold
        assert is_very_cold(sample, settings)

    def test_is_very_cold_without_wind_chill(self, settings):
        """Test cold condition detection using air temperature."""
        # Create sample with cold but calm conditions (no wind chill)
        sample = WeatherSample(
            temperature_c=-20.0,  # Below cold threshold
            relative_humidity=50.0,
            wind_speed_ms=0.5,  # Too low for wind chill
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        # Should fall back to air temperature
        assert sample.wind_chill_c is None
        assert is_very_cold(sample, settings)

        # Test just above threshold
        sample.temperature_c = -10.0
        assert not is_very_cold(sample, settings)

    def test_is_very_windy(self, settings):
        """Test windy condition detection."""
        sample = WeatherSample(
            temperature_c=25.0,
            relative_humidity=60.0,
            wind_speed_ms=15.0,  # Above windy threshold (12.0)
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        assert is_very_windy(sample, settings)

        # Test just below threshold
        sample.wind_speed_ms = 11.5
        assert not is_very_windy(sample, settings)

    def test_is_very_wet(self, settings):
        """Test wet condition detection with daily to hourly conversion."""
        # Test with high daily precipitation
        sample = WeatherSample(
            temperature_c=25.0,
            relative_humidity=90.0,
            wind_speed_ms=3.0,
            precipitation_mm_per_day=50.0,  # 50mm/day = 6.25mm/h
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        # 50mm/day ÷ 8 hours = 6.25mm/h > 5.0mm/h threshold
        assert is_very_wet(sample, settings)

        # Test just below threshold
        sample.precipitation_mm_per_day = 35.0  # 35mm/day = 4.375mm/h < threshold
        assert not is_very_wet(sample, settings)


class TestFlagWeatherConditions:
    """Test the main flag_weather_conditions function."""

    @pytest.fixture
    def settings(self):
        """Fixture providing test settings."""
        return Settings(
            thresholds_hi_hot_c=35.0,
            thresholds_wct_cold_c=-15.0,
            thresholds_wind_ms=12.0,
            thresholds_rain_mm_per_h=5.0,
        )

    def test_no_flags_normal_conditions(self, settings):
        """Test that normal conditions don't trigger any flags."""
        sample = WeatherSample(
            temperature_c=22.0,  # Comfortable temperature
            relative_humidity=55.0,  # Moderate humidity
            wind_speed_ms=3.0,  # Light breeze
            precipitation_mm_per_day=5.0,  # Light rain (0.625 mm/h)
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        flags = flag_weather_conditions(sample, settings)

        assert not flags.very_hot
        assert not flags.very_cold
        assert not flags.very_windy
        assert not flags.very_wet
        assert not flags.any_flagged()
        assert flags.count_flagged() == 0

    def test_multiple_flags_extreme_conditions(self, settings):
        """Test extreme conditions that trigger multiple flags."""
        # Extreme storm conditions: very windy and very wet
        sample = WeatherSample(
            temperature_c=25.0,
            relative_humidity=95.0,
            wind_speed_ms=20.0,  # Very windy
            precipitation_mm_per_day=80.0,  # Very wet (10 mm/h)
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        flags = flag_weather_conditions(sample, settings)

        assert not flags.very_hot  # Temperature not extreme
        assert not flags.very_cold
        assert flags.very_windy
        assert flags.very_wet
        assert flags.any_flagged()
        assert flags.count_flagged() == 2

    def test_hot_and_humid_conditions(self, settings):
        """Test hot and humid conditions."""
        sample = WeatherSample(
            temperature_c=34.0,  # Just below air temp threshold
            relative_humidity=85.0,  # High humidity triggers heat index
            wind_speed_ms=2.0,
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        flags = flag_weather_conditions(sample, settings)

        # Should be flagged as very hot due to heat index
        assert flags.very_hot
        assert not flags.very_cold
        assert not flags.very_windy
        assert not flags.very_wet
        assert flags.count_flagged() == 1

    def test_cold_and_windy_conditions(self, settings):
        """Test cold and windy conditions."""
        sample = WeatherSample(
            temperature_c=-8.0,  # Just above air temp threshold
            relative_humidity=70.0,
            wind_speed_ms=18.0,  # Strong wind (triggers wind chill + windy)
            precipitation_mm_per_day=0.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        flags = flag_weather_conditions(sample, settings)

        # Should be flagged as very cold (wind chill) and very windy
        assert not flags.very_hot
        assert flags.very_cold  # Due to wind chill
        assert flags.very_windy  # Due to high wind speed
        assert not flags.very_wet
        assert flags.count_flagged() == 2


class TestEvaluateSampleRisk:
    """Test the comprehensive risk evaluation function."""

    def test_evaluate_sample_risk_comprehensive(self):
        """Test comprehensive risk evaluation output."""
        sample = WeatherSample(
            temperature_c=38.0,
            relative_humidity=75.0,
            wind_speed_ms=15.0,
            precipitation_mm_per_day=60.0,
            timestamp=datetime(2023, 8, 15, 14, 30, tzinfo=UTC),
            latitude=33.4484,  # Phoenix, AZ
            longitude=-112.0740,
        )

        risk_eval = evaluate_sample_risk(sample)

        # Check that all expected fields are present
        assert "temperature_c" in risk_eval
        assert "relative_humidity" in risk_eval
        assert "wind_speed_ms" in risk_eval
        assert "precipitation_mm_per_day" in risk_eval
        assert "heat_index_c" in risk_eval
        assert "wind_chill_c" in risk_eval
        assert "feels_like_c" in risk_eval
        assert "flags" in risk_eval
        assert "any_dangerous" in risk_eval
        assert "danger_count" in risk_eval
        assert "timestamp" in risk_eval
        assert "location" in risk_eval

        # Check flag structure
        flags = risk_eval["flags"]
        assert isinstance(flags, dict)
        assert "very_hot" in flags
        assert "very_cold" in flags
        assert "very_windy" in flags
        assert "very_wet" in flags

        # Check location structure
        location = risk_eval["location"]
        assert location["latitude"] == 33.4484
        assert location["longitude"] == -112.0740

        # Check timestamp format
        assert risk_eval["timestamp"] == "2023-08-15T14:30:00+00:00"


class TestDefaultSettings:
    """Test threshold functions with default settings."""

    def test_functions_work_with_default_settings(self):
        """Test that all functions work without explicit settings."""
        sample = WeatherSample(
            temperature_c=30.0,
            relative_humidity=60.0,
            wind_speed_ms=8.0,
            precipitation_mm_per_day=20.0,
            timestamp=datetime.now(UTC),
            latitude=0.0,
            longitude=0.0,
        )

        # All functions should work without settings parameter
        assert isinstance(is_very_hot(sample), bool)
        assert isinstance(is_very_cold(sample), bool)
        assert isinstance(is_very_windy(sample), bool)
        assert isinstance(is_very_wet(sample), bool)

        flags = flag_weather_conditions(sample)
        assert isinstance(flags, WeatherConditionFlags)

        risk_eval = evaluate_sample_risk(sample)
        assert isinstance(risk_eval, dict)
