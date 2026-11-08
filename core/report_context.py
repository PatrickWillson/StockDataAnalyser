"""
The dossier's view model: values the output sections display, derived once in core so that
sections only format (M5). Built by DossierGenerator and passed to every section; a section
built on its own (e.g. in a unit test) builds it from the same inputs.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from config.risk_thresholds import PROFIT_MARGIN_SANITY_LIMIT_PCT, RISK_HISTORY_WINDOW_YEARS
from core.financial_data_processor import FinancialDataProcessor
from core.formulas import common_equity, net_current_asset_value, tangible_equity
from core.price_quote import is_minor_unit, major_currency
from config.data_quality_config import FINANCIAL_HISTORY_YEARS
from core.history import fiscal_year, has_income_data, has_statement_data, latest_year
from core.models import FinancialData, GrahamResult, HistoryRow, or_default


@dataclass(frozen=True)
class HistoryTableRow:
    """One row of the 20-year financial history table."""
    year: str                      # history key ('YYYY-MM-DD')
    row: HistoryRow
    has_income: bool               # False: a dividend-only row ("[Data Unavailable]")
    bvps: float                    # common equity (total − preferred) / shares, 2 dp; 0 when not computable


@dataclass(frozen=True)
class RiskFigures:
    """Figures behind the Risk Factors section (latest reported year unless stated)."""
    liquidity_pct: Optional[float] = None              # average daily volume / shares x 100
    current_ratio: Optional[float] = None
    long_term_debt: float = 0.0
    long_term_debt_unknown: bool = False               # borrowings reported, long-term debt not identified (§8.9)
    total_debt: float = 0.0
    other_debt: float = 0.0                            # total debt - long-term debt (short-term and leases)
    total_assets: float = 0.0
    net_current_assets: float = 0.0                    # working capital
    lt_debt_to_assets_pct: Optional[float] = None
    total_debt_to_assets_pct: Optional[float] = None
    debt_to_nca_pct: Optional[float] = None
    window_years: int = 0                              # reported years examined for margins and losses
    dividend_window_years: int = 0                     # rows examined for the dividend record
    profit_margins: Tuple[float, ...] = ()
    margin_mean: Optional[float] = None
    margin_stdev: Optional[float] = None               # with at least two margins
    loss_years: int = 0
    latest_dividend: float = 0.0                       # per share; 0 when the history holds payment counts
    paid_any: bool = False
    payout_pct: Optional[float] = None
    dividend_coverage: Optional[float] = None          # operating cash flow per share / dividend
    dividend_years: int = 0                            # rows with a dividend within the window
    history_years: int = 0


def _risk_figures(financial_data: FinancialData, history: Mapping[str, HistoryRow], years: list,
                  row: HistoryRow) -> RiskFigures:
    avg_volume = or_default(financial_data.average_volume, 0)
    shares = or_default(row.shares_outstanding, 0)
    current_assets = or_default(row.current_assets, 0.0)
    current_liabilities = or_default(row.current_liabilities, 0.0)
    long_term_debt_unknown = row.long_term_debt is None       # unknown, shown as such (not as zero debt)
    long_term_debt = 0.0 if long_term_debt_unknown else or_default(row.long_term_debt, 0.0)
    total_debt = or_default(row.total_debt, 0.0)
    total_assets = or_default(row.total_assets, 0.0)
    net_current_assets = current_assets - current_liabilities

    # Payment years: every row (a dividend-only row is a real payment year)
    window = years[:RISK_HISTORY_WINDOW_YEARS]
    # Earnings years: reported years only (dividend-only placeholder rows are not years of results)
    earnings_window = [year for year in years if has_statement_data(history[year])][:RISK_HISTORY_WINDOW_YEARS]
    margins = []
    loss_years = 0
    for year in earnings_window:
        revenue = or_default(history[year].revenue, 0.0)
        net_income = or_default(history[year].net_income, 0.0)
        if revenue > 0:
            margin = (net_income / revenue) * 100
            # Exclude non-finite margins from near-zero revenue
            if abs(margin) < PROFIT_MARGIN_SANITY_LIMIT_PCT:
                margins.append(margin)
            if net_income < 0:
                loss_years += 1

    # The latest fiscal year's audited dividend per share, never EODHD's forward estimate (F21);
    # history 'dividend' values are payment counts when is_dividend_amounts is False
    latest_div = or_default(row.dividend, 0.0) if or_default(financial_data.is_dividend_amounts, False) else 0.0
    eps = or_default(row.eps, 0.0)
    operating_cash_flow = or_default(row.operating_cash_flow, 0.0)
    return RiskFigures(
        liquidity_pct=(avg_volume / shares) * 100 if avg_volume > 0 and shares > 0 else None,
        current_ratio=current_assets / current_liabilities if current_liabilities > 0 else None,
        long_term_debt=long_term_debt,
        long_term_debt_unknown=long_term_debt_unknown,
        total_debt=total_debt,
        other_debt=total_debt - long_term_debt if total_debt > long_term_debt else 0.0,
        total_assets=total_assets,
        net_current_assets=net_current_assets,
        lt_debt_to_assets_pct=(long_term_debt / total_assets) * 100 if total_assets > 0 and long_term_debt > 0 else None,
        total_debt_to_assets_pct=(total_debt / total_assets) * 100 if total_assets > 0 else None,
        debt_to_nca_pct=(long_term_debt / net_current_assets) * 100 if net_current_assets > 0 and long_term_debt > 0 else None,
        window_years=len(earnings_window),
        dividend_window_years=len(window),
        profit_margins=tuple(margins),
        margin_mean=statistics.mean(margins) if margins else None,
        margin_stdev=statistics.stdev(margins) if len(margins) > 1 else None,
        loss_years=loss_years,
        latest_dividend=latest_div,
        paid_any=any(or_default(history[year].dividend, 0.0) > 0 for year in years),
        payout_pct=(latest_div / eps) * 100 if latest_div > 0 and eps > 0 else None,
        dividend_coverage=(operating_cash_flow / shares) / latest_div
                          if latest_div > 0 and operating_cash_flow > 0 and shares > 0 else None,
        dividend_years=sum(1 for year in window if or_default(history[year].dividend, 0.0) > 0),
        history_years=len(years),
    )


@dataclass(frozen=True)
class ReportContext:
    latest_year: Optional[str]                 # newest history key with statement data ('YYYY-MM-DD')
    latest_row: HistoryRow = field(default_factory=HistoryRow)
    risk: RiskFigures = field(default_factory=RiskFigures)
    # Latest reported year, when equity and shares are both positive
    latest_bvps: Optional[float] = None
    latest_tangible_equity: Optional[float] = None
    latest_tbvps: Optional[float] = None
    # Dividends per share and their yields on the current price; the trailing dividend is the
    # latest reported year's (0 when the history holds payment counts), the forward one EODHD's
    # labelled estimate (display only)
    trailing_dividend: float = 0.0
    trailing_yield_pct: Optional[float] = None
    forward_dividend: float = 0.0
    forward_yield_pct: Optional[float] = None
    # EODHD Highlights.BookValue (converted) against our latest BVPS, % difference (labelled comparison)
    api_bvps_diff_pct: Optional[float] = None
    # The three latest reported years' EPS (FinancialDataProcessor.extract_3year_eps_data); None
    # without history
    three_year_eps: Optional[Mapping[str, Any]] = None
    three_year_eps_avg: Optional[float] = None
    # Latest reported year: current assets - total liabilities - claims ahead of the common
    latest_ncav: Optional[float] = None
    # Quote currency (yfinance, else EODHD's trading code) and whether it is a minor unit (GBp, ZAc ...)
    quote_currency: Optional[str] = None
    quote_is_minor_unit: bool = False
    quote_major_currency: Optional[str] = None
    # Latest FINANCIAL_HISTORY_YEARS rows, newest first
    history_table: Tuple[HistoryTableRow, ...] = ()

    @property
    def latest_year_label(self) -> Optional[str]:
        """The latest reported fiscal year as 'YYYY', or None."""
        return fiscal_year(self.latest_year) if self.latest_year else None


def build_report_context(financial_data: Union[FinancialData, Dict[str, Any]],
                         metrics: Union[GrahamResult, Dict[str, Any], None] = None) -> ReportContext:
    """Derive the display values from the assembled financial data (and metrics)."""
    financial_data = FinancialData.from_dict(financial_data)
    history = financial_data.history or {}
    years = sorted(history.keys(), reverse=True)
    year = latest_year(history, years, has_statement_data)
    row = history[year] if year else HistoryRow()

    preferred = or_default(row.preferred_stock, 0)
    equity = common_equity(or_default(row.total_equity, 0), preferred)    # the common's equity (§3.5)
    shares = or_default(row.shares_outstanding, 0)
    has_book = equity > 0 and shares > 0
    tangible = tangible_equity(equity, or_default(row.intangible_assets, 0), or_default(row.goodwill, 0)) if has_book else None

    price = financial_data.price or 0
    trailing = or_default(row.dividend, 0.0) if or_default(financial_data.is_dividend_amounts, False) else 0.0
    forward = financial_data.forward_dividend_rate or 0.0

    bvps = equity / shares if has_book else None
    api_bvps = financial_data.book_value_per_share or 0
    eps_data = FinancialDataProcessor.extract_3year_eps_data(history) if history else None
    quote_currency = financial_data.price_quote_currency or or_default(financial_data.original_stock_currency, None)

    def yield_pct(amount):
        return (amount / price) * 100 if amount and amount > 0 and price > 0 else None

    return ReportContext(
        latest_year=year, latest_row=row, risk=_risk_figures(financial_data, history, years, row),
        latest_bvps=bvps,
        latest_tangible_equity=tangible,
        latest_tbvps=tangible / shares if has_book else None,
        trailing_dividend=trailing, trailing_yield_pct=yield_pct(trailing),
        forward_dividend=forward, forward_yield_pct=yield_pct(forward),
        api_bvps_diff_pct=abs(bvps - api_bvps) / api_bvps * 100 if bvps is not None and api_bvps > 0 else None,
        three_year_eps=eps_data,
        three_year_eps_avg=sum(eps_data['eps_values']) / 3 if eps_data and eps_data['valid'] else None,
        latest_ncav=net_current_asset_value(or_default(row.current_assets, 0), or_default(row.total_liabilities, 0),
                                            or_default(row.claims_outside_equity, 0.0), preferred) if year else None,
        quote_currency=quote_currency,
        quote_is_minor_unit=is_minor_unit(quote_currency),
        quote_major_currency=major_currency(quote_currency),
        history_table=tuple(_history_table_row(key, history[key]) for key in years[:FINANCIAL_HISTORY_YEARS]),
    )


def _history_table_row(year: str, row: HistoryRow) -> HistoryTableRow:
    equity = common_equity(or_default(row.total_equity, 0), or_default(row.preferred_stock, 0))
    shares = or_default(row.shares_outstanding, 0)
    return HistoryTableRow(year=year, row=row, has_income=has_income_data(row),
                           bvps=round(equity / shares, 2) if shares > 0 and equity > 0 else 0)
