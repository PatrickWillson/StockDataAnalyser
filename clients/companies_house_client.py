"""
Companies House public data API and Document API (config/companies_house_config.py): a company's accounts filings and
each filing's PDF, cached on disk (data/cache/companies_house, gitignored). The key (COMPANIES_HOUSE_API_KEY) is the
basic-auth user name and never appears in URLs, errors or logs. Requests are at least COMPANIES_HOUSE_MIN_REQUEST_INTERVAL
apart; a 429 waits COMPANIES_HOUSE_RATE_LIMIT_WAIT and retries (twice).
"""

import os
import time
from dataclasses import dataclass
from typing import List, Optional

import requests

from config.companies_house_config import (COMPANIES_HOUSE_API_URL, COMPANIES_HOUSE_CACHE_DIR,
                                           COMPANIES_HOUSE_MIN_REQUEST_INTERVAL, COMPANIES_HOUSE_RATE_LIMIT_WAIT,
                                           COMPANIES_HOUSE_USER_AGENT)
from core.errors import DataSourceError

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CompaniesHouseRequestError(DataSourceError):
    """Companies House could not be read (the key is never in the message)."""


@dataclass(frozen=True)
class AccountsFiling:
    """One accounts filing (type AA): its year end, page count and document."""
    transaction_id: str
    made_up_date: str                    # the accounts' year end (ISO date)
    description: str                     # e.g. 'accounts-with-accounts-type-group'
    pages: Optional[int]
    document_metadata_url: str

    @property
    def group(self) -> bool:
        """A group's consolidated accounts (else one company's own)."""
        return "group" in self.description

    @property
    def annual(self) -> bool:
        """Annual accounts: not interim or initial accounts (filed to justify a dividend) and not a dormant company's."""
        return not any(kind in self.description for kind in ("interim", "initial", "dormant"))


class CompaniesHouseClient:
    """A company's accounts filings and their PDFs."""

    def __init__(self, api_key: str, cache_dir: Optional[str] = None):
        if not api_key or not api_key.strip():
            raise ValueError("A Companies House API key is required")
        self._key = api_key.strip()
        self.cache_dir = cache_dir or os.path.join(REPO_ROOT, COMPANIES_HOUSE_CACHE_DIR)
        self.session = requests.Session()
        self._last_request = 0.0

    def _get(self, url: str, accept: Optional[str] = None, params: Optional[dict] = None):
        headers = {"User-Agent": COMPANIES_HOUSE_USER_AGENT, **({"Accept": accept} if accept else {})}
        for attempt in range(3):
            wait = COMPANIES_HOUSE_MIN_REQUEST_INTERVAL - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                response = self.session.get(url, params=params, headers=headers, auth=(self._key, ""), timeout=120)
            except requests.exceptions.RequestException as e:
                raise CompaniesHouseRequestError(f"Companies House request failed: {type(e).__name__}") from None
            finally:
                self._last_request = time.monotonic()
            if response.status_code != 429:
                return response
            time.sleep(COMPANIES_HOUSE_RATE_LIMIT_WAIT)
        raise CompaniesHouseRequestError("Companies House rate limit reached (HTTP 429)")

    def accounts_filings(self, company_number: str) -> List[AccountsFiling]:
        """The company's accounts filings with a year end, newest first ([] for an unknown company)."""
        response = self._get(f"{COMPANIES_HOUSE_API_URL}/company/{company_number}/filing-history",
                             params={"category": "accounts", "items_per_page": 100})
        if response.status_code == 404:
            return []
        if response.status_code in (401, 403):
            raise CompaniesHouseRequestError(f"Companies House rejected the API key (HTTP {response.status_code})")
        if response.status_code != 200:
            raise CompaniesHouseRequestError(f"Companies House returned status {response.status_code}")
        filings = []
        for item in response.json().get("items") or []:
            made_up = (item.get("description_values") or {}).get("made_up_date")
            link = (item.get("links") or {}).get("document_metadata")
            if item.get("type") == "AA" and made_up and link:
                filings.append(AccountsFiling(item.get("transaction_id", ""), made_up, item.get("description", ""),
                                              item.get("pages"), link))
        return sorted(filings, key=lambda f: f.made_up_date, reverse=True)

    def fetch_pdf(self, company_number: str, filing: AccountsFiling) -> Optional[str]:
        """The filing's PDF, cached for good; None when Companies House has no PDF for it."""
        path = os.path.join(self.cache_dir, company_number, f"{filing.transaction_id}.pdf")
        if os.path.exists(path):
            return path
        response = self._get(filing.document_metadata_url + "/content", accept="application/pdf")
        if response.status_code != 200 or not response.content.startswith(b"%PDF"):
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(response.content)
        return path
