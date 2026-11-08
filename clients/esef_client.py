"""
filings.xbrl.org client: the transport for the European route's statements (ESEF annual reports).

Lists a company's filings by LEI and downloads each report's xBRL-JSON. The index is not dependable on its own:
its period end can be wrong (Tenaris lists 2024-04-30 for a December year), interim reports are mixed in, and the
same report can be listed under two countries (TotalEnergies under FR and GB) or refiled as a new version. So this
client only picks one listing per report (select_reports); which reports are annual, and their dates, come from
the facts themselves (clients/esef_mapper.py).
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import requests

from clients.base_client import BaseAPIClient
from config.esef_config import (ESEF_BASE_URL, ESEF_ENTITIES_URL, ESEF_FILINGS_URL, ESEF_MAX_RETRY_WAIT, ESEF_MIN_REQUEST_INTERVAL,
                                ESEF_PAGE_SIZE, ESEF_RATE_LIMIT_RETRIES, ESEF_USER_AGENT)
from core.errors import SourceRateLimitError, SourceRequestError

logger = logging.getLogger(__name__)


class EsefRateLimitError(SourceRateLimitError):
    """filings.xbrl.org kept answering HTTP 429."""


class EsefRequestError(SourceRequestError):
    """A filings.xbrl.org request failed (network error, unexpected status or invalid JSON)."""


@dataclass(frozen=True)
class EsefFiling:
    """One listing in the filings.xbrl.org index."""
    fxo_id: str            # '<LEI>-<period end>-ESEF-<country>-<version>'
    period_end: str        # as indexed (can be wrong; the facts' own dates are used)
    country: str
    json_url: str          # absolute URL of the xBRL-JSON, '' if the index has none
    date_added: str
    error_count: int

    @property
    def version(self) -> int:
        tail = self.fxo_id.rsplit("-", 1)[-1]
        return int(tail) if tail.isdigit() else 0

    @property
    def is_esef(self) -> bool:
        return "-ESEF-" in self.fxo_id


def _filing(item: Mapping[str, Any]) -> EsefFiling:
    attributes = item.get("attributes") or {}
    json_url = attributes.get("json_url") or ""
    return EsefFiling(
        fxo_id=str(attributes.get("fxo_id") or ""),
        period_end=str(attributes.get("period_end") or ""),
        country=str(attributes.get("country") or ""),
        json_url=ESEF_BASE_URL + json_url if json_url.startswith("/") else json_url,
        date_added=str(attributes.get("date_added") or ""),
        error_count=int(attributes.get("error_count") or 0),
    )


def select_reports(filings: Sequence[EsefFiling]) -> List[EsefFiling]:
    """
    One listing per report, oldest first: ESEF listings with xBRL-JSON only; of a report listed more than once
    (same indexed period end: another country, or a refiled version), the one with the fewest validation errors,
    then the newest version, then the most recently added.
    """
    best: Dict[str, EsefFiling] = {}
    for filing in filings:
        if not filing.is_esef or not filing.json_url or not filing.period_end:
            continue
        current = best.get(filing.period_end)
        key = (-filing.error_count, filing.version, filing.date_added)
        if current is None or key > (-current.error_count, current.version, current.date_added):
            best[filing.period_end] = filing
    return [best[end] for end in sorted(best)]


class EsefClient(BaseAPIClient):
    """Fetches a company's ESEF filings from filings.xbrl.org."""

    def __init__(self, debug: bool = False):
        super().__init__(timeout=120, max_retries=3, backoff_factor=1.0)
        self.debug = debug
        self._last_request = 0.0

    def _get_json(self, url: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        for attempt in range(ESEF_RATE_LIMIT_RETRIES + 1):
            wait = ESEF_MIN_REQUEST_INTERVAL - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                response = self._make_request(url, params=dict(params) if params else None,
                                              headers={"User-Agent": ESEF_USER_AGENT,
                                                       "Accept": "application/vnd.api+json, application/json"})
            except requests.exceptions.RequestException as e:
                raise EsefRequestError(f"filings.xbrl.org request failed: {e}") from e
            finally:
                self._last_request = time.monotonic()
            if response.status_code == 429:
                if attempt == ESEF_RATE_LIMIT_RETRIES:
                    break
                time.sleep(_retry_after(response, attempt))
                continue
            if response.status_code != 200:
                raise EsefRequestError(f"filings.xbrl.org request failed with status {response.status_code}: {url}")
            try:
                return response.json()
            except ValueError as e:
                raise EsefRequestError(f"filings.xbrl.org returned invalid JSON for {url}") from e
        raise EsefRateLimitError("filings.xbrl.org rate limit exceeded (HTTP 429). Please wait and try again.")

    def fetch_filings(self, lei: str) -> List[EsefFiling]:
        """Every filing indexed for the LEI (all pages), in index order."""
        filings: List[EsefFiling] = []
        url: Optional[str] = ESEF_FILINGS_URL
        params: Optional[Dict[str, Any]] = {"filter[entity.identifier]": lei, "page[size]": ESEF_PAGE_SIZE}
        while url:
            page = self._get_json(url, params)
            filings.extend(_filing(item) for item in page.get("data") or [])
            following = (page.get("links") or {}).get("next")
            url = (ESEF_BASE_URL + following if following and following.startswith("/") else following) or None
            params = None                    # the next link carries the query
        return filings

    def search_entities(self, pattern: str) -> List[Tuple[str, str]]:
        """(LEI, name) of the entities whose name matches `pattern` (SQL ILIKE: '%' any text), at most a page."""
        query = json.dumps([{"name": "name", "op": "ilike", "val": pattern}])
        page = self._get_json(ESEF_ENTITIES_URL, {"filter": query, "page[size]": ESEF_PAGE_SIZE})
        return [(str((item.get("attributes") or {}).get("identifier") or ""), str((item.get("attributes") or {}).get("name") or ""))
                for item in page.get("data") or [] if (item.get("attributes") or {}).get("identifier")]

    def fetch_report(self, filing: EsefFiling) -> Dict[str, Any]:
        """The report's xBRL-JSON (facts keyed by id, each with value and dimensions)."""
        report = self._get_json(filing.json_url)
        if not isinstance(report, dict):
            raise EsefRequestError(f"filings.xbrl.org returned no report object for {filing.fxo_id}")
        return report


def _retry_after(response: Any, attempt: int) -> float:
    try:
        wait = float((getattr(response, "headers", None) or {}).get("Retry-After") or 0)
    except ValueError:
        wait = 0.0
    return min(wait or 10.0 * (attempt + 1), ESEF_MAX_RETRY_WAIT)
