"""CompaniesHouseClient: accounts filings and PDFs, the key only as basic auth, cached, errors typed (offline)."""

import pytest
import requests

import clients.companies_house_client as ch_client
from clients.companies_house_client import AccountsFiling, CompaniesHouseClient, CompaniesHouseRequestError

KEY = "secret-test-key"
API = "https://api.company-information.service.gov.uk"


class FakeResponse:
    def __init__(self, status_code, payload=None, content=b""):
        self.status_code, self._payload, self.content = status_code, payload, content

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, headers=None, auth=None, timeout=None):
        self.calls.append((url, params, headers, auth))
        route = self.routes.get(url)
        if isinstance(route, Exception):
            raise route
        if isinstance(route, list):
            return route.pop(0)
        return route or FakeResponse(404)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(ch_client.time, "sleep", lambda s: None)


def _client(tmp_path, routes):
    client = CompaniesHouseClient(KEY, cache_dir=str(tmp_path))
    client.session = FakeSession(routes)
    return client


ITEMS = {"items": [
    {"type": "AA", "transaction_id": "T1", "description": "accounts-with-accounts-type-group", "pages": 82,
     "description_values": {"made_up_date": "2025-12-31"}, "links": {"document_metadata": "https://doc/T1"}},
    {"type": "AA01", "transaction_id": "T2", "links": {"document_metadata": "https://doc/T2"}},
    {"type": "AA", "transaction_id": "T3", "description": "accounts-with-accounts-type-group", "pages": 78,
     "description_values": {"made_up_date": "2024-12-31"}, "links": {"document_metadata": "https://doc/T3"}}]}


def test_accounts_filings_newest_first_with_the_key_only_as_basic_auth(tmp_path):
    client = _client(tmp_path, {f"{API}/company/00488001/filing-history": FakeResponse(200, ITEMS)})
    filings = client.accounts_filings("00488001")
    assert [(f.transaction_id, f.made_up_date) for f in filings] == [("T1", "2025-12-31"), ("T3", "2024-12-31")]
    url, params, headers, auth = client.session.calls[0]
    assert KEY not in url and params["category"] == "accounts" and auth == (KEY, "")


def test_a_pdf_is_downloaded_once_then_from_the_cache(tmp_path):
    filing = AccountsFiling("T1", "2025-12-31", "group", 82, "https://doc/T1")
    client = _client(tmp_path, {"https://doc/T1/content": FakeResponse(200, content=b"%PDF-1.4 scan")})
    path = client.fetch_pdf("00488001", filing)
    assert open(path, "rb").read() == b"%PDF-1.4 scan"
    client.session.routes = {}
    assert client.fetch_pdf("00488001", filing) == path and len(client.session.calls) == 1


def test_a_rate_limited_request_waits_and_retries(tmp_path):
    route = [FakeResponse(429), FakeResponse(200, ITEMS)]
    client = _client(tmp_path, {f"{API}/company/00488001/filing-history": route})
    assert len(client.accounts_filings("00488001")) == 2


@pytest.mark.parametrize("route", [FakeResponse(401), FakeResponse(500),
                                   requests.exceptions.ConnectionError(f"failed {KEY}")])
def test_failures_raise_a_typed_error_without_the_key(tmp_path, route):
    with pytest.raises(CompaniesHouseRequestError) as raised:
        _client(tmp_path, {f"{API}/company/00488001/filing-history": route}).accounts_filings("00488001")
    assert KEY not in str(raised.value)


def test_a_key_is_required():
    with pytest.raises(ValueError):
        CompaniesHouseClient(" ")


@pytest.mark.parametrize("description, group, annual", [
    ("accounts-with-accounts-type-group", True, True), ("accounts-with-accounts-type-full", False, True),
    ("accounts-with-accounts-type-interim", False, False), ("accounts-with-accounts-type-initial", False, False),
    ("accounts-with-accounts-type-dormant", False, False), ("accounts-with-accounts-type-full-group", True, True)])
def test_a_filing_says_whether_it_is_a_groups_accounts_and_whether_it_is_annual(description, group, annual):
    """Maven VCT 3 files full (single-company) accounts each year and interim accounts for its dividends."""
    filing = AccountsFiling("T1", "2025-11-30", description, 40, "https://doc/T1")
    assert (filing.group, filing.annual) == (group, annual)
