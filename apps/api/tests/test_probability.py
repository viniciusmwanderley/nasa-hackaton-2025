# ABOUTME: Comprehensive test suite for probability engine and statistical functions
# ABOUTME: Tests Clopper-Pearson confidence intervals and probability calculations

import math
from datetime import UTC, datetime, timedelta

import pytest

from app.analysis.probability import (
    ProbabilityResult,
    beta_cdf,
    beta_inverse_cdf,
    beta_pdf,
    calculate_probability,
    clopper_pearson_interval,
    log_gamma,
    validate_sample_coverage,
)
from app.config import Settings
from app.weather.thresholds import WeatherSample


class TestProbabilityResult:
    """Test ProbabilityResult dataclass functionality."""

    def test_probability_result_creation(self):
        """Test basic ProbabilityResult creation and properties."""
        result = ProbabilityResult(
            probability=0.15,
            confidence_interval_lower=0.10,
            confidence_interval_upper=0.22,
            total_samples=100,
            positive_samples=15,
            coverage_years=10,
            coverage_adequate=True,
            condition_type="hot",
        )

        assert result.probability == 0.15
        assert result.confidence_interval_lower == 0.10
        assert result.confidence_interval_upper == 0.22
        assert result.total_samples == 100
        assert result.positive_samples == 15
        assert result.coverage_years == 10
        assert result.coverage_adequate is True
        assert result.condition_type == "hot"

        # Test computed properties
        assert result.confidence_interval_width == 0.12
        assert abs(result.relative_error - 0.4) < 0.001  # (0.12/2)/0.15 = 0.4

    def test_probability_result_zero_probability(self):
        """Test ProbabilityResult with zero probability."""
        result = ProbabilityResult(
            probability=0.0,
            confidence_interval_lower=0.0,
            confidence_interval_upper=0.05,
            total_samples=100,
            positive_samples=0,
        )

        assert result.probability == 0.0
        assert result.relative_error == float("inf")  # Division by zero case

    def test_to_dict_conversion(self):
        """Test conversion to dictionary format."""
        result = ProbabilityResult(
            probability=0.20,
            confidence_interval_lower=0.12,
            confidence_interval_upper=0.30,
            total_samples=50,
            positive_samples=10,
            coverage_years=5,
            coverage_adequate=False,
            condition_type="windy",
        )

        result_dict = result.to_dict()

        # Check structure
        assert "probability" in result_dict
        assert "confidence_interval" in result_dict
        assert "sample_statistics" in result_dict
        assert "coverage" in result_dict
        assert "metadata" in result_dict

        # Check values
        assert result_dict["probability"] == 0.20
        assert result_dict["confidence_interval"]["lower"] == 0.12
        assert result_dict["confidence_interval"]["upper"] == 0.30
        assert result_dict["confidence_interval"]["level"] == 0.95
        assert result_dict["sample_statistics"]["total_samples"] == 50
        assert result_dict["sample_statistics"]["positive_samples"] == 10
        assert result_dict["coverage"]["years"] == 5
        assert result_dict["coverage"]["adequate"] is False
        assert result_dict["metadata"]["condition_type"] == "windy"


