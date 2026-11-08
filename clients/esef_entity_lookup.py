"""
Finds the ESEF filer (an entity on filings.xbrl.org, by LEI) behind a European home listing (European route,
claude-output/EU_XBRL_EULERPOOL_SCOPE.md; docs/CODEBASE_GUIDE.md §12.1).

As on the SEC route, a listing is matched by its company name (Yahoo), never its ticker: filings.xbrl.org's
entities are searched by name, and an entity counts only if its name matches (sec_filer_lookup.names_match:
legal forms, accents and listing words ignored) and it has an annual report added within
ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS. Companies with more than one such entity are settled in config
(ESEF_ENTITY_LEIS); any other ambiguity gives no dossier, naming the candidates. The source then confirms the match
against Yahoo's financial currency and net income.
"""

import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

from clients.esef_client import EsefFiling, select_reports
from clients.sec_filer_lookup import DAYS_PER_MONTH, names_match, normalised_name
from config.data_quality_config import ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS
from config.esef_config import ESEF_ENTITY_LEIS
from core.errors import TickerNotCoveredError

MIN_FALLBACK_WORD = 4     # the shortest word searched alone when the whole name finds nothing


@dataclass(frozen=True)
class EsefEntity:
    """A company's ESEF filer and its reports (one listing per report, oldest first)."""
    lei: str
    name: str
    reports: Tuple[EsefFiling, ...]


def search_patterns(home_name: str) -> List[str]:
    """
    ILIKE patterns for a name: its words in order ('%associated%british%foods%'), then its first word and its
    longest word alone (an entity named without the listing's extra words: 'LVMH MOET HENNESSY LOUIS VUITTON').
    """
    words = normalised_name(home_name).split()
    if not words:
        return []
    patterns = ["%" + "%".join(words) + "%"]
    for word in (words[0], max(words, key=len)):
        pattern = f"%{word}%"
        if len(words) > 1 and len(word) >= MIN_FALLBACK_WORD and pattern not in patterns:
            patterns.append(pattern)
    return patterns


class EsefEntityLookup:
    """Resolves a home listing to its ESEF filer, or raises TickerNotCoveredError."""

    def __init__(self, client, overrides: Optional[Mapping[str, str]] = None, today: Optional[dt.date] = None):
        """
        Args:
            client: has search_entities(pattern) -> [(lei, name)] and fetch_filings(lei) -> [EsefFiling]
            overrides: EODHD ticker -> LEI (default: config ESEF_ENTITY_LEIS)
        """
        self.client = client
        self.overrides = dict(ESEF_ENTITY_LEIS if overrides is None else overrides)
        self.today = today

    def _recent_reports(self, lei: str) -> Optional[Tuple[EsefFiling, ...]]:
        reports = select_reports(self.client.fetch_filings(lei))
        if not reports:
            return None
        newest = max(filing.date_added[:10] for filing in reports)
        try:
            age_days = ((self.today or dt.date.today()) - dt.date.fromisoformat(newest)).days
        except ValueError:
            return None
        return tuple(reports) if age_days <= ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS * DAYS_PER_MONTH else None

    def resolve(self, ticker: str, home_name: Optional[str]) -> EsefEntity:
        """
        Args:
            ticker: EODHD ticker of the home listing, e.g. 'TSCO.LSE'
            home_name: the listing's company name (Yahoo)

        Raises:
            TickerNotCoveredError: no ESEF filer with a recent report, or more than one
        """
        stale = f"no ESEF report added within {ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS:g} months"
        if ticker.upper() in self.overrides:
            lei = self.overrides[ticker.upper()]
            reports = self._recent_reports(lei)
            if reports is None:
                raise TickerNotCoveredError(f"{ticker}: ESEF filer LEI {lei} (config) has {stale}")
            return EsefEntity(lei, home_name or "", reports)
        if not home_name:
            raise TickerNotCoveredError(f"{ticker}: no company name from Yahoo Finance to look up an ESEF filer")
        matches: Dict[str, str] = {}
        for pattern in search_patterns(home_name):
            matches = {lei: name for lei, name in self.client.search_entities(pattern) if names_match(home_name, name)}
            if matches:
                break
        if not matches:
            raise TickerNotCoveredError(f"{ticker}: no ESEF filer named like {home_name!r} on filings.xbrl.org (it has "
                                        "no reports from Germany, Ireland or AIM, and is incomplete elsewhere)")
        exact = [lei for lei, name in matches.items() if normalised_name(name) == normalised_name(home_name)]
        if len(exact) == 1 and len(matches) > 1:
            # 'AB Volvo (publ)' is Aktiebolaget Volvo, not Volvo Car AB; 'Novo Nordisk A/S' not Novo Nordisk Fonden
            matches = {exact[0]: matches[exact[0]]}
        recent = {lei: reports for lei in matches if (reports := self._recent_reports(lei)) is not None}
        listed = "; ".join(f"{name} (LEI {lei})" for lei, name in matches.items())
        if not recent:
            raise TickerNotCoveredError(f"{ticker}: ESEF filer(s) {listed} have {stale}")
        if len(recent) > 1:
            raise TickerNotCoveredError(f"{ticker}: more than one ESEF filer matches {home_name!r}: {listed}; "
                                        "list the right LEI in config ESEF_ENTITY_LEIS")
        lei, reports = next(iter(recent.items()))
        return EsefEntity(lei, matches[lei], reports)

