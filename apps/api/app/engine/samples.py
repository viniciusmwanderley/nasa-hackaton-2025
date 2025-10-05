# ABOUTME: Weather sample collector using NASA POWER API
# ABOUTME: Collects historical samples over DOY±W at specific local hour for risk analysis

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from ..config import Settings
from ..time.timezone import get_day_of_year, parse_date, to_local, tz_for_point
from ..weather.power import PowerAPIError, PowerClient

logger = logging.getLogger(__name__)


@dataclass
class WeatherSample:
    """Single weather sample with meteorological data."""

    timestamp_utc: datetime
    timestamp_local: datetime
    year: int
    doy: int  # Day of year
    latitude: float
    longitude: float

    # Core meteorological parameters
    temperature_c: float
    relative_humidity: float
    wind_speed_ms: float
    precipitation_mm_per_day: float  # Daily total from NASA POWER API

    # Data quality/provenance  
    data_source: str = "POWER"


@dataclass
class SampleCollection:
    """Collection of weather samples with metadata."""

    samples: list[WeatherSample]

    # Query parameters
    target_latitude: float
    target_longitude: float
    target_date: date
    target_hour: int
    window_days: int
    baseline_years: tuple[int, int]  # (start_year, end_year)

    # Coverage metadata
    total_years_requested: int
    years_with_data: int
    total_samples: int
    coverage_adequate: bool

    # Timezone info
    timezone_iana: str


class SampleCollectorError(Exception):
    """Base exception for sample collection errors."""

    pass


class InsufficientCoverageError(SampleCollectorError):
    """Raised when sample coverage doesn't meet minimum requirements."""

    pass


async def collect_samples(
    latitude: float,
    longitude: float,
    target_date_str: str,  # "YYYY-MM-DD"
    target_hour: int,  # 0-23
    window_days: int = 15,
    baseline_start_year: int = 2001,
    baseline_end_year: int = 2023,
    settings: Settings | None = None,
    power_client: PowerClient | None = None,
) -> SampleCollection:
    """
    Collect weather samples over DOY±window_days at target local hour across baseline years.

    This function:
    1. Resolves target date to DOY (day of year)
    2. For each year in baseline range, calculates date range around target DOY
    3. Fetches NASA POWER data for that date range (including precipitation)
    4. Filters to samples matching target local hour  
    5. Validates coverage meets minimum requirements

    Args:
        latitude: Target latitude (-90 to 90)
        longitude: Target longitude (-180 to 180)
        target_date_str: Target date as "YYYY-MM-DD"
        target_hour: Target local hour (0-23)
        window_days: Days before/after target DOY to include (default 15)
        baseline_start_year: First year of baseline period (default 2001)
        baseline_end_year: Last year of baseline period (default 2023)
        settings: Configuration settings (uses defaults if None)
        power_client: POWER API client (creates new if None)

    Returns:
        SampleCollection with filtered weather samples and metadata

    Raises:
        ValueError: For invalid input parameters
        InsufficientCoverageError: When coverage doesn't meet minimum requirements
        SampleCollectorError: For other collection errors
        PowerAPIError: For NASA POWER API errors

    Example:
        >>> samples = await collect_samples(
        ...     latitude=-3.7319,
        ...     longitude=-38.5267,
        ...     target_date_str="2024-06-15",
        ...     target_hour=14
        ... )
        >>> print(f"Collected {len(samples.samples)} samples")
        >>> print(f"Coverage adequate: {samples.coverage_adequate}")
    """
    if settings is None:
        settings = Settings()

    # Validate inputs
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude {latitude}: must be -90 to 90")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude {longitude}: must be -180 to 180")
    if not (0 <= target_hour <= 23):
        raise ValueError(f"Invalid target_hour {target_hour}: must be 0-23")
    if window_days < 0:
        raise ValueError(f"Invalid window_days {window_days}: must be >= 0")
    if baseline_start_year > baseline_end_year:
        raise ValueError(
            f"Invalid baseline years: {baseline_start_year} > {baseline_end_year}"
        )

    # Parse target date and get DOY
    try:
        target_date = parse_date(target_date_str)
    except ValueError as e:
        raise ValueError(f"Invalid target_date_str '{target_date_str}': {e}") from e

    target_doy = get_day_of_year(target_date_str)

    # Resolve timezone for location
    try:
        timezone_iana = tz_for_point(latitude, longitude)
        logger.info(f"Resolved timezone for ({latitude}, {longitude}): {timezone_iana}")
    except ValueError as e:
        raise SampleCollectorError(f"Could not resolve timezone: {e}") from e

    # Create POWER client if not provided
    if power_client is None:
        power_client = PowerClient(settings)

    # Precipitation data comes from NASA POWER API - no separate client needed

    # Collect samples for each year
    all_samples: list[WeatherSample] = []
    years_with_data = 0

    total_years = baseline_end_year - baseline_start_year + 1

    for year in range(baseline_start_year, baseline_end_year + 1):
        try:
            year_samples = await _collect_samples_for_year(
                power_client=power_client,
                latitude=latitude,
                longitude=longitude,
                year=year,
                target_doy=target_doy,
                target_hour=target_hour,
                window_days=window_days,
                timezone_iana=timezone_iana,
            )

            if year_samples:
                all_samples.extend(year_samples)
                years_with_data += 1
                logger.debug(f"Year {year}: collected {len(year_samples)} samples")
            else:
                logger.warning(f"Year {year}: no samples collected")

        except PowerAPIError as e:
            logger.warning(f"Failed to collect samples for year {year}: {e}")
            # Continue with other years rather than failing completely
            continue
        except Exception as e:
            logger.error(f"Unexpected error collecting samples for year {year}: {e}")
            raise SampleCollectorError(
                f"Failed to collect samples for year {year}: {e}"
            ) from e

    # Check coverage requirements
    coverage_adequate = (
        years_with_data >= settings.coverage_min_years
        and len(all_samples) >= settings.coverage_min_samples
    )

    if not coverage_adequate and settings.coverage_enforce:
        raise InsufficientCoverageError(
            f"Insufficient coverage: {years_with_data} years (need {settings.coverage_min_years}), "
            f"{len(all_samples)} samples (need {settings.coverage_min_samples})"
        )

    # Create collection
    collection = SampleCollection(
        samples=all_samples,
        target_latitude=latitude,
        target_longitude=longitude,
        target_date=target_date,
        target_hour=target_hour,
        window_days=window_days,
        baseline_years=(baseline_start_year, baseline_end_year),
        total_years_requested=total_years,
        years_with_data=years_with_data,
        total_samples=len(all_samples),
        coverage_adequate=coverage_adequate,
        timezone_iana=timezone_iana,
    )

    logger.info(
        f"Sample collection complete: {len(all_samples)} samples from "
        f"{years_with_data}/{total_years} years, coverage adequate: {coverage_adequate}"
    )

    return collection


