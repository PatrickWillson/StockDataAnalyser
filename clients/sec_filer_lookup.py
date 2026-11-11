"""
Finds the SEC filer behind a non-US home listing (SEC route for non-US companies, claude-output scope of
2026-11-07; docs/CODEBASE_GUIDE.md §12.1).

A ticker symbol is never matched across exchanges: the same letters are a different company (BA.LSE is BAE
Systems, BA.US Boeing). Instead: the home listing's company name (Yahoo) -> Yahoo's US listings of that name
-> the SEC ticker index -> a CIK, which counts only with an annual report (20-F, 40-F or 10-K) filed within
ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS. Known companies with two SEC filers are settled in config
(SEC_FOREIGN_FILER_CIKS); any other ambiguity gives no dossier, naming the candidates.
"""

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from config.data_quality_config import ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS
from config.edgar_config import SEC_FOREIGN_FILER_CIKS
from core.errors import TickerNotCoveredError

ANNUAL_REPORT_FORMS = ("20-F", "20-F/A", "40-F", "40-F/A", "10-K", "10-K/A")
DAYS_PER_MONTH = 365.25 / 12
# Words that differ between listings of one company: legal forms (Indonesia's 'PT ... Tbk' in either order),
# "holdings", "group", ADR wording, and the connective written as '&', 'and', 'et' or 'und'
_NAME_NOISE = re.compile(
    r"\b(public limited company|public limited|societe europeenne|societe anonyme|plc|p l c|ag|se|sa|s a|nv|n v|ltd|limited|inc|corp|corporation|co|"
    r"company|holdings?|group|ab|asa|oyj|spa|kgaa|the|aktiengesellschaft|aktiebolag|as|a s|bv|ordinary|shares?|"
    r"adr|ads|sponsored|telefonaktiebolaget|aktiebolaget|publ|pt|tbk|and|et|und)\b")


def without_accents(name: Optional[str]) -> str:
    """'Companhia Siderúrgica Nacional' -> 'Companhia Siderurgica Nacional' (Yahoo's search finds nothing for the first)."""
    return unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")


def normalised_name(name: str) -> str:
    """A company name without punctuation, legal forms and listing words: 'Rio Tinto Group' -> 'rio tinto'."""
    plain = re.sub(r"[^a-z0-9 ]", " ", without_accents(name).lower())
    return re.sub(r"\s+", " ", _NAME_NOISE.sub(" ", plain)).strip()


_GERMAN_SPELLING = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"})


def names_match(home: str, listing: str) -> bool:
    """
    One company's two listings: equal normalised names, or one the other plus trailing words. An umlaut may be written
    either way ('Dürr AG' at Yahoo, 'Duerr AG' at Eulerpool).
    """
    def forms(name: str):
        return {normalised_name(name), normalised_name((name or "").translate(_GERMAN_SPELLING))}

    return any(a and b and (a == b or a.startswith(b + " ") or b.startswith(a + " "))
               for a in forms(home) for b in forms(listing))


def latest_annual_report(submissions: Mapping[str, Any]) -> Optional[Tuple[str, str]]:
    """(form, filing date) of the filer's newest 20-F, 40-F or 10-K (amendments included), or None."""
    recent = submissions.get("filings", {}).get("recent", {})
    filed = [(date, form) for form, date in zip(recent.get("form", []), recent.get("filingDate", []))
             if form in ANNUAL_REPORT_FORMS and date]
    if not filed:
        return None
    date, form = max(filed)
    return form, date


@dataclass(frozen=True)
class SecFiler:
    """The SEC filer of a non-US company."""
    cik: str                       # 10 digits
    sec_name: str                  # the SEC's company name
    us_symbols: Tuple[str, ...]    # its US listings that led to it (empty when set in config)
    annual_form: str               # newest annual report: 20-F, 40-F or 10-K
    annual_filed: str              # its filing date


