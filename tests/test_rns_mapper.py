"""rns_mapper: the income statement of a results announcement, and the overlap gate. Synthetic announcements."""

from types import SimpleNamespace

from clients.rns_mapper import RnsStatement, parse_statement, rns_history, rows_of
from core.fundamentals import IncomeStatementRow


def _table(heading, rows, before=""):
    cells = "".join("<tr>" + "".join(f"<td><p><span>{c}</span></p></td>" for c in row) + "</tr>" for row in rows)
    return f"<html><body><p>{before}</p><p><b>{heading}</b></p><table>{cells}</table></body></html>"


MODERN = _table("Consolidated income statement for the year ended 31st December 2025 (audited)", [
    ["", "2025", "2024"], ["", "£'000", "£'000"],
    ["Revenue", "3", "50,935", "48,947"], ["Cost of sales", "(28,440)", "(27,292)"],
    ["Profit before tax", "4,089", "3,198"], ["Tax expense", "(1,381)", "(865)"],
    ["Profit for the year", "2,708", "2,333"], ["Profit attributable to:"],
    ["Non-controlling interests", "(6)", "53"], ["Owners of the parent", "2,714", "2,280"],
    ["Basic earnings per share", "188.50p", "158.37p"]],
    before="Annual results for the year ended 31 December 2025")


def test_the_owners_line_under_an_attributable_list_is_net_income():
    s = parse_statement(MODERN, 7)
    assert (s.period_end, s.prior_end, s.currency, s.unit) == ("2025-12-31", "2024-12-31", "GBP", 1e3)
    assert s.net_income == (2_714_000, 2_280_000) and s.revenue == (50_935_000, 48_947_000)
    assert s.label == "Profit attributable to: Owners of the parent"


def test_three_columns_a_year_take_the_total():
    page = _table("Consolidated statement of comprehensive income for the year ended 31 March 2026", [
        ["", "2026", "2026", "2026", "2025", "2025", "2025"], ["", "€'000"] * 1 + ["€'000"] * 5,
        ["", "Underlying", "Exceptional", "Total", "Underlying", "Exceptional", "Total"],
        ["Total revenue", "3", "153,276", "-", "153,276", "136,632", "-", "136,632"],
        ["Operating profit", "12,290", "1,300", "13,590", "7,649", "(12,030)", "(4,381)"],
        ["Finance costs", "(5,000)", "-", "(5,000)", "(4,000)", "-", "(4,000)"],
        ["Profit/(loss) for the year attributable to owners of the parent", "5,541", "1,300", "6,841",
         "1,300", "(12,030)", "(10,730)"]])
    s = parse_statement(page, 1)
    assert s.currency == "EUR" and s.net_income == (6_841_000, -10_730_000)


def test_a_label_split_over_two_rows_is_joined():
    page = _table("Consolidated Statement of Comprehensive Income", [
        ["For the year ended 30 June 2026"], ["Notes", "30 June 2026 £'000s", "30 June 2025 £'000s"],
        ["Revenue", "89", "42"], ["Operating loss", "(4,365)", "(3,255)"], ["Loss before tax", "(4,267)", "(3,215)"],
        ["Taxation", "4", "88", "110"], ["Loss and total comprehensive loss for the year"],
        ["from continuing operations to owners of the parent", "(4,179)", "(3,105)"]])
    s = parse_statement(page, 1)
    assert s.period_end == "2026-06-30" and s.net_income == (-4_179_000, -3_105_000)


def test_profit_for_the_year_is_not_the_continuing_operations_line():
    page = _table("CONSOLIDATED INCOME STATEMENT FOR THE YEAR ENDED 30 APRIL 2026", [
        ["", "2026 £000", "2025 £000"], ["Revenue", "21,867", "18,099"], ["Profit before tax", "1,852", "1,490"],
        ["Profit for the year from continuing operations", "1,300", "1,087"],
        ["Loss from discontinued operations", "5", "(716)", "(425)"], ["Loss per share – discontinued operations"],
        ["Profit for the year", "584", "662"]])
    assert parse_statement(page, 1).net_income == (584_000, 662_000)


