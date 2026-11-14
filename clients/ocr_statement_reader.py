"""
The consolidated income statement read by OCR from an image-only accounts PDF (Companies House filings;
claude-output/COMPANIES_HOUSE_OCR_SCOPE_2026-11-12.md). Deterministic: tesseract reads the words and their positions,
fixed rules rebuild the table, and the RNS rules (clients/rns_mapper.parse_statement) take the net income line.

Pure steps (tested on synthetic OCR output, no tesseract needed):
- words_from_tesseract: tesseract's image_to_data dict -> words with position and confidence;
- rows_from_words: words -> rows (by vertical position), a thousands separator read as a space rejoined ('14 476');
- is_statement_page: a page's low-resolution text -> whether it is the group income statement;
- table_html: rows -> a statement table (heading with the register's year end, year columns, one cell per year);
- read_statement: rows -> OcrReading (the statement, its checks: verify()).
OCR steps (tesseract via pytesseract, pages rendered by pymupdf; imported only when used): find_statement_page,
read_filing.
"""

import datetime as dt
import os
import re
from collections import Counter
import statistics
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from clients.rns_mapper import RnsStatement, _split, _value as _figure, parse_statement, rows_of
from config.companies_house_config import (OCR_CONFIRM_DPI, OCR_FIND_DPI, OCR_MIN_FIGURE_CONFIDENCE, OCR_READ_DPI,
                                           OCR_YEAR_REREAD_DPIS, OCR_FINER_DPIS, OCR_WORKERS)

HEAD = re.compile(r"(consolidated|group)\s+(income\s+statement|profit\s+and\s+loss\s+account|statement\s+of\s+"
                  r"(comprehensive\s+)?income|statement\s+of\s+profit\s+or\s+loss)"
                  r"|statement\s+of\s+consolidated\s+(comprehensive\s+)?(income|profit\s+or\s+loss)", re.I)   # Ortac
# loose: survives low-resolution damage ('INCOME STATEME!', 'Consol / lated income statement')
CANDIDATE = re.compile(r"income\s+stat|comprehensive\s+income|statement\s+of\s+compreh|profit\s+and\s+loss\s+acc|"
                       r"statement\s+of\s+profit", re.I)
# a single company's own statement (accounts that are not a group's: Maven VCT 3), as a whole line
PLAIN_HEADING_LINE = re.compile(r"^(?:the\s+)?(?:income\s+statement|profit\s+and\s+loss\s+account|statement\s+of\s+"
                                r"(?:comprehensive\s+)?income|statement\s+of\s+profit\s+or\s+loss"
                                r"(?:\s+and\s+other\s+comprehensive\s+income)?)[\s.:]*$", re.I)
# the heading as a whole line of its own anywhere on the page: tesseract can read a page's label column first, putting
# the heading far below the top (Samuel Heath 2025); a list item ('• the consolidated income statement;') is not one
HEADING_LINE = re.compile(r"^(?:(?:consolidated|group)\s+(?:income\s+statement|profit\s+and\s+loss\s+account|"
                          r"statement\s+of\s+(?:comprehensive\s+)?income|statement\s+of\s+profit\s+or\s+loss"
                          r"(?:\s+and\s+other\s+comprehensive\s+income)?)"
                          r"|statement\s+of\s+consolidated\s+(?:comprehensive\s+)?(?:income|profit\s+or\s+loss))[\s.:]*$", re.I)
FIGURE = re.compile(r"\(?\d[\d,.]*\d\)?")
DASH_TOKEN = re.compile(r"^[-\u2013\u2014]$")
NUM = re.compile(r"^\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?$|^[-–—]$")


@dataclass(frozen=True)
class Word:
    """One word tesseract read: text, box (pixels), confidence (0-100) and its line (block, paragraph, line)."""
    t: str
    x: int
    y: int
    w: int
    h: int
    c: float
    line: Tuple[int, int, int] = (0, 0, 0)


@dataclass
class Row:
    """A row of the page: its words left to right, and its vertical centre."""
    words: List[Word]
    cy: float = 0.0

    @property
    def text(self) -> str:
        return " ".join(w.t for w in self.words)


@dataclass(frozen=True)
class OcrReading:
    """The statement read from a page (None when unreadable), the table it came from, and the checks."""
    statement: Optional[RnsStatement]
    html: str = ""
    min_confidence: Optional[float] = None
    arithmetic: Optional[bool] = None            # verify()'s profit before tax + tax identity (None: not checkable)
    notes: Tuple[str, ...] = field(default_factory=tuple)
    verified: bool = False                       # the net income reconciles within the statement, both years (verify)

    @property
    def accepted(self) -> Optional[RnsStatement]:
        """The statement, only when its net income reconciled: an OCR figure is never used unchecked."""
        return self.statement if self.verified else None


def words_from_tesseract(data: Mapping[str, List[Any]]) -> List[Word]:
    """Words from pytesseract.image_to_data(..., output_type=DICT), empty ones left out."""
    out = []
    for k, text in enumerate(data.get("text", [])):
        if str(text).strip():
            out.append(Word(str(text).strip(), int(data["left"][k]), int(data["top"][k]), int(data["width"][k]),
                            int(data["height"][k]), float(data["conf"][k]),
                            (int(data.get("block_num", [0] * (k + 1))[k]), int(data.get("par_num", [0] * (k + 1))[k]),
                             int(data.get("line_num", [0] * (k + 1))[k]))))
    return out


def _median_height(words: List[Word]) -> float:
    return statistics.median(w.h for w in words) if words else 0.0


def _rejoin_thousands(words: List[Word], mh: float) -> List[Word]:
    """'14 476' (a thousands separator read as a space: the gap is narrow) -> '14,476'."""
    merged: List[Word] = []
    for w in words:
        if (merged and re.fullmatch(r"\(?\d{1,3}", merged[-1].t) and re.fullmatch(r"\d{3}\)?", w.t)
                and w.x - (merged[-1].x + merged[-1].w) < 0.5 * mh):
            m = merged[-1]
            merged[-1] = Word(f"{m.t},{w.t}", m.x, m.y, w.x + w.w - m.x, m.h, min(m.c, w.c), m.line)
        else:
            merged.append(w)
    return merged


