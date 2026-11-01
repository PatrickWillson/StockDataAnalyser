"""
Yahoo Finance (yfinance) company data -> pieces of CompanyFundamentals (free resolution path).

The only code that knows Yahoo's `info` keys. Supplies what SEC filings do not carry in usable form:
per-payment dividends, stock splits (for the share basis of EDGAR per-share facts), the profile
(name, sector, industry, employees, CEO) and Yahoo's pre-computed market figures, which are display /
labelled comparison only (CLAUDE.md raw-data rule), exactly like EODHD's Highlights.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple

from clients.yfinance_client import YahooCompanyData
from core.fundamentals import DividendPayment, MarketData, number_or_zero


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


def forward_dividend_rate(data: YahooCompanyData) -> Optional[float]:
    """Yahoo's forward annual dividend (an estimate: labelled display only, F21)."""
    rate = number_or_zero(data.info.get("dividendRate"))
    return rate or None