def test_total_comprehensive_income_is_not_net_income():
    page = _table("Consolidated Statement of Profit and Loss and Other Comprehensive Income", [
        ["for the year ended 31 March 2026"], ["Year ended 31 March", "Notes", "2026 £000", "2025 £000"],
        ["Revenue", "4", "45,002", "30,459"], ["Operating (loss)/profit", "(1,992)", "1,002"],
        ["Taxation", "(303)", "(227)"], ["(Loss)/profit for the year", "(2,303)", "1,104"],
        ["Exchange differences on translating foreign operations", "(178)", "(303)"],
        ["Total comprehensive (loss)/income for the year attributable to the owners", "(2,481)", "801"]])
    s = parse_statement(page, 1)
    assert s.net_income == (-2_303_000, 1_104_000) and s.unit == 1e3


def test_a_legacy_text_announcement_in_exact_pounds():
    text = """Braime (T.F.& J.H.) (Hldgs) PLC
      Consolidated Income Statement for the year ended 31st December 2006

                                              Note         2006           2005
                                                              Â£              Â£
Revenue                                              11,119,745      9,699,124
Raw materials and consumables used                   (6,011,478)    (5,250,183)
Loss from operations                                   (125,796)      (251,181)
Loss before tax                                        (116,200)      (228,441)
Loss for the year attributable to equity holders       (187,376)      (215,152)
"""
    page = f'<div class="legacy-text-announcement" style="white-space: pre-wrap;">{text}</div>'
    s = parse_statement(page, 1)
    assert (s.period_end, s.unit, s.currency) == ("2006-12-31", 1.0, "GBP")
    assert s.net_income == (-187_376, -215_152) and s.revenue == (11_119_745, 9_699_124)


def test_a_heading_in_narrative_text_or_a_statement_without_a_unit_is_not_read():
    narrative = _table("Group and recognised in the Statement of Comprehensive Income in the Period", [
        ["Profit for the year attributable to equity holders", "401", "(1,159)"]])
    no_unit = _table("Consolidated income statement for the year ended 31 December 2025", [
        ["", "2025", "2024"], ["Revenue", "500", "400"], ["Cost of sales", "(300)", "(200)"],
        ["Profit before tax", "120", "110"], ["Profit for the year", "100", "90"]])
    assert parse_statement(narrative, 1) is None and parse_statement(no_unit, 1) is None


def test_rows_join_a_tables_cells_and_split_legacy_lines_at_wide_gaps():
    assert rows_of(_table("H", [["Revenue", "1,000", "900"]]))[-1] == ["Revenue", "1,000", "900"]
    legacy = '<div class="legacy-text-announcement">Revenue        1,000      900\n</div>'
    assert rows_of(legacy) == [["Revenue", "1,000", "900"]]


def _annual(years):
    return SimpleNamespace(currency="GBP", income_statements=tuple(
        IncomeStatementRow(f"{y}-12-31", 50e6, ni, None) for y, ni in years.items()))


def _statement(year, ni, prior, announcement_id=None, unit=1e3, revenue=(50e6, 48e6), currency="GBP"):
    return RnsStatement(announcement_id or year, f"{year}-12-31", f"{year - 1}-12-31", currency, unit, (ni, prior),
                        revenue, "Profit for the year")


YAHOO = {2025: 2_714_000.0, 2024: 2_280_000.0, 2023: 2_274_000.0}
STATEMENTS = [_statement(2025, 2_714_000, 2_280_000), _statement(2024, 2_280_000, 2_274_000),
              _statement(2023, 2_274_000, 2_768_000), _statement(2022, 2_768_000, 1_500_000),
              _statement(2021, 1_480_000, 900_000)]


def test_the_announced_years_before_yahoos_are_used_when_every_overlap_year_agrees():
    history = rns_history(_annual(YAHOO), STATEMENTS)
    assert [r.period_end for r in history.income_statements] == ["2022-12-31", "2021-12-31", "2020-12-31"]
    # FY2021: the restated comparative of the FY2022 announcement (1.5M), not the year's own 1.48M
    assert [r.net_income for r in history.income_statements] == [2_768_000, 1_500_000, 900_000]
    assert history.shares_by_year == {"2022": 0.0, "2021": 0.0, "2020": 0.0}     # no per-share figures (§8.12)
    assert history.notes[0].startswith("History before FY2023: RNS results announcements")


def test_one_overlap_year_that_disagrees_rules_out_every_older_year():
    statements = [_statement(2025, 2_714_000, 2_280_000), _statement(2024, 2_380_000, 2_274_000)] + STATEMENTS[2:]
    history = rns_history(_annual({**YAHOO, 2024: 2_000_000.0}), statements)
    assert history.income_statements == () and "did not agree" in history.notes[0]


