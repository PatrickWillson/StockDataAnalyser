"""
yfinance client for fetching current stock prices.

This module provides the YFinanceClient class which serves as the primary
price source for the Stock Data Analyser application. It translates EODHD
ticker formats to yfinance formats and fetches current prices from Yahoo Finance.
"""

from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta
import logging


class YFinanceClient:
    """
    yfinance client for fetching current stock prices.
    Primary price source for the application.
    
    This client handles the translation of EODHD ticker formats (e.g., "AAPL.US", "YU.LSE")
    to yfinance formats (e.g., "AAPL", "YU.L") using a comprehensive exchange mapping.
    """
    
    # EODHD → yfinance exchange suffix mapping
    # Maps EODHD exchange codes to the corresponding yfinance ticker suffixes
    EXCHANGE_MAPPING = {
        # North America
        'US': '',           # No suffix for US stocks (NYSE, NASDAQ, AMEX)
        'NYSE': '',         # NYSE (alternative code)
        'NASDAQ': '',       # NASDAQ (alternative code)
        'AMEX': '',         # AMEX (alternative code)
        'TO': '.TO',        # Toronto Stock Exchange
        'V': '.V',          # TSX Venture
        'CN': '.CN',        # Canadian Securities Exchange
        'MX': '.MX',        # Mexico
        
        # Europe
        'LSE': '.L',        # London Stock Exchange
        'IL': '.L',         # London International
        'XETRA': '.DE',     # XETRA (Germany)
        'F': '.F',          # Frankfurt
        'SG': '.SG',        # Stuttgart
        'PA': '.PA',        # Paris (Euronext)
        'AS': '.AS',        # Amsterdam (Euronext)
        'BR': '.BR',        # Brussels (Euronext)
        'LS': '.LS',        # Lisbon (Euronext)
        'MC': '.MC',        # Madrid
        'MI': '.MI',        # Milan
        'SW': '.SW',        # Switzerland (SIX)
        'VI': '.VI',        # Vienna
        'IR': '.IR',        # Ireland (Euronext Dublin)
        'ST': '.ST',        # Stockholm
        'OL': '.OL',        # Oslo
        'CO': '.CO',        # Copenhagen
        'HE': '.HE',        # Helsinki
        'AT': '.AT',        # Athens
        'IS': '.IS',        # Istanbul
        'WAR': '.WA',       # Warsaw
        'BUD': '.BD',       # Budapest
        'PR': '.PR',        # Prague
        'MCX': '.ME',       # Moscow
        
        # Asia Pacific
        'AU': '.AX',        # Australia
        'TSE': '.T',        # Tokyo
        'HK': '.HK',        # Hong Kong
        'SHG': '.SS',       # Shanghai
        'SHE': '.SZ',       # Shenzhen
        'NSE': '.NS',       # India NSE
        'BSE': '.BO',       # India BSE
        'KO': '.KS',        # Korea (KOSPI)
        'KQ': '.KQ',        # Korea (KOSDAQ)
        'TW': '.TW',        # Taiwan
        'TWO': '.TWO',      # Taiwan OTC
        'SI': '.SI',        # Singapore
        'BK': '.BK',        # Bangkok
        'JK': '.JK',        # Jakarta
        'KLSE': '.KL',      # Kuala Lumpur
        'NZ': '.NZ',        # New Zealand
        
        # South America & Others
        'SA': '.SA',        # Brazil (B3)
        'BA': '.BA',        # Buenos Aires
        'SN': '.SN',        # Santiago
        'JSE': '.JO',       # Johannesburg
        'SAU': '.SAU',      # Saudi Arabia (Tadawul)
        'TA': '.TA',        # Tel Aviv
    }
    
    def __init__(self, debug: bool = False):
        """
        Initialize yfinance client.
        
        Args:
            debug: Enable debug logging for troubleshooting
        """
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def _parse_ticker(self, ticker: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse EODHD ticker format into symbol and exchange code.
        
        EODHD tickers are in the format "SYMBOL.EXCHANGE" (e.g., "AAPL.US", "YU.LSE").
        
        Args:
            ticker: Ticker in EODHD format (e.g., "AAPL.US", "YU.LSE")
            
        Returns:
            Tuple of (symbol, exchange_code) or (None, None) if parsing fails
            
        Examples:
            "AAPL.US" → ("AAPL", "US")
            "YU.LSE" → ("YU", "LSE")
            "INVALID" → (None, None)
        """
        if not ticker or '.' not in ticker:
            if self.debug:
                self.logger.debug(f"Invalid ticker format: {ticker}")
            return None, None
        
        parts = ticker.split('.')
        if len(parts) != 2:
            if self.debug:
                self.logger.debug(f"Invalid ticker format (expected SYMBOL.EXCHANGE): {ticker}")
            return None, None
        
        symbol, exchange = parts[0], parts[1]
        
        if not symbol or not exchange:
            if self.debug:
                self.logger.debug(f"Empty symbol or exchange in ticker: {ticker}")
            return None, None
        
        return symbol, exchange
    
    def _translate_ticker(self, symbol: str, eodhd_exchange: str) -> Optional[str]:
        """
        Translate EODHD ticker format to yfinance format.
        
        Uses the EXCHANGE_MAPPING to convert EODHD exchange codes to yfinance suffixes.
        For unmapped exchanges, logs a warning and returns the symbol without suffix.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "YU")
            eodhd_exchange: EODHD exchange code (e.g., "US", "LSE")
            
        Returns:
            yfinance ticker format (e.g., "AAPL", "YU.L") or None if translation fails
            
        Examples:
            ("AAPL", "US") → "AAPL"
            ("YU", "LSE") → "YU.L"
            ("VOD", "LSE") → "VOD.L"
            ("SHOP", "TO") → "SHOP.TO"
        """
        if not symbol or not eodhd_exchange:
            if self.debug:
                self.logger.debug("Empty symbol or exchange provided")
            return None
        
        # Check if exchange is in our mapping
        if eodhd_exchange in self.EXCHANGE_MAPPING:
            suffix = self.EXCHANGE_MAPPING[eodhd_exchange]
            yf_ticker = f"{symbol}{suffix}"
            
            if self.debug:
                self.logger.debug(f"Translated {symbol}.{eodhd_exchange} → {yf_ticker}")
            
            return yf_ticker
        else:
            # Unmapped exchange - log warning and attempt without conversion
            warning_msg = f"Unmapped exchange code '{eodhd_exchange}' for ticker {symbol}.{eodhd_exchange}. Attempting without suffix conversion."
            self.logger.warning(warning_msg)
            
            return symbol

    def get_price(self, ticker: str) -> Optional[float]:
        """
        Fetch current price for a ticker using yfinance.
        
        This method:
        1. Parses the EODHD ticker format
        2. Translates it to yfinance format
        3. Fetches the current price using yfinance.Ticker.fast_info
        4. Returns None on any failure (network errors, invalid tickers, missing data)
        
        Args:
            ticker: Ticker in EODHD format (e.g., "AAPL.US", "YU.LSE")
            
        Returns:
            Current price as float, or None if unavailable
            
        Examples:
            "AAPL.US" → 150.25 (current Apple stock price)
            "YU.LSE" → 12.50 (current Yu Group price)
            "INVALID.XX" → None (parsing fails)
        """
        try:
            # Parse EODHD ticker
            symbol, exchange = self._parse_ticker(ticker)
            if not symbol or not exchange:
                if self.debug:
                    self.logger.debug(f"Failed to parse ticker: {ticker}")
                return None
            
            # Translate to yfinance format
            yf_ticker = self._translate_ticker(symbol, exchange)
            if not yf_ticker:
                if self.debug:
                    self.logger.debug(f"Failed to translate ticker: {ticker}")
                return None
            
            if self.debug:
                self.logger.debug(f"Fetching price for {yf_ticker} from yfinance...")
            
            # Import yfinance here to avoid import errors if not installed
            try:
                import yfinance as yf
            except ImportError:
                self.logger.error("yfinance library not installed. Run: pip install yfinance")
                return None
            
            # Fetch price using yfinance
            ticker_obj = yf.Ticker(yf_ticker)
            
            # Use fast_info for better performance
            # Note: yfinance 1.0+ uses 'lastPrice' (camelCase), older versions used 'last_price'
            price = ticker_obj.fast_info.get('lastPrice') or ticker_obj.fast_info.get('last_price')
            
            if price is None:
                if self.debug:
                    self.logger.debug(f"No price data available for {yf_ticker}")
                return None
            
            # Validate price is positive
            if price <= 0:
                if self.debug:
                    self.logger.debug(f"Invalid price ({price}) for {yf_ticker}")
                return None
            
            if self.debug:
                self.logger.debug(f"Successfully fetched price for {yf_ticker}: {price}")
            
            return float(price)
            
        except Exception as e:
            # Catch all errors (network errors, invalid tickers, missing data, etc.)
            if self.debug:
                self.logger.debug(f"Error fetching price for {ticker}: {type(e).__name__}: {str(e)}")
            return None

    def fetch_historical_prices(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[Dict[str, float]]:
        """
        Fetch historical daily closing prices from yfinance.
        
        This method fetches split-adjusted historical prices for Graham-style
        trend analysis. Prices are adjusted for stock splits to ensure
        comparability across time.
        
        Args:
            ticker: Ticker in EODHD format (e.g., 'MSFT.US', 'VOD.LSE')
            start_date: ISO date string (e.g., '2004-01-01')
            end_date: ISO date string (e.g., '2024-12-31')
            
        Returns:
            Dict mapping date strings (YYYY-MM-DD) to closing prices, or None if failed
            Example: {'2024-06-30': 450.12, '2024-06-29': 449.50, ...}
            
        Note:
            - Uses auto_adjust=True to handle stock splits automatically
            - Historical prices are split-adjusted for comparability
            - Returns None on any failure (network errors, invalid tickers, etc.)
        """
        try:
            # Parse EODHD ticker
            symbol, exchange = self._parse_ticker(ticker)
            if not symbol or not exchange:
                if self.debug:
                    self.logger.debug(f"Failed to parse ticker: {ticker}")
                return None
            
            # Translate to yfinance format
            yf_ticker = self._translate_ticker(symbol, exchange)
            if not yf_ticker:
                if self.debug:
                    self.logger.debug(f"Failed to translate ticker: {ticker}")
                return None
            
            if self.debug:
                self.logger.debug(f"Fetching historical prices for {yf_ticker} from {start_date} to {end_date}...")
            
            # Import yfinance
            try:
                import yfinance as yf
            except ImportError:
                self.logger.error("yfinance library not installed. Run: pip install yfinance")
                return None
            
            # Fetch historical data with split adjustment
            ticker_obj = yf.Ticker(yf_ticker)
            hist = ticker_obj.history(start=start_date, end=end_date, auto_adjust=True)
            
            if hist.empty:
                if self.debug:
                    self.logger.debug(f"No historical data available for {yf_ticker}")
                return None
            
            # Convert DataFrame to dict: date_string → close_price
            price_dict = {}
            for date_index, row in hist.iterrows():
                date_str = date_index.strftime('%Y-%m-%d')
                price_dict[date_str] = float(row['Close'])
            
            if self.debug:
                self.logger.debug(f"Fetched {len(price_dict)} days of historical prices for {yf_ticker}")
            
            return price_dict
            
        except Exception as e:
            if self.debug:
                self.logger.debug(f"Error fetching historical prices for {ticker}: {type(e).__name__}: {str(e)}")
            return None
    
    def match_fiscal_year_end_prices(
        self,
        price_data: Dict[str, float],
        fiscal_year_ends: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Match historical prices to fiscal year end dates.
        
        For each fiscal year end date, this method:
        1. Tries to find an exact match in the price data
        2. If no exact match, searches backwards up to 7 days for the last trading day
        3. Returns None if no price found within the 7-day window
        
        This handles cases where fiscal year ends fall on weekends or holidays.
        
        Args:
            price_data: Dict mapping date strings to prices
                Example: {'2024-06-28': 450.12, '2024-06-29': 451.00, ...}
            fiscal_year_ends: List of fiscal year end dates (ISO format)
                Example: ['2024-06-30', '2023-06-30', '2022-06-30']
                
        Returns:
            Dict mapping fiscal year end dates to prices (or None if not found)
            Example: {'2024-06-30': 451.00, '2023-06-30': 340.50, '2022-06-30': None}
            
        Note:
            - Searches backwards (not forwards) to get the last traded price before year end
            - yfinance prices are split-adjusted, so no concern about crossing split boundaries
            - Returns None for years with no data within 7-day window
        """
        result = {}
        
        for fiscal_end in fiscal_year_ends:
            # Try exact match first
            if fiscal_end in price_data:
                result[fiscal_end] = price_data[fiscal_end]
                if self.debug:
                    self.logger.debug(f"{fiscal_end}: Exact match found - {price_data[fiscal_end]:.2f}")
                continue
            
            # Search backwards up to 7 days for last trading day
            try:
                target = datetime.strptime(fiscal_end, '%Y-%m-%d')
                found = False
                
                for days_back in range(1, 8):
                    search_date = (target - timedelta(days=days_back)).strftime('%Y-%m-%d')
                    if search_date in price_data:
                        result[fiscal_end] = price_data[search_date]
                        if self.debug:
                            self.logger.debug(f"{fiscal_end}: Using price from {search_date} ({days_back} days prior) - {price_data[search_date]:.2f}")
                        found = True
                        break
                
                if not found:
                    result[fiscal_end] = None
                    if self.debug:
                        self.logger.debug(f"{fiscal_end}: No price data within 7-day window")
                        
            except ValueError as e:
                # Invalid date format
                result[fiscal_end] = None
                if self.debug:
                    self.logger.debug(f"{fiscal_end}: Invalid date format - {e}")
        
        return result
