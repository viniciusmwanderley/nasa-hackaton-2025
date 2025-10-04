# ABOUTME: Tests for distribution analysis functionality
# ABOUTME: Validates histogram computation and parameter distribution calculations

import pytest
import numpy as np
from datetime import datetime
from app.analysis.distributions import (
    calculate_histogram_bins, create_distribution, calculate_distributions
)
from app.weather.thresholds import WeatherSample
from app.config import Settings


class TestHistogramBins:
    """Test histogram bin calculation."""
    
    def test_calculate_histogram_bins_basic(self):
        """Test basic histogram bin calculation."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        bin_edges, counts = calculate_histogram_bins(values, n_bins=5)
        
        assert len(bin_edges) == 6  # n+1 edges for n bins
        assert len(counts) == 5
        assert sum(counts) == 5  # Total count matches input
        assert bin_edges[0] == 1.0
        assert bin_edges[-1] == 5.0
    
    def test_calculate_histogram_bins_with_threshold(self):
        """Test histogram bins with threshold as bin edge."""
        values = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        threshold = 2.5
        
        bin_edges, counts = calculate_histogram_bins(values, n_bins=4, threshold_value=threshold)
        
        assert threshold in bin_edges
        assert len(counts) == len(bin_edges) - 1
    
    def test_calculate_histogram_bins_empty_data(self):
        """Test histogram with empty data."""
        values = np.array([])
        
        bin_edges, counts = calculate_histogram_bins(values)
        
        assert bin_edges == []
        assert counts == []
    
    def test_calculate_histogram_bins_nan_values(self):
        """Test histogram handles NaN values."""
        values = np.array([1.0, np.nan, 2.0, np.nan, 3.0])
        
        bin_edges, counts = calculate_histogram_bins(values, n_bins=3)
        
        assert len(bin_edges) > 0
        assert sum(counts) == 3  # Only non-NaN values counted


class TestCreateDistribution:
    """Test distribution object creation."""
    
    def test_create_distribution_basic(self):
        """Test basic distribution creation."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        dist = create_distribution(
            parameter="temperature", 
            unit="°C", 
            values=values,
            n_bins=3
        )
        
        assert dist.parameter == "temperature"
        assert dist.unit == "°C"
        assert len(dist.bins) == 3
        assert dist.mean == pytest.approx(3.0)
        assert dist.median == pytest.approx(3.0)
        assert dist.std_dev > 0
    
    def test_create_distribution_with_threshold(self):
        """Test distribution with threshold value."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        threshold = 3.5
        
        dist = create_distribution(
            parameter="wind_speed",
            unit="m/s",
            values=values,
            threshold_value=threshold,
            n_bins=4
        )
        
        assert dist.threshold_value == threshold
        assert len(dist.bins) == 4
        
        # Check that frequencies sum to 1.0
        total_frequency = sum(bin.frequency for bin in dist.bins)
        assert total_frequency == pytest.approx(1.0)
    
    def test_create_distribution_empty_data(self):
        """Test distribution creation with empty data."""
        values = np.array([])
        
        dist = create_distribution(
            parameter="precipitation", 
            unit="mm/h", 
            values=values
        )
        
        assert dist.parameter == "precipitation"
        assert dist.bins == []
        assert dist.mean == 0.0
        assert dist.median == 0.0
        assert dist.std_dev == 0.0


class TestCalculateDistributions:
    """Test full distribution calculation for weather samples."""
    
    def test_calculate_distributions_basic(self):
        """Test distribution calculation with basic samples."""
        settings = Settings()
        
        # Create test samples
        samples = []
        for i in range(10):
            sample = WeatherSample(
                temperature_c=20.0 + i,
                relative_humidity=50.0 + i,
                wind_speed_ms=5.0 + i * 0.5,
                precipitation_mm_per_day=2.0 + i * 0.1,
                timestamp=datetime(2020, 1, 1 + i),
                latitude=-3.7,
                longitude=-38.5
            )
            samples.append(sample)
        
        distributions = calculate_distributions(samples, settings)
        
        # Should have distributions for key parameters
        param_names = [d.parameter for d in distributions]
        expected_params = ["temperature", "relative_humidity", "wind_speed", "precipitation", "heat_index"]
        
        for param in expected_params:
            assert param in param_names
        
        # Check that each distribution has proper structure
        for dist in distributions:
            assert len(dist.bins) > 0
            assert dist.mean >= 0
            assert dist.unit is not None
    
    def test_calculate_distributions_extreme_conditions(self):
        """Test distributions with extreme weather conditions."""
        settings = Settings()
        
        # Create extreme samples 
        samples = [
            WeatherSample(
                temperature_c=45.0,  # Very hot
                relative_humidity=80.0,  # High humidity
                wind_speed_ms=15.0,  # Very windy
                precipitation_mm_per_day=100.0,  # Very wet
                timestamp=datetime(2020, 6, 15),
                latitude=-3.7,
                longitude=-38.5
            ),
            WeatherSample(
                temperature_c=-20.0,  # Very cold
                relative_humidity=30.0,  # Low humidity
                wind_speed_ms=20.0,  # Extreme wind
                precipitation_mm_per_day=0.0,  # Dry
                timestamp=datetime(2020, 12, 15),
                latitude=-3.7,
                longitude=-38.5
            )
        ]
        
        distributions = calculate_distributions(samples, settings)
        
        # Should handle extreme values without errors
        assert len(distributions) > 0
        
        # Find wind speed distribution
        wind_dist = next((d for d in distributions if d.parameter == "wind_speed"), None)
        assert wind_dist is not None
        assert wind_dist.threshold_value == settings.thresholds_wind_ms
    
    def test_calculate_distributions_empty_samples(self):
        """Test distribution calculation with empty sample list."""
        settings = Settings()
        
        distributions = calculate_distributions([], settings)
        
        assert distributions == []


class TestDistributionStatistics:
    """Test statistical properties of distributions."""
    
    def test_histogram_bin_properties(self):
        """Test histogram bin properties are correct."""
        values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
        
        dist = create_distribution(
            parameter="test", 
            unit="unit", 
            values=values,
            n_bins=2
        )
        
        # Check bin properties
        for i, bin in enumerate(dist.bins):
            assert bin.lower_bound < bin.upper_bound
            assert bin.count >= 0
            assert 0.0 <= bin.frequency <= 1.0
            
            # Last bin upper bound should be inclusive
            if i == len(dist.bins) - 1:
                assert bin.upper_bound >= values.max()
    
    def test_distribution_statistics_accuracy(self):
        """Test that calculated statistics match numpy results."""
        np.random.seed(42)
        values = np.random.normal(10.0, 2.0, 100)
        
        dist = create_distribution(
            parameter="test", 
            unit="unit", 
            values=values
        )
        
        # Compare with numpy calculations
        assert dist.mean == pytest.approx(np.mean(values), rel=1e-10)
        assert dist.median == pytest.approx(np.median(values), rel=1e-10)
        assert dist.std_dev == pytest.approx(np.std(values, ddof=1), rel=1e-10)