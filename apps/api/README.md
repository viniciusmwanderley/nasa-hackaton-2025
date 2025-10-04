# Outdoor Risk API 🌤️

A comprehensive FastAPI backend for outdoor activity risk assessment using NASA POWER weather data. This API provides intelligent weather analysis and classification to help users make informed decisions about outdoor activities.

## 🚀 Features

### Weather Analysis
- **Historical Data Integration**: Fetches comprehensive weather data from NASA POWER API
- **Statistical Analysis**: Provides detailed statistical insights including percentiles, means, and distributions
- **Climatology Comparison**: Compares current conditions against long-term averages
- **Multi-Granularity Support**: Both daily and hourly weather data analysis
- **Heat Index Calculation**: Advanced comfort index calculations for temperature and humidity

### Risk Classification
- **5 Weather Condition Classifications**:
  - 🌡️ **Very Hot**: Temperature exceeds 35°C
  - 🧊 **Very Cold**: Temperature below 5°C  
  - 💨 **Very Windy**: Wind speed exceeds 15 m/s (54 km/h)
  - 🌧️ **Very Wet**: Precipitation exceeds 25mm/day
  - 😰 **Very Uncomfortable**: Heat index exceeds 40°C

- **Probability Assessment**: Statistical probability calculations for each condition
- **Confidence Levels**: Low, medium, and high confidence based on sample size and probability
- **Risk Summary**: Overall risk assessment with primary concerns identification

### API Features
- **Clean Architecture**: Modular design with clear separation of concerns
- **Request Tracking**: Built-in request ID middleware for traceability
- **Comprehensive Validation**: Pydantic models ensure data integrity
- **Error Handling**: Graceful error handling with detailed error responses
- **Auto Documentation**: OpenAPI/Swagger documentation at `/docs`

## 📊 API Endpoints

### Weather Analysis
```http
POST /weather/analyze
```
Performs comprehensive weather analysis for a specific location and time.

**Request Body:**
```json
{
  "latitude": -7.115,
  "longitude": -34.863,
  "target_datetime": "2025-12-25T14:00:00",
  "granularity": "hourly",
  "start_year": 2005,
  "window_days": 7
}
```

**Response:**
```json
{
  "meta": {
    "latitude": -7.115,
    "longitude": -34.863,
    "target_datetime": "2025-12-25T14:00:00",
    "granularity": "hourly",
    "analysis_mode": "probabilistic",
    "historical_data_range": ["2005-01-01", "2025-10-04"],
    "window_days_used": 7
  },
  "derived_insights": {
    "heat_index": {
      "mean_heat_index_c": 30.2,
      "p90_heat_index_c": 34.5,
      "note": "Heat index calculated for T>=26.7C and RH>=40%."
    }
  },
  "parameters": {
    "T2M": {
      "mode": "probabilistic",
      "climatology_month_mean": 27.2,
      "stats": {
        "count": 150,
        "mean": 28.1,
        "median": 27.8,
        "min": 24.5,
        "max": 32.3,
        "std": 2.1,
        "p10": 25.8,
        "p25": 26.7,
        "p75": 29.4,
        "p90": 31.2
      },
      "sample_size": 150
    }
  },
  "classifications": [
    {
      "condition": "very_hot",
      "probability": 0.75,
      "confidence": "high",
      "threshold_value": 35.0,
      "parameter_used": "T2M",
      "description": "Temperature exceeds 35°C indicating very hot conditions"
    }
  ],
  "request_id": "uuid-string"
}
```

### Available Parameters
```http
GET /weather/parameters
```
Returns available weather parameters with descriptions and units.

### Classification Thresholds
```http
GET /weather/thresholds
```
Returns weather condition thresholds and their definitions.

### Health Check
```http
GET /health
```
API health status endpoint.

## 🛠️ Development

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installing uv

**On macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup
```bash
# Install dependencies
uv install

# Run development server
uv run dev-server
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Project Structure
```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── controllers/            # API route handlers
│   ├── __init__.py
│   └── weather_controller.py
├── services/              # Business logic
│   ├── __init__.py
│   ├── weather_service.py
│   └── classification_service.py
├── models/                # Pydantic models
│   ├── __init__.py
│   └── weather.py
└── mock-processing/       # Original mock implementation
    └── mock-processing.py
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_weather_endpoints.py

# Run with verbose output
uv run pytest -v
```

### Test Coverage
The project includes comprehensive test coverage:
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end API testing
- **Service Tests**: Business logic validation
- **Controller Tests**: API endpoint testing

## 🌐 Data Source

This API integrates with the **NASA POWER (Prediction Of Worldwide Energy Resources)** database, which provides:
- Global meteorological data from 1984 to near real-time
- Satellite-derived and modeled parameters
- Daily and hourly granularity options
- High-quality, validated weather data

### Supported Parameters
- **T2M**: Temperature at 2 meters (°C)
- **T2M_MAX/MIN**: Daily max/min temperature (°C)  
- **RH2M**: Relative humidity at 2 meters (%)
- **WS10M**: Wind speed at 10 meters (m/s)
- **PRECTOTCORR**: Bias-corrected precipitation (mm/day)

## 🔧 Configuration

### Environment Variables
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: info)

### Analysis Modes
- **Observed**: For historical dates with available data
- **Probabilistic**: For future dates using statistical analysis

### Granularity Options
- **Daily**: Aggregated daily weather data
- **Hourly**: Hourly weather data (limited historical range)

## 🚀 Deployment

### Production Setup
```bash
# Install production dependencies
uv install --no-dev

# Run with production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Support
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Copy project files
COPY . /app
WORKDIR /app

# Install dependencies
RUN uv install --no-dev

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Performance

### Optimization Features
- **Chunked Data Fetching**: Efficiently handles large historical datasets
- **Request Caching**: Session-based HTTP connection pooling
- **Retry Logic**: Robust handling of network issues
- **Statistical Sampling**: Smart data filtering for relevant time windows

### Response Times
- **Health Check**: < 10ms
- **Parameter/Threshold Endpoints**: < 50ms
- **Weather Analysis**: 2-15 seconds (depending on data range and granularity)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is part of NASA Hackathon 2025 and follows the event's licensing terms.

## 🙏 Acknowledgments

- **NASA POWER Team** for providing comprehensive global weather data
- **FastAPI** for the excellent web framework
- **Pydantic** for robust data validation
- **NumPy** for efficient statistical computations

---

Built with ❤️ for NASA Hackathon 2025 🚀