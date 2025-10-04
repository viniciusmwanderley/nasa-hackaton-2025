# Outdoor Risk (NASA Hackathon) — MVP Specification

> Monorepo MVP to estimate odds of **very hot, very cold, very windy, very wet,** and **very uncomfortable** conditions for a user‑selected location, calendar date, and local hour using NASA Earth observations. Optimized for a 2‑day hackathon ship.

---

## 0) High‑level summary

**Goal.** Let users drop a map pin, pick a **date** and **local time** (HH:00), and instantly see the **historical probability** (not a forecast) of five adverse conditions around that date at that location. Show clear, explainable outputs and allow data export.

**Key idea.** Use **DOY ± 7 days** across the baseline years **2001–present** at the chosen local hour to estimate a binomial exceedance probability for each condition.

**Primary data.**
- **IMERG V07 Final Run Half‑Hourly** (0.1°) → precipitation rate; aggregated to hourly; fallback to POWER hourly precip when missing.
- **NASA POWER Hourly** (MERRA‑2/GEOS) → 2‑m temperature (°C), 2‑m relative humidity (%), 10‑m wind speed (m/s), hourly precipitation rate (mm/h, fallback only).

**MVP UX.** One screen: **Overview + Tabs.** Overview shows **5 result cards** + **compact map**; tabs switch to **Distributions**, **Trends**, **Data** (table + CSV/JSON export).

---

## 1) Personas and use cases (MVP focus)
- **Primary persona:** Local event organizer/outdoor planner.
- **Use cases:** choose location/date/hour for a parade, hike, or beach day several weeks/months ahead; assess odds of heat, wind, rain; export supporting data.

Out of scope (MVP): multi‑day itineraries, alerts, user accounts.

---

## 2) Definitions & thresholds (metric)
All thresholds are configurable via env but compile‑time defaults are:

- **Very hot**: Heat Index (HI) **≥ 41 °C** (≈ 105 °F, NWS *Danger* range). Inputs: **T2M**, **RH2M**.
- **Very uncomfortable**: Heat Index **≥ 32 °C** (≈ 90 °F, NWS *Extreme Caution* lower bound). Inputs: **T2M**, **RH2M**.
- **Very cold**: Wind Chill (WCT) **≤ −10 °C**. Inputs: **T2M**, **WS10M**.
- **Very windy**: **WS10M ≥ 10.8 m/s** (Beaufort 6 “strong breeze”).
- **Very wet**: Precipitation **rate ≥ 4 mm/h** at the selected local hour. Primary source: **IMERG V07 Final Run half‑hourly** → average of the two half‑hours bracketing the selected clock hour; **fallback**: **POWER hourly precip** if both IMERG half‑hours are missing (provenance flagged).

**Notes.**
- HI uses the standard Rothfusz regression with Celsius conversion; WCT uses the NWS formula (valid for T≤10 °C and winds ≥1.3 m/s; we still compute the metric and gate the flag by these validity rules).
- All outputs use **metric units**; we display Fahrenheit equivalents once in glossary/help only.

---

## 3) Sampling & statistics

**Temporal sampling.** For user input **(lat, lon, date_local, hour_local)** select the **day‑of‑year (DOY)**; gather samples from **DOY − 7 … DOY + 7** for all baseline years **[2001 … present]** at the **same local hour**.

**Local time handling.**
- Derive **IANA timezone** from lat/lon (e.g., America/Fortaleza).
- Convert **IMERG (UTC)** and **POWER (UTC/LST)** timestamps to **local civil time** and select the samples whose **local hour == hour_local**.
- **Full hours only** in the UI (HH:00); default hour is **10:00**.

**Coverage requirement (quality gate).**
- Require **≥ 15 distinct years** with at least **8 valid hourly samples** total across the ±7‑day window; otherwise return `status: "insufficient_coverage"` with guidance.
- All thresholds, window width, and coverage gates are configurable via env.

**Probability.** For each condition, compute:
- `n =` number of valid hourly samples across all years within the window; `k =` count of samples exceeding the condition threshold.
- **Point estimate:** `p̂ = k / n`.
- **Interval:** 95% **Clopper–Pearson** (binomial exact) `[p_low, p_high]`.

