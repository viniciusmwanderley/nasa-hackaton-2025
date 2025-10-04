# ABOUTME: Unit tests for weather classification service functionality  
# ABOUTME: Tests weather condition classification, probability calculations, and risk assessment

import pytest
import numpy as np
from unittest.mock import Mock

from app.services.classification_service import WeatherClassificationService
from app.models.weather import WeatherCondition


class TestWeatherClassificationService:
    """Test suite for WeatherClassificationService."""
    
    def setup_method(self):
        """Set up test instance."""
        self.service = WeatherClassificationService()
    
    def test_normal_cdf_approximation(self):
        """Test normal CDF approximation function."""
        # Test some known values
        assert abs(self.service._normal_cdf(0) - 0.5) < 0.1
        assert self.service._normal_cdf(-3) < 0.1
        assert self.service._normal_cdf(3) > 0.9
    
    def test_calculate_probability_from_stats_above_threshold(self):
        """Test probability calculation for values above threshold."""
        stats = {
            "mean": 30.0,
            "std": 5.0
        }
        threshold = 35.0
        direction = "above"
        
        probability = self.service._calculate_probability_from_stats(stats, threshold, direction)
        
        # Probability should be between 0 and 1
        assert 0 <= probability <= 1
        # Should be relatively low since threshold is 1 std dev above mean
        assert probability < 0.5
    
    def test_calculate_probability_from_stats_below_threshold(self):
        """Test probability calculation for values below threshold."""
        stats = {
            "mean": 30.0,
            "std": 5.0
        }
        threshold = 25.0
        direction = "below"
        
        probability = self.service._calculate_probability_from_stats(stats, threshold, direction)
        
        # Probability should be between 0 and 1
        assert 0 <= probability <= 1
        # Should be relatively low since threshold is 1 std dev below mean
        assert probability < 0.5
    
    def test_calculate_probability_from_stats_invalid_stats(self):
        """Test probability calculation with invalid statistics."""
        # Empty stats
        assert self.service._calculate_probability_from_stats({}, 35.0, "above") == 0.0
        
        # NaN values
        stats_with_nan = {"mean": float('nan'), "std": 5.0}
        assert self.service._calculate_probability_from_stats(stats_with_nan, 35.0, "above") == 0.0
        
        # Zero standard deviation
        stats_zero_std = {"mean": 30.0, "std": 0.0}
        assert self.service._calculate_probability_from_stats(stats_zero_std, 35.0, "above") == 0.0
    
    def test_get_confidence_level_small_sample(self):
        """Test confidence level determination with small sample."""
        # Small sample size should result in low confidence
        assert self.service._get_confidence_level(0.9, 25) == "low"
        assert self.service._get_confidence_level(0.1, 25) == "low"
    
    def test_get_confidence_level_medium_sample(self):
        """Test confidence level determination with medium sample."""
        # Medium sample with extreme probability should be medium confidence
        assert self.service._get_confidence_level(0.9, 75) == "medium"
        assert self.service._get_confidence_level(0.1, 75) == "medium"
        
        # Medium sample with moderate probability should be low confidence
        assert self.service._get_confidence_level(0.5, 75) == "low"
    
    def test_get_confidence_level_large_sample(self):
        """Test confidence level determination with large sample."""
        # Large sample with extreme probability should be high confidence
        assert self.service._get_confidence_level(0.8, 150) == "high"
        assert self.service._get_confidence_level(0.2, 150) == "high"
        
        # Large sample with moderate probability should be medium confidence
        assert self.service._get_confidence_level(0.65, 150) == "medium"
        assert self.service._get_confidence_level(0.35, 150) == "medium"
        
        # Large sample with neutral probability should be low confidence
        assert self.service._get_confidence_level(0.5, 150) == "low"
    
    def test_classify_from_observed_value_above(self):
        """Test classification from observed value (above threshold)."""
        # Value above threshold
        assert self.service._classify_from_observed_value(40.0, 35.0, "above") == 1.0
        
        # Value below threshold
        assert self.service._classify_from_observed_value(30.0, 35.0, "above") == 0.0
    
    def test_classify_from_observed_value_below(self):
        """Test classification from observed value (below threshold)."""
        # Value below threshold
        assert self.service._classify_from_observed_value(2.0, 5.0, "below") == 1.0
        
        # Value above threshold
        assert self.service._classify_from_observed_value(8.0, 5.0, "below") == 0.0
    
    def test_classify_weather_conditions_observed_mode(self):
        """Test weather condition classification in observed mode."""
        analysis_result = {
            "meta": {
                "analysis_mode": "observed"
            },
            "parameters": {
                "T2M": {
                    "observed_value": 37.0  # Above very_hot threshold (35.0)
                },
                "WS10M": {
                    "observed_value": 12.0  # Below very_windy threshold (15.0)
                },
                "PRECTOTCORR": {
                    "observed_value": 30.0  # Above very_wet threshold (25.0)
                }
            },
            "derived_insights": {
                "heat_index": {
                    "observed_heat_index_c": 42.0  # Above very_uncomfortable threshold (40.0)
                }
            }
        }
        
        classifications = self.service.classify_weather_conditions(analysis_result)
        
        # Should have all 5 conditions
        assert len(classifications) == 5
        
        # Find specific classifications
        very_hot = next(c for c in classifications if c.condition == WeatherCondition.VERY_HOT)
        very_windy = next(c for c in classifications if c.condition == WeatherCondition.VERY_WINDY)
        very_wet = next(c for c in classifications if c.condition == WeatherCondition.VERY_WET)
        very_uncomfortable = next(c for c in classifications if c.condition == WeatherCondition.VERY_UNCOMFORTABLE)
        
        # Check probabilities
        assert very_hot.probability == 1.0  # Temperature above threshold
        assert very_windy.probability == 0.0  # Wind below threshold  
        assert very_wet.probability == 1.0  # Precipitation above threshold
        assert very_uncomfortable.probability == 1.0  # Heat index above threshold
        
        # Check confidence levels (observed mode should be high confidence)
        assert very_hot.confidence == "high"
        assert very_windy.confidence == "high"
        assert very_wet.confidence == "high"
        assert very_uncomfortable.confidence == "high"
    
    def test_classify_weather_conditions_probabilistic_mode(self):
        """Test weather condition classification in probabilistic mode."""
        analysis_result = {
            "meta": {
                "analysis_mode": "probabilistic"
            },
            "parameters": {
                "T2M": {
                    "stats": {
                        "mean": 32.0,
                        "std": 3.0
                    },
                    "sample_size": 150
                },
                "WS10M": {
                    "stats": {
                        "mean": 18.0,  # Mean above very_windy threshold (15.0)
                        "std": 4.0
                    },
                    "sample_size": 150
                }
            },
            "derived_insights": {
                "heat_index": {
                    "mean_heat_index_c": 35.0,
                    "p90_heat_index_c": 38.0  # Below very_uncomfortable threshold (40.0)
                }
            }
        }
        
        classifications = self.service.classify_weather_conditions(analysis_result)
        
        # Should have all 5 conditions
        assert len(classifications) == 5
        
        # All probabilities should be between 0 and 1
        for classification in classifications:
            assert 0 <= classification.probability <= 1
        
        # Find very_windy classification (should have higher probability due to mean > threshold)
        very_windy = next(c for c in classifications if c.condition == WeatherCondition.VERY_WINDY)
        assert very_windy.probability > 0.5  # Mean is above threshold
        
        # Sample size is large, so confidence should be high for extreme probabilities
        if very_windy.probability > 0.7:
            assert very_windy.confidence == "high"
    
    def test_classify_weather_conditions_missing_parameters(self):
        """Test classification when some parameters are missing."""
        analysis_result = {
            "meta": {
                "analysis_mode": "probabilistic"
            },
            "parameters": {
                "T2M": {
                    "stats": {
                        "mean": 25.0,
                        "std": 2.0
                    },
                    "sample_size": 100
                }
                # Missing other parameters
            },
            "derived_insights": {}
        }
        
        classifications = self.service.classify_weather_conditions(analysis_result)
        
        # Should still return all 5 conditions, but most will have 0 probability
        assert len(classifications) == 5
        
        # Most conditions should have 0 probability due to missing data
        zero_prob_count = sum(1 for c in classifications if c.probability == 0.0)
        assert zero_prob_count >= 4  # At least 4 should be zero (only T2M available)
    
    def test_get_risk_summary_high_risk(self):
        """Test risk summary generation with high risk conditions."""
        classifications = [
            Mock(condition=WeatherCondition.VERY_HOT, probability=0.8),
            Mock(condition=WeatherCondition.VERY_WET, probability=0.9),
            Mock(condition=WeatherCondition.VERY_WINDY, probability=0.2),
            Mock(condition=WeatherCondition.VERY_COLD, probability=0.1),
            Mock(condition=WeatherCondition.VERY_UNCOMFORTABLE, probability=0.75),
        ]
        
        # Mock the .value attribute for each condition
        for i, condition in enumerate([WeatherCondition.VERY_HOT, WeatherCondition.VERY_WET, 
                                     WeatherCondition.VERY_WINDY, WeatherCondition.VERY_COLD, 
                                     WeatherCondition.VERY_UNCOMFORTABLE]):
            classifications[i].condition.value = condition.value
        
        summary = self.service.get_risk_summary(classifications)
        
        assert summary["overall_risk"] == "high"
        assert summary["high_risk_count"] == 3  # Probabilities > 0.7
        assert summary["moderate_risk_count"] == 0  # None between 0.3 and 0.7
        assert summary["low_risk_count"] == 2  # Probabilities <= 0.3
        assert len(summary["primary_concerns"]) <= 3
        assert summary["max_probability"] == 0.9
        assert summary["avg_probability"] == 0.55  # (0.8+0.9+0.2+0.1+0.75)/5
    
    def test_get_risk_summary_moderate_risk(self):
        """Test risk summary generation with moderate risk conditions."""
        classifications = [
            Mock(condition=WeatherCondition.VERY_HOT, probability=0.5),
            Mock(condition=WeatherCondition.VERY_WET, probability=0.4),
            Mock(condition=WeatherCondition.VERY_WINDY, probability=0.2),
            Mock(condition=WeatherCondition.VERY_COLD, probability=0.1),
            Mock(condition=WeatherCondition.VERY_UNCOMFORTABLE, probability=0.3),
        ]
        
        # Mock the .value attribute for each condition  
        for i, condition in enumerate([WeatherCondition.VERY_HOT, WeatherCondition.VERY_WET,
                                     WeatherCondition.VERY_WINDY, WeatherCondition.VERY_COLD,
                                     WeatherCondition.VERY_UNCOMFORTABLE]):
            classifications[i].condition.value = condition.value
        
        summary = self.service.get_risk_summary(classifications)
        
        assert summary["overall_risk"] == "moderate"
        assert summary["high_risk_count"] == 0  # No probabilities > 0.7
        assert summary["moderate_risk_count"] == 3  # 0.5, 0.4, and boundary 0.3
        assert summary["low_risk_count"] == 2  # 0.2 and 0.1
    
    def test_get_risk_summary_low_risk(self):
        """Test risk summary generation with low risk conditions."""
        classifications = [
            Mock(condition=WeatherCondition.VERY_HOT, probability=0.1),
            Mock(condition=WeatherCondition.VERY_WET, probability=0.05),
            Mock(condition=WeatherCondition.VERY_WINDY, probability=0.2),
            Mock(condition=WeatherCondition.VERY_COLD, probability=0.15),
            Mock(condition=WeatherCondition.VERY_UNCOMFORTABLE, probability=0.0),
        ]
        
        # Mock the .value attribute for each condition
        for i, condition in enumerate([WeatherCondition.VERY_HOT, WeatherCondition.VERY_WET,
                                     WeatherCondition.VERY_WINDY, WeatherCondition.VERY_COLD,
                                     WeatherCondition.VERY_UNCOMFORTABLE]):
            classifications[i].condition.value = condition.value
        
        summary = self.service.get_risk_summary(classifications)
        
        assert summary["overall_risk"] == "low"
        assert summary["high_risk_count"] == 0
        assert summary["moderate_risk_count"] == 0
        assert summary["low_risk_count"] == 5  # All probabilities <= 0.3
        assert summary["primary_concerns"] == []  # No high risk conditions
    
    def test_get_risk_summary_empty_classifications(self):
        """Test risk summary with empty classifications list."""
        summary = self.service.get_risk_summary([])
        
        assert summary["overall_risk"] == "low"
        assert summary["high_risk_count"] == 0
        assert summary["moderate_risk_count"] == 0  
        assert summary["low_risk_count"] == 0
        assert summary["primary_concerns"] == []
        assert summary["max_probability"] == 0.0
        assert summary["avg_probability"] == 0.0