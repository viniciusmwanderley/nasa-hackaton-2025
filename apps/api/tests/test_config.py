# ABOUTME: Unit tests for configuration module and environment variable handling
# ABOUTME: Validates config parsing, defaults, CORS origins, and rate limit settings

import os
from unittest.mock import patch

from app.config import Settings


class TestSettings:
    """Test suite for the Settings configuration class."""

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            config = Settings()

            # Test default thresholds
            assert config.thresholds_hi_hot_c == 41.0
            assert config.thresholds_hi_uncomf_c == 32.0
            assert config.thresholds_wct_cold_c == -10.0
            assert config.thresholds_wind_ms == 10.8
            assert config.thresholds_rain_mm_per_h == 4.0

            # Test default CORS origins
            assert "http://localhost:5173" in config.cors_origins_list
            assert "http://localhost:4173" in config.cors_origins_list

            # Test default rate limits
            assert config.rate_limit_general == "30/minute;burst=10"
            assert config.rate_limit_export == "6/minute;burst=6"

            # Test default baseline and window
            assert config.default_baseline_start == 2001
            assert config.default_window_days == 7
            assert config.default_hour_local == "10:00"

    def test_environment_variable_overrides(self):
        """Test that environment variables override defaults."""
        test_env = {
            "THRESHOLDS_HI_HOT_C": "45.0",
            "THRESHOLDS_WIND_MS": "12.0",
            "ALLOWED_ORIGINS": "http://example.com,https://myapp.com",
            "RATE_LIMIT_GENERAL": "60/minute;burst=20",
            "DEFAULT_BASELINE_START": "2005",
        }

        with patch.dict(os.environ, test_env, clear=True):
            config = Settings()

            assert config.thresholds_hi_hot_c == 45.0
            assert config.thresholds_wind_ms == 12.0
            assert config.cors_origins_list == [
                "http://example.com",
                "https://myapp.com",
            ]
            assert config.rate_limit_general == "60/minute;burst=20"
            assert config.default_baseline_start == 2005

    def test_cors_origins_parsing(self):
        """Test CORS origins string parsing into list."""
        test_env = {
            "ALLOWED_ORIGINS": "http://localhost:3000, https://app.com,http://dev.local "
        }

        with patch.dict(os.environ, test_env, clear=True):
            config = Settings()

            expected = ["http://localhost:3000", "https://app.com", "http://dev.local"]
            assert config.cors_origins_list == expected

    def test_single_cors_origin(self):
        """Test single CORS origin configuration."""
        test_env = {"ALLOWED_ORIGINS": "https://production.com"}

        with patch.dict(os.environ, test_env, clear=True):
            config = Settings()

            assert config.cors_origins_list == ["https://production.com"]

    def test_timeout_settings(self):
        """Test timeout configuration settings."""
        test_env = {"TIMEOUT_CONNECT_S": "15", "TIMEOUT_READ_S": "45", "RETRIES": "5"}

        with patch.dict(os.environ, test_env, clear=True):
            config = Settings()

            assert config.timeout_connect_s == 15
            assert config.timeout_read_s == 45
            assert config.retries == 5