**Trends (tab).**
- For each **year y**, compute `p̂_y` over that year’s DOY±7 at the chosen hour.
- Fit **OLS** slope (percentage points per decade) and report sign, slope, and p‑value.

**Distributions (tab).**
- Per variable, build histogram arrays for all samples (e.g., HI, WS10M, precip rate) plus a vertical threshold marker. (Exact charting TBD; see §12.)

---

## 4) Data sources & variables

**IMERG V07 Final Run Half‑Hourly (GPM_3IMERGHH)**
- Spatial: 0.1°; Temporal: 30‑min; Units: precipitation **rate (mm/h)**.
- Use half‑hours **[HH:00–HH:29]** and **[HH:30–HH:59]** whose **local**, not UTC, time overlaps the chosen hour; aggregate to **hourly mean rate**.
- Mark gaps; if **both half‑hours missing**, use POWER hourly precip (mm/h) and set `precip_source = "POWER"` for that sample; otherwise `"IMERG"` or `"MIXED"`.

**NASA POWER Hourly (MERRA‑2/GEOS‑IT derived)**
- Variables: **T2M (°C)**, **RH2M (%)**, **WS10M (m/s)**, **precip (mm/h; fallback only)**.
- Time standard: query in **UTC** and convert to local, or request **LST** if needed (we will consistently normalize to **local civil time** in the API layer).

---

## 5) API design (FastAPI)

**Base URL** (dev): `http://localhost:8000`

### 5.1 Endpoints

`GET /health`
- Returns `{ status: "ok", version, uptime_s }`.

`POST /risk`
- **Request (JSON)**
```json
{
  "lat": -3.7319,
  "lon": -38.5267,
  "date_local": "2025-10-10",
  "hour_local": "10:00",
  "window_days": 7,
  "baseline_start": 2001,
  "baseline_end": 2025,
  "detail": "lean",
  "units": "metric"
}
```
- **Behavior**
  - Derive IANA zone, select samples at the specified **local hour** across **DOY±window_days** for all years in baseline.
  - Pull **IMERG** and **POWER** with conservative timeout/retry; fill precip gaps per §2.
  - Compute **HI**, **WCT**, wind, precip, and flags; calculate probabilities & intervals.
- **Response (lean)**
```json
{
  "meta": {
    "lat": -3.7319,
    "lon": -38.5267,
    "date_local": "2025-10-10",
    "hour_local": "10:00",
    "timezone": "America/Fortaleza",
    "window_days": 7,
    "baseline": { "start": 2001, "end": 2025 },
    "n_samples": 352,
    "coverage": "ok"
  },
  "conditions": {
    "very_hot": { "p": 0.18, "p95": [0.14, 0.22], "threshold": { "type": "HI_C", "value": 41 } },
    "very_uncomfortable": { "p": 0.36, "p95": [0.31, 0.41], "threshold": { "type": "HI_C", "value": 32 } },
    "very_cold": { "p": 0.00, "p95": [0.00, 0.01], "threshold": { "type": "WCT_C", "value": -10 } },
    "very_windy": { "p": 0.07, "p95": [0.05, 0.10], "threshold": { "type": "WS10M_MS", "value": 10.8 } },
    "very_wet": { "p": 0.12, "p95": [0.09, 0.15], "threshold": { "type": "PRECIP_MM_PER_H", "value": 4.0 } }
  }
}
```
- **Response (detail = "full")**
  - Adds: `distributions` (bin edges + counts for HI/WS10M/precip), `trend` (per‑year `p̂` and OLS fit), and `provenance` (share of samples by source: IMERG/POWER/MIXED).

`POST /export`
- Same request body as `/risk` plus `format: "csv"|"json"`.
- Returns a flat table of the samples (one row per hourly sample) with columns: `timestamp_local, year, doy, lat, lon, hi_c, wct_c, t2m_c, rh2m_pct, ws10m_ms, precip_mm_per_h, flags_{hot,uncomf,cold,windy,wet}, precip_source`.
- Rate‑limited stricter than `/risk`.

`GET /climatology`
- Lightweight helper returning baseline metadata (years available per source, last refresh date, etc.).

### 5.2 Error model
- 4xx: `validation_error`, `insufficient_coverage`, `unsupported_location` (e.g., over ocean if we later restrict), `upstream_timeout`.
- 5xx: `upstream_down`, `internal_error`.

