"""
RNS final-results announcement -> the company's announced revenue and net income for the year and the year before
(UK route; config/rns_config.py; GRAHAM_METHODOLOGY §8.12), and the overlap gate against Yahoo Finance's years.

The consolidated income statement is found by its heading (a short row naming the group's income statement, profit
and loss account or statement of comprehensive income), then read row by row until the next statement:
- a row is its label and its figures (a dash is zero; pence and percentages are not figures); a row with a label and
  no figures is joined to the next ("Profit attributable to:" + "Owners of the parent | 2,714 | 2,280");
- the columns: the commonest number of figures in a row; a note reference before them is dropped; with three
  columns a year (underlying / exceptional / total) the last of each year's group is the total;
- the unit and currency from the statement's own header (£'000, $m, £); none found: the statement is not read;
- net income: profit or loss attributable to the owners (equity holders, shareholders) of the parent, else profit or
  loss for the year (UK GAAP: for the financial year, or on ordinary activities after taxation).
Then the figures agree with Yahoo Finance's in every overlapping year, or none is used (rns_history).
"""

import datetime as dt
import html as html_lib
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from clients.edgar_mapper import EdgarAnnualData
from clients.eulerpool_mapper import CONTINUITY_RATIO, NO_PER_SHARE, NO_SHARE_COUNT, allowed_gap
from config.eulerpool_config import EULERPOOL_MATCH_REL
from config.rns_config import (RNS_CHAIN_REL, RNS_DATE_TOLERANCE_DAYS, RNS_MATCH_REL, RNS_MATCH_UNITS,
                               RNS_MIN_OVERLAP_YEARS)
from core.fundamentals import IncomeStatementRow
from core.history import fiscal_year

SOURCE = "RNS results announcements (the company's own announced results, via the Investegate archive)"
MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december")
_MONTH = "|".join(MONTHS)
DATE = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH}),?\s+((?:19|20)\d{{2}})\b|"
                  rf"\b({_MONTH})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+((?:19|20)\d{{2}})\b", re.I)
HEADING = re.compile(r"^(?:the )?(?:(?:unaudited|audited|condensed|preliminary|summary|summarised|abridged)\s+)*"
                     r"(?:(?:consolidated|group)\b[^|]{0,40}?\b(?:income statements?|statements? of (?:comprehensive )?income|"
                     r"profit and loss(?: account)?|statements? of profit or loss|statements? of total return)|"
                     r"statements? of (?:consolidated|group) (?:comprehensive )?income)", re.I)
# a heading without 'consolidated' or 'group' (a company presenting its group statement plainly), read only when the
# announcement has no consolidated one; never the parent company's own ('Company statement of ...')
PLAIN_HEADING = re.compile(r"^(?:the )?(?:(?:unaudited|audited|condensed|preliminary|summary)\s+)*(?:company\s+)?(?:income statements?|"
                           r"statements? of (?:comprehensive )?income|profit and loss(?: account)?|statements? of profit or loss|"
                           r"statements? of total return)", re.I)
OTHER_STATEMENT = re.compile(r"^(?:(?:unaudited|audited|condensed)\s+)*(?:(?:consolidated|group|company|parent)\b[^|]{0,40}?)?"
                             r"\b(?:statements? of financial position|balance sheets?|cash ?flows?|statements? of changes in equity|"
                             r"reconciliation of movements)", re.I)
