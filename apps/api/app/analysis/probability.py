# ABOUTME: Probability engine for outdoor risk assessment with confidence intervals
# ABOUTME: Implements Clopper-Pearson exact binomial confidence intervals for robust statistics

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..config import Settings
from ..weather.thresholds import (
    WeatherSample,
    flag_weather_conditions,
)


@dataclass
class ProbabilityResult:
    """
    Result of probability calculation with confidence intervals and metadata.

    Provides comprehensive statistical information about the probability of
    dangerous weather conditions based on historical sample analysis.
    """

    # Core probability statistics
    probability: float  # Point estimate (successes / total)
    confidence_interval_lower: float  # Lower bound of 95% CI
    confidence_interval_upper: float  # Upper bound of 95% CI
    confidence_level: float = 0.95  # Confidence level (default 95%)

    # Sample statistics
    total_samples: int = 0  # Total number of samples analyzed
    positive_samples: int = 0  # Number of samples with flagged conditions

    # Coverage and quality metrics
    coverage_years: int = 0  # Number of years of data coverage
    coverage_adequate: bool = False  # Whether coverage meets minimum requirements

    # Metadata
    condition_type: str = (
        "any"  # Type of condition analyzed ("any", "hot", "cold", etc.)
    )
    analysis_timestamp: datetime | None = None  # When analysis was performed

    def __post_init__(self):
        """Set analysis timestamp if not provided."""
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.utcnow()

    @property
    def confidence_interval_width(self) -> float:
        """Width of the confidence interval."""
        return self.confidence_interval_upper - self.confidence_interval_lower

    @property
    def relative_error(self) -> float:
        """Relative error (CI width / 2 / probability), or inf if probability is 0."""
        if self.probability == 0:
            return float("inf")
        return (self.confidence_interval_width / 2) / self.probability

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format for API responses."""
        return {
            "probability": self.probability,
            "confidence_interval": {
                "lower": self.confidence_interval_lower,
                "upper": self.confidence_interval_upper,
                "level": self.confidence_level,
                "width": self.confidence_interval_width,
            },
            "sample_statistics": {
                "total_samples": self.total_samples,
                "positive_samples": self.positive_samples,
            },
            "coverage": {
                "years": self.coverage_years,
                "adequate": self.coverage_adequate,
            },
            "metadata": {
                "condition_type": self.condition_type,
                "analysis_timestamp": self.analysis_timestamp.isoformat()
                if self.analysis_timestamp
                else None,
                "relative_error": self.relative_error
                if math.isfinite(self.relative_error)
                else None,
            },
        }


def beta_inverse_cdf(p: float, alpha: float, beta: float) -> float:
    """
    Inverse cumulative distribution function for Beta distribution.

    Uses robust bisection method to find x such that Beta_CDF(x; alpha, beta) = p.
    This method is numerically stable even for extreme parameter values.

    Args:
        p: Probability (0 <= p <= 1)
        alpha: Beta distribution alpha parameter (> 0)
        beta: Beta distribution beta parameter (> 0)

    Returns:
        Value x such that P(X <= x) = p for X ~ Beta(alpha, beta)
    """
    if not (0 <= p <= 1):
        raise ValueError(f"p must be between 0 and 1, got {p}")
    if alpha <= 0 or beta <= 0:
        raise ValueError(
            f"alpha and beta must be positive, got alpha={alpha}, beta={beta}"
        )

    # Handle edge cases
    if p == 0:
        return 0.0
    if p == 1:
        return 1.0

    # Use bisection method for numerical stability
    lower, upper = 0.0, 1.0
    tolerance = 1e-12
    max_iterations = 100

    # Initial bounds check
    cdf_lower = beta_cdf(lower, alpha, beta)
    cdf_upper = beta_cdf(upper, alpha, beta)

    # Ensure the target is within bounds
    if p <= cdf_lower:
        return lower
    if p >= cdf_upper:
        return upper

    # Bisection method
    for _ in range(max_iterations):
        x = (lower + upper) / 2
        cdf_x = beta_cdf(x, alpha, beta)

        if abs(cdf_x - p) < tolerance:
            return x

        if cdf_x < p:
            lower = x
        else:
            upper = x

        # Check for convergence on x values too
        if abs(upper - lower) < tolerance:
            return (lower + upper) / 2

    return (lower + upper) / 2


def beta_cdf(x: float, alpha: float, beta: float) -> float:
    """
    Cumulative distribution function for Beta distribution.

    Uses incomplete beta function to compute P(X <= x) for X ~ Beta(alpha, beta).

    Args:
        x: Value at which to evaluate CDF (0 <= x <= 1)
        alpha: Beta distribution alpha parameter (> 0)
        beta: Beta distribution beta parameter (> 0)

    Returns:
        P(X <= x) for X ~ Beta(alpha, beta)
    """
    if not (0 <= x <= 1):
        x = max(0, min(1, x))  # Clamp to valid range

    if x == 0:
        return 0.0
    if x == 1:
        return 1.0

    return incomplete_beta(x, alpha, beta)


def beta_pdf(x: float, alpha: float, beta: float) -> float:
    """
    Probability density function for Beta distribution.

    Args:
        x: Value at which to evaluate PDF (0 <= x <= 1)
        alpha: Beta distribution alpha parameter (> 0)
        beta: Beta distribution beta parameter (> 0)

    Returns:
        PDF value at x
    """
    if not (0 <= x <= 1):
        return 0.0

    if x == 0:
        return float("inf") if alpha < 1 else (1.0 if alpha == 1 else 0.0)
    if x == 1:
        return float("inf") if beta < 1 else (1.0 if beta == 1 else 0.0)

    # PDF = x^(alpha-1) * (1-x)^(beta-1) / B(alpha, beta)
    log_pdf = (
        (alpha - 1) * math.log(x)
        + (beta - 1) * math.log(1 - x)
        - log_beta_function(alpha, beta)
    )

    return math.exp(log_pdf)


def incomplete_beta(x: float, a: float, b: float) -> float:
    """
    Regularized incomplete beta function I_x(a,b).

    Uses continued fraction expansion for numerical computation.

    Args:
        x: Upper limit (0 <= x <= 1)
        a: First parameter (> 0)
        b: Second parameter (> 0)

    Returns:
        I_x(a,b) = B(x;a,b) / B(a,b)
    """
    if x == 0:
        return 0.0
    if x == 1:
        return 1.0

    # Use symmetry relation if needed for better convergence
    if x > (a + 1) / (a + b + 2):
        return 1.0 - incomplete_beta(1 - x, b, a)

    # Continued fraction expansion
    bt = math.exp(
        log_gamma(a + b)
        - log_gamma(a)
        - log_gamma(b)
        + a * math.log(x)
        + b * math.log(1 - x)
    )

    if x < (a + 1) / (a + b + 2):
        return bt * continued_fraction_beta(x, a, b) / a
    else:
        return 1.0 - bt * continued_fraction_beta(1 - x, b, a) / b


def continued_fraction_beta(x: float, a: float, b: float) -> float:
    """Continued fraction for incomplete beta function."""
    eps = 1e-15
    max_iter = 1000

    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1.0
    d = 1.0 - qab * x / qap

    if abs(d) < eps:
        d = eps

    d = 1.0 / d
    h = d

    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1.0 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1.0 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1.0 / d
        del_ = d * c
        h *= del_

        if abs(del_ - 1.0) < eps:
            break

    return h


def log_gamma(x: float) -> float:
    """Logarithm of gamma function using Stirling's approximation."""
    if x < 0.5:
        # Use reflection formula: Γ(z)Γ(1-z) = π/sin(πz)
        return math.log(math.pi) - math.log(math.sin(math.pi * x)) - log_gamma(1 - x)

    x -= 1
    # Coefficients for Stirling's series
    coeffs = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7,
    ]

    s = coeffs[0]
    for i in range(1, len(coeffs)):
        s += coeffs[i] / (x + i)

    t = x + len(coeffs) - 1.5
    return 0.5 * math.log(2 * math.pi) + (x + 0.5) * math.log(t) - t + math.log(s)