class TestBetaDistributionFunctions:
    """Test beta distribution statistical functions."""

    def test_log_gamma_known_values(self):
        """Test log gamma function with known values."""
        # Γ(1) = 1, so log(Γ(1)) = 0
        assert abs(log_gamma(1.0)) < 1e-10

        # Γ(2) = 1, so log(Γ(2)) = 0
        assert abs(log_gamma(2.0)) < 1e-10

        # Γ(3) = 2, so log(Γ(3)) = log(2)
        assert abs(log_gamma(3.0) - math.log(2)) < 1e-10

        # Γ(0.5) = √π, so log(Γ(0.5)) = log(√π) = 0.5*log(π)
        assert abs(log_gamma(0.5) - 0.5 * math.log(math.pi)) < 1e-10

    def test_beta_pdf_uniform_distribution(self):
        """Test beta PDF for uniform distribution Beta(1,1)."""
        # Beta(1,1) is uniform on [0,1], so PDF should be 1 everywhere
        assert abs(beta_pdf(0.0, 1.0, 1.0) - 1.0) < 1e-10
        assert abs(beta_pdf(0.5, 1.0, 1.0) - 1.0) < 1e-10
        assert abs(beta_pdf(1.0, 1.0, 1.0) - 1.0) < 1e-10

    def test_beta_cdf_uniform_distribution(self):
        """Test beta CDF for uniform distribution Beta(1,1)."""
        # Beta(1,1) CDF should be F(x) = x
        assert abs(beta_cdf(0.0, 1.0, 1.0) - 0.0) < 1e-10
        assert abs(beta_cdf(0.25, 1.0, 1.0) - 0.25) < 1e-10
        assert abs(beta_cdf(0.5, 1.0, 1.0) - 0.5) < 1e-10
        assert abs(beta_cdf(0.75, 1.0, 1.0) - 0.75) < 1e-10
        assert abs(beta_cdf(1.0, 1.0, 1.0) - 1.0) < 1e-10

    def test_beta_inverse_cdf_uniform(self):
        """Test beta inverse CDF for uniform distribution."""
        # For Beta(1,1), inverse CDF should be identity function
        assert abs(beta_inverse_cdf(0.0, 1.0, 1.0) - 0.0) < 1e-8
        assert abs(beta_inverse_cdf(0.25, 1.0, 1.0) - 0.25) < 1e-8
        assert abs(beta_inverse_cdf(0.5, 1.0, 1.0) - 0.5) < 1e-8
        assert abs(beta_inverse_cdf(0.75, 1.0, 1.0) - 0.75) < 1e-8
        assert abs(beta_inverse_cdf(1.0, 1.0, 1.0) - 1.0) < 1e-8

    def test_beta_inverse_cdf_input_validation(self):
        """Test beta inverse CDF input validation."""
        # Invalid probability
        with pytest.raises(ValueError, match="p must be between 0 and 1"):
            beta_inverse_cdf(-0.1, 1.0, 1.0)
        with pytest.raises(ValueError, match="p must be between 0 and 1"):
            beta_inverse_cdf(1.1, 1.0, 1.0)

        # Invalid parameters
        with pytest.raises(ValueError, match="alpha and beta must be positive"):
            beta_inverse_cdf(0.5, 0.0, 1.0)
        with pytest.raises(ValueError, match="alpha and beta must be positive"):
            beta_inverse_cdf(0.5, 1.0, -1.0)


class TestClopperPearsonInterval:
    """Test Clopper-Pearson confidence interval calculations."""

    def test_clopper_pearson_edge_cases(self):
        """Test Clopper-Pearson intervals for edge cases."""
        # Zero trials
        lower, upper = clopper_pearson_interval(0, 0)
        assert lower == 0.0
        assert upper == 1.0

        # Zero successes
        lower, upper = clopper_pearson_interval(0, 10)
        assert lower == 0.0
        assert upper > 0.0  # Should have some upper bound
        assert upper < 0.5  # But not too high for 0 successes

        # All successes
        lower, upper = clopper_pearson_interval(10, 10)
        assert lower > 0.5  # Should have reasonable lower bound
        assert upper == 1.0

    def test_clopper_pearson_symmetry(self):
        """Test that Clopper-Pearson intervals have expected symmetry properties."""
        # For 50% success rate, interval should be symmetric around 0.5
        lower, upper = clopper_pearson_interval(50, 100)
        center = (lower + upper) / 2
        assert abs(center - 0.5) < 0.05  # Should be approximately centered

    def test_clopper_pearson_coverage_property(self):
        """Test that intervals get narrower with more samples."""
        # Same proportion (20%), different sample sizes
        lower_small, upper_small = clopper_pearson_interval(2, 10)  # n=10
        lower_large, upper_large = clopper_pearson_interval(20, 100)  # n=100

        width_small = upper_small - lower_small
        width_large = upper_large - lower_large

        # Larger sample should give narrower interval
        assert width_large < width_small

    def test_clopper_pearson_input_validation(self):
        """Test input validation for Clopper-Pearson intervals."""
        # Successes > trials
        with pytest.raises(
            ValueError, match="successes .* must be between 0 and trials"
        ):
            clopper_pearson_interval(15, 10)

        # Negative values
        with pytest.raises(
            ValueError, match="successes .* must be between 0 and trials"
        ):
            clopper_pearson_interval(-1, 10)

        # Invalid confidence level
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            clopper_pearson_interval(5, 10, 0.0)
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            clopper_pearson_interval(5, 10, 1.0)


