"""EulerpoolClient: key only as a header, listing found by symbol or search with a name check, errors (offline)."""

import pytest
import requests

import clients.eulerpool_client as eulerpool_client
from clients.eulerpool_client import EulerpoolAuthError, EulerpoolClient, EulerpoolRateLimitError, EulerpoolRequestError

KEY = "secret-test-key"
BASE = "https://api.eulerpool.com/api/1/"


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code, self._payload = status_code, payload

    def json(self):
        if self._payload is ValueError:
            raise ValueError("bad json")
        return self._payload


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, headers))
        route = self.routes.get(url[len(BASE):])
        if isinstance(route, Exception):
            raise route
        return route or FakeResponse(404)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(eulerpool_client.time, "sleep", lambda s: None)


def _client(routes):
    client = EulerpoolClient(KEY)
    client.session = FakeSession(routes)
    return client


GAW = {"isin": "GB0003718474", "name": "Games Workshop Group PLC", "currency": "GBP"}
VOLVO = {"isin": "SE0000115446", "name": "Volvo AB", "currency": "SEK"}


def test_a_key_is_required():
    with pytest.raises(ValueError):
        EulerpoolClient(" ")


def test_the_listing_is_found_by_its_yahoo_symbol_with_the_key_only_in_a_header():
    client = _client({"equity/profile/GAW.L": FakeResponse(200, GAW)})
    assert client.find_profile("GAW.L", "Games Workshop Group PLC") == GAW
    url, headers = client.session.calls[0]
    assert KEY not in url and headers["Authorization"] == f"Bearer {KEY}"


def test_a_share_class_is_tried_with_a_space():
    client = _client({"equity/profile/VOLV%20B.ST": FakeResponse(200, VOLVO)})
    assert client.find_profile("VOLV-B.ST", "AB Volvo (publ)") == VOLVO


def test_a_listing_under_another_name_is_not_used():
    client = _client({"equity/profile/GAW.L": FakeResponse(200, {**GAW, "name": "Gawain Mining Ltd"})})
    assert client.find_profile("GAW.L", "Games Workshop Group PLC") is None


def test_search_is_the_last_resort_and_needs_one_matching_stock():
    search = {"results": [{"name": "Koenig & Bauer AG", "isin": "DE0007193500", "type": "stock"},
                          {"name": "Koenig & Bauer AG", "isin": "XS0000000001", "type": "bond"},
                          {"name": "Bauer AG", "isin": "DE0005168108", "type": "stock"}]}
    profile = {"isin": "DE0007193500", "name": "Koenig & Bauer AG", "currency": "EUR"}
    client = _client({"equity/search?q=KBA.DE": FakeResponse(200, search),
                      "equity/profile/DE0007193500": FakeResponse(200, profile)})
    assert client.find_profile("KBA.DE", "Koenig & Bauer AG") == profile


def test_a_hong_kong_code_is_tried_without_leading_zeros():
    profile = {"isin": "BMG677491539", "name": "Orient Overseas (International) Ltd", "currency": "USD"}
    client = _client({"equity/profile/316.HK": FakeResponse(200, profile)})
    assert client.find_profile("0316.HK", "Orient Overseas (International) Limited") == profile


def test_a_listing_named_with_and_for_ampersand_or_another_word_order_is_used():
    heath = {"isin": "GB0004178710", "name": "Samuel Heath and Sons PLC", "currency": "GBP"}
    itmg = {"isin": "ID1000108509", "name": "Indo Tambangraya Megah Tbk PT", "currency": "USD"}
    client = _client({"equity/profile/HSM.L": FakeResponse(200, heath), "equity/profile/ITMG.JK": FakeResponse(200, itmg)})
    assert client.find_profile("HSM.L", "Samuel Heath & Sons plc") == heath
    assert client.find_profile("ITMG.JK", "PT Indo Tambangraya Megah Tbk") == itmg


def test_a_listing_eulerpool_lacks_is_found_by_the_company_name():
    sixt = {"isin": "DE0007231326", "name": "Sixt SE", "currency": "EUR"}
    search = {"results": [{"name": "Sixt SE", "isin": "DE0007231326", "type": "stock"},
                          {"name": "Evolve S&P/TSX 60 CleanBeta Fund", "isin": "CA30052H1064", "type": "etf"}]}
    client = _client({"equity/search?q=Sixt%20SE": FakeResponse(200, search),
                      "equity/profile/DE0007231326": FakeResponse(200, sixt)})
    assert client.find_profile("SIX3.DE", "Sixt SE") == sixt


def test_a_name_search_with_two_matching_stocks_is_not_used():
    search = {"results": [{"name": "Braime Group PLC", "isin": "GB0001185056", "type": "stock"},
                          {"name": "Braime Group PLC", "isin": "GB0001185270", "type": "stock"}]}
    client = _client({"equity/search?q=Braime%20Group%20PLC": FakeResponse(200, search)})
    assert client.find_profile("BMT.L", "Braime Group PLC") is None


def test_statements_missing_come_back_empty():
    client = _client({"equity/incomestatement/GB0003718474": FakeResponse(200, [{"period": "2025-06-01"}])})
    assert client.fetch_statements("GB0003718474") == {"income": [{"period": "2025-06-01"}], "balance_quarterly": [],
                                                       "cashflow": []}


@pytest.mark.parametrize("response, error", [
    (FakeResponse(401), EulerpoolAuthError), (FakeResponse(429), EulerpoolRateLimitError),
    (FakeResponse(500), EulerpoolRequestError), (FakeResponse(200, ValueError), EulerpoolRequestError),
    (requests.exceptions.RequestException(f"failed {KEY}"), EulerpoolRequestError),
])
def test_failures_raise_typed_errors_without_the_key(response, error):
    with pytest.raises(error) as raised:
        _client({"equity/profile/GAW.L": response}).find_profile("GAW.L", "Games Workshop Group PLC")
    assert KEY not in str(raised.value) and raised.value.__cause__ is None
