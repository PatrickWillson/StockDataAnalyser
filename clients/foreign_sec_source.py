"""
Non-US companies from their SEC filings: 20-F / 40-F (or 10-K) XBRL + Yahoo Finance for the home listing.

Implements core.ports.FundamentalsSource for non-US exchanges on the free resolution path (SEC route for
non-US companies, claude-output scope of 2026-11-07; docs/CODEBASE_GUIDE.md §12.1). The ticker is the home
listing (BP.LSE, 7203.TSE): price, dividends, splits and profile come from it, so per-share figures are per
ordinary share, the basis of the SEC share counts (an ADR's price would need its ADS ratio, which the SEC
data does not give). clients/sec_filer_lookup.py finds the filer; Yahoo's annual net income must agree with
the filing's before any figure is used.
"""

import datetime as dt
import logging
from dataclasses import replace
from typing import Dict, List, Optional

from clients import edgar_mapper, yahoo_mapper
from clients.edgar_client import EdgarClient
from clients.sec_filer_lookup import SecFilerLookup
from clients.yfinance_client import YFinanceClient
from core.errors import TickerNotCoveredError
from core.fundamentals import CompanyFundamentals
from core.price_quote import is_minor_unit, major_currency, to_major_unit

logger = logging.getLogger(__name__)

SOURCE_NAME = "SEC EDGAR (20-F/40-F) + Yahoo Finance"
# Yahoo's annual net income must be this close to the filing's for a year both have
MAX_NET_INCOME_GAP = 0.02
FULL_HISTORY_YEARS = 10      # Graham's defensive earnings record; fewer years get the history note
MATCH_DAYS = 10


def _agreement(annual: edgar_mapper.EdgarAnnualData, yahoo_income: Dict[str, List[float]]) -> Optional[bool]:
    """
    Whether Yahoo's net income agrees with the filing's in the newest year both have (either of Yahoo's net
    income to common or net income within MAX_NET_INCOME_GAP); None when no year overlaps.
    """
    for row in annual.income_statements:
        if row.net_income is None:
            continue
        end = dt.date.fromisoformat(row.period_end)
        for yahoo_end, values in sorted(yahoo_income.items(), reverse=True):
            if abs((dt.date.fromisoformat(yahoo_end) - end).days) <= MATCH_DAYS:
                scale = max(abs(row.net_income), 1.0)
                return any(abs(value - row.net_income) <= MAX_NET_INCOME_GAP * scale for value in values)
    return None