class TestCalculateProbability:
    """Test the main calculate_probability function."""

    def create_test_samples(
        self,
        count: int,
        hot_fraction: float = 0.0,
        cold_fraction: float = 0.0,
        windy_fraction: float = 0.0,
        wet_fraction: float = 0.0,
    ) -> list[WeatherSample]:
        """Helper to create test samples with specified fractions of conditions."""
        samples = []
        base_date = datetime(2020, 1, 1, 12, 0, tzinfo=UTC)

        for i in range(count):
            # Distribute conditions based on fractions - ensure no overlap
            if i < int(count * hot_fraction):
                is_hot, is_cold, is_windy, is_wet = True, False, False, False
            elif i < int(count * (hot_fraction + cold_fraction)):
                is_hot, is_cold, is_windy, is_wet = False, True, False, False
            elif i < int(count * (hot_fraction + cold_fraction + windy_fraction)):
                is_hot, is_cold, is_windy, is_wet = False, False, True, False
            elif i < int(
                count * (hot_fraction + cold_fraction + windy_fraction + wet_fraction)
            ):
                is_hot, is_cold, is_windy, is_wet = False, False, False, True
            else:
                is_hot, is_cold, is_windy, is_wet = False, False, False, False

            # Create sample with appropriate conditions
            temp = 40.0 if is_hot else (-25.0 if is_cold else 20.0)
            humidity = 80.0 if is_hot else 50.0
            wind = (
                15.0 if is_windy else (12.0 if is_cold else 2.0)
            )  # Wind threshold is 10.8 m/s
            precip = 80.0 if is_wet else 5.0  # 80mm/day = 10mm/h (above threshold)

            sample = WeatherSample(
                temperature_c=temp,
                relative_humidity=humidity,
                wind_speed_ms=wind,
                precipitation_mm_per_day=precip,
                timestamp=base_date + timedelta(days=i),
                latitude=0.0,
                longitude=0.0,
            )
            samples.append(sample)

        return samples

    def test_calculate_probability_no_conditions(self):
        """Test probability calculation with no flagged conditions."""
        # Create samples with no dangerous conditions
        samples = self.create_test_samples(100)  # All normal conditions

        result = calculate_probability(samples, "any")

        assert result.probability == 0.0
        assert result.confidence_interval_lower == 0.0
        assert result.confidence_interval_upper > 0.0  # Should have upper bound
        assert result.total_samples == 100
        assert result.positive_samples == 0
        assert result.condition_type == "any"

    def test_calculate_probability_all_conditions(self):
        """Test probability calculation with all samples flagged."""
        # Create samples where all are hot
        samples = self.create_test_samples(50, hot_fraction=1.0)

        result = calculate_probability(samples, "hot")

        assert result.probability == 1.0
        assert result.confidence_interval_lower < 1.0  # Should have lower bound
        assert result.confidence_interval_upper == 1.0
        assert result.total_samples == 50
        assert result.positive_samples == 50
        assert result.condition_type == "hot"

    def test_calculate_probability_partial_conditions(self):
        """Test probability calculation with partial conditions."""
        # Create samples with 20% hot conditions
        samples = self.create_test_samples(100, hot_fraction=0.2)

        result = calculate_probability(samples, "hot")

        assert abs(result.probability - 0.2) < 0.01  # Should be approximately 20%
        assert result.confidence_interval_lower < result.probability
        assert result.confidence_interval_upper > result.probability
        assert result.total_samples == 100
        assert result.positive_samples == 20

    def test_calculate_probability_condition_types(self):
        """Test different condition types."""
        # Create samples with mixed conditions: 10% hot, 10% cold, 10% windy, 10% wet
        samples = self.create_test_samples(
            100,
            hot_fraction=0.1,
            cold_fraction=0.1,
            windy_fraction=0.1,
            wet_fraction=0.1,
        )

        # Test each condition type
        hot_result = calculate_probability(samples, "hot")
        cold_result = calculate_probability(samples, "cold")
        windy_result = calculate_probability(samples, "windy")
        wet_result = calculate_probability(samples, "wet")
        any_result = calculate_probability(samples, "any")

        # Hot and wet should be ~10% (no overlap)
        assert abs(hot_result.probability - 0.1) < 0.05
        assert abs(wet_result.probability - 0.1) < 0.05

        # Cold should be ~10%
        assert abs(cold_result.probability - 0.1) < 0.05

        # Windy should be ~20% (cold samples also have wind > threshold)
        # Cold samples: 12 m/s > 10.8 m/s threshold
        # Windy samples: 15 m/s > 10.8 m/s threshold
        assert abs(windy_result.probability - 0.2) < 0.05

        # "Any" should be higher due to overlaps
        assert any_result.probability >= 0.3  # hot + cold + windy + wet with overlaps
        assert any_result.positive_samples >= 30

    def test_calculate_probability_multiple_conditions(self):
        """Test multiple simultaneous conditions."""
        # Create samples where some have multiple conditions
        samples = []
        base_date = datetime(2020, 1, 1, 12, 0, tzinfo=UTC)

        # Create 20 samples with hot+windy (multiple conditions)
        for i in range(20):
            sample = WeatherSample(
                temperature_c=40.0,  # Hot
                relative_humidity=80.0,
                wind_speed_ms=15.0,  # Windy
                precipitation_mm_per_day=5.0,
                timestamp=base_date + timedelta(days=i),
                latitude=0.0,
                longitude=0.0,
            )
            samples.append(sample)

        # Add 80 samples with normal conditions
        for i in range(20, 100):
            sample = WeatherSample(
                temperature_c=20.0,
                relative_humidity=50.0,
                wind_speed_ms=2.0,
                precipitation_mm_per_day=5.0,
                timestamp=base_date + timedelta(days=i),
                latitude=0.0,
                longitude=0.0,
            )
            samples.append(sample)

        result = calculate_probability(samples, "multiple")

        # Should detect ~20% of samples with multiple conditions
        assert abs(result.probability - 0.2) < 0.05
        assert result.positive_samples == 20

    def test_calculate_probability_input_validation(self):
        """Test input validation for calculate_probability."""
        samples = self.create_test_samples(10)

        # Empty samples
        with pytest.raises(ValueError, match="samples list cannot be empty"):
            calculate_probability([])

        # Invalid condition type
        with pytest.raises(ValueError, match="condition_type must be one of"):
            calculate_probability(samples, "invalid_type")


