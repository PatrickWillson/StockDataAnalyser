"""
The dossier's view model: values the output sections display, derived once in core so that
sections only format (M5). Built by DossierGenerator and passed to every section; a section
built on its own (e.g. in a unit test) builds it from the same inputs.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from config.risk_thresholds import PROFIT_MARGIN_SANITY_LIMIT_PCT, RISK_HISTORY_WINDOW_YEARS
from core.financial_data_processor import FinancialDataProcessor
from core.formulas import net_current_asset_value, tangible_equity
from core.price_quote import is_minor_unit, major_currency
from config.data_quality_config import FINANCIAL_HISTORY_YEARS
from core.history import has_income_data, has_statement_data, latest_year


@dataclass(frozen=True)
class HistoryTableRow:
    """One row of the 20-year financial history table."""
    year: str                      # history key ('YYYY-MM-DD')
    row: Mapping[str, Any]
    has_income: bool               # False: a dividend-only row ("[Data Unavailable]")
    bvps: float                    # total equity / shares rounded to 2 dp; 0 when not computable


@dataclass(frozen=True)
class RiskFigures:
    """Figures behind the Risk Factors section (latest reported year unless stated)."""
    liquidity_pct: Optional[float] = None              # average daily volume / shares x 100
    current_ratio: Optional[float] = None
    long_term_debt: float = 0.0
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


def _risk_figures(financial_data: Dict[str, Any], history: Dict[str, Any], years: list,
                  row: Mapping[str, Any]) -> RiskFigures:
    avg_volume = financial_data.get('average_volume', 0)
    shares = row.get('shares_outstanding', 0)
    current_assets = row.get('current_assets', 0.0)
    current_liabilities = row.get('current_liabilities', 0.0)
    long_term_debt = row.get('long_term_debt', 0.0)
    total_debt = row.get('total_debt', 0.0)
    total_assets = row.get('total_assets', 0.0)
    net_current_assets = current_assets - current_liabilities

    # Payment years: every row (a dividend-only row is a real payment year)
    window = years[:RISK_HISTORY_WINDOW_YEARS]
    # Earnings years: reported years only (dividend-only placeholder rows are not years of results)
    earnings_window = [year for year in years if has_statement_data(history[year])][:RISK_HISTORY_WINDOW_YEARS]
    margins = []
    loss_years = 0
    for year in earnings_window:
        revenue = history[year].get('revenue', 0.0)
        net_income = history[year].get('net_income', 0.0)
        if revenue > 0:
            margin = (net_income / revenue) * 100
            # Exclude non-finite margins from near-zero revenue
            if abs(margin) < PROFIT_MARGIN_SANITY_LIMIT_PCT:
                margins.append(margin)
            if net_income < 0:
                loss_years += 1

    # The latest fiscal year's audited dividend per share, never EODHD's forward estimate (F21);
    # history 'dividend' values are payment counts when is_dividend_amounts is False
    latest_div = row.get('dividend', 0.0) if financial_data.get('is_dividend_amounts', False) else 0.0
    eps = row.get('eps', 0.0)
    operating_cash_flow = row.get('operating_cash_flow', 0.0)
    return RiskFigures(
        liquidity_pct=(avg_volume / shares) * 100 if avg_volume > 0 and shares > 0 else None,
        current_ratio=current_assets / current_liabilities if current_liabilities > 0 else None,
        long_term_debt=long_term_debt,
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
        paid_any=any(history[year].get('dividend', 0.0) > 0 for year in years),
        payout_pct=(latest_div / eps) * 100 if latest_div > 0 and eps > 0 else None,
        dividend_coverage=(operating_cash_flow / shares) / latest_div
                          if latest_div > 0 and operating_cash_flow > 0 and shares > 0 else None,
        dividend_years=sum(1 for year in window if history[year].get('dividend', 0.0) > 0),
        history_years=len(years),
    )


@dataclass(frozen=True)
class ReportContext:
    latest_year: Optional[str]                 # newest history key with statement data ('YYYY-MM-DD')
    latest_row: Mapping[str, Any] = field(default_factory=dict)
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
        """The latest reported year as 'YYYY', or None."""
        return self.latest_year.split('-')[0] if self.latest_year else None


def build_report_context(financial_data: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None) -> ReportContext:
    """Derive the display values from the assembled financial data (and metrics)."""
    history = financial_data.get('history') or {}
    years = sorted(history.keys(), reverse=True)
    year = latest_year(history, years, has_statement_data)
    row = history[year] if year else {}

    equity = row.get('total_equity', 0)
    shares = row.get('shares_outstanding', 0)
    has_book = equity > 0 and shares > 0
    tangible = tangible_equity(equity, row.get('intangible_assets', 0), row.get('goodwill', 0)) if has_book else None

    price = financial_data.get('price') or 0
    trailing = row.get('dividend', 0.0) if financial_data.get('is_dividend_amounts', False) else 0.0
    forward = financial_data.get('forward_dividend_rate') or 0.0

    bvps = equity / shares if has_book else None
    api_bvps = financial_data.get('book_value_per_share') or 0
    eps_data = FinancialDataProcessor.extract_3year_eps_data(history) if history else None
    quote_currency = financial_data.get('price_quote_currency') or financial_data.get('original_stock_currency')

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
        latest_ncav=net_current_asset_value(row.get('current_assets', 0), row.get('total_liabilities', 0),
                                            row.get('claims_outside_equity', 0.0)) if row else None,
        quote_currency=quote_currency,
        quote_is_minor_unit=is_minor_unit(quote_currency),
        quote_major_currency=major_currency(quote_currency),
        history_table=tuple(_history_table_row(key, history[key]) for key in years[:FINANCIAL_HISTORY_YEARS]),
    )


def _history_table_row(year: str, row: Mapping[str, Any]) -> HistoryTableRow:
    equity = row.get('total_equity', 0)
    shares = row.get('shares_outstanding', 0)
    return HistoryTableRow(year=year, row=row, has_income=has_income_data(row),
                           bvps=round(equity / shares, 2) if shares > 0 and equity > 0 else 0)
