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
    """Rows by vertical position (words whose centres are within 0.6 x the median word height), left to right."""
    if not words:
        return []
    mh = _median_height(words)
    rows: List[Row] = []
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


def table_html(rows: List[Row], made_up_date: str) -> Optional[Tuple[str, List[float]]]:
    """
    The statement as a table for parse_statement: the heading (with the register's year end, more reliable than OCR's
    '21st' for '31st'), the first row naming two or more years as the year columns, and per row the figure
    right-aligned nearest each year column. Returns (html, confidences of the figures placed) or None.
    """
    start = next((i for i, r in enumerate(rows) if HEAD.search(r.text)), None)
    if start is None:
        return None
    day = dt.date.fromisoformat(made_up_date)
    heading = f"{rows[start].text} for the year ended {day.day} {day:%B %Y}"
    cols: Optional[List[Tuple[int, int]]] = None
    html, confs = [f"<p>{heading}</p><table>"], []
    for r in rows[start + 1:start + 60]:
        years = [(int(w.t), w.x + w.w) for w in r.words if re.fullmatch(r"(19|20)\d\d", w.t)]
        if cols is None and len(years) >= 2:
            cols = years
            html.append("<tr>" + "".join(f"<td>{y}</td>" for y, _ in cols) + "</tr>")
            continue
        figs = [w for w in r.words if NUM.match(w.t)]
        if cols is not None and _unreadable(r.words, cols):
            # a figure misread ('$88' for 888) or uncertain: the line is shown without figures, so never taken
            html.append(f"<tr><td>{' '.join(w.t for w in r.words if w not in figs)} [unreadable]</td></tr>")
            continue
        if not figs or cols is None:
            html.append(f"<tr><td>{r.text}</td></tr>")
            continue
        label = " ".join(w.t for w in r.words if w not in figs)
        width = max(edge for _, edge in cols)
        cells = []
        for _, edge in cols:
            near = min(figs, key=lambda w: abs(w.x + w.w - edge))
            if abs(near.x + near.w - edge) < 0.12 * width:
                cells.append(near.t)
                confs.append(near.c)
        html.append(f"<tr><td>{label}</td>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    html.append("</table>")
    return "".join(html), confs


def _unreadable(words: List[Word], cols: List[Tuple[int, int]]) -> bool:
    """A token in a figure column that is not a clean figure ('$88', '1,0O6') or below OCR_MIN_FIGURE_CONFIDENCE."""
    width = max(edge for _, edge in cols)
    for w in words:
        in_column = any(abs(w.x + w.w - edge) < 0.12 * width for _, edge in cols)
        if in_column and re.search(r"\d|^[-\u2013\u2014]$", w.t) and (not NUM.match(w.t) or w.c < OCR_MIN_FIGURE_CONFIDENCE):
            return True
    return False


def verify(html: str, statement: RnsStatement) -> Tuple[bool, str]:
    """
    Whether the chosen net income reconciles within the statement, in both years (table units, 1 unit of rounding):
    profit before tax + tax = profit for the year where all three lines are there; and the net income ties in:
    net income + minority interests = profit for the year (minorities 0 when none is shown), or, with no profit for
    the year line, net income = profit before tax + tax (- minorities). (passed, which identities held or failed.)
    """
    lines = []
    for cells in rows_of(html):
        label, figures = _split(cells)
        if len(figures) >= 2 and label:
            lines.append((label.lower(), [_figure(f) for f in figures[:2]]))

    def find(pattern, exclude=r"$^"):
        return next((v for lab, v in lines if re.search(pattern, lab) and not re.search(exclude, lab)), None)

    pbt = find(r"(profit|loss).*before tax")
    tax = find(r"^(income )?tax(ation)?\b|^tax(ation)? on (profit|loss)|^taxation", r"before tax")
    pfy = find(r"(profit|loss).*(for the (financial )?(year|period)|after tax)",
               r"attributable|comprehensive|continuing|discontinued|owners|per share")
    nci = find(r"non-controlling|minority")
    unit = statement.unit or 1.0
    ni = [statement.net_income[0] / unit, statement.net_income[1] / unit]
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
