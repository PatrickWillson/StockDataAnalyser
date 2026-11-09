"""
ESEF annual reports (xBRL-JSON from filings.xbrl.org) -> companyfacts, so clients/edgar_mapper.py reads them with
the same rules as SEC filings: the IFRS tag chains, latest-filed figures (restatements noted), EPS and share-count
checks, debt, lease and net-assets rules. Only the company-wide figures are converted (no dimensions), as SEC
companyfacts keeps, and only the ifrs-full taxonomy: a company's own extension tags are not read (Tesco tags its
revenue as tescoplc:RevenueFromSaleOfGoodsAndServices, so it has none here).

xBRL-JSON periods are datetimes, a period end being the instant after it: "2024-01-01T00:00:00" ends 2023-12-31
(xBRL-JSON, OIM 1.0). Which reports are annual comes from the facts, not the index (whose period end can be wrong,
and which lists interim reports too): a report is annual when its profit, revenue or EPS covers a year ending on
the latest period end of those figures.
"""

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from clients import edgar_mapper
from clients.edgar_mapper import DURATIONS, ESEF_FORM, IFRS, YEAR_END_TAGS
from clients.esef_client import EsefFiling

SOURCE_LABEL = "ESEF"            # how dossier notes name the source
CORE_DIMENSIONS = frozenset({"concept", "entity", "period", "unit", "language"})
# A report's own period comes from its income-statement figures only: other durations can run past the year end
# (Unilever's annual reports date two facts as zero-day periods on the report's own date, 2023-02-09)
EPS_TAGS = frozenset({"BasicEarningsLossPerShare", "DilutedEarningsLossPerShare"})
DATING_TAGS = frozenset(tag.split(":", 1)[1] for tag in YEAR_END_TAGS if tag.startswith(f"{IFRS}:"))


def _date(text: str) -> str:
    """'2024-01-01T00:00:00' -> '2023-12-31' (a midnight is the end of the day before); '...T12:00:00' -> that day."""
    moment = dt.datetime.fromisoformat(text.strip()[:19])
    if moment.time() == dt.time(0, 0):
        moment -= dt.timedelta(days=1)
    return moment.date().isoformat()


def _period(text: str) -> Tuple[Optional[str], str]:
    """(start, end) of a duration, or (None, date) of an instant. A start is the first day itself."""
    if "/" in text:
        start, end = text.split("/", 1)
        return dt.datetime.fromisoformat(start.strip()[:19]).date().isoformat(), _date(end)
    return None, _date(text)


def _unit(text: Optional[str]) -> Optional[str]:
    """'iso4217:EUR' -> 'EUR', 'iso4217:EUR/xbrli:shares' -> 'EUR/shares', 'xbrli:shares' -> 'shares'; else None."""
    if not text:
        return None
    parts = [part.split(":")[-1] for part in text.split("/")]
    if parts == ["shares"] or (len(parts) == 1 and len(parts[0]) == 3 and parts[0].isupper()):
        return parts[0]
    if len(parts) == 2 and parts[1] == "shares" and len(parts[0]) == 3 and parts[0].isupper():
        return f"{parts[0]}/shares"
    return None


@dataclass(frozen=True)
class EsefReport:
    """One report's company-wide ifrs-full figures, as companyfacts rows."""
    filing: EsefFiling
    period_end: Optional[str]          # the report's own latest period end (None: no figures)
    annual: bool
    facts: Mapping[str, Any]           # {"facts": {"ifrs-full": {tag: {"units": {unit: [row]}}}}}
    notes: Tuple[str, ...] = ()        # tagging errors allowed for


def report_facts(filing: EsefFiling, report: Mapping[str, Any]) -> EsefReport:
    """A report's company-wide ifrs-full figures as companyfacts rows (form ESEF, filed = date added to the index)."""
    filed = filing.date_added[:10] or filing.period_end
    tags: Dict[str, Dict[str, Any]] = {}
    durations: List[Tuple[str, str]] = []
    for fact in (report.get("facts") or {}).values():
        dimensions = fact.get("dimensions") or {}
        concept, period, unit = dimensions.get("concept", ""), dimensions.get("period"), _unit(dimensions.get("unit"))
        prefix, _, tag = concept.partition(":")
        if prefix != IFRS or not period or unit is None or set(dimensions) - CORE_DIMENSIONS:
            continue
        if tag in EPS_TAGS and "/" not in unit and unit != "shares":
            unit = f"{unit}/shares"    # EPS tagged in a plain currency (Bonduelle FY2025-26: 0.51 "EUR"): per share
        try:
            value = float(fact.get("value"))
            start, end = _period(period)
        except (TypeError, ValueError):
            continue
        row: Dict[str, Any] = {"end": end, "val": value, "filed": filed, "form": ESEF_FORM, "accn": filing.fxo_id}
        if start:
            row["start"] = start
            if tag in DATING_TAGS:
                durations.append((start, end))
        rows = tags.setdefault(tag, {"units": {}})["units"].setdefault(unit, [])
        if row not in rows:
            rows.append(row)
    if not durations:
        return EsefReport(filing, None, False, {"facts": {}})
    latest = max(end for _, end in durations)
    low, high = DURATIONS["year"]
    annual = any(end == latest and low <= edgar_mapper._days(start, end) <= high for start, end in durations)
    notes = []
    year_start = next((start for start, end in durations if end == latest and low <= edgar_mapper._days(start, end) <= high), None)
    for tag in EPS_TAGS:
        for rows in tags.get(tag, {}).get("units", {}).values():
            own_year = [r for r in rows if r["end"] == latest and "start" in r]
            if year_start and own_year and not any(r["start"] == year_start for r in own_year):
                # The year's EPS in a context running back over more than the year (Games Workshop FY2025: 594.9 for
                # 2023-05-29 to 2025-06-01): its own year's figure, mis-dated
                for row in own_year:
                    if edgar_mapper._days(row["start"], latest) > high:
                        row["start"] = year_start
                        notes.append(f"{SOURCE_LABEL}: FY{latest[:4]} {tag} tagged for a period longer than the year "
                                     "(a dating error); read as the year's figure")
    return EsefReport(filing, latest, annual, {"facts": {IFRS: tags}}, tuple(dict.fromkeys(notes)))


def companyfacts(reports: Sequence[EsefReport]) -> Tuple[Dict[str, Any], List[str]]:
    """
    The annual reports pooled into one companyfacts, and notes on the reports left out. Of two annual reports for the
    same year (one report indexed twice under different dates), the one added to the index last is kept.
    """
    annual: Dict[str, EsefReport] = {}
    skipped: List[str] = []
    for report in reports:
        if not report.annual or report.period_end is None:
            skipped.append(report.filing.period_end)
            continue
        current = annual.get(report.period_end)
        if current is None or report.filing.date_added > current.filing.date_added:
            annual[report.period_end] = report
    pooled: Dict[str, Dict[str, Any]] = {}
    for end in sorted(annual):
        for tag, data in annual[end].facts["facts"].get(IFRS, {}).items():
            units = pooled.setdefault(tag, {"units": {}})["units"]
            for unit, rows in data["units"].items():
                units.setdefault(unit, []).extend(rows)
    notes = [note for end in sorted(annual) for note in annual[end].notes]
    if skipped:
        notes.append(f"{SOURCE_LABEL}: interim or undated reports not used (indexed period ends "
                     f"{', '.join(sorted(skipped))}); annual reports only")
    return {"facts": {IFRS: pooled}}, notes
