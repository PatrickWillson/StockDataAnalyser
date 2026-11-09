"""
Yahoo Finance (yfinance) company data -> pieces of CompanyFundamentals (free resolution path).

The only code that knows Yahoo's `info` keys. Supplies what SEC filings do not carry in usable form:
per-payment dividends, stock splits (for the share basis of EDGAR per-share facts), the profile
(name, sector, industry, employees, CEO) and Yahoo's pre-computed market figures, which are display /
labelled comparison only (CLAUDE.md raw-data rule), exactly like EODHD's Highlights.

annual_statements maps Yahoo's annual statement line items (raw lines, not ratios) for companies with no XBRL filings
(Germany, Ireland, AIM): Graham's analyst used the statistical services where the original reports were not to hand
(Security Analysis ch. 3), and Yahoo's tested more accurate than Eulerpool's (claude-output/YAHOO_VS_XBRL_EULERPOOL_*).
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple

from clients.edgar_mapper import EdgarAnnualData
from clients.yfinance_client import YahooCompanyData, YahooStatements
from core.fundamentals import BalanceSheetRow, DividendPayment, IncomeStatementRow, MarketData, number_or_zero, optional_float
from core.history import fiscal_year


@dataclass(frozen=True)
class YahooProfile:
    name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]           # Yahoo's industry names, e.g. "Utilities - Regulated Electric"
    employees: Optional[int]
    ceo_name: str
    quote_currency: Optional[str]     # trading currency as Yahoo quotes it (USD, GBp, ...)
    financial_currency: Optional[str]


def _ceo(officers: Any) -> str:
    """The officer titled CEO / Chief Executive (Yahoo's companyOfficers), else 'N/A'."""
    for officer in officers or ():
        if not isinstance(officer, Mapping):
            continue
        title = str(officer.get("title") or "").upper()
        if "CEO" in title or "CHIEF EXECUTIVE" in title:
            return " ".join(str(officer.get("name") or "").split()) or "N/A"
    return "N/A"


def profile(data: YahooCompanyData) -> YahooProfile:
    info = data.info
    employees = info.get("fullTimeEmployees")
    return YahooProfile(
        name=info.get("longName") or info.get("shortName"),
        sector=info.get("sector"),
        industry=info.get("industry"),
        employees=int(employees) if isinstance(employees, (int, float)) and employees > 0 else None,
        ceo_name=_ceo(info.get("companyOfficers")),
        quote_currency=info.get("currency"),
        financial_currency=info.get("financialCurrency"),
    )


def dividend_payments(data: YahooCompanyData, currency: str) -> Optional[Tuple[DividendPayment, ...]]:
    """Every dividend (ex-date, split-adjusted amount per share); None when Yahoo lists none."""
    payments = tuple(DividendPayment(date=date, amount=amount, currency=currency)
                     for date, amount in data.dividends if amount and amount > 0)
    return payments or None


def splits(data: YahooCompanyData) -> Sequence[Tuple[str, float]]:
    """(date, shares after / shares before) for each stock split."""
    return tuple((date, ratio) for date, ratio in data.splits if ratio and ratio > 0)


def _percent(value: Any) -> float:
    """Yahoo's ownership shares are fractions (0.0171); the dossier shows percent (1.71)."""
    return number_or_zero(value) * 100


def market_data(data: YahooCompanyData) -> MarketData:
    info = data.info
    return MarketData(
        dividend_per_share=number_or_zero(info.get("trailingAnnualDividendRate")),
        dividend_yield=number_or_zero(info.get("trailingAnnualDividendYield")),
        pe_ratio=number_or_zero(info.get("trailingPE")),
        book_value_per_share=number_or_zero(info.get("bookValue")),
        roe=number_or_zero(info.get("returnOnEquity")),
        roa=number_or_zero(info.get("returnOnAssets")),
        profit_margin=number_or_zero(info.get("profitMargins")),
        enterprise_value=number_or_zero(info.get("enterpriseValue")),
        insider_ownership=_percent(info.get("heldPercentInsiders")),
        institutional_ownership=_percent(info.get("heldPercentInstitutions")),
        beta=number_or_zero(info.get("beta")),
        week_52_high=number_or_zero(info.get("fiftyTwoWeekHigh")),
        week_52_low=number_or_zero(info.get("fiftyTwoWeekLow")),
        per_share_currency=info.get("financialCurrency") or info.get("currency") or "USD",
    )


def total_shares(data: YahooCompanyData) -> Optional[float]:
    """Yahoo's share count across all classes (`impliedSharesOutstanding`), else the quoted class's."""
    info = data.info or {}
    return optional_float(info.get("impliedSharesOutstanding")) or optional_float(info.get("sharesOutstanding"))


def forward_dividend_rate(data: YahooCompanyData) -> Optional[float]:
    """Yahoo's forward annual dividend (an estimate: labelled display only, F21)."""
    rate = number_or_zero(data.info.get("dividendRate"))
    return rate or None


# Yahoo statement rows -> fields (first row with a value wins)
INCOME_ROWS = {"revenue": ("Total Revenue", "Operating Revenue"),
               "net_income": ("Net Income Common Stockholders", "Net Income"),
               "eps": ("Basic EPS",)}
BALANCE_ROWS = {"total_equity": ("Stockholders Equity", "Common Stock Equity"),
                "total_assets": ("Total Assets",), "total_liabilities": ("Total Liabilities Net Minority Interest",),
                "current_assets": ("Current Assets",), "current_liabilities": ("Current Liabilities",),
                "inventory": ("Inventory",), "goodwill": ("Goodwill",), "intangibles": ("Other Intangible Assets",),
                "minority": ("Minority Interest",), "short_term_debt": ("Current Debt And Capital Lease Obligation", "Current Debt"),
                "shares": ("Ordinary Shares Number", "Share Issued"),
                "noncurrent_liabilities": ("Total Non Current Liabilities Net Minority Interest",)}
# Long-term debt counts lease liabilities (GRAHAM_METHODOLOGY §8.10): Yahoo's debt-and-lease total, but only when Yahoo
# reports the lease line it contains (IFRS 16 leases: SAP, Hornbach); otherwise all non-current liabilities, the upper
# bound (§8.4, §8.9), since operating leases may be missing (US GAAP: Coca-Cola)
DEBT_WITH_LEASES, LEASE_ROWS = "Long Term Debt And Capital Lease Obligation", ("Long Term Capital Lease Obligation", "Capital Lease Obligations")
CASHFLOW_ROWS = {"operating_cash_flow": ("Operating Cash Flow",), "dividends_paid": ("Cash Dividends Paid", "Common Stock Dividend Paid")}
SOURCE_LABEL = "Yahoo Finance"


def _value(table: Mapping[str, Mapping[str, float]], rows: Sequence[str], end: str) -> Optional[float]:
    for row in rows:
        value = (table.get(row) or {}).get(end)
        if value is not None:
            return value
    return None


def annual_statements(statements: YahooStatements, currency: str) -> EdgarAnnualData:
    """
    Yahoo's annual statements as statement rows (newest first), in `currency` (Yahoo's financialCurrency). Empty cells
    stay None. Long-term debt: the debt-and-lease total when a lease line is reported, else all non-current liabilities
    (noted). Year-end shares: ordinary shares (net of treasury), else shares issued.
    """
    ends = sorted({end for row in statements.income.values() for end in row}
                  | {end for row in statements.balance.values() for end in row}, reverse=True)
    income, balance, shares, dividends, cash, upper_bound = [], [], {}, {}, {}, []
    for end in ends:
        get = lambda rows, table=statements.income: _value(table, rows, end)   # noqa: E731
        net_income = get(INCOME_ROWS["net_income"])
        if net_income is not None:
            income.append(IncomeStatementRow(end, get(INCOME_ROWS["revenue"]), net_income, get(INCOME_ROWS["eps"])))
        b = {k: _value(statements.balance, rows, end) for k, rows in BALANCE_ROWS.items()}
        if b["total_assets"] is not None and b["total_equity"] is not None:
            if any(_value(statements.balance, (row,), end) is not None for row in LEASE_ROWS):
                ltd = _value(statements.balance, (DEBT_WITH_LEASES,), end) or 0.0
            else:
                ltd = b["noncurrent_liabilities"]
                upper_bound.append(fiscal_year(end))
            balance.append(BalanceSheetRow(
                period_end=end, total_equity=b["total_equity"], intangible_assets=b["intangibles"], goodwill=b["goodwill"],
                current_assets=b["current_assets"], current_liabilities=b["current_liabilities"],
                total_liabilities=b["total_liabilities"], long_term_debt=ltd, short_term_debt=b["short_term_debt"],
                total_debt_reported=None, total_assets=b["total_assets"], inventory=b["inventory"],
                noncontrolling_interest=b["minority"], shares_outstanding=b["shares"],
                long_term_debt_unknown=ltd is None))
            if b["shares"]:
                shares[fiscal_year(end)] = b["shares"]
        ocf = _value(statements.cashflow, CASHFLOW_ROWS["operating_cash_flow"], end)
        if ocf is not None:
            cash[end] = ocf
        paid = _value(statements.cashflow, CASHFLOW_ROWS["dividends_paid"], end)
        if paid is not None:
            dividends[end] = abs(paid)
    notes = []
    if upper_bound:
        notes.append(f"{SOURCE_LABEL}: long-term debt for FY{', FY'.join(sorted(set(upper_bound)))} is all non-current "
                     "liabilities (an upper bound: no lease line reported, so lease liabilities cannot be counted otherwise)")
    return EdgarAnnualData(tuple(balance), tuple(income), dividends, cash, shares, 0.0, tuple(notes), currency)