_NUMBER = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
VALUE = re.compile(rf"^(?:\(-?{_NUMBER}\)|-?{_NUMBER})$")                # brackets in pairs: '11)' is not a figure
DASH = re.compile(r"^[-–—]+$")
NOT_A_FIGURE = re.compile(r"^\(?-?\d+(?:\.\d+)?\)?\s*(?:p|c|cents?|pence|%)$", re.I)
YEAR = re.compile(r"^(?:19|20)\d{2}$")
NOTE_REF = re.compile(r"\d{1,2}(?:\.\d{1,2})?[a-z]?")
THOUSANDS = re.compile(r"['’`]\s?000|\b000['’]?s\b|[£$€]\s?000\b|[£$€]k\b|\bthousands?\b", re.I)
MILLIONS = re.compile(r"[£$€]\s?m\b|[£$€]\s?mn\b|\b(?:gbp|usd|eur)\s?m\b|\bmillions?\b", re.I)
UNITS = re.compile(r"(?:^|[\s|(])(?:£|\$|€|US\$|USD|GBP|EUR|euros?)(?:\s|\||\)|$)", re.I)
REVENUE = re.compile(r"^(?:total |group )?(?:revenue|turnover|sales)\b(?!.*\bcost)", re.I)
OWNERS = re.compile(r"attributable to\s*[:\-\u2013]*\s*(?:-\s*)?(?:the )?(?:owners|equity holders|equity shareholders|ordinary shareholders|"
                    r"shareholders|members)\b", re.I)
OWNER_LINE = re.compile(r"^(?:-\s*)?(?:the )?(?:owners|equity holders|equity shareholders|ordinary shareholders|"
                        r"shareholders|members)\b", re.I)
COLUMN_HEADER = re.compile(r"^(?:notes?\b|[£$€]|us\$|['\u2019]?000)[\s£$€'\u20190-9a-z]*$", re.I)
FOR_THE_YEAR = re.compile(r"^(?:net |retained |total )?(?:\(loss\)/profit|profit/\(loss\)|\(profit\)/loss|loss/\(profit\)|"
                          r"\(loss\)|profit|loss)(?: after tax(?:ation)?)?"
                          r"(?: and (?:total |other )?comprehensive (?:income|loss|expense|charge))?"
                          r"(?: attributable to [a-z ]+)? (?:for|of) (?:the )?(?:financial )?(?:year|period)(?:/(?:year|period))?\b",
                          re.I)
AFTER_TAX = re.compile(r"^(?:net |total )?(?:\(loss\)/profit|profit/\(loss\)|\(profit\)/loss|loss/\(profit\)|\(loss\)|profit|loss|"
                       r"return/\(loss\)|\(loss\)/return|return)(?: (?:for|of) the (?:financial )?(?:year|period))?"
                       r"(?: on ordinary activities)? (?:before and )?after tax(?:ation)?\b"
                       r"|^(?:net |total )?return attributable to (?:equity|ordinary)?\s*(?:shareholders|holders)?\b", re.I)
ORDINARY_ACTIVITIES = re.compile(r"^(?:\(loss\)/profit|profit/\(loss\)|profit|loss) on ordinary activities after tax", re.I)


@dataclass(frozen=True)
class RnsStatement:
    """One announcement's consolidated income statement: the year and the year before (figures in currency units)."""
    announcement_id: int
    period_end: str
    prior_end: str
    currency: Optional[str]
    unit: float
    net_income: Tuple[float, float]
    revenue: Tuple[Optional[float], Optional[float]]
    label: str
    # the statement's total 'profit for the year' (incl. minority interests) where net income is the owners' line:
    # a second reading of the year for the overlap check only (Yahoo may carry either)
    total: Optional[Tuple[float, float]] = None


@dataclass(frozen=True)
class RnsHistory:
    """Years before Yahoo Finance's (newest first) that passed the gate, or none, and the notes that explain them."""
    income_statements: Tuple[IncomeStatementRow, ...] = ()
    shares_by_year: Mapping[str, float] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()


