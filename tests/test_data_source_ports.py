"""
Data-source ports (core/ports.py): every adapter satisfies its port, and the core works from
any FundamentalsSource, not only EODHD.
"""

import pytest

from clients.eodhd_client import EODHDClient
from clients.eodhd_mapper import to_fundamentals
from clients.fx_client import FXClient
from clients.yfinance_client import YFinanceClient
from core.financial_data_assembler import load_financial_data
from core.fundamentals import BalanceSheetRow, CompanyFundamentals, DividendPayment, IncomeStatementRow
from core.graham_math import GrahamCalculator
from core.ports import FundamentalsSource, QuoteSource, RateSource
from core.price_quote import PriceQuote
from output.dossier_generator import DossierGenerator
from tests.fixtures import EODHDFixtures


def test_adapters_satisfy_their_ports():
    assert isinstance(EODHDClient("key"), FundamentalsSource)
    assert isinstance(YFinanceClient(), QuoteSource)
    assert isinstance(FXClient(), RateSource)


def assert_fundamentals_contract(fundamentals: CompanyFundamentals) -> None:
    """What core relies on from any adapter (run it on each new vendor's mapped fixtures)."""
    assert isinstance(fundamentals, CompanyFundamentals)
    assert fundamentals.source and fundamentals.symbol
    for currency in (fundamentals.trading_currency, fundamentals.statement_currency,
                     fundamentals.forward_dividend_currency, fundamentals.market.per_share_currency):
        assert isinstance(currency, str) and len(currency) == 3
    for rows in (fundamentals.annual_balance_sheets, fundamentals.annual_income_statements,
                 fundamentals.quarterly_balance_sheets, fundamentals.quarterly_income_statements):
        period_ends = [row.period_end for row in rows]
        assert period_ends == sorted(period_ends, reverse=True), "statement rows newest first"
    assert all(len(year) == 4 and year.isdigit() for year in fundamentals.shares_by_year)
    assert all(amount >= 0 for amount in fundamentals.annual_dividends_paid.values())
    for payment in fundamentals.dividend_payments or ():
        assert payment.amount >= 0 and len(payment.currency) == 3


def test_eodhd_mapping_meets_the_fundamentals_contract():
    us = to_fundamentals(EODHDFixtures.get_aapl_fundamentals(), EODHDFixtures.get_dividend_api_response(), "AAPL.US")
    lse = to_fundamentals(EODHDFixtures.get_lse_stock_fundamentals(), None, "YU.LSE")
    for fundamentals in (us, lse):
        assert_fundamentals_contract(fundamentals)
    assert us.source == "EODHD" and us.annual_balance_sheets and us.dividend_payments
    # EODHD labels LSE per-share values GBX although they are pounds (CODEBASE_GUIDE §11 E1, E2)
    assert lse.trading_currency == "GBX" and lse.market.per_share_currency == "GBP"


class _InMemorySource:
    """A non-EODHD fundamentals source: what a new vendor adapter has to provide."""

    name = "In-memory vendor"

    def __init__(self, fundamentals: CompanyFundamentals):
        self.fundamentals = fundamentals
        self.requested = None

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        self.requested = ticker
        return self.fundamentals


class _Quotes:
    def get_quote(self, ticker):
        return PriceQuote(40.0, "USD")

    def fetch_historical_prices(self, ticker, start_date, end_date):
        return None

    def match_fiscal_year_end_prices(self, price_data, fiscal_year_ends):
        return {}


class _Rates:
    def get_rate(self, from_currency, to_currency):
        return None

    def fetch_historical_rates(self, from_currency, to_currency, start_date, end_date):
        return None

    def match_fiscal_year_end_rates(self, rate_data, fiscal_year_ends):
        return {}


def _balance_sheet(period_end: str) -> BalanceSheetRow:
    return BalanceSheetRow(period_end=period_end, total_equity=500.0, intangible_assets=0.0, goodwill=0.0,
                           current_assets=400.0, current_liabilities=100.0, total_liabilities=300.0,
                           long_term_debt=50.0, short_term_debt=0.0, total_debt_reported=None,
                           total_assets=800.0, inventory=40.0, noncontrolling_interest=None,
                           shares_outstanding=100.0)


