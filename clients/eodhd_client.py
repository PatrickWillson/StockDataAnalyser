"""
EODHD API Client

Fetches financial data from EODHD API.
Delegates data processing to FinancialDataProcessor for separation of concerns.
"""

import requests
import sys
from typing import Dict, Any, Optional, List
from clients.base_client import BaseAPIClient
from clients.fx_client import FXClient
from core.financial_data_processor import FinancialDataProcessor


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
        self.debug = debug
        self.processor = FinancialDataProcessor(fx_client=self.fx_client, debug=debug)
    
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
                print(f"[ERROR] Authentication failed. Check your EODHD_API_KEY.")
                sys.exit(1)
            elif response.status_code == 429:
                print(f"[ERROR] Rate limit exceeded. Please wait and try again.")
                sys.exit(1)
            elif response.status_code != 200:
                print(f"[ERROR] API request failed with status {response.status_code}: {response.text}")
                sys.exit(1)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Unexpected error during API request: {str(e)}")
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
                    print(f"[DEBUG] Dividend API returned 403 (requires higher subscription tier)")
                return None
            elif response.status_code == 404:
                if self.debug:
                    print(f"[DEBUG] Dividend API returned 404 (no dividend data available)")
                return None
            elif response.status_code != 200:
                if self.debug:
                    print(f"[DEBUG] Dividend API failed with status {response.status_code}")
                return None
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                if self.debug:
                    print(f"[DEBUG] Dividend API returned {len(data)} dividend records")
                return data
            else:
                if self.debug:
                    print(f"[DEBUG] Dividend API returned empty data")
                return None
                
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Dividend API request failed: {str(e)}")
            return None
    
    def fetch_all_data(self, ticker: str, av_client: Optional[Any] = None) -> Dict[str, Any]:
        """
        Fetch all required financial data for a ticker.
        
        Args:
            ticker: Stock ticker with exchange suffix (e.g., AAPL.US, VOD.L)
            av_client: Optional Alpha Vantage client for price fallback
            
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
        
        print(f"\n[INFO] Fetching data for {ticker}...")
        
        # Fetch data from API
        data = self._make_eodhd_request(ticker)
        
        # Debug: Save raw API response to file
        if self.debug:
            import json
            debug_file = f"data/{ticker.replace('.', '_')}_raw_api_response.json"
            try:
                with open(debug_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"[DEBUG] Raw API response saved to: {debug_file}")
            except Exception as e:
                print(f"[DEBUG] Could not save raw API response: {e}")
        
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
        
        print(f"[INFO] Stock Currency: {currency}, Financials Currency: {financials_currency}")
        
        # Track currency conversion details for consolidated warning
        currency_conversion_details = []
        
        # Add note if currencies don't match
        if currency != financials_currency:
            currency_conversion_details.append(f"Stock trades in {currency}, financials in {financials_currency}")
            print(f"[WARNING] Currency Mismatch: Stock trades in {currency}, but financial statements are in {financials_currency}")
        
        # Extract additional company info
        sector = general.get('Sector', 'N/A')
        industry = general.get('Industry', 'N/A')
        employees = general.get('FullTimeEmployees', 0)
        
        print(f"[INFO] Company: {general.get('Name', 'Unknown')}")
        print(f"[INFO] Exchange: {exchange}, Currency: {currency}")
        print(f"[INFO] Sector: {sector}, Industry: {industry}")
        
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
        price_to_book = valuation.get('PriceBookMRQ', 0.0)
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
            print("[WARNING] Company is delisted")
        
        # Extract shares outstanding
        shares_outstanding = self.processor.extract_shares_outstanding(data)
        if shares_outstanding == 0.0:
            warnings.append("WARNING: Shares outstanding data unavailable")
            print("[WARNING] Shares outstanding data unavailable")
        else:
            print(f"[INFO] Shares Outstanding: {shares_outstanding:,.0f}")
        
        # Extract year-specific shares outstanding for accurate EPS calculation
        shares_by_year = self.processor.extract_shares_by_year(data)
        if shares_by_year:
            print(f"[INFO] Found year-specific shares data for {len(shares_by_year)} years")
            if self.debug:
                for year in sorted(shares_by_year.keys(), reverse=True)[:3]:
                    print(f"[DEBUG] {year} shares: {shares_by_year[year]:,.0f}")
        
        # Fetch dividend history from Dividend API (primary source)
        print("\n[INFO] Fetching dividend history...")
        dividend_api_data = self._fetch_dividend_history(ticker)
        if dividend_api_data:
            print(f"[INFO] Retrieved {len(dividend_api_data)} dividend records from Dividend API")
        else:
            print("[INFO] Dividend API unavailable - will use Cash Flow data as fallback")
        
        # Parse financial statements using processor
        print("\n[INFO] Parsing financial statements...")
        balance_sheet = self.processor.parse_balance_sheet(data)
        income_statement = self.processor.parse_income_statement(data)
        dividend_history, forward_dividend_rate, is_dividend_amounts, dividend_currency, dividend_sources = self.processor.parse_dividend_history(data, dividend_api_data=dividend_api_data)
        
        # Convert dividend history to financials currency if needed
        # This is critical for Dividend API data which comes in the stock's trading currency
        if dividend_currency != financials_currency:
            print(f"[INFO] Converting dividends from {dividend_currency} to {financials_currency}...")
            fx_rate = self.fx_client.get_rate(dividend_currency, financials_currency)
            if fx_rate:
                # Convert all dividend values in history
                for year_key in dividend_history:
                    old_value = dividend_history[year_key]
                    new_value = old_value * fx_rate
                    dividend_history[year_key] = new_value
                    if self.debug:
                        print(f"[DEBUG] Converted {year_key} dividend: {old_value:.4f} {dividend_currency} → {new_value:.4f} {financials_currency}")
                
                print(f"[INFO] Historical dividends converted from {dividend_currency} to {financials_currency} at rate {fx_rate:.4f}")
                currency_conversion_details.append(f"Dividends converted {dividend_currency} → {financials_currency} at rate {fx_rate:.4f}")
            else:
                warnings.append(f"WARNING: Could not convert dividends from {dividend_currency} to {financials_currency} - FX rate unavailable")
                print(f"[WARNING] Could not get FX rate for {dividend_currency}/{financials_currency}")
        
        # Merge financial data with year-specific shares
        print("\n[INFO] Merging financial data...")
        history = self.processor.merge_financial_data(balance_sheet, income_statement, 
                                                      dividend_history, shares_outstanding,
                                                      outstanding_shares_by_year=shares_by_year)
        
        # Get current price
        price, price_source = self.processor.get_current_price(data, av_client=av_client, ticker=ticker, warnings=warnings)
        print(f"\n[INFO] Current Price: {price} (Source: {price_source})")
        
        # Get most recent EPS for London Fix
        most_recent_eps = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_eps = history[sorted_years[0]].get('eps', 0.0)
        
        # Determine if London Fix is needed BEFORE applying it
        price_currency = currency
        london_fix_needed = False
        if exchange == "LSE" and most_recent_eps > 0:
            pe_ratio = price / most_recent_eps
            if pe_ratio > 500:
                london_fix_needed = True
        
        # Apply London Fix if needed (converts GBp to GBP)
        if london_fix_needed:
            price = self.processor.apply_london_fix(price, most_recent_eps, exchange, warnings)
            price_currency = "GBP"  # After London Fix, price is in GBP
            currency_conversion_details.append("London Fix applied (GBp → GBP)")
        elif exchange == "LSE" and currency == "GBX":
            # No London Fix needed, but currency is GBX, so convert to GBP
            price = price / 100
            price_currency = "GBP"
            currency_conversion_details.append("Converted GBX → GBP")
            print(f"[INFO] Converted GBX to GBP: {price:.2f} GBP")
        
        # Convert price to financials currency if they differ
        if price_currency != financials_currency:
            print(f"[INFO] Converting price from {price_currency} to {financials_currency}...")
            fx_rate = self.fx_client.get_rate(price_currency, financials_currency)
            
            if fx_rate:
                converted_price = price * fx_rate
                print(f"[INFO] Price conversion: {price:.2f} {price_currency} × {fx_rate:.4f} = {converted_price:.2f} {financials_currency}")
                price = converted_price
                currency_conversion_details.append(f"Price converted {price_currency} → {financials_currency} at rate {fx_rate:.4f}")
            else:
                warnings.append(f"WARNING: Could not convert price from {price_currency} to {financials_currency} - FX rate unavailable")
                print(f"[WARNING] Could not get FX rate for {price_currency}/{financials_currency}")
        
        # Convert Highlights dividends and book value to financials currency
        # Note: For LSE stocks, DividendShare and BookValue in API are already in GBP, not GBX
        highlights_dividend_currency = currency
        if exchange == "LSE" and highlights_dividend_currency == "GBX":
            # DividendShare and BookValue are already in GBP for LSE stocks, not GBX
            # So we don't divide by 100 - just change the currency label
            highlights_dividend_currency = "GBP"
        
        if dividend_per_share > 0 and highlights_dividend_currency != financials_currency:
            fx_rate = self.fx_client.get_rate(highlights_dividend_currency, financials_currency)
            if fx_rate:
                dividend_per_share = dividend_per_share * fx_rate
                book_value_per_share = book_value_per_share * fx_rate
                print(f"[INFO] Dividend and Book Value converted from {highlights_dividend_currency} to {financials_currency}")
        
        # Convert forward dividend rate to financials currency
        if forward_dividend_rate:
            fwd_div_currency = currency
            if exchange == "LSE" and fwd_div_currency == "GBX":
                # Forward dividend rate is already in GBP for LSE stocks
                fwd_div_currency = "GBP"
            
            if fwd_div_currency != financials_currency:
                fx_rate = self.fx_client.get_rate(fwd_div_currency, financials_currency)
                if fx_rate:
                    forward_dividend_rate = forward_dividend_rate * fx_rate
        
        # Recalculate P/E ratio using converted price and most recent EPS
        if most_recent_eps > 0:
            pe_ratio = price / most_recent_eps
            print(f"[INFO] Recalculated P/E ratio: {pe_ratio:.2f} (Price: {price:.2f} / EPS: {most_recent_eps:.2f})")
        
        # Calculate BVPS from balance sheet for validation
        calculated_bvps = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_year = sorted_years[0]
                most_recent_data = history[most_recent_year]
                total_equity = most_recent_data.get('total_equity', 0.0)
                year_shares = most_recent_data.get('shares_outstanding', 0.0)
                
                if year_shares > 0:
                    calculated_bvps = total_equity / year_shares
                    print(f"[INFO] Calculated BVPS: {calculated_bvps:.2f} (Equity: {total_equity:,.0f} / Shares: {year_shares:,.0f})")
        
        # Add consolidated currency conversion warning if any conversions were performed
        if currency_conversion_details:
            consolidated_warning = "Currency Conversions: " + "; ".join(currency_conversion_details)
            warnings.append(consolidated_warning)
        
        # Cross-validate calculated metrics against API values
        print("\n[INFO] Cross-validating metrics...")
        validation_warnings = self._cross_validate_metrics(data, pe_ratio, calculated_bvps)
        warnings.extend(validation_warnings)
        
        # Validate data quality
        print("\n[INFO] Validating data quality...")
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
            print(f"\n[WARNING] Found {len(warnings)} warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        print(f"\n[SUCCESS] Data fetch complete for {ticker}\n")
        
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
            'ceo_name': ceo_name,
            'sector': sector,
            'industry': industry,
            'employees': employees,
            'history': history,
            'warnings': warnings,
            'forward_dividend_rate': forward_dividend_rate,
            'is_dividend_amounts': is_dividend_amounts,
            'dividend_sources': dividend_sources,  # NEW: Source indicators for each year
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
            'fx_rate_used': fx_rate if price_currency != financials_currency else 1.0
        }

    def _cross_validate_metrics(self, data: Dict[str, Any], calculated_pe: float, calculated_bvps: float) -> List[str]:
        """
        Cross-validate calculated metrics against API's pre-calculated values.
        Flag significant discrepancies for user review.
        
        Args:
            data: Raw API response data
            calculated_pe: P/E ratio calculated from financials
            calculated_bvps: Book value per share calculated from balance sheet
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check P/E ratio
        api_pe = data.get('Highlights', {}).get('PERatio', 0)
        
        if api_pe > 0 and calculated_pe > 0:
            pe_diff_pct = abs(calculated_pe - api_pe) / api_pe * 100
            if pe_diff_pct > 20:  # More than 20% difference
                warnings.append(
                    f"[VALIDATION] P/E Ratio Difference: API shows {api_pe:.2f} (TTM basis), "
                    f"calculated {calculated_pe:.2f} (annual basis) ({pe_diff_pct:.1f}% difference). "
                    f"Using annual EPS from audited financials per Graham methodology."
                )
                print(f"[INFO] P/E difference: API {api_pe:.2f} (TTM) vs Calculated {calculated_pe:.2f} (Annual)")
        
        # Check Book Value
        api_bvps = data.get('Highlights', {}).get('BookValue', 0)
        
        if api_bvps > 0 and calculated_bvps > 0:
            bvps_diff_pct = abs(calculated_bvps - api_bvps) / api_bvps * 100
            if bvps_diff_pct > 15:  # More than 15% difference
                warnings.append(
                    f"[VALIDATION] Book Value Discrepancy: API shows ${api_bvps:.2f}, "
                    f"calculated ${calculated_bvps:.2f} ({bvps_diff_pct:.1f}% difference). "
                    f"May indicate different accounting standards or timing."
                )
                print(f"[WARNING] Book Value discrepancy detected: API ${api_bvps:.2f} vs Calculated ${calculated_bvps:.2f}")
        
        # Check for stale price data
        last_update = data.get('General', {}).get('UpdatedAt', '')
        if last_update:
            try:
                from datetime import datetime, timedelta
                # Handle ISO format with or without 'Z'
                update_date_str = last_update.replace('Z', '+00:00')
                update_date = datetime.fromisoformat(update_date_str)
                days_old = (datetime.now(update_date.tzinfo) - update_date).days
                
                if days_old > 7:
                    warnings.append(
                        f"[VALIDATION] API data is {days_old} days old (last update: {last_update[:10]}). "
                        f"Price and market data may be stale."
                    )
                    print(f"[WARNING] API data is {days_old} days old")
            except Exception as e:
                print(f"[DEBUG] Could not parse UpdatedAt date: {e}")
        
        return warnings