def _clean(text: str) -> str:
    text = html_lib.unescape(text).replace("\xa0", " ").replace("Â£", "£").replace("â€™", "'").replace("’", "'").replace("‘", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\b((?:19|20)\d) (\d)\b", r"\1\2", text)          # a year split by a stray space: '202 5'


def _bare(text: str) -> str:
    """A row's text without the rules and punctuation drawn around a heading ('____ INCOME STATEMENT ____')."""
    text = re.sub(r"^[\W_]+|[\W_]+$", "", text)
    return re.sub(r"^([A-Za-z]) ([A-Za-z]{2,})", r"\1\2", text)      # a drop capital: 'C ONSOLIDATED


def rows_of(page: str) -> List[List[str]]:
    """The announcement as rows of cells, in order: table rows, else (legacy text) lines split at wide gaps."""
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)
    legacy = re.search(r'class="legacy-text-announcement"[^>]*>(.*?)</div>', page, flags=re.S | re.I)
    if legacy:
        rows = []
        for line in html_lib.unescape(re.sub(r"<[^>]+>", "", legacy.group(1))).splitlines():
            line = line.replace("Â£", "£").replace("\xa0", " ").rstrip()
            if line.strip():
                rows.append([c for c in (_clean(c) for c in re.split(r"\s{2,}", line.strip())) if c])
        return rows
    rows = []
    for segment in re.split(r"(<tr\b.*?</tr>)", page, flags=re.S | re.I):
        if segment[:3].lower() == "<tr":
            cells = [_clean(re.sub(r"<[^>]+>", " ", c)) for c in re.findall(r"<t[dh]\b.*?</t[dh]>", segment, re.S | re.I)]
            if any(cells):
                rows.append([c for c in cells if c])
        else:
            text = re.sub(r"<br\s*/?>|</(?:p|div|li|h\d)>", "\n", segment, flags=re.I)
            for line in re.sub(r"<[^>]+>", " ", text).splitlines():
                if _clean(line):
                    rows.append([_clean(line)])
    return rows


def _value(token: str) -> Optional[float]:
    token = re.sub(r"\s+(?=\))|(?<=\()\s+", "", token.strip())     # '(1,756 )' is '(1,756)'; '5 1,234' stays two
    # a stray space inside a thousands group, from two spans of one cell: '1,01 8' and '1, 499' (three digits after the comma)
    token = re.sub(r",(\d{0,2}) (\d{1,3})(?=\)?$)", lambda m: "," + m[1] + m[2] if len(m[1] + m[2]) == 3 else m[0], token)
    if DASH.match(token):
        return 0.0
    if not VALUE.match(token):
        return None
    negative = token.startswith("(") or token.startswith("-")
    return (-1 if negative else 1) * float(re.sub(r"[(),\-]", "", token))


def _split(cells: Sequence[str]) -> Tuple[str, List[str]]:
    """(label, figure tokens) of a row; a legacy line's trailing figures are split off its label."""
    label, figures = [], []
    for cell in cells:
        if NOT_A_FIGURE.match(cell):
            continue
        if _value(cell) is not None:
            figures.append(cell)
            continue
        words = cell.split(" ")
        tail = []
        while words and _value(words[-1]) is not None:
            tail.insert(0, words.pop())
        if tail and not figures:
            label.append(" ".join(words))
            figures.extend(tail)
        else:
            label.append(cell)
    # 'Profit / (loss) for the year' is 'Profit/(loss) for the year'
    text = re.sub(r"\s*/\s*", "/", " ".join(x for x in label if x))
    text = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", text))           # 'profit/( loss)' is 'profit/(loss)'
    text = re.sub(r"\b([b-hj-z]) (?=[a-z]{2,}\b)", r"\1", text, flags=re.I)  # a word split by a space: 'y ear'
    return re.sub(r"\)(?=[a-z])", ") ", text, flags=re.I).strip(), figures  # '(loss)for' is '(loss) for'


def _dates(text: str) -> List[dt.date]:
    out = []
    for m in DATE.finditer(text):
        day, month, year = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(5), m.group(4), m.group(6))
        try:
            out.append(dt.date(int(year), MONTHS.index(month.lower()) + 1, int(day)))
        except ValueError:
            continue
    return out


def _year_before(day: dt.date) -> dt.date:
    try:
        return day.replace(year=day.year - 1)
    except ValueError:                       # 29 February
        return day.replace(year=day.year - 1, day=28)


