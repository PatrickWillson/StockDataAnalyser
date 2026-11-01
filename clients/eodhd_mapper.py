"""
EODHD → CompanyFundamentals (core/fundamentals.py).

The only place that knows EODHD's JSON: the fundamentals endpoint (`General`, `Highlights`,
`Financials`, `SplitsDividends`, `outstandingShares`, ...) and the Dividend API records. EODHD
labelling quirks are corrected here, so core sees true currencies (CODEBASE_GUIDE §11 lists the
readings of EODHD fields that are still pending confirmation).
"""

import logging
from typing import Any, Dict, List, Mapping, Optional

from core.fundamentals import (BalanceSheetRow, CompanyFundamentals, DatedDividend, DividendPayment,
                               IncomeStatementRow, MarketData, number_or_zero, optional_float)

logger = logging.getLogger(__name__)

SOURCE_NAME = "EODHD"
STATEMENT_PERIODS = ("yearly", "quarterly")
_MISSING_MARKERS = (None, "", "NA", "N/A")


sanitize = number_or_zero  # raw EODHD number -> float; null / "" / "NA" / "N/A" / junk -> 0.0


def _section(value: Any) -> Mapping[str, Any]:
    """A JSON object, or {} when EODHD sent null / something else."""
    return value if isinstance(value, Mapping) else {}


def _pound_scale(currency: str, exchange: str) -> str:
    """
    EODHD labels LSE per-share dividend and book values GBX although they are in pounds
    (CODEBASE_GUIDE §11 E1, E2): their true currency is GBP.
    """
    return "GBP" if exchange == "LSE" and currency == "GBX" else currency


# --- Financial statements -------------------------------------------------------------------

def balance_sheet_row(period_end: str, raw: Mapping[str, Any]) -> BalanceSheetRow:
    # EODHD uses several field names for the share count; the first truthy raw value wins
    shares_raw = (raw.get('commonStockSharesOutstanding') or raw.get('weightedAverageShsOut')
                  or raw.get('weightedAverageShsOutDil') or 0)
    return BalanceSheetRow(
        period_end=period_end,
        total_equity=optional_float(raw.get('totalStockholderEquity')),
        intangible_assets=optional_float(raw.get('intangibleAssets')),
        goodwill=optional_float(raw.get('goodWill')),
        current_assets=optional_float(raw.get('totalCurrentAssets')),
        current_liabilities=optional_float(raw.get('totalCurrentLiabilities')),
        total_liabilities=optional_float(raw.get('totalLiab')),
        long_term_debt=optional_float(raw.get('longTermDebt', 0)),
        short_term_debt=optional_float(raw.get('shortTermDebt', 0)),
        total_debt_reported=optional_float(raw.get('shortLongTermDebtTotal', 0)),
        total_assets=optional_float(raw.get('totalAssets')),
        inventory=optional_float(raw.get('inventory')),
        noncontrolling_interest=optional_float(raw.get('noncontrollingInterestInConsolidatedEntity')),
        shares_outstanding=optional_float(shares_raw),
    )


def income_statement_row(period_end: str, raw: Mapping[str, Any]) -> IncomeStatementRow:
    eps_raw = raw.get('eps')
    if eps_raw in _MISSING_MARKERS[:3]:
        eps_raw = raw.get('basicEPS') or raw.get('epsBasic')
    # Earnings for the common stock, special items included (GRAHAM_METHODOLOGY §2.3: special
    # charges and credits "should be included in the average earnings"). Never
    # netIncomeFromContinuingOps: it drops those items and EODHD reports it before minority
    # interest (WLKP 2024: 369.2M vs 62.4M attributable, ~6x the real EPS)
    net_income_raw = raw.get('netIncomeApplicableToCommonShares')
    if net_income_raw in _MISSING_MARKERS[:3]:
        net_income_raw = raw.get('netIncome')
    return IncomeStatementRow(
        period_end=period_end,
        revenue=optional_float(raw.get('totalRevenue')),
        net_income=optional_float(net_income_raw),
        eps=optional_float(eps_raw),
    )


def _parse_rows(data: Mapping[str, Any], statement: str, period: str, parse_row) -> List[Any]:
    if period not in STATEMENT_PERIODS:
        raise ValueError(f"period must be one of {STATEMENT_PERIODS}, got {period!r}")
    rows: List[Any] = []
    try:
        section = data.get('Financials', {}).get(statement, {}).get(period, {})
        if not section:
            return rows
        for period_end in sorted(section.keys(), reverse=True):
            rows.append(parse_row(period_end, section[period_end]))
    except (KeyError, TypeError, AttributeError):
        # Malformed section or row: keep the rows parsed so far
        pass
    return rows


