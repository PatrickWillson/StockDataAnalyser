"""
SEC EDGAR companyfacts -> annual statement rows (clients/edgar_mapper.py).

Fixtures in tests/fixtures_sec/ are real SEC companyfacts (US-government public data), trimmed to the
concepts the mapper reads. Golden values are from the companies' 10-K filings:
- Apple FY2024 10-K (filed 2024-11-01): https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/
- Southern Co FY2024 10-K (filed 2025-02-20): https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000092122&type=10-K
Splits (date, ratio) are the companies' published stock splits.
"""

import gzip
import json
import os

import pytest

from clients.edgar_mapper import annual_data

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures_sec")
SPLITS = {"AAPL": [("2014-06-09", 7.0), ("2020-08-31", 4.0)], "WMT": [("2024-02-26", 3.0)],
          "HRL": [("2011-02-15", 2.0), ("2016-02-10", 2.0)], "KO": [("2012-08-13", 2.0)]}


def fixture(ticker):
    with gzip.open(os.path.join(FIXTURES, f"{ticker}.json.gz")) as fh:
        return json.loads(fh.read())


def mapped(ticker):
    data = fixture(ticker)
    return annual_data(data["companyfacts"], SPLITS.get(ticker, ()), data["submissions"]["sic"])


def row(rows, end):
    return next(r for r in rows if r.period_end == end)


def test_apple_fy2024_matches_the_10k():
    data = mapped("AAPL")
    income = row(data.income_statements, "2024-09-28")
    balance = row(data.balance_sheets, "2024-09-28")
    assert (income.revenue, income.net_income, income.eps) == (391_035e6, 93_736e6, 6.11)
    assert balance.total_assets == 364_980e6 and balance.total_liabilities == 308_030e6
    assert balance.total_equity == 56_950e6
    assert balance.current_assets == 152_987e6 and balance.current_liabilities == 176_392e6
    assert balance.inventory == 7_286e6
    assert balance.long_term_debt == 85_750e6                    # term debt, non-current
    assert balance.short_term_debt == 9_967e6 + 10_912e6         # commercial paper + term debt, current
    assert balance.shares_outstanding == 15_116_786_000
    assert data.dividends_paid["2024-09-28"] == 15_234e6
    assert data.shares_by_year["2024"] == 15_116_786_000


def test_southern_fy2024_matches_the_10k():
    data = mapped("SO")
    balance = row(data.balance_sheets, "2024-12-31")
    assert (balance.total_assets, balance.total_liabilities, balance.total_equity) == (145_180e6, 108_506e6, 33_208e6)
    assert balance.noncontrolling_interest == 3_466e6
    income = row(data.income_statements, "2024-12-31")
    assert (income.revenue, income.net_income) == (26_724e6, 4_401e6)


def test_fiscal_years_keyed_by_actual_period_end_newest_first():
    data = mapped("AAPL")
    ends = [r.period_end for r in data.income_statements]
    assert ends == sorted(ends, reverse=True)
    assert ends[0] == "2025-09-27" and ends[-1] == "2007-09-29"       # 52/53-week years
    assert len(data.balance_sheets) == len(ends) - 1                  # FY2007: income comparatives only


def test_per_share_history_is_on_todays_share_basis():
    """Apple split 7:1 (2014) and 4:1 (2020): FY2013 basic EPS of $40.03 is 1.43 today."""
    data = mapped("AAPL")
    eps = {r.period_end[:4]: r.eps for r in data.income_statements}
    assert eps["2013"] == pytest.approx(40.03 / 28, abs=0.005)
    assert eps["2007"] == pytest.approx(4.04 / 28, abs=0.005)
    assert data.shares_by_year["2012"] == pytest.approx(939_208_000 * 28, rel=0.001)
    # Without the split history each year keeps the basis of its last filing: a mixed series
    raw = {r.period_end[:4]: r.eps for r in annual_data(fixture("AAPL")["companyfacts"]).income_statements}
    assert raw["2013"] == pytest.approx(40.03 / 7, abs=0.005)      # last filed after the 2014 split only
    assert raw["2007"] == pytest.approx(4.04, abs=0.005)           # last filed before any later split


def test_splits_are_not_reported_as_restatements():
    notes = " ".join(mapped("WMT").notes) + " ".join(mapped("HRL").notes)
    assert "EPS 4.29 -> 1.43" not in notes and "FY2022 EPS" not in notes
    assert "FY2015 EPS" not in notes


