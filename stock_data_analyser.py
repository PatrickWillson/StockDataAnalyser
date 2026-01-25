import argparse
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import Core Modules
from clients.factory import ClientFactory
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from output.dossier_generator import DossierGenerator

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)

def format_price_display(price: float, trading_currency: str, financials_currency: str, 
                        converted_value: float = None) -> str:
    """
    Format price display with trading currency first.
    
    Requirements 4.1, 4.2, 4.3, 4.4:
    - Shows trading currency first (e.g., "1,650 GBX")
    - Shows conversion when currencies differ (e.g., "1,650 GBX (16.50 GBP)")
    - Consistent format across all price displays
    
    Args:
        price: Price value in trading currency
        trading_currency: Currency the stock trades in
        financials_currency: Currency of financial statements
        converted_value: Optional converted value in financials currency
        
    Returns:
        Formatted price string
    """
    # Format price with commas and 2 decimal places
    formatted_price = f"{price:,.2f}"
    
    # Single currency case
    if trading_currency == financials_currency:
        return f"{formatted_price} {trading_currency}"
    
    # Dual currency case - show trading currency first, then conversion
    if converted_value is not None:
        formatted_converted = f"{converted_value:,.2f}"
        return f"{formatted_price} {trading_currency} ({formatted_converted} {financials_currency})"
    
    # Fallback if no converted value provided but currencies differ
    return f"{formatted_price} {trading_currency}"

def save_dossier(ticker, content):
    """Saves the Markdown dossier to the data/ directory."""
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{ticker.replace('.', '_')}_DOSSIER.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Dossier generated: {filename}")
    logger.info("Action: Upload this file to Perplexity Deep Research.")

