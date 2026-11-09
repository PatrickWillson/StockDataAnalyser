"""
Eulerpool client: the transport for the European route's older history (config/eulerpool_config.py).

Finds a listing by its Yahoo symbol (Eulerpool writes share classes with a space: 'VOLV B.ST'), else by its own
search, and accepts it only when Eulerpool's company name matches the listing's. The key is sent only as a header and
never logged. clients/eulerpool_mapper.py turns the figures into statement rows behind the overlap gate.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from clients.base_client import BaseAPIClient
from clients.sec_filer_lookup import names_match
from config.eulerpool_config import EULERPOOL_BASE_URL, EULERPOOL_MIN_REQUEST_INTERVAL, EULERPOOL_USER_AGENT
from core.errors import SourceAuthError, SourceRateLimitError, SourceRequestError

logger = logging.getLogger(__name__)


class EulerpoolAuthError(SourceAuthError):
    """Eulerpool rejected the key (HTTP 401 / 403)."""


class EulerpoolRateLimitError(SourceRateLimitError):
    """Eulerpool's request limit was reached (HTTP 429)."""


class EulerpoolRequestError(SourceRequestError):
    """An Eulerpool request failed (network error, unexpected status or invalid JSON)."""


class EulerpoolClient(BaseAPIClient):
    """Fetches a listed company's profile and statements from Eulerpool."""

    def __init__(self, api_key: str, debug: bool = False):
        if not api_key or not api_key.strip():
            raise ValueError("Eulerpool API key is required")
        super().__init__(timeout=60, max_retries=3, backoff_factor=1.0)
        self._api_key = api_key.strip()
        self.debug = debug
        self._last_request = 0.0

    def _get(self, path: str) -> Optional[Any]:
        """The JSON at `path`, or None when Eulerpool has nothing there (HTTP 404)."""
        wait = EULERPOOL_MIN_REQUEST_INTERVAL - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        url = f"{EULERPOOL_BASE_URL}/{path}"
        try:
            response = self._make_request(url, headers={"Authorization": f"Bearer {self._api_key}",
                                                        "Accept": "application/json",
                                                        "User-Agent": EULERPOOL_USER_AGENT})
        except requests.exceptions.RequestException as e:
            raise EulerpoolRequestError(f"Eulerpool request failed: {type(e).__name__}") from None
        finally:
            self._last_request = time.monotonic()
        if response.status_code in (401, 403):
            raise EulerpoolAuthError(f"Eulerpool rejected the API key (HTTP {response.status_code})")
        if response.status_code == 429:
            raise EulerpoolRateLimitError("Eulerpool request limit reached (HTTP 429)")
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise EulerpoolRequestError(f"Eulerpool request failed with status {response.status_code}: {path}")
        try:
            return response.json()
        except ValueError:
            raise EulerpoolRequestError(f"Eulerpool returned invalid JSON for {path}") from None

    def find_profile(self, yahoo_symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Eulerpool's profile of a listing (isin, name, currency, ...), found by its Yahoo symbol, the symbol with a
        space for '-' (share classes), else its own search for the symbol; only when the names match. None if not
        found.
        """
        candidates = [yahoo_symbol] + ([yahoo_symbol.replace("-", " ")] if "-" in yahoo_symbol else [])
        for identifier in candidates:
            profile = self._get(f"equity/profile/{quote(identifier)}")
            if isinstance(profile, dict) and profile.get("isin"):
                return profile if names_match(name, str(profile.get("name") or "")) else None
        found = self._get(f"equity/search?q={quote(yahoo_symbol)}")
        results = (found or {}).get("results") or [] if isinstance(found, dict) else []
        isins = [r.get("isin") for r in results
                 if r.get("type") == "stock" and r.get("isin") and names_match(name, str(r.get("name") or ""))]
        if len(set(isins)) != 1:
            return None
        profile = self._get(f"equity/profile/{isins[0]}")
        return profile if isinstance(profile, dict) and profile.get("isin") else None

    def fetch_statements(self, isin: str) -> Dict[str, List[Dict[str, Any]]]:
        """Annual income and cash-flow statements and quarterly balance sheets ([] when Eulerpool has none)."""
        out = {}
        for key, path in (("income", "equity/incomestatement"), ("balance_quarterly", "equity/balance-sheet-quarterly"),
                          ("cashflow", "equity/cashflowstatement")):
            rows = self._get(f"{path}/{isin}")
            out[key] = rows if isinstance(rows, list) else []
        return out