def _unit(header: str) -> Tuple[Optional[float], Optional[str]]:
    if THOUSANDS.search(header):
        unit = 1e3
    elif MILLIONS.search(header):
        unit = 1e6
    elif UNITS.search(f" {header} "):
        unit = 1.0
    else:
        return None, None
    lowered = header.lower()
    currency = ("USD" if ("$" in header or "usd" in lowered) else "EUR" if ("€" in header or "eur" in lowered
                                                                          or "euro" in lowered)
                else "GBP" if ("£" in header or "gbp" in lowered) else None)
    return unit, currency


def parse_statement(page: str, announcement_id: int) -> Optional[RnsStatement]:
    """The consolidated income statement of a results announcement, or None when it cannot be read."""
    rows = rows_of(page)
    announced_period = next((d for row in rows[:60] for d in _dates(" ".join(row))
                             if re.search(r"(?:year|period|months) ended", " ".join(row), re.I)), None)
    for pattern in (HEADING, PLAIN_HEADING):
        fallback = None
        for start, row in enumerate(rows):
            heading = _bare(" ".join(row))
            if len(heading) > 200 or not pattern.match(heading) or any(
                    not re.search(r"\b(?:19|20)\d{2}\b", cell) for cell in row[1:]):
                continue                             # a table's header row ('Income statement | 1% increase ...')
            statement = _read_block(rows[start + 1:start + 180], heading, announced_period, announcement_id)
            if statement is not None and statement.revenue[0] is not None:
                return statement
            fallback = fallback or statement
        # a statement without a revenue line (a separate statement of comprehensive income) only when none has one
        if fallback is not None:
            return fallback
    return None