def test_genuine_restatement_uses_the_latest_figure_and_is_flagged():
    """Apple restated FY2009 for its 2009 revenue-recognition change."""
    data = mapped("AAPL")
    assert row(data.income_statements, "2009-09-26").revenue == 42_905e6
    restated = next(n for n in data.notes if "restated" in n)
    assert "FY2009 revenue 36,537M -> 42,905M" in restated


def test_derived_total_liabilities_and_shares_are_noted():
    data = mapped("KO")
    balance = row(data.balance_sheets, "2024-12-31")
    # KO tags no `Liabilities`: liabilities and equity - equity incl. minority interest
    assert balance.total_liabilities == pytest.approx(balance.total_assets - balance.total_equity
                                                      - balance.noncontrolling_interest)
    assert any("total liabilities: derived as liabilities and equity - total equity" in n for n in data.notes)
    assert any("year-end shares: derived as shares issued - treasury shares" in n for n in data.notes)


def test_parent_equity_derived_when_only_total_equity_is_tagged():
    data = mapped("JNJ")
    assert row(data.balance_sheets, "2024-12-29").total_equity == 71_490e6
    assert any("stockholders' equity: derived as equity incl. minority interest - minority interest" in n
               for n in data.notes)


def test_cover_page_shares_and_temporary_equity():
    data = mapped("WMT")
    balance = row(data.balance_sheets, "2026-01-31")
    assert balance.shares_outstanding == 7_972_402_501
    assert any("cover-page count" in n for n in data.notes)
    assert any("- temporary equity" in n for n in data.notes)


def test_weighted_average_shares_as_last_resort():
    data = mapped("HRL")
    assert row(data.balance_sheets, "2025-10-26").shares_outstanding == 550_164_000
    assert any("weighted-average basic shares" in n for n in data.notes)


def test_utility_revenue_is_total_operating_revenues():
    """Southern Co: contract revenue 28,942 excludes other operating revenues; total is 29,553."""
    assert row(mapped("SO").income_statements, "2025-12-31").revenue == 29_553e6


def test_utility_inventory_is_the_sum_of_its_parts():
    data = mapped("SO")
    assert row(data.balance_sheets, "2024-12-31").inventory == 3_369e6
    assert any("inventory: derived as the sum of" in n for n in data.notes)


def test_bank_has_no_classified_balance_sheet():
    balance = row(mapped("JPM").balance_sheets, "2024-12-31")
    assert balance.current_assets is None and balance.current_liabilities is None and balance.inventory is None
    assert balance.total_assets == 4_002_814e6


def _facts(concepts):
    """Synthetic companyfacts: {tag: [(start, end, value, filed, form, unit)]}."""
    out = {}
    for tag, rows in concepts.items():
        units = {}
        for start, end, value, filed, form, unit in rows:
            entry = {"end": end, "val": value, "filed": filed, "form": form, "fy": int(end[:4]), "fp": "FY"}
            if start:
                entry["start"] = start
            units.setdefault(unit, []).append(entry)
        out[tag] = {"units": units}
    return {"facts": {"us-gaap": out}}


def test_latest_filed_tag_wins_and_ties_go_to_chain_order():
    facts = _facts({
        "SalesRevenueNet": [("2020-01-01", "2020-12-31", 100.0, "2021-02-01", "10-K", "USD")],
        "Revenues": [("2020-01-01", "2020-12-31", 104.0, "2022-02-01", "10-K", "USD")],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [("2021-01-01", "2021-12-31", 110.0, "2022-02-01", "10-K", "USD")],
        "NetIncomeLoss": [("2020-01-01", "2020-12-31", 10.0, "2021-02-01", "10-K", "USD"),
                          ("2021-01-01", "2021-12-31", 11.0, "2022-02-01", "10-K", "USD")],
    })
    facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"].append(
        {"start": "2021-01-01", "end": "2021-12-31", "val": 115.0, "filed": "2022-02-01", "form": "10-K"})
    data = annual_data(facts)
    revenue = {r.period_end: r.revenue for r in data.income_statements}
    assert revenue["2020-12-31"] == 104.0        # the 2022 filing restated FY2020 under `Revenues`
    assert revenue["2021-12-31"] == 110.0        # same filing: sales tag first (D-F3)


def test_non_usd_filer_is_rejected():
    facts = _facts({"NetIncomeLoss": [("2020-01-01", "2020-12-31", 10.0, "2021-02-01", "10-K", "EUR")]})
    with pytest.raises(ValueError, match="only USD"):
        annual_data(facts)


