# ABOUTME: Weather analysis service containing NASA POWER API integration and processing logic
# ABOUTME: Provides core weather data fetching and statistical analysis functionality

import time
import random
import datetime as dt
from typing import Dict, List, Optional, Any

import requests
import numpy as np

from ..models.weather import Granularity, AnalysisMode


class WeatherDataService:
    """Service for fetching and processing weather data from NASA POWER API."""
    
    BASE_URL = "https://power.larc.nasa.gov/api/temporal"
    API_PATHS = {
        Granularity.DAILY: "daily/point",
        Granularity.HOURLY: "hourly/point",
        "climatology": "climatology/point",
    }
    DEFAULT_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS10M"]
    DEFAULT_COMMUNITY = "SB"

    def __init__(self):
        self.session = requests.Session()

    def http_get(self, url: str, params: dict, retries: int = 4, timeout: int = 120) -> dict:
        """Make HTTP GET request with retries and timing."""
        start_time = time.perf_counter()
        for attempt in range(retries):
            try:
                r = self.session.get(url, params=params, timeout=timeout)
                r.raise_for_status()
                duration = time.perf_counter() - start_time
                print(f"    [TIMER] Request to {r.url.split('?')[0]} completed in {duration:.2f} seconds.")
                return r.json()
            except requests.RequestException as e:
                is_retryable = "r" not in locals() or r.status_code in (429,) or 500 <= r.status_code < 600
                if attempt == retries - 1 or not is_retryable:
                    print(f"Request error: {r.status_code if 'r' in locals() else 'N/A'} - {r.text if 'r' in locals() else e}")
                    raise e
                time.sleep((2**attempt) * random.uniform(0.8, 1.2))
        raise RuntimeError("Maximum retries exceeded")

    def fetch_temporal_data(
        self,
        lat: float,
        lon: float,
        granularity: Granularity,
        start_date: dt.date,
        end_date: dt.date,
        parameters: List[str],
    ) -> Dict[str, Any]:
        """Fetch temporal weather data from NASA POWER API."""
        path = self.API_PATHS[granularity]
        params = {
            "latitude": lat,
            "longitude": lon,
            "parameters": ",".join(parameters),
            "community": self.DEFAULT_COMMUNITY,
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "format": "JSON",
        }
        return self.http_get(f"{self.BASE_URL}/{path}", params)

    def fetch_climatology(self, lat: float, lon: float, parameters: List[str]) -> Dict[str, Any]:
        """Fetch climatology data from NASA POWER API."""
        path = self.API_PATHS["climatology"]
        params = {
            "latitude": lat,
            "longitude": lon,
            "parameters": ",".join(parameters),
            "community": self.DEFAULT_COMMUNITY,
            "format": "JSON",
        }
        return self.http_get(f"{self.BASE_URL}/{path}", params)

    def extract_param_series(self, json_obj: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Extract parameter series from API response."""
        try:
            params = json_obj["properties"]["parameter"]
            for param, series in params.items():
                for date_key, value in series.items():
                    if value == -999:
                        series[date_key] = None
            return params
        except KeyError:
            return {}

    def extract_climatology_monthly(self, json_obj: Dict[str, Any]) -> Dict[str, Dict[int, float]]:
        """Extract monthly climatology data."""
        param_series = self.extract_param_series(json_obj)
        result: Dict[str, Dict[int, float]] = {}
        for param, monthly_data in param_series.items():
            month_map: Dict[int, float] = {}
            for month_key, value in monthly_data.items():
                if month_key.isdigit() and 1 <= int(month_key) <= 12:
                    month_num = int(month_key)
                elif len(month_key) == 3 and month_key.isalpha() and month_key != "ANN":
                    try:
                        month_num = dt.datetime.strptime(month_key, "%b").month
                    except ValueError:
                        continue
                else:
                    continue
                if value is not None:
                    month_map[month_num] = float(value)
            result[param] = month_map
        return result

    def basic_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values."""
        valid_values = [v for v in values if v is not None and not np.isnan(v)]
        if not valid_values:
            keys = ["count", "mean", "median", "min", "max", "std", "p10", "p25", "p75", "p90"]
            return {k: float("nan") for k in keys}
        a = np.array(valid_values, dtype=float)
        return {
            "count": int(a.size),
            "mean": float(np.nanmean(a)),
            "median": float(np.nanmedian(a)),
            "min": float(np.nanmin(a)),
            "max": float(np.nanmax(a)),
            "std": float(np.nanstd(a, ddof=0)),
            "p10": float(np.nanpercentile(a, 10)),
            "p25": float(np.nanpercentile(a, 25)),
            "p75": float(np.nanpercentile(a, 75)),
            "p90": float(np.nanpercentile(a, 90)),
        }

    def filter_series_by_datetime(
        self,
        series: Dict[str, float],
        target_dt: dt.datetime,
        granularity: Granularity,
        window_days: int,
    ) -> List[float]:
        """Filter time series data by datetime window."""
        target_doy = target_dt.timetuple().tm_yday
        doy_range = {(target_doy + i - 1) % 365 + 1 for i in range(-window_days, window_days + 1)}
        values: List[float] = []
        date_format = "%Y%m%d" if granularity == Granularity.DAILY else "%Y%m%d%H"
        for date_str, value in series.items():
            if value is None:
                continue
            try:
                d = dt.datetime.strptime(date_str, date_format)
                is_in_day_window = d.timetuple().tm_yday in doy_range
                is_correct_hour = True if granularity == Granularity.DAILY else d.hour == target_dt.hour
                if is_in_day_window and is_correct_hour:
                    values.append(float(value))
            except (ValueError, TypeError):
                continue
        return values

    def calculate_heat_index(self, temp_c: float, rh_percent: float) -> Optional[float]:
        """Calculate heat index from temperature and relative humidity."""
        if temp_c is None or rh_percent is None or np.isnan(temp_c) or np.isnan(rh_percent):
            return None
        if temp_c < 26.7 or rh_percent < 40:
            return temp_c
        t_f = temp_c * 9 / 5 + 32
        hi_f = (
            -42.379
            + 2.04901523 * t_f
            + 10.14333127 * rh_percent
            - 0.22475541 * t_f * rh_percent
            - 6.83783e-3 * t_f**2
            - 5.481717e-2 * rh_percent**2
            + 1.22874e-3 * t_f**2 * rh_percent
            + 8.5282e-4 * t_f * rh_percent**2
            - 1.99e-6 * t_f**2 * rh_percent**2
        )
        return (hi_f - 32) * 5 / 9

    def analyze_weather(
        self,
        lat: float,
        lon: float,
        target_dt: dt.datetime,
        granularity: Granularity = Granularity.DAILY,
        parameters: Optional[List[str]] = None,
        start_year: int = 2005,
        window_days: int = 7,
        hourly_chunk_years: int = 5,
    ) -> Dict[str, Any]:
        """Main weather analysis function."""
        if parameters is None:
            parameters = self.DEFAULT_PARAMS
        params_to_fetch = list(parameters)
        if granularity == Granularity.HOURLY:
            invalid_hourly_params = {"T2M_MAX", "T2M_MIN"}
            params_to_fetch = [p for p in params_to_fetch if p not in invalid_hourly_params]
        required_params = {"T2M", "RH2M"}
        params_to_fetch = list(set(params_to_fetch) | required_params)

        end_date = dt.datetime.now(dt.timezone.utc).date()
        start_date = dt.date(start_year, 1, 1)

        print("Fetching climatology data...")
        clim_json = self.fetch_climatology(lat, lon, params_to_fetch)
        clim_map = self.extract_climatology_monthly(clim_json)
        print("Climatology data obtained.")

        all_series: Dict[str, Dict[str, float]] = {p: {} for p in params_to_fetch}

        historical_fetch_start = time.perf_counter()

        if granularity == Granularity.DAILY:
            print(f"Fetching daily data from {start_date} to {end_date} in single request...")
            try:
                historical_json = self.fetch_temporal_data(
                    lat, lon, granularity, start_date, end_date, params_to_fetch
                )
                all_series = self.extract_param_series(historical_json)
            except Exception as e:
                print(f"Warning: Failed to fetch daily historical data. Error: {e}")
        else:  # Granularity.HOURLY
            print(f"Fetching hourly data from {start_date.year} to {end_date.year} (in {hourly_chunk_years}-year chunks)...")
            for year in range(start_date.year, end_date.year + 1, hourly_chunk_years):
                chunk_start_date = dt.date(year, 1, 1)
                chunk_end_year = min(year + hourly_chunk_years - 1, end_date.year)
                chunk_end_date = min(dt.date(chunk_end_year, 12, 31), end_date)

                print(f"  - Fetching chunk from {chunk_start_date.year} to {chunk_end_date.year}...")
                try:
                    chunk = self.fetch_temporal_data(
                        lat, lon, granularity, chunk_start_date, chunk_end_date, params_to_fetch
                    )
                    param_block = self.extract_param_series(chunk)
                    for p, series in param_block.items():
                        if p in all_series:
                            all_series[p].update(series)
                except Exception as e:
                    print(f"  - Warning: Failed to fetch data for period {chunk_start_date.year}-{chunk_end_date.year}. Error: {e}")

        historical_fetch_duration = time.perf_counter() - historical_fetch_start
        print(f"  [TIMER] Total time to fetch all historical data: {historical_fetch_duration:.2f} seconds.")

        # Determine analysis mode
        date_format = "%Y%m%d" if granularity == Granularity.DAILY else "%Y%m%d%H"
        target_date_str = target_dt.strftime(date_format)
        mode = AnalysisMode.PROBABILISTIC
        if target_dt.date() <= end_date and any(target_date_str in s for s in all_series.values()):
            mode = AnalysisMode.OBSERVED

        # Analyze parameters
        results: Dict[str, Any] = {}
        for p in params_to_fetch:
            series = all_series.get(p, {})
            climatology_mean = clim_map.get(p, {}).get(target_dt.month)
            entry: Dict[str, Any] = {
                "mode": mode.value,
                "climatology_month_mean": climatology_mean,
            }
            if mode == AnalysisMode.OBSERVED:
                entry["observed_value"] = series.get(target_date_str)
            else:
                values = self.filter_series_by_datetime(series, target_dt, granularity, window_days)
                stats = self.basic_stats(values)
                entry["stats"] = stats
                entry["sample_size"] = stats.get("count", 0)
            results[p] = entry

        # Calculate derived insights
        derived_insights: Dict[str, Any] = {}
        if "T2M" in results and "RH2M" in results:
            t2m_data, rh2m_data = results["T2M"], results["RH2M"]
            heat_index_note = "Heat index calculated for T>=26.7C and RH>=40%."
            if mode == AnalysisMode.OBSERVED:
                derived_insights["heat_index"] = {
                    "observed_heat_index_c": self.calculate_heat_index(
                        t2m_data.get("observed_value"), rh2m_data.get("observed_value")
                    ),
                    "note": heat_index_note,
                }
            else:
                t2m_stats, rh2m_stats = (
                    t2m_data.get("stats", {}),
                    rh2m_data.get("stats", {}),
                )
                if t2m_stats and rh2m_stats:
                    derived_insights["heat_index"] = {
                        "mean_heat_index_c": self.calculate_heat_index(
                            t2m_stats.get("mean"), rh2m_stats.get("mean")
                        ),
                        "p90_heat_index_c": self.calculate_heat_index(
                            t2m_stats.get("p90"), rh2m_stats.get("p90")
                        ),
                        "note": heat_index_note,
                    }

        return {
            "meta": {
                "latitude": lat,
                "longitude": lon,
                "target_datetime": target_dt.isoformat(),
                "granularity": granularity.value,
                "analysis_mode": mode.value,
                "historical_data_range": [start_date.isoformat(), end_date.isoformat()],
                "window_days_used": window_days,
            },
            "derived_insights": derived_insights,
            "parameters": results,
        }