# ABOUTME: Data export functionality for weather samples
# ABOUTME: Provides CSV and JSON export formats with full sample details and provenance

import csv
import json
import io
from typing import List, Dict, Any
from datetime import datetime
from app.models import ExportSampleRow
from app.engine.samples import WeatherSample, SampleCollection
from app.weather.calculations import heat_index, wind_chill
from app.config import Settings


def create_export_rows(
    sample_collection: SampleCollection,
    settings: Settings
) -> List[ExportSampleRow]:
    """
    Convert weather samples to export rows with all required fields.
    
    Args:
        sample_collection: Collection of weather samples
        settings: Configuration settings for thresholds
        
    Returns:
        List of export rows with calculated fields and flags
    """
    export_rows = []
    
    for sample in sample_collection.samples:
        # Calculate derived metrics
        hi_c = heat_index(sample.temperature_c, sample.relative_humidity)
        wct_c = wind_chill(sample.temperature_c, sample.wind_speed_ms)
        
        # Convert precipitation from daily to hourly average
        # Note: This is an approximation - IMERG hourly data would be more accurate
        precip_mm_per_h = sample.precipitation_mm_per_day / 24.0
        
        # Use IMERG hourly data if available
        if hasattr(sample, 'precipitation_mm_hourly') and sample.precipitation_mm_hourly is not None:
            precip_mm_per_h = sample.precipitation_mm_hourly
            
        precip_source = getattr(sample, 'precipitation_source', 'POWER')
        
        # Calculate condition flags directly
        # Very hot: use heat index if available, otherwise temperature
        very_hot = False
        if hi_c is not None:
            very_hot = hi_c >= settings.thresholds_hi_hot_c
        else:
            very_hot = sample.temperature_c >= settings.thresholds_hi_hot_c
            
        # Very cold: use wind chill if available, otherwise temperature
        very_cold = False
        if wct_c is not None:
            very_cold = wct_c <= settings.thresholds_wct_cold_c
        else:
            very_cold = sample.temperature_c <= settings.thresholds_wct_cold_c
            
        # Very windy
        very_windy = sample.wind_speed_ms >= settings.thresholds_wind_ms
        
        # Very wet: convert to hourly rate
        very_wet = precip_mm_per_h >= settings.thresholds_rain_mm_per_h
        
        # Any adverse condition
        any_adverse = very_hot or very_cold or very_windy or very_wet
        
        # Create export row
        row = ExportSampleRow(
            timestamp_local=sample.timestamp_local.isoformat(),
            year=sample.year,
            doy=sample.doy,
            lat=sample.latitude,
            lon=sample.longitude,
            t2m_c=sample.temperature_c,
            rh2m_pct=sample.relative_humidity,
            ws10m_ms=sample.wind_speed_ms,
            hi_c=hi_c,
            wct_c=wct_c,
            precip_mm_per_h=precip_mm_per_h,
            precip_source=precip_source,
            flags_very_hot=very_hot,
            flags_very_cold=very_cold,
            flags_very_windy=very_windy,
            flags_very_wet=very_wet,
            flags_any_adverse=any_adverse
        )
        
        export_rows.append(row)
    
    return export_rows


def export_to_csv(export_rows: List[ExportSampleRow]) -> str:
    """
    Export data rows to CSV format.
    
    Args:
        export_rows: List of export sample rows
        
    Returns:
        CSV content as string
    """
    if not export_rows:
        # Return headers only for empty data
        return "timestamp_local,year,doy,lat,lon,t2m_c,rh2m_pct,ws10m_ms,hi_c,wct_c,precip_mm_per_h,precip_source,flags_very_hot,flags_very_cold,flags_very_windy,flags_very_wet,flags_any_adverse\\n"
    
    # Use StringIO to build CSV in memory
    output = io.StringIO()
    
    # Get field names from the first row
    fieldnames = list(export_rows[0].model_dump().keys())
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write data rows
    for row in export_rows:
        # Convert Pydantic model to dict for CSV writer
        row_dict = row.model_dump()
        
        # Handle None values in optional fields
        for key, value in row_dict.items():
            if value is None:
                row_dict[key] = ""
        
        writer.writerow(row_dict)
    
    csv_content = output.getvalue()
    output.close()
    
    return csv_content


def export_to_json(export_rows: List[ExportSampleRow]) -> str:
    """
    Export data rows to JSON format.
    
    Args:
        export_rows: List of export sample rows
        
    Returns:
        JSON content as string
    """
    # Convert Pydantic models to dictionaries
    data = [row.model_dump() for row in export_rows]
    
    # Pretty print JSON for better readability
    return json.dumps(data, indent=2, default=str)


def generate_export_filename(
    latitude: float,
    longitude: float, 
    target_date: str,
    target_hour: int,
    format: str
) -> str:
    """
    Generate appropriate filename for export download.
    
    Args:
        latitude: Target latitude
        longitude: Target longitude  
        target_date: Target date string (YYYY-MM-DD)
        target_hour: Target hour
        format: Export format ('csv' or 'json')
        
    Returns:
        Filename for Content-Disposition header
    """
    # Create timestamp for filename uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Clean coordinates for filename (remove decimals and signs)
    lat_str = f"{abs(latitude):.1f}{'N' if latitude >= 0 else 'S'}"
    lon_str = f"{abs(longitude):.1f}{'E' if longitude >= 0 else 'W'}"
    
    # Clean date string (remove hyphens)
    date_str = target_date.replace("-", "")
    
    # Build filename
    filename = f"outdoor_risk_export_{lat_str}_{lon_str}_{date_str}_{target_hour:02d}h_{timestamp}.{format}"
    
    return filename


def get_content_type(format: str) -> str:
    """
    Get appropriate MIME content type for export format.
    
    Args:
        format: Export format ('csv' or 'json')
        
    Returns:
        MIME content type string
    """
    if format == "csv":
        return "text/csv"
    elif format == "json":
        return "application/json"
    else:
        raise ValueError(f"Unsupported export format: {format}")


def validate_export_data(export_rows: List[ExportSampleRow]) -> Dict[str, Any]:
    """
    Validate export data and return summary statistics.
    
    Args:
        export_rows: List of export sample rows
        
    Returns:
        Dictionary with validation results and summary stats
    """
    if not export_rows:
        return {
            "valid": True,
            "row_count": 0,
            "year_range": None,
            "coordinate_consistency": True,
            "data_sources": []
        }
    
    # Basic validation
    row_count = len(export_rows)
    years = [row.year for row in export_rows]
    year_range = (min(years), max(years))
    
    # Check coordinate consistency (all rows should have same lat/lon)
    first_lat, first_lon = export_rows[0].lat, export_rows[0].lon
    coordinate_consistency = all(
        row.lat == first_lat and row.lon == first_lon 
        for row in export_rows
    )
    
    # Collect unique data sources
    data_sources = list(set(row.precip_source for row in export_rows))
    
    # Check for required fields
    required_fields = ["timestamp_local", "year", "doy", "t2m_c", "rh2m_pct", "ws10m_ms"]
    missing_fields = []
    
    for field in required_fields:
        if any(getattr(row, field) is None for row in export_rows):
            missing_fields.append(field)
    
    return {
        "valid": len(missing_fields) == 0 and coordinate_consistency,
        "row_count": row_count,
        "year_range": year_range,
        "coordinate_consistency": coordinate_consistency,
        "data_sources": data_sources,
        "missing_fields": missing_fields
    }