# ABOUTME: Climate energy analysis module for calculating solar and wind energy potential using NASA POWER data
# ABOUTME: Provides functions to fetch climatology data and compute kWh/m² metrics for renewable energy assessment

import requests
import json
import time
import random
from typing import List, Dict, Any


# ==============================================================================
# 1. CONFIGURATION AND CONSTANTS
# ==============================================================================

# NASA API Configuration
NASA_API_BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
NASA_API_COMMUNITY = "RE"
NASA_API_START_YEAR = "2010"
NASA_API_END_YEAR = "2024"

# Technological Parameters (For kWh/m² calculations only)
# Solar
SOLAR_LOSS_FACTOR: float = 0.80  # System losses (inverter, cables, dirt)

# Wind
TURBINE_SWEPT_AREA_M2: float = 14314.0  # Reference turbine swept area (m²)
TURBINE_CP: float = 0.45  # Reference turbine power coefficient

# Calculation Constants
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DAYS_IN_MONTH: Dict[str, int] = dict(zip(MONTHS, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]))

# API Parameter Mapping
API_PARAMETERS_MAP: Dict[str, str] = {
    "SolarIrradianceOptimal": "SI_TILTED_AVG_OPTIMAL",
    "SolarIrradianceOptimalAngle": "SI_TILTED_AVG_OPTIMAL_ANG",
    "SurfaceAirDensity": "RHOA",
    "WindSpeed50m": "WS50M",
    "WindDirection50m": "WD50M"
}


# ==============================================================================
# 2. API ACCESS LAYER
# ==============================================================================

def http_get(url: str, params: dict, retries: int = 4, timeout: int = 45) -> Dict[str, Any]:
    """
    Performs HTTP GET request with robust error handling and retries.
    
    Args:
        url: The URL to make the request to
        params: Query parameters for the request
        retries: Number of retry attempts
        timeout: Request timeout in seconds
        
    Returns:
        JSON response as dictionary
        
    Raises:
        requests.exceptions.RequestException: If request fails after all retries
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response else 'N/A'
            is_retryable = status_code in (429, 500, 502, 503, 504)
            if not is_retryable or attempt == retries - 1:
                raise e
            time.sleep((2 ** attempt) * random.uniform(0.8, 1.2))
    raise RuntimeError("Maximum request attempts exceeded.")


def fetch_climatology_data(lat: float, lon: float, params_list: List[str]) -> Dict[str, Any]:
    """
    Fetches climatology data from NASA POWER API for a single coordinate.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        params_list: List of parameters to request from the API
        
    Returns:
        Dictionary containing the parameter data
    """
    payload = {
        "start": NASA_API_START_YEAR,
        "end": NASA_API_END_YEAR,
        "latitude": lat,
        "longitude": lon,
        "community": NASA_API_COMMUNITY,
        "parameters": ",".join(params_list),
        "units": "metric",
        "header": "true",
    }
    data = http_get(NASA_API_BASE_URL, params=payload)
    return data.get("properties", {}).get("parameter", {})


# ==============================================================================
# 3. CALCULATION LAYER
# ==============================================================================

def calculate_solar_kwh_per_m2(api_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates solar energy density (kWh/m²/month) for each month.
    
    Args:
        api_data: Dictionary containing NASA API response data
        
    Returns:
        Dictionary with monthly and annual kWh/m² values
    """
    insolation_data = api_data.get(API_PARAMETERS_MAP["SolarIrradianceOptimal"], {})
    results = {}
    
    for month in MONTHS:
        daily_insolation = insolation_data.get(month)
        if daily_insolation is None or daily_insolation == -999:
            continue

        days = DAYS_IN_MONTH[month]
        monthly_kwh_per_m2 = daily_insolation * SOLAR_LOSS_FACTOR * days
        results[month] = round(monthly_kwh_per_m2, 2)

    if results:
        results["ANN"] = round(sum(results.values()), 2)

    return results


