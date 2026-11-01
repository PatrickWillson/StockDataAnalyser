"""
The dossier's view model: values the output sections display, derived once in core so that
sections only format (M5). Built by DossierGenerator and passed to every section; a section
built on its own (e.g. in a unit test) builds it from the same inputs.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from config.risk_thresholds import PROFIT_MARGIN_SANITY_LIMIT_PCT, RISK_HISTORY_WINDOW_YEARS
from core.history import has_statement_data, latest_year


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
    window_years: int = 0                              # years examined (latest RISK_HISTORY_WINDOW_YEARS rows)
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

    window = years[:RISK_HISTORY_WINDOW_YEARS] if len(years) >= RISK_HISTORY_WINDOW_YEARS else years
    margins = []
    loss_years = 0
    for year in window:
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
        window_years=len(window),
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
    return ReportContext(latest_year=year, latest_row=row, risk=_risk_figures(financial_data, history, years, row))
