"""
Companies with no filings on any free route (Germany, Ireland, AIM: no SEC filer, no ESEF report on
filings.xbrl.org) from Eulerpool alone + Yahoo Finance for the listing (European route, step 6; user decision
2026-11-08: include, clearly labelled; GRAHAM_METHODOLOGY §8.11).

Every figure is vendor data, unverified against the company's reports. With nothing filed to check it against, it
must agree with Yahoo Finance: the same reporting currency, net income within MAX_NET_INCOME_GAP (or 1.1M: Eulerpool
gives whole millions) in every year both
have (at least MIN_YAHOO_YEARS), and the latest year-end share count within MAX_SHARE_GAP of Yahoo's current total.
"""

import datetime as dt
import logging
from typing import List

from clients import eulerpool_mapper, yahoo_mapper
from clients.eulerpool_client import EulerpoolClient
from clients.foreign_sec_source import FULL_HISTORY_YEARS, MATCH_DAYS, MAX_NET_INCOME_GAP, home_listing_fundamentals
from clients.yfinance_client import YFinanceClient
from config.eulerpool_config import EULERPOOL_MATCH_ABS
from core.errors import TickerNotCoveredError
from core.fundamentals import CompanyFundamentals

logger = logging.getLogger(__name__)

SOURCE_NAME = "Eulerpool (vendor data, unverified) + Yahoo Finance"
MIN_YAHOO_YEARS = 2
MAX_SHARE_GAP = 0.10


class EulerpoolOnlySource:
    """CompanyFundamentals from Eulerpool alone, checked against Yahoo (core.ports.FundamentalsSource)."""

    name = SOURCE_NAME

    def __init__(self, eulerpool: EulerpoolClient, yahoo: YFinanceClient):
        self.eulerpool = eulerpool
        self.yahoo = yahoo

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        """
        Raises:
            TickerNotCoveredError: no Yahoo or Eulerpool data for the listing, or they disagree
            EulerpoolAuthError / EulerpoolRateLimitError / EulerpoolRequestError: Eulerpool request failed
        """
        yahoo = self.yahoo.fetch_company_data(ticker)
        if yahoo is None:
            raise TickerNotCoveredError(f"{ticker}: no Yahoo Finance data for this listing")
        profile = yahoo_mapper.profile(yahoo)
        found = self.eulerpool.find_profile(yahoo.yahoo_symbol, profile.name or "")
        if found is None:
            raise TickerNotCoveredError(f"{ticker}: Eulerpool has no listing {yahoo.yahoo_symbol} named like {profile.name!r}")
        data = eulerpool_mapper.parse(found, self.eulerpool.fetch_statements(found["isin"]))
        annual = eulerpool_mapper.vendor_annual(data)
        if not annual.income_statements:
            raise TickerNotCoveredError(f"{ticker}: Eulerpool has no annual figures for {data.name}")
        if not profile.financial_currency or profile.financial_currency != annual.currency:
            raise TickerNotCoveredError(f"{ticker}: Eulerpool's figures are in {annual.currency or 'no stated currency'}, "
                                        f"Yahoo's statements in {profile.financial_currency or 'no stated currency'}: "
                                        "not used (vendor figures are never converted)")
        checked = self._check_net_income(ticker, annual)
        latest = annual.balance_sheets[0].shares_outstanding if annual.balance_sheets else None
        today = yahoo_mapper.total_shares(yahoo)
        if not latest or not today or abs(latest / today - 1) > MAX_SHARE_GAP:
            raise TickerNotCoveredError(f"{ticker}: Eulerpool's latest share count ({(latest or 0) / 1e6:,.1f}M) is not "
                                        f"within {MAX_SHARE_GAP:.0%} of Yahoo's ({(today or 0) / 1e6:,.1f}M): not used")

        years = [row.period_end[:4] for row in annual.income_statements]
        notes: List[str] = [
            f"Statements: Eulerpool (commercial vendor data) for {data.name} (ISIN {data.isin}), FY{years[-1]}-FY{years[0]}: "
            "UNVERIFIED against the company's reports (no SEC or ESEF filings on the free routes). Checked only against "
            f"Yahoo Finance: same reporting currency, net income within {MAX_NET_INCOME_GAP:.0%} (or 1.1M) in {checked}, latest "
            f"share count within {MAX_SHARE_GAP:.0%}; price, dividends and profile from this listing",
            "Eulerpool figures: whole millions; EPS is net income / Eulerpool's year-end share count (its own EPS is not "
            "used); no intangibles (tangible book overstated); long-term debt as Eulerpool defines it (whether it "
            "includes lease liabilities is not known)",
            "No quarterly figures: TTM is N/A",
        ]
        if len(years) < FULL_HISTORY_YEARS:
            notes.append(f"History: Eulerpool has {len(years)} fiscal years (from FY{years[-1]}); tests needing more years "
                         "fail or show N/A because of this data limit, not because of the company's record")
        splits = yahoo_mapper.splits(yahoo)
        if splits:
            notes.append("Stock splits (Yahoo Finance): " + ", ".join(f"{d} {r:g}:1" for d, r in splits)
                         + "; Eulerpool's share counts are already on today's basis (restated for splits: Novo "
                         "Nordisk's 2022 count is after its 2023 2:1 split)")
        return home_listing_fundamentals(ticker, SOURCE_NAME, yahoo, profile, annual, notes,
                                         fallback_name=data.name, data_name="the Eulerpool data")

    def _check_net_income(self, ticker: str, annual) -> str:
        """The years Eulerpool's net income agreed with Yahoo's ('FY2023-FY2025'), or TickerNotCoveredError."""
        yahoo_income = self.yahoo.fetch_annual_net_income(ticker)
        agreed = []
        for row in annual.income_statements:
            end = dt.date.fromisoformat(row.period_end)
            values = next((v for e, v in yahoo_income.items()
                           if abs((dt.date.fromisoformat(e) - end).days) <= MATCH_DAYS), None)
            if values is None:
                continue
            allowed = max(MAX_NET_INCOME_GAP * abs(row.net_income), EULERPOOL_MATCH_ABS)   # whole millions
            if not any(abs(v - row.net_income) <= allowed for v in values):
                raise TickerNotCoveredError(f"{ticker}: Eulerpool's FY{row.period_end[:4]} net income "
                                            f"({row.net_income / 1e6:,.1f}M) differs from Yahoo Finance's: not used")
            agreed.append(row.period_end[:4])
        if len(agreed) < MIN_YAHOO_YEARS:
            raise TickerNotCoveredError(f"{ticker}: fewer than {MIN_YAHOO_YEARS} years of Yahoo Finance net income to "
                                        "check Eulerpool's figures against: not used")
        return f"FY{min(agreed)}-FY{max(agreed)}"