def test_quarterly_and_partial_year_facts_are_not_annual():
    facts = _facts({"NetIncomeLoss": [("2020-10-01", "2020-12-31", 3.0, "2021-02-01", "10-K", "USD"),
                                      ("2020-01-01", "2020-12-31", 10.0, "2021-02-01", "10-K", "USD"),
                                      ("2021-01-01", "2021-12-31", 99.0, "2022-02-01", "10-Q", "USD")]})
    data = annual_data(facts)
    assert [(r.period_end, r.net_income) for r in data.income_statements] == [("2020-12-31", 10.0)]


# --- Quarterly (TTM) ----------------------------------------------------------------------------

def periodic(ticker, quarters=8):
    from clients.edgar_mapper import periodic_data
    data = fixture(ticker)
    return periodic_data(data["companyfacts"], SPLITS.get(ticker, ()), data["submissions"]["sic"], quarters)


def test_fiscal_fourth_quarter_is_the_year_minus_nine_months():
    """Apple Q4 FY2025 (Jul-Sep 2025): revenue $102.5bn, net income $27.5bn (Q4 FY25 results)."""
    data = periodic("AAPL")
    q4 = row(data.income_statements, "2025-09-27")
    assert q4.revenue == 416_161e6 - 313_695e6 == 102_466e6
    assert q4.net_income == 27_466e6
    assert any("fourth quarter: derived as the fiscal year minus the first nine months" in n for n in data.notes)


def test_latest_quarters_newest_first_with_balance_sheets():
    data = periodic("AAPL", quarters=8)
    ends = [r.period_end for r in data.income_statements]
    assert len(ends) == 8 and ends == sorted(ends, reverse=True)
    assert [b.period_end for b in data.balance_sheets] == ends
    spacing = {(row_a - row_b).days for row_a, row_b in zip(
        *[[__import__("datetime").date.fromisoformat(e) for e in seq] for seq in (ends[:-1], ends[1:])])}
    assert all(84 <= d <= 98 for d in spacing)                    # quarterly reporter


def test_quarters_use_reported_three_month_figures():
    """Coca-Cola reported 13,380 in both Q2 and Q3 2026 (nine months 39,232 - six months 25,852)."""
    data = periodic("KO")
    assert row(data.income_statements, "2026-07-03").revenue == 13_380e6
    assert row(data.income_statements, "2026-10-02").revenue == 13_380e6
    assert row(data.income_statements, "2026-04-03").revenue == 12_472e6


