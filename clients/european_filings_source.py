"""
European companies from their ESEF annual reports (filings.xbrl.org) + Yahoo Finance for the home listing.

Implements core.ports.FundamentalsSource for EU / EEA / UK listings on the free resolution path (European route,
claude-output/EU_XBRL_EULERPOOL_SCOPE.md; docs/CODEBASE_GUIDE.md §12.1). It is used after the SEC route: a company
that files 20-F / 40-F with the SEC is read there, for its longer history. clients/esef_entity_lookup.py finds the
filer by the listing's name; Yahoo's financial currency and annual net income must agree with the reports before
any figure is used. The reports are the company's own tagged annual reports, read with the SEC route's rules
(edgar_mapper.annual_data), so the same Graham data rules apply; ESEF started with FY2020 (FY2021 in some
countries), so the history is about six years.
"""

import logging
from dataclasses import replace
from typing import List, Optional

from clients import edgar_mapper, esef_mapper, eulerpool_mapper, yahoo_mapper
from clients.esef_client import EsefClient
from clients.esef_entity_lookup import EsefEntityLookup
from clients.eulerpool_client import EulerpoolClient
from clients.foreign_sec_source import FULL_HISTORY_YEARS, _agreement, home_listing_fundamentals
from clients.yfinance_client import YFinanceClient
from core.errors import DataSourceError, SourceRequestError, TickerNotCoveredError
from core.fundamentals import CompanyFundamentals
from core.price_quote import major_currency

logger = logging.getLogger(__name__)

SOURCE_NAME = "ESEF annual reports (filings.xbrl.org) + Yahoo Finance"


