"""EsefClient (filings.xbrl.org): listing by LEI with paging, one listing per report, pacing and 429 (offline)."""

import pytest
import requests

import clients.esef_client as esef_client
from clients.esef_client import EsefClient, EsefFiling, EsefRateLimitError, EsefRequestError, select_reports
from config.esef_config import ESEF_USER_AGENT

LEI = "2138002P5RNKC5W2JZ46"
BASE = "https://filings.xbrl.org"


def _item(end, country="GB", version=0, json_url="/x.json", errors=0, added="2025-05-01 00:00:00"):
    return {"type": "filing", "attributes": {
        "fxo_id": f"{LEI}-{end}-ESEF-{country}-{version}", "period_end": end, "country": country,
        "json_url": json_url, "date_added": added, "error_count": errors}}


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None, bad_json=False):
        self.status_code, self._payload, self.headers, self._bad_json = status_code, payload, headers or {}, bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params, headers))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _client(*responses):
    client = EsefClient()
    client.session = FakeSession(responses)
    return client


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    calls = []
    monkeypatch.setattr(esef_client.time, "sleep", calls.append)
    return calls


def test_filings_are_listed_by_lei_across_pages_with_the_neutral_user_agent():
    client = _client(
        FakeResponse(200, {"data": [_item("2024-02-24")], "links": {"next": "/api/filings?page%5Bnumber%5D=2"}}),
        FakeResponse(200, {"data": [_item("2025-02-22", json_url="")], "links": {}}))
    filings = client.fetch_filings(LEI)
    assert [f.period_end for f in filings] == ["2024-02-24", "2025-02-22"]
    assert filings[0].json_url == BASE + "/x.json" and filings[1].json_url == ""
    (url1, params1, headers1), (url2, params2, _) = client.session.calls
    assert url1 == BASE + "/api/filings" and params1["filter[entity.identifier]"] == LEI
    assert url2 == BASE + "/api/filings?page%5Bnumber%5D=2" and params2 is None
    assert headers1["User-Agent"] == ESEF_USER_AGENT and "@example.invalid" in ESEF_USER_AGENT


def test_one_listing_per_report_fewest_errors_then_newest_version():
    filings = [esef_client._filing(i) for i in (
        _item("2022-12-31", "IT"), _item("2022-12-31", "LU", errors=2),         # same report, two countries
        _item("2023-12-31", "IT", version=0), _item("2023-12-31", "IT", version=1),   # refiled
        _item("2024-12-31", json_url=""),                                       # no xBRL-JSON
        {"attributes": {"fxo_id": f"{LEI}-2021-12-31-UKSEF-GB-0", "period_end": "2021-12-31", "json_url": "/y.json"}})]
    chosen = select_reports(filings)
    assert [(f.period_end, f.country, f.version) for f in chosen] == [("2022-12-31", "IT", 0), ("2023-12-31", "IT", 1)]


def test_requests_are_paced(sleeps, monkeypatch):
    clock = iter([100.0, 100.0, 100.2, 100.2, 100.2])
    monkeypatch.setattr(esef_client.time, "monotonic", lambda: next(clock))
    client = _client(FakeResponse(200, {"data": []}), FakeResponse(200, {"data": []}))
    client.fetch_filings(LEI)
    client.fetch_filings(LEI)
    assert sleeps and sleeps[-1] == pytest.approx(0.8)


def test_429_waits_the_servers_retry_after_then_succeeds(sleeps):
    client = _client(FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200, {"facts": {}}))
    report = client.fetch_report(EsefFiling("id", "2024-12-31", "FR", BASE + "/r.json", "", 0))
    assert report == {"facts": {}} and 7.0 in sleeps


def test_429_that_persists_raises_a_rate_limit_error(sleeps):
    client = _client(*[FakeResponse(429, headers={"Retry-After": "999"})] * 3)
    with pytest.raises(EsefRateLimitError):
        client.fetch_filings(LEI)
    assert max(sleeps) == 60.0                       # capped wait


@pytest.mark.parametrize("response, message", [
    (FakeResponse(500), "status 500"),
    (FakeResponse(200, bad_json=True), "invalid JSON"),
    (requests.exceptions.RequestException("boom"), "boom"),
    (FakeResponse(200, ["not", "a", "report"]), "no report object"),
])
def test_failures_raise_request_errors(response, message):
    with pytest.raises(EsefRequestError, match=message):
        _client(response).fetch_report(EsefFiling("id", "2024-12-31", "FR", BASE + "/r.json", "", 0))
