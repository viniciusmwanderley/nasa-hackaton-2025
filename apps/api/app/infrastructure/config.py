# ABOUTME: Configuration constants for NASA POWER API integration
# ABOUTME: Contains API endpoints, parameters, and retry settings

from ..domain.enums import Granularity


# NASA POWER API Configuration
BASE_URL = "https://power.larc.nasa.gov/api/temporal"

API_PATHS = {
    Granularity.DAILY: "daily/point",
    Granularity.HOURLY: "hourly/point",
    "climatology": "climatology/point"
}

# Weather Parameters
CLIMATOLOGY_PARAMS = [
    "T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", 
    "IMERG_PRECTOT", "RH2M", "WS10M"
]

DEFAULT_PARAMS = [
    "T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "IMERG_PRECTOT", 
    "RH2M", "WS10M", "CLOUD_AMT", "FRSNO", "ALLSKY_SFC_SW_DWN"
]

DEFAULT_COMMUNITY = "RE"

# Parameters unavailable for hourly data
HOURLY_UNAVAILABLE_PARAMS = {
    "T2M_MAX", "T2M_MIN", "IMERG_PRECTOT", "CLOUD_AMT"
}

# HTTP Client Configuration
DEFAULT_RETRIES = 4
DEFAULT_TIMEOUT = 120
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}