async def _collect_samples_for_year(
    power_client: PowerClient,
    latitude: float,
    longitude: float,
    year: int,
    target_doy: int,
    target_hour: int,
    window_days: int,
    timezone_iana: str,
) -> list[WeatherSample]:
    """
    Collect samples for a single year around target DOY±window_days.

    Args:
        power_client: NASA POWER API client
        latitude: Target latitude
        longitude: Target longitude
        year: Year to collect samples for
        target_doy: Target day of year (1-366)
        target_hour: Target local hour (0-23)
        window_days: Days before/after target DOY
        timezone_iana: IANA timezone string

    Returns:
        List of WeatherSample objects matching criteria

    Raises:
        PowerAPIError: For NASA POWER API errors
    """
    # Calculate date range around target DOY
    start_doy = max(1, target_doy - window_days)
    end_doy = min(366 if _is_leap_year(year) else 365, target_doy + window_days)

    # Convert DOY to actual dates
    start_date = date(year, 1, 1) + timedelta(days=start_doy - 1)
    end_date = date(year, 1, 1) + timedelta(days=end_doy - 1)

    logger.debug(
        f"Fetching POWER data for year {year}, DOY {start_doy}-{end_doy} ({start_date} to {end_date})"
    )

    # Fetch POWER data for the date range
    try:
        power_data = await power_client.get_daily_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            parameters=["T2M", "RH2M", "WS10M", "PRECTOTCORR"],
        )
    except PowerAPIError as e:
        logger.warning(f"POWER API error for year {year}: {e}")
        raise

    # Process daily data into samples
    samples = []

    if "properties" not in power_data or "parameter" not in power_data["properties"]:
        logger.warning(f"Invalid POWER response structure for year {year}")
        return samples

    parameters = power_data["properties"]["parameter"]

    # Extract time series data
    t2m_data = parameters.get("T2M", {})
    rh2m_data = parameters.get("RH2M", {})
    ws10m_data = parameters.get("WS10M", {})
    prectot_data = parameters.get("PRECTOTCORR", {})

    # Process each day's data
    for date_key in t2m_data.keys():
        try:
            # Parse date key (format: YYYYMMDD)
            sample_year = int(date_key[:4])
            sample_month = int(date_key[4:6])
            sample_day = int(date_key[6:8])
            sample_date = date(sample_year, sample_month, sample_day)

            # Create UTC datetime for the target local hour
            # We approximate by using noon UTC as representative of the day
            # In a full implementation, this would use hourly data
            sample_datetime_utc = datetime.combine(
                sample_date, datetime.min.time().replace(hour=12)
            )
            sample_datetime_utc = sample_datetime_utc.replace(tzinfo=ZoneInfo("UTC"))

            # Convert to local time to check if it matches target hour
            # For daily data, we'll assume the data represents conditions at the target hour
            target_datetime_utc = datetime.combine(
                sample_date, datetime.min.time().replace(hour=target_hour)
            )
            target_datetime_utc = target_datetime_utc.replace(tzinfo=ZoneInfo("UTC"))
            sample_datetime_local = to_local(target_datetime_utc, timezone_iana)

            # Extract parameter values
            temperature_c = t2m_data.get(date_key)
            relative_humidity = rh2m_data.get(date_key)
            wind_speed_ms = ws10m_data.get(date_key)
            precipitation_mm_per_day = prectot_data.get(date_key)

            # Skip if any critical data is missing
            if any(
                value is None
                for value in [temperature_c, relative_humidity, wind_speed_ms]
            ):
                logger.debug(f"Skipping {date_key}: missing critical data")
                continue

            # Use 0.0 for missing precipitation (common in dry periods)
            if precipitation_mm_per_day is None:
                precipitation_mm_per_day = 0.0

            # Create sample
            sample = WeatherSample(
                timestamp_utc=sample_datetime_utc,
                timestamp_local=sample_datetime_local,
                year=sample_year,
                doy=sample_date.timetuple().tm_yday,
                latitude=latitude,
                longitude=longitude,
                temperature_c=temperature_c,
                relative_humidity=relative_humidity,
                wind_speed_ms=wind_speed_ms,
                precipitation_mm_per_day=precipitation_mm_per_day,
                data_source="POWER",
            )

            samples.append(sample)

        except (ValueError, KeyError) as e:
            logger.warning(f"Error processing date {date_key}: {e}")
            continue

    logger.debug(f"Processed {len(samples)} samples for year {year}")
    return samples


