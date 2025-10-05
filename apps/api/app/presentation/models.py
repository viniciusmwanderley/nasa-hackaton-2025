# ABOUTME: API response models and error handling for weather analysis endpoints
# ABOUTME: Defines response schemas and exception handling for clean API contracts

from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException, status


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    details: Optional[str] = None


class WeatherAnalysisException(HTTPException):
    """Custom exception for weather analysis errors."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class ValidationException(WeatherAnalysisException):
    """Exception for validation errors."""
    
    def __init__(self, detail: str):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)


class ExternalServiceException(WeatherAnalysisException):
    """Exception for external service errors."""
    
    def __init__(self, detail: str):
        super().__init__(detail, status.HTTP_502_BAD_GATEWAY)