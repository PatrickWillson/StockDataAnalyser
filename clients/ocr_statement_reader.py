"""
The consolidated income statement read by OCR from an image-only accounts PDF (Companies House filings;
claude-output/COMPANIES_HOUSE_OCR_SCOPE_2026-11-12.md). Deterministic: tesseract reads the words and their positions,
fixed rules rebuild the table, and the RNS rules (clients/rns_mapper.parse_statement) take the net income line.

Pure steps (tested on synthetic OCR output, no tesseract needed):
- words_from_tesseract: tesseract's image_to_data dict -> words with position and confidence;
- rows_from_words: words -> rows (by vertical position), a thousands separator read as a space rejoined ('14 476');
- is_statement_page: a page's low-resolution text -> whether it is the group income statement;
- table_html: rows -> a statement table (heading with the register's year end, year columns, one cell per year);
- read_statement: rows -> OcrReading (the statement, its checks).
OCR steps (tesseract via pytesseract, pages rendered by pymupdf; imported only when used): find_statement_page,
read_filing.
"""

import datetime as dt
import re
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from clients.rns_mapper import RnsStatement, _split, _value as _figure, parse_statement, rows_of
from config.companies_house_config import OCR_CONFIRM_DPI, OCR_FIND_DPI, OCR_MIN_FIGURE_CONFIDENCE, OCR_READ_DPI

HEAD = re.compile(r"(consolidated|group)\s+(income\s+statement|profit\s+and\s+loss\s+account|statement\s+of\s+"
                  r"(comprehensive\s+)?income|statement\s+of\s+profit\s+or\s+loss)", re.I)
# loose: survives low-resolution damage ('INCOME STATEME!', 'Consol / lated income statement')
CANDIDATE = re.compile(r"income\s+stat|comprehensive\s+income|profit\s+and\s+loss\s+acc|statement\s+of\s+profit", re.I)
FIGURE = re.compile(r"\(?\d[\d,.]*\d\)?")
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
    arithmetic: Optional[bool] = None            # profit before tax + tax = profit for the year (None: not checkable)
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
    return bool(CANDIDATE.search(top) and not re.search(r"company\s+(income|profit)", top, re.I))


def is_statement_page(text: str) -> bool:
    """Confirmation (higher resolution): the group income statement heading as a line of its own near the top (not a
    sentence or an auditor's paragraph that names it), revenue or turnover, a 'before tax' line and at least 10
    figures of any form (a small company's, or £m with decimals)."""
    top = _top(text)
    heading = any(HEAD.search(line) and len(line) <= 120 and not re.search(r"\b(we|our|the group's|in our opinion)\b", line, re.I)
                  for line in top)
    return bool(heading and not re.search(r"company\s+(income|profit)", "\n".join(top), re.I)
                and re.search(r"revenue|turnover|sales", text, re.I) and re.search(r"before\s+(tax|t\w{1,3}ation)", text, re.I)
                and len(FIGURE.findall(text)) >= 10)


# a year column header: '2025', or a split year '2009/10' (named by the year it ends: 2010)
YEAR_HEADER = re.compile(r"((?:19|20)\d\d)(?:/(\d\d))?")


def _header_year(token: str) -> Optional[int]:
    m = YEAR_HEADER.fullmatch(token)
    if not m:
        return None
    return int(m.group(1)) + 1 if m.group(2) else int(m.group(1))


UNIT_TOKEN = re.compile(r"^[£$€]?['\u2019]?0{3}s?$|^[£$€]m$", re.I)
NOTE_REF = re.compile(r"^\d{1,2}(?:[.,]\s?\d{1,2})*[a-z]?$")


def _is_figure_like(w: Word) -> bool:
    return bool(re.search(r"\d", w.t) or re.fullmatch(r"[-\u2013\u2014]", w.t)) and not UNIT_TOKEN.match(w.t)


def _clean_label(words) -> str:
    """A label without the stray punctuation OCR picks up between words ('Profit for the : year')."""
    return " ".join(t for t in words if not re.fullmatch(r"[^\w£$€()]+", t)).strip()


