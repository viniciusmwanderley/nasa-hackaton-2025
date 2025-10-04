from __future__ import annotations

import time
import random
import math
import datetime as dt
from statistics import mean, median, pstdev
from typing import Dict, List, Optional

import httpx  


BASE = "https://power.larc.nasa.gov/api/temporal"
CLIMATOLOGY_PATH = "climatology/point"
DAILY_PATH = "daily/point"
DEFAULT_COMMUNITY = "SB"
DEFAULT_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M"]

__all__ = [
    "http_get",
    "fetch_climatology",
    "fetch_daily_chunk",
    "extract_param_series",
    "extract_climatology_monthly",
    "basic_stats",
    "filter_by_day_of_year",
    "calculate_heat_index",
    "analyze_weather_for_date",
]


# --------------- 1.HTTP/retry ---------------
def http_get(url: str, params: dict, retries: int = 4, timeout: int = 90) -> dict:
    """Faz uma requisição GET com tentativas exponenciais em caso de erro retryable."""
    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.get(url, params=params)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPError as e:  # inclui timeout, etc.
            status_code = getattr(e.response, "status_code", None)
            is_retryable = status_code in (429,) or (status_code is not None and 500 <= status_code < 600)
            if attempt == retries - 1 or not is_retryable:
                last_exc = e
                break
            sleep_for = (2 ** attempt) * random.uniform(0.8, 1.2)
            time.sleep(sleep_for)
    if last_exc:
        raise last_exc
    raise RuntimeError("Máximo de tentativas excedido sem exceção explícita")


# --------------- 2. API Wrappers ---------------
def fetch_climatology(lat: float, lon: float, parameters: List[str]) -> dict:
    """Busca as médias climatológicas mensais."""
    return http_get(
        f"{BASE}/{CLIMATOLOGY_PATH}",
        {
            "latitude": lat,
            "longitude": lon,
            "parameters": ",".join(parameters),
            "community": DEFAULT_COMMUNITY,
            "format": "JSON",
        },
    )


def fetch_daily_chunk(lat: float, lon: float, parameters: List[str], start: str, end: str) -> dict:
    """Busca dados diários para um período específico."""
    return http_get(
        f"{BASE}/{DAILY_PATH}",
        {
            "latitude": lat,
            "longitude": lon,
            "parameters": ",".join(parameters),
            "community": DEFAULT_COMMUNITY,
            "start": start,
            "end": end,
            "format": "JSON",
        },
    )


# --------------- 3. Extraction/Analysis ---------------
def extract_param_series(json_obj: dict) -> Dict[str, Dict[str, float]]:
    """Extrai os dados de séries temporais da resposta JSON da API."""
    try:
        return json_obj["properties"]["parameter"]  # type: ignore[index]
    except KeyError:
        return {}


def extract_climatology_monthly(json_obj: dict) -> Dict[str, Dict[int, float]]:
    """Extrai dados de climatologia, convertendo mês para inteiro (1-12)."""
    param_series = extract_param_series(json_obj)
    result: Dict[str, Dict[int, float]] = {}
    for param, monthly_data in param_series.items():
        month_map: Dict[int, float] = {}
        for month_key, value in monthly_data.items():
            try:
                month_num = int(month_key)  # "1", "01"
            except ValueError:
                try:
                    month_num = dt.datetime.strptime(str(month_key)[:3], "%b").month  # "JAN", "January"
                except ValueError:
                    continue  # ignora agregados anuais tipo "ANN"
            if 1 <= month_num <= 12 and value is not None:
                try:
                    month_map[month_num] = float(value)
                except (TypeError, ValueError):  # valor não numérico
                    continue
        result[param] = month_map
    return result


def _percentile(sorted_values: List[float], p: float) -> float:
    """Calcula percentil (0-100) usando interpolação linear simples.
    Evita dependência de numpy para o mock inicial.
    """
    if not sorted_values:
        return math.nan
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def basic_stats(values: List[float]) -> Dict[str, float]:
    """Calcula estatísticas básicas; remove sentinela -999 antes.

    Retorna NaN para campos quando não houver dados válidos.
    """
    keys = ["count", "mean", "median", "min", "max", "std", "p10", "p25", "p75", "p90"]
    if not values:
        return {k: float("nan") for k in keys}
    filtered = [float(v) for v in values if v is not None and not math.isnan(v) and v != -999]
    if not filtered:
        return {k: float("nan") for k in keys}
    sorted_vals = sorted(filtered)
    return {
        "count": float(len(filtered)),
        "mean": mean(filtered),
        "median": median(filtered),
        "min": sorted_vals[0],
        "max": sorted_vals[-1],
        "std": 0.0 if len(filtered) == 1 else pstdev(filtered),  # população
        "p10": _percentile(sorted_vals, 10),
        "p25": _percentile(sorted_vals, 25),
        "p75": _percentile(sorted_vals, 75),
        "p90": _percentile(sorted_vals, 90),
    }


def filter_by_day_of_year(series: Dict[str, float], target_date: dt.date, window: int = 0) -> List[float]:
    """Filtra valores cujo dia-do-ano está dentro de ±window dias do alvo.
    Lida com virada de ano usando aritmética modular 365.
    """
    target_doy = target_date.timetuple().tm_yday
    doy_range = {(target_doy + i - 1) % 365 + 1 for i in range(-window, window + 1)}
    values: List[float] = []
    for date_str, value in series.items():
        try:
            d = dt.datetime.strptime(date_str, "%Y%m%d").date()
            if d.timetuple().tm_yday in doy_range:
                values.append(float(value))
        except (ValueError, TypeError):
            continue
    return values


