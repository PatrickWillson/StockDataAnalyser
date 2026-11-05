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


def test_energy_inventory_tagged_as_finished_goods():
    """ExxonMobil FY2012 10-K: crude oil, products and merchandise 10,836 + materials and supplies 3,706;
    natural gas in storage (300) is a detail of the first line, not added again."""
    facts = _facts({
        "NetIncomeLoss": [("2012-01-01", "2012-12-31", 1.0, "2013-02-27", "10-K", "USD")],
        "Assets": [(None, "2012-12-31", 100.0, "2013-02-27", "10-K", "USD")],
        "InventoryFinishedGoodsAndWorkInProcess": [(None, "2012-12-31", 10_836.0, "2013-02-27", "10-K", "USD")],
        "InventoryPartsAndComponentsNetOfReserves": [(None, "2012-12-31", 3_706.0, "2013-02-27", "10-K", "USD")],
        "EnergyRelatedInventoryNaturalGasInStorage": [(None, "2012-12-31", 300.0, "2013-02-27", "10-K", "USD")],
    })
    assert annual_data(facts).balance_sheets[0].inventory == 14_542.0


# --- Long-term debt due after a year, when no non-current total is tagged (GRAHAM_METHODOLOGY §4.2) -

def _debt_facts(end="2024-12-31", **tags):
    filed = str(int(end[:4]) + 1) + "-03-01"
    facts = {"NetIncomeLoss": [(end[:4] + "-01-01", end, 1.0, filed, "10-K", "USD")],
             "Assets": [(None, end, 100.0, filed, "10-K", "USD")]}
    facts.update({tag: [(None, end, value, filed, "10-K", "USD")] for tag, value in tags.items()})
    return annual_data(_facts(facts))


def test_long_term_debt_from_its_tagged_kinds():
    """Lifetime Brands FY2023 balance sheet: term loan 135,830 + revolving credit 60,395 = 196,225."""
    data = _debt_facts(LongTermDebt=150_000.0, LongTermLoansPayable=135_830.0, LongTermLineOfCredit=60_395.0,
                       LongTermDebtCurrent=4_742.0)
    balance = data.balance_sheets[0]
    assert balance.long_term_debt == 196_225.0 and balance.short_term_debt == 4_742.0
    assert any("long-term debt: derived as the sum of LongTermLoansPayable, LongTermLineOfCredit" in n for n in data.notes)


def test_long_term_notes_replace_a_mismatched_total():
    """Utah Medical FY2013 balance sheet: notes payable 5,065, though LongTermDebt is tagged 7."""
    assert _debt_facts(LongTermDebt=7.0, LongTermNotesPayable=5_065.0).balance_sheets[0].long_term_debt == 5_065.0


def test_other_long_term_debt_counts_beside_a_named_line_or_alone_but_not_over_a_total():
    """Village FY2023: 72,426 + Wakefern notes 1,686. Village FY2018: other 6.4M is a detail of the 48.2M total."""
    assert _debt_facts(LongTermNotesPayable=72_426.0,
                       OtherLongTermDebtNoncurrent=1_686.0).balance_sheets[0].long_term_debt == 74_112.0
    assert _debt_facts(OtherLongTermDebtNoncurrent=900.0).balance_sheets[0].long_term_debt == 900.0
    assert _debt_facts(LongTermDebt=48_200.0, OtherLongTermDebtNoncurrent=6_400.0).balance_sheets[0].long_term_debt == 48_200.0


def test_a_tagged_part_smaller_than_the_total_is_only_a_piece_of_it():
    """Village FY2018: notes payable 6,418 is one component of total long-term debt 48,186."""
    assert _debt_facts(LongTermDebt=48_186.0, LongTermNotesPayable=6_418.0).balance_sheets[0].long_term_debt == 48_186.0
    assert _debt_facts(LongTermDebt=42_646.0, LongTermNotesPayable=0.0).balance_sheets[0].long_term_debt == 42_646.0


def test_long_term_debt_total_less_its_current_portion():
    data = _debt_facts(LongTermDebt=349_822.0, LongTermDebtCurrent=96_000.0)
    balance = data.balance_sheets[0]
    assert balance.long_term_debt == 253_822.0 and balance.short_term_debt == 96_000.0  # not counted twice
    assert any("derived as LongTermDebt - LongTermDebtCurrent" in n for n in data.notes)


