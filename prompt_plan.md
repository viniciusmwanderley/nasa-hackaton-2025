# Outdoor Risk — Build Blueprint (MVP)

This blueprint translates **spec.md** into a concrete, test-driven, incremental plan you can execute during the hackathon. It breaks work into phases → chunks → bite-size steps, and includes ready-to-use **LLM coding prompts** (TDD-first) with no orphan code.

> Primary references (kept in this plan for dev context):
> • NASA POWER Hourly API & parameters • IMERG V07 Final Run (half-hourly mm/hr) • Harmony (subset/regrid) • NWS Heat Index & Wind Chill formulas • Python `zoneinfo` & `timezonefinder` • Clopper–Pearson method. See **spec.md** citations list.

---

## 0) Guiding principles
- **Safety first**: ship a small, correct core quickly; expand in small, verified increments.
- **TDD**: every step adds (or expands) tests that run fast locally.
- **One change at a time**: introduce a new module behind an interface; integrate immediately.
- **12-factor config**: all thresholds, windows, timeouts, CORS, and rate limits via env.
- **Observability**: JSON logs (request id, latency, cache hits, upstream timings), no metrics for MVP.

---

## 1) Architecture at a glance (monorepo)
```
/ (repo)
  apps/
    api/                    # FastAPI (Python 3.11)
    frontend/               # React + Vite + TS
  packages/
    shared-schemas/         # (later) OpenAPI → TS types
  infra/
    docker/                 # Dockerfiles, compose, Caddyfile
  docs/
    spec.md, plan.md, todo.md
```
**Back end**: FastAPI, httpx, numpy, (scipy optional), timezonefinder, zoneinfo, pytest, VCR.py.  
**Front end**: React, React Router; charts later; simple Leaflet map later.  
**Proxy**: Caddy (auto-HTTPS) — local compose first.

---

## 2) Phases → Chunks → Steps

### Phase 0 — Repo, Tooling, and CI (baseline)
**Chunks**  
0.1 Init monorepo scaffolding.  
0.2 API skeleton with `/health` + JSON logging.  
0.3 Frontend scaffold with routing stubs.  
0.4 Local dev scripts + Compose (dev profile only).  
0.5 CI (lint/tests) with minimal jobs.

**Steps**
- 0.1.1 Create repo layout (`apps/api`, `apps/frontend`, `infra/docker`, `docs`).
- 0.1.2 Add `.editorconfig`, `.gitignore`, `README.md`.
- 0.2.1 API: FastAPI app with `/health`; Pydantic models dir.
- 0.2.2 Add JSON logger (uvicorn + app logger) and request id middleware.
- 0.3.1 FE: Vite React-TS scaffold; add Router; stub pages (Overview, Distributions, Trends, Data).
- 0.4.1 Dev `compose.yaml` with `api` and `frontend`; wire ports.
- 0.5.1 GitHub Actions (CI only): run `pytest` and `vitest` on push/PR.

### Phase 1 — Backend foundations
**Chunks**  
1.1 Configuration module (env with defaults from spec).  
1.2 Error model & common responses.  
1.3 CORS + rate limit middleware (dev origins; 30 rpm; export 6 rpm).

**Steps**
- 1.1.1 Implement `config.py` (env parsing, defaults, validation).
- 1.1.2 Unit test config (override envs).
- 1.2.1 Define error schemas + exception handlers.
- 1.3.1 Add CORSMiddleware; SlowAPI (or simple in-proc limiter) with env-driven limits.

### Phase 2 — Time & calendar handling
**Chunks**  
2.1 Timezone resolver (lat/lon → IANA).  
2.2 Local hour validation (HH:00) and DOY extraction.

**Steps**
- 2.1.1 Wrap `timezonefinder` lookup + `zoneinfo` conversion; cache by (lat,lon).
- 2.1.2 Tests for DST edges (America/Fortaleza has no DST — include a zone that does for unit tests).
- 2.2.1 Helper: date string → DOY; validate hour string → int 0..23.

### Phase 3 — POWER client (hourly)
**Chunks**  
3.1 httpx client with retries/backoff.  
3.2 Fetch hourly `T2M`, `RH2M`, `WS10M`, `PRECIP` in UTC window; map to local hour.  
3.3 VCR cassettes for 1–2 locations.

**Steps**
- 3.1.1 Implement `clients/power.py` with base URL, params, and retry policy.
- 3.1.2 Test: happy path parses arrays and timestamps.
- 3.2.1 Local-hour selector: filter by local hour; return arrays aligned to sample dates.
- 3.3.1 Record VCR cassettes; add offline test.

### Phase 4 — Numerics (HI, WCT, wind, precip)
**Chunks**  
4.1 Heat Index (Rothfusz) in °C.  
4.2 Wind Chill (NWS) in °C with validity gating.  
4.3 Threshold helpers (hot/uncomf/cold/windy/wet at hour).

**Steps**
- 4.1.1 Implement `metrics/heat_index.py` with conversions and vectorization.
- 4.1.2 Unit tests using published examples / internal cases.
- 4.2.1 Implement `metrics/wind_chill.py` with validity masks.
- 4.2.2 Unit tests (edge temps/winds).
- 4.3.1 Implement threshold functions with env defaults.

### Phase 5 — Probability engine & coverage
**Chunks**  
5.1 Sample collector (build sample set for DOY±W at hour).  
5.2 Probability + Clopper–Pearson 95% interval.  
5.3 Coverage gate and status reporting.

**Steps**
- 5.1.1 Implement `engine/samples.py` → unify POWER pulls per year and local hour.
- 5.1.2 Unit test: counts for synthetic inputs.
- 5.2.1 Implement `engine/probability.py` with binomial CI.
- 5.2.2 Unit tests for small/large n; k=0 and k=n cases.
- 5.3.1 Coverage check; unit tests.

### Phase 6 — IMERG aggregator (hourly) + fallback
**Chunks**  
6.1 Harmony/earthaccess or direct download wrapper (token via env).  
6.2 Half-hour → hourly aggregation; provenance flagging.  
6.3 Tests with tiny sample files or cassettes.

**Steps**
- 6.1.1 Implement `clients/imerg.py` (half-hourly rates, mm/h) with retries.
- 6.1.2 Unit test parsing minimal granules (fixture file) without relying on network.
- 6.2.1 Aggregation: map UTC half-hours → local hour; compute hourly mean; fallback to POWER if both missing.
- 6.2.2 Unit tests for (both present / one missing / both missing → fallback).

### Phase 7 — `/risk` endpoint (lean + full)
**Chunks**  
7.1 Lean response: probabilities + thresholds + CI.  
7.2 Full response: add distributions and yearly trend series.

**Steps**
- 7.1.1 Wire request model → sampling engine (POWER + IMERG); compute flags; return lean JSON.
- 7.1.2 Integration test with mocks for both clients.
- 7.2.1 Distributions: bin edges + counts for HI/WS10M/precip.
- 7.2.2 Trends: annual exceedance rate and simple OLS fit (slope, p).

### Phase 8 — `/export` (CSV/JSON)
**Chunks**  
8.1 Row builder per hourly sample with provenance.  
8.2 CSV + JSON serializers; rate limit applied.

**Steps**
- 8.1.1 Implement exporter with unit tests for header/rows and units.
- 8.2.1 Endpoint wiring + integration test.

### Phase 9 — Frontend integration (Overview + Tabs)
**Chunks**  
9.1 FE scaffold (React/Vite/TS + Router) — if not done in Phase 0.  
9.2 Query form (lat/lon, date, hour) + call `/risk`.  
9.3 Overview cards rendering.  
9.4 Tabs shell (Distributions/Trends/Data) with placeholders.

**Steps**
- 9.1.1 Initialize Vite app; smoke test.
- 9.2.1 Form and API client; render lean results.
- 9.3.1 Card component with % and CI; snapshot test.
- 9.4.1 Tabs + navigation smoke tests.

### Phase 10 — Compose + Caddy (local dev)
**Chunks**  
10.1 Dockerfiles for api/frontend.  
10.2 Compose file; Caddyfile; SPA fallback.

**Steps**
- 10.1.1 Write Dockerfiles; verify local builds.
- 10.2.1 Compose up; verify reverse proxy routes FE and API.

---

## 3) Right-sizing check
- Each step yields a runnable build/test; no step introduces large, untested surfaces.
- External calls are either mocked or cassette-recorded before use.
- FE integrates early with mocked `/risk` to avoid late surprises.

---

## 4) LLM Coding Prompts (TDD-first)
> Use these sequentially. Each prompt: write tests **first**, then minimal code to pass, then refactor if needed.

