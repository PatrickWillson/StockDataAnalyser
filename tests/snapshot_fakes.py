"""
Fakes for the two external boundaries of the application, used by snapshot tests.

Only the outermost I/O is replaced, so all real client code still runs:
  - FakeEODHDSession stands in for the requests.Session inside EODHDClient
  - FakeYFinanceModule stands in for the ``yfinance`` module that YFinanceClient and
    FXClient import lazily (``import yfinance as yf``); it serves prices and FX
    rates through the same ``yf.Ticker(...)`` interface
"""

from datetime import date
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


class FakeTicker:
    """The subset of yfinance.Ticker the clients use: fast_info, info, history()."""

    def __init__(self, last_price: Optional[float], closes: Dict[str, float]):
        self.fast_info = {} if last_price is None else {"lastPrice": last_price}
        self.info = {} if last_price is None else {"regularMarketPrice": last_price}
        self._closes = closes

    def history(self, start=None, end=None, auto_adjust=True, **kwargs) -> pd.DataFrame:
        # Like yfinance, `end` is exclusive
        rows = {d: c for d, c in sorted(self._closes.items())
                if (start is None or d >= str(start)) and (end is None or d < str(end))}
        index = pd.DatetimeIndex([pd.Timestamp(d) for d in rows])
        return pd.DataFrame({"Close": list(rows.values())}, index=index)


class FakeYFinanceModule:
    """
    Drop-in for the ``yfinance`` module.

    symbols maps a Yahoo symbol (e.g. "AAPL", "YU.L", "EURUSD=X") to
    {"last": float, "closes": {"YYYY-MM-DD": float}}. Unknown symbols behave like
    yfinance for a missing ticker: no price and an empty history.
    """

    __version__ = "fake"

    def __init__(self, symbols: Dict[str, Dict[str, Any]]):
        self._symbols = symbols
        self.requested: List[str] = []

    def Ticker(self, symbol: str) -> FakeTicker:  # noqa: N802 (mirrors yfinance API)
        self.requested.append(symbol)
        entry = self._symbols.get(symbol, {})
        return FakeTicker(entry.get("last"), entry.get("closes", {}))


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
