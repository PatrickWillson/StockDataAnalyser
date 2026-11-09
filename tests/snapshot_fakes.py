"""
Fakes for the two external boundaries of the application, used by snapshot tests.

Only the outermost I/O is replaced, so all real client code still runs:
  - FakeEODHDSession stands in for the requests.Session inside EODHDClient
  - FakeSecSession stands in for the requests.Session inside EdgarClient (free path)
  - FakeYFinanceModule stands in for the ``yfinance`` module that YFinanceClient and
    FXClient import lazily (``import yfinance as yf``); it serves prices and FX
    rates through the same ``yf.Ticker(...)`` interface
"""

from datetime import date
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd


class FakeResponse:
    def __init__(self, status_code: int, payload: Any = None):
        self.status_code = status_code
        self._payload = payload
        self.text = "" if payload is None else repr(payload)[:200]

    def json(self) -> Any:
        return self._payload


class FakeEODHDSession:
    """Serves fundamentals and dividend-endpoint payloads by URL path."""

    def __init__(self, fundamentals: Dict[str, Dict[str, Any]],
                 dividends: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self._fundamentals = fundamentals
        self._dividends = dividends or {}
        self.requests: List[str] = []

    def get(self, url, params=None, headers=None, timeout=None):
        path = urlparse(url).path
        self.requests.append(path)
        _, api, endpoint, ticker = path.split("/", 3)
        if endpoint == "fundamentals" and ticker in self._fundamentals:
            return FakeResponse(200, self._fundamentals[ticker])
        if endpoint == "div" and ticker in self._dividends:
            return FakeResponse(200, self._dividends[ticker])
        return FakeResponse(404, {"error": "not found"})

    def mount(self, *args, **kwargs):
        pass

    def close(self):
        pass


def _series(values: Optional[Dict[str, float]]) -> pd.Series:
    items = sorted((values or {}).items())
    return pd.Series([v for _, v in items], index=pd.DatetimeIndex([pd.Timestamp(d) for d, _ in items]),
                     dtype=float)


class FakeTicker:
    """The subset of yfinance.Ticker the clients use: fast_info, info, history(), dividends, splits."""

    def __init__(self, last_price: Optional[float], closes: Dict[str, float], currency: Optional[str] = None,
                 info: Optional[Dict[str, Any]] = None, dividends: Optional[Dict[str, float]] = None,
                 splits: Optional[Dict[str, float]] = None, net_income: Optional[Dict[str, float]] = None,
                 statements: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None):
        self.fast_info = {} if last_price is None else {"lastPrice": last_price, "currency": currency}
        self.info = {} if last_price is None else {"regularMarketPrice": last_price}
        self.info.update(info or {})
        self.dividends = _series(dividends)
        self.splits = _series(splits)
        self._closes = closes
        # Annual income statement: one "Net Income" row, a column per fiscal year end (as yfinance)
        items = sorted((net_income or {}).items(), reverse=True)
        self.income_stmt = pd.DataFrame([[v for _, v in items]], index=["Net Income"],
                                        columns=pd.DatetimeIndex([pd.Timestamp(d) for d, _ in items]))
        # Full annual statements when given: {"income" | "balance" | "cashflow": {row: {"YYYY-MM-DD": value}}}
        self.balance_sheet = self.cashflow = pd.DataFrame()
        for key, attr in (("income", "income_stmt"), ("balance", "balance_sheet"), ("cashflow", "cashflow")):
            if statements and statements.get(key):
                rows = statements[key]
                dates = sorted({d for values in rows.values() for d in values}, reverse=True)
                setattr(self, attr, pd.DataFrame([[rows[r].get(d, float("nan")) for d in dates] for r in rows], index=list(rows),
                                                 columns=pd.DatetimeIndex([pd.Timestamp(d) for d in dates])))

    def history(self, start=None, end=None, auto_adjust=False, **kwargs) -> pd.DataFrame:
        # Like yfinance, `end` is exclusive
        rows = {d: c for d, c in sorted(self._closes.items())
                if (start is None or d >= str(start)) and (end is None or d < str(end))}
        index = pd.DatetimeIndex([pd.Timestamp(d) for d in rows])
        return pd.DataFrame({"Close": list(rows.values())}, index=index)


class FakeYFinanceModule:
    """
    Drop-in for the ``yfinance`` module.

    symbols maps a Yahoo symbol (e.g. "AAPL", "YU.L", "EURUSD=X") to
    {"last": float, "currency": str, "closes": {"YYYY-MM-DD": float}} and optionally "info" (extra
    Ticker.info keys), "dividends" and "splits" ({"YYYY-MM-DD": value}); currency is the quote
    currency as Yahoo reports it (e.g. "USD", "GBp" for pence), "net_income" ({"YYYY-MM-DD": value},
    the annual income statement) or "statements" (full annual statements, FakeTicker). Unknown symbols behave like yfinance for a missing ticker: no price
    and an empty history. search maps a query to yfinance.Search quotes ({"symbol", "exchange",
    "longname"}).
    """

    __version__ = "fake"

    def __init__(self, symbols: Dict[str, Dict[str, Any]], search: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self._symbols = symbols
        self._search = search or {}
        self.requested: List[str] = []

    def Search(self, query: str, max_results: int = 10, news_count: int = 0):  # noqa: N802 (mirrors yfinance API)
        found = SimpleNamespace(quotes=list(self._search.get(query, []))[:max_results])
        return found

    def Ticker(self, symbol: str) -> FakeTicker:  # noqa: N802 (mirrors yfinance API)
        self.requested.append(symbol)
        entry = self._symbols.get(symbol, {})
        return FakeTicker(entry.get("last"), entry.get("closes", {}), entry.get("currency"),
                          entry.get("info"), entry.get("dividends"), entry.get("splits"), entry.get("net_income"),
                          entry.get("statements"))


class FakeSecSession:
    """
    Serves the SEC ticker index, companyfacts and submissions for {ticker: (cik, companyfacts, submissions)};
    the ticker is the company's US trading symbol (a foreign filer's US listing, e.g. "SAP").
    """

    def __init__(self, companies: Dict[str, Any]):
        self._index = {str(i): {"cik_str": int(cik), "ticker": ticker, "title": ticker}
                       for i, (ticker, (cik, _, _)) in enumerate(companies.items())}
        self._by_cik = {cik: (facts, submissions) for cik, facts, submissions in companies.values()}
        self.requests: List[Any] = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.requests.append((url, (headers or {}).get("User-Agent")))
        if url.endswith("/files/company_tickers.json"):
            return FakeResponse(200, self._index)
        for cik, (facts, submissions) in self._by_cik.items():
            if url.endswith(f"companyfacts/CIK{cik}.json"):
                return FakeResponse(200, facts)
            if url.endswith(f"submissions/CIK{cik}.json"):
                return FakeResponse(200, submissions)
        return FakeResponse(404, {"error": "not found"})

    def mount(self, *args, **kwargs):
        pass

    def close(self):
        pass


def closes_around(dates: List[str], price_for, days_before: int = 4) -> Dict[str, float]:
    """
    Daily closes on each given date and the few days before it, so the clients'
    7-day fiscal-year-end lookback always finds a value.

    Args:
        dates: Anchor dates (YYYY-MM-DD)
        price_for: Function anchor_date -> close price
        days_before: How many earlier days to fill
    """
    closes = {}
    for anchor in dates:
        anchor_date = date.fromisoformat(anchor)
        for offset in range(days_before + 1):
            day = date.fromordinal(anchor_date.toordinal() - offset)
            closes[day.isoformat()] = round(price_for(anchor), 4)
    return closes