def _read_block(block: List[List[str]], heading: str, announced: Optional[dt.date],
                announcement_id: int) -> Optional[RnsStatement]:
    header, data, prefix, year_columns, attribution = [heading], [], "", [], ""
    for cells in block:
        text = " ".join(cells)
        bare = _bare(text)
        if (HEADING.match(bare) or PLAIN_HEADING.match(bare)) and re.search(r"\bcontinued\b", text, re.I):
            continue                                 # the same statement over a page break
        if HEADING.match(bare) or PLAIN_HEADING.match(bare) or OTHER_STATEMENT.match(bare) \
                or re.match(r"^company\b[^|]{0,40}?\b(?:income|profit)", bare, re.I):
            break
        label, figures = _split(cells)
        if not data:
            # a header row naming each column's year ('Underlying 2025 | Non-underlying 2025 | Total 2025 | 2024')
            cell_years = [y for y in (re.findall(r"\b((?:19|20)\d{2})\b", cell) for cell in cells) if y]
            if len(cell_years) >= 2 and all(len(y) == 1 for y in cell_years):
                year_columns = [int(y[0]) for y in cell_years]
        if figures and all(YEAR.match(f) for f in figures):
            header.append(text)
            continue
        if len(figures) == 1 and not data:
            header.append(text)                      # 'Year ended | 31 March 2026' before the first line of figures
            continue
        if not figures:
            if not data:
                header.append(text)
            if COLUMN_HEADER.match(label):           # 'Note £'000 £'000' heads columns, not lines
                continue
            if re.search(r"attributable to", label, re.I):
                # a bare 'Attributable to:' belongs to the line above it ('Total comprehensive income ...')
                attribution = (f"{data[-1][0]} {label}" if data and re.match(r"^attributable to:?$", label, re.I)
                               else label)
                label = attribution
            prefix = label
            continue
        if len(figures) % 2 and NOTE_REF.fullmatch(figures[0]):
            figures = figures[1:]                    # a note reference before the year columns
        if not OWNER_LINE.match(label) and not re.match(r"non-controlling|minority", label, re.I):
            attribution = ""                         # the list of attributions has ended
        context = attribution if attribution and attribution != prefix else ""
        data.append((label, " ".join(x for x in (context, prefix, label) if x), figures))
        if not prefix.endswith(":"):                 # 'Profit attributable to:' heads each line of its list
            prefix = ""
    widths = Counter(len(f) for _, _, f in data if len(f) >= 2)
    if len(data) < 4 or not widths:
        return None
    width = min(w for w, n in widths.items() if n == max(widths.values()))
    if len(year_columns) > width and widths.get(len(year_columns)):
        # the header names a year for more columns than the commonest line has (many lines unreadable, Judges
        # Scientific): the table is that wide; a header naming one year per group never narrows it (Alumasc)
        width = len(year_columns)
    unit, currency = _unit(" | ".join(header))
    if unit is None:
        return None
    years_desc = sorted(set(year_columns), reverse=True)
    group_and_company = re.search(r"\band company\b", heading, re.I) or re.search(r"\bthe company\b", " ".join(header), re.I)
    if group_and_company and len(year_columns) == width and len(years_desc) >= 2:
        picks = (year_columns.index(years_desc[0]), year_columns.index(years_desc[1]))     # the group's, first
    elif len(year_columns) == width and len(years_desc) >= 2 and years_desc[0] - years_desc[1] == 1:
        # columns headed by year (Billington: underlying, non-underlying, total 2025 | total 2024): the last column
        # under each year is its total
        picks = (max(i for i, y in enumerate(year_columns) if y == years_desc[0]),
                 max(i for i, y in enumerate(year_columns) if y == years_desc[1]))
    elif group_and_company and width == 4:
        picks = (0, 1)                               # group 2025, group 2024 | company 2025, company 2024
    elif width % 2:
        return None
    else:
        picks = (0, 1) if width == 2 else (width // 2 - 1, width - 1)

    def figures_of(tokens: List[str], pair: bool = False) -> Optional[Tuple[float, float]]:
        if pair and width > 2 and len(tokens) == 2:
            # an attribution line printed under the totals only (owners | minorities lists, Alumasc 2010): current, prior
            return _value(tokens[0]) * unit, _value(tokens[1]) * unit
        if len(tokens) != width:
            return None
        return _value(tokens[picks[0]]) * unit, _value(tokens[picks[1]]) * unit

    def first(predicate, pair: bool = False) -> Optional[Tuple[str, Tuple[float, float]]]:
        for own, joined, tokens in data:
            if predicate(own, joined):
                got = figures_of(tokens, pair)
                if got is not None:
                    return joined, got
        return None

    def after_discontinued(predicate) -> Optional[Tuple[str, Tuple[float, float]]]:
        """The first line the predicate takes, unless a discontinued-operations line follows it and then another line
        the predicate takes: that later line is the total after discontinued operations (ALU 2017: 'Profit for the
        period' 5,178 under continuing operations, 'Profit for the period' 6,484 after the discontinued line)."""
        hits = [i for i, (own, joined, tokens) in enumerate(data) if predicate(own, joined) and figures_of(tokens)]
        if not hits:
            return None
        chosen = hits[0]
        for later in hits[1:]:
            if any(re.search(r"discontinued", data[k][0], re.I) for k in range(chosen + 1, later)):
                chosen = later
        own, joined, tokens = data[chosen]
        return joined, figures_of(tokens)

    def excluded(text: str) -> bool:
        return bool(re.search(r"per share|earnings per|dividend|non-controlling|minority|^(?:total )?equity\b", text, re.I))

    found = (first(lambda own, joined: bool(OWNERS.search(joined) or (re.search(r"attributable to", joined, re.I)
                                                                     and OWNER_LINE.match(own)))
                   and not excluded(joined)
                   and ("comprehensive" not in joined.lower()
                        or re.search(r"(?:profit|loss) and total comprehensive", joined, re.I) is not None), pair=True)
             # 'Total (loss)/profit for the year' after continuing and discontinued lines is the year's net income
             or first(lambda own, joined: re.match(r"^total ", own, re.I) is not None and bool(FOR_THE_YEAR.match(own))
                      and "comprehensive" not in own.lower() and not excluded(own))
             or after_discontinued(lambda own, joined: any(FOR_THE_YEAR.match(t) and not excluded(t)
                                                           and not re.search(r"continuing|discontinued", t, re.I)
                                                           for t in (own, joined)))
             or first(lambda own, joined: any(FOR_THE_YEAR.match(t) and not excluded(t) for t in (own, joined)))
             or first(lambda own, joined: bool(AFTER_TAX.match(own)) and not excluded(own)
                      and not re.search(r"continuing|discontinued", own, re.I))
             or first(lambda own, joined: bool(ORDINARY_ACTIVITIES.match(own)) and not excluded(joined)))
    if found is None:
        return None
    revenue = first(lambda own, joined: bool(REVENUE.match(own)))
    total = after_discontinued(lambda own, joined: bool(FOR_THE_YEAR.match(own)) and not excluded(own)
                               and not re.search(r"continuing|discontinued|attributable|comprehensive", own, re.I))
    dates = sorted(set(_dates(" | ".join(header))), reverse=True)
    end = dates[0] if dates else announced
    if end is None:
        return None
    prior = next((d for d in dates[1:] if abs((_year_before(end) - d).days) <= 15), _year_before(end))
    return RnsStatement(announcement_id, end.isoformat(), prior.isoformat(), currency, unit, found[1],
                        revenue[1] if revenue else (None, None), found[0][:120],
                        total[1] if total and total[1] != found[1] else None)


def _days_apart(a: str, b: str) -> int:
    return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days)


