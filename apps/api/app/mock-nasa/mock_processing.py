# ABOUTME: Conversão do notebook mock_processing.ipynb para script Python standalone.
# ABOUTME: Fornece função analyze_weather e bloco de execução demonstrativo (mock inicial de desenho futuro).

import time, random, re, json  # noqa: E401,E402
import datetime as dt
from typing import Dict, List, Optional, Any
from enum import Enum

import requests  # type: ignore
import numpy as np  # type: ignore

# --------------- 1. Constantes e Tipos (sem alterações) ---------------
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
    "climatology": "climatology/point",
}
DEFAULT_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS10M"]
DEFAULT_COMMUNITY = "SB"

# --------------- 2. Helper HTTP com Retry (sem alterações) ---------------
def http_get(url: str, params: dict, retries: int = 4, timeout: int = 120) -> dict:
    """Faz uma requisição GET com tentativas e medição de tempo."""
    start_time = time.perf_counter()
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            duration = time.perf_counter() - start_time
            print(
                f"    [TIMER] Requisição para {r.url.split('?')[0]} concluída em {duration:.2f} segundos."
            )
            return r.json()
        except requests.RequestException as e:  # pragma: no cover (network variability)
            is_retryable = "r" not in locals() or r.status_code in (429,) or 500 <= r.status_code < 600
            if attempt == retries - 1 or not is_retryable:
                print(
                    f"Erro na requisição: {r.status_code if 'r' in locals() else 'N/A'} - {r.text if 'r' in locals() else e}"
                )
                raise e
            time.sleep((2**attempt) * random.uniform(0.8, 1.2))
    raise RuntimeError("Máximo de tentativas excedido")


# --------------- 3. Wrappers da API (sem alterações) ---------------
def fetch_temporal_data(
    lat: float,
    lon: float,
    granularity: Granularity,
    start_date: dt.date,
    end_date: dt.date,
    parameters: List[str],
) -> Dict[str, Any]:
    path = API_PATHS[granularity]
    params = {
        "latitude": lat,
        "longitude": lon,
        "parameters": ",".join(parameters),
        "community": DEFAULT_COMMUNITY,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }
    return http_get(f"{BASE_URL}/{path}", params)

def fetch_climatology(lat: float, lon: float, parameters: List[str]) -> Dict[str, Any]:
    path = API_PATHS["climatology"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "parameters": ",".join(parameters),
        "community": DEFAULT_COMMUNITY,
        "format": "JSON",
    }
    return http_get(f"{BASE_URL}/{path}", params)


# --------------- 4. Funções de Análise e Extração (sem alterações) ---------------
def extract_param_series(json_obj: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    try:
        params = json_obj["properties"]["parameter"]
        for param, series in params.items():
            for date_key, value in series.items():
                if value == -999:
                    series[date_key] = None
        return params
    except KeyError:
        return {}


def extract_climatology_monthly(json_obj: Dict[str, Any]) -> Dict[str, Dict[int, float]]:
    param_series = extract_param_series(json_obj)
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


def basic_stats(values: List[float]) -> Dict[str, float]:
    valid_values = [v for v in values if v is not None and not np.isnan(v)]
    if not valid_values:
        keys = [
            "count",
            "mean",
            "median",
            "min",
            "max",
            "std",
            "p10",
            "p25",
            "p75",
            "p90",
        ]
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
    series: Dict[str, float],
    target_dt: dt.datetime,
    granularity: Granularity,
    window_days: int,
) -> List[float]:
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
        except (ValueError, TypeError):  # pragma: no cover (defensive)
            continue
    return values


def calculate_heat_index(temp_c: float, rh_percent: float) -> Optional[float]:
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
        - 1.99e-6 * t_f*2 * rh_percent*2
    )
    return (hi_f - 32) * 5 / 9