class ForeignSECFundamentalsSource:
    """CompanyFundamentals for non-US SEC filers from EDGAR + Yahoo (core.ports.FundamentalsSource)."""

    name = SOURCE_NAME

    def __init__(self, edgar: EdgarClient, yahoo: YFinanceClient, lookup: Optional[SecFilerLookup] = None):
        self.edgar = edgar
        self.yahoo = yahoo
        self.lookup = lookup or SecFilerLookup(edgar, yahoo)

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        """
        Raises:
            TickerNotCoveredError: no Yahoo data for the listing, no (or no single, current) SEC filer, no
                annual XBRL statements, or Yahoo's figures disagree with the filing's
            EdgarAuthError / EdgarRateLimitError / EdgarRequestError: SEC request failed
        """
        yahoo = self.yahoo.fetch_company_data(ticker)
        if yahoo is None:
            raise TickerNotCoveredError(f"{ticker}: no Yahoo Finance data for this listing")
        profile = yahoo_mapper.profile(yahoo)
        filer = self.lookup.resolve(ticker, profile.name)
        logger.info(f"SEC EDGAR: {ticker} is {filer.sec_name} (CIK {filer.cik})")
        facts = self.edgar.fetch_company_facts(filer.cik)
        submissions = self.edgar.fetch_submissions(filer.cik)
        splits = yahoo_mapper.splits(yahoo)
        notes: List[str] = []
        if not splits and filer.annual_form.startswith("40-F") and filer.us_symbols:
            # A 40-F filer's US line trades the same shares (Canada's MJDS), and Yahoo sometimes records a split or
            # consolidation only there (Eldorado's 2018 1-for-5: EGO, not ELD.TO). Not for 20-F filers, whose US line
            # is usually an ADR, where a "split" can be an ADS ratio change
            us_line = self.yahoo.fetch_company_data(f"{filer.us_symbols[0]}.US")
            us_splits = yahoo_mapper.splits(us_line) if us_line else ()
            if us_splits:
                splits = us_splits
                notes.append(f"Stock splits from the US listing {filer.us_symbols[0]} (Yahoo Finance lists none for "
                             "this home listing; a 40-F filer's US line trades the same shares)")
        missing = edgar_mapper.filings_missing_from_companyfacts(facts, submissions)
        instances = [(filing, self.edgar.fetch_filing_instance(filer.cik, filing[3])) for filing in missing]
        instances = [(filing, instance) for filing, instance in instances if instance]
        if instances:
            facts = edgar_mapper.merge_companyfacts(facts, [
                edgar_mapper.instance_companyfacts(instance, filing[0], filing[2], filing[3]) for filing, instance in instances])
            notes.append("SEC EDGAR: " + ", ".join(f"{filing[0]} for {filing[1]}" for filing, _ in instances)
                         + " read from the filing's own XBRL file: the SEC's company facts do not include it")
        annual = edgar_mapper.annual_data(facts, splits, submissions.get("sic"), eps_implied_shares=True)
        if not annual.income_statements:
            raise TickerNotCoveredError(f"{ticker}: {filer.sec_name} (CIK {filer.cik}) has no annual reports with "
                                        "XBRL financial data at the SEC")
        if profile.financial_currency and profile.financial_currency != annual.currency:
            raise TickerNotCoveredError(f"{ticker}: Yahoo reports this company's statements in "
                                        f"{profile.financial_currency}, the SEC filing of {filer.sec_name} in "
                                        f"{annual.currency}: not confirmed to be the same company")
        agrees = _agreement(annual, self.yahoo.fetch_annual_net_income(ticker))
        if agrees is False:
            raise TickerNotCoveredError(f"{ticker}: Yahoo's net income differs from the SEC filing of "
                                        f"{filer.sec_name} (CIK {filer.cik}): not confirmed to be the same company")

        listings = f" (US listing {', '.join(filer.us_symbols)})" if filer.us_symbols else ""
        notes.insert(0, f"Statements: SEC EDGAR XBRL of {filer.sec_name} (CIK {filer.cik}){listings}, latest annual report "
                 f"{filer.annual_form} filed {filer.annual_filed}; price, dividends and profile from this home "
                 "listing, so per-share figures are per ordinary share")
        if agrees is None:
            notes.append("SEC filer matched by company name; Yahoo Finance has no overlapping year of net income to "
                         "confirm it")
        years = len(annual.income_statements)
        if years < FULL_HISTORY_YEARS:
            notes.append(f"History: the SEC's XBRL data for this filer covers {years} fiscal years (from "
                         f"FY{annual.income_statements[-1].period_end[:4]}); tests needing more years fail or show "
                         "N/A because of this data limit, not because of the company's record")
        if splits:
            notes.append("Per-share figures and share counts adjusted to today's share basis for stock splits "
                         "(Yahoo Finance split history of the home listing): "
                         + ", ".join(f"{d} {r:g}:1" for d, r in splits))
        notes.append("No quarterly figures: foreign filers' interim reports (6-K) carry no XBRL, so TTM is N/A")
        notes.append("Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)")

        quote_currency = profile.quote_currency or annual.currency
        # Yahoo gives a London listing's dividends in pence (GBp), like its price: expressed here in pounds, the
        # currency the FX conversion understands (the price's London Fix happens in core)
        dividend_currency = major_currency(quote_currency) or quote_currency
        payments = yahoo_mapper.dividend_payments(yahoo, quote_currency)
        if payments and is_minor_unit(quote_currency):
            payments = tuple(replace(p, amount=to_major_unit(p.amount, quote_currency)[0], currency=dividend_currency)
                             for p in payments)
            notes.append(f"Dividends: Yahoo Finance quotes them in {quote_currency}; converted to {dividend_currency} (÷100)")
        # Yahoo's forward dividend rate (a display-only estimate, F21) is in the listing's currency only when that is
        # also the reporting currency; otherwise its unit is not dependable (BP.L and AZN.L: dollars, as declared,
        # beside a pence price), so it is left out rather than shown in a wrong unit
        forward_rate = yahoo_mapper.forward_dividend_rate(yahoo) if quote_currency == annual.currency else None
        market = yahoo_mapper.market_data(yahoo)
        if quote_currency != annual.currency:
            # Same for Yahoo's per-share figures (book value, trailing dividend and yield, P/E): HSBA.L's bookValue
            # 7.57 is in pounds, labelled as the dollar statements' currency. They feed only the [VALIDATION]
            # comparisons, which would otherwise report false discrepancies
            market = replace(market, book_value_per_share=0.0, dividend_per_share=0.0, dividend_yield=0.0, pe_ratio=0.0)
        latest_balance = annual.balance_sheets[0] if annual.balance_sheets else None
        latest_shares = (latest_balance.shares_outstanding if latest_balance else None) or 0.0
        current_shares = annual.latest_cover_shares or latest_shares
        if not current_shares:
            # EPS and shares only under the company's own tags (BP): today's count of this home listing's shares
            # (ordinary shares) stands for every year without a count, as on the US path for dual-class companies
            current_shares = yahoo_mapper.total_shares(yahoo) or 0.0
            if current_shares:
                notes.append("Share count: not in the SEC data (the company uses its own tags); today's total from "
                             "Yahoo Finance for this listing stands for every year without a count, so per-share "
                             "history (EPS, book value per share) is approximate")
        symbol, _, exchange = ticker.rpartition(".")
        return CompanyFundamentals(
            source=SOURCE_NAME,
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            trading_currency=quote_currency,
            statement_currency=annual.currency,
            name=profile.name or filer.sec_name,
            sector=profile.sector,
            industry=profile.industry,
            employees=profile.employees,
            ceo_name=profile.ceo_name,
            is_delisted=False,
            updated_at=None,
            annual_balance_sheets=annual.balance_sheets,
            annual_income_statements=annual.income_statements,
            shares_outstanding=current_shares,
            shares_by_year=dict(annual.shares_by_year),
            latest_statement_shares=latest_shares,
            dividend_payments=payments,
            annual_dividends_paid=dict(annual.dividends_paid),
            annual_operating_cash_flow=dict(annual.operating_cash_flow),
            cash_flow_currency=annual.currency,
            forward_dividend_rate=forward_rate,
            forward_dividend_currency=dividend_currency,
            market=market,
            notes=tuple(notes) + annual.notes,
        )