---

## 6) Algorithms & formulas

**Heat Index (HI).** Rothfusz regression (primary) with Celsius conversions; gate to T≥26 °C for messaging, but still compute numerically for continuity.

**Wind Chill (WCT).** NWS formula; valid when T≤10 °C and wind ≥1.3 m/s; outside validity, we compute the formula but do **not** set the cold flag.

**Very wet aggregation (IMERG→hourly).**
- For the chosen **local hour H**: compute mean of `[H:00–H:29]` and `[H:30–H:59]` **rates (mm/h)**. If both half‑hours missing → **fallback** to POWER hourly precip.

**Trends.** OLS slope of yearly `p̂_y` (percentage points per decade) with two‑sided t‑test; report slope and p‑value.

**Intervals.** Clopper–Pearson exact 95% CI from Beta quantiles.

---

## 7) System architecture

**Monorepo** (git):
```
/ (repo root)
  apps/
    api/                    # FastAPI service
    frontend/               # React + Vite app (TypeScript)
  packages/
    shared-schemas/         # Pydantic/TS OpenAPI-derived types
  infra/
    docker/                 # Dockerfiles, compose, Caddyfile
  docs/
    spec.md                 # this file
```

**Backend (apps/api).** FastAPI + Pydantic v2; `httpx` for clients; `numpy/pandas/xarray` for arrays; `timezonefinder` + `zoneinfo`; JSON logging.

**Frontend (apps/frontend).** React + Vite (TypeScript); React Router; Chart.js via `react-chartjs-2` (later); simple map (pin‑drop) with a minimal tiles basemap; no auth.

**Reverse proxy.** **Caddy** (auto‑HTTPS) in front of FE and API on a **single VM**.

**Cache.** Filesystem cache (LRU + TTL) stored under a named Docker volume, keyed by `(lat,lon, doy, window_days, hour, baseline_start, baseline_end, thresholds)`.

**Observability.** JSON structured logs only (request ID, latency, cache hits/misses, upstream timings). No metrics/tracing for MVP.

---

## 8) Deployment & operations

**Single VM + Docker Compose.** One host runs three containers: `caddy` (443/80), `api`, `frontend` (static files can also be served by Caddy directly).

**Caddyfile (sketch).**
```caddy
${SITE_DOMAIN} {
  encode gzip zstd
  @api path /health /risk /export /climatology
  reverse_proxy @api api:8000
  handle {
    root * /srv/frontend
    try_files {path} /index.html
    file_server
  }
}
```

**compose.yaml (sketch).**
```yaml
services:
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./infra/docker/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
      - frontend_dist:/srv/frontend:ro
    depends_on: [api, frontend]

  api:
    build: ./apps/api
    environment:
      - POWER_BASE_URL=https://power.larc.nasa.gov
      - CACHE_DIR=/cache
      - CACHE_MAX_GB=5
      - CACHE_TTL_DAYS=30
      - RATE_LIMIT_GENERAL=30/minute;burst=10
      - RATE_LIMIT_EXPORT=6/minute;burst=6
      - ALLOWED_ORIGINS=http://localhost:5173,http://localhost:4173
      - DEFAULT_BASELINE=2001:present
      - DEFAULT_WINDOW_DAYS=7
      - DEFAULT_HOUR_LOCAL=10:00
      - THRESHOLDS_HI_HOT_C=41
      - THRESHOLDS_HI_UNCOMF_C=32
      - THRESHOLDS_WCT_COLD_C=-10
      - THRESHOLDS_WIND_MS=10.8
      - THRESHOLDS_RAIN_MM_PER_H=4
      - TIMEOUT_CONNECT_S=10
      - TIMEOUT_READ_S=30
      - RETRIES=3
    volumes:
      - cache:/cache

  frontend:
    build: ./apps/frontend
    environment:
      - VITE_API_BASE_URL=/
    volumes:
      - frontend_dist:/dist

volumes:
  cache:
  caddy_data:
  caddy_config:
  frontend_dist:
```

**Secrets.** MVP does not store Earthdata credentials (we use public POWER and open IMERG endpoints via Harmony if needed later). If we add Earthdata auth, mount credentials via Docker secrets/env and never expose to the client.

**Rate limiting.** App‑level IP rate limits (30 req/min, burst 10; `/export` 6/min). CORS allowlist for dev origins only.

---

## 9) API: endpoint stubs (FastAPI)

```py
# apps/api/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional

app = FastAPI(title="Outdoor Risk API", version="0.1.0")

class RiskRequest(BaseModel):
    lat: float
    lon: float
    date_local: str  # YYYY-MM-DD
    hour_local: str  # HH:00 (24h)
    window_days: int = 7
    baseline_start: int = 2001
    baseline_end: int = 9999  # treated as "present"
    detail: Literal["lean", "full"] = "lean"
    units: Literal["metric"] = "metric"

class ConditionOut(BaseModel):
    p: float
    p95: tuple[float, float]
    threshold: dict

class RiskOut(BaseModel):
    meta: dict
    conditions: dict[str, ConditionOut]

@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}

@app.post("/risk", response_model=RiskOut)
async def risk(req: RiskRequest):
    # 1) Resolve timezone from lat/lon; convert to local civil time
    # 2) Fetch/aggregate IMERG half-hours; fallback to POWER hourly precip
    # 3) Fetch POWER hourly T2M, RH2M, WS10M for same hours
    # 4) Compute HI, WCT, flags; estimate p and Clopper–Pearson CI
    # 5) Return lean/full payload
    raise HTTPException(501, "not_implemented")

class ExportRequest(RiskRequest):
    format: Literal["csv", "json"] = "csv"

@app.post("/export")
async def export(req: ExportRequest):
    # Return rows for each hourly sample with computed fields and provenance
    raise HTTPException(501, "not_implemented")

@app.get("/climatology")
async def climatology():
    # Return years available per source and last processed date
    raise HTTPException(501, "not_implemented")
```

---

## 10) Backend implementation notes

**Clients**
- Use `httpx` with: connect 10 s, read 30 s; **3 retries** exponential backoff with full jitter; honor `Retry‑After`; global cap ≈60 s.

**Caching**
- Filesystem cache under `/cache` with (1) **TTL** days, (2) **max size** GB (LRU prune), and (3) key hashing of normalized request params.
- Cache both **raw pulls** (per‑source per‑hour arrays) and **final computed responses** (per request) for speed.

**Time zones**
- `timezonefinder` (lat/lon → IANA zone)
- Python `zoneinfo` for conversion and DST handling; log both UTC and local timestamps in exports.

**Numerics**
- Implement HI (Rothfusz) and WCT in a vectorized helper (`numpy`), with masks for validity domains.
- Clopper–Pearson via `scipy.stats.beta` or an in‑house incomplete beta util (if avoiding SciPy weight).

**Quality**
- For each hourly sample, keep a tri‑state **precip provenance**: `IMERG`, `POWER`, or `MIXED`.
- Record an **inputs snapshot** in the response (`meta.inputs_hash`) for reproducibility.

---

## 11) Frontend skeleton (ship‑ready for dev)

**Stack**: React + Vite (TS), React Router. (Charting and map can be added later without changing the skeleton.)

**Pages**
- **Overview**: 5 cards (one per condition) + compact map (pin‑drop); date + hour pickers (HH:00); submit → calls `/risk`.
- **Distributions**: placeholder for histograms/CDF with threshold lines.
- **Trends**: placeholder for annual exceedance line chart with trend fit.
- **Data**: placeholder for table + export buttons (CSV/JSON).

**State**
- Global query state: `{ lat, lon, date_local, hour_local, window_days, baseline_start, baseline_end }` synced to URL.

**Dev CORS origins**: `http://localhost:5173`, `http://localhost:4173`.

---

## 12) Visualizations (initial defaults)

- **Distributions**: **Histogram + threshold line** per variable (20 bins). (If we change libraries, keep data contracts stable.)
- **Trends**: line of yearly `p̂_y` with a light regression overlay and 95% band.
- **Overview cards**: show `p̂` as a large percentage, `[p_low, p_high]` small, and 1‑line explainer (e.g., “Odds of HI≥41 °C at 10:00 on Oct 10, using Oct 3–17 from 2001–2025”).

---

## 13) Security & compliance