def rows_from_words(words: List[Word]) -> List[Row]:
    """
    Rows as tesseract grouped the words into printed lines (block, paragraph, line), so a slightly tilted page keeps
    each line whole; without line numbers, by vertical position (centres within 0.6 x the median word height).
    Words left to right; rows top to bottom.
    """
    if not words:
        return []
    mh = _median_height(words)
    rows: List[Row] = []
    if any(w.line != (0, 0, 0) for w in words):
        by_line: Dict[Tuple[int, int, int], List[Word]] = {}
        for w in words:
            by_line.setdefault(w.line, []).append(w)
        rows = [Row(ws, statistics.median(w.y + w.h / 2 for w in ws)) for ws in by_line.values()]
        rows.sort(key=lambda r: r.cy)
    else:
        for w in sorted(words, key=lambda w: w.y + w.h / 2):
            cy = w.y + w.h / 2
            if rows and abs(rows[-1].cy - cy) < 0.6 * mh:
                rows[-1].words.append(w)
            else:
                rows.append(Row([w], cy))
    for r in rows:
        r.words = _rejoin_thousands(sorted(r.words, key=lambda w: w.x), mh)
    return rows


def _top(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:15]


def is_candidate_page(text: str) -> bool:
    """First look (low resolution): a heading-like line near the top suggests an income statement; not the parent
    company's own."""
    top = "\n".join(_top(text))
    return bool((CANDIDATE.search(top) or _heading_line(text)) and not re.search(r"company\s+(income|profit)", top, re.I))


def _with_pairs(lines: List[str]) -> List[str]:
    """The lines, then each line joined to the next: a heading wrapped over two lines ('CONSOLIDATED STATEMENT OF' /
    'COMPREHENSIVE INCOME', NAHL 2025)."""
    lines = [_no_stray_marks(line) for line in lines if line.strip()]
    return lines + [f"{a} {b}" for a, b in zip(lines, lines[1:])]


def _no_stray_marks(text: str) -> str:
    """A line without lone punctuation tokens: a ruled line read as '|' ('CONSOLIDATED STATEMENT OF |', NAHL 2025)."""
    return " ".join(t for t in text.split() if not re.fullmatch(r"[^\w£$€()]+", t))


def _heading_line(text: str) -> bool:
    return any(HEADING_LINE.match(line) for line in _with_pairs(text.splitlines()))


def _before_tax(text: str) -> bool:
    """A 'before tax' line, or a profit, loss or return line whose 'tax' wrapped below it ('Profit /(loss) before  29,319',
    Vertu 2025; 'Net return on ordinary activities before' / 'taxation', Maven VCT 3 2025) followed by a taxation line."""
    return bool(re.search(r"before\s+(tax|t\w{1,3}ation)", text, re.I)
                or re.search(r"(?:profit|loss|return)\b[^\n]*?\bbefore\b[^\n]*\n(?:[^\n]*\n)?\s*(?:income\s+)?tax", text, re.I))


def is_statement_page(text: str, single_entity: bool = False) -> bool:
    """Confirmation (higher resolution): the group income statement heading as a line of its own near the top (not a
    sentence or an auditor's paragraph that names it), revenue or turnover (or, without revenue, administrative
    expenses or an operating profit or loss: an exploration company), a 'before tax' line (_before_tax) and at least 10
    figures of any form (a small company's, or £m with decimals); never an auditor's report (its top lines). For a single company's accounts (single_entity: the
    filing is not a group's) a plain heading near the top ('Income Statement') also counts."""
    top = _top(text)
    heading = any(HEAD.search(line) and len(line) <= 120 and not re.search(r"\b(we|our|the group's|in our opinion)\b", line, re.I)
                  for line in _with_pairs(top)) or _heading_line(text) \
        or (single_entity and any(PLAIN_HEADING_LINE.match(line) for line in top))
    # an auditor's report names the statements, sometimes as a short line of its own (Empresaria 2024, two columns)
    return bool(heading and not re.search(r"company\s+(income|profit)|\bauditor", "\n".join(top), re.I)
                and re.search(r"revenue|turnover|sales|administrative\s+expenses|operating\s+(?:profit|loss|activities)",
                              text, re.I)
                and _before_tax(text)
                and len(FIGURE.findall(text)) >= 10)


# a year column header: '2025', or a split year '2009/10' (named by the year it ends: 2010)
YEAR_HEADER = re.compile(r"((?:19|20)\d\d)(?:/(\d\d))?")


# a column headed by its date: '30.06.25' (dotDigital), '30/06/2025'
DATE_HEADER = re.compile(r"(\d{1,2})[./](\d{1,2})[./]((?:19|20)\d\d|\d\d)")


def _header_year(token: str) -> Optional[int]:
    m = YEAR_HEADER.fullmatch(token)
    if m:
        return int(m.group(1)) + 1 if m.group(2) else int(m.group(1))
    m = DATE_HEADER.fullmatch(token)
    if m and 1 <= int(m.group(1)) <= 31 and 1 <= int(m.group(2)) <= 12:
        year = int(m.group(3))
        return year if year > 99 else 2000 + year if year < 70 else 1900 + year
    return None


PLAIN_NOTE = re.compile(r"\d{1,2}(?:,\s?\d{1,2})*[a-z]?")     # a note number before the figures: '5', '4,12', '9a'
UNIT_TOKEN = re.compile(r"^[£$€]?['\u2019]?0{3}s?$|^[£$€]m$", re.I)
NOTE_REF = re.compile(r"^\d{1,2}(?:[.,]\s?\d{1,2})*[a-z]?$")


