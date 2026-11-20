"""
Companies House public data API and Document API (config/companies_house_config.py): a company's accounts filings and
each filing's PDF, cached on disk (data/cache/companies_house, gitignored). The key (COMPANIES_HOUSE_API_KEY) is the
basic-auth user name and never appears in URLs, errors or logs. Requests are at least COMPANIES_HOUSE_MIN_REQUEST_INTERVAL
apart; a 429 waits COMPANIES_HOUSE_RATE_LIMIT_WAIT and retries, and a timeout or dropped connection retries after a
short wait (three attempts in all).
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

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
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                self._last_request = time.monotonic()
                if attempt == 2:
                    raise CompaniesHouseRequestError(f"Companies House request failed: {type(e).__name__}") from None
                time.sleep(COMPANIES_HOUSE_MIN_REQUEST_INTERVAL * 5)     # a stalled connection: wait, then retry
                continue
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

    def company_number(self, *names: str) -> Optional[str]:
        """The company number of the one active public limited company matching the listing's names (Yahoo's long
        and short names, in order): a name ending 'plc' matched exactly (normalised: case, punctuation, 'public limited
        company' = 'plc', '&' = 'and', a leading or trailing 'the'), else a name of 25 characters or more matched as
        the start of the company's (Yahoo cuts short names at 31: 'BRITISH & AMERICAN INVESTMENT T'). None when none or
        more than one matches. The overlap check against the listing's figures rejects a wrong company anyway."""
        plcs: Dict[str, str] = {}                        # company number -> normalised title, active plcs found
        for query in dict.fromkeys(SHARE_CLASS.sub("", n).strip() for n in names if n and n.strip()):
            response = self._get(f"{COMPANIES_HOUSE_API_URL}/search/companies", params={"q": query, "items_per_page": 50})
            if response.status_code in (401, 403):
                raise CompaniesHouseRequestError(f"Companies House rejected the API key (HTTP {response.status_code})")
            if response.status_code != 200:
                continue
            for item in response.json().get("items") or []:
                if item.get("company_status") == "active" and item.get("company_type") == "plc":
                    plcs[item.get("company_number")] = normalise_name(item.get("title", ""))
        for name in names:
            wanted = normalise_name(SHARE_CLASS.sub("", name or ""))
            if wanted.endswith(" plc"):
                found = {number for number, title in plcs.items() if title == wanted}
            elif len(wanted) >= 25:
                found = {number for number, title in plcs.items() if title.startswith(wanted)}
            else:
                continue
            if found:
                return found.pop() if len(found) == 1 else None
        return None

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


SHARE_CLASS = re.compile(r"\s+(?:ord|ords|ordinary(?: shares?)?|shs)\.?$", re.I)   # Yahoo: 'British & American Ord'


def normalise_name(name: str) -> str:
    """A company name for comparison: lower case, '&' as 'and', no punctuation, 'public limited company' and 'p.l.c.'
    as 'plc', a leading or trailing 'the' dropped ('... COMPANY (THE)'), single spaces."""
    text = re.sub(r"\bp\s*\.?\s*l\s*\.?\s*c\b\.?", "plc", name.lower().replace("&", " and "))
    text = re.sub(r"\bpublic limited company\b", "plc", text)
    text = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()
    return re.sub(r"^the |\bthe$", "", text).strip()
