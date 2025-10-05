# ABOUTME: HTTP client utilities for NASA API with retry logic and error handling
# ABOUTME: Provides robust HTTP operations with exponential backoff and timeout management

import time
import random
import logging
import asyncio
from typing import Dict, Any
import httpx


logger = logging.getLogger("outdoor_risk_api.http_client")


class HTTPClient:
    """HTTP client with retry logic for external API calls."""
    
    def __init__(self, retries: int = 4, timeout: int = 120):
        self.retries = retries
        self.timeout = timeout
        
    async def get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform HTTP GET request with retry logic.
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            httpx.HTTPError: On non-retryable errors or max retries exceeded
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.retries):
                try:
                    logger.info(
                        f"Making HTTP request (attempt {attempt + 1})",
                        extra={"url": url, "params": params}
                    )
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    logger.info(
                        f"HTTP request successful",
                        extra={"status_code": response.status_code}
                    )
                    
                    return response.json()
                    
                except httpx.HTTPError as e:
                    is_retryable = (
                        not hasattr(e, 'response') or
                        e.response is None or
                        e.response.status_code in {429, 500, 502, 503, 504}
                    )
                    
                    logger.warning(
                        f"HTTP request failed (attempt {attempt + 1})",
                        extra={
                            "error": str(e),
                            "is_retryable": is_retryable,
                            "url": url
                        }
                    )
                    
                    if attempt == self.retries - 1 or not is_retryable:
                        logger.error(
                            "HTTP request failed after all retries",
                            extra={"error": str(e), "url": url}
                        )
                        raise e
                        
                    # Exponential backoff with jitter
                    sleep_time = (2 ** attempt) * random.uniform(0.8, 1.2)
                    await asyncio.sleep(sleep_time)
                    
        raise RuntimeError("Maximum retry attempts exceeded")