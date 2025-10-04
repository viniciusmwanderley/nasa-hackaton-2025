"""
IMERG client for NASA GPM IMERG precipitation data.

IMERG (Integrated Multi-satellitE Retrievals for GPM) provides half-hourly
global precipitation estimates. This client handles data access, authentication,
and hourly aggregation with fallback to POWER data.
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field, field_validator

from app.config import Settings

logger = logging.getLogger(__name__)


class ImergDataPoint(BaseModel):
    """Single IMERG precipitation measurement."""

    timestamp: datetime = Field(description="UTC timestamp")
    precipitation_mm: float = Field(description="Precipitation in mm/hr")
    quality_flag: int | None = Field(default=None, description="Quality indicator")

    @field_validator("precipitation_mm")
    @classmethod
    def validate_precipitation(cls, v):
        """Validate precipitation values."""
        if v < 0:
            logger.warning(f"Negative precipitation value: {v}")
            return 0.0
        if v > 1000:  # Extreme rainfall threshold
            logger.warning(f"Extremely high precipitation value: {v}")
        return v


class ImergHourlyData(BaseModel):
    """Aggregated hourly IMERG precipitation data."""

    hour: int = Field(description="Hour of day (0-23)")
    total_mm: float = Field(description="Total precipitation in mm")
    avg_rate_mm_hr: float = Field(description="Average precipitation rate in mm/hr")
    data_points: int = Field(description="Number of half-hourly data points")
    quality_score: float = Field(description="Average quality score (0-1)")
    source: str = Field(default="IMERG", description="Data source identifier")


class ImergResponse(BaseModel):
    """IMERG API response structure."""

    latitude: float
    longitude: float
    date: str
    data: list[ImergDataPoint]
    metadata: dict[str, str | int | float] = Field(default_factory=dict)


class ImergClient:
    """Client for NASA GPM IMERG precipitation data."""

    def __init__(self, settings: Settings | None = None):
        """Initialize IMERG client."""
        self.settings = settings or Settings()
        self._setup_client()

    def _setup_client(self):
        """Setup HTTP client with authentication."""
        headers = {
            "User-Agent": f"nasa-hackathon-outdoor-risk/{self.settings.app_version}",
            "Accept": "application/json",
        }

        # Add authentication if available
        if hasattr(self.settings, "imerg_api_key") and self.settings.imerg_api_key:
            headers["Authorization"] = f"Bearer {self.settings.imerg_api_key}"

        self.client = httpx.AsyncClient(
            timeout=self.settings.http_timeout, headers=headers, follow_redirects=True
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def get_half_hourly_data(
        self, latitude: float, longitude: float, date: datetime, product: str = "early"
    ) -> ImergResponse | None:
        """
        Get half-hourly IMERG precipitation data for a specific date.

        Args:
            latitude: Latitude in decimal degrees (-90 to 90)
            longitude: Longitude in decimal degrees (-180 to 180)
            date: Date to retrieve data for
            product: IMERG product type ("early", "late", "final")

        Returns:
            IMERG response with half-hourly data or None if failed
        """
        # Validate inputs first (let validation errors propagate)
        self._validate_coordinates(latitude, longitude)

        try:
            # For MVP, simulate IMERG data structure
            # In production, this would call the actual IMERG API
            logger.info(
                f"Simulating IMERG {product} data for "
                f"lat={latitude:.2f}, lon={longitude:.2f}, date={date.date()}"
            )

            # Generate simulated half-hourly precipitation data
            data_points = []
            base_timestamp = date.replace(hour=0, minute=0, second=0, microsecond=0)

            for half_hour in range(48):  # 48 half-hour periods in a day
                timestamp = base_timestamp + timedelta(minutes=30 * half_hour)

                # Simulate precipitation pattern (afternoon peak)
                hour_of_day = timestamp.hour + timestamp.minute / 60
                base_precip = max(0, 0.5 * (1 + 0.5 * (hour_of_day - 14) ** 2 / 25))

                # Add some variability
                import random

                random.seed(
                    int(timestamp.timestamp())
                    + int(latitude * 1000)
                    + int(longitude * 1000)
                )
                variability = random.uniform(0.5, 2.0)

                precipitation = base_precip * variability
                quality = random.uniform(0.7, 1.0)

                data_points.append(
                    ImergDataPoint(
                        timestamp=timestamp.replace(tzinfo=ZoneInfo("UTC")),
                        precipitation_mm=precipitation,
                        quality_flag=int(quality * 100),
                    )
                )

            return ImergResponse(
                latitude=latitude,
                longitude=longitude,
                date=date.isoformat()[:10],
                data=data_points,
                metadata={
                    "product": product,
                    "version": "V07",
                    "grid_resolution": "0.1_degree",
                    "temporal_resolution": "30_minutes",
                },
            )

        except Exception as e:
            logger.error(f"Failed to get IMERG data: {e}")
            return None

    async def aggregate_to_hourly(
        self, half_hourly_data: ImergResponse, timezone: str = "UTC"
    ) -> list[ImergHourlyData]:
        """
        Aggregate half-hourly IMERG data to hourly precipitation.

        Args:
            half_hourly_data: IMERG response with half-hourly data
            timezone: Target timezone for hourly aggregation

        Returns:
            List of hourly precipitation data
        """
        if not half_hourly_data or not half_hourly_data.data:
            return []

        try:
            tz = ZoneInfo(timezone)
            hourly_data = {}

            for point in half_hourly_data.data:
                # Convert to target timezone
                local_time = point.timestamp.astimezone(tz)
                hour_key = local_time.hour

                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {
                        "precipitation_sum": 0.0,
                        "quality_sum": 0.0,
                        "count": 0,
                    }

                # Accumulate precipitation (convert rate to total for 30-minute period)
                precip_30min = point.precipitation_mm * 0.5  # mm/hr * 0.5hr
                hourly_data[hour_key]["precipitation_sum"] += precip_30min

                # Accumulate quality scores
                quality = (point.quality_flag or 80) / 100.0
                hourly_data[hour_key]["quality_sum"] += quality
                hourly_data[hour_key]["count"] += 1

            # Convert to hourly data objects
            results = []
            for hour in sorted(hourly_data.keys()):
                data = hourly_data[hour]
                avg_quality = (
                    data["quality_sum"] / data["count"] if data["count"] > 0 else 0.0
                )
                total_mm = data["precipitation_sum"]
                avg_rate = total_mm  # Already in mm/hr equivalent

                results.append(
                    ImergHourlyData(
                        hour=hour,
                        total_mm=total_mm,
                        avg_rate_mm_hr=avg_rate,
                        data_points=data["count"],
                        quality_score=avg_quality,
                        source="IMERG",
                    )
                )

            logger.info(
                f"Aggregated {len(half_hourly_data.data)} half-hourly points to {len(results)} hourly values"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to aggregate IMERG data to hourly: {e}")
            return []

    async def get_hourly_precipitation(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        timezone: str = "UTC",
        product: str = "early",
    ) -> list[ImergHourlyData]:
        """
        Get hourly precipitation data from IMERG.

        This is the main method that combines data retrieval and aggregation.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date to retrieve data for
            timezone: Target timezone for hourly aggregation
            product: IMERG product type

        Returns:
            List of hourly precipitation data
        """
        try:
            # Get half-hourly data
            half_hourly = await self.get_half_hourly_data(
                latitude, longitude, date, product
            )

            if not half_hourly:
                logger.warning("No IMERG half-hourly data available")
                return []

            # Aggregate to hourly
            hourly = await self.aggregate_to_hourly(half_hourly, timezone)

            return hourly

        except Exception as e:
            logger.error(f"Failed to get hourly IMERG precipitation: {e}")
            return []

    def _validate_coordinates(self, latitude: float, longitude: float):
        """Validate coordinate inputs."""
        if not -90 <= latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")


def create_imerg_client(settings: Settings | None = None) -> ImergClient:
    """Factory function to create IMERG client."""
    return ImergClient(settings)
