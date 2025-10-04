# ABOUTME: Comprehensive test suite for meteorological calculations
# ABOUTME: Tests Heat Index, Wind Chill, and utility functions with known values


import pytest

from app.weather.calculations import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    feels_like_temperature,
    heat_index,
    mph_to_ms,
    ms_to_mph,
    validate_temperature_range,
    wind_chill,
)


class TestHeatIndex:
    """Test Heat Index calculations with known reference values."""

    def test_heat_index_basic_calculation(self):
        """Test heat index with standard conditions."""
        # Reference: 35°C (95°F) at 50% humidity should be ~41.1°C (106°F)
        result = heat_index(35.0, 50.0)
        assert result is not None
        assert abs(result - 41.1) < 1.0  # Allow 1°C tolerance

    def test_heat_index_extreme_heat(self):
        """Test heat index with extreme heat conditions."""
        # Reference: 40°C (104°F) at 75% humidity should be very high
        result = heat_index(40.0, 75.0)
        assert result is not None
        assert result > 45.0  # Should be significantly higher than air temp

    def test_heat_index_low_humidity(self):
        """Test heat index with low humidity."""
        # 35°C at 30% humidity - should return None (below 40% threshold)
        result = heat_index(35.0, 30.0)
        assert result is None

    def test_heat_index_cool_temperature(self):
        """Test heat index with temperature too low."""
        # 25°C (below 26.7°C threshold) should return None
        result = heat_index(25.0, 80.0)
        assert result is None

    def test_heat_index_boundary_conditions(self):
        """Test heat index at boundary conditions."""
        # Just above thresholds - should return a value
        result = heat_index(26.8, 40.1)
        assert result is not None

        # Just below thresholds - should return None
        result = heat_index(26.6, 40.0)
        assert result is None
        result = heat_index(26.8, 39.9)
        assert result is None

    def test_heat_index_input_validation(self):
        """Test heat index input validation."""
        # Invalid temperature type
        with pytest.raises(TypeError, match="Temperature must be a number"):
            heat_index("hot", 50.0)

        # Invalid humidity type
        with pytest.raises(TypeError, match="Relative humidity must be a number"):
            heat_index(30.0, "humid")

        # Humidity out of range
        with pytest.raises(
            ValueError, match="Relative humidity .* must be between 0-100%"
        ):
            heat_index(30.0, -5.0)
        with pytest.raises(
            ValueError, match="Relative humidity .* must be between 0-100%"
        ):
            heat_index(30.0, 105.0)

    def test_heat_index_known_nws_values(self):
        """Test with known National Weather Service reference values."""
        # Test: 32.2°C (90°F) at 85% RH
        result = heat_index(32.2, 85.0)
        assert result is not None
        assert abs(result - 47.4) < 1.0  # Calculated value ~47.4°C

        # Test: 37.8°C (100°F) at 50% RH
        result = heat_index(37.8, 50.0)
        assert result is not None
        assert abs(result - 48.0) < 1.0  # Calculated value ~48.0°C


class TestWindChill:
    """Test Wind Chill calculations with known reference values."""

    def test_wind_chill_basic_calculation(self):
        """Test wind chill with standard conditions."""
        # Reference: 0°C (32°F) with 10 m/s (~22 mph) wind
        result = wind_chill(0.0, 10.0)
        assert result is not None
        assert result < 0.0  # Should feel colder than actual temperature
        assert abs(result - (-7.0)) < 1.0  # Calculated value ~-7.0°C

    def test_wind_chill_extreme_cold(self):
        """Test wind chill with extreme cold conditions."""
        # -20°C with strong wind should be very cold
        result = wind_chill(-20.0, 15.0)
        assert result is not None
        assert result < -25.0  # Should feel much colder

    def test_wind_chill_low_wind(self):
        """Test wind chill with insufficient wind speed."""
        # Low wind speed (< 1.34 m/s) should return None
        result = wind_chill(5.0, 1.0)
        assert result is None

    def test_wind_chill_warm_temperature(self):
        """Test wind chill with temperature too warm."""
        # Temperature above 10°C threshold should return None
        result = wind_chill(15.0, 10.0)
        assert result is None

    def test_wind_chill_boundary_conditions(self):
        """Test wind chill at boundary conditions."""
        # Just at thresholds - should return a value
        result = wind_chill(10.0, 1.35)
        assert result is not None

        # Just outside thresholds - should return None
        result = wind_chill(10.1, 5.0)
        assert result is None
        result = wind_chill(5.0, 1.33)
        assert result is None

    def test_wind_chill_input_validation(self):
        """Test wind chill input validation."""
        # Invalid temperature type
        with pytest.raises(TypeError, match="Temperature must be a number"):
            wind_chill("cold", 10.0)

        # Invalid wind speed type
        with pytest.raises(TypeError, match="Wind speed must be a number"):
            wind_chill(0.0, "windy")

        # Negative wind speed
        with pytest.raises(ValueError, match="Wind speed .* cannot be negative"):
            wind_chill(0.0, -5.0)

    def test_wind_chill_known_nws_values(self):
        """Test with known National Weather Service reference values."""
        # NWS reference: -6.7°C (20°F) with 8.9 m/s (20 mph) = -15.6°C (4°F)
        result = wind_chill(-6.7, 8.9)
        assert result is not None
        assert abs(result - (-15.6)) < 2.0  # Allow reasonable tolerance

        # NWS reference: -17.8°C (0°F) with 13.4 m/s (30 mph) = -31.7°C (-25°F)
        result = wind_chill(-17.8, 13.4)
        assert result is not None
        assert abs(result - (-31.7)) < 2.0