def figure_columns(rows: List[Row]) -> List[float]:
    """
    The figure columns' right edges: the right edges of figure-like words cluster (within 2 x the median word height,
    at least 4 words) where the columns are; a column of bare note references (mostly '3', '4,5') is left out.
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
    return [statistics.median(w.x + w.w for w in c) for c in clusters
            if len(c) >= 4 and sum(bool(NOTE_REF.match(w.t)) for w in c) < 0.6 * len(c)]


def table_html(rows: List[Row], made_up_date: str) -> Optional[Tuple[str, List[float]]]:
    """
    The statement as a table for parse_statement: the heading (with the register's year end, more reliable than OCR's
    '21st' for '31st'), the first row naming two or more years as the header, then per row its label and the figure
    in each figure column (figure_columns: underlying / exceptional / total columns all pass through; the parser takes
    each year's total). Returns (html, confidences of the figures placed) or None.
    """
    start = next((i for i, r in enumerate(rows) if HEAD.search(r.text)), None)
    if start is None:
        return None
    day = dt.date.fromisoformat(made_up_date)
    heading = f"{rows[start].text} for the year ended {day.day} {day:%B %Y}"
    body = rows[start + 1:start + 70]
    year_row = next((i for i, r in enumerate(body) if sum(_header_year(w.t) is not None for w in r.words) >= 2), None)
    if year_row is None:
        return None
    cols = figure_columns(body[year_row + 1:])
    mh = _median_height([w for r in body for w in r.words])
    html, confs, pending = [f"<p>{heading}</p><table>"], [], None
    for k, r in enumerate(body):
        if k < year_row:
            html.append(f"<tr><td>{r.text}</td></tr>")
            continue
        if k == year_row:
            years = [_header_year(w.t) for w in r.words if _header_year(w.t) is not None]
            html.append("<tr>" + "".join(f"<td>{y}</td>" for y in years) + "</tr>")
            continue
        placed: Dict[int, Word] = {}
        for w in r.words:
            if not _is_figure_like(w) or not cols:
                continue
            j = min(range(len(cols)), key=lambda j: abs(w.x + w.w - cols[j]))
            if abs(w.x + w.w - cols[j]) < 1.5 * mh:
                placed[j] = w
        if _unreadable(list(placed.values())):
            # a figure misread ('$88' for 888) or uncertain: the line is shown without figures, so never taken
            html.append(f"<tr><td>{' '.join(w.t for w in r.words if w not in placed.values())} [unreadable]</td></tr>")
            continue
        label = _clean_label(w.t for w in r.words if w not in placed.values())
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


def _unreadable(placed: List[Word]) -> bool:
    """A word in a figure column that is not a clean figure ('$88', '1,0O6') or is below OCR_MIN_FIGURE_CONFIDENCE."""
    return any(not NUM.match(w.t) or w.c < OCR_MIN_FIGURE_CONFIDENCE for w in placed)


def verify(html: str, statement: RnsStatement) -> Tuple[bool, str]:
    """
    Whether the chosen net income reconciles within the statement, in both years (table units, 1 unit of rounding):
    profit before tax + tax = profit for the year where all three lines are there; and the net income ties in:
    net income + minority interests = profit for the year (minorities 0 when none is shown), or, with no profit for
    the year line, net income = profit before tax + tax (- minorities). (passed, which identities held or failed.)
    """
    rows = []
    for cells in rows_of(html):
        label, figures = _split(cells)
        if len(figures) % 2 and re.fullmatch(r"\d{1,2}", figures[0]):
            figures = figures[1:]                      # a note reference, as the parser drops it
        rows.append((label, figures))
    header = next((f for lab, f in rows if f and all(re.fullmatch(r"(19|20)\d\d", x) for x in f)), [])
    widths = [len(f) for lab, f in rows if lab and len(f) >= 2]
    width = max(set(widths), key=widths.count) if widths else 2
    years = [int(y) for y in header]
    if len(years) == width and len(set(years)) >= 2:          # the parser's choice: each year's last column
        top = sorted(set(years), reverse=True)
        picks = (max(i for i, y in enumerate(years) if y == top[0]), max(i for i, y in enumerate(years) if y == top[1]))
    else:
        picks = (0, 1) if width == 2 else (width // 2 - 1, width - 1)
    lines = []
    for label, figures in rows:
        if len(figures) == width and label:
            lines.append((label.lower(), [_figure(figures[picks[0]]), _figure(figures[picks[1]])]))
        elif len(figures) == 2 and label:
            # a two-figure line under a wider table (an attribution list: owners | minorities) is current | prior
            lines.append((label.lower(), [_figure(figures[0]), _figure(figures[1])]))

    def find(pattern, exclude=r"$^"):
        return next((v for lab, v in lines if re.search(pattern, lab) and not re.search(exclude, lab)), None)

    pbt = find(r"(profit|loss).*before tax")
    tax = find(r"^(income )?tax(ation)?\b|^tax(ation)? on (profit|loss)|^taxation", r"before tax")
    pfy = find(r"(profit|loss).*(for the (financial )?(year|period)|after tax)",
               r"attributable|comprehensive|continuing|discontinued|owners|per share")
    unit = statement.unit or 1.0
    ni = [statement.net_income[0] / unit, statement.net_income[1] / unit]
    # the minorities beside the chosen figure: the nearest such line after it in the same attribution list (not the
    # total comprehensive income list's, ALU 2010: 10 there, 6 beside the profit)
    at = next((i for i, (lab, v) in enumerate(lines) if all(abs(a - b) <= 1 for a, b in zip(v, ni))), None)
    nci = None
    if at is not None:
        nci = next((v for lab, v in lines[at + 1:at + 4] if re.search(r"non-controlling|minority", lab)), None)
    held, failed = [], []

    def check(name, left, right):
        ok = all(abs(a - b) <= 1 for a, b in zip(left, right))
        (held if ok else failed).append(name)
        return ok

    if pbt and tax and pfy:
        check("profit before tax + tax = profit for the year", [a + b for a, b in zip(pbt, tax)], pfy)
    minorities = nci or [0.0, 0.0]
    if pfy:
        tied = check("net income + minorities = profit for the year", [a + b for a, b in zip(ni, minorities)], pfy)
    elif pbt and tax:
        tied = check("net income = profit before tax + tax - minorities",
                     ni, [a + b - m for a, b, m in zip(pbt, tax, minorities)])
    else:
        tied = False
        failed.append("no profit for the year or profit before tax and tax lines to tie the net income to")
    passed = tied and not failed
    return passed, ("held: " + "; ".join(held) if held else "") + (" failed: " + "; ".join(failed) if failed else "")


def _value(token: str) -> float:
    token = token.strip()
    if re.fullmatch(r"[-–—]", token):
        return 0.0
    return (-1 if token.startswith("(") else 1) * float(re.sub(r"[(),]", "", token))


def arithmetic_ok(html: str) -> Optional[bool]:
    """Profit before tax + tax = profit for the year (the owners' line when there is no plain one), current column;
    None when a line is missing."""
    cells = re.findall(r"<tr><td>([^<]*)</td><td>([^<]*)</td>", html)
    pbt = next((_value(v) for lab, v in cells if re.search(r"(profit|loss).*before tax", lab, re.I)), None)
    tax = next((_value(v) for lab, v in cells
                if re.fullmatch(r"(income )?tax(ation)?( expense| charge| credit)?(.*)", lab.strip(), re.I)
                or re.match(r"tax(ation)? on (profit|loss)", lab, re.I)), None)
    pat = next((_value(v) for lab, v in cells if re.search(r"(profit|loss).*(for the (financial )?year|after tax)", lab, re.I)
                and not re.search(r"attributable|comprehensive|continuing", lab, re.I)), None)
    if pat is None:
        pat = next((_value(v) for lab, v in cells if re.search(r"owners|equity holders|parent company", lab, re.I)
                    and not re.search(r"comprehensive|non-controlling", lab, re.I)), None)
    if None in (pbt, tax, pat):
        return None
    return abs(pbt + tax - pat) <= 1


def read_statement(rows: List[Row], made_up_date: str) -> OcrReading:
    """The statement on a page's rows, with its checks."""
    table = table_html(rows, made_up_date)
    if table is None:
        return OcrReading(None, notes=("no statement heading on the page",))
    html, confs = table
    statement = parse_statement(html, 0)
    if statement is None:
        return OcrReading(None, html, min(confs) if confs else None, arithmetic_ok(html), ("statement not read",))
    passed, checks = verify(html, statement)
    return OcrReading(statement, html, min(confs) if confs else None, arithmetic_ok(html), (checks,), passed)


# --- OCR (tesseract, pymupdf): imported only when used -----------------------------------------------------------
def _render(page, dpi: int):
    import pymupdf
    from PIL import Image
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    return Image.frombytes("L", (pix.width, pix.height), pix.samples)


def find_statement_page(doc) -> Optional[int]:
    """The index of the group income statement page, or None: every page at OCR_FIND_DPI for candidates
    (is_candidate_page), candidates re-read at OCR_CONFIRM_DPI to confirm (is_statement_page)."""
    import pytesseract
    for i, page in enumerate(doc):
        if is_candidate_page(pytesseract.image_to_string(_render(page, OCR_FIND_DPI))) \
                and is_statement_page(pytesseract.image_to_string(_render(page, OCR_CONFIRM_DPI))):
            return i
    return None


def page_rows(page, dpi: int = OCR_READ_DPI) -> List[Row]:
    import pytesseract
    data = pytesseract.image_to_data(_render(page, dpi), config="--psm 6", output_type=pytesseract.Output.DICT)
    return rows_from_words(words_from_tesseract(data))


def read_filing(pdf_path: str, made_up_date: str) -> Tuple[Optional[int], OcrReading]:
    """(the statement page index or None, the reading) for one filed accounts PDF."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    index = find_statement_page(doc)
    if index is None:
        return None, OcrReading(None, notes=("group income statement page not found",))
    return index, read_statement(page_rows(doc[index]), made_up_date)


def page_dpi(pdf_path: str) -> Optional[int]:
    """The scan resolution of the first page (image width over page width), for reporting."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    images: Dict = doc[0].get_images()
    return round(images[0][2] / (doc[0].rect.width / 72)) if images else None