def configure_logging(debug: bool = False):
    """
    Configure logging with proper format and level.
    
    Args:
        debug: If True, set level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    parser = argparse.ArgumentParser(description="Stock Data Analyser - Financial Analysis Engine")
    parser.add_argument("ticker", type=str, help="Ticker symbol (e.g., AAPL.US, VOD.L)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    ticker = args.ticker.upper()
    
    # Configure logging based on debug flag
    configure_logging(debug=args.debug)

    if not API_KEY:
        logger.error("EODHD_API_KEY not found in .env file.")
        sys.exit(1)

    logger.info(f"Stock Data Analyser Starting for {ticker}")

    try:
        # 1. Fetch Data
        logger.info("[1/4] Fetching Fundamentals from EODHD...")
        client = ClientFactory.create_eodhd_client(API_KEY, debug=args.debug)
        yf_client = ClientFactory.create_yfinance_client(debug=args.debug)
        financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
        
        # Check if price is available - fatal error if not
        price = financial_data.get('price', 0.0)
        if price == 0.0:
            logger.error("="*80)
            logger.error("FATAL ERROR: Current price unavailable from all sources")
            logger.error("="*80)
            logger.error("Graham's Principle: 'No data is better than wrong data.'")
            logger.error("The system cannot generate a reliable valuation without current price data.")
            logger.error("Please verify the ticker symbol or try again later.")
            logger.error("Data sources attempted:")
            logger.error("  1. yfinance (Yahoo Finance - primary source)")
            logger.error("  2. EODHD API (Highlights.SharePrice, General.SharePrice, General.LastPrice)")
            logger.error("Both sources failed to provide current price data.")
            logger.error("="*80)
            sys.exit(1)
        
        # 1.5. Fetch Historical Prices (for Historical P/E and P/B columns)
        logger.info("[1.5/4] Fetching Historical Prices from yfinance...")
        history_keys = list(financial_data.get('history', {}).keys())
        if history_keys:
            # Get date range from balance sheet fiscal year ends
            oldest_date = min(history_keys)
            newest_date = max(history_keys)
            
            logger.debug(f"Fetching historical prices from {oldest_date} to {newest_date}")
            
            # Fetch daily prices
            daily_prices = yf_client.fetch_historical_prices(
                ticker,
                start_date=oldest_date,
                end_date=newest_date
            )
            
            if daily_prices:
                logger.debug(f"Fetched {len(daily_prices)} days of historical price data")
                
                # Match to fiscal year ends
                year_end_prices = yf_client.match_fiscal_year_end_prices(
                    daily_prices,
                    fiscal_year_ends=history_keys
                )
                
                logger.debug(f"Matched prices to {len([p for p in year_end_prices.values() if p is not None])} fiscal year ends")
                
                # Convert currency if needed
                stock_currency = financial_data.get('original_stock_currency', '')
                financials_currency = financial_data.get('financials_currency', '')
                exchange = financial_data.get('exchange', '')
                
                # For LSE stocks, yfinance returns prices in GBX (pence), not GBP
                # We need to convert GBX → GBP first, then GBP → USD (if needed)
                if exchange == "LSE" and stock_currency == "GBX":
                    logger.debug("Converting historical prices from GBX (pence) to GBP (pounds)")
                    gbp_prices = {}
                    for date_key, price_value in year_end_prices.items():
                        if price_value is not None:
                            gbp_prices[date_key] = price_value / 100  # GBX → GBP
                        else:
                            gbp_prices[date_key] = None
                    year_end_prices = gbp_prices
                    # Update currency for next conversion step
                    stock_currency = "GBP"
                    logger.debug(f"Converted {len([p for p in gbp_prices.values() if p is not None])} prices from GBX to GBP")
                
                if stock_currency and financials_currency and stock_currency != financials_currency:
                    logger.debug(f"Converting historical prices from {stock_currency} to {financials_currency}")
                    
                    # Get historical FX rates and current rate
                    historical_fx_rates = financial_data.get('historical_fx_rates', {})
                    current_fx_rate = financial_data.get('fx_rate_used')
                    
                    if current_fx_rate and current_fx_rate > 0:
                        # Convert all prices using date-matched rates
                        converted_prices = {}
                        fallback_years = []
                        
                        for date_key, price_value in year_end_prices.items():
                            if price_value is not None:
                                # Use historical rate if available, otherwise current rate
                                fx_rate = historical_fx_rates.get(date_key)
                                
                                if fx_rate is None:
                                    # No historical rate available, use current rate as fallback
                                    fx_rate = current_fx_rate
                                    year_only = date_key.split('-')[0]
                                    fallback_years.append(year_only)
                                
                                converted_prices[date_key] = price_value * fx_rate
                            else:
                                converted_prices[date_key] = None
                        
                        year_end_prices = converted_prices
                        
                        # Add appropriate warning based on whether historical rates were used
                        if historical_fx_rates and len(fallback_years) == 0:
                            # All years used historical rates
                            financial_data['warnings'].append(
                                f"Historical prices converted from {stock_currency} to {financials_currency} "
                                f"using date-matched historical FX rates. This ensures accurate historical P/E and P/B ratios."
                            )
                            logger.debug(f"Applied historical FX rates to {len(year_end_prices)} prices")
                        elif historical_fx_rates and len(fallback_years) > 0:
                            # Some years used fallback
                            unique_years = sorted(set(fallback_years))
                            financial_data['warnings'].append(
                                f"Historical prices converted from {stock_currency} to {financials_currency} "
                                f"using date-matched historical FX rates. Years {', '.join(unique_years)} used current rate "
                                f"{current_fx_rate:.4f} as fallback (historical rate unavailable)."
                            )
                            logger.debug(f"Applied historical FX rates with {len(fallback_years)} fallbacks")
                        else:
                            # No historical rates available, all used current rate
                            financial_data['warnings'].append(
                                f"Historical prices converted from {stock_currency} to {financials_currency} "
                                f"using current FX rate {current_fx_rate:.4f}. Note: Historical FX rates not used - "
                                f"actual historical valuations may differ due to FX fluctuations."
                            )
                            logger.debug(f"Applied current FX rate {current_fx_rate:.4f} to historical prices (historical rates unavailable)")
                    else:
                        logger.warning("FX rate not available for historical price conversion")
                        financial_data['warnings'].append(
                            "Historical prices could not be converted to financials currency - "
                            "FX rate unavailable. Historical P/E and P/B may be inaccurate."
                        )
                
                # Merge into history
                missing_price_count = 0
                for date_key, price_value in year_end_prices.items():
                    if date_key in financial_data['history']:
                        financial_data['history'][date_key]['year_end_price'] = price_value
                        if price_value is None:
                            missing_price_count += 1
                
                if missing_price_count > 0:
                    logger.debug(f"{missing_price_count} fiscal year ends have no price data within 7-day window")
                    financial_data['warnings'].append(
                        f"Historical prices unavailable for {missing_price_count} fiscal year ends "
                        f"(no trading data within 7-day window). Historical P/E and P/B will show N/A for those years."
                    )
                
                logger.info(f"Historical prices added to {len(year_end_prices) - missing_price_count} years")
            else:
                logger.warning("Historical prices unavailable from yfinance - price columns will show N/A")
                financial_data['warnings'].append(
                    "Historical prices unavailable from yfinance. Historical P/E and P/B columns will show N/A. "
                    "This may be due to ticker format issues, delisted stock, or yfinance API unavailability."
                )
        else:
            logger.warning("No financial history available - skipping historical price fetch")
            financial_data['warnings'].append(
                "No financial history data available - historical price columns will be empty."
            )
        
        # 2. Compute Metrics
        logger.info("[2/4] Calculating Graham Metrics (Strict Rules)...")
        calculator = GrahamCalculator(financial_data)
        metrics = calculator.compute_all()
        
        # 3. Detect Anomalies (Statistical)
        logger.info("[3/4] Scanning for Statistical Anomalies...")
        detector = AnomalyDetector(financial_data)
        anomalies = detector.scan()
        
        # 4. Generate Output
        logger.info("[4/4] Generating Dossier...")
        generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
        dossier_content = generator.generate()
        save_dossier(ticker, dossier_content)

    except Exception as e:
        logger.critical(f"Failed to process {ticker}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