def _is_figure_like(w: Word) -> bool:
    return bool(re.search(r"\d", w.t) or re.fullmatch(r"[-\u2013\u2014]", w.t)) and not UNIT_TOKEN.match(w.t)


def unit_token(text: str) -> Optional[str]:
    """A header word read as a unit, allowing OCR's confusions: '£m', 'gm', '&m' -> '£m'; '£000', "£'000", '£°000'
    -> '£000', and '£7000' (also $ and €). None for anything else."""
    t = text.strip()
    if re.fullmatch(r"[£&g€$]m", t, re.I):
        return ("$" if t[0] == "$" else "€" if t[0] == "€" else "£") + "m"
    if re.fullmatch(r"[£€$]?['\u2019`°]?0{3}s?|[£€$]70{3}", t):          # '£7000': the apostrophe read as a 7
        return ("$" if t.startswith("$") else "€" if t.startswith("€") else "£") + "000"
    return None


PROFIT_OR_LOSS = re.compile(r"^\(?(?:profit|loss|return)\)?$", re.I)


def _clean_label(words) -> str:
    """A label without the stray punctuation OCR picks up between words ('Profit for the : year'); a '/' between
    profit and loss is kept ('(Loss) / profit for year')."""
    words = list(words)
    kept = [t for k, t in enumerate(words)
            if not re.fullmatch(r"[^\w£$€()]+", t)
            or (t == "/" and 0 < k < len(words) - 1 and PROFIT_OR_LOSS.match(words[k - 1]) and PROFIT_OR_LOSS.match(words[k + 1]))]
    return " ".join(kept).strip()


def figure_columns(rows: List[Row]) -> List[float]:
    """
    The figure columns' right edges: the right edges of figure-like words cluster (within 2 x the median word height,
    at least 4 words) where the columns are; a column of plain note numbers (mostly '3', '4,5'), not the rightmost,
    is left out.
    """
    words = [w for r in rows for w in r.words if _is_figure_like(w)]
    if not words:
        return []
    mh = _median_height(words)
    clusters: List[List[Word]] = []
    for w in sorted(words, key=lambda w: w.x + w.w):
        if clusters and w.x + w.w - (clusters[-1][-1].x + clusters[-1][-1].w) < 2 * mh:
            clusters[-1].append(w)
        else:
            clusters.append([w])
    clusters = [c for c in clusters if len(c) >= 4]
    # dashes left of every column with figures are bullets or a rule (Alumasc 2017's earnings per share lines), not a
    # column; a mostly-nil column between figure columns (exceptional items: '-' but one year) stays
    figured = [k for k, c in enumerate(clusters) if sum(not DASH_TOKEN.match(w.t) for w in c) >= 2]
    clusters = clusters[figured[0]:] if figured else clusters
    # a notes column: mostly plain note numbers ('3', '4,9'), left of the figures; small decimal figures ('12.8' in a
    # £m column, Judges Scientific 2023) also fit a note number, so a column of them is never dropped
    return [statistics.median(w.x + w.w for w in c) for k, c in enumerate(clusters)
            if k == len(clusters) - 1 or sum(bool(PLAIN_NOTE.fullmatch(w.t)) for w in c) < 0.6 * len(c)]


