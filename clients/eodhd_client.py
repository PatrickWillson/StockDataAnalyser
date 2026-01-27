"""
EODHD API Client

Fetches financial data from EODHD API.
Delegates data processing to FinancialDataProcessor for separation of concerns.
"""

import requests
import sys
import logging
from typing import Dict, Any, Optional, List
from clients.base_client import BaseAPIClient
from clients.fx_client import FXClient
from core.currency_converter import CurrencyConverter
from core.financial_data_processor import FinancialDataProcessor

logger = logging.getLogger(__name__)


class EODHDClient(BaseAPIClient):
    """Client for fetching financial data from EODHD API."""
    
    API_BASE_URL = "https://eodhd.com/api/fundamentals/{ticker}"
    
    def __init__(self, api_key: str, fx_client: Optional[FXClient] = None, debug: bool = False):
        """
        Initialize EODHD client with retry logic.
        
        Args:
            api_key: EODHD API key
            fx_client: Optional FX client for currency conversion (creates one if not provided)
            debug: Enable debug logging (default: False)
        """
        super().__init__(timeout=30, max_retries=3, backoff_factor=1.0)
        self.api_key = api_key
        self.fx_client = fx_client or FXClient()
        self.currency_converter = CurrencyConverter(fx_client=self.fx_client)
        self.debug = debug
        self.processor = FinancialDataProcessor(currency_converter=self.currency_converter, debug=debug)
    
    def _make_eodhd_request(self, ticker: str) -> Dict[str, Any]:
        """
        Make API request to EODHD with error handling.
        
        Args:
            ticker: Stock ticker with exchange suffix
            
        Returns:
            API response as dictionary
            
        Raises:
            SystemExit: On API errors
        """
        url = self.API_BASE_URL.format(ticker=ticker)
        params = {
            'api_token': self.api_key,
            'fmt': 'json'
        }
        
        try:
            response = self._make_request(url, params=params)
            
            # Handle EODHD-specific errors
            if response.status_code == 401:
                logger.error("Authentication failed. Check your EODHD_API_KEY.")
                sys.exit(1)
            elif response.status_code == 429:
                logger.error("Rate limit exceeded. Please wait and try again.")
                sys.exit(1)
            elif response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                sys.exit(1)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during API request: {str(e)}")
            sys.exit(1)
    
    def _fetch_dividend_history(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch dividend history from EODHD Dividend API.
        
        Args:
            ticker: Stock ticker with exchange suffix (e.g., AAPL.US, VOD.LSE)
            
        Returns:
            List of dividend records with date, value, declarationDate, paymentDate, etc.
            Returns None if API call fails (403, 404, etc.)
        """
        url = f"https://eodhd.com/api/div/{ticker}"
        params = {
            'api_token': self.api_key,
            'fmt': 'json'
        }
        
        try:
            response = self._make_request(url, params=params)
            
            # Handle expected failures gracefully (403 = subscription tier, 404 = no data)
            if response.status_code == 403:
                if self.debug:
                    logger.debug("Dividend API returned 403 (requires higher subscription tier)")
                return None
            elif response.status_code == 404:
                if self.debug:
                    logger.debug("Dividend API returned 404 (no dividend data available)")
                return None
            elif response.status_code != 200:
                if self.debug:
                    logger.debug(f"Dividend API failed with status {response.status_code}")
                return None
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                if self.debug:
                    logger.debug(f"Dividend API returned {len(data)} dividend records")
                return data
            else:
                if self.debug:
                    logger.debug("Dividend API returned empty data")
                return None
                
        except Exception as e:
            if self.debug:
                logger.debug(f"Dividend API request failed: {str(e)}")
            return None
    
    def fetch_all_data(self, ticker: str, yf_client: Optional[Any] = None) -> Dict[str, Any]:
        """
        Fetch all required financial data for a ticker.
        
        Args:
            ticker: Stock ticker with exchange suffix (e.g., AAPL.US, VOD.L)
            yf_client: Optional yfinance client for price fetching (primary source)
            
        Returns:
            Standardized dictionary containing:
                - ticker: str
                - exchange: str
                - currency: str
                - price: float
                - ceo_name: str
                - history: Dict[year, financial_data]
                - warnings: List[str]
        """
        warnings = []
        
        logger.info(f"Fetching data for {ticker}...")
        
        # Fetch data from API
        data = self._make_eodhd_request(ticker)
        
        # Save raw API response to file when debug mode is enabled
        if self.debug:
            import json
            debug_file = f"data/{ticker.replace('.', '_')}_raw_api_response.json"
            try:
                with open(debug_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"Raw API response saved to: {debug_file}")
            except Exception as e:
                logger.debug(f"Could not save raw API response: {e}")
        
        # Extract general information
        general = data.get('General', {})
        ticker_code = general.get('Code', ticker.split('.')[0])
        exchange = general.get('Exchange', 'UNKNOWN')
        currency = general.get('CurrencyCode', 'USD')
        ceo_name = self.processor.extract_ceo_name(data)
        
        # Extract financial statement currency
        financials_currency = data.get('Financials', {}).get('Balance_Sheet', {}).get('currency_symbol', 'USD')
        if not financials_currency or financials_currency == '':
            financials_currency = 'USD'
        
        logger.info(f"Stock Currency: {currency}, Financials Currency: {financials_currency}")
        
        # Add note if currencies don't match
        if currency != financials_currency:
            logger.warning(f"Currency Mismatch: Stock trades in {currency}, but financial statements are in {financials_currency}")
        
        # Extract additional company info
        sector = general.get('Sector', 'N/A')
        industry = general.get('Industry', 'N/A')
        employees = general.get('FullTimeEmployees', 0)
        
        logger.info(f"Company: {general.get('Name', 'Unknown')}")
        logger.info(f"Exchange: {exchange}, Currency: {currency}")
        logger.info(f"Sector: {sector}, Industry: {industry}")
        
        # Extract highlights data
        highlights = data.get('Highlights', {})
        dividend_per_share = highlights.get('DividendShare', 0.0)
        dividend_yield = highlights.get('DividendYield', 0.0)
        pe_ratio = highlights.get('PERatio', 0.0)
        book_value_per_share = highlights.get('BookValue', 0.0)
        roe = highlights.get('ReturnOnEquityTTM', 0.0)
        roa = highlights.get('ReturnOnAssetsTTM', 0.0)
        profit_margin = highlights.get('ProfitMargin', 0.0)
        
        # Extract valuation data
        valuation = data.get('Valuation', {})
        # Note: We calculate P/B ratio ourselves instead of using PriceBookMRQ
        # API value is often stale and uses quarterly data vs our annual audited data
        enterprise_value = valuation.get('EnterpriseValue', 0.0)
        
        # Extract ownership data
        shares_stats = data.get('SharesStats', {})
        insider_ownership = shares_stats.get('PercentInsiders', 0.0)
        institutional_ownership = shares_stats.get('PercentInstitutions', 0.0)
        
        # Extract technical data
        technicals = data.get('Technicals', {})
        beta = technicals.get('Beta', 0.0)
        week_52_high = technicals.get('52WeekHigh', 0.0)
        week_52_low = technicals.get('52WeekLow', 0.0)
        
        # Check if delisted
        is_delisted = general.get('IsDelisted', False)
        if is_delisted:
            warnings.append("WARNING: Company is delisted")
            logger.warning("Company is delisted")
        
        # Extract shares outstanding
        shares_outstanding = self.processor.extract_shares_outstanding(data)
        if shares_outstanding == 0.0:
            warnings.append("WARNING: Shares outstanding data unavailable")
            logger.warning("Shares outstanding data unavailable")
        else:
            logger.info(f"Shares Outstanding: {shares_outstanding:,.0f}")
        
        # Extract year-specific shares outstanding for accurate EPS calculation
        shares_by_year = self.processor.extract_shares_by_year(data)
        if shares_by_year:
            logger.info(f"Found year-specific shares data for {len(shares_by_year)} years")
            if self.debug:
                for year in sorted(shares_by_year.keys(), reverse=True)[:3]:
                    logger.debug(f"{year} shares: {shares_by_year[year]:,.0f}")
        
        # Fetch dividend history from Dividend API (primary source)
        logger.info("Fetching dividend history...")
        dividend_api_data = self._fetch_dividend_history(ticker)
        if dividend_api_data:
            logger.info(f"Retrieved {len(dividend_api_data)} dividend records from Dividend API")
        else:
            logger.info("Dividend API unavailable - will use Cash Flow data as fallback")
        
        # Parse financial statements using processor
        logger.info("Parsing financial statements...")
        balance_sheet = self.processor.parse_balance_sheet(data)
        income_statement = self.processor.parse_income_statement(data)
        dividend_history, forward_dividend_rate, is_dividend_amounts, dividend_currency, dividend_sources = self.processor.parse_dividend_history(data, dividend_api_data=dividend_api_data)
        
        # Calculate TTM dividend from Dividend API data
        ttm_dividend, ttm_dividend_payments, ttm_dividend_currency = self.processor.calculate_ttm_dividend(dividend_api_data)
        if ttm_dividend > 0:
            logger.info(f"TTM Dividend: {ttm_dividend:.4f} {ttm_dividend_currency} from {len(ttm_dividend_payments)} payments")
        
        # Convert dividend history to financials currency if needed
        # This is critical for Dividend API data which comes in the stock's trading currency
        if dividend_currency != financials_currency:
            logger.info(f"Converting dividends from {dividend_currency} to {financials_currency}...")
            converted_dividends = self.currency_converter.convert_batch(
                dividend_history, dividend_currency, financials_currency
            )
            
            if converted_dividends != dividend_history:
                # Conversion succeeded
                dividend_history = converted_dividends
                logger.info(f"Historical dividends converted from {dividend_currency} to {financials_currency}")
                if self.debug:
                    for year_key in list(dividend_history.keys())[:3]:  # Show first 3 for debug
                        logger.debug(f"Converted {year_key} dividend: {dividend_history[year_key]:.4f} {financials_currency}")
            else:
                # Conversion failed
                warnings.append(f"WARNING: Could not convert dividends from {dividend_currency} to {financials_currency} - FX rate unavailable")
                logger.warning(f"Could not get FX rate for {dividend_currency}/{financials_currency}")
        
        # Merge financial data with year-specific shares
        logger.info("Merging financial data...")
        history = self.processor.merge_financial_data(balance_sheet, income_statement, 
                                                      dividend_history, shares_outstanding,
                                                      outstanding_shares_by_year=shares_by_year)
        
        # Get current price
        price, price_source, is_from_market_cap = self.processor.get_current_price(data, yf_client=yf_client, ticker=ticker, warnings=warnings)
        
        # Check if price is available
        if price == 0.0 or price_source == 'Missing':
            logger.error("="*70)
            logger.error("Both sources failed to provide current price data.")
            logger.error("="*70)
            logger.error("Troubleshooting:")
            logger.error("1. EODHD API: Price not available in fundamentals endpoint")
            logger.error("   - This can happen for delisted stocks or data gaps")
            logger.error("   - Check if ticker format is correct (e.g., AAPL.US, VOD.LSE)")
            logger.error("2. yfinance Fallback: Failed or unavailable")
            logger.error("   - yfinance may not have data for this ticker")
            logger.error("   - Check if ticker format is correct for yfinance")
            logger.error("   - Verify stock is actively trading")
            logger.error(f"   - Ticker: {ticker}")
            logger.error("3. Possible Solutions:")
            logger.error("   - Verify ticker format matches exchange requirements")
            logger.error("   - Try a different ticker that has EODHD price data")
            logger.error("   - Check if stock is actively trading")
            logger.error("   - Check exchange mapping in yfinance client")
            logger.error("="*70)
            sys.exit(1)
        
        logger.info(f"Current Price: {price} (Source: {price_source})")
        
        # Get most recent EPS for London Fix and P/E calculation
        # Need to find the most recent year with actual financial data (not just dividend data)
        most_recent_eps = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            # Find most recent year with financial data
            for year in sorted_years:
                year_data = history[year]
                # Check if year has actual financial data (not just dividend)
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                    most_recent_eps = year_data.get('eps', 0.0)
                    break
        
        # Determine if London Fix is needed BEFORE applying it
        price_currency = currency
        london_fix_needed = False
        if exchange == "LSE" and most_recent_eps and most_recent_eps > 0 and price > 0:
            pe_ratio = price / most_recent_eps
            if pe_ratio > 500:
                london_fix_needed = True
        
        # Apply London Fix if needed (converts GBp to GBP)
        if london_fix_needed:
            price, fix_applied = self.currency_converter.apply_london_fix(price, most_recent_eps, exchange)
            if fix_applied:
                price_currency = "GBP"  # After London Fix, price is in GBP
                # Also apply London Fix to 52-week high/low
                if week_52_high > 0:
                    week_52_high = week_52_high / 100
                    logger.info(f"London Fix applied to 52-week high: {week_52_high:.2f} GBP")
                if week_52_low > 0:
                    week_52_low = week_52_low / 100
                    logger.info(f"London Fix applied to 52-week low: {week_52_low:.2f} GBP")
        elif exchange == "LSE" and currency == "GBX" and not is_from_market_cap:
            # No London Fix needed, but currency is GBX, so convert to GBP
            # Skip this if price is from MarketCap (already in GBP)
            price = price / 100
            price_currency = "GBP"
            logger.info(f"Converted GBX to GBP: {price:.2f} GBP")
            # Also convert 52-week high/low from GBX to GBP
            if week_52_high > 0:
                week_52_high = week_52_high / 100
                logger.info(f"Converted 52-week high from GBX to GBP: {week_52_high:.2f} GBP")
            if week_52_low > 0:
                week_52_low = week_52_low / 100
                logger.info(f"Converted 52-week low from GBX to GBP: {week_52_low:.2f} GBP")
        elif exchange == "LSE" and is_from_market_cap:
            # Price from MarketCap is already in GBP
            price_currency = "GBP"
            logger.info(f"Price from MarketCap is in GBP: {price:.2f} GBP")
        
        # Convert price to financials currency if they differ
        fx_rate_used = None
        historical_fx_rates = {}  # NEW: Store historical FX rates
        
        if price_currency != financials_currency:
            logger.info(f"Converting price from {price_currency} to {financials_currency}...")
            # Get the FX rate for historical price conversion
            fx_rate_used = self.fx_client.get_rate(price_currency, financials_currency)
            converted_price, success = self.currency_converter.convert(price, price_currency, financials_currency)
            
            if success:
                logger.info(f"Price conversion: {price:.2f} {price_currency} → {converted_price:.2f} {financials_currency}")
                price = converted_price
            else:
                warnings.append(f"WARNING: Could not convert price from {price_currency} to {financials_currency} - FX rate unavailable")
                logger.warning(f"Could not get FX rate for {price_currency}/{financials_currency}")
            
            # NEW: Fetch historical FX rates for historical data conversion
            if history and fx_rate_used:
                logger.info(f"Fetching historical FX rates for {price_currency}/{financials_currency}...")
                
                # Extract fiscal year end dates from history
                fiscal_year_ends = list(history.keys())
                
                if fiscal_year_ends:
                    # Get date range
                    oldest_date = min(fiscal_year_ends)
                    newest_date = max(fiscal_year_ends)
                    
                    logger.info(f"Date range: {oldest_date} to {newest_date}")
                    
                    # Fetch historical rates
                    rate_data = self.fx_client.fetch_historical_rates(
                        price_currency,
                        financials_currency,
                        oldest_date,
                        newest_date
                    )
                    
                    if rate_data:
                        # Match rates to fiscal year ends
                        historical_fx_rates = self.fx_client.match_fiscal_year_end_rates(
                            rate_data,
                            fiscal_year_ends
                        )
                        logger.info(f"Matched historical FX rates to {len(historical_fx_rates)} fiscal year ends")
                    else:
                        logger.warning(f"Could not fetch historical FX rates for {price_currency}/{financials_currency}")
                        warnings.append(f"Historical FX rates unavailable - using current rate for all years")
        
        # Convert Highlights dividends and book value to financials currency
        # Note: For LSE stocks, DividendShare and BookValue in API are already in GBP, not GBX
        highlights_dividend_currency = currency
        if exchange == "LSE" and highlights_dividend_currency == "GBX":
            # DividendShare and BookValue are already in GBP for LSE stocks, not GBX
            # So we don't divide by 100 - just change the currency label
            highlights_dividend_currency = "GBP"
        
        if dividend_per_share and dividend_per_share > 0 and highlights_dividend_currency != financials_currency:
            converted_dividend, success = self.currency_converter.convert(
                dividend_per_share, highlights_dividend_currency, financials_currency
            )
            converted_book_value, _ = self.currency_converter.convert(
                book_value_per_share, highlights_dividend_currency, financials_currency
            )
            
            if success:
                dividend_per_share = converted_dividend
                book_value_per_share = converted_book_value
                logger.info(f"Dividend and Book Value converted from {highlights_dividend_currency} to {financials_currency}")
        
        # Convert forward dividend rate to financials currency
        if forward_dividend_rate:
            fwd_div_currency = currency
            if exchange == "LSE" and fwd_div_currency == "GBX":
                # Forward dividend rate is already in GBP for LSE stocks
                fwd_div_currency = "GBP"
            
            if fwd_div_currency != financials_currency:
                converted_fwd_rate, success = self.currency_converter.convert(
                    forward_dividend_rate, fwd_div_currency, financials_currency
                )
                if success:
                    forward_dividend_rate = converted_fwd_rate
        
        # Convert TTM dividend to financials currency
        if ttm_dividend and ttm_dividend > 0:
            # TTM dividend currency handling (same as forward rate)
            ttm_div_currency = ttm_dividend_currency
            if exchange == "LSE" and ttm_div_currency == "GBX":
                # TTM dividend is already in GBP for LSE stocks
                ttm_div_currency = "GBP"
            
            if ttm_div_currency != financials_currency:
                converted_ttm_div, success = self.currency_converter.convert(
                    ttm_dividend, ttm_div_currency, financials_currency
                )
                if success:
                    ttm_dividend = converted_ttm_div
                    ttm_dividend_currency = financials_currency
                    logger.info(f"TTM dividend converted from {ttm_div_currency} to {financials_currency}: {ttm_dividend:.4f}")
        
        # Recalculate P/E ratio using converted price and most recent EPS
        pe_ratio = 0.0  # Initialize to 0
        if most_recent_eps and most_recent_eps > 0:
            pe_ratio = price / most_recent_eps
            logger.info(f"Recalculated P/E ratio: {pe_ratio:.2f} (Price: {price:.2f} / EPS: {most_recent_eps:.2f})")
        
        # Calculate BVPS and P/B ratio from balance sheet
        calculated_bvps = 0.0
        calculated_pb = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            # Find most recent year with financial data
            most_recent_year = None
            for year in sorted_years:
                year_data = history[year]
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                    most_recent_year = year
                    break
            
            if most_recent_year:
                most_recent_data = history[most_recent_year]
                total_equity = most_recent_data.get('total_equity', 0.0)
                year_shares = most_recent_data.get('shares_outstanding', 0.0)
                
                if year_shares > 0:
                    calculated_bvps = total_equity / year_shares
                    logger.info(f"Calculated BVPS: {calculated_bvps:.2f} (Equity: {total_equity:,.0f} / Shares: {year_shares:,.0f})")
                    
                    # Calculate P/B ratio using our calculated BVPS and converted price
                    if calculated_bvps > 0 and price > 0:
                        calculated_pb = price / calculated_bvps
                        logger.info(f"Calculated P/B ratio: {calculated_pb:.2f} (Price: {price:.2f} / BVPS: {calculated_bvps:.2f})")
        
        # Use calculated P/B ratio (based on audited annual data)
        price_to_book = calculated_pb
        
        # Calculate profitability metrics from annual data
        calculated_roe, calculated_roa, calculated_profit_margin, calc_year = \
            self.processor.calculate_profitability_metrics(history, debug=self.debug)
        
        if calc_year:
            logger.info(f"Calculated profitability metrics from {calc_year}:")
            logger.info(f"  ROE: {calculated_roe*100:.2f}% (Net Income / Total Equity)")
            logger.info(f"  ROA: {calculated_roa*100:.2f}% (Net Income / Total Assets)")
            logger.info(f"  Profit Margin: {calculated_profit_margin*100:.2f}% (Net Income / Revenue)")
        else:
            logger.warning("Could not calculate profitability metrics - no complete annual data")
        
        # Replace API TTM values with calculated annual values
        roe = calculated_roe
        roa = calculated_roa
        profit_margin = calculated_profit_margin
        
        # Add consolidated currency conversion warning if any conversions were performed
        consolidated_warning = self.currency_converter.get_consolidated_warning()
        if consolidated_warning:
            warnings.append(consolidated_warning)
        
        # Cross-validate calculated metrics against API values
        logger.info("Cross-validating metrics...")
        validation_warnings = self._cross_validate_metrics(data, pe_ratio, calculated_bvps, calculated_roe, calculated_roa, calculated_profit_margin)
        warnings.extend(validation_warnings)
        
        # Validate data quality
        logger.info("Validating data quality...")
        self.processor.validate_data_quality(history, warnings)
        
        # Determine overall dividend source for data quality assessment
        dividend_source = 'Unknown'
        if dividend_sources:
            sources = set(dividend_sources.values())
            if len(sources) == 1:
                # All years use same source
                source = sources.pop()
                if source == 'dividend_api':
                    dividend_source = 'Dividend API'
                elif source == 'cash_flow':
                    dividend_source = 'Cash Flow'
                elif source == 'forward_rate':
                    dividend_source = 'Forward Rate'
            else:
                # Mixed sources
                dividend_source = 'Mixed'
        
        # Add data quality warning if Cash Flow dividend differs significantly from Forward Rate
        # This indicates potential timing issues or incomplete data for most recent year
        # Note: Skip this warning if using Dividend API (declared dividends are authoritative)
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_year = sorted_years[0].split('-')[0]
                if most_recent_year in dividend_sources:
                    if dividend_sources[most_recent_year] == 'cash_flow' and forward_dividend_rate and forward_dividend_rate > 0:
                        most_recent_div = history[sorted_years[0]].get('dividend', 0.0)
                        if most_recent_div > 0:
                            diff_pct = abs(most_recent_div - forward_dividend_rate) / forward_dividend_rate * 100
                            if diff_pct > 10:
                                warnings.append(f"Dividend Data Quality: {most_recent_year} Cash Flow shows {most_recent_div:.2f} vs Forward Rate {forward_dividend_rate:.2f} ({diff_pct:.1f}% difference) - most recent year may be incomplete due to payment timing")
        
        if warnings:
            logger.warning(f"Found {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        # Parse quarterly data for TTM calculations
        quarterly_balance_sheet = self.processor.parse_quarterly_balance_sheet(data)
        quarterly_income_statement = self.processor.parse_quarterly_income_statement(data)
        quarterly_data = self.processor.merge_quarterly_data(quarterly_balance_sheet, quarterly_income_statement)
        
        logger.info(f"Data fetch complete for {ticker}")
        
        return {
            'ticker': ticker_code,
            'exchange': exchange,
            'currency': financials_currency,  # Use financials_currency as the unified currency
            'original_stock_currency': currency,  # Keep original for reference
            'financials_currency': financials_currency,
            'dividend_currency': financials_currency,  # Dividends now converted to financials_currency
            'price': price,
            'price_source': price_source,  # NEW: Track price source for data quality assessment
            'dividend_source': dividend_source,  # NEW: Track dividend source for data quality assessment
            'fx_rate_used': fx_rate_used,  # NEW: FX rate used for price conversion (for historical prices)
            'historical_fx_rates': historical_fx_rates,  # NEW: Historical FX rates for date-matched conversion
            'price_currency_before_fx': price_currency,  # NEW: Price currency before FX conversion (GBP for LSE after London Fix)
            'ceo_name': ceo_name,
            'sector': sector,
            'industry': industry,
            'employees': employees,
            'history': history,
            'warnings': warnings,
            'forward_dividend_rate': forward_dividend_rate,
            'is_dividend_amounts': is_dividend_amounts,
            'dividend_sources': dividend_sources,  # NEW: Source indicators for each year
            'ttm_dividend': ttm_dividend,  # NEW: TTM dividend (last 12 months)
            'ttm_dividend_payments': ttm_dividend_payments,  # NEW: List of payments in TTM
            'ttm_dividend_currency': ttm_dividend_currency,  # NEW: Currency of TTM dividend
            # Highlights
            'dividend_per_share': dividend_per_share,
            'dividend_yield': dividend_yield,
            'pe_ratio': pe_ratio,
            'book_value_per_share': book_value_per_share,
            'roe': roe,
            'roa': roa,
            'profit_margin': profit_margin,
            # Valuation
            'price_to_book': price_to_book,
            'enterprise_value': enterprise_value,
            # Ownership
            'insider_ownership': insider_ownership,
            'institutional_ownership': institutional_ownership,
            # Technicals
            'beta': beta,
            'week_52_high': week_52_high,
            'week_52_low': week_52_low,
            # Data quality metadata
            'api_last_update': general.get('UpdatedAt', 'Unknown'),
            # TTM data
            'quarterly_data': quarterly_data
        }

    def _cross_validate_metrics(self, data: Dict[str, Any], calculated_pe: float, calculated_bvps: float, 
                                calculated_roe: float, calculated_roa: float, calculated_profit_margin: float) -> List[str]:
        """
        Cross-validate calculated metrics against API's pre-calculated values.
        Flag significant discrepancies for user review.
        
        Args:
            data: Raw API response data
            calculated_pe: P/E ratio calculated from financials
            calculated_bvps: Book value per share calculated from balance sheet
            calculated_roe: Return on Equity calculated from annual data
            calculated_roa: Return on Assets calculated from annual data
            calculated_profit_margin: Profit Margin calculated from annual data
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check Share Count Consistency
        shares_stats = data.get('SharesStats', {}).get('SharesOutstanding', 0)
        
        # Get balance sheet shares from most recent year
        balance_sheet_shares = 0
        balance_sheet = data.get('Financials', {}).get('Balance_Sheet', {}).get('yearly', {})
        if balance_sheet:
            sorted_years = sorted(balance_sheet.keys(), reverse=True)
            if sorted_years:
                balance_sheet_shares = self.processor.sanitize_value(
                    balance_sheet[sorted_years[0]].get('commonStockSharesOutstanding', 0)
                )
        
        # Get outstandingShares.annual
        outstanding_shares_annual = 0
        outstanding_shares_data = data.get('outstandingShares', {}).get('annual', {})
        if outstanding_shares_data:
            # Get most recent year
            for item in outstanding_shares_data.values():
                if isinstance(item, dict) and 'shares' in item:
                    outstanding_shares_annual = item.get('shares', 0)
                    break  # Get first (most recent)
        
        # Compare share counts if they differ significantly
        if shares_stats > 0 and outstanding_shares_annual > 0:
            diff_pct = abs(outstanding_shares_annual - shares_stats) / shares_stats * 100
            if diff_pct > 5:  # More than 5% difference
                warnings.append(
                    f"[VALIDATION] Share Count: Using {outstanding_shares_annual:,.0f} shares from financial statements. "
                    f"Market data (SharesStats) shows {shares_stats:,.0f} shares ({diff_pct:.1f}% difference). "
                    f"Financial statement shares are used for accurate per-share calculations per Graham methodology."
                )
                logger.info(f"Share count difference: Financial statements {outstanding_shares_annual:,.0f} vs Market data {shares_stats:,.0f}")
        
        # Check P/E ratio
        api_pe = data.get('Highlights', {}).get('PERatio')
        
        # Handle None values - convert to 0 for comparison
        if api_pe is None:
            api_pe = 0
        if calculated_pe is None:
            calculated_pe = 0
        
        if api_pe > 0 and calculated_pe > 0:
            pe_diff_pct = abs(calculated_pe - api_pe) / api_pe * 100
            if pe_diff_pct > 20:  # More than 20% difference
                warnings.append(
                    f"[VALIDATION] P/E Ratio Difference: API shows {api_pe:.2f} (TTM basis), "
                    f"calculated {calculated_pe:.2f} (annual basis) ({pe_diff_pct:.1f}% difference). "
                    f"Using annual EPS from audited financials per Graham methodology."
                )
                logger.info(f"P/E difference: API {api_pe:.2f} (TTM) vs Calculated {calculated_pe:.2f} (Annual)")
        
        # Check Book Value
        api_bvps = data.get('Highlights', {}).get('BookValue', 0)
        
        if api_bvps > 0 and calculated_bvps > 0:
            bvps_diff_pct = abs(calculated_bvps - api_bvps) / api_bvps * 100
            if bvps_diff_pct > 15:  # More than 15% difference
                warnings.append(
                    f"[VALIDATION] Book Value Discrepancy: API shows ${api_bvps:.2f}, "
                    f"calculated ${calculated_bvps:.2f} ({bvps_diff_pct:.1f}% difference). "
                    f"Calculated value subtracts intangibles/goodwill per Graham methodology. "
                    f"API may use different share count or accounting treatment."
                )
                logger.warning(f"Book Value discrepancy detected: API ${api_bvps:.2f} vs Calculated ${calculated_bvps:.2f}")
        
        # Check for stale price data
        last_update = data.get('General', {}).get('UpdatedAt', '')
        if last_update:
            try:
                from datetime import datetime, timedelta, timezone
                # Handle ISO format with or without 'Z'
                update_date_str = last_update.replace('Z', '+00:00')
                update_date = datetime.fromisoformat(update_date_str)
                
                # Ensure both datetimes are timezone-aware for comparison
                if update_date.tzinfo is None:
                    update_date = update_date.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                days_old = (now - update_date).days
                
                if days_old > 7:
                    warnings.append(
                        f"[VALIDATION] API data is {days_old} days old (last update: {last_update[:10]}). "
                        f"Price and market data may be stale."
                    )
                    logger.warning(f"API data is {days_old} days old")
            except Exception as e:
                logger.debug(f"Could not parse UpdatedAt date: {e}")
        
        # Validate profitability metrics
        api_roe = data.get('Highlights', {}).get('ReturnOnEquityTTM')
        api_roa = data.get('Highlights', {}).get('ReturnOnAssetsTTM')
        api_profit_margin = data.get('Highlights', {}).get('ProfitMargin')
        
        # Handle None values
        if api_roe is None:
            api_roe = 0
        if api_roa is None:
            api_roa = 0
        if api_profit_margin is None:
            api_profit_margin = 0
        
        # Validate ROE
        if api_roe > 0 and calculated_roe > 0:
            roe_diff_pct = abs(calculated_roe - api_roe) / api_roe * 100
            if roe_diff_pct > 20:
                warnings.append(
                    f"[VALIDATION] ROE Difference: API shows {api_roe*100:.2f}% (TTM basis), "
                    f"calculated {calculated_roe*100:.2f}% (annual basis) ({roe_diff_pct:.1f}% difference). "
                    f"Using annual data from audited financials per Graham methodology."
                )
                logger.info(f"ROE difference: API {api_roe*100:.2f}% (TTM) vs Calculated {calculated_roe*100:.2f}% (Annual)")
        
        # Validate ROA
        if api_roa > 0 and calculated_roa > 0:
            roa_diff_pct = abs(calculated_roa - api_roa) / api_roa * 100
            if roa_diff_pct > 20:
                warnings.append(
                    f"[VALIDATION] ROA Difference: API shows {api_roa*100:.2f}% (TTM basis), "
                    f"calculated {calculated_roa*100:.2f}% (annual basis) ({roa_diff_pct:.1f}% difference). "
                    f"Using annual data from audited financials per Graham methodology."
                )
                logger.info(f"ROA difference: API {api_roa*100:.2f}% (TTM) vs Calculated {calculated_roa*100:.2f}% (Annual)")
        
        # Validate Profit Margin
        if api_profit_margin > 0 and calculated_profit_margin > 0:
            margin_diff_pct = abs(calculated_profit_margin - api_profit_margin) / api_profit_margin * 100
            if margin_diff_pct > 20:
                warnings.append(
                    f"[VALIDATION] Profit Margin Difference: API shows {api_profit_margin*100:.2f}% (TTM basis), "
                    f"calculated {calculated_profit_margin*100:.2f}% (annual basis) ({margin_diff_pct:.1f}% difference). "
                    f"Using annual data from audited financials per Graham methodology."
                )
                logger.info(f"Profit Margin difference: API {api_profit_margin*100:.2f}% (TTM) vs Calculated {calculated_profit_margin*100:.2f}% (Annual)")
        
        return warnings
