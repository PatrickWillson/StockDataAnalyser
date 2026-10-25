"""
API Client Configuration.

This module defines configuration settings for external API clients,
including timeout values, retry policies, and backoff strategies.

The configurations are immutable (frozen dataclasses) to ensure
consistent behavior across all API interactions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class APIConfig:
    """
    Configuration for API client behavior.
    
    This dataclass encapsulates the settings that control how API clients
    handle requests, including timeout durations, retry attempts, and
    exponential backoff behavior.
    
    Attributes:
        timeout: Maximum time (in seconds) to wait for an API response
        max_retries: Maximum number of retry attempts for failed requests
        backoff_factor: Multiplier for exponential backoff between retries
                       (e.g., 1.0 means delays of 1s, 2s, 4s, 8s...)
    """
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 1.0


# EODHD API configuration
# EODHD provides fundamental data and requires longer timeouts due to
# the comprehensive nature of the data returned
EODHD_CONFIG: APIConfig = APIConfig(
    timeout=30,
    max_retries=3,
    backoff_factor=1.0
)

# FX (Foreign Exchange) API configuration
# FX rate lookups are typically fast, so we use a shorter timeout
FX_CONFIG: APIConfig = APIConfig(
    timeout=10,
    max_retries=3,
    backoff_factor=1.0
)
