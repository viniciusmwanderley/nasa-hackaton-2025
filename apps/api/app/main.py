# ABOUTME: Main FastAPI application with health endpoint and request ID middleware
# ABOUTME: Provides basic API structure with JSON logging and request tracking

import uuid
import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pythonjsonlogger import jsonlogger
from app.config import Settings
from app.models import (
    RiskRequest, RiskResponseLean, RiskResponseFull, ErrorResponse,
    ConditionProbability, ConfidenceInterval, SampleStatistics, ConditionThresholds,
    ExportRequest
)
from app.analysis.distributions import calculate_distributions
from app.analysis.trends import calculate_all_trends
from app.export.exporter import (
    create_export_rows, export_to_csv, export_to_json,
    generate_export_filename, get_content_type, validate_export_data
)
from app.engine.samples import collect_samples, InsufficientCoverageError
from app.analysis.probability import calculate_probability
from app.weather.calculations import heat_index, wind_chill
from app.weather.thresholds import flag_weather_conditions, WeatherSample
from app.weather.power import PowerClient


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to inject X-Request-ID header if missing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state for logging
        request.state.request_id = request_id
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request details
        logger = logging.getLogger("outdoor_risk_api")
        logger.info(
            "Request processed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
            }
        )
        
        return response


def setup_logging():
    """Configure JSON structured logging."""
    # Create custom formatter
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logHandler.setFormatter(formatter)
    
    # Configure logger
    logger = logging.getLogger("outdoor_risk_api")
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    # Configure uvicorn logger to use JSON format
    uvicorn_logger = logging.getLogger("uvicorn.access")
    if uvicorn_logger.handlers:
        uvicorn_logger.handlers[0].setFormatter(formatter)


# Setup logging
setup_logging()

# Load configuration
settings = Settings()

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Outdoor Risk API",
    version="0.1.0",
    description="NASA Hackathon 2025 - Estimate odds of adverse weather conditions"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
@limiter.limit(settings.rate_limit_general)
def health(request: Request):
    """Health check endpoint with rate limiting."""
    return {
        "status": "ok",
        "version": app.version
    }


