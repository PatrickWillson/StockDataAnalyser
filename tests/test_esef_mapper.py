"""ESEF xBRL-JSON -> companyfacts (clients/esef_mapper.py), read by edgar_mapper.annual_data. Synthetic reports."""

import pytest

from clients.edgar_mapper import annual_data
from clients.esef_client import EsefFiling
from clients.esef_mapper import _date, _period, _unit, companyfacts, report_facts

LEI = "529900EXAMPLE000LEI0"


def _filing(end, added, country="FR", version=0):
    return EsefFiling(f"{LEI}-{end}-ESEF-{country}-{version}", end, country, f"https://x/{end}.json", added, 0)


def _fact(concept, period, value, unit="iso4217:EUR", **dimensions):
    return {"value": str(value), "dimensions": {"concept": concept, "entity": f"scheme:{LEI}", "period": period,
                                                **({"unit": unit} if unit else {}), **dimensions}}


def _report(*facts):
    return {"documentInfo": {"documentType": "https://xbrl.org/2021/xbrl-json"},
            "facts": {f"f{i}": fact for i, fact in enumerate(facts)}}


FY24 = "2024-01-01T00:00:00/2025-01-01T00:00:00"
FY23 = "2023-01-01T00:00:00/2024-01-01T00:00:00"
END24, END23 = "2025-01-01T00:00:00", "2024-01-01T00:00:00"

ANNUAL_2024 = _report(
    _fact("ifrs-full:Revenue", FY24, 1000e6), _fact("ifrs-full:Revenue", FY23, 900e6),
    _fact("ifrs-full:ProfitLossAttributableToOwnersOfParent", FY24, 110e6),
    _fact("ifrs-full:ProfitLossAttributableToOwnersOfParent", FY23, 95e6),
    _fact("ifrs-full:BasicEarningsLossPerShare", FY24, 1.10, "iso4217:EUR/xbrli:shares"),
    _fact("ifrs-full:Assets", END24, 2000e6), _fact("ifrs-full:Assets", END23, 1900e6),
    _fact("ifrs-full:EquityAttributableToOwnersOfParent", END24, 800e6),
    _fact("ifrs-full:NumberOfSharesOutstanding", END24, 100e6, "xbrli:shares"),
    # not converted: a dimension, the company's own tag, a text fact, a non-numeric value
    _fact("ifrs-full:Revenue", FY24, 600e6, **{"ifrs-full:SegmentsAxis": "x:EuropeMember"}),
    _fact("example:AdjustedProfit", FY24, 130e6),
    _fact("ifrs-full:DisclosureOfGeneralInformation", FY24, "text", unit=None, language="en"),
    _fact("ifrs-full:Assets", END24, "n/a"),
)


@pytest.mark.parametrize("text, expected", [("2025-01-01T00:00:00", "2024-12-31"), ("2024-03-01T00:00:00", "2024-02-29"),
                                            ("2024-12-31T23:59:59", "2024-12-31")])
def test_a_midnight_period_end_is_the_day_before(text, expected):
    assert _date(text) == expected


def test_periods_and_units():
    assert _period(FY24) == ("2024-01-01", "2024-12-31")
    assert _period(END24) == (None, "2024-12-31")
    assert [_unit(u) for u in ("iso4217:EUR", "iso4217:GBP/xbrli:shares", "xbrli:shares", "xbrli:pure", None)] \
        == ["EUR", "GBP/shares", "shares", None, None]


def test_an_annual_report_becomes_companyfacts_rows():
    report = report_facts(_filing("2024-12-31", "2025-04-10 00:00:00"), ANNUAL_2024)
    assert report.annual and report.period_end == "2024-12-31"
    ifrs = report.facts["facts"]["ifrs-full"]
    assert set(ifrs) == {"Revenue", "ProfitLossAttributableToOwnersOfParent", "BasicEarningsLossPerShare", "Assets",
                         "EquityAttributableToOwnersOfParent", "NumberOfSharesOutstanding"}
    assert ifrs["Revenue"]["units"]["EUR"][0] == {"start": "2024-01-01", "end": "2024-12-31", "val": 1000e6,
                                                  "filed": "2025-04-10", "form": "ESEF",
                                                  "accn": f"{LEI}-2024-12-31-ESEF-FR-0"}
    assert ifrs["Assets"]["units"]["EUR"][0]["end"] == "2024-12-31" and "start" not in ifrs["Assets"]["units"]["EUR"][0]
    assert "EUR/shares" in ifrs["BasicEarningsLossPerShare"]["units"]


