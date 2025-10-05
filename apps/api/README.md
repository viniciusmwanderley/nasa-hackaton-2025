# Weather Risk Assessment API

A comprehensive FastAPI service for analyzing weather conditions and assessing risks for outdoor activities using NASA POWER data. This API provides historical weather analysis, predictions, and risk classifications to help users make informed decisions about outdoor activities.

## Features

- **Weather Data Analysis**: Historical and predictive weather data using NASA POWER API
- **Risk Classifications**: Precipitation, temperature extremes, wind, and snow risk assessments  
- **Multiple Granularities**: Daily and hourly weather analysis
- **Temporal Predictions**: Machine learning-based weather predictions using linear regression
- **Comprehensive Statistics**: Historical weather statistics and percentile-based risk scoring
- **Clean Architecture**: Layered architecture with proper separation of concerns
- **Robust Error Handling**: Comprehensive error handling and logging
- **Interactive Documentation**: Auto-generated API documentation with Swagger UI

## Architecture

The API follows Clean Architecture principles with the following layers:

- **Domain**: Core business entities, enums, and interfaces
- **Application**: Business logic services and use cases  
- **Infrastructure**: External service integrations (NASA POWER API)
- **Presentation**: FastAPI routes and API models

## Prerequisites

### Installing uv

This project uses [uv](https://docs.astral.sh/uv/) for fast Python package management. If you don't have uv installed:

**On macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Start

### Installation

```bash
# Install dependencies
uv sync

# Run development server  
uv run dev-server
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Basic Usage

```python
import requests
from datetime import datetime

# Analyze weather risk for Recife, Brazil
response = requests.post("http://localhost:8000/weather/analyze", json={
    "latitude": -8.0476,
    "longitude": -34.8770, 
    "center_datetime": "2024-07-15T14:00:00-03:00",
    "target_timezone": "America/Fortaleza",
    "days_before": 3,
    "days_after": 3,
    "granularity": "daily"
})

# Equivalent curl command
curl -X POST "http://localhost:8000/weather/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -8.0476,
    "longitude": -34.8770,
    "center_datetime": "2024-07-15T14:00:00-03:00",
    "target_timezone": "America/Fortaleza",
    "days_before": 3,
    "days_after": 3,
    "granularity": "daily"
  }'

result = response.json()
print(f"Rain probability: {result['classifications']['rain_probability']:.1%}")
```

## API Endpoints

### Weather Analysis

**POST `/weather/analyze`** - Main weather analysis endpoint

Analyzes weather conditions and risk factors for a date range around a center date.

**Request Parameters:**
- `latitude` (float): Latitude coordinate (-90 to 90)
- `longitude` (float): Longitude coordinate (-180 to 180) 
- `center_datetime` (datetime): Center datetime for analysis
- `target_timezone` (str): Target timezone (e.g., "America/Sao_Paulo")
- `days_before` (int, optional): Days before center date (default: 3)
- `days_after` (int, optional): Days after center date (default: 3)
- `granularity` (str): "daily" or "hourly"
- `parameters` (list, optional): Weather parameters to include
- `start_year` (int, optional): Historical data start year (default: 1984)
- `window_days` (int, optional): Temporal regression window (default: 7)

**Response:** Complete weather analysis with:
- Historical statistics
- Weather predictions for each day/hour
- Risk classifications and percentiles
- Metadata about the analysis

### Utility Endpoints

**GET `/weather/health`** - Weather service health check
**GET `/weather/parameters`** - List of available weather parameters
**GET `/health`** - Main application health check

## Weather Parameters

The API supports various weather parameters from NASA POWER:

- **T2M**: Temperature at 2 Meters (°C)
- **T2M_MAX/MIN**: Daily max/min temperatures (°C) 
- **PRECTOTCORR**: Precipitation Corrected (mm)
- **IMERG_PRECTOT**: IMERG Precipitation (mm) - Daily only
- **RH2M**: Relative Humidity at 2 Meters (%)
- **WS10M**: Wind Speed at 10 Meters (m/s)
- **CLOUD_AMT**: Cloud Amount (%) - Daily only
- **FRSNO**: Snow Fraction (%)
- **ALLSKY_SFC_SW_DWN**: Solar Irradiance (kW-hr/m²/day)

## Risk Classifications

The API provides several risk classifications:

- **Rain Probability**: Likelihood of precipitation based on seasonal patterns
- **Temperature Percentiles**: How extreme predicted temperatures are compared to historical data
- **Heat Index**: Feels-like temperature considering humidity
- **Wind Percentiles**: Wind speed relative to historical patterns  
- **Snow Probability**: Likelihood of snow based on temperature and historical patterns
- **Stormy Weather**: Probability of combined high precipitation and wind

## Examples

See `examples.py` for comprehensive usage examples including:
- Daily weather analysis
- Hourly weather analysis  
- Historical statistics analysis

```bash
# Run examples
cd apps/api
uv run python examples.py
```

## Development

### Project Structure

```
app/
├── domain/          # Core business entities and interfaces
├── application/     # Business logic services  
├── infrastructure/  # External service integrations
├── presentation/    # FastAPI routes and models
└── main.py         # FastAPI application entry point
```

### Running the Server

**Option 1: Using uv run with uvicorn (recommended)**
```bash
uv run --with uvicorn uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option 2: Using the run script**
```bash
uv run python run.py
```

### Run integration test
#### Groelandia (Very cold)
```bash
curl -s -X POST "http://localhost:8000/risk"   -H "Content-Type: application/json"   -d '{
       "latitude": -76.916356,
       "longitude": 45.327665,
       "target_date": "2024-06-15",
       "target_hour": 14,
       "window_days": 3,
       "detail": "lean"
     }' | python -m json.tool
```

#### Antartica (Very wind)
```bash
curl -s -X POST "http://localhost:8000/risk"   -H "Content-Type: application/json"   -d '{
       "latitude": -66.909701,
       "longitude": 143.162005,
       "target_date": "2024-06-15",
       "target_hour": 14,
       "window_days": 3,
       "detail": "lean"
     }' | python -m json.tool
```

#### 


### Running Tests

```bash
uv run python -m pytest tests/ -v
```

## NASA POWER API Integration

This API integrates with NASA's POWER (Prediction Of Worldwide Energy Resources) API to access:
- Historical weather data from 1984-present
- Global coverage with 0.5° x 0.625° resolution
- Multiple temporal granularities (daily/hourly)
- Comprehensive meteorological parameters

## License

This project was developed for NASA Hackathon 2025.