class EuropeanFilingsSource:
    """CompanyFundamentals for European ESEF filers from filings.xbrl.org + Yahoo (core.ports.FundamentalsSource)."""

    name = SOURCE_NAME

    def __init__(self, client: EsefClient, yahoo: YFinanceClient, lookup: EsefEntityLookup = None,
                 history: Optional[EulerpoolClient] = None):
        """
        Args:
            history: Eulerpool, for the years before the first ESEF report (optional: EULERPOOL_API_KEY)
        """
        self.client = client
        self.yahoo = yahoo
        self.lookup = lookup or EsefEntityLookup(client)
        self.history = history

    def _with_older_years(self, yahoo, profile, annual: edgar_mapper.EdgarAnnualData,
                          notes: List[str]) -> edgar_mapper.EdgarAnnualData:
        """Eulerpool's years before the first ESEF report, behind the overlap gate (eulerpool_mapper); never fatal."""
        try:
            found = self.history.find_profile(yahoo.yahoo_symbol, profile.name or "")
            if found is None:
                notes.append(f"History before the filed years: Eulerpool has no listing {yahoo.yahoo_symbol} named like "
                             f"{profile.name!r}; ESEF years only")
                return annual
            data = eulerpool_mapper.parse(found, self.history.fetch_statements(found["isin"]))
        except DataSourceError as e:
            logger.warning(f"Eulerpool history not used: {e}")
            notes.append(f"History before the filed years: Eulerpool unavailable ({e}); ESEF years only")
            return annual
        quote = profile.quote_currency or annual.currency
        older = eulerpool_mapper.older_years(annual, data, strict=(major_currency(quote) or quote) != annual.currency,
                                             filed_source="the ESEF reports")
        notes.extend(older.notes)
        return replace(annual,
                       balance_sheets=annual.balance_sheets + older.balance_sheets,
                       income_statements=annual.income_statements + older.income_statements,
                       shares_by_year={**older.shares_by_year, **annual.shares_by_year},
                       dividends_paid={**older.dividends_paid, **annual.dividends_paid},
                       operating_cash_flow={**older.operating_cash_flow, **annual.operating_cash_flow})

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        """
        Raises:
            TickerNotCoveredError: no Yahoo data for the listing, no (or no single, current) ESEF filer, no annual
                report with figures, or Yahoo's figures disagree with the reports
            EsefRateLimitError: filings.xbrl.org kept refusing requests
        """
        yahoo = self.yahoo.fetch_company_data(ticker)
        if yahoo is None:
            raise TickerNotCoveredError(f"{ticker}: no Yahoo Finance data for this listing")
        profile = yahoo_mapper.profile(yahoo)
        entity = self.lookup.resolve(ticker, profile.name)
        logger.info(f"ESEF: {ticker} is {entity.name} (LEI {entity.lei})")
        notes: List[str] = []
        reports, failed = [], []
        for filing in entity.reports:
            try:
                reports.append(esef_mapper.report_facts(filing, self.client.fetch_report(filing)))
            except SourceRequestError as e:
                logger.debug(f"ESEF: report {filing.fxo_id} not read: {e}")
                failed.append(filing.period_end)
        if failed:
            notes.append(f"ESEF: reports that could not be downloaded were left out (indexed period ends "
                         f"{', '.join(failed)})")
        facts, skipped = esef_mapper.companyfacts(reports)
        splits = yahoo_mapper.splits(yahoo)
        annual = edgar_mapper.annual_data(facts, splits, eps_implied_shares=True, source=esef_mapper.SOURCE_LABEL,
                                          reference_shares=yahoo_mapper.total_shares(yahoo))
        if not annual.income_statements:
            raise TickerNotCoveredError(f"{ticker}: {entity.name} (LEI {entity.lei}) has no annual ESEF report with "
                                        "figures on filings.xbrl.org")
        if profile.financial_currency and profile.financial_currency != annual.currency:
            raise TickerNotCoveredError(f"{ticker}: Yahoo reports this company's statements in "
                                        f"{profile.financial_currency}, the ESEF reports of {entity.name} in "
                                        f"{annual.currency}: not confirmed to be the same company")
        agrees = _agreement(annual, self.yahoo.fetch_annual_net_income(ticker))
        if agrees is False:
            raise TickerNotCoveredError(f"{ticker}: Yahoo's net income differs from the ESEF reports of "
                                        f"{entity.name} (LEI {entity.lei}): not confirmed to be the same company")

        latest = max(entity.reports, key=lambda filing: filing.date_added)
        notes.insert(0, f"Statements: ESEF annual reports of {entity.name} (LEI {entity.lei}) from filings.xbrl.org "
                     f"(XBRL International's unofficial repository of the reports filed with national regulators), "
                     f"latest added {latest.date_added[:10]}; company-wide IFRS figures only (a company's own XBRL "
                     "tags are not read); price, dividends and profile from this listing")
        notes.extend(skipped)
        if agrees is None:
            notes.append("ESEF filer matched by company name; Yahoo Finance has no overlapping year of net income to "
                         "confirm it")
        filed_years = len(annual.income_statements)
        first_filed = annual.income_statements[-1].period_end[:4]
        if self.history is not None:
            annual = self._with_older_years(yahoo, profile, annual, notes)
        years = len(annual.income_statements)
        if years < FULL_HISTORY_YEARS:
            older = f"; {years - filed_years} earlier from Eulerpool" if years > filed_years else ""
            notes.append(f"History: {years} fiscal years (the ESEF reports cover {filed_years}, from FY{first_filed}; ESEF "
                         f"tagging began with FY2020{older}); tests needing more years fail or show N/A because of this "
                         "data limit, not because of the company's record")
        if splits:
            notes.append("Per-share figures and share counts adjusted to today's share basis for stock splits "
                         "(Yahoo Finance split history of this listing): "
                         + ", ".join(f"{d} {r:g}:1" for d, r in splits))
        notes.append("No quarterly figures: only annual ESEF reports are read, so TTM is N/A")
        return home_listing_fundamentals(ticker, SOURCE_NAME, yahoo, profile, annual, notes,
                                         fallback_name=entity.name, data_name="the ESEF data")
