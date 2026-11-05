"""
EODHD statement mapping (clients/eodhd_mapper.py): typed rows keep "not reported" (None) distinct from 0.0, and
as_history_fields() reproduces the history-row shape (missing -> 0.0).
"""

import pytest

from clients.eodhd_mapper import (
    balance_sheet_row, income_statement_row, parse_balance_sheet_rows, parse_income_statement_rows,
)
from core.fundamentals import optional_float


@pytest.mark.parametrize("raw,expected", [
    (None, None), ("", None), ("NA", None), ("N/A", None), ("abc", None), ([1], None),
    (0, 0.0), ("0", 0.0), (12, 12.0), ("-3.5", -3.5),
])
def test_optional_float(raw, expected):
    assert optional_float(raw) == expected


def test_balance_sheet_row_keeps_missing_distinct_from_zero():
    row = balance_sheet_row("2023-12-31", {"totalStockholderEquity": 0, "goodWill": None})
    assert row.total_equity == 0.0
    assert row.goodwill is None
    assert row.as_history_fields()["goodwill"] == 0.0


def test_balance_sheet_field_mapping():
    raw = {"totalStockholderEquity": 500, "intangibleAssets": 10, "goodWill": 20, "totalCurrentAssets": 300,
           "totalCurrentLiabilities": 100, "totalLiab": 250, "longTermDebt": 80, "totalAssets": 750,
           "commonStockSharesOutstanding": 50, "inventory": 40}
    assert balance_sheet_row("2023-12-31", raw).as_history_fields() == {
        "total_equity": 500.0, "intangible_assets": 10.0, "goodwill": 20.0, "current_assets": 300.0,
        "current_liabilities": 100.0, "total_liabilities": 250.0, "long_term_debt": 80.0,
        "total_assets": 750.0, "total_debt": 80.0, "shares_outstanding": 50.0, "inventory": 40.0,
        "claims_outside_equity": 0.0, "preferred_stock": 0.0}  # 750 - 250 - 500


def test_claims_outside_equity_from_balance_sheet_gap():
    """WLKP 2024 (real EODHD data): minority-interest field null, TA - TL - equity = 310.6M."""
    row = balance_sheet_row("2024-12-31", {"totalAssets": "1287956000.00", "totalLiab": "458642000.00",
                                                    "totalStockholderEquity": "518701000.00",
                                                    "noncontrollingInterestInConsolidatedEntity": None})
    assert row.claims_outside_common_equity == 310_613_000.0


def test_explicit_minority_interest_preferred_over_gap():
    row = balance_sheet_row("d", {"totalAssets": 1000, "totalLiab": 600, "totalStockholderEquity": 300,
                                           "noncontrollingInterestInConsolidatedEntity": 80})
    assert row.claims_outside_common_equity == 80.0


def test_claims_never_negative_and_zero_when_unreported():
    assert balance_sheet_row("d", {"totalAssets": 100, "totalLiab": 80, "totalStockholderEquity": 30}
                                      ).claims_outside_common_equity == 0.0
    assert balance_sheet_row("d", {"totalAssets": 100, "totalStockholderEquity": 30}
                                      ).claims_outside_common_equity == 0.0


def test_unreported_inventory_is_none_not_zero():
    """F14: the quick ratio must tell "not reported" (None) from "no inventory" (0.0)."""
    assert balance_sheet_row("d", {}).as_history_fields()["inventory"] is None
    assert balance_sheet_row("d", {"inventory": 0}).as_history_fields()["inventory"] == 0.0


def test_share_count_fallback_chain():
    assert balance_sheet_row("d", {"weightedAverageShsOut": 7}).shares_outstanding == 7.0
    assert balance_sheet_row("d", {"weightedAverageShsOutDil": 9}).shares_outstanding == 9.0
    assert balance_sheet_row("d", {}).shares_outstanding == 0.0


def test_income_statement_chains():
    row = income_statement_row("d", {"eps": "NA", "basicEPS": 2.0, "netIncomeFromContinuingOps": None,
                                              "netIncome": 40, "totalRevenue": 100})
    assert (row.eps, row.net_income, row.revenue) == (2.0, 40.0, 100.0)


def test_rows_newest_first_for_either_period():
    data = {"Financials": {"Income_Statement": {"quarterly": {"2023-03-31": {"eps": 1}, "2023-06-30": {"eps": 2}}}}}
    assert [r.period_end for r in parse_income_statement_rows(data, "quarterly")] == ["2023-06-30", "2023-03-31"]
    assert parse_income_statement_rows(data, "yearly") == []


def test_malformed_row_keeps_rows_parsed_so_far():
    data = {"Financials": {"Balance_Sheet": {"yearly": {"2023-12-31": {"totalAssets": 1}, "2022-12-31": "junk"}}}}
    assert [r.period_end for r in parse_balance_sheet_rows(data)] == ["2023-12-31"]


def test_unknown_period_is_rejected():
    with pytest.raises(ValueError):
        parse_balance_sheet_rows({}, "monthly")



def test_preferred_stock_inside_equity_is_mapped():
    row = balance_sheet_row("2024-12-31", {"totalStockholderEquity": 300, "preferredStockTotalEquity": 20})
    assert row.preferred_stock == 20.0 and row.as_history_fields()["preferred_stock"] == 20.0
    assert balance_sheet_row("2024-12-31", {}).preferred_stock is None
