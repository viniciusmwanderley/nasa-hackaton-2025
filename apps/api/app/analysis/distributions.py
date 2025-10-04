# ABOUTME: Distribution analysis for meteorological parameters
# ABOUTME: Computes histograms and descriptive statistics for weather variables


import numpy as np

from app.config import Settings
from app.models import Distribution, HistogramBin
from app.weather.calculations import heat_index, wind_chill
from app.weather.thresholds import WeatherSample


def calculate_histogram_bins(
    values: np.ndarray, n_bins: int = 20, threshold_value: float | None = None
) -> tuple[list[float], list[int]]:
    """
    Calculate histogram bins for a dataset.

    Args:
        values: Array of values to bin
        n_bins: Number of bins to create
        threshold_value: Optional threshold to include as a bin edge

    Returns:
        Tuple of (bin_edges, counts)
    """
    if len(values) == 0:
        return [], []

    # Remove any NaN values
    clean_values = values[~np.isnan(values)]
    if len(clean_values) == 0:
        return [], []

    # Determine bin edges
    min_val, max_val = clean_values.min(), clean_values.max()

    # If we have a threshold, ensure it's included as a bin edge
    if threshold_value is not None and min_val <= threshold_value <= max_val:
        # Create bins that include the threshold as an edge
        lower_bins = np.linspace(min_val, threshold_value, n_bins // 2 + 1)
        upper_bins = np.linspace(threshold_value, max_val, n_bins // 2 + 1)[1:]
        bin_edges = np.concatenate([lower_bins, upper_bins])
    else:
        bin_edges = np.linspace(min_val, max_val, n_bins + 1)

    # Calculate histogram
    counts, _ = np.histogram(clean_values, bins=bin_edges)

    return bin_edges.tolist(), counts.tolist()


def create_distribution(
    parameter: str,
    unit: str,
    values: np.ndarray,
    threshold_value: float | None = None,
    n_bins: int = 20,
) -> Distribution:
    """
    Create a Distribution object from parameter values.

    Args:
        parameter: Name of the parameter
        unit: Unit of measurement
        values: Array of parameter values
        threshold_value: Optional threshold value for this parameter
        n_bins: Number of histogram bins

    Returns:
        Distribution object with histogram and statistics
    """
    # Remove NaN values for calculations
    clean_values = values[~np.isnan(values)]

    if len(clean_values) == 0:
        # Return empty distribution for no data
        return Distribution(
            parameter=parameter,
            unit=unit,
            bins=[],
            mean=0.0,
            median=0.0,
            std_dev=0.0,
            threshold_value=threshold_value,
        )

    # Calculate histogram
    bin_edges, counts = calculate_histogram_bins(clean_values, n_bins, threshold_value)

    # Create histogram bins
    bins = []
    total_samples = len(clean_values)

    for i in range(len(counts)):
        if i < len(bin_edges) - 1:
            lower = bin_edges[i]
            upper = bin_edges[i + 1]
            count = counts[i]
            frequency = count / total_samples if total_samples > 0 else 0.0

            bins.append(
                HistogramBin(
                    lower_bound=lower,
                    upper_bound=upper,
                    count=count,
                    frequency=frequency,
                )
            )

    # Calculate descriptive statistics
    mean_val = float(np.mean(clean_values))
    median_val = float(np.median(clean_values))
    std_dev_val = float(np.std(clean_values, ddof=1)) if len(clean_values) > 1 else 0.0

    return Distribution(
        parameter=parameter,
        unit=unit,
        bins=bins,
        mean=mean_val,
        median=median_val,
        std_dev=std_dev_val,
        threshold_value=threshold_value,
    )


def calculate_distributions(
    samples: list[WeatherSample], settings: Settings
) -> list[Distribution]:
    """
    Calculate distributions for all meteorological parameters.

    Args:
        samples: List of weather samples
        settings: Configuration settings with thresholds

    Returns:
        List of Distribution objects for each parameter
    """
    if not samples:
        return []

    # Extract parameter arrays
    temperatures = np.array([s.temperature_c for s in samples])
    humidities = np.array([s.relative_humidity for s in samples])
    wind_speeds = np.array([s.wind_speed_ms for s in samples])
    precipitations = np.array([s.precipitation_mm_per_day for s in samples])

    # Calculate derived parameters - vectorize the functions
    heat_indices = np.array(
        [
            heat_index(temp, hum) if heat_index(temp, hum) is not None else np.nan
            for temp, hum in zip(temperatures, humidities, strict=False)
        ]
    )

    wind_chills = np.array(
        [
            wind_chill(temp, ws) if wind_chill(temp, ws) is not None else np.nan
            for temp, ws in zip(temperatures, wind_speeds, strict=False)
        ]
    )

    distributions = []

    # Temperature distribution
    distributions.append(
        create_distribution(parameter="temperature", unit="°C", values=temperatures)
    )

    # Humidity distribution
    distributions.append(
        create_distribution(parameter="relative_humidity", unit="%", values=humidities)
    )

    # Wind speed distribution
    distributions.append(
        create_distribution(
            parameter="wind_speed",
            unit="m/s",
            values=wind_speeds,
            threshold_value=settings.thresholds_wind_ms,
        )
    )

    # Precipitation distribution (convert to mm/h for threshold comparison)
    precip_mm_per_h = precipitations / 24.0  # Convert daily to hourly average
    distributions.append(
        create_distribution(
            parameter="precipitation",
            unit="mm/h",
            values=precip_mm_per_h,
            threshold_value=settings.thresholds_rain_mm_per_h,
        )
    )

    # Heat index distribution
    distributions.append(
        create_distribution(
            parameter="heat_index",
            unit="°C",
            values=heat_indices,
            threshold_value=settings.thresholds_hi_hot_c,
        )
    )

    # Wind chill distribution (only for valid cases)
    valid_wc_mask = ~np.isnan(wind_chills)
    if np.any(valid_wc_mask):
        distributions.append(
            create_distribution(
                parameter="wind_chill",
                unit="°C",
                values=wind_chills[valid_wc_mask],
                threshold_value=settings.thresholds_wct_cold_c,
            )
        )

    return distributions