def parse_balance_sheet_rows(data: Mapping[str, Any], period: str = "yearly") -> List[BalanceSheetRow]:
    """Balance sheet rows for `period` ("yearly" or "quarterly"), newest first."""
    return _parse_rows(data, 'Balance_Sheet', period, balance_sheet_row)


def parse_income_statement_rows(data: Mapping[str, Any], period: str = "yearly") -> List[IncomeStatementRow]:
    """Income statement rows for `period` ("yearly" or "quarterly"), newest first."""
    return _parse_rows(data, 'Income_Statement', period, income_statement_row)


# --- Company and share data -----------------------------------------------------------------

def extract_ceo_name(data: Mapping[str, Any]) -> str:
    """CEO from General.Officers (a dict with numeric keys "0", "1", ...), else the first officer."""
    try:
        officers = data.get('General', {}).get('Officers', {})
        if isinstance(officers, dict) and officers:
            for officer in officers.values():
                if isinstance(officer, dict):
                    title = (officer.get('Title') or '').lower()
                    if 'chief executive' in title or 'ceo' in title:
                        return officer.get('Name') or 'N/A'
            first_officer = officers.get('0', {})
            if isinstance(first_officer, dict):
                return first_officer.get('Name') or 'N/A'
    except (KeyError, TypeError, AttributeError):
        pass
    return 'N/A'


def extract_shares_outstanding(data: Mapping[str, Any]) -> float:
    """Current share count from SharesStats.SharesOutstanding (market data)."""
    try:
        return sanitize(data.get('SharesStats', {}).get('SharesOutstanding', 0))
    except (KeyError, TypeError, AttributeError):
        return 0.0


def extract_shares_by_year(data: Mapping[str, Any]) -> Dict[str, float]:
    """Reported share count per year from outstandingShares.annual ({'YYYY': shares})."""
    shares_by_year = {}
    try:
        outstanding_shares_data = data.get('outstandingShares', {}).get('annual', {})
        if outstanding_shares_data:
            for item in outstanding_shares_data.values():
                if isinstance(item, dict) and 'date' in item and 'shares' in item:
                    # Sanitise per row so one malformed row doesn't discard the others
                    shares = sanitize(item['shares'])
                    if shares > 0:
                        shares_by_year[str(item['date'])] = shares
        return shares_by_year
    except (KeyError, TypeError, AttributeError):
        return {}


def _latest_statement_shares(data: Mapping[str, Any]) -> float:
    """First (most recent) outstandingShares.annual entry with a share count."""
    for item in _section(_section(data.get('outstandingShares')).get('annual')).values():
        if isinstance(item, dict) and 'shares' in item:
            return sanitize(item.get('shares'))
    return 0.0


# --- Dividends ------------------------------------------------------------------------------

def dividend_payments(records: Optional[List[Mapping[str, Any]]], trading_currency: str,
                      exchange: str) -> Optional[tuple]:
    """
    Dividend API records -> DividendPayment (None when the endpoint gave nothing). A record
    without a currency is in the trading currency; LSE records labelled GBX are pounds (E1).
    """
    if not records:
        return None
    return tuple(
        DividendPayment(
            date=record.get('paymentDate') or record.get('date'),
            amount=sanitize(record.get('value', 0)),
            currency=_pound_scale(record.get('currency') or trading_currency, exchange),
        )
        for record in records
    )


def _annual_dividends_paid(data: Mapping[str, Any]) -> Dict[str, float]:
    """Cash_Flow.yearly dividendsPaid as positive totals ({period end: amount})."""
    paid = {}
    cash_flow = _section(_section(_section(data.get('Financials')).get('Cash_Flow')).get('yearly'))
    for period_end, entry in cash_flow.items():
        if not isinstance(entry, dict):
            continue
        dividends_paid = entry.get('dividendsPaid')
        if dividends_paid and dividends_paid != 'null':
            try:
                paid[period_end] = abs(float(dividends_paid))
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse dividendsPaid for {period_end}: {e}")
    return paid


def _dividend_amounts(splits_divs: Mapping[str, Any]) -> tuple:
    """SplitsDividends.Dividends (date + amount, no currency)."""
    dividend_list = splits_divs.get('Dividends', [])
    if not isinstance(dividend_list, list):
        return ()
    return tuple(
        DatedDividend(date=div['Date'],
                      amount=sanitize(div.get('Value') or div.get('Dividend') or div.get('Amount')))
        for div in dividend_list if isinstance(div, dict) and 'Date' in div
    )


