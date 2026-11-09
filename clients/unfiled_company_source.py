"""
Companies with no filings on any free route (Germany, Ireland, AIM: no SEC filer, no ESEF report on
filings.xbrl.org): Yahoo Finance's annual statements for the recent years, Eulerpool for the years before them.

Graham's analyst consulted the original reports "wherever possible" and otherwise the statistical services (Security
Analysis ch. 3); with no filed XBRL, Yahoo's statements, the more accurate service in testing (94-100% against filed
figures), cover its ~4 years (claude-output/YAHOO_STATEMENTS_SCOPE.md, decisions of 2026-11-09). Eulerpool's older
years (EULERPOOL_API_KEY) pass the overlap gate against the Yahoo years, field by field, never rescaled (§8.11), and
fill a Yahoo year without net income only where Eulerpool's net income passed the gate. Without Yahoo statements,
the earlier Eulerpool-only route (labelled unverified, checked against Yahoo's net income) remains.
"""

import datetime as dt
import logging
from dataclasses import replace
from typing import List, Optional

from clients import eulerpool_mapper, yahoo_mapper
from core.fundamentals import IncomeStatementRow
from core.price_quote import major_currency
from clients.eulerpool_client import EulerpoolClient
from clients.foreign_sec_source import FULL_HISTORY_YEARS, MATCH_DAYS, MAX_NET_INCOME_GAP, home_listing_fundamentals
from clients.yfinance_client import YFinanceClient
from config.eulerpool_config import EULERPOOL_MATCH_ABS
from core.errors import DataSourceError, TickerNotCoveredError
from core.fundamentals import CompanyFundamentals

logger = logging.getLogger(__name__)

SOURCE_NAME = "Yahoo Finance statements (+ Eulerpool history)"
VENDOR_ONLY_SOURCE_NAME = "Eulerpool (vendor data, unverified) + Yahoo Finance"
MIN_YAHOO_YEARS = 2
MAX_SHARE_GAP = 0.10


