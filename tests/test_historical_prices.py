"""
core.historical_prices.apply_year_end_prices: currency handling and merge of year-end prices.
"""

import pytest

from core.historical_prices import apply_year_end_prices


def _financial_data(trading="USD", financials="USD", exchange="NASDAQ", fx_rate=None, historical=None):
    return {
        "history": {"2023-12-31": {}, "2022-12-31": {}},
        "original_stock_currency": trading,
        "financials_currency": financials,
        "exchange": exchange,
        "fx_rate_used": fx_rate,
        "historical_fx_rates": historical or {},
        "warnings": [],
    }


def test_same_currency_prices_are_merged_unchanged():
    fd = _financial_data()
    apply_year_end_prices(fd, {"2023-12-31": 150.0, "2022-12-31": 120.0})
    assert fd["history"]["2023-12-31"]["year_end_price"] == 150.0
    assert fd["history"]["2022-12-31"]["year_end_price"] == 120.0
    assert fd["warnings"] == []


def test_lse_gbx_prices_are_divided_by_100():
    fd = _financial_data(trading="GBX", financials="GBP", exchange="LSE")
    apply_year_end_prices(fd, {"2023-12-31": 1650.0, "2022-12-31": None})
    assert fd["history"]["2023-12-31"]["year_end_price"] == 16.5
    assert fd["history"]["2022-12-31"]["year_end_price"] is None


def test_historical_rates_used_with_current_rate_fallback():
    fd = _financial_data(trading="EUR", financials="USD", fx_rate=1.10, historical={"2023-12-31": 1.05})
    apply_year_end_prices(fd, {"2023-12-31": 100.0, "2022-12-31": 100.0})
    assert fd["history"]["2023-12-31"]["year_end_price"] == pytest.approx(105.0)
    assert fd["history"]["2022-12-31"]["year_end_price"] == pytest.approx(110.0)
    assert any("Years 2022 used current rate 1.1000 as fallback" in w for w in fd["warnings"])


def test_all_historical_rates_available():
    fd = _financial_data(trading="EUR", financials="USD", fx_rate=1.10,
                         historical={"2023-12-31": 1.05, "2022-12-31": 1.02})
    apply_year_end_prices(fd, {"2023-12-31": 100.0, "2022-12-31": 100.0})
    assert fd["history"]["2022-12-31"]["year_end_price"] == pytest.approx(102.0)
    assert any("using date-matched historical FX rates. This ensures" in w for w in fd["warnings"])


def test_no_fx_rate_leaves_prices_unconverted_with_warning():
    fd = _financial_data(trading="EUR", financials="USD", fx_rate=None)
    apply_year_end_prices(fd, {"2023-12-31": 100.0, "2022-12-31": 90.0})
    assert fd["history"]["2023-12-31"]["year_end_price"] == 100.0
    assert any("FX rate unavailable" in w for w in fd["warnings"])


def test_years_without_a_price_are_counted():
    fd = _financial_data()
    apply_year_end_prices(fd, {"2023-12-31": 150.0, "2022-12-31": None})
    assert fd["warnings"] == [
        "Historical prices unavailable for 1 fiscal year ends (no trading data within 7-day window). "
        "Historical P/E and P/B will show N/A for those years."]


def test_unavailable_prices_warn_and_leave_history_untouched():
    fd = _financial_data()
    apply_year_end_prices(fd, None)
    assert "year_end_price" not in fd["history"]["2023-12-31"]
    assert fd["warnings"][0].startswith("Historical prices unavailable from yfinance.")


def test_no_history_warns():
    fd = _financial_data()
    fd["history"] = {}
    apply_year_end_prices(fd, {"2023-12-31": 150.0})
    assert fd["warnings"] == ["No financial history data available - historical price columns will be empty."]