def vendor_confirms(vendor: Optional[Mapping[str, float]], end: str, value: float) -> Optional[bool]:
    """
    Whether a second source (Eulerpool's net income per year end, in currency units) has the same figure for the year:
    within its whole-million allowance (eulerpool_mapper.allowed_gap); None when it has no figure for the year.
    """
    match = next((e for e in (vendor or {}) if _days_apart(e, end) <= RNS_DATE_TOLERANCE_DAYS), None)
    if match is None or vendor[match] is None:
        return None
    return abs(vendor[match] - value) <= allowed_gap(value, EULERPOOL_MATCH_REL)


def linked_chain(statements: Sequence[RnsStatement], vendor: Optional[Mapping[str, float]] = None
                 ) -> Tuple[List[RnsStatement], Optional[RnsStatement], List[str]]:
    """
    The statements linked year by year from the newest (config RNS_CHAIN_REL), newest first; the first one that
    did not link (None if all did); and the bridged links, described. Of several for one year end, the latest
    announcement is taken. A link is bridged, not broken:
    - a restatement (the year end links, the net income moved over RNS_CHAIN_REL): when the revenue links within
      RNS_CHAIN_REL (the same business) or the second source has the older statement's net income for its year;
    - a gap of one or two years (no announcement read: the year end is the later one's prior year end one or two
      years earlier): only when the second source has the older statement's net income for its year.
    """
    by_end: Dict[str, RnsStatement] = {}
    for s in sorted(statements, key=lambda s: s.announcement_id):
        same = next((e for e in by_end if _days_apart(e, s.period_end) <= RNS_DATE_TOLERANCE_DAYS), None)
        if same is not None:
            del by_end[same]
        by_end[s.period_end] = s
    ordered = [by_end[e] for e in sorted(by_end, reverse=True)]
    if not ordered:
        return [], None, []
    chain, bridged = [ordered[0]], []
    for s in ordered[1:]:
        later = chain[-1]
        allowed = max(RNS_CHAIN_REL * abs(later.net_income[1]), RNS_MATCH_UNITS * max(s.unit, later.unit))
        dates_link = _days_apart(s.period_end, later.prior_end) <= RNS_DATE_TOLERANCE_DAYS
        if dates_link and abs(s.net_income[0] - later.net_income[1]) <= allowed:
            chain.append(s)
            continue
        confirmed = vendor_confirms(vendor, s.period_end, s.net_income[0])
        if dates_link:
            revenue_links = (s.revenue[0] is not None and later.revenue[1] not in (None, 0)
                             and abs(s.revenue[0] - later.revenue[1]) <= RNS_CHAIN_REL * abs(later.revenue[1]))
            if revenue_links or confirmed:
                bridged.append(f"FY{fiscal_year(s.period_end)} restated in the next announcement "
                               f"({s.net_income[0] / 1e6:,.3f}M -> {later.net_income[1] / 1e6:,.3f}M), linked by "
                               + ("its revenue" if revenue_links else "Eulerpool's net income for the year"))
                chain.append(s)
                continue
            return chain, s, bridged
        prior = dt.date.fromisoformat(later.prior_end)
        gap = next((k for k in (1, 2) if _days_apart(s.period_end, _years_before(prior, k).isoformat())
                    <= RNS_DATE_TOLERANCE_DAYS), None)
        if gap is not None and confirmed:
            prior = int(fiscal_year(later.prior_end))
            missing = f"FY{prior}" if gap == 1 else f"FY{prior - 1}-FY{prior}"
            bridged.append(f"{missing} results announcement missing (no announcement read), "
                           f"FY{fiscal_year(s.period_end)} linked by Eulerpool's net income for the year")
            chain.append(s)
            continue
        return chain, s, bridged
    return chain, None, bridged