def test_either_the_first_reported_or_the_restated_figure_may_agree():
    statements = [_statement(2025, 2_714_000, 2_310_000), _statement(2024, 2_280_000, 2_274_000)] + STATEMENTS[2:]
    assert rns_history(_annual(YAHOO), statements).income_statements


def test_statements_in_another_currency_are_left_out():
    statements = [_statement(y, 1e6, 1e6, currency="USD") for y in (2025, 2024, 2023)]
    history = rns_history(_annual(YAHOO), statements)
    assert history.income_statements == () and "in USD" in history.notes[0]


def test_revenue_is_cut_where_it_moves_tenfold():
    statements = STATEMENTS[:4] + [_statement(2021, 1_500_000, 900_000, revenue=(48e6, 1e6))]
    history = rns_history(_annual(YAHOO), statements)
    assert [r.revenue for r in history.income_statements] == [48e6, 48e6, None]
    assert any("revenue not used for FY2020" in n for n in history.notes)


def test_an_announcement_that_does_not_link_ends_the_history():
    """Quadrise's QED page also carries an earlier QED's March-year results: they do not link to the June years."""
    stranger = RnsStatement(1, "2015-03-31", "2014-03-31", "GBP", 1e6, (37_900_000, 52_900_000), (None, None), "x")
    history = rns_history(_annual(YAHOO), STATEMENTS + [stranger])
    assert [r.period_end for r in history.income_statements] == ["2022-12-31", "2021-12-31", "2020-12-31"]
    assert any("does not link" in n for n in history.notes)


def test_a_total_written_with_spaced_slashes_is_the_net_income_not_the_continuing_line():
    """ActiveOps FY2021: -2,791 from continuing activities, +8,992 in all (a gain on discontinued activities)."""
    page = _table("Consolidated statement of profit and loss and other comprehensive income", [
        ["Year ended 31 March 2022", "Notes", "2022 £000", "2021 £000"], ["Revenue", "22,917", "20,394"],
        ["Operating loss", "(2,550)", "(1,767)"], ["Loss before taxation", "(2,612)", "(2,048)"],
        ["Loss for the year from continuing activities", "(2,731)", "(2,791)"],
        ["Profit for the year from discontinued activities, net of tax", "-", "11,783"],
        ["Profit / (loss) for the year", "(2,731)", "8,992"]])
    assert parse_statement(page, 1).net_income == (-2_731_000, 8_992_000)


def test_columns_headed_by_year_take_each_years_last_column():
    """Billington 2025: underlying / non-underlying / total 2025, then total 2024."""
    page = _table("Consolidated Income Statement", [
        ["Underlying", "Non-underlying", "Total"], ["2025", "2025", "2025", "2024"], ["£'000", "£'000", "£'000", "£'000"],
        ["Revenue", "95,694", "-", "95,694", "113,061"], ["Operating profit", "3,462", "(2,758)", "704", "10,021"],
        ["Profit before tax", "4,095", "(2,758)", "1,337", "10,814"],
        ["Profit after tax", "3,451", "(2,124)", "1,327", "8,272"],
        ["Profit for the year attributable to equity holders", "3,451", "(2,124)", "1,327", "8,272"]],
        before="Results for the year ended 31 December 2025")
    s = parse_statement(page, 1)
    assert s.net_income == (1_327_000, 8_272_000) and s.revenue == (95_694_000, 113_061_000)


def test_years_inside_column_labels_head_the_columns():
    page = _table("Consolidated income statement for the year ended 31 December 2025", [
        ["Underlying 2025", "Non-underlying 2025", "Total 2025", "2024"], ["£'000", "£'000"],
        ["Revenue", "95,694", "-", "95,694", "113,061"], ["Operating profit", "3,462", "(2,758)", "704", "10,021"],
        ["Profit before tax", "4,095", "(2,758)", "1,337", "10,814"], ["Tax", "(644)", "634", "(10)", "(2,542)"],
        ["Profit for the year attributable to equity holders of the parent company", "3,451", "(2,124)", "1,327", "8,272"]])
    assert parse_statement(page, 1).net_income == (1_327_000, 8_272_000)


