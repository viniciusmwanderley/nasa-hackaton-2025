# Outdoor Risk API

FastAPI backend for the NASA Hackathon 2025 Outdoor Risk MVP.

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

**Alternative (using pip):**
```bash
pip install uv
```

**Verify installation:**
```bash
uv --version
```

## Development

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

### Installing Dependencies

Dependencies are automatically managed by uv. If needed:
```bash
uv pip install fastapi uvicorn[standard] pydantic httpx python-json-logger pytest pytest-asyncio requests anyio
```

## Endpoints

- `GET /health` - Health check endpoint

## Architecture

- **FastAPI** - Modern async web framework
- **Pydantic v2** - Data validation and serialization  
- **Uvicorn** - ASGI server with auto-reload
- **Structured JSON logging** - Request tracking with X-Request-ID
- **Request ID middleware** - Automatic request correlation