def test_utility_quarters_use_total_operating_revenues():
    """Southern Co Q4 2025 = total operating revenues for 2025 minus those of the first nine months."""
    revenues = fixture("SO")["companyfacts"]["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    nine_months = next(r["val"] for r in revenues if r.get("start") == "2025-01-01" and r["end"] == "2025-09-30")
    assert row(periodic("SO").income_statements, "2025-12-31").revenue == 29_553e6 - nine_months


def test_rounded_issued_and_treasury_counts_yield_to_the_cover_page():
    """Southern Co tags issued shares as 1.1 billion and treasury in millions: the cover page is exact."""
    data = mapped("SO")
    shares = row(data.balance_sheets, "2025-12-31").shares_outstanding
    assert shares != 1_099_000_000 and 1_100e6 < shares < 1_130e6
    assert any("issued and treasury counts are tagged rounded to millions" in n for n in data.notes)
    # Coca-Cola's issued count is genuinely round but its treasury count is exact: kept
    assert any("derived as shares issued - treasury shares" in n for n in mapped("KO").notes)


def test_quarterly_balance_sheets_have_share_counts():
    for ticker in ("SO", "AAPL", "KO", "JPM"):
        latest = periodic(ticker).balance_sheets[0]
        assert latest.shares_outstanding and latest.shares_outstanding > 0, ticker


def test_years_without_share_count_or_eps_are_noted():
    facts = _facts({
        "NetIncomeLoss": [("2020-01-01", "2020-12-31", 10.0, "2021-02-01", "10-K", "USD")],
        "Assets": [(None, "2020-12-31", 100.0, "2021-02-01", "10-K", "USD")],
    })
    notes = " ".join(annual_data(facts).notes)
    assert "share count: not in the SEC data" in notes and "(FY2020)" in notes
    assert "EPS: not in the SEC data" in notes


# --- Intangibles, bank debt and energy inventory tagged by component ----------------------------

def test_intangibles_tagged_by_kind_are_summed_once():
    """Coca-Cola tags no intangibles total: trademarks + the 'other intangible assets' line."""
    data = mapped("KO")
    assert row(data.balance_sheets, "2024-12-31").intangible_assets == 13_301e6          # trademarks
    assert row(data.balance_sheets, "2020-12-31").intangible_assets == pytest.approx(10_395e6 + 649e6, rel=0.001)
    assert any("intangibles (ex goodwill): derived as the sum of IndefiniteLivedTrademarks" in n for n in data.notes)


def test_bank_long_term_debt_including_current_maturities():
    """JPMorgan tags long-term debt only including current maturities: not added again as short-term."""
    data = mapped("JPM")
    balance = row(data.balance_sheets, "2024-12-31")
    assert balance.long_term_debt == 401_418e6 and balance.short_term_debt == 52_893e6
    assert balance.total_debt == 454_311e6
    assert any("LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities used" in n for n in data.notes)


def test_energy_inventory_total_plus_supplies():
    """ExxonMobil 2024: crude oil, products and merchandise 19,444 + materials and supplies 4,080."""
    facts = _facts({
        "NetIncomeLoss": [("2024-01-01", "2024-12-31", 1.0, "2025-02-01", "10-K", "USD")],
        "Assets": [(None, "2024-12-31", 100.0, "2025-02-01", "10-K", "USD")],
        "EnergyRelatedInventory": [(None, "2024-12-31", 19_444.0, "2025-02-01", "10-K", "USD")],
        "EnergyRelatedInventoryPetroleum": [(None, "2024-12-31", 6_483.0, "2025-02-01", "10-K", "USD")],
        "InventoryPartsAndComponentsNetOfReserves": [(None, "2024-12-31", 4_080.0, "2025-02-01", "10-K", "USD")],
    })
    assert annual_data(facts).balance_sheets[0].inventory == 23_524.0


def test_unmapped_intangible_tags_are_noted():
    facts = _facts({
        "NetIncomeLoss": [("2024-01-01", "2024-12-31", 1.0, "2025-02-01", "10-K", "USD")],
        "Assets": [(None, "2024-12-31", 100.0, "2025-02-01", "10-K", "USD")],
        "IndefiniteLivedBroadcastIntangibles": [(None, "2024-12-31", 30.0, "2025-02-01", "10-K", "USD")],
        "DeferredTaxLiabilitiesGoodwillAndIntangibleAssets": [(None, "2024-12-31", 5.0, "2025-02-01", "10-K", "USD")],
        "BusinessAcquisitionPurchasePriceAllocationAmortizableIntangibleAssets": [
            (None, "2024-12-31", 7.0, "2025-02-01", "10-K", "USD")],
    })
    notes = " ".join(annual_data(facts).notes)
    assert "IndefiniteLivedBroadcastIntangibles is tagged but not included" in notes
    assert "DeferredTax" not in notes and "BusinessAcquisition" not in notes   # not balance-sheet amounts


def _profit_facts(minority=None, minority_share=None):
    concepts = {"ProfitLoss": [("2009-01-01", "2009-12-31", 100.0, "2010-02-01", "10-K", "USD")],
                "Assets": [(None, "2009-12-31", 1000.0, "2010-02-01", "10-K", "USD")]}
    if minority is not None:
        concepts["MinorityInterest"] = [(None, "2009-12-31", minority, "2010-02-01", "10-K", "USD")]
    if minority_share is not None:
        concepts["NetIncomeLossAttributableToNoncontrollingInterest"] = [
            ("2009-01-01", "2009-12-31", minority_share, "2010-02-01", "10-K", "USD")]
    facts = _facts(concepts)
    facts["facts"]["us-gaap"]["NetIncomeLoss"] = {"units": {}}
    facts["facts"]["us-gaap"]["Revenues"] = {"units": {"USD": [{"start": "2009-01-01", "end": "2009-12-31",
                                                                 "val": 500.0, "filed": "2010-02-01", "form": "10-K"}]}}
    return annual_data(facts)


def test_net_income_from_profit_loss_without_minority_interest():
    data = _profit_facts()
    assert data.income_statements[0].net_income == 100.0
    assert any("ProfitLoss used (no minority interest reported)" in n for n in data.notes)


def test_net_income_from_profit_loss_less_the_minority_share():
    data = _profit_facts(minority=50.0, minority_share=8.0)
    assert data.income_statements[0].net_income == 92.0
    assert any("derived as ProfitLoss - the minority interests' share" in n for n in data.notes)


def test_net_income_not_guessed_when_the_minority_share_is_untagged():
    data = _profit_facts(minority=50.0)
    assert data.income_statements[0].net_income is None
    assert any("not available: only ProfitLoss is tagged" in n for n in data.notes)


# --- Holding-company reorganisations (predecessor filers) ---------------------------------------

GOOGL_SPLITS = [("2014-03-27", 2.002), ("2022-07-18", 20.0)]


def test_predecessor_filings_extend_the_history():
    """Alphabet (CIK 1652044, from 2015) succeeded Google Inc. (CIK 1288776): 13 years alone, 19 merged."""
    from clients.edgar_mapper import merge_companyfacts
    alphabet, google = fixture("GOOGL")["companyfacts"], fixture("GOOGL_PREDECESSOR")["companyfacts"]
    alone = annual_data(alphabet, GOOGL_SPLITS)
    merged = annual_data(merge_companyfacts(alphabet, [google]), GOOGL_SPLITS)
    assert alone.income_statements[-1].period_end == "2013-12-31"
    assert merged.income_statements[-1].period_end == "2007-12-31" and len(merged.income_statements) == 19
    assert row(merged.income_statements, "2014-12-31").revenue == 66_001e6            # Google Inc. FY2014 10-K
    # Per-share history continues on today's basis: Google's FY2008 basic EPS $13.46 / 2.002 / 20
    assert row(merged.income_statements, "2008-12-31").eps == pytest.approx(13.46 / 2.002 / 20, abs=0.001)


def test_successor_figures_win_where_years_overlap():
    from clients.edgar_mapper import merge_companyfacts
    successor = _facts({"NetIncomeLoss": [("2014-01-01", "2014-12-31", 141.0, "2016-02-01", "10-K", "USD"),
                                          ("2015-01-01", "2015-12-31", 158.0, "2016-02-01", "10-K", "USD")]})
    predecessor = _facts({"NetIncomeLoss": [("2013-01-01", "2013-12-31", 127.0, "2015-02-01", "10-K", "USD"),
                                            ("2014-01-01", "2014-12-31", 144.0, "2015-02-01", "10-K", "USD")]})
    data = annual_data(merge_companyfacts(successor, [predecessor]))
    assert {r.period_end: r.net_income for r in data.income_statements} == {
        "2015-12-31": 158.0, "2014-12-31": 141.0, "2013-12-31": 127.0}     # 2014: the successor's later filing


# --- Preferred stock ahead of the common (GRAHAM_METHODOLOGY §3.5) --------------------------------

def test_preferred_stock_at_the_higher_of_carrying_value_and_liquidation_preference():
    """JPMorgan FY2024: carrying 20,050 (incl. paid-in capital), liquidation preference 20,200."""
    balance = row(mapped("JPM").balance_sheets, "2024-12-31")
    assert balance.preferred_stock == 20_200e6
    assert any("preferred stock: at its liquidation preference" in n for n in mapped("JPM").notes)
    assert row(mapped("AAPL").balance_sheets, "2024-09-28").preferred_stock is None


def test_preferred_stock_par_value_only_is_raised_to_its_liquidation_preference():
    facts = _facts({
        "NetIncomeLoss": [("2024-01-01", "2024-12-31", 1.0, "2025-02-01", "10-K", "USD")],
        "Assets": [(None, "2024-12-31", 100.0, "2025-02-01", "10-K", "USD")],
        "PreferredStockValue": [(None, "2024-12-31", 1.0, "2025-02-01", "10-K", "USD")],             # par only
        "PreferredStockLiquidationPreferenceValue": [(None, "2024-12-31", 25.0, "2025-02-01", "10-K", "USD")],
    })
    assert annual_data(facts).balance_sheets[0].preferred_stock == 25.0


def test_operating_cash_flow_from_the_cash_flow_statement():
    """Southern Company 10-K: net cash provided from operating activities, FY2025 9,802M; JPMorgan's is negative."""
    assert mapped("SO").operating_cash_flow["2025-12-31"] == 9_802e6
    assert mapped("JPM").operating_cash_flow["2025-12-31"] < 0


def test_operating_cash_flow_falls_back_to_continuing_operations():
    facts = _facts({
        "NetIncomeLoss": [("2024-01-01", "2024-12-31", 1.0, "2025-02-01", "10-K", "USD")],
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations":
            [("2024-01-01", "2024-12-31", 7.0, "2025-02-01", "10-K", "USD")],
    })
    assert annual_data(facts).operating_cash_flow == {"2024-12-31": 7.0}