def log_beta_function(a: float, b: float) -> float:
    """Logarithm of beta function: log(B(a,b)) = log(Γ(a)) + log(Γ(b)) - log(Γ(a+b))."""
    return log_gamma(a) + log_gamma(b) - log_gamma(a + b)


def clopper_pearson_interval(
    successes: int, trials: int, confidence_level: float = 0.95
) -> tuple[float, float]:
    """
    Calculate Clopper-Pearson exact binomial confidence interval.

    This method provides exact coverage probability for binomial proportions,
    making it more reliable than normal approximations for small sample sizes.

    Args:
        successes: Number of successful trials (flagged conditions)
        trials: Total number of trials (weather samples)
        confidence_level: Desired confidence level (default 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound) for confidence interval

    References:
        - Clopper, C.J. & Pearson, E.S. (1934). Biometrika 26: 404-413
        - Brown et al. (2001). Statistical Science 16(2): 101-117
    """
    if not (0 <= successes <= trials):
        raise ValueError(
            f"successes ({successes}) must be between 0 and trials ({trials})"
        )
    if not (0 < confidence_level < 1):
        raise ValueError(
            f"confidence_level must be between 0 and 1, got {confidence_level}"
        )

    alpha = 1 - confidence_level

    # Handle edge cases
    if trials == 0:
        return (0.0, 1.0)
    if successes == 0:
        # Lower bound is 0, upper bound from Beta(1, trials)
        upper = beta_inverse_cdf(1 - alpha / 2, 1, trials) if trials > 0 else 0.0
        return (0.0, upper)
    if successes == trials:
        # Upper bound is 1, lower bound from Beta(trials, 1)
        lower = beta_inverse_cdf(alpha / 2, trials, 1) if trials > 0 else 1.0
        return (lower, 1.0)

    # General case: use Beta distribution quantiles
    # The correct Clopper-Pearson formulas:
    # Lower bound: α/2 quantile of Beta(successes, trials - successes + 1)
    # Upper bound: (1 - α/2) quantile of Beta(successes + 1, trials - successes)

    if successes > 0:
        lower = beta_inverse_cdf(alpha / 2, successes, trials - successes + 1)
    else:
        lower = 0.0

    if successes < trials:
        upper = beta_inverse_cdf(1 - alpha / 2, successes + 1, trials - successes)
    else:
        upper = 1.0

    return (lower, upper)


