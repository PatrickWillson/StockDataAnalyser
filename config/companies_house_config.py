"""
Companies House: the accounts a UK-incorporated company filed (claude-output/COMPANIES_HOUSE_OCR_SCOPE_2026-11-12.md).

The free public data API (COMPANIES_HOUSE_API_KEY in .env, sent as the basic-auth user name, never logged) lists a
company's filing history; the Document API serves each filing's PDF. Accounts filed on paper or as PDF are image
scans (about 300 dpi from the 2010s, about 200 dpi in the 1990s), read by OCR (clients/ocr_statement_reader.py).
Companies House: "We impose no rules or requirements on how the information on the public register is used".
Rate limit: 600 requests per 5 minutes per key (429 beyond it; repeated breaches can get a key banned).
"""

from typing import Final, Tuple

COMPANIES_HOUSE_API_URL: Final[str] = "https://api.company-information.service.gov.uk"
COMPANIES_HOUSE_USER_AGENT: Final[str] = "StockDataAnalyser research (no-reply@example.invalid)"
COMPANIES_HOUSE_MIN_REQUEST_INTERVAL: Final[float] = 1.0      # seconds: well inside 600 per 5 minutes
COMPANIES_HOUSE_RATE_LIMIT_WAIT: Final[float] = 60.0          # seconds to wait after a 429 before retrying
COMPANIES_HOUSE_CACHE_DIR: Final[str] = "data/cache/companies_house"   # relative to the repository root

# OCR (tesseract): resolutions for finding the statement page and for reading it, and the lowest tesseract word
# confidence (0-100) accepted for a figure that is used
OCR_FIND_DPI: Final[int] = 100          # a quick first look at every page
OCR_CONFIRM_DPI: Final[int] = 200       # candidate pages re-read to confirm the statement
OCR_READ_DPI: Final[int] = 300
OCR_MIN_FIGURE_CONFIDENCE: Final[float] = 60.0
# a lost year row is re-read on its own at each resolution in turn (a 2017 scan's shaded years read only at 250 dpi)
OCR_YEAR_REREAD_DPIS: Final[Tuple[int, ...]] = (300, 250, 200)
# a reading that does not reconcile is read again finer, in turn (RWS 2010: '476' for 14,476 at 300 dpi, right at 400)
OCR_FINER_DPIS: Final[Tuple[int, ...]] = (400, 450)