def test_junior_subordinated_debt_is_noted_but_never_added():
    """Arrow Financial keeps it outside LongTermDebt, JPMorgan inside; the tags do not say which."""
    data = _debt_facts(LongTermDebt=55_000.0, JuniorSubordinatedDebentureOwedToUnconsolidatedSubsidiaryTrust=20_000.0)
    assert data.balance_sheets[0].long_term_debt == 55_000.0
    assert any("junior subordinated debt is tagged separately and may not be included" in n for n in data.notes)


# --- Earnings for the common: the tag is not always net income less preferred (GRAHAM_METHODOLOGY §2.3) -

def _income(**tags):
    facts = {"Assets": [(None, "2024-12-31", 100.0, "2025-03-01", "10-K", "USD")]}
    facts.update({tag: [("2024-01-01", "2024-12-31", value, "2025-03-01", "10-K", "USD")] for tag, value in tags.items()})
    return annual_data(_facts(facts))


@pytest.mark.parametrize("available, net, preferred, expected", [
    (-479_000.0, 22_179_000.0, None, 22_179_000.0),       # Arrow FY2012: a small allocation, not earnings
    (-12_890.0, -26_967.0, None, -26_967.0),              # Hooker FY2026: continuing operations only
    (12_040.0, 9_865.0, None, 9_865.0),                   # Hooker FY2024: above net income
    (51_416.0, 53_996.0, None, 51_416.0),                 # Oil-Dri FY2025: two-class allocation, kept
    (8_774.0, 11_728.0, None, 8_774.0),                   # JPMorgan FY2009: 25% below, kept
    (-6_180.0, -6_254.0, None, -6_180.0),                 # Hurco FY2020: a loss shared with participating securities
    (-2_204.0, 6_276.0, 8_480.0, -2_204.0),               # Bank of America FY2009: preferred dividends explain it
    (-2_204.0, 6_276.0, 1_000.0, 6_276.0),                # the same gap, preferred dividends do not explain it
    (-3_595.0, -2_238.0, 1_357.0, -3_595.0),              # Bank of America FY2010: a loss, deeper for the common
])
def test_earnings_for_the_common_need_net_income_less_what_ranks_ahead(available, net, preferred, expected):
    tags = {"NetIncomeLossAvailableToCommonStockholdersBasic": available, "NetIncomeLoss": net}
    if preferred is not None:
        tags["PreferredStockDividendsAndOtherAdjustments"] = preferred
    data = _income(**tags)
    assert data.income_statements[0].net_income == expected
    assert any("NetIncomeLoss used" in n for n in data.notes) == (expected == net and available != net)


def test_earnings_for_the_common_alone_are_used_as_tagged():
    data = _income(NetIncomeLossAvailableToCommonStockholdersBasic=5.0, Revenues=50.0)
    assert data.income_statements[0].net_income == 5.0


def test_immaterial_minority_interest_does_not_block_profit_loss():
    """Ethan Allen FY2025: only ProfitLoss 51,596K is tagged, minority balance -85K."""
    facts = {"Assets": [(None, "2025-06-30", 700_000.0, "2025-08-01", "10-K", "USD")],
             "MinorityInterest": [(None, "2025-06-30", -85.0, "2025-08-01", "10-K", "USD")],
             "ProfitLoss": [("2024-07-01", "2025-06-30", 51_596.0, "2025-08-01", "10-K", "USD")]}
    data = annual_data(_facts(facts))
    assert data.income_statements[0].net_income == 51_596.0
    assert any("ProfitLoss used (minority interest immaterial)" in n for n in data.notes)
    facts["MinorityInterest"] = [(None, "2025-06-30", 9_000.0, "2025-08-01", "10-K", "USD")]   # material: unknown share
    assert annual_data(_facts(facts)).income_statements[0].net_income is None


def test_a_misdated_year_without_a_balance_sheet_is_dropped():
    """Ethan Allen's FY2022 10-K dates June-year revenue as calendar 2020; a real fiscal-year change stays."""
    def revenue(start, end):
        return (start, end, 589_837.0, "2022-08-01", "10-K", "USD")
    tag = "RevenueFromContractWithCustomerExcludingAssessedTax"
    facts = {tag: [revenue("2019-07-01", "2020-06-30"), revenue("2020-01-01", "2020-12-31"), revenue("2020-07-01", "2021-06-30")],
             "Assets": [(None, "2020-06-30", 1.0, "2022-08-01", "10-K", "USD"), (None, "2021-06-30", 1.0, "2022-08-01", "10-K", "USD")]}
    assert [r.period_end for r in annual_data(_facts(facts)).income_statements] == ["2021-06-30", "2020-06-30"]
    facts[tag] = [revenue("2018-07-01", "2019-06-30"), revenue("2020-01-01", "2020-12-31")]   # a year's gap: both real
    assert [r.period_end for r in annual_data(_facts(facts)).income_statements] == ["2020-12-31", "2019-06-30"]