def calculate_probability(
    samples: list[WeatherSample],
    condition_type: str = "any",
    settings: Settings | None = None,
) -> ProbabilityResult:
    """
    Calculate probability of dangerous weather conditions with confidence intervals.

    This is the main function for outdoor risk probability assessment. It analyzes
    a collection of historical weather samples to determine the probability that
    dangerous conditions will occur, with statistical confidence intervals.

    Args:
        samples: List of weather samples to analyze
        condition_type: Type of condition to analyze:
            - "any": Any dangerous condition (hot, cold, windy, or wet)
            - "hot": Heat-related conditions (heat index or high temperature)
            - "cold": Cold-related conditions (wind chill or low temperature)
            - "windy": High wind speed conditions
            - "wet": High precipitation conditions
            - "multiple": Multiple simultaneous conditions
        settings: Configuration with thresholds and coverage requirements

    Returns:
        ProbabilityResult with probability estimate, confidence intervals, and metadata

    Raises:
        ValueError: If samples list is empty or condition_type is invalid

    Example:
        >>> samples = [WeatherSample(...), ...]
        >>> result = calculate_probability(samples, "hot")
        >>> print(f"Hot weather probability: {result.probability:.2%}")
        >>> print(f"95% CI: [{result.confidence_interval_lower:.2%}, {result.confidence_interval_upper:.2%}]")
    """
    if settings is None:
        settings = Settings()

    if not samples:
        raise ValueError("samples list cannot be empty")

    valid_condition_types = {"any", "hot", "cold", "windy", "wet", "multiple"}
    if condition_type not in valid_condition_types:
        raise ValueError(
            f"condition_type must be one of {valid_condition_types}, got '{condition_type}'"
        )

    # Count positive samples based on condition type
    positive_count = 0
    for sample in samples:
        flags = flag_weather_conditions(sample, settings)

        if condition_type == "any":
            if flags.any_flagged():
                positive_count += 1
        elif condition_type == "hot":
            if flags.very_hot:
                positive_count += 1
        elif condition_type == "cold":
            if flags.very_cold:
                positive_count += 1
        elif condition_type == "windy":
            if flags.very_windy:
                positive_count += 1
        elif condition_type == "wet":
            if flags.very_wet:
                positive_count += 1
        elif condition_type == "multiple":
            if flags.count_flagged() >= 2:
                positive_count += 1

    total_count = len(samples)
    point_estimate = positive_count / total_count if total_count > 0 else 0.0

    # Calculate Clopper-Pearson confidence interval
    lower_bound, upper_bound = clopper_pearson_interval(positive_count, total_count)

    # Assess coverage adequacy
    coverage_years = _estimate_coverage_years(samples)
    coverage_adequate = (
        coverage_years >= settings.coverage_min_years
        and total_count >= settings.coverage_min_samples
    )

    return ProbabilityResult(
        probability=point_estimate,
        confidence_interval_lower=lower_bound,
        confidence_interval_upper=upper_bound,
        total_samples=total_count,
        positive_samples=positive_count,
        coverage_years=coverage_years,
        coverage_adequate=coverage_adequate,
        condition_type=condition_type,
    )


def _estimate_coverage_years(samples: list[WeatherSample]) -> int:
    """
    Estimate the number of years covered by the sample data.

    Args:
        samples: List of weather samples

    Returns:
        Estimated number of years of coverage
    """
    if not samples:
        return 0

    # Get date range
    dates = [sample.timestamp for sample in samples]
    min_date = min(dates)
    max_date = max(dates)

    # Calculate year span
    year_span = max_date.year - min_date.year + 1
    return year_span


def validate_sample_coverage(
    samples: list[WeatherSample], settings: Settings | None = None
) -> dict[str, Any]:
    """
    Validate that sample coverage meets minimum requirements for reliable statistics.

    Args:
        samples: List of weather samples to validate
        settings: Configuration with coverage requirements

    Returns:
        Dictionary with coverage validation results
    """
    if settings is None:
        settings = Settings()

    total_samples = len(samples)
    coverage_years = _estimate_coverage_years(samples)

    meets_year_requirement = coverage_years >= settings.coverage_min_years
    meets_sample_requirement = total_samples >= settings.coverage_min_samples

    return {
        "total_samples": total_samples,
        "coverage_years": coverage_years,
        "requirements": {
            "min_years": settings.coverage_min_years,
            "min_samples": settings.coverage_min_samples,
        },
        "meets_requirements": {
            "years": meets_year_requirement,
            "samples": meets_sample_requirement,
            "overall": meets_year_requirement and meets_sample_requirement,
        },
        "adequacy_score": (
            (coverage_years / settings.coverage_min_years) * 0.5
            + (total_samples / settings.coverage_min_samples) * 0.5
        )
        if settings.coverage_min_years > 0 and settings.coverage_min_samples > 0
        else 0.0,
    }
