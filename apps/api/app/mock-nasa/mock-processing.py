import time
import random
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import requests
import numpy as np
from scipy.stats import percentileofscore
from sklearn.linear_model import LinearRegression


class Granularity(Enum):
    DAILY = "daily"
    HOURLY = "hourly"


class AnalysisMode(Enum):
    OBSERVED = "observed"
    PROBABILISTIC = "probabilistic"


BASE_URL = "https://power.larc.nasa.gov/api/temporal"
API_PATHS = {
    Granularity.DAILY: "daily/point",
    Granularity.HOURLY: "hourly/point",
    "climatology": "climatology/point"
}
CLIMATOLOGY_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "IMERG_PRECTOT", "RH2M", "WS10M"]
DEFAULT_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "IMERG_PRECTOT", "RH2M", "WS10M", "CLOUD_AMT", "FRSNO", "ALLSKY_SFC_SW_DWN"]
DEFAULT_COMMUNITY = "RE"

HOURLY_UNAVAILABLE_PARAMS = {"T2M_MAX", "T2M_MIN", "IMERG_PRECTOT", "CLOUD_AMT"}


def http_get(url: str, params: dict, retries: int = 4, timeout: int = 120) -> dict:
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            is_retryable = 'r' not in locals() or r.status_code in (429,) or 500 <= r.status_code < 600
            if attempt == retries - 1 or not is_retryable:
                raise e
            time.sleep((2 ** attempt) * random.uniform(0.8, 1.2))
    raise RuntimeError("Maximum retry attempts exceeded")


def fetch_temporal_data(lat: float, lon: float, granularity: Granularity, start_date: dt.date, end_date: dt.date, parameters: List[str]) -> Dict[str, Any]:
    path = API_PATHS[granularity]
    if not parameters:
        return {}
        
    params = {
        "latitude": lat, "longitude": lon, "parameters": ",".join(parameters),
        "community": DEFAULT_COMMUNITY, "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"), "format": "JSON", "time-standard": "UTC"
    }
    return http_get(f"{BASE_URL}/{path}", params)


def fetch_climatology(lat: float, lon: float, parameters: List[str]) -> Dict[str, Any]:
    path = API_PATHS["climatology"]
    params = {"latitude": lat, "longitude": lon, "parameters": ",".join(parameters), "community": DEFAULT_COMMUNITY, "format": "JSON"}
    return http_get(f"{BASE_URL}/{path}", params)