class SecFilerLookup:
    """Resolves a home listing to its SEC filer, or raises TickerNotCoveredError."""

    def __init__(self, edgar, yahoo, overrides: Optional[Mapping[str, str]] = None,
                 today: Optional[dt.date] = None):
        """
        Args:
            edgar: has filer_for_symbol(symbol) -> (cik, name) | None and fetch_submissions(cik)
            yahoo: has search_us_listings(name) -> [(symbol, exchange, name)], or None when the search failed
            overrides: EODHD ticker -> CIK (default: config SEC_FOREIGN_FILER_CIKS)
        """
        self.edgar = edgar
        self.yahoo = yahoo
        self.overrides = dict(SEC_FOREIGN_FILER_CIKS if overrides is None else overrides)
        self.today = today

    def _recent(self, submissions: Mapping[str, Any]) -> Optional[Tuple[str, str]]:
        latest = latest_annual_report(submissions)
        if latest is None:
            return None
        age_days = ((self.today or dt.date.today()) - dt.date.fromisoformat(latest[1])).days
        return latest if age_days <= ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS * DAYS_PER_MONTH else None

    def resolve(self, ticker: str, home_name: Optional[str]) -> SecFiler:
        """
        Args:
            ticker: EODHD ticker of the home listing, e.g. 'BP.LSE'
            home_name: the listing's company name (Yahoo)

        Raises:
            TickerNotCoveredError: no SEC filer with a recent annual report, or more than one
        """
        if ticker.upper() in self.overrides:
            cik = self.overrides[ticker.upper()]
            submissions = self.edgar.fetch_submissions(cik)
            latest = self._recent(submissions)
            if latest is None:
                raise TickerNotCoveredError(f"{ticker}: SEC filer CIK {cik} (config) has no annual report within "
                                            f"{ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS:g} months")
            return SecFiler(cik, str(submissions.get("name", "")), (), latest[0], latest[1])
        if not home_name:
            raise TickerNotCoveredError(f"{ticker}: no company name from Yahoo Finance to look up an SEC filer")
        candidates: Dict[str, List[str]] = {}
        names: Dict[str, str] = {}
        queries = [home_name] + ([without_accents(home_name)] if without_accents(home_name) != home_name else [])
        results = [self.yahoo.search_us_listings(query) for query in queries]
        listings = None if all(r is None for r in results) else [x for r in results if r for x in r]
        if listings is None:
            raise TickerNotCoveredError(f"{ticker}: Yahoo Finance search failed, so the SEC filer could not be looked "
                                        "up; try again later")
        for symbol, _, listed_name in listings:
            if not names_match(home_name, listed_name):
                continue
            found = self.edgar.filer_for_symbol(symbol)
            if found is not None:
                candidates.setdefault(found[0], []).append(symbol)
                names[found[0]] = found[1]
        if not candidates:
            raise TickerNotCoveredError(f"{ticker}: no SEC filer found for {home_name!r} (no US listing in the SEC "
                                        "index); the SEC route covers only companies that file with the SEC")
        recent = {}
        for cik in candidates:
            latest = self._recent(self.edgar.fetch_submissions(cik))
            if latest is not None:
                recent[cik] = latest
        listed = "; ".join(f"{names[c]} (CIK {c}, {', '.join(candidates[c])})" for c in candidates)
        if not recent:
            raise TickerNotCoveredError(f"{ticker}: SEC filer(s) {listed} have no 20-F, 40-F or 10-K within "
                                        f"{ANNUAL_REPORT_MAX_AGE_FOR_VERDICT_MONTHS:g} months")
        if len(recent) > 1:
            raise TickerNotCoveredError(f"{ticker}: more than one SEC filer matches {home_name!r}: {listed}; "
                                        "list the right CIK in config SEC_FOREIGN_FILER_CIKS")
        cik, (form, filed) = next(iter(recent.items()))
        return SecFiler(cik, names[cik], tuple(candidates[cik]), form, filed)
