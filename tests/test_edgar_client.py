"""EdgarClient: SEC fair-access headers and throttling, ticker -> CIK, typed errors (offline)."""

import pytest
import requests

import clients.edgar_client as edgar_client
from clients.edgar_client import (EdgarAuthError, EdgarClient, EdgarRateLimitError, EdgarRequestError,
                                  sec_symbol)
from core.errors import TickerNotCoveredError

UA = "StockDataAnalyser Test tester@example.invalid"
INDEX = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
         "1": {"cik_str": 1067983, "ticker": "BRK-B", "title": "BERKSHIRE HATHAWAY INC"},
         "2": {"cik_str": 2115436, "ticker": "XOM", "title": "ExxonMobil Holdings Corp"}}


class FakeResponse:
    def __init__(self, status_code, payload=None, bad_json=False):
        self.status_code, self._payload, self._bad_json = status_code, payload, bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, headers))
        route = self.routes.get(url)
        if isinstance(route, Exception):
            raise route
        return route or FakeResponse(404)


def _client(routes, **kwargs):
    client = EdgarClient(UA, **kwargs)
    client.session = FakeSession(routes)
    return client


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(edgar_client.time, "sleep", sleeps.append)
    return sleeps


INDEX_URL = "https://www.sec.gov/files/company_tickers.json"


def test_user_agent_needs_a_contact_email():
    with pytest.raises(ValueError, match="contact email"):
        EdgarClient("StockDataAnalyser")
    with pytest.raises(ValueError):
        EdgarClient("")


@pytest.mark.parametrize("ticker, symbol", [("AAPL.US", "AAPL"), ("brk.b.US", "BRK-B"), ("BRK-B.US", "BRK-B"),
                                            ("aapl", "AAPL")])
def test_sec_symbol(ticker, symbol):
    assert sec_symbol(ticker) == symbol


def test_resolves_cik_with_declared_user_agent_and_fetches_the_index_once():
    client = _client({INDEX_URL: FakeResponse(200, INDEX)})
    assert client.resolve_cik("AAPL.US") == "0000320193"
    assert client.resolve_cik("BRK.B.US") == "0001067983"
    assert len(client.session.calls) == 1
    assert client.session.calls[0][1]["User-Agent"] == UA


def test_reorganised_company_resolves_to_its_current_cik_and_lists_predecessors():
    client = _client({INDEX_URL: FakeResponse(200, INDEX)}, predecessors={"XOM": ("0000034088",)})
    assert client.resolve_cik("XOM.US") == "0002115436"
    assert client.predecessor_ciks("XOM.US") == ("0000034088",)
    assert client.predecessor_ciks("AAPL.US") == ()


def test_default_predecessors_come_from_config():
    assert EdgarClient(UA).predecessor_ciks("GOOGL.US") == ("0001288776",)
    assert EdgarClient(UA).predecessor_ciks("XOM.US") == ("0000034088",)


def test_unknown_ticker_is_not_covered():
    client = _client({INDEX_URL: FakeResponse(200, INDEX)})
    with pytest.raises(TickerNotCoveredError, match="not in the SEC ticker index"):
        client.resolve_cik("ZZZZ.US")


def test_fetches_facts_and_submissions():
    facts_url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    sub_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    client = _client({facts_url: FakeResponse(200, {"cik": 320193, "facts": {}}),
                      sub_url: FakeResponse(200, {"name": "Apple Inc."})})
    assert client.fetch_company_facts("0000320193") == {"cik": 320193, "facts": {}}
    assert client.fetch_submissions("0000320193")["name"] == "Apple Inc."


@pytest.mark.parametrize("response, error", [
    (FakeResponse(403), EdgarAuthError), (FakeResponse(429), EdgarRateLimitError),
    (FakeResponse(500), EdgarRequestError), (FakeResponse(200, bad_json=True), EdgarRequestError),
    (FakeResponse(404), TickerNotCoveredError),
    (requests.exceptions.ConnectionError("down"), EdgarRequestError),
])
def test_typed_errors(response, error):
    client = _client({"https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json": response})
    with pytest.raises(error):
        client.fetch_company_facts("0000000001")


def test_requests_are_throttled(no_sleep):
    client = _client({INDEX_URL: FakeResponse(200, INDEX)})
    client.resolve_cik("AAPL.US")
    client._ticker_index = None
    client.resolve_cik("AAPL.US")
    assert no_sleep and all(0 < s <= 0.11 for s in no_sleep)