class TestFeelsLikeTemperature:
    """Test the comprehensive feels-like temperature function."""

    def test_feels_like_hot_conditions(self):
        """Test feels-like with hot conditions (uses heat index)."""
        result = feels_like_temperature(35.0, relative_humidity=70.0)
        # Should be higher than actual temperature due to heat index
        assert result > 35.0

    def test_feels_like_cold_conditions(self):
        """Test feels-like with cold conditions (uses wind chill)."""
        result = feels_like_temperature(0.0, wind_speed_ms=10.0)
        # Should be lower than actual temperature due to wind chill
        assert result < 0.0

    def test_feels_like_moderate_conditions(self):
        """Test feels-like with moderate conditions (no adjustment)."""
        temp = 20.0
        result = feels_like_temperature(temp, relative_humidity=50.0, wind_speed_ms=3.0)
        # Should return actual temperature (no heat index or wind chill applies)
        assert result == temp

    def test_feels_like_missing_data(self):
        """Test feels-like with missing humidity or wind data."""
        temp = 35.0
        # No humidity data - can't calculate heat index
        result = feels_like_temperature(temp)
        assert result == temp

        # No wind data - can't calculate wind chill
        temp = 0.0
        result = feels_like_temperature(temp, relative_humidity=50.0)
        assert result == temp

    def test_feels_like_input_validation(self):
        """Test feels-like input validation."""
        with pytest.raises(TypeError, match="Temperature must be a number"):
            feels_like_temperature("warm")


class TestUnitConversions:
    """Test unit conversion utility functions."""

    def test_celsius_fahrenheit_conversion(self):
        """Test temperature conversions."""
        # Known conversion points
        assert abs(celsius_to_fahrenheit(0.0) - 32.0) < 0.001
        assert abs(celsius_to_fahrenheit(100.0) - 212.0) < 0.001
        assert abs(celsius_to_fahrenheit(-40.0) - (-40.0)) < 0.001

        assert abs(fahrenheit_to_celsius(32.0) - 0.0) < 0.001
        assert abs(fahrenheit_to_celsius(212.0) - 100.0) < 0.001
        assert abs(fahrenheit_to_celsius(-40.0) - (-40.0)) < 0.001

    def test_round_trip_conversions(self):
        """Test that conversions are reversible."""
        test_temps = [-40, -10, 0, 20, 37.5, 100]
        for temp_c in test_temps:
            # C -> F -> C should return original value
            temp_f = celsius_to_fahrenheit(temp_c)
            back_to_c = fahrenheit_to_celsius(temp_f)
            assert abs(back_to_c - temp_c) < 0.001

    def test_wind_speed_conversion(self):
        """Test wind speed conversions."""
        # Known conversion points
        assert abs(ms_to_mph(1.0) - 2.23694) < 0.001
        assert abs(mph_to_ms(2.23694) - 1.0) < 0.001

        # Round trip test
        test_speeds = [0, 1.34, 5.0, 10.0, 25.0]
        for speed_ms in test_speeds:
            speed_mph = ms_to_mph(speed_ms)
            back_to_ms = mph_to_ms(speed_mph)
            assert abs(back_to_ms - speed_ms) < 0.001


class TestTemperatureValidation:
    """Test temperature range validation."""

    def test_validate_temperature_normal_range(self):
        """Test validation with normal temperature ranges."""
        # Should not raise for normal temperatures
        validate_temperature_range(25.0)
        validate_temperature_range(-10.0)
        validate_temperature_range(50.0)

    def test_validate_temperature_custom_range(self):
        """Test validation with custom ranges."""
        validate_temperature_range(15.0, min_temp=10.0, max_temp=20.0)

        with pytest.raises(ValueError, match="Temperature .* is outside valid range"):
            validate_temperature_range(5.0, min_temp=10.0, max_temp=20.0)

        with pytest.raises(ValueError, match="Temperature .* is outside valid range"):
            validate_temperature_range(25.0, min_temp=10.0, max_temp=20.0)

    def test_validate_temperature_extreme_values(self):
        """Test validation with extreme temperature values."""
        with pytest.raises(ValueError, match="Temperature .* is outside valid range"):
            validate_temperature_range(-150.0)  # Too cold

        with pytest.raises(ValueError, match="Temperature .* is outside valid range"):
            validate_temperature_range(150.0)  # Too hot


class TestEdgeCasesAndPrecision:
    """Test edge cases and numerical precision."""

    def test_heat_index_regression_equation_thresholds(self):
        """Test heat index regression equation activation."""
        # The full regression equation should activate at HI >= 80°F
        # Test conditions that should trigger both simple and full equations

        # Conditions that should use simple equation initially
        temp_c = 27.0  # ~80.6°F
        rh = 45.0
        result = heat_index(temp_c, rh)
        assert result is not None

    def test_wind_chill_very_low_wind(self):
        """Test wind chill with wind speeds just above threshold."""
        # Test with wind speed just above 1.34 m/s threshold
        result = wind_chill(5.0, 1.35)
        assert result is not None
        assert result < 5.0  # Should feel colder

    def test_numerical_precision(self):
        """Test calculations maintain reasonable precision."""
        # Test that small changes in input produce reasonable output changes
        hi1 = heat_index(30.0, 60.0)
        hi2 = heat_index(30.1, 60.0)  # Tiny temperature increase

        if hi1 is not None and hi2 is not None:
            # Small input change should produce small output change
            assert abs(hi2 - hi1) < 1.0

    def test_zero_values(self):
        """Test calculations with zero values."""
        # Wind chill with zero wind (should return None due to threshold)
        result = wind_chill(5.0, 0.0)
        assert result is None

        # Heat index with zero humidity (should return None)
        result = heat_index(30.0, 0.0)
        assert result is None