def _years_before(day: dt.date, years: int) -> dt.date:
    for _ in range(years):
        day = _year_before(day)
    return day


def _years(statements: Sequence[RnsStatement]) -> Dict[str, Dict[str, object]]:
    """Per year end: net income, revenue, unit and the announcement; a later announcement's comparative (the
    restated figure) replaces the year's own, which is kept as first_reported."""
    years: Dict[str, Dict[str, object]] = {}
    for s in sorted(statements, key=lambda s: s.announcement_id):
        totals = s.total or (None, None)
        for end, ni, rev, tot in ((s.prior_end, s.net_income[1], s.revenue[1], totals[1]),
                                  (s.period_end, s.net_income[0], s.revenue[0], totals[0])):
            match = next((e for e in years if abs((dt.date.fromisoformat(e) - dt.date.fromisoformat(end)).days)
                          <= RNS_DATE_TOLERANCE_DAYS), None)
            if match is not None and match != end:
                years[end] = years.pop(match)
            earlier = years.get(end, {})
            years[end] = {"net_income": ni, "revenue": rev, "unit": s.unit, "id": s.announcement_id,
                          "first_reported": earlier.get("first_reported", ni),
                          "totals": tuple(earlier.get("totals", ())) + ((tot,) if tot is not None else ())}
    return years


