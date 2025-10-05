# ABOUTME: Climate energy analysis service implementation with NASA API integration  
# ABOUTME: Orchestrates climate data fetching and energy potential calculations

import time
from typing import List, Dict, Any
from ..domain.climate_interfaces import IClimateEnergyService, INASAClimateRepository
from ..domain.climate_entities import (
    ClimateEnergyAnalysisRequest,
    ClimateEnergyAnalysisResult,
    LocationResult,
    LocationError,
    AnalysisMeta,
    ClimateEnergyPotential,
    LocationInput
)


class ClimateEnergyService(IClimateEnergyService):    
    # API Parameter Mapping
    API_PARAMETERS_MAP: Dict[str, str] = {
        "SolarIrradianceOptimal": "SI_TILTED_AVG_OPTIMAL",
        "SolarIrradianceOptimalAngle": "SI_TILTED_AVG_OPTIMAL_ANG",
        "SurfaceAirDensity": "RHOA",
        "WindSpeed50m": "WS50M",
        "WindDirection50m": "WD50M"
    }
    
    # Technological Parameters
    SOLAR_LOSS_FACTOR: float = 0.80  # System losses (inverter, cables, dirt)
    TURBINE_SWEPT_AREA_M2: float = 14314.0  # Reference turbine swept area (m²)
    TURBINE_CP: float = 0.45  # Reference turbine power coefficient
    
    # Calculation Constants
    MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    DAYS_IN_MONTH: Dict[str, int] = dict(zip(MONTHS, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]))
    
    def __init__(self, nasa_repository: INASAClimateRepository):
        self.nasa_repository = nasa_repository
    
    async def analyze_climate_energy_potential(
        self,
        request: ClimateEnergyAnalysisRequest
    ) -> ClimateEnergyAnalysisResult:
        """        
        Args:
            request: Climate energy analysis request
            
        Returns:
            Complete analysis results with metadata and errors
        """
        start_time = time.perf_counter()
        analysis_results = []
        failed_locations = []
        param_list = list(self.API_PARAMETERS_MAP.values())

        for location_input in request.locations:
            try:
                api_data = await self.nasa_repository.fetch_climatology_data(
                    location_input.latitude, 
                    location_input.longitude, 
                    param_list
                )
                
                if not api_data:
                    raise ValueError("Empty API response")
                
                solar_kwh_per_m2 = self._calculate_solar_kwh_per_m2(api_data)
                wind_kwh_per_m2 = self._calculate_wind_kwh_per_m2(api_data)
                
                raw_metrics = {
                    key: api_data.get(value, {}) 
                    for key, value in self.API_PARAMETERS_MAP.items()
                }
                
                analysis_results.append(LocationResult(
                    location=location_input,
                    climate_energy_potential=ClimateEnergyPotential(
                        solar_kwh_per_m2=solar_kwh_per_m2,
                        wind_kwh_per_m2=wind_kwh_per_m2
                    ),
                    raw_nasa_metrics_monthly=raw_metrics
                ))
                
            except Exception as e:
                failed_locations.append(LocationError(
                    location=location_input,
                    error=str(e)
                ))

        duration = time.perf_counter() - start_time
        
        return ClimateEnergyAnalysisResult(
            meta=AnalysisMeta(
                timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                processing_time_seconds=round(duration, 2),
                locations_processed=len(analysis_results),
                locations_failed=len(failed_locations)
            ),
            data=analysis_results,
            errors=failed_locations
        )
    
    def _calculate_solar_kwh_per_m2(self, api_data: Dict[str, Any]) -> Dict[str, float]:
        """        
        Args:
            api_data: Dictionary containing NASA API response data
            
        Returns:
            Dictionary with monthly and annual kWh/m² values
        """
        insolation_data = api_data.get(self.API_PARAMETERS_MAP["SolarIrradianceOptimal"], {})
        results = {}
        
        for month in self.MONTHS:
            daily_insolation = insolation_data.get(month)
            if daily_insolation is None or daily_insolation == -999:
                continue

            days = self.DAYS_IN_MONTH[month]
            monthly_kwh_per_m2 = daily_insolation * self.SOLAR_LOSS_FACTOR * days
            results[month] = round(monthly_kwh_per_m2, 2)

        if results:
            results["ANN"] = round(sum(results.values()), 2)

        return results
    
    def _calculate_wind_kwh_per_m2(self, api_data: Dict[str, Any]) -> Dict[str, float]:
        """        
        Args:
            api_data: Dictionary containing NASA API response data
            
        Returns:
            Dictionary with monthly and annual kWh/m² values
        """
        air_density_data = api_data.get(self.API_PARAMETERS_MAP["SurfaceAirDensity"], {})
        wind_speed_data = api_data.get(self.API_PARAMETERS_MAP["WindSpeed50m"], {})
        results = {}
        
        for month in self.MONTHS:
            air_density = air_density_data.get(month)
            wind_speed = wind_speed_data.get(month)
            if any(v is None or v == -999 for v in [air_density, wind_speed]):
                continue

            hours = self.DAYS_IN_MONTH[month] * 24
            avg_power_watts = 0.5 * air_density * self.TURBINE_SWEPT_AREA_M2 * (wind_speed ** 3) * self.TURBINE_CP
            total_monthly_energy_kwh = (avg_power_watts * hours) / 1000
            
            monthly_kwh_per_m2 = total_monthly_energy_kwh / self.TURBINE_SWEPT_AREA_M2
            results[month] = round(monthly_kwh_per_m2, 2)

        if results:
            results["ANN"] = round(sum(results.values()), 2)

        return results
    
    async def analyze_single_location(
        self, 
        latitude: float, 
        longitude: float
    ) -> LocationResult:
        """        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Single location analysis result
            
        Raises:
            Exception: If analysis fails for the location
        """
        param_list = list(self.API_PARAMETERS_MAP.values())
        
        api_data = await self.nasa_repository.fetch_climatology_data(
            latitude, longitude, param_list
        )
        
        if not api_data:
            raise ValueError("Empty API response")
        
        solar_kwh_per_m2 = self._calculate_solar_kwh_per_m2(api_data)
        wind_kwh_per_m2 = self._calculate_wind_kwh_per_m2(api_data)
        
        raw_metrics = {
            key: api_data.get(value, {}) 
            for key, value in self.API_PARAMETERS_MAP.items()
        }
        
        location_input = LocationInput(latitude=latitude, longitude=longitude)
        
        return LocationResult(
            location=location_input,
            climate_energy_potential=ClimateEnergyPotential(
                solar_kwh_per_m2=solar_kwh_per_m2,
                wind_kwh_per_m2=wind_kwh_per_m2
            ),
            raw_nasa_metrics_monthly=raw_metrics
        )