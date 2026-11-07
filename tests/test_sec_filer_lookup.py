"""SEC filer lookup for non-US home listings (clients/sec_filer_lookup.py). Synthetic Yahoo and SEC data."""

import datetime as dt

import pytest

from clients.sec_filer_lookup import SecFilerLookup, latest_annual_report, names_match
from core.errors import TickerNotCoveredError

TODAY = dt.date(2026, 11, 7)


def submissions(*filings, name="Company"):
    return {"name": name, "filings": {"recent": {"form": [f for f, _ in filings], "filingDate": [d for _, d in filings]}}}


class FakeYahoo:
    def __init__(self, listings):
        self.listings = listings

    def search_us_listings(self, name):
        return self.listings.get(name, [])


class FakeEdgar:
    def __init__(self, index, subs):
        self.index, self.subs = index, subs

    def filer_for_symbol(self, symbol):
        return self.index.get(symbol)

    def fetch_submissions(self, cik):
        return self.subs[cik]


def lookup(listings, index, subs, overrides=None):
    return SecFilerLookup(FakeEdgar(index, subs), FakeYahoo(listings), overrides=overrides or {}, today=TODAY)


BP = {"BP p.l.c.": [("BP", "NYQ", "BP p.l.c."), ("BPAQF", "PNK", "BP p.l.c."), ("BPH", "PCX", "BP p.l.c. ADRhedged")]}
BP_INDEX = {"BP": ("0000313807", "BP PLC"), "BPAQF": ("0000313807", "BP PLC")}
BP_SUBS = {"0000313807": submissions(("6-K", "2026-10-01"), ("20-F", "2026-03-20"), ("20-F", "2025-03-21"))}


def test_home_listing_resolves_to_its_sec_filer_by_name():
    filer = lookup(BP, BP_INDEX, BP_SUBS).resolve("BP.LSE", "BP p.l.c.")
    assert (filer.cik, filer.sec_name, filer.annual_form, filer.annual_filed) == ("0000313807", "BP PLC", "20-F", "2026-03-20")
    assert filer.us_symbols == ("BP", "BPAQF")


def test_a_us_listing_of_another_name_is_not_matched():
    # Yu Group's search returns Big Yellow Group's OTC line
    yu = {"Yü Group PLC": [("BYLOF", "PNK", "Big Yellow Group Plc")]}
    with pytest.raises(TickerNotCoveredError, match="no SEC filer found"):
        lookup(yu, {"BYLOF": ("0000000001", "BIG YELLOW")}, {}).resolve("YU.LSE", "Yü Group PLC")


def test_otc_lines_outside_the_sec_index_are_not_filers():
    tesco = {"Tesco PLC": [("TSCDY", "OQX", "Tesco PLC"), ("TSCDF", "OQX", "Tesco PLC")]}
    with pytest.raises(TickerNotCoveredError, match="no SEC filer found"):
        lookup(tesco, {}, {}).resolve("TSCO.LSE", "Tesco PLC")


def test_a_filer_without_a_recent_annual_report_is_not_used():
    gaw = {"Games Workshop Group PLC": [("GMWKF", "PNK", "Games Workshop Group PLC")]}
    subs = {"0000000002": submissions(("F-6", "2019-05-01"))}
    with pytest.raises(TickerNotCoveredError, match="no 20-F, 40-F or 10-K within 18 months"):
        lookup(gaw, {"GMWKF": ("0000000002", "GAMES WORKSHOP GROUP PLC")}, subs).resolve("GAW.LSE", "Games Workshop Group PLC")


def test_two_current_filers_give_no_dossier_and_name_the_candidates():
    rio = {"Rio Tinto Group": [("RIO", "NYQ", "Rio Tinto Group"), ("RTNTF", "PNK", "Rio Tinto Group")]}
    index = {"RIO": ("0000863064", "RIO TINTO PLC"), "RTNTF": ("0000887028", "RIO TINTO LTD")}
    subs = {"0000863064": submissions(("20-F", "2026-02-20")), "0000887028": submissions(("20-F", "2026-02-20"))}
    with pytest.raises(TickerNotCoveredError, match="more than one SEC filer.*RIO TINTO PLC.*RIO TINTO LTD"):
        lookup(rio, index, subs).resolve("RIO.XETRA", "Rio Tinto Group")
    filer = lookup(rio, index, subs, overrides={"RIO.LSE": "0000863064"}).resolve("RIO.LSE", "Rio Tinto Group")
    assert filer.cik == "0000863064" and filer.us_symbols == ()


def test_names_match_ignores_legal_forms_and_listing_words():
    assert names_match("Vodafone Group Public Limited Company", "Vodafone Group Public Ltd")
    assert names_match("Telefonaktiebolaget LM Ericsson (publ)", "Telefonaktiebolaget LM Ericsson")
    assert names_match("Toyota Motor Corporation", "Toyota Motor Corp ADR")
    assert not names_match("Capital Limited", "Burford Capital Limited")
    assert not names_match("Hilton Food Group plc", "Hilton Worldwide Holdings Inc")


def test_latest_annual_report_takes_the_newest_annual_form():
    subs = submissions(("6-K", "2026-08-01"), ("40-F", "2026-03-01"), ("20-F", "2024-03-01"))
    assert latest_annual_report(subs) == ("40-F", "2026-03-01")
    assert latest_annual_report(submissions(("6-K", "2026-08-01"))) is None


def test_a_failed_yahoo_search_is_not_reported_as_no_filer():
    class FailingYahoo:
        def search_us_listings(self, name):
            return None
    lookup = SecFilerLookup(FakeEdgar({}, {}), FailingYahoo(), overrides={}, today=TODAY)
    with pytest.raises(TickerNotCoveredError, match="search failed.*try again"):
        lookup.resolve("2330.TW", "Taiwan Semiconductor Manufacturing Company Limited")
