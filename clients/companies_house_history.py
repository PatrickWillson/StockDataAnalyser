"""
London listings: net income for the years before the ones already held (Yahoo Finance, then RNS announcements), from
the annual accounts the company filed at Companies House, read by OCR (clients/ocr_statement_reader.py).

GRAHAM_METHODOLOGY §8.13 (and §8.12): "the chief source of statistical data is, of course, the reports issued to the
stockholders" (Security Analysis ch. 3): the filed accounts are those reports. They are image scans, so each figure is
an OCR reading, used only when it reconciled within its own statement (OcrReading.verified). The years are gated like
the announcements: the readings must agree with the held years in at least RNS_MIN_OVERLAP_YEARS overlapping years
and disagree in none (within RNS_MATCH_REL, or RNS_MATCH_UNITS of the statement's rounding unit), which also rules out
a wrong company number. Each older year is read twice where it can be: from its own accounts and as the next year's
comparative; the comparative (the restated figure, §8.7) is used, flagged when it differs, and the year is refused
when the two are more than RNS_CHAIN_REL apart. Net income only: revenue is not reconciled by the checks, so it is not
used; no share count or per-share figure (as for announcement years).
"""

import datetime as dt
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from clients.companies_house_client import AccountsFiling, CompaniesHouseClient
from clients.eulerpool_mapper import NO_SHARE_COUNT
from config.companies_house_config import CH_MAX_FILINGS_READ
from config.rns_config import (RNS_CHAIN_REL, RNS_DATE_TOLERANCE_DAYS, RNS_MATCH_REL, RNS_MATCH_UNITS,
                               RNS_MIN_OVERLAP_YEARS)
from core.history import fiscal_year
from core.fundamentals import IncomeStatementRow
from core.errors import DataSourceError

logger = logging.getLogger(__name__)

SOURCE = "Companies House filed accounts (the company's annual reports, read by OCR)"
READING_VERSION = "2026-11-14"        # cached OCR readings of another version are read again


@dataclass(frozen=True)
class FilingYears:
    """One accepted (reconciled) OCR reading of a filing: its two years' net income in currency units."""
    made_up_date: str
    period_end: str
    prior_end: str
    net_income: Tuple[float, float]               # (current, prior)
    unit: float
    currency: Optional[str]
    total: Optional[Tuple[float, float]] = None   # the statement's total profit where net income is the owners' line


@dataclass(frozen=True)
class CompaniesHouseHistory:
    income_statements: Tuple[IncomeStatementRow, ...] = ()
    shares_by_year: Mapping[str, float] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()


def _near(a: str, b: str) -> bool:
    return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days) <= RNS_DATE_TOLERANCE_DAYS


def companies_house_history(known: Mapping[str, float], readings: Sequence[FilingYears], currency: str,
                            held_source: str = "Yahoo Finance's statements") -> CompaniesHouseHistory:
    """The years before the held ones (known: period end -> net income), from accepted readings (see module)."""
    def not_used(reason: str) -> CompaniesHouseHistory:
        return CompaniesHouseHistory(notes=(f"History before the held years: {SOURCE} not used: {reason}",))

    other = [r for r in readings if r.currency and r.currency != currency]
    readings = [r for r in readings if r not in other]
    if not readings:
        return not_used("no accounts could be read and reconciled" if not other else
                        f"its accounts are in {other[0].currency}, the held years in {currency}")
    # every reading of each year end: (value, unit, 'own' or 'comparative', the statement's total profit or None)
    by_end: Dict[str, List[Tuple[float, float, str, Optional[float]]]] = {}
    for r in readings:
        for end, value, kind, total in ((r.period_end, r.net_income[0], "own", r.total[0] if r.total else None),
                                        (r.prior_end, r.net_income[1], "comparative", r.total[1] if r.total else None)):
            key = next((e for e in by_end if _near(e, end)), end)
            by_end.setdefault(key, []).append((value, r.unit, kind, total))
    pairs, disagreed = [], []
    for end, held in known.items():
        key = next((e for e in by_end if _near(e, end)), None)
        if key is None:
            continue
        pairs.append(end)
        if all(abs(v - held) > max(RNS_MATCH_REL * abs(held), RNS_MATCH_UNITS * unit)
               for value, unit, _, total in by_end[key] for v in (value, total) if v is not None):
            disagreed.append(f"FY{fiscal_year(end)} {by_end[key][0][0] / 1e6:,.3f}M filed, {held / 1e6:,.3f}M in "
                             f"{held_source}")
    checked = f"within {RNS_MATCH_REL:.0%}, or {RNS_MATCH_UNITS:g} of the statement's rounding unit"
    if len(pairs) < RNS_MIN_OVERLAP_YEARS:
        return not_used(f"its accounts overlap {held_source} in {len(pairs)} year(s), fewer than {RNS_MIN_OVERLAP_YEARS}")
    if disagreed:
        return not_used(f"its net income did not agree with {held_source} ({checked}) in every overlapping year: "
                        + "; ".join(disagreed))
    first_held = min(known)
    rows, restated, refused, single = [], [], [], []
    for end in sorted((e for e in by_end if e < first_held and not _near(e, first_held)), reverse=True):
        own = [v for v, _, kind, _ in by_end[end] if kind == "own"]
        comparative = [v for v, _, kind, _ in by_end[end] if kind == "comparative"]
        unit = max(u for _, u, _, _ in by_end[end])
        if own and comparative:
            if abs(comparative[0] - own[0]) > RNS_CHAIN_REL * max(abs(own[0]), abs(comparative[0])):
                refused.append(f"FY{fiscal_year(end)} ({own[0] / 1e6:,.3f}M in its accounts, {comparative[0] / 1e6:,.3f}M "
                               "as the next year's comparative)")
                continue
            if abs(comparative[0] - own[0]) > RNS_MATCH_UNITS * unit:
                restated.append(f"FY{fiscal_year(end)} {own[0] / 1e6:,.3f}M -> {comparative[0] / 1e6:,.3f}M")
            value = comparative[0]
        else:
            value = (comparative or own)[0]
            single.append(fiscal_year(end))
        rows.append(IncomeStatementRow(end, None, float(value), None))
    if not rows:
        return not_used(f"no year before FY{fiscal_year(first_held)} could be read and reconciled"
                        + (f" (not used: {'; '.join(refused)})" if refused else ""))
    span = sorted(fiscal_year(r.period_end) for r in rows)
    overlap = sorted(fiscal_year(e) for e in pairs)
    notes = [f"History before FY{fiscal_year(first_held)}: {SOURCE} for FY{span[0]}-FY{span[-1]} ({len(span)} years), "
             f"each figure reconciled within its own statement and net income checked against {held_source} in "
             f"FY{overlap[0]}-FY{overlap[-1]} ({checked}) in every overlapping year; a year read both from its own "
             "accounts and as the next year's comparative takes the comparative (restated). Net income (attributable "
             "to the owners of the parent) only: revenue is not used (the checks do not reconcile it), no balance "
             "sheets, no share count or per-share figures for those years"]
    if restated:
        notes.append(f"{SOURCE}: restated in the next year's accounts: " + "; ".join(restated))
    if single:
        notes.append(f"{SOURCE}: read from one filing only (not cross-checked against a second): FY"
                     + ", FY".join(sorted(single)))
    if refused:
        notes.append(f"{SOURCE}: not used, the two readings of the year differ by more than {RNS_CHAIN_REL:.0%}: "
                     + "; ".join(refused))
    if other:
        notes.append(f"{SOURCE}: accounts in another currency than the held years' {currency} left out: "
                     + ", ".join(f"FY{fiscal_year(r.period_end)} ({r.currency})" for r in other))
    return CompaniesHouseHistory(tuple(rows), {fiscal_year(r.period_end): NO_SHARE_COUNT for r in rows}, tuple(notes))