@app.post("/risk")
@limiter.limit(settings.rate_limit_general)
async def assess_risk(request: Request, risk_request: RiskRequest):
    """
    Assess outdoor weather risk for a specific location, date, and time.
    
    Analyzes historical weather patterns to estimate the probability of
    dangerous conditions (very hot, very cold, very windy, very wet).
    
    Returns probabilities with 95% confidence intervals based on historical
    data analysis over the specified time window.
    
    Query parameter 'detail' can be 'lean' (default) or 'full':
    - lean: Returns probabilities and basic statistics only
    - full: Returns probabilities, distributions, and trend analysis
    """
    try:
        logger = logging.getLogger("outdoor_risk_api")
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.info(
            f"Risk assessment requested for ({risk_request.latitude}, {risk_request.longitude}) "
            f"on {risk_request.target_date} at {risk_request.target_hour}:00 local time",
            extra={"request_id": request_id}
        )
        
        # Collect historical weather samples
        try:
            sample_collection = await collect_samples(
                latitude=risk_request.latitude,
                longitude=risk_request.longitude,
                target_date_str=risk_request.target_date,
                target_hour=risk_request.target_hour,
                window_days=risk_request.window_days,
                settings=settings
            )
        except InsufficientCoverageError as e:
            logger.warning(f"Insufficient coverage: {e}", extra={"request_id": request_id})
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient historical data coverage: {e}"
            )
        except ValueError as e:
            logger.error(f"Invalid request parameters: {e}", extra={"request_id": request_id})
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Sample collection failed: {e}", extra={"request_id": request_id})
            raise HTTPException(
                status_code=500,
                detail="Failed to collect weather samples"
            )
        
        # Convert engine WeatherSample to weather WeatherSample for compatibility
        from app.weather.thresholds import WeatherSample as ThresholdWeatherSample
        
        threshold_samples = []
        for sample in sample_collection.samples:
            threshold_sample = ThresholdWeatherSample(
                temperature_c=sample.temperature_c,
                relative_humidity=sample.relative_humidity,
                wind_speed_ms=sample.wind_speed_ms,
                precipitation_mm_per_day=sample.precipitation_mm_per_day,
                timestamp=sample.timestamp_utc,
                latitude=sample.latitude,
                longitude=sample.longitude
            )
            threshold_samples.append(threshold_sample)
        
        # Calculate probabilities for each condition
        conditions = ['hot', 'cold', 'windy', 'wet', 'any']
        probabilities = {}
        
        for condition in conditions:
            try:
                prob_result = calculate_probability(
                    samples=threshold_samples,
                    condition_type=condition,
                    settings=settings
                )
                
                probabilities[condition] = ConditionProbability(
                    probability=prob_result.probability,
                    confidence_interval=ConfidenceInterval(
                        lower=prob_result.confidence_interval_lower,
                        upper=prob_result.confidence_interval_upper,
                        level=prob_result.confidence_level,
                        width=prob_result.confidence_interval_width
                    ),
                    positive_samples=prob_result.positive_samples
                )
                
            except Exception as e:
                logger.error(f"Probability calculation failed for {condition}: {e}", extra={"request_id": request_id})
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to calculate {condition} probability"
                )
        
        # Build base response data
        base_data = {
            "latitude": risk_request.latitude,
            "longitude": risk_request.longitude,
            "target_date": risk_request.target_date,
            "target_hour": risk_request.target_hour,
            "very_hot": probabilities['hot'],
            "very_cold": probabilities['cold'],
            "very_windy": probabilities['windy'],
            "very_wet": probabilities['wet'],
            "any_adverse": probabilities['any'],
            "sample_statistics": SampleStatistics(
                total_samples=sample_collection.total_samples,
                years_with_data=sample_collection.years_with_data,
                coverage_adequate=sample_collection.coverage_adequate,
                timezone_iana=sample_collection.timezone_iana
            ),
            "thresholds": ConditionThresholds(
                very_hot_c=settings.thresholds_hi_hot_c,
                very_cold_c=settings.thresholds_wct_cold_c,
                very_windy_ms=settings.thresholds_wind_ms,
                very_wet_mm_per_h=settings.thresholds_rain_mm_per_h
            )
        }
        
        # Check if full detail is requested
        if risk_request.detail == "full":
            logger.info("Calculating distributions and trends for full response", extra={"request_id": request_id})
            
            try:
                # Calculate distributions
                distributions = calculate_distributions(threshold_samples, settings)
                
                # Calculate trends
                trends = calculate_all_trends(threshold_samples, settings)
                
                # Build full response
                response = RiskResponseFull(
                    **base_data,
                    distributions=distributions,
                    trends=trends
                )
                
            except Exception as e:
                logger.error(f"Failed to calculate distributions/trends: {e}", extra={"request_id": request_id})
                # Fall back to lean response if full calculations fail
                response = RiskResponseLean(**base_data)
        else:
            # Build lean response
            response = RiskResponseLean(**base_data)
        
        logger.info(
            f"Risk assessment completed: {sample_collection.total_samples} samples analyzed, "
            f"detail={risk_request.detail}",
            extra={"request_id": request_id}
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.error(f"Unexpected error in risk assessment: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="Internal server error during risk assessment"
        )


@app.post("/export")
@limiter.limit(settings.rate_limit_export)
async def export_data(request: Request, export_request: ExportRequest):
    """
    Export weather sample data in CSV or JSON format.
    
    Provides detailed sample-by-sample data including all meteorological
    parameters, calculated indices, and condition flags for the specified
    location, date, and time window.
    
    Rate limited to prevent abuse - stricter than general API endpoints.
    """
    try:
        logger = logging.getLogger("outdoor_risk_api")
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.info(
            f"Data export requested for ({export_request.latitude}, {export_request.longitude}) "
            f"on {export_request.target_date} at {export_request.target_hour}:00 "
            f"in {export_request.format} format",
            extra={"request_id": request_id}
        )
        
        # Collect historical weather samples (same as risk assessment)
        try:
            sample_collection = await collect_samples(
                latitude=export_request.latitude,
                longitude=export_request.longitude,
                target_date_str=export_request.target_date,
                target_hour=export_request.target_hour,
                window_days=export_request.window_days,
                settings=settings
            )
        except InsufficientCoverageError as e:
            logger.warning(f"Insufficient coverage for export: {e}", extra={"request_id": request_id})
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient historical data coverage: {e}"
            )
        except ValueError as e:
            logger.error(f"Invalid export parameters: {e}", extra={"request_id": request_id})
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Sample collection failed for export: {e}", extra={"request_id": request_id})
            raise HTTPException(
                status_code=500,
                detail="Failed to collect weather samples for export"
            )
        
        # Create export rows with all sample details
        try:
            export_rows = create_export_rows(sample_collection, settings)
            
            # Validate export data
            validation_result = validate_export_data(export_rows)
            if not validation_result["valid"]:
                logger.error(
                    f"Export data validation failed: {validation_result}", 
                    extra={"request_id": request_id}
                )
                raise HTTPException(
                    status_code=500,
                    detail="Export data validation failed"
                )
            
            # Generate export content based on format
            if export_request.format == "csv":
                content = export_to_csv(export_rows)
                content_type = get_content_type("csv")
            elif export_request.format == "json":
                content = export_to_json(export_rows)
                content_type = get_content_type("json")
            else:
                raise HTTPException(status_code=400, detail="Invalid export format")
            
            # Generate filename for download
            filename = generate_export_filename(
                export_request.latitude,
                export_request.longitude,
                export_request.target_date,
                export_request.target_hour,
                export_request.format
            )
            
            logger.info(
                f"Export completed: {len(export_rows)} samples exported as {export_request.format}",
                extra={"request_id": request_id}
            )
            
            # Return file as download
            return StreamingResponse(
                iter([content.encode()]),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            logger.error(f"Export processing failed: {e}", extra={"request_id": request_id})
            raise HTTPException(
                status_code=500,
                detail="Failed to process export data"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.error(f"Unexpected error in data export: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="Internal server error during data export"
        )


def run_dev_server():
    """Entry point for development server using uv."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )