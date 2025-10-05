# ABOUTME: Example usage and testing script for the Weather Risk Assessment API
# ABOUTME: Demonstrates various API features and provides sample requests

import asyncio
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app.domain.entities import WeatherAnalysisRequest
from app.domain.enums import Granularity
from app.presentation.dependencies import get_container


async def example_daily_analysis():
    """Example of daily weather analysis for Recife, Brazil."""
    print("=== Daily Weather Analysis Example ===")
    
    # Get service instance
    container = get_container()
    weather_service = container.weather_service
    
    # Create request for Recife, Brazil
    target_tz = ZoneInfo("America/Recife")
    center_datetime = datetime(2024, 7, 15, 14, 0, 0, tzinfo=target_tz)
    
    request = WeatherAnalysisRequest(
        latitude=-8.0476,  # Recife coordinates
        longitude=-34.8770,
        center_datetime=center_datetime,
        target_timezone="America/Recife",
        days_before=3,
        days_after=3,
        granularity=Granularity.DAILY,
        start_year=2000,
        window_days=10
    )
    
    try:
        result = await weather_service.analyze_weather_range(request)
        
        print(f"Analysis completed for coordinates: {result.meta.latitude}, {result.meta.longitude}")
        print(f"Historical data range: {result.meta.historical_data_range[0]} to {result.meta.historical_data_range[1]}")
        print(f"Total analysis days: {len(result.results)}")
        
        # Show center day analysis
        center_day = result.results[request.days_before]
        print(f"\n--- Center Day Analysis ({center_day.datetime}) ---")
        
        # Temperature analysis
        if 'T2M' in center_day.parameters:
            t2m = center_day.parameters['T2M']
            print(f"Temperature: {t2m.value:.1f}°C ({t2m.mode.value})")
            if t2m.climatology_month_mean:
                print(f"  Climatology average: {t2m.climatology_month_mean:.1f}°C")
        
        # Heat index
        if center_day.derived_insights.get('heat_index_c'):
            print(f"Heat Index: {center_day.derived_insights['heat_index_c']:.1f}°C")
        
        # Classifications
        print(f"\n--- Risk Classifications ---")
        if result.classifications.rain_probability is not None:
            print(f"Rain Probability: {result.classifications.rain_probability:.1%}")
        if result.classifications.very_hot_temp_percentile is not None:
            print(f"Hot Temperature Percentile: {result.classifications.very_hot_temp_percentile:.1f}%")
        if result.classifications.very_windy_percentile is not None:
            print(f"Wind Percentile: {result.classifications.very_windy_percentile:.1f}%")
        if result.classifications.very_wet_probability is not None:
            print(f"Stormy Weather Probability: {result.classifications.very_wet_probability:.1%}")
        
        return result
        
    except Exception as e:
        print(f"Error in daily analysis: {e}")
        return None


async def example_hourly_analysis():
    """Example of hourly weather analysis for São Paulo, Brazil."""
    print("\n=== Hourly Weather Analysis Example ===")
    
    container = get_container()
    weather_service = container.weather_service
    
    # Create request for São Paulo
    target_tz = ZoneInfo("America/Sao_Paulo")
    center_datetime = datetime(2024, 1, 10, 14, 0, 0, tzinfo=target_tz)
    
    request = WeatherAnalysisRequest(
        latitude=-23.5505,  # São Paulo coordinates
        longitude=-46.6333,
        center_datetime=center_datetime,
        target_timezone="America/Sao_Paulo",
        days_before=1,
        days_after=1,
        granularity=Granularity.HOURLY,
        start_year=2010,
        window_days=7,
        hourly_chunk_years=3
    )
    
    try:
        result = await weather_service.analyze_weather_range(request)
        
        print(f"Hourly analysis completed for São Paulo")
        print(f"Total analysis periods: {len(result.results)}")
        
        # Show each hourly prediction
        for i, hourly_data in enumerate(result.results):
            print(f"\n--- Hour {i+1}: {hourly_data.datetime} ---")
            
            if 'T2M' in hourly_data.parameters:
                temp = hourly_data.parameters['T2M'].value
                if temp is not None:
                    print(f"Temperature: {temp:.1f}°C")
            
            if 'PRECTOTCORR' in hourly_data.parameters:
                precip = hourly_data.parameters['PRECTOTCORR'].value
                if precip is not None:
                    print(f"Precipitation: {precip:.2f}mm/hr")
        
        return result
        
    except Exception as e:
        print(f"Error in hourly analysis: {e}")
        return None


async def example_statistics_analysis():
    """Example showing historical statistics analysis."""
    print("\n=== Historical Statistics Example ===")
    
    container = get_container()
    weather_service = container.weather_service
    
    target_tz = ZoneInfo("UTC")
    center_datetime = datetime(2023, 12, 25, 12, 0, 0, tzinfo=target_tz)
    
    request = WeatherAnalysisRequest(
        latitude=0.0,  # Equator
        longitude=0.0,
        center_datetime=center_datetime,
        target_timezone="UTC",
        days_before=0,
        days_after=0,
        granularity=Granularity.DAILY,
        start_year=1990
    )
    
    try:
        result = await weather_service.analyze_weather_range(request)
        
        print("Historical Statistics (1990-present):")
        print("-" * 50)
        
        for param, stats in result.stats.items():
            if stats is not None:
                print(f"\n{param}:")
                print(f"  Count: {stats.count}")
                print(f"  Mean: {stats.mean:.2f}")
                print(f"  Std Dev: {stats.std:.2f}")
                print(f"  Min: {stats.min:.2f}")
                print(f"  Max: {stats.max:.2f}")
        
        return result
        
    except Exception as e:
        print(f"Error in statistics analysis: {e}")
        return None


def save_example_results(result, filename):
    """Save analysis results to JSON file."""
    if result:
        try:
            # Convert to dict for JSON serialization
            result_dict = result.model_dump()
            
            with open(filename, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            print(f"Results saved to {filename}")
            
        except Exception as e:
            print(f"Error saving results: {e}")


async def main():
    """Run all examples."""
    print("Weather Risk Assessment API - Examples")
    print("=" * 50)
    
    # Daily analysis example
    daily_result = await example_daily_analysis()
    if daily_result:
        save_example_results(daily_result, "daily_analysis_example.json")
    
    # Hourly analysis example  
    hourly_result = await example_hourly_analysis()
    if hourly_result:
        save_example_results(hourly_result, "hourly_analysis_example.json")
    
    # Statistics example
    stats_result = await example_statistics_analysis()
    if stats_result:
        save_example_results(stats_result, "statistics_example.json")
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())