# ABOUTME: Unit tests for timezone utilities and date/time handling
# ABOUTME: Validates lat/lon to IANA timezone resolution and local hour operations

import pytest
from datetime import datetime, date
from zoneinfo import ZoneInfo
from app.time.timezone import (
    tz_for_point,
    to_local,
    local_hour_matches,
    parse_date,
    doy,
    parse_hour,
    get_day_of_year,
    build_date_range_for_doy
)


class TestTimezoneResolution:
    """Test suite for timezone resolution functionality."""
    
    def test_tz_for_point_fortaleza(self):
        """Test timezone resolution for Fortaleza, Brazil (no DST)."""
        # Fortaleza coordinates
        lat, lon = -3.7319, -38.5267
        timezone = tz_for_point(lat, lon)
        
        # Fortaleza is in the same timezone as São Paulo
        assert timezone == "America/Sao_Paulo"
    
    def test_tz_for_point_new_york(self):
        """Test timezone resolution for New York (has DST)."""
        # New York coordinates
        lat, lon = 40.7128, -74.0060
        timezone = tz_for_point(lat, lon)
        
        assert timezone == "America/New_York"
    
    def test_tz_for_point_london(self):
        """Test timezone resolution for London (has DST)."""
        # London coordinates  
        lat, lon = 51.5074, -0.1278
        timezone = tz_for_point(lat, lon)
        
        assert timezone == "Europe/London"
    
    def test_tz_for_point_caching(self):
        """Test that timezone resolution results are cached."""
        lat, lon = -3.7319, -38.5267
        
        # First call
        tz1 = tz_for_point(lat, lon)
        # Second call should use cache
        tz2 = tz_for_point(lat, lon)
        
        assert tz1 == tz2 == "America/Sao_Paulo"


class TestLocalTimeConversion:
    """Test suite for local time conversion functionality."""
    
    def test_to_local_utc_to_fortaleza(self):
        """Test UTC to Fortaleza local time conversion."""
        # UTC datetime
        dt_utc = datetime(2025, 7, 15, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        
        # Convert to São Paulo time (UTC-3)
        dt_local = to_local(dt_utc, "America/Sao_Paulo")
        
        assert dt_local.hour == 11  # 14 - 3 = 11
        assert dt_local.tzinfo == ZoneInfo("America/Sao_Paulo")
    
    def test_to_local_utc_to_new_york_summer(self):
        """Test UTC to New York time conversion during DST."""
        # UTC datetime in summer (EDT = UTC-4)
        dt_utc = datetime(2025, 7, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        
        # Convert to New York time
        dt_local = to_local(dt_utc, "America/New_York")
        
        assert dt_local.hour == 14  # 18 - 4 = 14 (EDT)
        assert dt_local.tzinfo == ZoneInfo("America/New_York")
    
    def test_to_local_utc_to_new_york_winter(self):
        """Test UTC to New York time conversion during standard time."""
        # UTC datetime in winter (EST = UTC-5)
        dt_utc = datetime(2025, 1, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        
        # Convert to New York time
        dt_local = to_local(dt_utc, "America/New_York")
        
        assert dt_local.hour == 13  # 18 - 5 = 13 (EST)
        assert dt_local.tzinfo == ZoneInfo("America/New_York")


class TestLocalHourMatching:
    """Test suite for local hour matching functionality."""
    
    def test_local_hour_matches_true(self):
        """Test local hour matching returns true for correct hour."""
        # UTC datetime that is 10:00 in São Paulo (UTC-3)
        dt_utc = datetime(2025, 7, 15, 13, 0, 0, tzinfo=ZoneInfo("UTC"))
        
        matches = local_hour_matches(dt_utc, "America/Sao_Paulo", 10)
        assert matches is True
    
    def test_local_hour_matches_false(self):
        """Test local hour matching returns false for incorrect hour.""" 
        # UTC datetime that is 11:00 in São Paulo
        dt_utc = datetime(2025, 7, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
        
        matches = local_hour_matches(dt_utc, "America/Sao_Paulo", 10)
        assert matches is False
    
    def test_local_hour_matches_dst_transition(self):
        """Test local hour matching during DST transition."""
        # UTC datetime that is 10:00 in New York during EDT
        dt_utc = datetime(2025, 7, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
        
        matches = local_hour_matches(dt_utc, "America/New_York", 10)
        assert matches is True


class TestDateParsing:
    """Test suite for date and time parsing utilities."""
    
    def test_parse_date_valid(self):
        """Test parsing valid date strings."""
        parsed = parse_date("2025-10-15")
        expected = date(2025, 10, 15)
        
        assert parsed == expected
    
    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format raises error."""
        with pytest.raises(ValueError):
            parse_date("2025/10/15")  # Wrong format
    
    def test_parse_date_invalid_date(self):
        """Test parsing invalid date raises error."""
        with pytest.raises(ValueError):
            parse_date("2025-02-30")  # Invalid date
    
    def test_doy_calculation(self):
        """Test day-of-year calculation."""
        # January 1st
        assert doy(date(2025, 1, 1)) == 1
        
        # December 31st (non-leap year)
        assert doy(date(2025, 12, 31)) == 365
        
        # March 1st
        assert doy(date(2025, 3, 1)) == 60  # 31 (Jan) + 28 (Feb) + 1 = 60
        
        # Leap year test (2024)
        assert doy(date(2024, 3, 1)) == 61  # 31 + 29 + 1 = 61
    
    def test_parse_hour_valid(self):
        """Test parsing valid hour strings."""
        assert parse_hour("10:00") == 10
        assert parse_hour("00:00") == 0
        assert parse_hour("23:00") == 23
    
    def test_parse_hour_invalid_format(self):
        """Test parsing invalid hour format raises error."""
        with pytest.raises(ValueError):
            parse_hour("10")  # Missing :00
            
        with pytest.raises(ValueError):
            parse_hour("10:30")  # Minutes not 00
    
    def test_parse_hour_invalid_hour(self):
        """Test parsing invalid hour values raises error."""
        with pytest.raises(ValueError):
            parse_hour("24:00")  # Invalid hour
            
        with pytest.raises(ValueError):
            parse_hour("-1:00")  # Negative hour


class TestDayOfYearUtilities:
    """Test suite for day-of-year range utilities."""
    
    def test_get_day_of_year_from_date_string(self):
        """Test getting DOY from date string."""
        doy_result = get_day_of_year("2025-10-15")
        expected = doy(date(2025, 10, 15))
        
        assert doy_result == expected
    
    def test_build_date_range_for_doy_simple(self):
        """Test building date range for DOY with simple case."""
        # DOY 100, window ±3 days
        target_doy = 100
        window_days = 3
        
        date_range = build_date_range_for_doy(target_doy, window_days)
        
        assert len(date_range) == 7  # ±3 = 7 days total
        assert min(date_range) == 97  # 100 - 3
        assert max(date_range) == 103  # 100 + 3
    
    def test_build_date_range_for_doy_year_boundary(self):
        """Test building date range for DOY at year boundaries."""
        # DOY 3, window ±5 days (should wrap around year boundary)
        target_doy = 3
        window_days = 5
        
        date_range = build_date_range_for_doy(target_doy, window_days)
        
        # DOY 3 ± 5 = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
        # Wrapping: -2→363, -1→364, 0→365, then 1,2,3,4,5,6,7,8
        expected_low = list(range(1, 9))  # 1-8
        expected_high = [363, 364, 365]  # Wrapped negative values
        expected = expected_high + expected_low  # Wrapped range
        
        assert sorted(date_range) == sorted(expected)