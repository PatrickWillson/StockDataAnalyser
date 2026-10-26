"""
Snapshot test scenarios, built by deterministically varying the payloads in tests/fixtures.py.

The base fixtures only cover 2-3 annual years and no periodic data, so helpers here:
  - extend_years: add older fiscal years (values decline by a fixed rate per year back)
  - add_periodic: derive quarterly or semi-annual statements from the latest annual year
so that EPV, the 10/20-year Graham tests and TTM analysis are all exercised.
"""

import calendar
import copy
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from fixtures import EODHDFixtures
from snapshot_fakes import closes_around

STATEMENTS = ("Balance_Sheet", "Income_Statement", "Cash_Flow")
BALANCE_ONLY_FIELDS = {"date", "filing_date", "currency_symbol"}


@dataclass
class Scenario:
    name: str
    ticker: str                                   # as passed to the CLI, e.g. "AAPL.US"
    fundamentals: Dict[str, Any]
    yahoo: Dict[str, Dict[str, Any]]              # FakeYFinanceModule symbols
    dividends: Optional[List[Dict[str, Any]]] = None  # dividend endpoint payload; None -> 404
    description: str = ""


# --- payload helpers -------------------------------------------------------------------

def _scale(value: Any, factor: float) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return int(round(value * factor))
    if isinstance(value, float):
        return value * factor
    return value


def _shift_year(iso_date: str, years: int) -> str:
    d = date.fromisoformat(iso_date)
    day = min(d.day, calendar.monthrange(d.year - years, d.month)[1])
    return date(d.year - years, d.month, day).isoformat()


def _months_before(iso_date: str, months: int) -> str:
    d = date.fromisoformat(iso_date)
    total = d.year * 12 + (d.month - 1) - months
    year, month = divmod(total, 12)
    return date(year, month + 1, calendar.monthrange(year, month + 1)[1]).isoformat()


def fiscal_year_ends(raw: Dict[str, Any]) -> List[str]:
    return sorted(raw["Financials"]["Income_Statement"]["yearly"])


def extend_years(raw: Dict[str, Any], total_years: int, decline: float = 0.05,
                 share_growth: float = 0.02) -> Dict[str, Any]:
    """Add older fiscal years until each statement has total_years annual entries."""
    raw = copy.deepcopy(raw)
    for statement in STATEMENTS:
        yearly = raw["Financials"][statement]["yearly"]
        earliest = min(yearly)
        base = yearly[earliest]
        for years_back in range(1, total_years - len(yearly) + 1):
            new_date = _shift_year(earliest, years_back)
            factor = (1 - decline) ** years_back
            entry = {k: (v if k in BALANCE_ONLY_FIELDS else _scale(v, factor)) for k, v in base.items()}
            entry["date"] = new_date
            if "filing_date" in entry:
                entry["filing_date"] = _shift_year(entry["filing_date"], years_back)
            yearly[new_date] = entry

    annual_shares = raw.get("outstandingShares", {}).get("annual", {})
    if annual_shares:
        by_year = {int(v["date"]): v["shares"] for v in annual_shares.values()}
        oldest_year, oldest_shares = min(by_year.items())
        for fye in fiscal_year_ends(raw):
            year = int(fye[:4])
            if year not in by_year:
                by_year[year] = int(oldest_shares * (1 + share_growth) ** (oldest_year - year))
        raw["outstandingShares"]["annual"] = {
            str(i): {"date": str(year), "shares": shares}
            for i, (year, shares) in enumerate(sorted(by_year.items(), reverse=True))
        }
    return raw


