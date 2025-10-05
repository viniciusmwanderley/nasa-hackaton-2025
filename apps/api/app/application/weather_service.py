# ABOUTME: Main weather analysis service implementing business logic
# ABOUTME: Orchestrates data fetching, processing, and analysis for weather risk assessment

import logging
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Dict, List, Optional, Any
from ..domain.entities import (
    WeatherAnalysisRequest, WeatherAnalysisResult, WeatherData, WeatherParameter,
    WeatherAnalysisMeta
)
from ..domain.enums import Granularity, AnalysisMode
from ..domain.interfaces import IWeatherDataRepository, IWeatherAnalysisService
from ..infrastructure.config import (
    DEFAULT_PARAMS, CLIMATOLOGY_PARAMS, HOURLY_UNAVAILABLE_PARAMS
)
from .weather_utils import (
    calculate_historical_stats, predict_with_temporal_regression, calculate_heat_index
)
from .classification_service import WeatherClassificationService


logger = logging.getLogger("outdoor_risk_api.weather_service")


class WeatherAnalysisService(IWeatherAnalysisService):
    """Main service for weather analysis operations."""
    
    def __init__(self, weather_repo: IWeatherDataRepository):
        self.weather_repo = weather_repo
        self.classification_service = WeatherClassificationService()
    
    async def analyze_weather_range(
        self,
        request: WeatherAnalysisRequest
    ) -> WeatherAnalysisResult:
        """
        Perform comprehensive weather analysis for a date range.
        
        Args:
            request: Weather analysis request parameters
            
        Returns:
            Complete weather analysis result
            
        Raises:
            ValueError: For invalid timezone or other input validation errors
        """
        # Validate timezone
        try:
            target_tz = ZoneInfo(request.target_timezone)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: '{request.target_timezone}'")
        
        # Convert center datetime to UTC
        center_dt_utc = request.center_datetime.astimezone(timezone.utc)
        
        logger.info(
            "Starting weather analysis",
            extra={
                "lat": request.latitude,
                "lon": request.longitude,
                "center_datetime": center_dt_utc.isoformat(),
                "granularity": request.granularity.value
            }
        )
        
        # Prepare parameters
        parameters = request.parameters or DEFAULT_PARAMS
        essential_params = {"T2M", "RH2M", "T2M_MAX", "WS10M", "PRECTOTCORR", "IMERG_PRECTOT", "FRSNO"}
        params_to_fetch = list(set(parameters) | essential_params)
        
        # Remove hourly unavailable parameters if needed
        if request.granularity == Granularity.HOURLY:
            params_to_fetch = [p for p in params_to_fetch if p not in HOURLY_UNAVAILABLE_PARAMS]
        
        # Fetch climatology data
        clim_json = await self.weather_repo.fetch_climatology(
            request.latitude, request.longitude, CLIMATOLOGY_PARAMS
        )
        clim_map = self.weather_repo.extract_climatology_monthly(clim_json)
        
        # Fetch historical data
        all_series = await self._fetch_historical_data(
            request, params_to_fetch
        )
        
        # Calculate historical statistics
        historical_stats = calculate_historical_stats(all_series)
        
        # Generate analysis for date range
        analysis_results = await self._analyze_date_range(
            request, center_dt_utc, target_tz, params_to_fetch, all_series, clim_map
        )
        
        # Calculate classifications for center day
        center_day_data = analysis_results[request.days_before]
        center_day_params = center_day_data.parameters
        center_day_classifications = self.classification_service.calculate_classifications(
            center_dt_utc, center_day_params, all_series, request.granularity
        )
        
        # Build metadata
        end_date_available = datetime.now(timezone.utc).date()
        start_date_fetch = date(request.start_year, 1, 1)
        
        meta = WeatherAnalysisMeta(
            latitude=request.latitude,
            longitude=request.longitude,
            center_datetime_utc=center_dt_utc.isoformat(),
            center_datetime_local=request.center_datetime.isoformat(),
            target_timezone=request.target_timezone,
            granularity=request.granularity.value,
            historical_data_range=[start_date_fetch.isoformat(), end_date_available.isoformat()]
        )
        
        logger.info(
            "Weather analysis completed",
            extra={
                "analysis_days": len(analysis_results),
                "parameters_analyzed": len(params_to_fetch)
            }
        )
        
        return WeatherAnalysisResult(
            meta=meta,
            stats=historical_stats,
            classifications=center_day_classifications,
            results=analysis_results
        )
    
    async def _fetch_historical_data(
        self,
        request: WeatherAnalysisRequest,
        params_to_fetch: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Fetch historical weather data based on granularity."""
        end_date_available = datetime.now(timezone.utc).date()
        start_date_fetch = date(request.start_year, 1, 1)
        
        all_series: Dict[str, Dict[str, float]] = {p: {} for p in params_to_fetch}
        
        if request.granularity == Granularity.DAILY:
            try:
                historical_json = await self.weather_repo.fetch_temporal_data(
                    request.latitude, request.longitude, request.granularity,
                    start_date_fetch, end_date_available, params_to_fetch
                )
                all_series = self.weather_repo.extract_param_series(historical_json)
                
            except Exception as e:
                logger.warning(f"Failed to fetch daily historical data: {e}")
                
        else:  # Hourly data - fetch in chunks
            for year in range(start_date_fetch.year, end_date_available.year + 1, request.hourly_chunk_years):
                chunk_start_dt = date(year, 1, 1)
                chunk_end_dt = date(
                    min(year + request.hourly_chunk_years - 1, end_date_available.year), 12, 31
                )
                
                if chunk_end_dt > end_date_available:
                    chunk_end_dt = end_date_available
                
                try:
                    hourly_json = await self.weather_repo.fetch_temporal_data(
                        request.latitude, request.longitude, request.granularity,
                        chunk_start_dt, chunk_end_dt, params_to_fetch
                    )
                    chunk_series = self.weather_repo.extract_param_series(hourly_json)
                    
                    for param, values in chunk_series.items():
                        if param in all_series:
                            all_series[param].update(values)
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch hourly chunk {year}: {e}")
                    continue
        
        return all_series
    
    async def _analyze_date_range(
        self,
        request: WeatherAnalysisRequest,
        center_dt_utc: datetime,
        target_tz: ZoneInfo,
        params_to_fetch: List[str],
        all_series: Dict[str, Dict[str, float]],
        clim_map: Dict[str, Dict[int, float]]
    ) -> List[WeatherData]:
        """Analyze weather data for each day in the requested range."""
        analysis_results = []
        
        datetimes_to_analyze_utc = [
            center_dt_utc + timedelta(days=i) 
            for i in range(-request.days_before, request.days_after + 1)
        ]
        
        for target_dt_utc in datetimes_to_analyze_utc:
            date_format_api = "%Y%m%d" if request.granularity == Granularity.DAILY else "%Y%m%d%H"
            target_date_str_api = target_dt_utc.strftime(date_format_api)
            is_in_past = target_dt_utc <= datetime.now(timezone.utc)
            
            results_for_moment = {}
            
            # Process each parameter
            for param in params_to_fetch:
                series = all_series.get(param, {})
                climatology_mean = clim_map.get(param, {}).get(target_dt_utc.month)
                
                if is_in_past:
                    observed_value = series.get(target_date_str_api)
                    if observed_value is not None:
                        # Use observed value
                        param_data = WeatherParameter(
                            value=observed_value,
                            mode=AnalysisMode.OBSERVED,
                            climatology_month_mean=climatology_mean
                        )
                    else:
                        # Use prediction
                        predicted_value = predict_with_temporal_regression(
                            series, target_dt_utc, request.granularity, request.window_days
                        )
                        param_data = WeatherParameter(
                            value=predicted_value,
                            mode=AnalysisMode.PROBABILISTIC,
                            climatology_month_mean=climatology_mean,
                            model_used="TemporalLinearRegressionByNullObserved"
                        )
                else:
                    # Future prediction
                    predicted_value = predict_with_temporal_regression(
                        series, target_dt_utc, request.granularity, request.window_days
                    )
                    param_data = WeatherParameter(
                        value=predicted_value,
                        mode=AnalysisMode.PROBABILISTIC,
                        climatology_month_mean=climatology_mean,
                        model_used="TemporalLinearRegression"
                    )
                
                results_for_moment[param] = param_data
            
            # Calculate derived insights
            t2m_val = results_for_moment.get('T2M')
            rh2m_val = results_for_moment.get('RH2M')
            
            heat_index_val = None
            if t2m_val and rh2m_val and t2m_val.value is not None and rh2m_val.value is not None:
                heat_index_val = calculate_heat_index(t2m_val.value, rh2m_val.value)
            
            # Convert to local timezone
            target_dt_local = target_dt_utc.astimezone(target_tz)
            
            analysis_results.append(WeatherData(
                datetime=target_dt_local.isoformat(),
                parameters=results_for_moment,
                derived_insights={'heat_index_c': heat_index_val}
            ))
        
        return analysis_results