### Prompt 0 — Monorepo bootstrap - COMPLETE
```text
You are helping build a monorepo with apps/api (FastAPI, Python 3.11) and apps/frontend (React+Vite+TS).
TASKS:
1) Create directories: apps/api, apps/frontend, infra/docker, docs.
2) Add repo root files: .gitignore (Python, Node, Vite, macOS), .editorconfig, README.md (one-paragraph project summary).
3) In docs/, create placeholders: spec.md (will be provided), plan.md, todo.md.
4) Output the final tree and any generated files.
NO CODE RUN YET.
```

### Prompt 1 — API skeleton with `/health` and tests - COMPLETE
```text
Goal: Create FastAPI app with /health and JSON logging.

1) In apps/api, create Poetry project or bare requirements with: fastapi, uvicorn[standard], pydantic, httpx, python-json-logger, pytest, pytest-asyncio, requests, anyio.
2) Implement apps/api/app/main.py exposing GET /health returning {"status":"ok","version":"0.1.0"}.
3) Add minimal Uvicorn config to run locally (port 8000).
4) Tests: create apps/api/tests/test_health.py using TestClient to assert 200 and JSON body.
5) Add a JSON logger config (app logger + uvicorn access) and a middleware that injects X-Request-ID if missing; unit test that the header is present on response.
Return file diffs and test results.
```

### Prompt 2 — Config module (env) + CORS + rate limiting - COMPLETE
```text
Goal: Config + security baselines.

1) Implement apps/api/app/config.py reading env vars with defaults (see spec thresholds, windows, CORS origins, rate limits). Provide typed accessors.
2) Wire CORSMiddleware to allow only http://localhost:5173 and http://localhost:4173.
3) Add simple in-process rate limiter (e.g., SlowAPI or a token-bucket) with env-driven limits: 30 req/min (burst 10), export=6/min.
4) Tests: unit test env overrides; functional test that a burst over the limit yields HTTP 429 with Retry-After header.
```

### Prompt 3 — Timezone utilities (lat/lon → IANA; local hour) - COMPLETE
```text
Goal: Robust local-time handling.

1) Add deps: timezonefinder, tzdata.
2) Implement app/time/timezone.py: fn tz_for_point(lat,lon)->str using timezonefinder; cache results.
3) Implement fn to_local(dt_utc, iana)->aware datetime; fn local_hour_matches(dt_utc, iana, target_hour:int)->bool.
4) Helper: parse_date("YYYY-MM-DD")->date; doy(date)->int; parse_hour("HH:00")->int.
5) Tests: DST edge cases (pick a zone with DST), Fortaleza (no DST), hour parsing validations.
```

### Prompt 4 — POWER client (hourly) with retries + VCR - COMPLETE
```text
Goal: Fetch hourly T2M, RH2M, WS10M, PRECIP in UTC and map to local hour.

1) Add app/clients/power.py using httpx Client with connect=10s, read=30s, 3 retries exponential backoff with jitter; honor Retry-After.
2) Implement fetch_power_hourly(lat,lon,start,end, params=["T2M","RH2M","WS10M","PRECTOTCORR"]) returning a tidy dataframe with utc timestamp and variables.
3) Implement select_local_hour(df, iana, hour)->filtered df whose local hour==hour.
4) Tests: use VCR.py to record a real request for a tiny range; assert columns/rows and that local-hour filter works.
```

### Prompt 5 — Heat Index & Wind Chill modules (tested) - COMPLETE
```text
Goal: Add metrics with unit-safe implementations.

1) Implement app/metrics/heat_index.py with Rothfusz regression in Celsius (convert inputs/outputs appropriately). Provide vectorized fn hi_c(t2m_c, rh_pct)->np.ndarray.
2) Implement app/metrics/wind_chill.py with NWS formula; also return a boolean mask indicating validity domain (T<=10C and wind>=1.3m/s). Fn wct_c(t2m_c, ws_ms)->(np.ndarray, mask).
3) Tests: numeric cases including boundary conditions; verify monotonicity and basic sanity (e.g., HI>=T when RH>0, etc.).
```

### Prompt 6 — Threshold helpers - COMPLETE
```text
Goal: Flag conditions per sample at the selected hour.

1) Implement app/engine/thresholds.py with functions:
   is_very_hot(hi_c>=41), is_uncomfortable(hi_c>=32), is_very_cold(wct_c<=-10 & mask), is_very_windy(ws>=10.8), is_very_wet(prate>=4.0).
2) Tests: truth tables with synthetic arrays.
```