def calculate_heat_index(temp_c: float, rh_percent: float) -> Optional[float]:
    """Calcula Heat Index (sensação térmica) em °C. Fora da faixa retorna a própria temperatura.
    Fórmula Rothfusz (NOAA) adaptada.
    """
    if temp_c is None or rh_percent is None:
        return None
    try:
        if math.isnan(temp_c) or math.isnan(rh_percent):  # type: ignore[arg-type]
            return None
    except TypeError:
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


# --------------- Main Analytics ---------------
def analyze_weather_for_date(
    lat: float,
    lon: float,
    target_date: dt.date,
    parameters: Optional[List[str]] = None,
    start_year: int = 1981,
    window_days: int = 7,
) -> dict:
    """Analisa clima para uma data alvo.

    Modo "observed" se existir dado para a data até o presente; caso contrário, usa
    abordagem probabilística com janela de ±window_days baseada em histórico multi-ano.
    """
    if parameters is None:
        parameters = list(DEFAULT_PARAMS)
    if "T2M" not in parameters:
        parameters.append("T2M")
    if "RH2M" not in parameters:
        parameters.append("RH2M")

    end_date = dt.datetime.utcnow().date()
    start_date = dt.date(start_year, 1, 1)

    # Passo 1: Climatologia
    clim_json = fetch_climatology(lat, lon, parameters)
    clim_map = extract_climatology_monthly(clim_json)

    # Passo 2: Série histórica completa (ano a ano)
    all_series: Dict[str, Dict[str, float]] = {p: {} for p in parameters}
    print(f"Buscando dados históricos de {start_date.year} a {end_date.year}...")
    for year in range(start_date.year, end_date.year + 1):
        try:
            chunk = fetch_daily_chunk(lat, lon, parameters, f"{year}0101", f"{year}1231")
            param_block = extract_param_series(chunk)
            for p, series in param_block.items():
                if p in all_series:
                    all_series[p].update(series)
        except Exception as e:  # pragma: no cover - apenas logging simples
            print(f"Aviso: Falha ao buscar dados para o ano {year}. Erro: {e}")

    # Passo 3: Modo de análise
    mode = "probabilistic"
    target_date_str = target_date.strftime("%Y%m%d")
    if target_date <= end_date and any(target_date_str in s for s in all_series.values()):
        mode = "observed"

    # Passo 4: Construção resultado por parâmetro
    results: Dict[str, dict] = {}
    for p in parameters:
        series = all_series.get(p, {})
        climatology_mean = clim_map.get(p, {}).get(target_date.month)
        entry: Dict[str, object] = {"mode": mode, "climatology_month_mean": climatology_mean}
        if mode == "observed":
            val = series.get(target_date_str)
            entry["observed_value"] = float(val) if val is not None and val != -999 else None
        else:
            values = filter_by_day_of_year(series, target_date, window=window_days)
            stats = basic_stats(values)
            entry["stats"] = stats
            entry["sample_size"] = int(stats.get("count", 0))
        results[p] = entry

    # Passo 5: Insights derivados (Heat Index)
    derived_insights: Dict[str, dict] = {}
    if mode == "probabilistic" and "T2M" in results and "RH2M" in results:
        t2m_stats = results["T2M"].get("stats", {})  # type: ignore[assignment]
        rh2m_stats = results["RH2M"].get("stats", {})  # type: ignore[assignment]
        if t2m_stats and rh2m_stats:
            derived_insights["heat_index"] = {
                "mean_heat_index_c": calculate_heat_index(
                    t2m_stats.get("mean"), rh2m_stats.get("mean")  # type: ignore[arg-type]
                ),
                "p90_heat_index_c": calculate_heat_index(
                    t2m_stats.get("p90"), rh2m_stats.get("p90")  # type: ignore[arg-type]
                ),
                "note": "Heat Index calculado apenas quando T>=26.7C e RH>=40% (senão retorna T).",
            }

    return {
        "meta": {
            "latitude": lat,
            "longitude": lon,
            "target_date": target_date.isoformat(),
            "analysis_mode": mode,
            "historical_data_until": end_date.isoformat(),
            "window_days_used": window_days,
        },
        "derived_insights": derived_insights,
        "parameters": results,
    }


# --------------- 5. Sample Run ---------------
if __name__ == "__main__":  # pragma: no cover - exemplo manual
    import json

    LOCATION_LAT = -7.115  # João Pessoa, PB, Brasil
    LOCATION_LON = -34.863
    future_target_date = dt.date(2024, 1, 15)

    print("=" * 60)
    print(
        f"▶️  Iniciando análise para {future_target_date.isoformat()} com janela de 7 dias (protótipo)"
    )
    print("=" * 60)
    try:
        analysis_result = analyze_weather_for_date(
            lat=LOCATION_LAT, lon=LOCATION_LON, target_date=future_target_date, window_days=7
        )
        print("\n✅ Análise concluída! Resultado:\n")
        print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        print(f"❌ Ocorreu um erro durante a análise: {e}")