def test_owners_under_a_nested_attribution_list():
    """Ironveld FY2025: 'Attributable to:', a column header, 'Loss for the year', then the owners' line."""
    page = _table("Consolidated Statement of Comprehensive Income for the year ended 30 June 2025", [
        ["Note", "£'000", "£'000"], ["Revenue", "4", "164"], ["Loss before taxation", "(1,556)", "(1,756)"],
        ["Taxation", "5", "-", "(494)"], ["Loss for the year from continuing operations", "(1,556)", "(2,250)"],
        ["Attributable to:"], ["Note", "£'000", "£'000"], ["Loss for the year"],
        ["Owners of the Company", "(1,414)", "(2,236)"], ["Non-controlling interest", "(142)", "(14)"],
        ["Total comprehensive loss for the year"], ["Owners of the Company", "(2,436)", "(1,597)"]])
    assert parse_statement(page, 1).net_income == (-1_414_000, -2_236_000)


def test_a_statement_continued_over_a_page_break_is_one_statement():
    page = _table("CONSOLIDATED STATEMENT OF COMPREHENSIVE INCOME", [
        ["Year ended 30 June 2025", "Year ended 30 June 2024"], ["Note", "£'000", "£'000"], ["Revenue", "4", "164"],
        ["Loss before taxation", "(1,556)", "(1,756 )"], ["Taxation", "5", "-", "(494)"],
        ["Loss for the year from continuing operations", "(1,556)", "(2,250)"],
        ["CONSOLIDATED STATEMENT OF COMPREHENSIVE INCOME (CONTINUED)"], ["Attributable to:"],
        ["Note", "£'000", "£'000"], ["Loss for the year"], ["Owners of the Company", "(1,414)", "(2,236)"],
        ["Non-controlling interest", "(142)", "(14)"]])
    assert parse_statement(page, 1).net_income == (-1_414_000, -2_236_000)


def test_a_note_and_a_figure_in_one_cell_stay_apart():
    from clients.rns_mapper import _value
    assert _value("( 1,756 )") == -1756 and _value("5 1,234") is None


def test_a_plain_heading_is_read_when_there_is_no_consolidated_statement():
    rows = [["2025", "2024"], ["£'000", "£'000"], ["Revenue", "10", "8"], ["Administrative expenses", "(900)", "(800)"],
            ["Loss before tax", "(890)", "(792)"], ["Loss for the year", "(890)", "(792)"]]
    plain = _table("STATEMENT OF COMPREHENSIVE INCOME for the year ended 31 December 2025", rows)
    assert parse_statement(plain, 1).net_income == (-890_000, -792_000)
    both = _table("Consolidated income statement for the year ended 31 December 2025",
                  [r if r[0] != "Loss for the year" else ["Loss for the year", "(1,000)", "(700)"] for r in rows])
    assert parse_statement(both + plain, 1).net_income == (-1_000_000, -700_000)


def test_a_header_cell_ending_in_a_note_number_is_not_a_figure():
    from clients.rns_mapper import _value
    assert _value("11)") is None and _value("(11") is None and _value("(1,234)") == -1234 and _value("0") == 0
    page = _table("CONSOLIDATED INCOME STATEMENT", [
        ["FOR THE YEAR ENDED 31 DECEMBER 2025"], ["Year ended 31 December 2025", "Year ended 31 December 2024"],
        ["Underlying", "Non-underlying 1 (Note 11)", "Total", "Underlying", "Non-underlying 1 (Note 11)", "Total"],
        ["Note", "£'000", "£'000", "£'000", "£'000", "£'000", "£'000"],
        ["Revenue", "7", "1,035,897", "-", "1,035,897", "962,506", "-", "962,506"],
        ["Operating profit", "40,000", "(5,000)", "35,000", "30,000", "(1,000)", "29,000"],
        ["Profit before tax", "38,000", "(5,000)", "33,000", "28,000", "(1,000)", "27,000"],
        ["Profit for the year", "30,000", "(4,000)", "26,000", "21,000", "(800)", "20,200"]])
    assert parse_statement(page, 1).net_income == (26_000_000, 20_200_000)


