import argparse
import os
import sys
import logging
from dataclasses import replace
from dotenv import load_dotenv

# Import Core Modules
from core.errors import DataSourceError, PriceUnavailableError
from core.financial_data_assembler import load_financial_data
from clients.factory import ClientFactory
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from core.historical_prices import apply_year_end_prices
from core.ttm_calculator import TTMCalculator
from core.models import FinancialData, or_default
from output.dossier_generator import DossierGenerator
from logging_utils import install_secret_redaction

# Load Environment Variables (FUNDAMENTALS_PROVIDER picks the fundamentals vendor, default "eodhd";
# the variables it needs are read from the names the provider declares, e.g. EODHD_API_KEY)
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def save_dossier(ticker, content):
    """Saves the Markdown dossier to the data/ directory."""
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{ticker.replace('.', '_')}_DOSSIER.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Dossier generated: {filename}")
    logger.info("Action: Upload this file to Perplexity Deep Research.")

def configure_logging(debug: bool = False, secrets=()):
    """
    Configure logging with proper format and level.

    Args:
        debug: If True, set level to DEBUG; otherwise INFO
        secrets: Secret values (e.g. API keys) to redact from all log output
    """
    level = logging.DEBUG if debug else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # urllib3 logs full request URLs (including api_token) at DEBUG
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    install_secret_redaction(secrets)

def main():
    parser = argparse.ArgumentParser(description="Stock Data Analyser - Financial Analysis Engine")
    parser.add_argument("ticker", type=str, help="Ticker symbol (e.g., AAPL.US, VOD.L)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    ticker = args.ticker.upper()
    
    try:
        provider = ClientFactory.fundamentals_provider(os.getenv("FUNDAMENTALS_PROVIDER"))
    except ValueError as e:
        configure_logging(debug=args.debug)
        logger.error(str(e))
        sys.exit(1)
    env = {name: os.getenv(name) for name in provider.required_env}
    optional = {name: os.getenv(name) for name in provider.optional_env if os.getenv(name)}

    # Configure logging based on debug flag
    configure_logging(debug=args.debug, secrets=[os.getenv(name) for name in provider.secret_env])

    missing = [name for name, value in env.items() if not value]
    if missing:
        logger.error(f"{', '.join(missing)} not found in .env file.")
        sys.exit(1)

    logger.info(f"Stock Data Analyser Starting for {ticker}")

    try:
        # 1. Fetch Data
        fundamentals_source = ClientFactory.create_fundamentals_source({**env, **optional}, provider.name,
                                                                       debug=args.debug)
        logger.info(f"[1/6] Fetching Fundamentals from {fundamentals_source.name}...")
        quote_source = ClientFactory.create_quote_source(debug=args.debug)
        financial_data = load_financial_data(ticker, fundamentals_source, quote_source,
                                             ClientFactory.create_rate_source(), debug=args.debug)
        price = financial_data.get('price', 0.0)
        
        # 1.5. Fetch Historical Prices (for Historical P/E and P/B columns)
        logger.info("[2/6] Fetching Historical Prices from yfinance...")
        history_keys = list(financial_data.get('history', {}).keys())
        year_end_prices = None
        if history_keys:
            logger.debug(f"Fetching historical prices from {min(history_keys)} to {max(history_keys)}")
            daily_prices = quote_source.fetch_historical_prices(
                ticker,
                start_date=min(history_keys),
                end_date=max(history_keys)
            )
            if daily_prices:
                logger.debug(f"Fetched {len(daily_prices)} days of historical price data")
                year_end_prices = quote_source.match_fiscal_year_end_prices(
                    daily_prices,
                    fiscal_year_ends=history_keys
                )
        apply_year_end_prices(financial_data, year_end_prices)
        
        # Financial data is final from here on (TTM warnings are added below): a typed, frozen model (M7)
        financial_data = FinancialData.from_dict(financial_data)
        
        # 2. Parse Quarterly Data for TTM Calculations
        logger.info("[3/6] Parsing Quarterly Data for TTM Analysis...")
        quarterly_data = or_default(financial_data.quarterly_data, {'balance_sheet': {}, 'income_statement': {}})
        
        # 3. Compute Metrics
        logger.info("[4/6] Calculating Graham Metrics (Strict Rules)...")
        calculator = GrahamCalculator(financial_data)
        metrics = calculator.compute()
        
        # 4. Calculate TTM Metrics
        logger.info("[5/6] Calculating TTM Metrics...")
        ttm_metrics = None
        ttm_warnings = []
        if quarterly_data and (quarterly_data.get('balance_sheet') or quarterly_data.get('income_statement')):
            try:
                # Periodic statements are in the financials (= unified) currency
                ttm_calculator = TTMCalculator(
                    quarterly_data=quarterly_data,
                    price=price,
                    currency=or_default(financial_data.currency, 'USD'),
                )
                
                ttm_metrics = ttm_calculator.compute()
                
                # Add TTM warnings to financial data warnings
                if ttm_metrics.warnings:
                    ttm_warnings.extend(ttm_metrics.warnings)
                
                logger.info(f"TTM Analysis: {or_default(ttm_metrics.reporting_frequency, 'N/A')} reporting detected")
            except Exception as e:
                logger.warning(f"TTM calculation failed: {str(e)}")
                ttm_warnings.append(f"TTM Analysis: Calculation failed - {str(e)}")
        else:
            logger.info("TTM Analysis: Quarterly data not available")
            ttm_warnings.append("TTM Analysis: Periodic data not available from API")
        
        financial_data = replace(financial_data, warnings=(*or_default(financial_data.warnings, ()), *ttm_warnings))
        
        # 5. Detect Anomalies (Statistical)
        logger.info("[6/6] Scanning for Statistical Anomalies...")
        detector = AnomalyDetector(financial_data)
        anomalies = detector.scan()
        
        # 6. Generate Output
        logger.info("[7/7] Generating Dossier...")
        generator = DossierGenerator(ticker, financial_data, metrics, anomalies, ttm_metrics=ttm_metrics)
        dossier_content = generator.generate()
        save_dossier(ticker, dossier_content)

    except PriceUnavailableError as e:
        _log_price_unavailable(ticker, e)
        sys.exit(1)
    except DataSourceError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to process {ticker}: {str(e)}")
        sys.exit(1)


def _log_price_unavailable(ticker, error):
    """Explain why no dossier was produced when no current price is available."""
    logger.error("="*80)
    logger.error("FATAL ERROR: Current price unavailable")
    logger.error("="*80)
    logger.error(str(error))
    logger.error("Graham's Principle: 'No data is better than wrong data.'")
    logger.error("The system cannot generate a reliable valuation without current price data.")
    logger.error("Price source: yfinance (Yahoo Finance). Fundamentals-vendor price fields are not used: their date and unit are opaque.")
    logger.error("Troubleshooting:")
    logger.error("  - Check the ticker format (e.g. AAPL.US, VOD.LSE) and that the stock is actively trading")
    logger.error("  - yfinance may not have data for this ticker; check the exchange mapping in clients/yfinance_client.py")
    logger.error("  - Delisted or suspended stocks have no current price")
    logger.error("="*80)

if __name__ == "__main__":
    main()