# --- Filers tagging figures in thousands as units ---------------------------------------------------

def test_a_later_filing_tagged_in_thousands_is_ignored():
    """Ingles: FY2010 assets 1,532,358,110 (10-K 2011), re-tagged 1,532,358 (10-K 2012)."""
    data = annual_data(_facts({
        "NetIncomeLoss": [("2009-09-27", "2010-09-25", 1.0, "2011-12-02", "10-K", "USD"),
                          ("2010-09-26", "2011-09-24", 1.0, "2011-12-02", "10-K", "USD")],
        "Assets": [(None, "2010-09-25", 1_532_358_110.0, "2011-12-02", "10-K", "USD"),
                   (None, "2010-09-25", 1_532_358.0, "2012-12-26", "10-K", "USD"),
                   (None, "2011-09-24", 1_618_349_808.0, "2011-12-02", "10-K", "USD")]}))
    assert row(data.balance_sheets, "2010-09-25").total_assets == 1_532_358_110.0
    assert any("tagged in thousands or millions" in n and "Assets 2010" in n for n in data.notes)
    assert not any("restated" in n for n in data.notes)


def test_a_genuine_restatement_is_not_a_scale_error():
    data = annual_data(_facts({
        "NetIncomeLoss": [("2010-01-01", "2010-12-31", 1.0, "2011-03-01", "10-K", "USD")],
        "Assets": [(None, "2010-12-31", 1_000.0, "2011-03-01", "10-K", "USD"),
                   (None, "2010-12-31", 900.0, "2012-03-01", "10-K", "USD")]}))
    assert data.balance_sheets[0].total_assets == 900.0


def _shares_by_year(counts):
    facts = {"NetIncomeLoss": [], "Assets": [], "CommonStockSharesOutstanding": []}
    for year, count in counts.items():
        filed = f"{year + 1}-03-01"
        facts["NetIncomeLoss"].append((f"{year}-01-01", f"{year}-12-31", 1.0, filed, "10-K", "USD"))
        facts["Assets"].append((None, f"{year}-12-31", 100.0, filed, "10-K", "USD"))
        facts["CommonStockSharesOutstanding"].append((None, f"{year}-12-31", count, filed, "10-K", "shares"))
    return annual_data(_facts(facts))


def test_a_share_count_in_thousands_is_repaired_from_the_other_years():
    """Graham Corp: FY2011 10,216 among about 10 million a year."""
    data = _shares_by_year({2010: 9_900_000.0, 2011: 10_216.0, 2012: 10_297_000.0, 2013: 10_400_000.0})
    assert data.shares_by_year["2011"] == 10_216_000.0
    assert row(data.balance_sheets, "2011-12-31").shares_outstanding == 10_216_000.0
    assert any("share count: tagged in thousands" in n and "FY2011" in n for n in data.notes)


def test_share_counts_that_really_changed_are_left_alone():
    counts = {2010: 1_000_000.0, 2011: 2_000_000.0, 2012: 4_000_000.0, 2013: 50_000.0}   # 80x: not a 1,000x slip
    assert _shares_by_year(counts).shares_by_year["2013"] == 50_000.0


def test_an_issued_count_far_below_the_cover_page_is_not_trusted():
    """Unitil FY2010: CommonStockSharesIssued 41,455; 10,891,621 shares on the cover of the 10-K."""
    data = annual_data({"facts": {**_facts({
        "NetIncomeLoss": [("2010-01-01", "2010-12-31", 1.0, "2011-02-01", "10-K", "USD")],
        "Assets": [(None, "2010-12-31", 100.0, "2011-02-01", "10-K", "USD")],
        "CommonStockSharesIssued": [(None, "2010-12-31", 41_455.0, "2011-02-01", "10-K", "shares")]})["facts"],
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            {"end": "2011-02-01", "val": 10_891_621.0, "filed": "2011-02-01", "form": "10-K", "fy": 2010, "fp": "FY"}]}}}}})
    assert data.balance_sheets[0].shares_outstanding == 10_891_621.0


