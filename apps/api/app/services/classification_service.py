# ABOUTME: Classification service for weather condition thresholds and probabilities
# ABOUTME: Provides intelligent classification of weather conditions with confidence levels

import numpy as np
from typing import Dict, List, Any, Optional
from ..models.weather import WeatherCondition, ClassificationThreshold


class WeatherClassificationService:
    """Service for classifying weather conditions based on analysis results."""
    
    # Classification thresholds for different conditions
    THRESHOLDS = {
        WeatherCondition.VERY_HOT: {
            "parameter": "T2M",
            "threshold": 35.0,  # Celsius
            "direction": "above",
            "description": "Temperature exceeds 35°C indicating very hot conditions"
        },
        WeatherCondition.VERY_COLD: {
            "parameter": "T2M",
            "threshold": 5.0,  # Celsius
            "direction": "below",
            "description": "Temperature below 5°C indicating very cold conditions"
        },
        WeatherCondition.VERY_WINDY: {
            "parameter": "WS10M",
            "threshold": 15.0,  # m/s (approximately 54 km/h or 33.6 mph)
            "direction": "above",
            "description": "Wind speed exceeds 15 m/s indicating very windy conditions"
        },
        WeatherCondition.VERY_WET: {
            "parameter": "PRECTOTCORR",
            "threshold": 25.0,  # mm/day
            "direction": "above",
            "description": "Precipitation exceeds 25mm indicating very wet conditions"
        },
        WeatherCondition.VERY_UNCOMFORTABLE: {
            "parameter": "heat_index",
            "threshold": 40.0,  # Heat index in Celsius
            "direction": "above",
            "description": "Heat index exceeds 40°C indicating very uncomfortable conditions"
        }
    }
    
    def __init__(self):
        pass
    
    def _calculate_probability_from_stats(
        self, 
        stats: Dict[str, float], 
        threshold: float, 
        direction: str
    ) -> float:
        """Calculate probability based on statistical distribution."""
        if not stats or "mean" not in stats or "std" not in stats:
            return 0.0
        
        mean = stats["mean"]
        std = stats["std"]
        
        if np.isnan(mean) or np.isnan(std) or std == 0:
            return 0.0
        
        # Use normal distribution approximation
        z_score = (threshold - mean) / std
        
        if direction == "above":
            # Probability of value being above threshold
            probability = 1 - self._normal_cdf(z_score)
        else:  # direction == "below"
            # Probability of value being below threshold
            probability = self._normal_cdf(z_score)
        
        return max(0.0, min(1.0, probability))
    
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal cumulative distribution function."""
        # Using approximation for standard normal CDF
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x * x / np.pi)))
    
    def _get_confidence_level(self, probability: float, sample_size: int) -> str:
        """Determine confidence level based on probability and sample size."""
        if sample_size < 30:
            return "low"
        elif sample_size < 100:
            if probability > 0.8 or probability < 0.2:
                return "medium"
            else:
                return "low"
        else:  # sample_size >= 100
            if probability > 0.7 or probability < 0.3:
                return "high"
            elif probability > 0.6 or probability < 0.4:
                return "medium"
            else:
                return "low"
    
    def _classify_from_observed_value(
        self, 
        observed_value: float, 
        threshold: float, 
        direction: str
    ) -> float:
        """Calculate probability from observed value."""
        if direction == "above":
            return 1.0 if observed_value > threshold else 0.0
        else:  # direction == "below"
            return 1.0 if observed_value < threshold else 0.0
    
    def classify_weather_conditions(
        self, 
        analysis_result: Dict[str, Any]
    ) -> List[ClassificationThreshold]:
        """Classify weather conditions based on analysis results."""
        classifications = []
        parameters = analysis_result.get("parameters", {})
        derived_insights = analysis_result.get("derived_insights", {})
        analysis_mode = analysis_result.get("meta", {}).get("analysis_mode", "probabilistic")
        
        for condition, config in self.THRESHOLDS.items():
            param_name = config["parameter"]
            threshold = config["threshold"]
            direction = config["direction"]
            description = config["description"]
            
            probability = 0.0
            confidence = "low"
            sample_size = 0
            
            # Handle heat index specially
            if param_name == "heat_index":
                heat_index_data = derived_insights.get("heat_index", {})
                if analysis_mode == "observed":
                    observed_hi = heat_index_data.get("observed_heat_index_c")
                    if observed_hi is not None and not np.isnan(observed_hi):
                        probability = self._classify_from_observed_value(observed_hi, threshold, direction)
                        confidence = "high"
                else:
                    # Use mean or p90 heat index for probabilistic analysis
                    mean_hi = heat_index_data.get("mean_heat_index_c")
                    p90_hi = heat_index_data.get("p90_heat_index_c")
                    
                    if mean_hi is not None and not np.isnan(mean_hi):
                        # Create synthetic stats for heat index
                        hi_value = p90_hi if p90_hi is not None and not np.isnan(p90_hi) else mean_hi
                        probability = self._classify_from_observed_value(hi_value, threshold, direction)
                        
                        # Get sample size from temperature data
                        t2m_data = parameters.get("T2M", {})
                        sample_size = t2m_data.get("sample_size", 0)
                        confidence = self._get_confidence_level(probability, sample_size)
            
            # Handle regular weather parameters
            elif param_name in parameters:
                param_data = parameters[param_name]
                
                if analysis_mode == "observed":
                    observed_value = param_data.get("observed_value")
                    if observed_value is not None and not np.isnan(observed_value):
                        probability = self._classify_from_observed_value(observed_value, threshold, direction)
                        confidence = "high"
                else:
                    stats = param_data.get("stats", {})
                    sample_size = param_data.get("sample_size", 0)
                    
                    if stats:
                        probability = self._calculate_probability_from_stats(stats, threshold, direction)
                        confidence = self._get_confidence_level(probability, sample_size)
            
            # Create classification threshold
            classification = ClassificationThreshold(
                condition=condition,
                probability=round(probability, 3),
                confidence=confidence,
                threshold_value=threshold,
                parameter_used=param_name,
                description=description
            )
            
            classifications.append(classification)
        
        # Sort by probability (descending)
        classifications.sort(key=lambda x: x.probability, reverse=True)
        
        return classifications
    
    def get_risk_summary(self, classifications: List[ClassificationThreshold]) -> Dict[str, Any]:
        """Generate a risk summary based on classifications."""
        high_risk_conditions = [c for c in classifications if c.probability > 0.7]
        moderate_risk_conditions = [c for c in classifications if 0.3 < c.probability <= 0.7]
        low_risk_conditions = [c for c in classifications if c.probability <= 0.3]
        
        overall_risk = "low"
        if high_risk_conditions:
            overall_risk = "high"
        elif moderate_risk_conditions:
            overall_risk = "moderate"
        
        return {
            "overall_risk": overall_risk,
            "high_risk_count": len(high_risk_conditions),
            "moderate_risk_count": len(moderate_risk_conditions),
            "low_risk_count": len(low_risk_conditions),
            "primary_concerns": [c.condition.value for c in high_risk_conditions[:3]],
            "max_probability": max([c.probability for c in classifications]) if classifications else 0.0,
            "avg_probability": sum([c.probability for c in classifications]) / len(classifications) if classifications else 0.0
        }