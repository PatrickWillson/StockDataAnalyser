"""
Free US fundamentals: SEC EDGAR statements + Yahoo Finance dividends, profile and market data.

Implements core.ports.FundamentalsSource for `.US` tickers (the free resolution path,
docs/CODEBASE_GUIDE.md §12). EDGAR supplies every statement figure (as filed with the SEC); Yahoo
supplies what filings do not carry in usable form: per-payment dividends, stock splits (for the share
basis of the EDGAR per-share facts), the industry name and the officers.
"""

import json
import logging
import os
from typing import Any, List, Mapping, Optional

from clients import edgar_mapper, yahoo_mapper
from clients.edgar_client import EdgarClient, sec_symbol
from clients.yfinance_client import YahooCompanyData, YFinanceClient
from core.errors import TickerNotCoveredError
from core.fundamentals import CompanyFundamentals

logger = logging.getLogger(__name__)

SOURCE_NAME = "SEC EDGAR + Yahoo Finance"
STATEMENT_CURRENCY = "USD"   # edgar_mapper maps USD filers only


def _latest_filing_date(submissions: Mapping[str, Any]) -> Optional[str]:
    """Date of the newest 10-K / 10-Q (the 'last updated' of the statements)."""
    recent = submissions.get("filings", {}).get("recent", {})
    dates = [date for form, date in zip(recent.get("form", []), recent.get("filingDate", []))
             if form in ("10-K", "10-K/A", "10-Q", "10-Q/A")]
    return max(dates) if dates else None


def _successor_filing(submissions: Mapping[str, Any]) -> Optional[str]:
    """Date of a Form 8-K12B (the successor-issuer notice) among the company's filings, if any."""
    recent = submissions.get("filings", {}).get("recent", {})
    dates = [date for form, date in zip(recent.get("form", []), recent.get("filingDate", []))
             if str(form).startswith("8-K12B")]
    return min(dates) if dates else None


def _exchange(submissions: Mapping[str, Any]) -> str:
    exchanges = [e for e in submissions.get("exchanges", []) or [] if e]
    return exchanges[0] if exchanges else "US"


