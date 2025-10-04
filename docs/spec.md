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

*[Continuing with full specification content...]*