def rns_history(annual: EdgarAnnualData, statements: Sequence[RnsStatement],
                filed_source: str = "Yahoo Finance's statements",
                vendor: Optional[Mapping[str, float]] = None) -> RnsHistory:
    """
    The announced years before the filed ones, when the announced net income agreed with the filed figure in every
    overlapping year (at least RNS_MIN_OVERLAP_YEARS; within RNS_MATCH_REL or RNS_MATCH_UNITS of the statement's
    unit), or, where they disagreed, when the second source (vendor: Eulerpool's net income per year end, in the
    filings' currency) has the announced figure and not the filed one (two sources against one). The vendor also
    bridges gaps and restatements in the chain (linked_chain). Statements in another currency are left out. Revenue is cut at the first year-to-year move over
    CONTINUITY_RATIO from the earliest filed year back (as the vendor gate); net income is not (it can move tenfold).
    """
    def not_used(reason: str) -> RnsHistory:
        return RnsHistory(notes=(f"History before the filed years: {SOURCE} not used: {reason}",))

    other = [s for s in statements if s.currency and s.currency != annual.currency]
    statements = [s for s in statements if s not in other]
    if not statements:
        return not_used("no consolidated income statement could be read from the company's results announcements"
                        if not other else f"its statements are in {other[0].currency}, the filings' in {annual.currency}")
    statements, broken, bridged = linked_chain(statements, vendor)
    years = _years(statements)
    filed = {row.period_end: row for row in annual.income_statements if row.net_income is not None}
    if not filed:
        return not_used("no filed years to check it against")
    pairs, disagreed, sided = [], [], []
    for end, row in filed.items():
        match = next((e for e in years if abs((dt.date.fromisoformat(e) - dt.date.fromisoformat(end)).days)
                      <= RNS_DATE_TOLERANCE_DAYS), None)
        if match is None:
            continue
        ours, theirs = years[match]["net_income"], row.net_income
        allowed = max(RNS_MATCH_REL * abs(theirs), RNS_MATCH_UNITS * float(years[match]["unit"]))
        pairs.append(end)
        # either of the company's figures for the year: as first reported, or restated in the next announcement
        # the year agrees when any of the company's own readings does: the owners' figure as first reported or as
        # restated, or the statement's total profit for the year (Yahoo may carry the figure incl. minorities)
        if all(abs(value - theirs) > allowed
               for value in (ours, years[match]["first_reported"]) + tuple(years[match]["totals"])):
            if vendor_confirms(vendor, end, ours) and not vendor_confirms(vendor, end, theirs):
                sided.append(f"FY{fiscal_year(end)} {ours / 1e6:,.3f}M announced, {theirs / 1e6:,.3f}M in {filed_source}")
                continue
            disagreed.append(f"FY{fiscal_year(end)} {ours / 1e6:,.3f}M announced, {theirs / 1e6:,.3f}M in {filed_source}")
    checked = (f"within {RNS_MATCH_REL:.0%}, or {RNS_MATCH_UNITS:g} of the statement's rounding unit")
    if len(pairs) < RNS_MIN_OVERLAP_YEARS:
        return not_used(f"its announced years overlap {filed_source} in {len(pairs)} year(s), fewer than "
                        f"{RNS_MIN_OVERLAP_YEARS}")
    if disagreed:
        return not_used(f"its net income did not agree with {filed_source} ({checked}) in every overlapping year: "
                        + "; ".join(disagreed))
    first_filed = min(filed)
    older = sorted((e for e in years if e < first_filed and (dt.date.fromisoformat(first_filed)
                                                              - dt.date.fromisoformat(e)).days > RNS_DATE_TOLERANCE_DAYS),
                   reverse=True)
    if not older:
        return not_used(f"it has no year before FY{fiscal_year(first_filed)}")
    last, cut = filed[first_filed].revenue, None
    rows = []
    for end in older:
        revenue = years[end]["revenue"]
        if cut is None and revenue is not None and revenue > 0:
            if last is not None and last > 0 and max(revenue, last) / min(revenue, last) > CONTINUITY_RATIO:
                cut = end
            else:
                last = revenue
        rows.append(IncomeStatementRow(end, None if (cut is not None or revenue is None) else revenue,
                                       float(years[end]["net_income"]), None))
    overlap = sorted(fiscal_year(e) for e in pairs)
    span = sorted(fiscal_year(r.period_end) for r in rows)
    notes = [f"History before FY{fiscal_year(first_filed)}: {SOURCE} for FY{span[0]}-FY{span[-1]} ({len(span)} years), "
             f"net income checked against {filed_source} in FY{overlap[0]}-FY{overlap[-1]} ({checked}) in every "
             f"overlapping year; a year's figures are from the next year's announcement where it restated them. Revenue "
             f"and net income (attributable to the owners of the parent) only: no balance sheets; {NO_PER_SHARE}"]
    if sided:
        notes.append(f"{SOURCE}: where the announced net income and {filed_source} disagreed, Eulerpool has the "
                     f"announced figure (two sources against one), so the announcements are used: " + "; ".join(sided))
    if bridged:
        notes.append(f"{SOURCE}: links bridged: " + "; ".join(bridged))
    if broken is not None:
        notes.append(f"{SOURCE}: announcements before FY{fiscal_year(statements[-1].period_end)} not used: the next older "
                     f"one read (year ended {broken.period_end}) does not link to it (its year end or net income does not "
                     "match the later announcement's prior-year comparative: a gap, a restatement, or another company "
                     "under the same ticker)")
    if cut is not None:
        notes.append(f"{SOURCE}: revenue not used for FY{fiscal_year(cut)} and earlier (it moves over "
                     f"{CONTINUITY_RATIO:g}x in a year: a reading of the wrong line, not a change of business)")
    return RnsHistory(tuple(rows), {fiscal_year(r.period_end): NO_SHARE_COUNT for r in rows}, tuple(notes))