def add_periodic(raw: Dict[str, Any], periods_per_year: int, count: int) -> Dict[str, Any]:
    """
    Derive `count` periodic statements (4/year = quarterly, 2/year = semi-annual) ending at
    the latest fiscal year end. Income values are the latest annual values / periods_per_year;
    balance sheet values are the latest annual balance sheet.
    """
    raw = copy.deepcopy(raw)
    months = 12 // periods_per_year
    latest = fiscal_year_ends(raw)[-1]
    for statement in ("Balance_Sheet", "Income_Statement"):
        annual = raw["Financials"][statement]["yearly"][latest]
        periodic = {}
        for i in range(count):
            period_end = _months_before(latest, months * i) if i else latest
            if statement == "Income_Statement":
                entry = {k: (v if k in BALANCE_ONLY_FIELDS else _scale(v, 1 / periods_per_year))
                         for k, v in annual.items()}
            else:
                entry = dict(annual)
            entry["date"] = period_end
            periodic[period_end] = entry
        raw["Financials"][statement]["quarterly"] = periodic
    return raw


def set_currencies(raw: Dict[str, Any], exchange: str, trading: str, financials: str) -> Dict[str, Any]:
    raw = copy.deepcopy(raw)
    raw["General"]["Exchange"] = exchange
    raw["General"]["CurrencyCode"] = trading
    for statement in STATEMENTS:
        raw["Financials"][statement]["currency_symbol"] = financials
        for period in ("yearly", "quarterly"):
            for entry in raw["Financials"][statement].get(period, {}).values():
                if "currency_symbol" in entry:
                    entry["currency_symbol"] = financials
    return raw


def yahoo_symbol(symbol: str, last: float, anchors: List[str],
                 price_for: Optional[Callable[[str], float]] = None) -> Dict[str, Dict[str, Any]]:
    """One Yahoo symbol with a current price and closes around each anchor date."""
    if price_for is None:
        latest_year = int(max(anchors)[:4])
        price_for = lambda d: last * (0.92 ** (latest_year - int(d[:4])))  # noqa: E731
    return {symbol: {"last": last, "closes": closes_around(anchors, price_for)}}


# --- scenarios -------------------------------------------------------------------------

def us_mature_quarterly() -> Scenario:
    raw = add_periodic(extend_years(EODHDFixtures.get_aapl_fundamentals(), 12), 4, 6)
    return Scenario(
        "us_mature_quarterly", "AAPL.US", raw,
        yahoo=yahoo_symbol("AAPL", 187.45, fiscal_year_ends(raw)),
        dividends=EODHDFixtures.get_dividend_api_response(),
        description="US/USD, 12 years, quarterly TTM, dividend endpoint data",
    )


def us_young_company() -> Scenario:
    raw = EODHDFixtures.get_aapl_fundamentals()
    return Scenario(
        "us_young_company", "AAPL.US", raw,
        yahoo=yahoo_symbol("AAPL", 187.45, fiscal_year_ends(raw)),
        description="US/USD, only 3 annual years (EPV and 10-year tests unavailable), no TTM",
    )


def lse_gbx_london_fix_semi_annual() -> Scenario:
    raw = add_periodic(extend_years(EODHDFixtures.get_lse_stock_fundamentals(), 10), 2, 4)
    return Scenario(
        "lse_gbx_london_fix_semi_annual", "YU.LSE", raw,
        yahoo=yahoo_symbol("YU.L", 1650.0, fiscal_year_ends(raw)),
        description="LSE, trades in GBX, financials GBP, P/E > 500 in pence -> London Fix, semi-annual TTM",
    )


def lse_gbx_weak_quarter() -> Scenario:
    raw = add_periodic(extend_years(EODHDFixtures.get_lse_stock_fundamentals(), 10), 4, 6)
    latest = max(raw["Financials"]["Income_Statement"]["quarterly"])
    for field in ("netIncome", "netIncomeFromContinuingOps"):
        raw["Financials"]["Income_Statement"]["quarterly"][latest][field] = 500_000
    return Scenario(
        "lse_gbx_weak_quarter", "YU.LSE", raw,
        yahoo=yahoo_symbol("YU.L", 1650.0, fiscal_year_ends(raw)),
        description="LSE, quarterly TTM with one weak quarter (P/E on that quarter > 500): "
                    "TTM must not re-apply the London Fix to the already-converted price",
    )