class FreeUSFundamentalsSource:
    """CompanyFundamentals for US SEC filers from EDGAR + Yahoo (core.ports.FundamentalsSource)."""

    name = SOURCE_NAME

    def __init__(self, edgar: EdgarClient, yahoo: YFinanceClient, debug: bool = False):
        self.edgar = edgar
        self.yahoo = yahoo
        self.debug = debug

    def _save_debug(self, ticker: str, label: str, payload: Any) -> None:
        if not self.debug:
            return
        path = f"data/{ticker.replace('.', '_')}_sec_{label}.json"
        try:
            os.makedirs("data", exist_ok=True)
            with open(path, "w") as fh:
                json.dump(payload, fh)
            logger.debug(f"Raw SEC {label} saved to: {path}")
        except OSError as e:
            logger.debug(f"Could not save raw SEC {label}: {e}")

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        """
        Raises:
            TickerNotCoveredError: not an SEC filer, no annual XBRL statements, or not a USD filer
            EdgarAuthError / EdgarRateLimitError / EdgarRequestError: SEC request failed
        """
        cik = self.edgar.resolve_cik(ticker)
        logger.info(f"SEC EDGAR: {ticker} is CIK {cik}")
        facts = self.edgar.fetch_company_facts(cik)
        submissions = self.edgar.fetch_submissions(cik)
        self._save_debug(ticker, "companyfacts", facts)
        self._save_debug(ticker, "submissions", submissions)

        notes: List[str] = []
        predecessors = self.edgar.predecessor_ciks(ticker)
        if predecessors:
            earlier = []
            for predecessor in predecessors:
                try:
                    earlier.append(self.edgar.fetch_company_facts(predecessor))
                except TickerNotCoveredError:
                    notes.append(f"SEC EDGAR: predecessor CIK {predecessor} has no XBRL data")
            facts = edgar_mapper.merge_companyfacts(facts, earlier)
            names = ", ".join(f"{f.get('entityName')} (CIK {str(f.get('cik')).zfill(10)})" for f in earlier)
            if names:
                notes.append(f"SEC EDGAR: earlier years from the predecessor filer {names}, which this company "
                             f"succeeded in a holding-company reorganisation (shares exchanged one for one)")
        else:
            succession = _successor_filing(submissions)
            if succession:
                notes.append(f"SEC EDGAR: this company filed a Form 8-K12B (successor issuer) on {succession}; "
                             "years before that may be under a predecessor's CIK (config SEC_PREDECESSOR_CIKS)")
        yahoo = self.yahoo.fetch_company_data(ticker)
        if yahoo is None:
            notes.append("Yahoo Finance company data unavailable: no dividend payments, splits or profile; "
                         "per-share history is not adjusted for stock splits")
            yahoo = YahooCompanyData(yahoo_symbol=ticker)
        splits = yahoo_mapper.splits(yahoo)
        sic = submissions.get("sic")
        try:
            annual = edgar_mapper.annual_data(facts, splits, sic)
        except ValueError as e:
            raise TickerNotCoveredError(f"{ticker}: {e}") from e
        if not annual.income_statements:
            raise TickerNotCoveredError(f"{ticker}: no annual reports with XBRL financial data at the SEC")
        periodic = edgar_mapper.periodic_data(facts, splits, sic)
        profile = yahoo_mapper.profile(yahoo)
        ceo_name = profile.ceo_name
        if ceo_name == "N/A":
            officer = self.edgar.fetch_certifying_officer(cik, submissions)
            if officer:
                ceo_name = officer
                notes.append("CEO: the principal executive officer who signed the latest 10-K's Exhibit 31.1 "
                             "certification (Yahoo Finance lists no CEO)")
        quote_currency = profile.quote_currency or STATEMENT_CURRENCY
        if splits:
            notes.append("Per-share figures and share counts adjusted to today's share basis for stock splits "
                         "(Yahoo Finance split history): " + ", ".join(f"{d} {r:g}:1" for d, r in splits))
        notes.append("Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)")
        latest_filing = _latest_filing_date(submissions)
        if latest_filing:
            notes.append(f"Statements as filed with the SEC; latest 10-K/10-Q filed {latest_filing}")

        latest_balance = annual.balance_sheets[0] if annual.balance_sheets else None
        latest_shares = (latest_balance.shares_outstanding if latest_balance else None) or 0.0
        return CompanyFundamentals(
            source=SOURCE_NAME,
            symbol=sec_symbol(ticker),
            exchange=_exchange(submissions),
            trading_currency=quote_currency,
            statement_currency=STATEMENT_CURRENCY,
            name=profile.name or submissions.get("name"),
            sector=profile.sector,
            industry=profile.industry,
            employees=profile.employees,
            ceo_name=ceo_name,
            is_delisted=False,
            # No vendor refresh date: SEC figures are as filed (the latest filing date is in the notes)
            updated_at=None,
            annual_balance_sheets=annual.balance_sheets,
            annual_income_statements=annual.income_statements,
            quarterly_balance_sheets=periodic.balance_sheets,
            quarterly_income_statements=periodic.income_statements,
            shares_outstanding=annual.latest_cover_shares or latest_shares,
            shares_by_year=dict(annual.shares_by_year),
            latest_statement_shares=latest_shares,
            dividend_payments=yahoo_mapper.dividend_payments(yahoo, quote_currency),
            annual_dividends_paid=dict(annual.dividends_paid),
            cash_flow_currency=STATEMENT_CURRENCY,
            forward_dividend_rate=yahoo_mapper.forward_dividend_rate(yahoo),
            forward_dividend_currency=quote_currency,
            market=yahoo_mapper.market_data(yahoo),
            notes=tuple(notes) + annual.notes + periodic.notes,
        )