### Prompt 7 — Probability engine + Clopper–Pearson - COMPLETE
```text
Goal: Compute probabilities with exact 95% CI.

1) Implement app/engine/probability.py: binom_point_ci(k,n,alpha=0.05)->(p,lo,hi) using scipy.stats.beta or an exact beta-quantile fallback.
2) Tests: k=0, k=n, mid k for several n; compare to known values within tolerance.
```

### Prompt 8 — Sample collector (POWER only) and integration - COMPLETE
```text
Goal: Assemble samples over DOY±W at local hour using POWER.

1) app/engine/samples.py: given lat,lon,date_local,hour_local,window_days, baseline_y1,y2, build a list of UTC timestamps to pull; fetch POWER once per year; select local-hour rows; return arrays for T2M,RH2M,WS10M and placeholder precip.
2) Tests: synthetic seasons (mock client) to verify counts and boundaries; ensure coverage gate (>=15 years & >=8 samples) enforced.
```

### Prompt 9 — IMERG client + hourly aggregation + fallback - COMPLETE
```text
Goal: Integrate precipitation from IMERG half-hourly (mm/h) aggregated to the selected local hour; fallback to POWER when both half-hours missing.

1) app/clients/imerg.py: implement fetch_imerg_halfhour(lat,lon,start,end) returning df with utc timestamps and rate_mm_per_h.
2) app/engine/precip_hourly.py: given iana zone and target hour, compute the mean of the two half-hours overlapping the local hour; provenance flag IMERG/MIXED/POWER.
3) Tests: fixtures with half-hour records for cases: (a) both present, (b) one present, (c) both missing -> fallback; assert provenance.
```

### Prompt 10 — `/risk` (lean) end-to-end - COMPLETE
```text
Goal: Wire inputs → sampling → metrics → probabilities; return lean JSON.

1) Implement request/response models per spec.
2) In the route, resolve timezone, collect POWER samples, integrate IMERG hourly precip, compute HI/WCT, flags and probabilities with CI.
3) Tests: integration with mocked clients producing deterministic arrays; assert JSON shape and values.
```

### Prompt 11 — `/risk?detail=full` (distributions + trends)
```text
Goal: Add distributions (histograms) and annual exceedance trend series.

1) Compute histogram bins+counts for HI, WS10M, precip; include threshold values.
2) Compute yearly exceedance rate for each condition; perform OLS slope and p-value; include in response.
3) Tests: deterministic inputs hitting known bins and a monotone trend; assert payload.
```

### Prompt 12 — `/export` CSV/JSON
```text
Goal: Export one row per hourly sample with provenance and flags.

1) Implement exporters (CSV and JSONL or array) with headers: timestamp_local, year, doy, lat, lon, t2m_c, rh2m_pct, ws10m_ms, hi_c, wct_c, precip_mm_per_h, precip_source, flags_*.
2) Route wiring with stricter rate limit; Content-Disposition filename.
3) Tests: header match, row count, units, and provenance correctness.
```

### Prompt 13 — Frontend scaffold + Overview call to `/risk`
```text
Goal: Render Overview with 5 cards fed by /risk (lean).

1) Initialize Vite React-TS app with React Router; stub pages.
2) Implement API client using VITE_API_BASE_URL; add form (lat,lon,date,hour) with defaults; on submit call /risk.
3) Render 5 cards showing p% and CI; basic CSS.
4) Tests: smoke test mounting Overview; mock fetch to return fixture JSON and assert card values.
```

### Prompt 14 — Tabs shell + Data export
```text
Goal: Add tabs (Overview/Distributions/Trends/Data) and /export buttons.

1) Implement tabs and routes; Distributions/Trends placeholders.
2) Add Data table bound to /export result; download CSV/JSON.
3) Tests: navigation and download link presence.
```

### Prompt 15 — Compose + Caddy (dev) and run
```text
Goal: Containerize and run locally.

1) Write Dockerfiles for api and frontend; multi-stage for FE.
2) Compose file with caddy reverse_proxy to api:8000 and FE static files; SPA fallback to index.html.
3) Manual verification: compose up; open FE, run a sample query.
```

---

## 5) Done definition per phase
- **Green tests**, **lint passes**, and **manual smoke** via Compose.
- No TODO comments unresolved in core modules.
- Logs are informative for failures.

---

## 6) Rollback & contingency
- If IMERG access blocks progress, keep `/risk` working with POWER only and mark `very_wet` as `unknown` with reason in response until IMERG comes online.

---