def test_the_mapper_reads_converted_reports_with_its_usual_rules():
    restating = _report(_fact("ifrs-full:ProfitLossAttributableToOwnersOfParent", "2025-01-01T00:00:00/2026-01-01T00:00:00", 120e6),
                        _fact("ifrs-full:ProfitLossAttributableToOwnersOfParent", FY24, 108e6),      # restated
                        _fact("ifrs-full:Assets", "2026-01-01T00:00:00", 2100e6))
    reports = [report_facts(_filing("2024-12-31", "2025-04-10 00:00:00"), ANNUAL_2024),
               report_facts(_filing("2025-12-31", "2026-04-09 00:00:00"), restating)]
    facts, notes = companyfacts(reports)
    data = annual_data(facts, eps_implied_shares=True, source="ESEF")
    assert data.currency == "EUR" and notes == []
    assert [(r.period_end, r.net_income) for r in data.income_statements] == [
        ("2025-12-31", 120e6), ("2024-12-31", 108e6), ("2023-12-31", 95e6)]
    assert any(n.startswith("ESEF: restated in later filings") and "110M -> 108M" in n for n in data.notes)
    assert data.balance_sheets[1].shares_outstanding == 100e6


def test_an_interim_report_is_left_out_and_noted():
    half_year = _report(_fact("ifrs-full:ProfitLossAttributableToOwnersOfParent", "2024-01-01T00:00:00/2024-07-01T00:00:00", 50e6),
                        # its comparative full year ends before its own period end
                        _fact("ifrs-full:ProfitLossAttributableToOwnersOfParent", FY23, 95e6),
                        _fact("ifrs-full:Assets", "2024-07-01T00:00:00", 1950e6))
    report = report_facts(_filing("2024-06-30", "2024-09-01 00:00:00"), half_year)
    assert not report.annual and report.period_end == "2024-06-30"
    facts, notes = companyfacts([report])
    assert facts["facts"]["ifrs-full"] == {}
    assert notes == ["ESEF: interim or undated reports not used (indexed period ends 2024-06-30); annual reports only"]


def test_figures_dated_after_the_year_end_do_not_make_an_annual_report_interim():
    """Unilever: two facts are zero-day periods on the report's own date (2023-02-09)."""
    report = report_facts(_filing("2023-02-09", "2023-03-15 00:00:00"), _report(
        *ANNUAL_2024["facts"].values(), _fact("ifrs-full:SharesRepurchased", "2025-02-09T00:00:00/2025-02-10T00:00:00", 5)))
    assert report.annual and report.period_end == "2024-12-31"


def test_the_facts_date_a_report_not_the_index():
    """Tenaris: its FY2023 report indexed as 2024-04-30."""
    report = report_facts(_filing("2024-04-30", "2024-05-10 00:00:00"), ANNUAL_2024)
    assert report.annual and report.period_end == "2024-12-31"


def test_one_report_indexed_twice_is_used_once():
    first = report_facts(_filing("2024-12-31", "2025-04-10 00:00:00"), ANNUAL_2024)
    second = report_facts(_filing("2025-04-30", "2025-05-02 00:00:00", "LU"), ANNUAL_2024)
    facts, _ = companyfacts([first, second])
    rows = facts["facts"]["ifrs-full"]["Revenue"]["units"]["EUR"]
    assert len(rows) == 2 and {r["accn"] for r in rows} == {second.filing.fxo_id}


def test_a_report_without_figures_is_not_annual():
    report = report_facts(_filing("2024-12-31", ""), _report(_fact("ifrs-full:Assets", END24, 10.0),
                                                             _fact("ifrs-full:CashFlowsFromUsedInOperatingActivities", FY24, 3.0)))
    assert not report.annual and report.period_end is None
