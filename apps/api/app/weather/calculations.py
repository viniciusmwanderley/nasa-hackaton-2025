# ABOUTME: Meteorological calculations for outdoor risk assessment
# ABOUTME: Implements Heat Index and Wind Chill formulas with validation

import math


def heat_index(temperature_c: float, relative_humidity: float) -> float | None:
    """
    Calculate Heat Index using the National Weather Service formula.

    The Heat Index is a measure of how hot it feels when relative humidity
    is factored in with the actual air temperature.

    Args:
        temperature_c: Air temperature in Celsius
        relative_humidity: Relative humidity as a percentage (0-100)

    Returns:
        Heat Index in Celsius, or None if conditions don't apply

    Note:
        Heat Index is only meaningful for temperatures >= 26.7°C (80°F)
        and relative humidity >= 40%. Returns None otherwise.

    References:
        - National Weather Service Heat Index formula
        - Rothfusz, L.P.: The Heat Index Equation (1990)
    """
    # Input validation
    if not isinstance(temperature_c, (int, float)):
        raise TypeError("Temperature must be a number")
    if not isinstance(relative_humidity, (int, float)):
        raise TypeError("Relative humidity must be a number")

    if not (0 <= relative_humidity <= 100):
        raise ValueError(
            f"Relative humidity {relative_humidity}% must be between 0-100%"
        )

    # Heat Index only applies to hot conditions
    if temperature_c < 26.7:  # 80°F
        return None
    if relative_humidity < 40:
        return None

    # Convert to Fahrenheit for calculation (NWS formula is in °F)
    temp_f = celsius_to_fahrenheit(temperature_c)
    rh = relative_humidity

    # NWS Heat Index formula (Rothfusz equation)
    # Simple formula for initial approximation
    heat_index_f = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (rh * 0.094))

    # If result >= 80°F, use full regression equation for accuracy
    if heat_index_f >= 80:
        heat_index_f = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * rh
            - 0.22475541 * temp_f * rh
            - 0.00683783 * temp_f * temp_f
            - 0.05481717 * rh * rh
            + 0.00122874 * temp_f * temp_f * rh
            + 0.00085282 * temp_f * rh * rh
            - 0.00000199 * temp_f * temp_f * rh * rh
        )

        # Apply adjustments for extreme conditions
        if rh < 13 and 80 <= temp_f <= 112:
            # Dry condition adjustment
            adjustment = ((13 - rh) / 4) * math.sqrt((17 - abs(temp_f - 95)) / 17)
            heat_index_f -= adjustment
        elif rh > 85 and 80 <= temp_f <= 87:
            # High humidity adjustment
            adjustment = ((rh - 85) / 10) * ((87 - temp_f) / 5)
            heat_index_f += adjustment

    # Convert back to Celsius
    return fahrenheit_to_celsius(heat_index_f)


def wind_chill(temperature_c: float, wind_speed_ms: float) -> float | None:
    """
    Calculate Wind Chill using the National Weather Service formula.

    Wind Chill describes how cold it feels when wind is factored in with
    the actual air temperature.

    Args:
        temperature_c: Air temperature in Celsius
        wind_speed_ms: Wind speed in meters per second

    Returns:
        Wind Chill temperature in Celsius, or None if conditions don't apply

    Note:
        Wind Chill is only meaningful for temperatures <= 10°C (50°F)
        and wind speeds >= 1.34 m/s (3 mph). Returns None otherwise.

    References:
        - National Weather Service Wind Chill formula (2001)
        - Environment Canada Wind Chill model
    """
    # Input validation
    if not isinstance(temperature_c, (int, float)):
        raise TypeError("Temperature must be a number")
    if not isinstance(wind_speed_ms, (int, float)):
        raise TypeError("Wind speed must be a number")

    if wind_speed_ms < 0:
        raise ValueError(f"Wind speed {wind_speed_ms} m/s cannot be negative")

    # Wind Chill only applies to cold and windy conditions
    if temperature_c > 10.0:  # 50°F
        return None
    if wind_speed_ms < 1.34:  # 3 mph
        return None

    # Convert to Fahrenheit and mph for calculation (NWS formula units)
    temp_f = celsius_to_fahrenheit(temperature_c)
    wind_mph = ms_to_mph(wind_speed_ms)

    # NWS Wind Chill formula (2001)
    wind_chill_f = (
        35.74
        + 0.6215 * temp_f
        - 35.75 * (wind_mph**0.16)
        + 0.4275 * temp_f * (wind_mph**0.16)
    )

    # Convert back to Celsius
    return fahrenheit_to_celsius(wind_chill_f)


def feels_like_temperature(
    temperature_c: float,
    relative_humidity: float | None = None,
    wind_speed_ms: float | None = None,
) -> float:
    """
    Calculate the "feels like" temperature considering heat index and wind chill.

    This function automatically determines whether to apply heat index (hot conditions)
    or wind chill (cold conditions) based on the temperature and available data.

    Args:
        temperature_c: Air temperature in Celsius
        relative_humidity: Relative humidity percentage (0-100), optional
        wind_speed_ms: Wind speed in m/s, optional

    Returns:
        "Feels like" temperature in Celsius

    Logic:
        - If temperature >= 26.7°C and humidity available: use heat index
        - If temperature <= 10°C and wind speed available: use wind chill
        - Otherwise: return actual temperature
    """
    if not isinstance(temperature_c, (int, float)):
        raise TypeError("Temperature must be a number")

    # Try heat index for hot conditions
    if temperature_c >= 26.7 and relative_humidity is not None:
        hi = heat_index(temperature_c, relative_humidity)
        if hi is not None:
            return hi

    # Try wind chill for cold conditions
    if temperature_c <= 10.0 and wind_speed_ms is not None:
        wc = wind_chill(temperature_c, wind_speed_ms)
        if wc is not None:
            return wc

    # No adjustment applies, return actual temperature
    return temperature_c


# Utility functions for unit conversions


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return celsius * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32.0) * 5.0 / 9.0


def ms_to_mph(meters_per_second: float) -> float:
    """Convert meters per second to miles per hour."""
    return meters_per_second * 2.23694


def mph_to_ms(miles_per_hour: float) -> float:
    """Convert miles per hour to meters per second."""
    return miles_per_hour / 2.23694


def validate_temperature_range(
    temperature_c: float, min_temp: float = -100, max_temp: float = 100
) -> None:
    """
    Validate temperature is within reasonable meteorological range.

    Args:
        temperature_c: Temperature in Celsius
        min_temp: Minimum allowed temperature (default -100°C)
        max_temp: Maximum allowed temperature (default 100°C)

    Raises:
        ValueError: If temperature is outside the valid range
    """
    if not (min_temp <= temperature_c <= max_temp):
        raise ValueError(
            f"Temperature {temperature_c}°C is outside valid range "
            f"[{min_temp}°C, {max_temp}°C]"
        )