- **Public, read‑only** API.
- **CORS allowlist**: dev origins only (see §11).
- **Rate limits**: 30 req/min (burst 10); `/export` 6/min.
- **No secrets in query strings**; consistent 4xx/5xx error bodies; log `X‑Request‑ID`.

---

## 14) Observability

- **JSON structured logs** for API requests/responses (status, latency, cache hit, upstream timings, request ID); aggregate with `docker logs` for MVP.

---

## 15) Testing policy (CI only)

**Backend**
- Pytest unit tests for HI/WCT helpers and probability/CI math.
- FastAPI TestClient smoke tests for `/health` and one `/risk` happy‑path with mocked clients.
- **VCR.py cassettes** for a couple of POWER hourly calls (offline replay later).

**Frontend**
- React Testing Library: smoke tests for the shell + Overview cards rendering (stubbed API).

---

## 16) Runtimes & versions

- **Python** 3.11 (API) — built‑in `zoneinfo`.
- **Node.js** 20 LTS (frontend).

---

## 17) Configuration (env)

```
ALLOWED_ORIGINS= http://localhost:5173,http://localhost:4173
DEFAULT_BASELINE= 2001:present
DEFAULT_WINDOW_DAYS= 7
DEFAULT_HOUR_LOCAL= 10:00
THRESHOLDS_HI_HOT_C= 41
THRESHOLDS_HI_UNCOMF_C= 32
THRESHOLDS_WCT_COLD_C= -10
THRESHOLDS_WIND_MS= 10.8
THRESHOLDS_RAIN_MM_PER_H= 4
COVERAGE_MIN_YEARS= 15
COVERAGE_MIN_SAMPLES= 8
CACHE_DIR= /cache
CACHE_MAX_GB= 5
CACHE_TTL_DAYS= 30
TIMEOUT_CONNECT_S= 10
TIMEOUT_READ_S= 30
RETRIES= 3
RATE_LIMIT_GENERAL= 30/minute;burst=10
RATE_LIMIT_EXPORT= 6/minute;burst=6
POWER_BASE_URL= https://power.larc.nasa.gov
# If/when using Earthdata‑authenticated services later:
# EARTHDATA_USERNAME= (secret)
# EARTHDATA_PASSWORD= (secret)
```

---

## 18) Milestones (2‑day hackathon)

**Day 1**
- FE scaffold, form + map pin, call `/risk` (mocked).
- API skeleton, cache layer, timezone resolution, POWER client + VCR cassette.
- Implement HI/WCT math + wind/rain thresholds; compute probabilities from mocked samples.
- Wire Caddy + Compose locally; logs OK.

**Day 2**
- IMERG half‑hour aggregation and fallback logic; swap mocked data → live POWER + partial IMERG.
- Lean `/risk` response; Overview cards; `/export` CSV.
- Distributions/Trends placeholders; polish copy; basic tests green; prepare demo.

---

## 19) Risks & mitigations

- **IMERG access/latency** → cache aggressively; limit window to ±7; pre‑validate coverage before pulling data; fallback to POWER for precip in gaps.
- **Timezone edge cases** (DST transitions) → rely on IANA `zoneinfo`; compare UTC vs local indices in tests near DST changes.
- **Sparse samples** (high latitudes / oceans) → return `insufficient_coverage` with rationale and suggest widening window.

---

## 20) Future (post‑MVP)

- Area polygons (drawn AOI) and spatial averaging.
- User place search (Mapbox) with autocomplete.
- SSO/Auth and saved plans.
- Add air quality (PM2.5) and dust from NASA sources.
- Better maps (GIBS imagery overlays for context).

---

## 21) Glossary (user‑facing snippets)

- **Heat Index (HI)**: how hot it feels combining air temperature and humidity. Thresholds used here: **32 °C** (very uncomfortable), **41 °C** (very hot/danger).
- **Wind Chill (WCT)**: how cold it feels considering wind + temperature (valid for cold temps and non‑calm winds). Threshold used here: **−10 °C**.
- **Precipitation rate**: millimeters per hour (mm/h). Threshold used here: **4 mm/h** (heavy rain onset).
- **Very windy**: **≥ 10.8 m/s** (strong breeze).

---

**End of spec.**