def extract_param_series(json_obj: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    try:
        params = json_obj.get("properties", {}).get("parameter", {})
        for param, series in params.items():
            for date_key, value in series.items():
                if value == -999: series[date_key] = None
        return params
    except KeyError: 
        return {}


def extract_climatology_monthly(json_obj: Dict[str, Any]) -> Dict[str, Dict[int, float]]:
    param_series = extract_param_series(json_obj)
    result = {}
    for param, monthly_data in param_series.items():
        month_map = {}
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


def calculate_historical_stats(all_series: Dict[str, Dict[str, float]]) -> Dict[str, Optional[Dict[str, float]]]:
    stats_results = {}
    for param, series in all_series.items():
        values = [v for v in series.values() if v is not None]
        if not values:
            stats_results[param] = None
            continue
        np_values = np.array(values, dtype=np.float64)
        stats_results[param] = {
            "count": len(np_values), 
            "mean": np.mean(np_values), 
            "median": np.median(np_values),
            "min": np.min(np_values), 
            "max": np.max(np_values), 
            "std": np.std(np_values)
        }
    return stats_results


def calculate_classifications(
    target_dt_utc: dt.datetime,
    daily_values: Dict[str, Any],
    all_historical_series: Dict[str, Dict[str, float]],
    granularity: Granularity
) -> Dict[str, Any]:

    def _get_sanitized_series(param: str) -> List[float]:
        return [v for v in all_historical_series.get(param, {}).values() if v is not None]

    classifications = {}

    has_imerg = "IMERG_PRECTOT" in all_historical_series and any(all_historical_series["IMERG_PRECTOT"].values())
    precip_param = "IMERG_PRECTOT" if has_imerg else "PRECTOTCORR"
    if precip_param in all_historical_series:
      classifications["precipitation_source"] = precip_param

    target_doy = target_dt_utc.timetuple().tm_yday
    window_days = 15
    doy_range = {(target_doy - 1 + i) % 365 + 1 for i in range(-window_days, window_days + 1)}

    seasonal_precip = []
    historical_precip_series = all_historical_series.get(precip_param, {})
    for date_str, value in historical_precip_series.items():
        try:
            d = dt.datetime.strptime(date_str, "%Y%m%d%H") if granularity == Granularity.HOURLY else dt.datetime.strptime(date_str, "%Y%m%d")
            if d.timetuple().tm_yday in doy_range and value is not None:
                seasonal_precip.append(value)
        except (ValueError, TypeError):
            continue

    if seasonal_precip:
        rainy_events = sum(1 for p in seasonal_precip if p > 0.1)
        classifications["rain_probability"] = rainy_events / len(seasonal_precip)
        
    predicted_t_avg = daily_values.get("T2M", {}).get("value")
    predicted_rh2m = daily_values.get("RH2M", {}).get("value")

    if granularity == Granularity.DAILY:
        predicted_t_max = daily_values.get("T2M_MAX", {}).get("value")
        hist_t_max = _get_sanitized_series("T2M_MAX")
        if hist_t_max and predicted_t_max is not None:
            classifications["very_hot_temp_percentile"] = percentileofscore(hist_t_max, predicted_t_max, kind='rank')
        
        hist_snow = _get_sanitized_series("FRSNO")
        if predicted_t_avg is not None and predicted_t_avg > 2.0:
            classifications["very_snowy_probability"] = 0.0
        elif hist_snow:
            snowy_days = sum(1 for s in hist_snow if s > 0)
            classifications["very_snowy_probability"] = snowy_days / len(hist_snow) if hist_snow else 0.0

    hist_t_avg_series = all_historical_series.get("T2M", {})
    hist_rh2m_series = all_historical_series.get("RH2M", {})
    historical_heat_index = []
    for date_key, t_avg in hist_t_avg_series.items():
        rh = hist_rh2m_series.get(date_key)
        if t_avg is not None and rh is not None:
            hi = calculate_heat_index(t_avg, rh)
            if hi is not None: 
                historical_heat_index.append(hi)

    if historical_heat_index and predicted_t_avg is not None and predicted_rh2m is not None:
        predicted_heat_index = calculate_heat_index(predicted_t_avg, predicted_rh2m)
        if predicted_heat_index is not None:
            classifications["very_hot_feels_like_percentile"] = percentileofscore(historical_heat_index, predicted_heat_index, kind='rank')

    hist_wind = _get_sanitized_series("WS10M")
    predicted_wind = daily_values.get("WS10M", {}).get("value")
    if hist_wind and predicted_wind is not None:
        classifications["very_windy_percentile"] = percentileofscore(hist_wind, predicted_wind, kind='rank')

    hist_precip_full = _get_sanitized_series(precip_param)
    if hist_precip_full and hist_wind:
        precip_threshold = np.percentile(hist_precip_full, 90)
        wind_threshold = np.percentile(hist_wind, 75)
        stormy_events = 0
        total_events = len(all_historical_series.get("T2M", {}))
        hist_wind_series = all_historical_series.get("WS10M", {})
        for date_key, precip_val in historical_precip_series.items():
            wind_val = hist_wind_series.get(date_key)
            if precip_val is not None and wind_val is not None and precip_val > precip_threshold and wind_val > wind_threshold:
                stormy_events += 1
        classifications["very_wet_probability"] = stormy_events / total_events if total_events > 0 else 0.0
        classifications["very_wet_precip_threshold"] = precip_threshold
        classifications["very_wet_wind_threshold"] = wind_threshold
    
    return classifications


def predict_with_temporal_regression(series: Dict[str, float], target_dt: dt.datetime, granularity: Granularity, window_days: int) -> Optional[float]:
    target_doy = target_dt.timetuple().tm_yday
    doy_range = {(target_doy - 1 + i) % 365 + 1 for i in range(-window_days, window_days + 1)}
    historical_points = []
    date_format = "%Y%m%d" if granularity == Granularity.DAILY else "%Y%m%d%H"
    for date_str, value in series.items():
        if value is None: 
            continue
        try:
            d = dt.datetime.strptime(date_str, date_format).replace(tzinfo=dt.timezone.utc)
            is_in_day_window = d.timetuple().tm_yday in doy_range
            is_correct_hour = True if granularity == Granularity.DAILY else d.hour == target_dt.hour
            if is_in_day_window and is_correct_hour: 
                historical_points.append((d.year, float(value)))
        except (ValueError, TypeError): 
            continue
    if not historical_points: 
        return None
    yearly_data = {}
    for year, value in historical_points:
        if year not in yearly_data: 
            yearly_data[year] = []
        yearly_data[year].append(value)
    X_train_list, y_train_list = [], []
    for year, values in sorted(yearly_data.items()):
        X_train_list.append(year)
        y_train_list.append(np.mean(values))
    if len(X_train_list) < 2: 
        return np.mean(y_train_list) if y_train_list else None
    X_train = np.array(X_train_list).reshape(-1, 1)
    y_train = np.array(y_train_list)
    try:
        model = LinearRegression().fit(X_train, y_train)
        return float(model.predict(np.array([[target_dt.year]]))[0])
    except Exception:
        return float(np.mean(y_train))


def calculate_heat_index(temp_c: Optional[float], rh_percent: Optional[float]) -> Optional[float]:
    if temp_c is None or rh_percent is None or np.isnan(temp_c) or np.isnan(rh_percent): 
        return None
    if temp_c < 26.7 or rh_percent < 40: 
        return temp_c
    t_f = temp_c * 9/5 + 32
    hi_f = (-42.379 + 2.04901523*t_f + 10.14333127*rh_percent - 0.22475541*t_f*rh_percent - 6.83783e-3*t_f**2 - 5.481717e-2*rh_percent**2 + 1.22874e-3*t_f**2*rh_percent + 8.5282e-4*t_f*rh_percent**2 - 1.99e-6*t_f**2*rh_percent**2)
    return (hi_f - 32) * 5/9


def analyze_weather_range(
    lat: float, 
    lon: float,
    center_dt: dt.datetime,
    target_timezone: str,
    days_before: int = 3,
    days_after: int = 3,
    granularity: Granularity = Granularity.DAILY,
    parameters: Optional[List[str]] = None,
    start_year: int = 1984,
    window_days: int = 7,
    hourly_chunk_years: int = 5,
    debug_mode: bool = False
) -> Dict[str, Any]:
    try:
        target_tz = ZoneInfo(target_timezone)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Invalid timezone: '{target_timezone}'")

    center_dt_utc = center_dt.astimezone(dt.timezone.utc)
    
    if parameters is None: 
        parameters = DEFAULT_PARAMS
    essential_params = {"T2M", "RH2M", "T2M_MAX", "WS10M", "PRECTOTCORR", "IMERG_PRECTOT", "FRSNO"}
    params_to_fetch = list(set(parameters) | essential_params)
    
    if granularity == Granularity.HOURLY:
        params_to_fetch = [p for p in params_to_fetch if p not in HOURLY_UNAVAILABLE_PARAMS]

    end_date_available = dt.datetime.now(dt.timezone.utc).date()
    start_date_fetch = dt.date(start_year, 1, 1)
    
    clim_json = fetch_climatology(lat, lon, CLIMATOLOGY_PARAMS)
    clim_map = extract_climatology_monthly(clim_json)
    
    all_series: Dict[str, Dict[str, float]] = {p: {} for p in params_to_fetch}

    if granularity == Granularity.DAILY:
        try:
            historical_json = fetch_temporal_data(lat, lon, granularity, start_date_fetch, end_date_available, params_to_fetch)
            all_series = extract_param_series(historical_json)
        except Exception:
            pass
    else:
        for year in range(start_date_fetch.year, end_date_available.year + 1, hourly_chunk_years):
            chunk_start_dt = dt.date(year, 1, 1)
            chunk_end_dt = dt.date(min(year + hourly_chunk_years - 1, end_date_available.year), 12, 31)
            if chunk_end_dt > end_date_available: 
                chunk_end_dt = end_date_available
            try:
                hourly_json = fetch_temporal_data(lat, lon, granularity, chunk_start_dt, chunk_end_dt, params_to_fetch)
                chunk_series = extract_param_series(hourly_json)
                for param, values in chunk_series.items():
                    if param in all_series: 
                        all_series[param].update(values)
            except Exception:
                continue
    
    historical_stats = calculate_historical_stats(all_series)

    analysis_results = []
    datetimes_to_analyze_utc = [center_dt_utc + dt.timedelta(days=i) for i in range(-days_before, days_after + 1)]
    
    for target_dt_utc in datetimes_to_analyze_utc:
        date_format_api = "%Y%m%d" if granularity == Granularity.DAILY else "%Y%m%d%H"
        target_date_str_api = target_dt_utc.strftime(date_format_api)
        is_in_past = target_dt_utc <= dt.datetime.now(dt.timezone.utc)
        results_for_moment = {}
        
        for p in params_to_fetch:
            series = all_series.get(p, {})
            climatology_mean = clim_map.get(p, {}).get(target_dt_utc.month)
            entry = {"climatology_month_mean": climatology_mean}
            if is_in_past:
                observed_value = series.get(target_date_str_api)
                if observed_value is not None:
                    entry["mode"] = AnalysisMode.OBSERVED.value
                    entry["value"] = observed_value
                else:
                    predicted_value = predict_with_temporal_regression(series, target_dt_utc, granularity, window_days)
                    entry["mode"] = AnalysisMode.PROBABILISTIC.value
                    entry["value"] = predicted_value
                    entry["model_used"] = "TemporalLinearRegressionByNullObserved"
            else:
                predicted_value = predict_with_temporal_regression(series, target_dt_utc, granularity, window_days)
                entry["mode"] = AnalysisMode.PROBABILISTIC.value
                entry["value"] = predicted_value
                entry["model_used"] = "TemporalLinearRegression"
            results_for_moment[p] = entry
            
        t2m_val = results_for_moment.get('T2M', {}).get('value')
        rh2m_val = results_for_moment.get('RH2M', {}).get('value')
        heat_index_val = calculate_heat_index(t2m_val, rh2m_val)
        target_dt_local = target_dt_utc.astimezone(target_tz)
        
        analysis_results.append({
            "datetime": target_dt_local.isoformat(),
            "parameters": results_for_moment,
            "derived_insights": {'heat_index_c': heat_index_val}
        })
        
    center_day_data = analysis_results[days_before]
    center_day_params = center_day_data['parameters']
    center_day_classifications = calculate_classifications(center_dt_utc, center_day_params, all_series, granularity)
        
    return {
        "meta": {
            "latitude": lat, 
            "longitude": lon, 
            "center_datetime_utc": center_dt_utc.isoformat(),
            "center_datetime_local": center_dt.isoformat(), 
            "target_timezone": target_timezone,
            "granularity": granularity.value, 
            "historical_data_range": [start_date_fetch.isoformat(), end_date_available.isoformat()]
        },
        "stats": historical_stats,
        "classifications": center_day_classifications,
        "results": analysis_results
    }


if __name__ == "__main__":
    LOCATION_LAT = -7.115
    LOCATION_LON = -34.863
    TARGET_TIMEZONE = "America/Sao_Paulo" 
    ANO = 2024
    MES = 1
    DIA = 10
    HORA = 14 
    
    try:
        target_tz = ZoneInfo(TARGET_TIMEZONE)
        naive_dt = dt.datetime(ANO, MES, DIA, HORA)
        center_dt_localized = naive_dt.replace(tzinfo=target_tz)
    except Exception as e:
        exit()
    
    try:
        analysis_result = analyze_weather_range(
            lat=LOCATION_LAT,
            lon=LOCATION_LON,
            center_dt=center_dt_localized,
            target_timezone=TARGET_TIMEZONE,
            days_before=3,
            days_after=3,
            granularity=Granularity.HOURLY,
            start_year=2010,
            debug_mode=False
        )
        print(json.dumps(analysis_result, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        pass