def test_group_and_company_columns_take_the_groups():
    page = _table("Consolidated and Company Statements of Comprehensive Income", [
        ["for the year ended 31 December 2020"], ["The Group", "The Company", "The Group", "The Company"],
        ["(Euro 000's)", "Note", "2020", "2020", "2019", "2019"], ["Revenue", "5", "252,784", "1,442", "187,868", "1,283"],
        ["Operating profit", "40,000", "100", "30,000", "90"], ["Profit before tax", "38,000", "90", "28,000", "80"],
        ["Profit for the year", "30,000", "80", "21,000", "70"]])
    s = parse_statement(page, 1)
    assert (s.currency, s.unit, s.net_income) == ("EUR", 1e3, (30_000_000, 21_000_000))


def test_a_year_split_by_a_space_and_for_year_without_the():
    page = _table("Consolidated Income Statement", [
        ["for the year ended 31 December 202 5"], ["Notes", "202 5", "202 4"], ["£", "£"], ["Continuing Operations"],
        ["Revenue", "500,000", "400,000"], ["Operating loss", "(90,000)", "(80,000)"],
        ["Loss before tax", "(95,000)", "(85,000)"], ["(Loss)/profit for year", "(95,000)", "(85,000)"]])
    s = parse_statement(page, 1)
    assert (s.period_end, s.unit, s.net_income) == ("2025-12-31", 1.0, (-95_000, -85_000))


def test_after_tax_and_investment_trust_return_lines():
    rows = [["2025", "2024"], ["£'000", "£'000"], ["Revenue", "500", "400"], ["Operating profit", "120", "100"],
            ["Profit before tax", "110", "90"]]
    after_tax = _table("Consolidated income statement for the year ended 31 December 2025",
                       rows + [["Profit after tax and total comprehensive income", "80", "70"]])
    trust = _table("Statement of total return for the year ended 31 December 2025",
                   rows + [["Net return after taxation", "80", "70"]])
    assert parse_statement(after_tax, 1).net_income == (80_000, 70_000)
    assert parse_statement(trust, 1).net_income == (80_000, 70_000)


def test_eulerpool_settles_a_disagreement_with_yahoo_when_it_has_the_announced_figure():
    """FY2024 announced 2.28M, Yahoo 1.5M: Eulerpool's 2.3M (whole millions) sides with the announcement."""
    yahoo = {**YAHOO, 2024: 1_500_000.0}
    assert rns_history(_annual(yahoo), STATEMENTS).income_statements == ()
    vendor = {"2024-12-31": 2_300_000.0}
    history = rns_history(_annual(yahoo), STATEMENTS, vendor=vendor)
    assert [r.period_end for r in history.income_statements][:1] == ["2022-12-31"]
    assert any("two sources against one" in n for n in history.notes)
    # a vendor that has Yahoo's figure does not side with the announcement
    assert rns_history(_annual(yahoo), STATEMENTS, vendor={"2024-12-31": 1_500_000.0}).income_statements == ()


def _chain_with(older):
    return STATEMENTS[:3] + older


def test_a_restatement_links_by_revenue():
    """FY2022 announced 2.5M, restated to 2.768M in the next announcement; the revenue links (48M)."""
    restated = [_statement(2022, 2_500_000, 1_500_000, revenue=(48e6, 47e6))]
    history = rns_history(_annual(YAHOO), _chain_with(restated))
    assert [r.period_end for r in history.income_statements] == ["2022-12-31", "2021-12-31"]
    assert any("restated in the next announcement" in n and "its revenue" in n for n in history.notes)


def test_a_gap_is_bridged_only_by_the_second_source():
    """No FY2022 announcement read: FY2021's statement links only where Eulerpool has its net income."""
    gap = [_statement(2021, 1_500_000, 900_000)]
    without = rns_history(_annual(YAHOO), _chain_with(gap))
    assert [r.period_end for r in without.income_statements] == ["2022-12-31"]      # the comparative only
    with_vendor = rns_history(_annual(YAHOO), _chain_with(gap), vendor={"2021-12-31": 1_550_000.0})
    assert [r.period_end for r in with_vendor.income_statements] == ["2022-12-31", "2021-12-31", "2020-12-31"]
    assert any("missing (no announcement read)" in n for n in with_vendor.notes)


def test_another_companys_results_do_not_link_even_with_a_vendor():
    stranger = RnsStatement(1, "2015-03-31", "2014-03-31", "GBP", 1e6, (37_900_000, 52_900_000), (None, None), "x")
    history = rns_history(_annual(YAHOO), STATEMENTS + [stranger], vendor={"2015-03-31": 1_000_000.0})
    assert "2015-03-31" not in [r.period_end for r in history.income_statements]