def lse_gbx_low_pe() -> Scenario:
    raw = extend_years(EODHDFixtures.get_lse_stock_fundamentals(), 10)
    return Scenario(
        "lse_gbx_low_pe", "YU.LSE", raw,
        yahoo=yahoo_symbol("YU.L", 150.0, fiscal_year_ends(raw)),
        description="LSE, GBX price with P/E < 500 -> plain GBX/100 branch",
    )


def lse_gbp_label_pence_price() -> Scenario:
    raw = set_currencies(extend_years(EODHDFixtures.get_lse_stock_fundamentals(), 10), "LSE", "GBP", "GBP")
    return Scenario(
        "lse_gbp_label_pence_price", "YU.LSE", raw,
        yahoo=yahoo_symbol("YU.L", 1650.0, fiscal_year_ends(raw)),
        description="LSE labelled GBP but price quoted in pence -> London Fix via P/E heuristic",
    )


def tsx_cad() -> Scenario:
    raw = set_currencies(extend_years(EODHDFixtures.get_aapl_fundamentals(), 10), "TO", "CAD", "CAD")
    return Scenario(
        "tsx_cad", "AAPL.TO", raw,
        yahoo=yahoo_symbol("AAPL.TO", 255.10, fiscal_year_ends(raw)),
        description="Toronto, CAD trading and financials",
    )


def xetra_eur_usd_financials() -> Scenario:
    raw = set_currencies(extend_years(EODHDFixtures.get_aapl_fundamentals(), 10), "XETRA", "EUR", "USD")
    anchors = fiscal_year_ends(raw)
    yahoo = yahoo_symbol("AAPL.DE", 173.20, anchors)
    yahoo.update(yahoo_symbol("EURUSD=X", 1.0825, anchors,
                              price_for=lambda d: 1.0 + (int(d[:4]) % 7) * 0.03))
    return Scenario(
        "xetra_eur_usd_financials", "AAPL.XETRA", raw, yahoo=yahoo,
        description="Trades in EUR, financials in USD -> current and historical FX conversion",
    )


def negative_tangible_equity() -> Scenario:
    raw = extend_years(EODHDFixtures.get_aapl_fundamentals(), 10)
    for entry in raw["Financials"]["Balance_Sheet"]["yearly"].values():
        # EODHD's key is "goodWill"; the base fixture's lowercase "goodwill" is never parsed
        entry["goodWill"] = entry["totalStockholderEquity"] * 2
    return Scenario(
        "negative_tangible_equity", "AAPL.US", raw,
        yahoo=yahoo_symbol("AAPL", 187.45, fiscal_year_ends(raw)),
        description="Goodwill exceeds equity -> negative TBVPS, Graham Number unavailable",
    )


def dividend_counts_only() -> Scenario:
    raw = extend_years(EODHDFixtures.get_aapl_fundamentals(), 10)
    for entry in raw["Financials"]["Cash_Flow"]["yearly"].values():
        entry.pop("dividendsPaid", None)
    raw["SplitsDividends"].pop("ForwardAnnualDividendRate", None)
    return Scenario(
        "dividend_counts_only", "AAPL.US", raw,
        yahoo=yahoo_symbol("AAPL", 187.45, fiscal_year_ends(raw)),
        description="No dividend amounts anywhere; only NumberDividendsByYear payment counts",
    )


ALL_SCENARIOS = [
    us_mature_quarterly,
    us_young_company,
    lse_gbx_london_fix_semi_annual,
    lse_gbx_low_pe,
    lse_gbx_weak_quarter,
    lse_gbp_label_pence_price,
    tsx_cad,
    xetra_eur_usd_financials,
    negative_tangible_equity,
    dividend_counts_only,
]