def table_html(rows: List[Row], made_up_date: str) -> Optional[Tuple[str, List[float]]]:
    """
    The statement as a table for parse_statement: the heading (with the register's year end, more reliable than OCR's
    '21st' for '31st'), the first row naming two or more years as the header, then per row its label and the figure
    in each figure column (figure_columns: underlying / exceptional / total columns all pass through; the parser takes
    each year's total). Returns (html, confidences of the figures placed) or None.
    """
    start = next((i for i, r in enumerate(rows) if HEAD.search(r.text)), None)
    wrapped = next((i for i in range(min(20, len(rows) - 1)) if not HEAD.search(rows[i].text)
                    and HEADING_LINE.match(_no_stray_marks(f"{rows[i].text} {rows[i + 1].text}"))), None)
    if wrapped is not None and (start is None or wrapped < start):
        # the heading wrapped over two rows ('Statement of consolidated' / 'comprehensive income', Ortac 2025)
        rows = rows[:wrapped] + [Row(rows[wrapped].words + rows[wrapped + 1].words, rows[wrapped].cy)] + rows[wrapped + 2:]
        start = wrapped
    if start is None:              # a single company's own statement ('Income Statement'), on a page confirmed as one
        start = next((i for i, r in enumerate(rows[:20]) if PLAIN_HEADING_LINE.match(r.text.strip())), None)
    day = dt.date.fromisoformat(made_up_date)
    if start is None:
        # the page was confirmed as the statement (find_statement_page), but this read dropped its large heading
        # (ALU 2017): the statement starts just above the first row naming two years near the top
        first_years = next((i for i, r in enumerate(rows[:20]) if sum(_header_year(w.t) is not None for w in r.words) >= 2),
                           None)
        if first_years is None:
            return None
        start = first_years - 1
        heading = f"Consolidated income statement for the year ended {day.day} {day:%B %Y}"
    else:
        heading = f"{_no_stray_marks(rows[start].text)} for the year ended {day.day} {day:%B %Y}"
    body = rows[start + 1:start + 70]
    year_row = next((i for i, r in enumerate(body) if sum(_header_year(w.t) is not None for w in r.words) >= 2), None)
    first_figures = next((i for i, r in enumerate(body)
                          if sum(bool(NUM.match(w.t)) and not _header_year(w.t) for w in r.words) >= 2), len(body))
    if year_row is None or year_row > first_figures:
        # no two-year row above the figures (a later one heads earnings per share, NAHL 2025): staggered years
        staggered, at = _staggered_years(body, made_up_date)
        if at is not None:
            body, year_row = staggered, at
    if year_row is None or not names_accounts_year([_header_year(w.t) for w in body[year_row].words], made_up_date):
        return None                # no year row, or one for other years than the register's (not this statement)
    cols = figure_columns(body[year_row + 1:])
    mh = _median_height([w for r in body for w in r.words])
    body = _decimal_commas(body, year_row, cols, mh)
    first_figures = next((i for i, r in enumerate(body)
                          if sum(bool(NUM.match(w.t)) and not _header_year(w.t) for w in r.words) >= 2), len(body))
    html, confs, pending = [f"<p>{heading}</p><table>"], [], None
    data_started = False
    for k, r in enumerate(body):
        if k < year_row:
            html.append(f"<tr><td>{r.text}</td></tr>")
            continue
        if k > year_row and not data_started:
            units = [unit_token(w.t) for w in r.words]
            if any(units) and all(u or not _is_figure_like(w) for u, w in zip(units, r.words)):
                # the unit row ('£m £m', read 'gm gm'): normalised so the parser finds the unit
                html.append("<tr><td>" + " ".join(u or w.t for u, w in zip(units, r.words)) + "</td></tr>")
                continue
        if k == year_row:
            years = [_header_year(w.t) for w in r.words if _header_year(w.t) is not None]
            column_years = _column_years(body[:first_figures], cols, mh)
            if column_years is not None:
                years = column_years             # each figure column's own year, from any header row (Microlise 2024)
            elif len(set(years)) < len(years) and len(years) != len(cols):
                return None                      # a repeated year ('2024 2024') over columns not all placed: ambiguous
            html.append("<tr>" + "".join(f"<td>{y}</td>" for y in years) + "</tr>")
            continue
        placed: Dict[int, Word] = {}
        stray = []
        for w in r.words:
            if not _is_figure_like(w) or not cols:
                continue
            j = min(range(len(cols)), key=lambda j: abs(w.x + w.w - cols[j]))
            if abs(w.x + w.w - cols[j]) < 1.5 * mh:
                placed[j] = w
            elif w.x + w.w > min(cols) - 8 * mh and not NOTE_REF.match(w.t):
                stray.append(w)          # a figure-like token in the figure area but in no column
        if stray or _unreadable(list(placed.values()), mh):
            # a figure misread ('$88' for 888) or uncertain: the line is shown without figures, so never taken
            kept = [w.t for w in r.words if w not in placed.values() and w not in stray]
            html.append(f"<tr><td>{' '.join(kept)} [unreadable]</td></tr>")
            continue
        label = _clean_label(w.t for w in r.words if w not in placed.values())
        tail = label.split(" ")[-1] if label else ""
        if placed and _figure(tail) is not None and not PLAIN_NOTE.fullmatch(tail):
            # a figure left in the label (DATA 2024: '73.7' off its column, kept as a note number): the parser would
            # read it as the first figure and swap the years, so the line is shown without figures
            html.append(f"<tr><td>{label} [unreadable]</td></tr>")
            continue
        data_started = data_started or bool(placed)
        if not placed:
            if pending is not None and re.match(r"[a-z]", label):      # a label continued on the next line
                pending = f"{pending} {label}"
                html[-1] = f"<tr><td>{pending}</td></tr>"
            else:
                pending = label
                html.append(f"<tr><td>{label}</td></tr>")
            continue
        if pending is not None and (not re.search(r"[A-Za-z]{3}", label) or re.match(r"[a-z]", label)):
            html.pop()                                                  # 'Profit for the' / 'year  1,580  1,719'
            label = f"{pending} {label}".strip()
        pending = None
        html.append(f"<tr><td>{label}</td>" + "".join(f"<td>{placed[j].t}</td>" for j in sorted(placed)) + "</tr>")
        confs += [w.c for w in placed.values()]
    html.append("</table>")
    return "".join(html), confs


DECIMAL_COMMA = re.compile(r"\(?-?\d{1,3},\d{1,2}\)?")


def _decimal_commas(body: List[Row], year_row: int, cols: List[float], mh: float) -> List[Row]:
    """The rows with a decimal point read as a comma ('(14,9)', Judges Scientific 2023) made a point, when most figures
    below the year row are decimals (£m to one place) and the token sits on a figure column: a comma before one or two
    digits is never a thousands separator there, while in the notes column it lists notes ('4,9'). On a page of whole
    figures nothing changes (such a token stays unreadable)."""
    figures = [w.t for r in body[year_row + 1:] for w in r.words if NUM.match(w.t) and not DASH_TOKEN.match(w.t)]
    if not cols or not figures or sum("." in t for t in figures) <= 0.5 * len(figures):
        return body

    def on_column(w):
        return min(abs(w.x + w.w - c) for c in cols) < 1.5 * mh
    return [Row([Word(w.t.replace(",", "."), w.x, w.y, w.w, w.h, w.c, w.line)
                 if DECIMAL_COMMA.fullmatch(w.t) and on_column(w) else w for w in r.words], r.cy) for r in body]


def _column_years(header: List[Row], cols: List[float], mh: float) -> Optional[List[int]]:
    """The year over each figure column, from the header rows above the first figures: each column takes the year word
    whose right edge is nearest its own (within 3 text heights). Only when there are three or more columns, every one
    gets exactly one year and two or more years are named, or each year word sits over the last column of its group
    (each column then takes the year to its right); else None. (Microlise 2024: '2024 2024' over the first two columns,
    '2024 2023' a line below over the last two; Judges Scientific 2023: '2023' over the third of six, '2022' the sixth.)"""
    if len(cols) < 3:
        return None
    placed: Dict[int, List[int]] = {}
    for r in header:
        for w in r.words:
            year = _header_year(w.t)
            if year is None:
                continue
            j = min(range(len(cols)), key=lambda j: abs(w.x + w.w - cols[j]))
            if abs(w.x + w.w - cols[j]) <= 3 * mh:
                placed.setdefault(j, []).append(year)
    if any(len(v) != 1 for v in placed.values()):
        return None
    if len(placed) != len(cols):
        # each year over the last column of its group ('Adjusted | Adjusting items | Total 2023', Judges Scientific
        # 2023): a column takes the year of the first year word at or to its right; the last must be over the last column
        over = sorted(placed)
        if len(over) < 2 or over[-1] != len(cols) - 1:
            return None
        years = [next(placed[j][0] for j in over if j >= c) for c in range(len(cols))]
    else:
        years = [placed[j][0] for j in range(len(cols))]
    return years if len(set(years)) >= 2 else None