def _dividend_counts(splits_divs: Mapping[str, Any]) -> Dict[str, float]:
    """SplitsDividends.NumberDividendsByYear in either of its shapes -> {'YYYY': count}."""
    div_data = splits_divs.get('NumberDividendsByYear', {})
    counts: Dict[str, float] = {}
    if not isinstance(div_data, dict) or not div_data:
        return counts
    first_value = div_data[list(div_data.keys())[0]]
    if isinstance(first_value, dict) and 'Year' in first_value and 'Count' in first_value:
        # Indexed: {"0": {"Year": 2023, "Count": 4}, ...}
        for value in div_data.values():
            if isinstance(value, dict) and 'Year' in value and 'Count' in value:
                counts[str(value['Year'])] = sanitize(value['Count'])
    elif all(isinstance(k, str) and k.isdigit() and len(k) == 4 for k in list(div_data.keys())[:3]):
        # Year-keyed: {"2023": 4, ...}
        for year, value in div_data.items():
            counts[year] = sanitize(value)
    return counts


def _forward_dividend_rate(splits_divs: Mapping[str, Any]) -> Optional[float]:
    forward_rate = splits_divs.get('ForwardAnnualDividendRate')
    return sanitize(forward_rate) if forward_rate else forward_rate


# --- The whole payload ----------------------------------------------------------------------

def to_fundamentals(data: Mapping[str, Any], dividend_records: Optional[List[Mapping[str, Any]]] = None,
                    ticker: str = "") -> CompanyFundamentals:
    """
    Args:
        data: EODHD fundamentals JSON (https://eodhd.com/api/fundamentals/{ticker})
        dividend_records: EODHD Dividend API records (https://eodhd.com/api/div/{ticker}), or None
        ticker: The ticker as requested (symbol fallback when General.Code is absent)
    """
    general = _section(data.get('General'))
    exchange = general.get('Exchange', 'UNKNOWN')
    trading_currency = general.get('CurrencyCode', 'USD')
    statement_currency = _section(_section(data.get('Financials')).get('Balance_Sheet')).get('currency_symbol', 'USD')
    if not statement_currency:
        statement_currency = 'USD'
    splits_divs = _section(data.get('SplitsDividends'))
    highlights = _section(data.get('Highlights'))
    shares_stats = _section(data.get('SharesStats'))
    technicals = _section(data.get('Technicals'))
    return CompanyFundamentals(
        source=SOURCE_NAME,
        symbol=general.get('Code', ticker.split('.')[0]),
        exchange=exchange,
        trading_currency=trading_currency,
        statement_currency=statement_currency,
        name=general.get('Name'),
        sector=general.get('Sector'),
        industry=general.get('Industry'),
        employees=general.get('FullTimeEmployees'),
        ceo_name=extract_ceo_name(data),
        is_delisted=bool(general.get('IsDelisted', False)),
        updated_at=general.get('UpdatedAt'),
        annual_balance_sheets=tuple(parse_balance_sheet_rows(data, 'yearly')),
        annual_income_statements=tuple(parse_income_statement_rows(data, 'yearly')),
        quarterly_balance_sheets=tuple(parse_balance_sheet_rows(data, 'quarterly')),
        quarterly_income_statements=tuple(parse_income_statement_rows(data, 'quarterly')),
        shares_outstanding=extract_shares_outstanding(data),
        shares_by_year=extract_shares_by_year(data),
        latest_statement_shares=_latest_statement_shares(data),
        dividend_payments=dividend_payments(dividend_records, trading_currency, exchange),
        annual_dividends_paid=_annual_dividends_paid(data),
        cash_flow_currency=_section(_section(data.get('Financials')).get('Cash_Flow')).get('currency_symbol', 'USD'),
        dividend_amounts=_dividend_amounts(splits_divs),
        dividend_counts_by_year=_dividend_counts(splits_divs),
        forward_dividend_rate=_forward_dividend_rate(splits_divs),
        forward_dividend_currency=_pound_scale(trading_currency, exchange),
        market=MarketData(
            dividend_per_share=sanitize(highlights.get('DividendShare')),
            dividend_yield=sanitize(highlights.get('DividendYield')),
            pe_ratio=sanitize(highlights.get('PERatio')),
            book_value_per_share=sanitize(highlights.get('BookValue')),
            roe=sanitize(highlights.get('ReturnOnEquityTTM')),
            roa=sanitize(highlights.get('ReturnOnAssetsTTM')),
            profit_margin=sanitize(highlights.get('ProfitMargin')),
            enterprise_value=sanitize(_section(data.get('Valuation')).get('EnterpriseValue')),
            insider_ownership=sanitize(shares_stats.get('PercentInsiders')),
            institutional_ownership=sanitize(shares_stats.get('PercentInstitutions')),
            beta=sanitize(technicals.get('Beta')),
            week_52_high=sanitize(technicals.get('52WeekHigh')),
            week_52_low=sanitize(technicals.get('52WeekLow')),
            per_share_currency=_pound_scale(trading_currency, exchange),
        ),
    )