def filings_to_read(filings: Sequence[AccountsFiling], known: Mapping[str, float], wanted_years: int) -> List[AccountsFiling]:
    """The annual filings worth reading: the two whose year ends are the earliest held years (the overlap), then the
    older ones, newest first, enough for wanted_years more years and one more (the cross-check of the oldest year);
    at most CH_MAX_FILINGS_READ."""
    annual = sorted((f for f in filings if f.annual), key=lambda f: f.made_up_date, reverse=True)
    held = sorted(known)
    first_held = held[0]
    overlap = [f for f in annual if any(_near(f.made_up_date, e) for e in held[:2])]
    older = [f for f in annual if f.made_up_date < first_held and not _near(f.made_up_date, first_held)]
    return (overlap + older[:max(0, wanted_years)])[:CH_MAX_FILINGS_READ]


class CompaniesHouseHistorySource:
    """Reads (and caches) a London listing's filed accounts for the years before the held ones."""

    def __init__(self, client: CompaniesHouseClient, read_filing=None):
        self.client = client
        if read_filing is None:
            from clients.ocr_statement_reader import read_filing
        self._read_filing = read_filing

    def history(self, name: str, known: Mapping[str, float], currency: str, wanted_years: int,
                held_source: str = "Yahoo Finance's statements") -> CompaniesHouseHistory:
        def not_used(reason: str) -> CompaniesHouseHistory:
            return CompaniesHouseHistory(notes=(f"History before the held years: {SOURCE} not used: {reason}",))

        if not known or wanted_years <= 0:
            return CompaniesHouseHistory()
        try:
            number = self.client.company_number(name)
            if number is None:
                return not_used(f"no single active plc named {name!r} at Companies House")
            filings = filings_to_read(self.client.accounts_filings(number), known, wanted_years)
            readings = [r for f in filings if (r := self._reading(number, f)) is not None]
        except DataSourceError as e:
            return not_used(f"Companies House unavailable ({e})")
        except (OSError, RuntimeError, ImportError) as e:       # tesseract or the PDF library missing or failing
            return not_used(f"OCR unavailable ({type(e).__name__})")
        history = companies_house_history(known, readings, currency, held_source)
        if history.income_statements:
            history = CompaniesHouseHistory(history.income_statements, history.shares_by_year,
                                            history.notes[:1] + (f"Companies House company {number}; {len(filings)} "
                                                                 f"accounts read, {len(readings)} reconciled",)
                                            + history.notes[1:])
        return history

    def _reading(self, number: str, filing: AccountsFiling) -> Optional[FilingYears]:
        """The filing's accepted reading, or None (refused or unreadable); cached beside the PDF."""
        cache = os.path.join(self.client.cache_dir, number, f"{filing.transaction_id}.reading.json")
        if os.path.exists(cache):
            with open(cache) as f:
                saved = json.load(f)
            if saved.get("version") == READING_VERSION:
                return FilingYears(**{k: tuple(v) if isinstance(v, list) else v for k, v in saved["years"].items()}) \
                    if saved.get("years") else None
        path = self.client.fetch_pdf(number, filing)
        years = None
        if path is not None:
            logger.info("Companies House %s: reading the accounts to %s by OCR", number, filing.made_up_date)
            _, reading = self._read_filing(path, filing.made_up_date, single_entity=not filing.group)
            st = reading.accepted
            if st is not None:
                years = FilingYears(filing.made_up_date, st.period_end, st.prior_end, tuple(st.net_income), st.unit or 1.0,
                                    st.currency, tuple(st.total) if st.total else None)
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w") as f:
            json.dump({"version": READING_VERSION, "years": years.__dict__ if years else None}, f)
        return years