# --- Share counts reported per class (dual-class companies) ----------------------------------------

def _instance(*facts, extra_contexts=""):
    """A minimal XBRL instance. facts: (tag, instant, member or None, value)."""
    contexts, rows = [], []
    for i, (tag, instant, member, value) in enumerate(facts):
        segment = (f'<segment><xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">{member}'
                   "</xbrldi:explicitMember></segment>") if member else ""
        contexts.append(f'<context id="c{i}"><entity>{segment}</entity><period><instant>{instant}</instant></period></context>')
        prefix = "dei" if tag.startswith("Entity") else "us-gaap"
        rows.append(f'<{prefix}:{tag} contextRef="c{i}">{value}</{prefix}:{tag}>')
    return ('<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" '
            'xmlns:us-gaap="http://fasb.org/us-gaap/2024" xmlns:dei="http://xbrl.sec.gov/dei/2024">'
            + "".join(contexts) + extra_contexts + "".join(rows) + "</xbrl>")


def test_class_share_counts_add_the_classes_of_each_date():
    """Bel Fuse FY2025 10-K: Class A 2,115,263 + Class B 10,543,368, and a year earlier."""
    from clients.edgar_mapper import class_share_counts
    counts, cover = class_share_counts(_instance(
        ("CommonStockSharesOutstanding", "2025-12-31", "us-gaap:CommonClassAMember", 2_115_263),
        ("CommonStockSharesOutstanding", "2025-12-31", "us-gaap:CommonClassBMember", 10_543_368),
        ("CommonStockSharesOutstanding", "2024-12-31", "us-gaap:CommonClassAMember", 2_115_263),
        ("CommonStockSharesOutstanding", "2024-12-31", "us-gaap:CommonClassBMember", 10_425_175),
        ("CommonStockSharesIssued", "2025-12-31", "us-gaap:CommonClassBMember", 99_999_999),   # issued is not outstanding
        ("EntityCommonStockSharesOutstanding", "2026-01-31", "us-gaap:CommonClassAMember", 2_115_263),
        ("EntityCommonStockSharesOutstanding", "2026-01-31", "us-gaap:CommonClassBMember", 10_541_050)))
    assert counts == {"2025-12-31": 12_658_631.0, "2024-12-31": 12_540_438.0}
    assert cover == 12_656_313.0


def test_class_share_counts_need_two_classes():
    from clients.edgar_mapper import class_share_counts
    assert class_share_counts(_instance(("CommonStockSharesOutstanding", "2025-12-31", None, 100),
                                        ("CommonStockSharesOutstanding", "2024-12-31", "x:ClassBMember", 5))) == ({}, None)


def test_instance_filename():
    from clients.edgar_mapper import instance_filename
    assert instance_filename(["a.htm", "belfb20251231d_10k_htm.xml", "x_cal.xml"]) == "belfb20251231d_10k_htm.xml"
    assert instance_filename(["belfb-20181231.xml", "belfb-20181231_cal.xml"]) == "belfb-20181231.xml"
    assert instance_filename(["R1.htm"]) is None


def test_the_other_years_decide_which_scale_is_wrong():
    """Berkshire FY2011 average shares: 1,649,891,000,000 (10-K 2012), corrected to 1,649,891 (10-K 2013)."""
    tag = "WeightedAverageNumberOfSharesOutstandingBasic"
    def year(y, value, filed):
        return (f"{y}-01-01", f"{y}-12-31", value, filed, "10-K", "shares")
    facts = {"NetIncomeLoss": [(f"{y}-01-01", f"{y}-12-31", 1.0, f"{y + 1}-03-01", "10-K", "USD") for y in (2011, 2012, 2013)],
             "Assets": [(None, f"{y}-12-31", 1.0, f"{y + 1}-03-01", "10-K", "USD") for y in (2011, 2012, 2013)],
             tag: [year(2011, 1_649_891_000_000.0, "2012-03-01"), year(2011, 1_649_891.0, "2013-03-01"),
                   year(2012, 1_651_294.0, "2013-03-01"), year(2013, 1_643_613.0, "2014-03-01")]}
    assert annual_data(_facts(facts)).shares_by_year["2011"] == 1_649_891.0