def calculate_wind_kwh_per_m2(api_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates wind energy density (kWh/m²/month) for each month.
    
    Args:
        api_data: Dictionary containing NASA API response data
        
    Returns:
        Dictionary with monthly and annual kWh/m² values
    """
    air_density_data = api_data.get(API_PARAMETERS_MAP["SurfaceAirDensity"], {})
    wind_speed_data = api_data.get(API_PARAMETERS_MAP["WindSpeed50m"], {})
    results = {}
    
    for month in MONTHS:
        air_density = air_density_data.get(month)
        wind_speed = wind_speed_data.get(month)
        if any(v is None or v == -999 for v in [air_density, wind_speed]):
            continue

        hours = DAYS_IN_MONTH[month] * 24
        avg_power_watts = 0.5 * air_density * TURBINE_SWEPT_AREA_M2 * (wind_speed ** 3) * TURBINE_CP
        total_monthly_energy_kwh = (avg_power_watts * hours) / 1000
        
        monthly_kwh_per_m2 = total_monthly_energy_kwh / TURBINE_SWEPT_AREA_M2
        results[month] = round(monthly_kwh_per_m2, 2)

    if results:
        results["ANN"] = round(sum(results.values()), 2)

    return results


# ==============================================================================
# 4. MAIN ORCHESTRATOR
# ==============================================================================

def run_climate_energy_analysis(locations_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Orchestrates energy potential analysis for a list of locations,
    focusing on energy density metrics (kWh/m²).
    
    Args:
        locations_payload: List of location dictionaries with city, lat, lon keys
        
    Returns:
        Dictionary containing analysis results, metadata, and any errors
    """
    start_time = time.perf_counter()
    analysis_results = []
    failed_locations = []
    param_list = list(API_PARAMETERS_MAP.values())

    for loc in locations_payload:
        city, lat, lon = loc.get("city"), loc.get("lat"), loc.get("lon")
        if not all([city, lat, lon]):
            failed_locations.append({"location": loc, "error": "Invalid format."})
            continue

        try:
            api_data = fetch_climatology_data(lat, lon, param_list)
            if not api_data:
                raise ValueError("Empty API response.")
            
            solar_kwh_per_m2 = calculate_solar_kwh_per_m2(api_data)
            wind_kwh_per_m2 = calculate_wind_kwh_per_m2(api_data)
            
            raw_metrics = {key: api_data.get(value, {}) for key, value in API_PARAMETERS_MAP.items()}
            
            analysis_results.append({
                "location": {"city": city, "latitude": lat, "longitude": lon},
                "climate_energy_potential": {
                    "solar_kwh_per_m2": solar_kwh_per_m2,
                    "wind_kwh_per_m2": wind_kwh_per_m2
                },
                "raw_nasa_metrics_monthly": raw_metrics
            })
            
        except Exception as e:
            failed_locations.append({
                "location": {"city": city, "latitude": lat, "longitude": lon}, 
                "error": str(e)
            })

    duration = time.perf_counter() - start_time
    
    return {
        "meta": {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "processing_time_seconds": round(duration, 2),
            "locations_processed": len(analysis_results),
            "locations_failed": len(failed_locations),
        },
        "data": analysis_results,
        "errors": failed_locations
    }


# ==============================================================================
# 5. EXECUTION BLOCK
# ==============================================================================

if __name__ == "__main__":
    locations_payload: List[Dict[str, Any]] = [
        {"city": "Joao Pessoa, PB", "lat": -7.1195, "lon": -34.8451},
        {"city": "Caetite, BA", "lat": -14.0683, "lon": -42.4794},
        {"city": "Sao Miguel do Gostoso, RN", "lat": -5.1225, "lon": -35.6361},
        {"city": "Petrolina, PE", "lat": -9.38, "lon": -40.5},
        {"city": "Munich (Germany)", "lat": 48.13, "lon": 11.57},
        {"city": "Local Inválido", "lat": 999, "lon": 999},
    ]
    
    final_report = run_climate_energy_analysis(locations_payload)
    
    print(json.dumps(final_report, indent=2, ensure_ascii=False))