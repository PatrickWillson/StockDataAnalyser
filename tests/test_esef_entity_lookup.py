"""EsefEntityLookup: home listing name -> ESEF filer on filings.xbrl.org (offline fakes)."""

import datetime as dt

import pytest

from clients.esef_client import EsefFiling
from clients.esef_entity_lookup import EsefEntityLookup, search_patterns
from core.errors import TickerNotCoveredError

TODAY = dt.date(2026, 11, 8)


def _filing(lei, end, added):
    return EsefFiling(f"{lei}-{end}-ESEF-SE-0", end, "SE", f"https://x/{lei}/{end}.json", added, 0)


class FakeClient:
    def __init__(self, entities, filings):
        self.entities, self.filings, self.searches = entities, filings, []

    def search_entities(self, pattern):
        self.searches.append(pattern)
        words = pattern.strip("%").split("%")
        return [(lei, name) for lei, name in self.entities
                if all(w in name.lower() for w in words) and _in_order(name.lower(), words)]

    def fetch_filings(self, lei):
        return self.filings.get(lei, [])


def _in_order(text, words):
    position = 0
    for word in words:
        position = text.find(word, position)
        if position < 0:
            return False
        position += len(word)
    return True


RECENT = "2026-03-20 00:00:00"
VOLVO = ("549300HGV012CNC8JD22", "Aktiebolaget Volvo")
VOLVO_CARS = ("5299000EAMGGBEYP7J33", "Volvo Car AB")
FILINGS = {VOLVO[0]: [_filing(VOLVO[0], "2025-12-31", RECENT), _filing(VOLVO[0], "2024-12-31", "2025-03-20 00:00:00")],
           VOLVO_CARS[0]: [_filing(VOLVO_CARS[0], "2025-12-31", RECENT)]}


def test_search_patterns():
    assert search_patterns("Associated British Foods plc") == ["%associated%british%foods%", "%associated%"]
    assert search_patterns("LVMH Moët Hennessy - Louis Vuitton, Société Européenne") == [
        "%lvmh%moet%hennessy%louis%vuitton%", "%lvmh%", "%hennessy%"]
    assert search_patterns("Eni S.p.A.") == ["%eni%s%p%a%"]             # specific: "%eni%" alone would fill a page
    assert search_patterns("plc") == []


def test_the_entity_named_exactly_like_the_listing_is_chosen_over_a_longer_name():
    entity = EsefEntityLookup(FakeClient([VOLVO, VOLVO_CARS], FILINGS), today=TODAY).resolve("VOLV-B.ST", "AB Volvo (publ)")
    assert (entity.lei, entity.name) == VOLVO
    assert [f.period_end for f in entity.reports] == ["2024-12-31", "2025-12-31"]


def test_a_name_with_extra_words_falls_back_to_shorter_searches():
    lvmh = ("IOG4E947OATN0KJYSD45", "LVMH MOET HENNESSY LOUIS VUITTON")
    client = FakeClient([lvmh], {lvmh[0]: [_filing(lvmh[0], "2025-12-31", RECENT)]})
    entity = EsefEntityLookup(client, today=TODAY).resolve("MC.PA", "LVMH Moët Hennessy - Louis Vuitton, Société Européenne")
    assert entity.lei == lvmh[0]


def test_two_entities_neither_named_exactly_are_ambiguous():
    client = FakeClient([("A", "Volvo Car AB"), ("B", "Volvo Trucks AB")],
                        {"A": [_filing("A", "2025-12-31", RECENT)], "B": [_filing("B", "2025-12-31", RECENT)]})
    with pytest.raises(TickerNotCoveredError, match="more than one ESEF filer.*ESEF_ENTITY_LEIS"):
        EsefEntityLookup(client, today=TODAY).resolve("X.ST", "Volvo AB")


def test_an_entity_without_a_recent_report_gives_no_dossier():
    sap = ("529900D6BF99LW9R2E68", "SAP SE")
    client = FakeClient([sap], {sap[0]: [_filing(sap[0], "2021-12-31", "2022-03-10 00:00:00")]})
    with pytest.raises(TickerNotCoveredError, match="no ESEF report added within 18 months"):
        EsefEntityLookup(client, today=TODAY).resolve("SAP.XETRA", "SAP SE")


def test_no_matching_entity_names_the_coverage_gaps():
    with pytest.raises(TickerNotCoveredError, match="Germany, Ireland or AIM"):
        EsefEntityLookup(FakeClient([("Z", "Yorkshire Water")], {}), today=TODAY).resolve("YU.LSE", "Yü Group PLC")


def test_a_name_that_only_contains_the_words_is_not_a_match():
    client = FakeClient([("Z", "Volvofinans Bank AB")], {"Z": [_filing("Z", "2025-12-31", RECENT)]})
    with pytest.raises(TickerNotCoveredError, match="no ESEF filer named like"):
        EsefEntityLookup(client, today=TODAY).resolve("VOLV-B.ST", "AB Volvo (publ)")


def test_config_settles_a_company_by_lei():
    client = FakeClient([], FILINGS)
    entity = EsefEntityLookup(client, overrides={"VOLV-B.ST": VOLVO[0]}, today=TODAY).resolve("VOLV-B.ST", "AB Volvo")
    assert entity.lei == VOLVO[0] and client.searches == []


def test_no_name_gives_no_dossier():
    with pytest.raises(TickerNotCoveredError, match="no company name"):
        EsefEntityLookup(FakeClient([], {}), today=TODAY).resolve("X.ST", None)
