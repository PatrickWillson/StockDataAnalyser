"""
Base API Client

Provides common functionality for API clients including:
- Session management with retry logic
- HTTP request handling
- Error handling patterns
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional


class BaseAPIClient:
    """
    Base class for API clients with retry logic and session management.
    
    Subclasses should override:
    - API_BASE_URL: The base URL for the API
    """
    
    API_BASE_URL: Optional[str] = None
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize base API client with configurable retry logic.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            backoff_factor: Backoff factor for retries (default: 1.0)
                           Wait times: backoff_factor * (2 ** (retry_number - 1))
                           e.g., 1.0 → 1s, 2s, 4s between retries
        """
        self.timeout = timeout
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["GET"]  # Only retry GET requests
        )
        
        # Create session with retry adapter
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _make_request(self, url: str, params: Optional[dict] = None, 
                     headers: Optional[dict] = None) -> requests.Response:
        """
        Make HTTP GET request with error handling.
        
        Args:
            url: Full URL to request
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: On request failures
        """
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            return response
            
        except requests.exceptions.Timeout as e:
            raise requests.exceptions.RequestException(
                f"Request timeout after {self.timeout}s. Check your network connection."
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise requests.exceptions.RequestException(
                "Connection error. Check your network connection."
            ) from e
        except Exception as e:
            raise requests.exceptions.RequestException(
                f"Unexpected error during API request: {str(e)}"
            ) from e
    
    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
