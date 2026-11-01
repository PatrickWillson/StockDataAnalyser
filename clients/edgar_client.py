"""
SEC EDGAR client: the transport for the free resolution path's US statements.

Fetches the SEC ticker index (ticker -> CIK), a company's XBRL "companyfacts" (every fact it has
filed) and its "submissions" (name, SIC, fiscal year end, filings). clients/edgar_mapper.py turns the
facts into provider-neutral statement rows. SEC data is US-government public data; requests follow
the SEC fair-access policy (config/edgar_config.py).
"""

import logging
import time
from typing import Any, Dict, Mapping, Optional, Tuple

import requests

from clients import edgar_mapper
from clients.base_client import BaseAPIClient
from config.edgar_config import (SEC_ARCHIVES_URL, SEC_COMPANY_FACTS_URL, SEC_MIN_REQUEST_INTERVAL, SEC_PREDECESSOR_CIKS,
                                 SEC_SUBMISSIONS_URL, SEC_TICKER_INDEX_URL)
from core.errors import SourceAuthError, SourceRateLimitError, SourceRequestError, TickerNotCoveredError

logger = logging.getLogger(__name__)


class EdgarAuthError(SourceAuthError):
    """SEC refused the request (HTTP 403), usually a missing or undescriptive User-Agent."""


class EdgarRateLimitError(SourceRateLimitError):
    """SEC rate limit exceeded (HTTP 429)."""


class EdgarRequestError(SourceRequestError):
    """An SEC request failed (network error, unexpected status or invalid JSON)."""


def sec_symbol(ticker: str) -> str:
    """'BRK.B.US' / 'brk-b.US' -> 'BRK-B': the SEC index writes share classes with '-'."""
    symbol = ticker.rsplit('.', 1)[0] if ticker.upper().endswith('.US') else ticker
    return symbol.upper().replace('.', '-')


class EdgarClient(BaseAPIClient):
    """Fetches SEC EDGAR data for one or more US tickers."""

    def __init__(self, user_agent: str, debug: bool = False,
                 predecessors: Optional[Mapping[str, Tuple[str, ...]]] = None):
        """
        Args:
            user_agent: requester name and contact email, as the SEC requires (SEC_USER_AGENT)
            predecessors: ticker -> predecessor CIKs of reorganised companies (default: config
                SEC_PREDECESSOR_CIKS)

        Raises:
            ValueError: the User-Agent has no contact email
        """
        if not user_agent or '@' not in user_agent:
            raise ValueError("SEC_USER_AGENT must name the requester and include a contact email "
                             "(SEC fair-access policy), e.g. 'StockDataAnalyser Jane Doe jane@example.com'")
        super().__init__(timeout=30, max_retries=3, backoff_factor=1.0)
        self.user_agent = user_agent
        self.debug = debug
        self.predecessors = dict(SEC_PREDECESSOR_CIKS if predecessors is None else predecessors)
        self._ticker_index: Optional[Dict[str, str]] = None
        self._last_request = 0.0

    def _get_json(self, url: str) -> Any:
        response = self._get(url)
        try:
            return response.json()
        except ValueError as e:
            raise EdgarRequestError(f"SEC returned invalid JSON for {url}") from e

    def _get_text(self, url: str) -> str:
        return self._get(url).text

    def _get(self, url: str):
        wait = SEC_MIN_REQUEST_INTERVAL - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self._make_request(url, headers={"User-Agent": self.user_agent,
                                                        "Accept-Encoding": "gzip, deflate"})
        except requests.exceptions.RequestException as e:
            raise EdgarRequestError(str(e)) from e
        finally:
            self._last_request = time.monotonic()
        if response.status_code == 403:
            raise EdgarAuthError("SEC refused the request (HTTP 403). Check SEC_USER_AGENT: it must name "
                                 "you and give a contact email.")
        if response.status_code == 429:
            raise EdgarRateLimitError("SEC rate limit exceeded (HTTP 429). Please wait and try again.")
        if response.status_code == 404:
            raise TickerNotCoveredError(f"SEC has no data at {url}")
        if response.status_code != 200:
            raise EdgarRequestError(f"SEC request failed with status {response.status_code}: {url}")
        return response

    def resolve_cik(self, ticker: str) -> str:
        """
        The 10-digit CIK of a US ticker (e.g. 'AAPL.US' -> '0000320193').

        Raises:
            TickerNotCoveredError: the ticker is not in the SEC index (not an SEC filer)
        """
        symbol = sec_symbol(ticker)
        if self._ticker_index is None:
            index = self._get_json(SEC_TICKER_INDEX_URL)
            self._ticker_index = {str(entry["ticker"]).upper(): str(entry["cik_str"]).zfill(10)
                                  for entry in index.values()}
        if symbol not in self._ticker_index:
            raise TickerNotCoveredError(f"{ticker}: not in the SEC ticker index (not an SEC filer?)")
        return self._ticker_index[symbol]

    def predecessor_ciks(self, ticker: str) -> Tuple[str, ...]:
        """CIKs of the filers this company succeeded (config SEC_PREDECESSOR_CIKS), oldest last."""
        return tuple(self.predecessors.get(sec_symbol(ticker), ()))

    def fetch_company_facts(self, cik: str) -> Dict[str, Any]:
        """Every XBRL fact the company has filed (data.sec.gov companyfacts)."""
        return self._get_json(SEC_COMPANY_FACTS_URL.format(cik=cik))

    def fetch_certifying_officer(self, cik: str, submissions: Mapping[str, Any]) -> Optional[str]:
        """
        The principal executive officer who signed the latest 10-K's Exhibit 31.1 certification
        (Sarbanes-Oxley s.302), or None. Two requests: the filing's SGML header (which names each
        document's type) and the exhibit. Failures return None: the name is display only.
        """
        recent = submissions.get("filings", {}).get("recent", {})
        accession = next((acc for form, acc in zip(recent.get("form", []), recent.get("accessionNumber", []))
                          if form == "10-K"), None)
        if not accession:
            return None
        folder = SEC_ARCHIVES_URL.format(cik=int(cik), accession=accession.replace("-", ""))
        try:
            header = self._get_text(f"{folder}/{accession}-index-headers.html")
            exhibit = edgar_mapper.exhibit_filename(header, "EX-31.1")
            return edgar_mapper.certifying_officer(self._get_text(f"{folder}/{exhibit}")) if exhibit else None
        except (SourceRequestError, SourceRateLimitError, SourceAuthError, TickerNotCoveredError) as e:
            logger.debug(f"SEC: no Exhibit 31.1 officer for CIK {cik}: {e}")
            return None

    def fetch_submissions(self, cik: str) -> Dict[str, Any]:
        """Company metadata and recent filings (data.sec.gov submissions)."""
        return self._get_json(SEC_SUBMISSIONS_URL.format(cik=cik))