def test_other_intangibles_count_beside_an_indefinite_lived_total():
    """Preformed Line Products FY2025: indefinite-lived 0, other intangible assets 10,140."""
    assert _debt_facts(IndefiniteLivedIntangibleAssetsExcludingGoodwill=0.0,
                       OtherIntangibleAssetsNet=10_140.0).balance_sheets[0].intangible_assets == 10_140.0


def test_long_term_debt_from_senior_notes_and_bank_advances():
    """Oil-Dri FY2026: senior notes 37,860K. Citizens & Northern FY2024: 165.45M + 14.9M + 24.83M."""
    assert _debt_facts(SeniorLongTermNotes=37_860.0, SeniorNotesCurrent=1_000.0).balance_sheets[0].long_term_debt == 37_860.0
    assert _debt_facts(SeniorLongTermNotes=37_860.0, SeniorNotesCurrent=1_000.0).balance_sheets[0].short_term_debt == 1_000.0
    balance = _debt_facts(FederalHomeLoanBankAdvancesLongTerm=165.45, SeniorNotes=14.9, SubordinatedDebt=24.83).balance_sheets[0]
    assert balance.long_term_debt == pytest.approx(205.18)


# --- A 10-K the SEC's company facts do not include -----------------------------------------------

_SENECA_INSTANCE = """<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
  xmlns:us-gaap="http://fasb.org/us-gaap/2025" xmlns:dei="http://xbrl.sec.gov/dei/2025" xmlns:iso4217="iso">
  <context id="i"><entity><identifier>88948</identifier></entity><period><instant>2026-03-31</instant></period></context>
  <context id="d"><entity><identifier>88948</identifier></entity><period><startDate>2025-04-01</startDate><endDate>2026-03-31</endDate></period></context>
  <context id="seg"><entity><segment><xbrldi:explicitMember dimension="x:SegAxis">x:Veg</xbrldi:explicitMember></segment></entity><period><instant>2026-03-31</instant></period></context>
  <unit id="USD"><measure>iso4217:USD</measure></unit>
  <unit id="Share"><measure>shares</measure></unit>
  <unit id="EPS"><divide><unitNumerator><measure>iso4217:USD</measure></unitNumerator><unitDenominator><measure>shares</measure></unitDenominator></divide></unit>
  <us-gaap:Assets contextRef="i" unitRef="USD" decimals="-3">1247758000</us-gaap:Assets>
  <us-gaap:Assets contextRef="seg" unitRef="USD" decimals="-3">1473285000</us-gaap:Assets>
  <us-gaap:NetIncomeLoss contextRef="d" unitRef="USD" decimals="-3">114674000</us-gaap:NetIncomeLoss>
  <us-gaap:NetIncomeLoss contextRef="d" unitRef="USD" decimals="-3">114674000</us-gaap:NetIncomeLoss>
  <us-gaap:EarningsPerShareBasic contextRef="d" unitRef="EPS" decimals="2">16.30</us-gaap:EarningsPerShareBasic>
  <us-gaap:CommonStockSharesOutstanding contextRef="i" unitRef="Share" decimals="0">7000000</us-gaap:CommonStockSharesOutstanding>
  <us-gaap:Notes contextRef="d">text</us-gaap:Notes>
</xbrl>"""


def test_an_instance_reads_as_company_wide_companyfacts():
    from clients.edgar_mapper import instance_companyfacts
    facts = instance_companyfacts(_SENECA_INSTANCE, "10-K", "2026-06-11", "acc-1")
    data = annual_data(facts)
    assert data.income_statements[0].net_income == 114_674_000.0 and data.income_statements[0].eps == 16.30
    assert data.balance_sheets[0].total_assets == 1_247_758_000.0            # the segment's figure is left out
    assert data.balance_sheets[0].shares_outstanding == 7_000_000.0
    assert len(facts["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"]) == 1   # repeated in the filing


def test_only_filings_for_later_years_are_unreported():
    from clients.edgar_mapper import unreported_annual_filings
    data = _debt_facts(end="2024-12-31")
    recent = {"form": ["10-K", "10-K", "10-Q"], "reportDate": ["2025-12-31", "2024-12-31", "2026-06-27"],
              "filingDate": ["2026-02-11", "2025-02-11", "2026-08-06"], "accessionNumber": ["a", "b", "c"], "isXBRL": [1, 1, 1]}
    assert unreported_annual_filings(data, {"filings": {"recent": recent}}) == [("2025-12-31", "2026-02-11", "a")]