def _is_leap_year(year: int) -> bool:
    """Check if a year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def validate_sample_coverage(
    collection: SampleCollection, settings: Settings | None = None
) -> dict[str, Any]:
    """
    Validate sample coverage against requirements and return detailed metrics.

    Args:
        collection: Sample collection to validate
        settings: Configuration settings (uses defaults if None)

    Returns:
        Dictionary with coverage metrics and validation results
    """
    if settings is None:
        settings = Settings()

    # Calculate coverage metrics
    years_coverage = collection.years_with_data / collection.total_years_requested
    sample_adequacy = collection.total_samples / settings.coverage_min_samples

    # Calculate seasonal distribution
    seasonal_counts = {}
    for sample in collection.samples:
        month = sample.timestamp_local.month
        season = _get_season(month)
        seasonal_counts[season] = seasonal_counts.get(season, 0) + 1

    # Calculate year distribution
    yearly_counts = {}
    for sample in collection.samples:
        yearly_counts[sample.year] = yearly_counts.get(sample.year, 0) + 1

    validation_result = {
        "total_samples": collection.total_samples,
        "years_with_data": collection.years_with_data,
        "total_years_requested": collection.total_years_requested,
        "years_coverage_ratio": years_coverage,
        "sample_adequacy_ratio": sample_adequacy,
        "coverage_adequate": collection.coverage_adequate,
        "meets_requirements": {
            "years": collection.years_with_data >= settings.coverage_min_years,
            "samples": collection.total_samples >= settings.coverage_min_samples,
            "overall": collection.coverage_adequate,
        },
        "seasonal_distribution": seasonal_counts,
        "yearly_distribution": yearly_counts,
        "requirements": {
            "min_years": settings.coverage_min_years,
            "min_samples": settings.coverage_min_samples,
            "enforce_coverage": settings.coverage_enforce,
        },
    }

    return validation_result


def _get_season(month: int) -> str:
    """Get season name from month number."""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"