def names_accounts_year(years: List[Optional[int]], made_up_date: str) -> bool:
    """Whether a year row names the accounts' own year (the register's year end); a 52/53-week year ending early in
    January may be headed by the year before ('2015' for the year to 2 January 2016)."""
    end = dt.date.fromisoformat(made_up_date)
    return end.year in years or (end.month == 1 and end.day <= 10 and end.year - 1 in years)


def _staggered_years(body: List[Row], made_up_date: str) -> Tuple[List[Row], Optional[int]]:
    """(body, year row index) with the year words of the header rows before the first row of figures gathered into one
    row, left to right, when no row names two years (NAHL 2025: '2024' a line above '2025 £000'). Only year words over
    a figure column, two or more in distinct columns, including the register's year end; else (body, None)."""
    first = next((i for i, r in enumerate(body) if sum(bool(NUM.match(w.t)) and not _header_year(w.t) for w in r.words) >= 2),
                 len(body))
    mh = _median_height([w for r in body for w in r.words])
    cols = figure_columns(body[first:])
    # column headers sit over the figure columns ('31 March 2024' over its column, RCN 2025); a title's year
    # ('For the year ended 31 December 2025', NAHL 2025) does not
    header = [(i, w) for i, r in enumerate(body[:first]) for w in r.words if _header_year(w.t) is not None
              and cols and min(abs(w.x + w.w - c) for c in cols) <= 3 * mh]
    years = [_header_year(w.t) for _, w in header]
    edges = sorted(w.x + w.w for _, w in header)
    if len(header) < 2 or not names_accounts_year(years, made_up_date) or any(b - a < 3 * mh for a, b in zip(edges, edges[1:])):
        return body, None
    at = header[0][0]
    merged = Row(sorted((w for _, w in header), key=lambda w: w.x), body[at].cy)
    used = {id(w) for _, w in header}
    kept = [Row([w for w in r.words if id(w) not in used], r.cy) for r in body[:first]]
    rows = [r for r in kept[:at] if r.words] + [merged] + [r for r in kept[at:] if r.words] + body[first:]
    return rows, len([r for r in kept[:at] if r.words])


def _unreadable(placed: List[Word], mh: float) -> bool:
    """A word in a figure column that is not a clean figure ('$88', '1,0O6') or is below OCR_MIN_FIGURE_CONFIDENCE. A nil
    dash no wider than the text is tall is exempt from the confidence floor: tesseract scores dashes low (Plexus 2025:
    47), and a misread figure is wider; a wrong nil would still have to pass verify's arithmetic."""
    return any(not NUM.match(w.t) or (w.c < OCR_MIN_FIGURE_CONFIDENCE and not (DASH_TOKEN.match(w.t) and w.w <= mh))
               for w in placed)