# --------------- 5. Função Principal de Análise (COM LÓGICA DE CHUNKS OTIMIZADA) ---------------
def analyze_weather(
    lat: float,
    lon: float,
    target_dt: dt.datetime,
    granularity: Granularity = Granularity.DAILY,
    parameters: Optional[List[str]] = None,
    start_year: int = 2005,
    window_days: int = 7,
    hourly_chunk_years: int = 5,  # <--- NOVO PARÂMETRO: Define o tamanho do chunk em anos
) -> Dict[str, Any]:
    if parameters is None:
        parameters = DEFAULT_PARAMS
    params_to_fetch = list(parameters)
    if granularity == Granularity.HOURLY:
        invalid_hourly_params = {"T2M_MAX", "T2M_MIN"}
        params_to_fetch = [p for p in params_to_fetch if p not in invalid_hourly_params]
    required_params = {"T2M", "RH2M"}
    params_to_fetch = list(set(params_to_fetch) | required_params)

    end_date = dt.datetime.now(dt.timezone.utc).date()
    start_date = dt.date(start_year, 1, 1)

    print("Buscando dados de climatologia...")
    clim_json = fetch_climatology(lat, lon, params_to_fetch)
    clim_map = extract_climatology_monthly(clim_json)
    print("Dados de climatologia obtidos.")

    all_series: Dict[str, Dict[str, float]] = {p: {} for p in params_to_fetch}

    historical_fetch_start = time.perf_counter()

    if granularity == Granularity.DAILY:
        print(f"Buscando dados 'daily' de {start_date} a {end_date} em uma única requisição...")
        try:
            historical_json = fetch_temporal_data(
                lat, lon, granularity, start_date, end_date, params_to_fetch
            )
            all_series = extract_param_series(historical_json)
        except Exception as e:  # pragma: no cover (network variability)
            print(f"Aviso: Falha ao buscar dados diários históricos. Erro: {e}")
    else:  # Granularity.HOURLY
        # <--- LÓGICA DE BUSCA OTIMIZADA EM CHUNKS DE 5 ANOS --->
        print(
            f"Buscando dados 'hourly' de {start_date.year} a {end_date.year} (em chunks de {hourly_chunk_years} anos)..."
        )
        for year in range(start_date.year, end_date.year + 1, hourly_chunk_years):
            chunk_start_date = dt.date(year, 1, 1)
            chunk_end_year = min(year + hourly_chunk_years - 1, end_date.year)
            chunk_end_date = min(dt.date(chunk_end_year, 12, 31), end_date)

            print(
                f"  - Buscando chunk de {chunk_start_date.year} a {chunk_end_date.year}..."
            )
            try:
                chunk = fetch_temporal_data(
                    lat, lon, granularity, chunk_start_date, chunk_end_date, params_to_fetch
                )
                param_block = extract_param_series(chunk)
                for p, series in param_block.items():
                    if p in all_series:
                        all_series[p].update(series)
            except Exception as e:  # pragma: no cover (network variability)
                print(
                    f"  - Aviso: Falha ao buscar dados para o período {chunk_start_date.year}-{chunk_end_date.year}. Erro: {e}"
                )

    historical_fetch_duration = time.perf_counter() - historical_fetch_start
    print(
        f"  [TIMER] Tempo total para buscar todos os dados históricos: {historical_fetch_duration:.2f} segundos."
    )

    # O resto da função continua normalmente...
    date_format = "%Y%m%d" if granularity == Granularity.DAILY else "%Y%m%d%H"
    target_date_str = target_dt.strftime(date_format)
    mode = AnalysisMode.PROBABILISTIC
    if target_dt.date() <= end_date and any(
        target_date_str in s for s in all_series.values()
    ):
        mode = AnalysisMode.OBSERVED

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
            values = filter_series_by_datetime(
                series, target_dt, granularity, window_days
            )
            stats = basic_stats(values)
            entry["stats"] = stats
            entry["sample_size"] = stats.get("count", 0)
        results[p] = entry

    derived_insights: Dict[str, Any] = {}
    if "T2M" in results and "RH2M" in results:
        t2m_data, rh2m_data = results["T2M"], results["RH2M"]
        heat_index_note = (
            "Sensação térmica (Heat Index) calculada para T>=26.7C e RH>=40%."
        )
        if mode == AnalysisMode.OBSERVED:
            derived_insights["heat_index"] = {
                "observed_heat_index_c": calculate_heat_index(
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
                    "mean_heat_index_c": calculate_heat_index(
                        t2m_stats.get("mean"), rh2m_stats.get("mean")
                    ),
                    "p90_heat_index_c": calculate_heat_index(
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


# --------------- 6. Bloco de Execução do Script (sem alterações) ---------------
if _name_ == "_main_":  # pragma: no cover (exemplo / manual)
    LOCATION_LAT = -7.115
    LOCATION_LON = -34.863

    # --- Exemplo 1: Análise PROBABILÍSTICA HORÁRIA ---
    future_datetime = dt.datetime(2025, 12, 25, 14, 0)

    print("=" * 60)
    print(
        f"▶️  Exemplo 1: Análise HORÁRIA e PROBABILÍSTICA para {future_datetime.isoformat()}"
    )
    print("=" * 60)
    total_start_time = time.perf_counter()
    try:
        hourly_analysis = analyze_weather(
            lat=LOCATION_LAT,
            lon=LOCATION_LON,
            target_dt=future_datetime,
            granularity=Granularity.HOURLY,
            start_year=2005,
        )
        print("\n✅ Análise Horária concluída! Resultado:\n")
        print(json.dumps(hourly_analysis, indent=2, ensure_ascii=False))
    except Exception as e:  # pragma: no cover (exemplo)
        print(f"❌ Ocorreu um erro na análise horária: {e}")
    finally:
        total_duration = time.perf_counter() - total_start_time
        print(
            f"\n[TIMER] Análise completa (Exemplo 1) finalizada em {total_duration:.2f} segundos."
        )

    print("\n\n")

    # --- Exemplo 2: Análise OBSERVADA DIÁRIA ---
    past_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=365)

    print("=" * 60)
    print(
        f"▶️  Exemplo 2: Análise DIÁRIA e OBSERVADA para {past_date.date().isoformat()}"
    )
    print("=" * 60)
    total_start_time = time.perf_counter()
    try:
        daily_analysis = analyze_weather(
            lat=LOCATION_LAT,
            lon=LOCATION_LON,
            target_dt=past_date,
            granularity=Granularity.DAILY,
            start_year=1984,  # Dados diários desde 1984
        )
        print("\n✅ Análise Diária concluída! Resultado:\n")
        print(json.dumps(daily_analysis, indent=2, ensure_ascii=False))
    except Exception as e:  # pragma: no cover (exemplo)
        print(f"❌ Ocorreu um erro na análise diária: {e}")
    finally:
        total_duration = time.perf_counter() - total_start_time
        print(
            f"\n[TIMER] Análise completa (Exemplo 2) finalizada em {total_duration:.2f} segundos."
        )