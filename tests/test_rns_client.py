"""RnsClient: a listing's final-results announcements, paged and cached; errors typed (offline, fake session)."""

import pytest
import requests

import clients.rns_client as rns_client
from clients.rns_client import RnsAnnouncement, RnsClient, RnsRequestError

SITE = "https://www.investegate.co.uk"


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code, self.content = status_code, text.encode("utf-8")


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, headers=None, timeout=None):
        self.calls.append((url, headers))
        route = self.routes.get(url)
        if isinstance(route, Exception):
            raise route
        return route or FakeResponse(404)


def _link(slug, number):
    return f'<a href="{SITE}/announcement/rns/braime-group--bmto/{slug}/{number}">x</a>'


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(rns_client.time, "sleep", lambda s: None)


def _client(tmp_path, routes):
    client = RnsClient(cache_dir=str(tmp_path))
    client.session = FakeSession(routes)
    return client


def test_final_results_are_listed_newest_first_across_pages(tmp_path):
    sidebar = f'<a href="{SITE}/announcement/rns/galliford-try--gfrd/final-results/99">x</a>'
    routes = {f"{SITE}/company/BMTO?page=1": FakeResponse(200, sidebar + _link("final-results", 100) + _link("interim-results", 101)
                                                         + _link("holding-s-in-company", 102) + '<a href="?page=2">2</a>'),
              f"{SITE}/company/BMTO?page=2": FakeResponse(200, _link("annual-results-for-the-year-ended-31-dec", 50))}
    client = _client(tmp_path, routes)
    assert [a.announcement_id for a in client.results_announcements("bmto")] == [100, 50]
    assert all(h["User-Agent"].startswith("StockDataAnalyser") for _, h in client.session.calls)


def test_an_announcement_is_read_once_then_from_the_cache(tmp_path):
    url = f"{SITE}/announcement/rns/x/final-results/100"
    client = _client(tmp_path, {url: FakeResponse(200, "<p>£ results</p>")})
    announcement = RnsAnnouncement(100, url)
    assert client.fetch_announcement(announcement) == "<p>£ results</p>"
    client.session.routes = {}
    assert client.fetch_announcement(announcement) == "<p>£ results</p>" and len(client.session.calls) == 1


def test_an_unusable_symbol_or_unknown_company_has_no_announcements(tmp_path):
    client = _client(tmp_path, {})
    assert client.results_announcements("BT/A") == [] and client.session.calls == []
    assert client.results_announcements("ZZZZ") == []


@pytest.mark.parametrize("route", [FakeResponse(500), requests.exceptions.ConnectionError("down")])
def test_failures_raise_a_typed_error(tmp_path, route):
    with pytest.raises(RnsRequestError):
        _client(tmp_path, {f"{SITE}/company/BMTO?page=1": route}).results_announcements("BMTO")