class TestCoverageValidation:
    """Test sample coverage validation functions."""

    def test_validate_sample_coverage_adequate(self):
        """Test coverage validation with adequate samples."""
        # Create samples spanning multiple years
        samples = []
        base_date = datetime(2015, 1, 1, tzinfo=UTC)

        # 20 years of data, 1 sample per year (minimum coverage)
        for year in range(20):
            sample = WeatherSample(
                temperature_c=20.0,
                relative_humidity=50.0,
                wind_speed_ms=2.0,
                precipitation_mm_per_day=5.0,
                timestamp=base_date.replace(year=2015 + year),
                latitude=0.0,
                longitude=0.0,
            )
            samples.append(sample)

        settings = Settings(coverage_min_years=15, coverage_min_samples=8)
        validation = validate_sample_coverage(samples, settings)

        assert validation["total_samples"] == 20
        assert validation["coverage_years"] == 20
        assert validation["meets_requirements"]["years"] is True
        assert validation["meets_requirements"]["samples"] is True
        assert validation["meets_requirements"]["overall"] is True
        assert validation["adequacy_score"] > 1.0  # Exceeds requirements

    def test_validate_sample_coverage_inadequate(self):
        """Test coverage validation with inadequate samples."""
        # Create insufficient samples
        samples = []
        base_date = datetime(2023, 1, 1, tzinfo=UTC)

        # Only 2 years of data, 5 samples total
        for i in range(5):
            sample = WeatherSample(
                temperature_c=20.0,
                relative_humidity=50.0,
                wind_speed_ms=2.0,
                precipitation_mm_per_day=5.0,
                timestamp=base_date.replace(year=2023 + (i // 3)),  # Spans 2 years
                latitude=0.0,
                longitude=0.0,
            )
            samples.append(sample)

        settings = Settings(coverage_min_years=15, coverage_min_samples=8)
        validation = validate_sample_coverage(samples, settings)

        assert validation["total_samples"] == 5
        assert validation["coverage_years"] == 2
        assert validation["meets_requirements"]["years"] is False
        assert validation["meets_requirements"]["samples"] is False
        assert validation["meets_requirements"]["overall"] is False
        assert validation["adequacy_score"] < 1.0  # Below requirements

    def test_validate_sample_coverage_empty(self):
        """Test coverage validation with no samples."""
        validation = validate_sample_coverage([])

        assert validation["total_samples"] == 0
        assert validation["coverage_years"] == 0
        assert validation["meets_requirements"]["overall"] is False


class TestStatisticalAccuracy:
    """Test statistical accuracy and numerical properties."""

    def test_confidence_interval_coverage(self):
        """Test that confidence intervals have approximately correct coverage."""
        # For a true probability of 0.2, 95% of confidence intervals should contain 0.2
        # This is a Monte Carlo test of the statistical properties

        true_prob = 0.2
        n_trials = 100
        n_simulations = 100  # Reduced for faster testing

        coverage_count = 0
        for _ in range(n_simulations):
            # Simulate binomial successes
            import random

            successes = sum(1 for _ in range(n_trials) if random.random() < true_prob)

            # Calculate confidence interval
            lower, upper = clopper_pearson_interval(successes, n_trials)

            # Check if interval covers true probability
            if lower <= true_prob <= upper:
                coverage_count += 1

        # Should be approximately 95% coverage (allow some variance)
        coverage_rate = coverage_count / n_simulations
        assert 0.90 <= coverage_rate <= 1.00  # Allow for Monte Carlo variance

    def test_numerical_stability(self):
        """Test numerical stability with extreme values."""
        # Very small probabilities
        lower, upper = clopper_pearson_interval(1, 10000)
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0
        assert lower <= upper  # Order constraint (may be very close for extreme cases)
        assert not math.isnan(lower)
        assert not math.isnan(upper)

        # Very large sample sizes
        lower, upper = clopper_pearson_interval(500, 1000)
        assert 0.0 <= lower <= upper <= 1.0
        assert not math.isnan(lower)
        assert not math.isnan(upper)
