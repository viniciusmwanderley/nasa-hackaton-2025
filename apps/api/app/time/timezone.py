# ABOUTME: Timezone utilities for lat/lon resolution and local time handling
# ABOUTME: Provides IANA timezone lookup, local time conversion, and DOY calculations

from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

# Global timezone finder instance
_tz_finder = TimezoneFinder()


@lru_cache(maxsize=1000)
def tz_for_point(lat: float, lon: float) -> str:
    """
    Resolve IANA timezone from latitude and longitude coordinates.

    Uses timezonefinder library with LRU caching for performance.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees

    Returns:
        IANA timezone string (e.g., 'America/Fortaleza')

    Raises:
        ValueError: If coordinates are invalid or no timezone found
    """
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")

    if not (-180 <= lon <= 180):
        raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180.")

    timezone = _tz_finder.timezone_at(lat=lat, lng=lon)

    if timezone is None:
        raise ValueError(f"No timezone found for coordinates ({lat}, {lon})")

    return timezone


def to_local(dt_utc: datetime, iana_zone: str) -> datetime:
    """
    Convert UTC datetime to local civil time in specified timezone.

    Args:
        dt_utc: UTC datetime (must be timezone-aware)
        iana_zone: IANA timezone string (e.g., 'America/Fortaleza')

    Returns:
        Datetime in local timezone

    Raises:
        ValueError: If input datetime is not UTC or timezone is invalid
    """
    if dt_utc.tzinfo is None:
        raise ValueError("Input datetime must be timezone-aware")

    if dt_utc.tzinfo != ZoneInfo("UTC"):
        raise ValueError("Input datetime must be in UTC timezone")

    try:
        local_tz = ZoneInfo(iana_zone)
    except Exception as e:
        raise ValueError(f"Invalid timezone '{iana_zone}': {e}")

    return dt_utc.astimezone(local_tz)


def local_hour_matches(dt_utc: datetime, iana_zone: str, target_hour: int) -> bool:
    """
    Check if UTC datetime matches target local hour in specified timezone.

    Args:
        dt_utc: UTC datetime (must be timezone-aware)
        iana_zone: IANA timezone string
        target_hour: Target local hour (0-23)

    Returns:
        True if local hour matches target hour

    Raises:
        ValueError: If target_hour is not 0-23
    """
    if not (0 <= target_hour <= 23):
        raise ValueError(f"Invalid hour: {target_hour}. Must be 0-23.")

    dt_local = to_local(dt_utc, iana_zone)
    return dt_local.hour == target_hour


def parse_date(date_str: str) -> date:
    """
    Parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Date object

    Raises:
        ValueError: If date string format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD. {e}")


def doy(date_obj: date) -> int:
    """
    Calculate day-of-year (1-365/366) for given date.

    Args:
        date_obj: Date object

    Returns:
        Day of year (1-based)
    """
    return date_obj.timetuple().tm_yday


def parse_hour(hour_str: str) -> int:
    """
    Parse hour string in HH:00 format.

    Args:
        hour_str: Hour string in HH:00 format

    Returns:
        Hour as integer (0-23)

    Raises:
        ValueError: If hour string format is invalid
    """
    try:
        # Parse as time and validate format
        parsed_time = datetime.strptime(hour_str, "%H:%M").time()

        # Ensure minutes are 00
        if parsed_time.minute != 0:
            raise ValueError("Minutes must be 00")

        return parsed_time.hour

    except ValueError as e:
        raise ValueError(f"Invalid hour format '{hour_str}'. Expected HH:00. {e}")


def get_day_of_year(date_str: str) -> int:
    """
    Get day-of-year from date string.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Day of year (1-based)
    """
    date_obj = parse_date(date_str)
    return doy(date_obj)


def build_date_range_for_doy(target_doy: int, window_days: int) -> list[int]:
    """
    Build list of day-of-year values for DOY ± window_days.

    Handles year boundary wrapping (e.g., DOY 3 ± 5 includes DOY 361-365 and 1-8).

    Args:
        target_doy: Target day of year (1-365)
        window_days: Window size (e.g., 7 for ±7 days)

    Returns:
        List of day-of-year values in range

    Raises:
        ValueError: If target_doy is invalid
    """
    if not (1 <= target_doy <= 365):
        raise ValueError(f"Invalid DOY: {target_doy}. Must be 1-365.")

    if window_days < 0:
        raise ValueError(f"Invalid window_days: {window_days}. Must be >= 0.")

    doy_range = []

    for offset in range(-window_days, window_days + 1):
        doy_val = target_doy + offset

        # Handle year boundary wrapping
        if doy_val < 1:
            doy_val = 365 + doy_val  # Wrap to end of year
        elif doy_val > 365:
            doy_val = doy_val - 365  # Wrap to start of year

        doy_range.append(doy_val)

    return sorted(list(set(doy_range)))  # Remove duplicates and sort
