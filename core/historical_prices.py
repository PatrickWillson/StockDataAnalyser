"""
Historical year-end prices: currency handling and merge into the financial history.

The CLI fetches daily prices and matches them to fiscal year-ends (I/O, yfinance client);
this module converts them to the financials currency (GBX -> GBP, then date-matched
historical FX with the current rate as fallback), stores them as history[date]['year_end_price']
and records what was done in financial_data['warnings']. Moved from main() (M3.5).
"""

import logging
from typing import Any, Dict, Optional

from config.data_quality_config import FISCAL_YEAR_END_LOOKBACK_DAYS

logger = logging.getLogger(__name__)


def apply_year_end_prices(financial_data: Dict[str, Any],
                          year_end_prices: Optional[Dict[str, Optional[float]]]) -> None:
    """
    Convert year-end prices to the financials currency and merge them into the history.

    Args:
        financial_data: Assembled financial data (history, currencies, FX rates, warnings); updated in place
        year_end_prices: Fiscal year end -> closing price in the trading currency (None for no
                         trading data near that date), or None if historical prices were unavailable
    """
    if not financial_data.get('history'):
        logger.warning("No financial history available - skipping historical price fetch")
        financial_data['warnings'].append(
            "No financial history data available - historical price columns will be empty."
        )
        return

    if year_end_prices is None:
        logger.warning("Historical prices unavailable from yfinance - price columns will show N/A")
        financial_data['warnings'].append(
            "Historical prices unavailable from yfinance. Historical P/E and P/B columns will show N/A. "
            "This may be due to ticker format issues, delisted stock, or yfinance API unavailability."
        )
        return

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
        logger.debug(f"{missing_price_count} fiscal year ends have no price data within {FISCAL_YEAR_END_LOOKBACK_DAYS}-day window")
        financial_data['warnings'].append(
            f"Historical prices unavailable for {missing_price_count} fiscal year ends "
            f"(no trading data within {FISCAL_YEAR_END_LOOKBACK_DAYS}-day window). Historical P/E and P/B will show N/A for those years."
        )
    
    logger.info(f"Historical prices added to {len(year_end_prices) - missing_price_count} years")