def verify(html: str, statement: RnsStatement) -> Tuple[bool, str]:
    """
    Whether the chosen net income reconciles within the statement, in both years (table units; rounding of one step of
    the printed precision: 1 for whole figures, 0.1 for figures to one decimal place):
    profit before tax + tax = profit for the year where all three lines are there; and the net income ties in:
    net income + minority interests = profit for the year (minorities 0 when none is shown), or, with no profit for
    the year line, net income = profit before tax + tax (- minorities); with neither, net income + minorities + other
    comprehensive income = total comprehensive income. (passed, which identities held or failed.)
    """
    rows = []
    for cells in rows_of(html):
        label, figures = _split(cells)
        if len(figures) % 2 and re.fullmatch(r"\d{1,2}", figures[0]):
            figures = figures[1:]                      # a note reference, as the parser drops it
        rows.append((label, figures))
    # the year row: two or more years (not the heading's '... 31 December 2023')
    header = next((f for lab, f in rows if len(f) >= 2 and all(re.fullmatch(r"(19|20)\d\d", x) for x in f)), [])
    widths = [len(f) for lab, f in rows if lab and len(f) >= 2]
    width = max(set(widths), key=widths.count) if widths else 2
    if len(header) > width and len(header) in widths:
        width = len(header)            # a year named for more columns than the commonest line has: as the parser takes it
    years = [int(y) for y in header]
    if len(years) == width and len(set(years)) >= 2:          # the parser's choice: each year's last column
        top = sorted(set(years), reverse=True)
        picks = (max(i for i, y in enumerate(years) if y == top[0]), max(i for i, y in enumerate(years) if y == top[1]))
    else:
        picks = (0, 1) if width == 2 else (width // 2 - 1, width - 1)
    lines = []
    for label, figures in rows:
        label = re.sub(r"^\d{1,2}(?:[.,]\d{1,2})?[a-z]?\s+(?=[A-Za-z])", "", label)   # a note number before it: '8 Taxation'
        if len(figures) == width and label:
            lines.append((label.lower(), [_figure(figures[picks[0]]), _figure(figures[picks[1]])]))
        elif len(figures) == 2 and label:
            # a two-figure line under a wider table (an attribution list: owners | minorities) is current | prior
            lines.append((label.lower(), [_figure(figures[0]), _figure(figures[1])]))

    def find(pattern, exclude=r"$^"):
        return next((v for lab, v in lines if re.search(pattern, lab) and not re.search(exclude, lab)), None)

    # the statutory line ('Profit before tax') before an adjusted one ('Profit before tax, amortisation ... and
    # exceptional charges', Vertu 2011); 'return' for an investment company
    pbt = find(r"^(net )?(\(?(profit|loss|return)\)?/?)+ (on ordinary activities )?before tax(ation)?$") \
        or find(r"(profit|loss|return).*before tax")
    tax = find(r"^(income )?tax(ation)?\b|^tax(ation)? on (profit|loss)|^taxation", r"before tax")
    # profit for the year: the last such line when a discontinued-operations line comes before it (the total)
    pfy_lines = [(i, v) for i, (lab, v) in enumerate(lines)
                 if re.search(r"(profit|loss|return).*(for the (financial )?(year|period)|after tax)", lab)
                 and not re.search(r"attributable|comprehensive|continuing|discontinued|owners|per share", lab)]
    pfy = pfy_lines[0][1] if pfy_lines else None
    # the statement of comprehensive income's totals (not an attribution of them)
    oci = find(r"^(total )?other comprehensive (income|loss|expense|\(loss\)|\(expense\))\S*( for the (financial )?(year|period))?"
               r"( net of tax)?$", r"attributable")
    tci = find(r"^total comprehensive (income|loss|expense|\(loss\)|\(expense\))\S*( for the (financial )?(year|period))?$",
               r"attributable")
    continuing, discontinued = None, None
    for (i, v) in pfy_lines[1:]:
        between = [w for lab, w in lines[pfy_lines[0][0] + 1:i] if "discontinued" in lab]
        if between:
            continuing, discontinued, pfy = pfy_lines[0][1], between[0], v
    unit = statement.unit or 1.0
    ni = [statement.net_income[0] / unit, statement.net_income[1] / unit]
    # rounding: one step of the statement's printed precision (1 for whole figures, 0.1 for £m to one place)
    places = _decimal_places(html)
    step = 10.0 ** -Counter(places).most_common(1)[0][0] if places else 1.0
    tolerance = step + 1e-9
    # the minorities beside the chosen figure: the nearest such line after it in the same attribution list (not the
    # total comprehensive income list's, ALU 2010: 10 there, 6 beside the profit)
    at = next((i for i, (lab, v) in enumerate(lines) if all(abs(a - b) <= tolerance for a, b in zip(v, ni))), None)
    nci = None
    if at is not None:
        nci = next((v for lab, v in lines[at + 1:at + 4] if re.search(r"non-controlling|minority", lab)), None)
    held, failed = [], []

    def check(name, left, right):
        ok = all(abs(a - b) <= tolerance for a, b in zip(left, right))
        (held if ok else failed).append(name)
        return ok

    if continuing is not None:
        # with discontinued operations: profit before tax + tax = the continuing profit, and continuing +
        # discontinued = the total profit for the year
        if pbt and tax:
            check("profit before tax + tax = profit from continuing operations", [a + b for a, b in zip(pbt, tax)],
                  continuing)
        check("continuing + discontinued = profit for the year", [a + b for a, b in zip(continuing, discontinued)], pfy)
    elif pbt and tax and pfy:
        check("profit before tax + tax = profit for the year", [a + b for a, b in zip(pbt, tax)], pfy)
    minorities = nci or [0.0, 0.0]
    # the net income is the profit for the year line itself (no owners' line): tying it to that line compares it with
    # itself and proves nothing, so a real identity must tie it
    ni_is_pfy = pfy is not None and not re.search(r"attributable|owners|equity holders|shareholders|members",
                                                  statement.label, re.I)
    columns = _column_sums(rows, width, years, ni, tolerance)
    if pfy and not ni_is_pfy:
        tied = check("net income + minorities = profit for the year", [a + b for a, b in zip(ni, minorities)], pfy)
    elif ni_is_pfy and (continuing is not None or (pbt and tax)):
        tied = bool(held) and not failed                # profit before tax + tax (and continuing + discontinued) tie it
    elif pbt and tax:
        tied = check("net income = profit before tax + tax - minorities",
                     ni, [a + b - m for a, b, m in zip(pbt, tax, minorities)])
    elif oci and tci:
        # no usable tax line (Braime 2010): the statement of comprehensive income below gives the profit back
        tied = check("net income + minorities + other comprehensive income = total comprehensive income",
                     [a + m + o for a, m, o in zip(ni, minorities, oci)], tci)
    elif columns is not None:
        # before exceptional items + exceptional items = total, each year, on the net income line itself (WJG 2025)
        tied = check("columns of the net income line add to its total", columns[0], columns[1])
    else:
        tied = False
        failed.append("no profit for the year or profit before tax and tax lines to tie the net income to")
    passed = tied and not failed
    return passed, ("held: " + "; ".join(held) if held else "") + (" failed: " + "; ".join(failed) if failed else "")


def _column_sums(rows, width: int, years: List[int], ni: List[float],
                 tolerance: float) -> Optional[Tuple[List[float], List[float]]]:
    """([sum of each year's other columns], [each year's total]) on the net income line of a table with three or more
    columns per year (underlying | exceptional | total), or None."""
    if len(years) == width and len(set(years)) >= 2:
        top = sorted(set(years), reverse=True)[:2]
        groups = [[i for i, y in enumerate(years) if y == t] for t in top]
    elif width % 2 == 0:
        groups = [list(range(width // 2)), list(range(width // 2, width))]
    else:
        return None
    if any(len(g) < 3 for g in groups):
        return None
    for label, figures in rows:
        if len(figures) != width or not label:
            continue
        values = [_figure(f) for f in figures]
        if all(abs(values[g[-1]] - n) <= tolerance for g, n in zip(groups, ni)):
            return [sum(values[i] for i in g[:-1]) for g in groups], [values[g[-1]] for g in groups]
    return None


def _value(token: str) -> float:
    token = token.strip()
    if re.fullmatch(r"[-–—]", token):
        return 0.0
    return (-1 if token.startswith("(") else 1) * float(re.sub(r"[(),]", "", token))


def unit_plausible(html: str, unit: float) -> bool:
    """
    A unit of whole pounds (£, not £'000) is believed only when the statement's figures are of that size: a listed
    company in exact pounds shows figures like 11,119,745. Plain '£' with no figure reaching 100,000 is far more
    likely a '£'000' whose '000 OCR lost (AST 2009: '£ £' over figures like 898 and (10,756), in £'000).
    """
    if unit != 1.0:
        return True
    figures = [abs(_figure(f)) for cells in rows_of(html) for f in _split(cells)[1]
               if not re.fullmatch(r"(19|20)\d\d", f)]
    return bool(figures) and max(figures) >= 100_000


def _decimal_places(html: str) -> List[int]:
    """The decimal places of each figure cell of a statement table (not a row's label cell, dashes or years)."""
    cells = [c for row in re.findall(r"<tr>(.*?)</tr>", html) for c in re.findall(r"<td>([^<]*)</td>", row)[1:]]
    figures = [c for c in cells if NUM.match(c) and not DASH_TOKEN.match(c) and not re.fullmatch(r"(?:19|20)\d\d", c)]
    return [len(c.split(".")[1].rstrip(")")) if "." in c else 0 for c in figures]


def restore_decimals(html: str) -> Tuple[str, int]:
    """A statement most of whose figures (at least 8, over half) carry the same number of decimals (£m to one place), with
    the point restored in a figure OCR read without it ('15' for 1.5, Empresaria 2024): (html, figures restored). Only
    figure cells (not a row's label cell), never a year-like token. A wrong restoration fails verify's reconciliation."""
    places = _decimal_places(html)
    if len(places) < 8 or not any(places):
        return html, 0
    d = Counter(p for p in places if p).most_common(1)[0][0]
    if places.count(d) <= 0.5 * len(places):
        return html, 0
    restored = 0

    def fix_row(row):
        nonlocal restored
        cells = re.findall(r"<td>([^<]*)</td>", row.group(1))
        out = cells[:1]
        for c in cells[1:]:
            digits = re.sub(r"\D", "", c)
            if NUM.match(c) and "." not in c and not DASH_TOKEN.match(c) and not re.fullmatch(r"(?:19|20)\d\d", c) \
                    and len(digits) > d:
                whole = f"{int(digits[:-d]):,}"
                c = c.replace(re.sub(r"[()\-]", "", c), f"{whole}.{digits[-d:]}")
                restored += 1
            out.append(c)
        return "<tr>" + "".join(f"<td>{c}</td>" for c in out) + "</tr>"

    html = re.sub(r"<tr>(.*?)</tr>", fix_row, html)
    return html, restored


def read_statement(rows: List[Row], made_up_date: str) -> OcrReading:
    """The statement on a page's rows, with its checks."""
    table = table_html(rows, made_up_date)
    if table is None:
        return OcrReading(None, notes=("no statement heading on the page",))
    html, confs = table
    html, restored = restore_decimals(html)
    extra = (f"decimal point restored in {restored} figures",) if restored else ()
    statement = parse_statement(html, 0)
    if statement is None:
        return OcrReading(None, html, min(confs) if confs else None, None, ("statement not read",))
    if not unit_plausible(html, statement.unit):
        return OcrReading(statement, html, min(confs) if confs else None, None,
                          ("unit unknown: '£' over figures below 100,000 (a lost '000?)",), False)
    passed, checks = verify(html, statement)
    # the profit before tax identity on its own, for reporting (verify() decides acceptance)
    arithmetic = (True if re.search(r"held:[^|]*profit before tax \+ tax", checks.split(" failed:")[0])
                  else False if re.search(r"failed:.*profit before tax \+ tax", checks) else None)
    return OcrReading(statement, html, min(confs) if confs else None, arithmetic, (checks,) + extra, passed)


# --- OCR (tesseract, pymupdf): imported only when used -----------------------------------------------------------
def _render(page, dpi: int):
    import pymupdf
    from PIL import Image
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    return Image.frombytes("L", (pix.width, pix.height), pix.samples)


def find_statement_page(doc, single_entity: bool = False,
                        read_text: Optional[Callable[[int, int], str]] = None) -> Optional[int]:
    """The index of the group income statement page (or, single_entity, the company's own), or None: pages read at
    OCR_FIND_DPI for candidates (is_candidate_page), candidates re-read at OCR_CONFIRM_DPI to confirm
    (is_statement_page). Pages are read OCR_WORKERS at a time; the page returned is the lowest-numbered one that is a
    candidate and confirms, as a page-by-page search would return. read_text(index, dpi) -> text (tesseract by
    default, one thread per page: OMP_THREAD_LIMIT=1 unless already set)."""
    from concurrent.futures import ThreadPoolExecutor
    if read_text is None:
        import pytesseract
        os.environ.setdefault("OMP_THREAD_LIMIT", "1")

        def read_text(i, dpi):
            return pytesseract.image_to_string(_render(doc[i], dpi))
    with ThreadPoolExecutor(OCR_WORKERS) as pool:
        for start in range(0, len(doc), OCR_WORKERS):
            batch = list(range(start, min(start + OCR_WORKERS, len(doc))))
            first_look = list(pool.map(lambda i: read_text(i, OCR_FIND_DPI), batch))
            candidates = [i for i, text in zip(batch, first_look) if is_candidate_page(text)]
            confirmed = list(pool.map(lambda i: is_statement_page(read_text(i, OCR_CONFIRM_DPI), single_entity), candidates))
            found = [i for i, ok in zip(candidates, confirmed) if ok]
            if found:
                return found[0]
    return None


def page_rows(page, dpi: int = OCR_READ_DPI) -> List[Row]:
    import pytesseract
    data = pytesseract.image_to_data(_render(page, dpi), config="--psm 6", output_type=pytesseract.Output.DICT)
    return rows_from_words(words_from_tesseract(data))


def reread_finer(read_at: Callable[[int], OcrReading], reading: OcrReading) -> OcrReading:
    """A reading that did not reconcile, read again at each of OCR_FINER_DPIS in turn (read_at(dpi)); the first pass that
    reconciles on its own replaces it, noted. When none does, the reading stands (still refused)."""
    if reading.verified:
        return reading
    for dpi in OCR_FINER_DPIS:
        finer = read_at(dpi)
        if finer.verified:
            return replace(finer, notes=finer.notes + (f"read at {dpi} dpi",))
    return reading


def read_filing(pdf_path: str, made_up_date: str, single_entity: bool = False) -> Tuple[Optional[int], OcrReading]:
    """(the statement page index or None, the reading) for one filed accounts PDF; single_entity when the filing is not a
    group's accounts (AccountsFiling.group)."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    index = find_statement_page(doc, single_entity)
    if index is None:
        return None, OcrReading(None, notes=("group income statement page not found",))
    rows = page_rows(doc[index])
    reading = read_statement(rows, made_up_date)
    if reading.statement is None:
        reread = _reread_year_row(doc[index], rows, made_up_date)
        if reread is not None:
            rows = reread
            reading = read_statement(rows, made_up_date)
    if reading.statement is None or reading.notes[:1] == ("unit unknown: '£' over figures below 100,000 (a lost '000?)",):
        unit = _reread_unit_strip(doc[index], rows)
        if unit and unit.endswith(("000", "m")):
            reading = read_statement(_with_unit_row(rows, unit), made_up_date)
    reading = reread_finer(lambda dpi: read_statement(page_rows(doc[index], dpi), made_up_date), reading)
    return index, reading


def _year_and_first_figure_rows(rows: List[Row]) -> Tuple[Optional[int], Optional[int]]:
    year = next((i for i, r in enumerate(rows) if sum(_header_year(w.t) is not None for w in r.words) >= 2), None)
    if year is None:
        return None, None
    first = next((i for i in range(year + 1, len(rows)) if sum(bool(NUM.match(w.t)) for w in rows[i].words) >= 2), None)
    return year, first


def year_row_from_reread(words: List[Word], top: int, made_up_date: str) -> Optional[Row]:
    """A header line re-read on its own (words placed in its strip, which starts at y = top on the page) as the year
    row, when it names two or more years and one is the accounts' own (the register's year end): else None."""
    words = [Word(w.t, w.x, w.y + top, w.w, w.h, w.c, w.line) for w in words]
    years = [y for y in (_header_year(w.t) for w in words) if y is not None]
    if len(years) < 2 or not names_accounts_year(years, made_up_date):
        return None
    return Row(words, sum(w.y + w.h / 2 for w in words) / len(words))


def _reread_year_row(page, rows: List[Row], made_up_date: str) -> Optional[List[Row]]:
    """The rows with the year row re-read when the page read lost it (Empresaria 2024: a shaded band read 'BRE BOBS'):
    each line between the heading and the first row of figures read on its own (tesseract, one line) at each of
    OCR_YEAR_REREAD_DPIS in turn, the first that names the accounts' year taking its place (positions at OCR_READ_DPI). None when there is nothing to re-read or no line gives the years."""
    import pytesseract
    start = next((i for i, r in enumerate(rows) if HEAD.search(r.text) or PLAIN_HEADING_LINE.match(r.text.strip())), None)
    if start is None:
        return None
    first = next((i for i in range(start + 1, len(rows)) if sum(bool(NUM.match(w.t)) for w in rows[i].words) >= 2), None)
    if first is None or any(sum(_header_year(w.t) is not None for w in r.words) >= 2 for r in rows[start + 1:first]):
        return None
    for dpi in OCR_YEAR_REREAD_DPIS:
        image, scale = _render(page, dpi), dpi / OCR_READ_DPI
        for i in range(start + 1, first):
            top = max(0, int((min(w.y for w in rows[i].words) - 8) * scale))
            bottom = min(image.height, int((max(w.y + w.h for w in rows[i].words) + 8) * scale))
            data = pytesseract.image_to_data(image.crop((0, top, image.width, bottom)), config="--psm 7",
                                             output_type=pytesseract.Output.DICT)
            words = [Word(w.t, int(w.x / scale), int(w.y / scale), int(w.w / scale), int(w.h / scale), w.c, w.line)
                     for w in words_from_tesseract(data)]
            row = year_row_from_reread(words, int(top / scale), made_up_date)
            if row is not None:
                return rows[:i] + [row] + rows[i + 1:]
    return None


def _with_unit_row(rows: List[Row], unit: str) -> List[Row]:
    """The rows with a unit row ('£m £m') inserted after the year row (the unit re-read from its strip)."""
    year, _ = _year_and_first_figure_rows(rows)
    if year is None:
        return rows
    row = Row([Word(unit, 0, 0, 0, 0, 100.0)], rows[year].cy + 1)
    return rows[:year + 1] + [row] + rows[year + 1:]


def _reread_unit_strip(page, rows: List[Row]) -> Optional[str]:
    """The unit read from the strip between the year row and the first row of figures on its own (a thick rule under
    a header can turn '£m £m' into 'ee LLL' when the whole page is read)."""
    import pytesseract
    year, first = _year_and_first_figure_rows(rows)
    if year is None or first is None:
        return None
    image = _render(page, OCR_READ_DPI)
    top = int(max(w.y + w.h for w in rows[year].words))
    bottom = int(min(w.y for w in rows[first].words))
    if bottom - top < 10:
        return None
    text = pytesseract.image_to_string(image.crop((0, top, image.width, bottom)), config="--psm 6")
    return next((u for u in (unit_token(t) for t in text.split()) if u), None)


def page_dpi(pdf_path: str) -> Optional[int]:
    """The scan resolution of the first page (image width over page width), for reporting."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    images: Dict = doc[0].get_images()
    return round(images[0][2] / (doc[0].rect.width / 72)) if images else None