def test_the_core_runs_on_any_fundamentals_source():
    years = [f"{year}-12-31" for year in range(2023, 2013, -1)]
    fundamentals = CompanyFundamentals(
        source="In-memory vendor", symbol="TEST", exchange="US", trading_currency="USD",
        statement_currency="USD", sector="Industrials", industry="Machinery",
        annual_balance_sheets=tuple(_balance_sheet(year) for year in years),
        annual_income_statements=tuple(IncomeStatementRow(year, revenue=1000.0, net_income=50.0, eps=None)
                                       for year in years),
        dividend_payments=tuple(DividendPayment(f"{year[:4]}-06-30", 0.2, "USD") for year in years),
    )
    source = _InMemorySource(fundamentals)
    assert isinstance(source, FundamentalsSource)
    assert_fundamentals_contract(fundamentals)

    financial_data = load_financial_data("TEST.US", source, _Quotes(), _Rates())

    assert source.requested == "TEST.US"
    assert financial_data["price"] == 40.0 and financial_data["currency"] == "USD"
    assert financial_data["history"]["2023-12-31"]["eps"] == 0.5          # 50 / 100 shares
    assert financial_data["history"]["2023-12-31"]["dividend"] == 0.2
    metrics = GrahamCalculator(financial_data).compute()
    assert metrics.defensive_tests["earnings_stability"] == "PASS"
    assert financial_data["data_source"] == "In-memory vendor"
    header = DossierGenerator("TEST.US", financial_data, metrics, []).header.generate()
    assert "# SOURCE: In-memory vendor (Tier 1 Data)" in header


def _with_cash_flow(cash_flow_currency, **operating):
    years = [f"{year}-12-31" for year in range(2023, 2013, -1)]
    return CompanyFundamentals(
        source="In-memory vendor", symbol="TEST", exchange="US", trading_currency="USD", statement_currency="USD",
        annual_balance_sheets=tuple(_balance_sheet(year) for year in years),
        annual_income_statements=tuple(IncomeStatementRow(year, revenue=1000.0, net_income=50.0, eps=None)
                                       for year in years),
        dividend_payments=tuple(DividendPayment(f"{year[:4]}-06-30", 0.2, "USD") for year in years),
        cash_flow_currency=cash_flow_currency,
        annual_operating_cash_flow={"2023-12-31": 80.0, "2022-12-31": 70.0, "2030-12-31": 1.0, **operating})


def test_operating_cash_flow_reaches_statement_years_and_dividend_coverage():
    from core.report_context import build_report_context
    data = load_financial_data("TEST.US", _InMemorySource(_with_cash_flow("USD")), _Quotes(), _Rates())
    assert data["history"]["2023-12-31"]["operating_cash_flow"] == 80.0
    assert "2030-12-31" not in data["history"]                  # no row is created for a cash-flow-only year
    assert "operating_cash_flow" not in data["history"]["2021-12-31"]
    # (80 / 100 shares) / 0.2 dividend per share
    assert build_report_context(data).risk.dividend_coverage == pytest.approx(4.0)


def test_operating_cash_flow_in_another_currency_is_converted_or_left_out():
    class EurRates(_Rates):
        def get_rate(self, from_currency, to_currency):
            return 1.1 if (from_currency, to_currency) == ("EUR", "USD") else None
    converted = load_financial_data("TEST.US", _InMemorySource(_with_cash_flow("EUR")), _Quotes(), EurRates())
    assert converted["history"]["2023-12-31"]["operating_cash_flow"] == pytest.approx(88.0)
    unconverted = load_financial_data("TEST.US", _InMemorySource(_with_cash_flow("EUR")), _Quotes(), _Rates())
    assert "operating_cash_flow" not in unconverted["history"]["2023-12-31"]
    assert any("Could not convert operating cash flow from EUR" in w for w in unconverted["warnings"])