class UnfiledCompanySource:
    """CompanyFundamentals for companies with no XBRL filings: Yahoo statements + Eulerpool history (FundamentalsSource)."""

    name = SOURCE_NAME

    def __init__(self, yahoo: YFinanceClient, eulerpool: Optional[EulerpoolClient] = None):
        self.yahoo = yahoo
        self.eulerpool = eulerpool

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        """
        Raises:
            TickerNotCoveredError: no Yahoo data for the listing; or no Yahoo statements and no Eulerpool figures
                that agree with Yahoo
            EulerpoolAuthError / EulerpoolRateLimitError / EulerpoolRequestError: Eulerpool request failed
        """
        yahoo = self.yahoo.fetch_company_data(ticker)
        if yahoo is None:
            raise TickerNotCoveredError(f"{ticker}: no Yahoo Finance data for this listing")
        profile = yahoo_mapper.profile(yahoo)
        statements = self.yahoo.fetch_annual_statements(ticker) if profile.financial_currency else None
        if statements is not None:
            annual = yahoo_mapper.annual_statements(statements, profile.financial_currency)
            if annual.income_statements:
                return self._from_yahoo(ticker, yahoo, profile, annual)
        if self.eulerpool is None:
            raise TickerNotCoveredError(f"{ticker}: no SEC or ESEF filings and no Yahoo Finance statements for this listing")
        return self._vendor_only(ticker, yahoo, profile)

    def _from_yahoo(self, ticker: str, yahoo, profile, annual) -> CompanyFundamentals:
        notes: List[str] = [
            f"Statements: Yahoo Finance annual statements for FY{annual.income_statements[-1].period_end[:4]}-"
            f"FY{annual.income_statements[0].period_end[:4]} (a statistical service, not the company's filings: no SEC or "
            "ESEF XBRL on the free routes); price, dividends and profile from this listing"]
        notes.extend(annual.notes)
        yahoo_years = len(annual.income_statements)
        if self.eulerpool is not None:
            annual = self._with_eulerpool(yahoo, profile, annual, notes)
        years = len(annual.income_statements)
        if years < FULL_HISTORY_YEARS:
            older = f"; {years - yahoo_years} from Eulerpool" if years > yahoo_years else ""
            notes.append(f"History: {years} fiscal years ({yahoo_years} from Yahoo Finance{older}); tests needing more years "
                         "fail or show N/A because of this data limit, not because of the company's record")
        notes.append("No quarterly figures: TTM is N/A")
        return home_listing_fundamentals(ticker, SOURCE_NAME, yahoo, profile, replace(annual, notes=()), notes,
                                         fallback_name=profile.name or ticker, data_name="Yahoo Finance's statements")

    def _with_eulerpool(self, yahoo, profile, annual, notes: List[str]):
        """Eulerpool's years before Yahoo's, gated against them; it also fills Yahoo years without net income."""
        try:
            found = self.eulerpool.find_profile(yahoo.yahoo_symbol, profile.name or "")
            if found is None:
                notes.append(f"History before Yahoo Finance's years: Eulerpool has no listing {yahoo.yahoo_symbol} named "
                             f"like {profile.name!r}")
                return annual
            data = eulerpool_mapper.parse(found, self.eulerpool.fetch_statements(found["isin"]))
        except DataSourceError as e:
            notes.append(f"History before Yahoo Finance's years: Eulerpool unavailable ({e})")
            return annual
        quote = profile.quote_currency or annual.currency
        older = eulerpool_mapper.older_years(annual, data, strict=(major_currency(quote) or quote) != annual.currency,
                                             filed_source="Yahoo Finance's statements")
        notes.extend(n.replace("History before the filed years", "History before Yahoo Finance's years")
                     .replace("unverified against the company's reports", "checked only against Yahoo Finance")
                     for n in older.notes)
        filled = []
        if "net_income" in older.accepted and yahoo_rows(annual):
            # A year inside or after Yahoo's range with no Yahoo net income (an empty Yahoo column: James Halstead and
            # Fevertree FY2025): Eulerpool's figures, net income having passed the gate
            first = dt.date.fromisoformat(min(yahoo_rows(annual)))
            covered = [dt.date.fromisoformat(row.period_end) for row in annual.income_statements]
            for end, values in sorted(data.years.items(), reverse=True):
                day = dt.date.fromisoformat(end)
                if values.get("net_income") is None or (day - first).days <= MATCH_DAYS \
                        or any(abs((day - c).days) <= MATCH_DAYS for c in covered):
                    continue
                filled.append(IncomeStatementRow(end, values.get("revenue") if "revenue" in older.accepted else None,
                                                 values["net_income"], None))
            if filled:
                notes.append(f"Eulerpool: net income for FY{', FY'.join(sorted(r.period_end[:4] for r in filled))} (Yahoo "
                             "Finance's statement has none; Eulerpool's net income passed the overlap gate)")
        income = tuple(sorted(annual.income_statements + tuple(filled) + older.income_statements,
                              key=lambda r: r.period_end, reverse=True))
        return replace(annual, income_statements=income,
                       balance_sheets=annual.balance_sheets + older.balance_sheets,
                       shares_by_year={**older.shares_by_year, **annual.shares_by_year},
                       dividends_paid={**older.dividends_paid, **annual.dividends_paid},
                       operating_cash_flow={**older.operating_cash_flow, **annual.operating_cash_flow})

    def _vendor_only(self, ticker: str, yahoo, profile) -> CompanyFundamentals:
        """No Yahoo statements: Eulerpool alone, checked against Yahoo's net income (labelled unverified)."""
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
            "used); no intangibles (tangible book overstated); long-term debt is taken as all non-current liabilities "
            "(an upper bound: it includes provisions and pensions as well as borrowings and leases), because "
            "Eulerpool's own long-term debt includes lease liabilities for some companies and not others, so the "
            "debt tests may fail a company whose debt alone would pass",
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
        return home_listing_fundamentals(ticker, VENDOR_ONLY_SOURCE_NAME, yahoo, profile, annual, notes,
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


def yahoo_rows(annual) -> List[str]:
    """Period ends Yahoo's statements cover (balance sheets or income), newest first."""
    return sorted({row.period_end for row in annual.balance_sheets} | {row.period_end for row in annual.income_statements},
                  reverse=True)
