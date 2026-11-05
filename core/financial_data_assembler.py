"""
Assembles the normalised financial_data dict from provider-neutral CompanyFundamentals
(core/fundamentals.py), the current quote and FX rates. Reads no vendor format: a fundamentals
source adapter (e.g. clients/eodhd_mapper.py) produces the CompanyFundamentals.
"""

import logging
from typing import Dict, Any, Optional, List
from core.currency_converter import CurrencyConverter
from core.errors import PriceUnavailableError
from core.financial_data_processor import FinancialDataProcessor
from core.formulas import common_equity
from core.fundamentals import CompanyFundamentals
from core.ports import FundamentalsSource, QuoteSource, RateSource
from core.history import fiscal_year, has_statement_data
from core.price_quote import PriceQuote, to_major_unit
from config.data_quality_config import (API_DATA_MAX_AGE_DAYS, BVPS_MAX_DIFF_PCT, DIVIDEND_SOURCE_MAX_DIFF_PCT,
                                         PE_MAX_DIFF_PCT, PROFITABILITY_MAX_DIFF_PCT,
                                         SHARE_COUNT_MAX_DIFF_PCT)

logger = logging.getLogger(__name__)


def load_financial_data(ticker: str, fundamentals_source: FundamentalsSource, quote_source: QuoteSource,
                        rate_source: RateSource, debug: bool = False) -> Dict[str, Any]:
    """
    Fetch the fundamentals and current quote through the ports and assemble financial_data.

    Args:
        ticker: SYMBOL.EXCHANGE as given to the CLI (e.g. AAPL.US)
        fundamentals_source, quote_source, rate_source: adapters chosen by clients.factory

    Raises:
        DataSourceError: a source failed; PriceUnavailableError: no usable current price
    """
    fundamentals = fundamentals_source.fetch_fundamentals(ticker)
    # Current price from the quote source (the only price source); assembly itself does no I/O
    quote = quote_source.get_quote(ticker)
    currency_converter = CurrencyConverter(fx_client=rate_source)
    processor = FinancialDataProcessor(currency_converter=currency_converter, debug=debug)
    assembler = FinancialDataAssembler(processor, currency_converter, rate_source, debug=debug)
    return assembler.assemble(fundamentals, ticker, quote=quote)


class FinancialDataAssembler:
    """Builds financial_data from CompanyFundamentals, the current quote and FX rates."""
    
    def __init__(self, processor: FinancialDataProcessor, currency_converter: CurrencyConverter,
                 fx_client: Any, debug: bool = False):
        """
        Args:
            processor: Normaliser for the fundamentals
            currency_converter: Converter sharing the same FX source
            fx_client: RateSource (core/ports.py)
            debug: Enable debug logging
        """
        self.processor = processor
        self.currency_converter = currency_converter
        self.fx_client = fx_client
        self.debug = debug
    

    def _attach_operating_cash_flow(self, history: Dict, fundamentals: CompanyFundamentals,
                                    financials_currency: str, warnings: List[str]) -> None:
        """Annual net cash from operations onto each statement year's history row (display only:
        Risk Factors' dividend coverage, not a Graham criterion), in the financials currency."""
        cash_flow = {end: value for end, value in fundamentals.annual_operating_cash_flow.items() if end in history}
        currency = fundamentals.cash_flow_currency
        if cash_flow and currency != financials_currency:
            cash_flow = self.currency_converter.try_convert_batch(cash_flow, currency, financials_currency)
            if cash_flow is None:
                warnings.append(f"WARNING: Could not convert operating cash flow from {currency} to "
                                f"{financials_currency} - FX rate unavailable; dividend coverage not shown")
                return
        for end, value in cash_flow.items():
            history[end]['operating_cash_flow'] = value
    def assemble(self, fundamentals: CompanyFundamentals, ticker: str,
                 quote: Optional[PriceQuote] = None) -> Dict[str, Any]:
        """
        Build the financial_data dict (see docs/CODEBASE_GUIDE.md §4.1).

        Args:
            fundamentals: Company fundamentals from the fundamentals source
            ticker: Ticker as given to the CLI (e.g. AAPL.US)
            quote: Current price and quote currency from yfinance (the only price source),
                   fetched by the caller, or None

        Raises:
            PriceUnavailableError: no usable current price from yfinance (missing, or quote currency mismatch)
        """
        # The source's own data-quality notes (e.g. values derived from other filed figures) come first
        warnings = list(fundamentals.notes)
        
        # Extract general information
        ticker_code = fundamentals.symbol
        exchange = fundamentals.exchange
        currency = fundamentals.trading_currency
        ceo_name = fundamentals.ceo_name
        
        # Financial statement currency
        financials_currency = fundamentals.statement_currency
        
        logger.info(f"Stock Currency: {currency}, Financials Currency: {financials_currency}")
        
        # Add note if currencies don't match
        if currency != financials_currency:
            logger.warning(f"Currency Mismatch: Stock trades in {currency}, but financial statements are in {financials_currency}")
        
        # Extract additional company info
        sector = fundamentals.sector or 'N/A'
        industry = fundamentals.industry or 'N/A'
        employees = fundamentals.employees or 0
        
        logger.info(f"Company: {fundamentals.name or 'Unknown'}")
        logger.info(f"Exchange: {exchange}, Currency: {currency}")
        logger.info(f"Sector: {sector}, Industry: {industry}")
        
        # The vendor's market figures (display / labelled comparison only; 0.0 = missing)
        market = fundamentals.market
        dividend_per_share = market.dividend_per_share
        dividend_yield = market.dividend_yield
        book_value_per_share = market.book_value_per_share
        # P/E, P/B, ROE, ROA and margin are calculated below from annual audited data
        enterprise_value = market.enterprise_value
        insider_ownership = market.insider_ownership
        institutional_ownership = market.institutional_ownership
        beta = market.beta
        week_52_high = market.week_52_high
        week_52_low = market.week_52_low
        
        # Check if delisted
        if fundamentals.is_delisted:
            warnings.append("WARNING: Company is delisted")
            logger.warning("Company is delisted")
        
        # Extract shares outstanding
        shares_outstanding = fundamentals.shares_outstanding
        if shares_outstanding == 0.0:
            warnings.append("WARNING: Shares outstanding data unavailable")
            logger.warning("Shares outstanding data unavailable")
        else:
            logger.info(f"Shares Outstanding: {shares_outstanding:,.0f}")
        
        # Extract year-specific shares outstanding for accurate EPS calculation
        shares_by_year = dict(fundamentals.shares_by_year)
        if shares_by_year:
            logger.info(f"Found year-specific shares data for {len(shares_by_year)} years")
            if self.debug:
                for year in sorted(shares_by_year.keys(), reverse=True)[:3]:
                    logger.debug(f"{year} shares: {shares_by_year[year]:,.0f}")
        
        # Dividend payments (primary dividend source)
        if fundamentals.dividend_payments:
            logger.info(f"Retrieved {len(fundamentals.dividend_payments)} dividend payment records")
        else:
            logger.info("Dividend payments unavailable - will use Cash Flow data as fallback")
        
        # Parse financial statements using processor
        logger.info("Parsing financial statements...")
        balance_sheet = self.processor.parse_balance_sheet(fundamentals)
        income_statement = self.processor.parse_income_statement(fundamentals)
        dividend_history, forward_dividend_rate, is_dividend_amounts, dividend_currency, dividend_sources = self.processor.parse_dividend_history(fundamentals)
        
        # Calculate TTM dividend from the dividend payments
        ttm_dividend, ttm_dividend_payments, ttm_dividend_currency = self.processor.calculate_ttm_dividend(fundamentals.dividend_payments)
        if ttm_dividend > 0:
            logger.info(f"TTM Dividend: {ttm_dividend:.4f} {ttm_dividend_currency} from {len(ttm_dividend_payments)} payments")
        
        # Convert dividend history to financials currency if needed
        # This is critical for dividend payments, which come in the stock's trading currency.
        # Payment counts have no currency and are never converted (F21)
        if is_dividend_amounts and dividend_currency != financials_currency:
            logger.info(f"Converting dividends from {dividend_currency} to {financials_currency}...")
            converted_dividends = self.currency_converter.try_convert_batch(
                dividend_history, dividend_currency, financials_currency
            )
            
            if converted_dividends is not None:
                dividend_history = converted_dividends
                logger.info(f"Historical dividends converted from {dividend_currency} to {financials_currency}")
                if self.debug:
                    for year_key in list(dividend_history.keys())[:3]:  # Show first 3 for debug
                        logger.debug(f"Converted {year_key} dividend: {dividend_history[year_key]:.4f} {financials_currency}")
            else:
                warnings.append(f"WARNING: Could not convert dividends from {dividend_currency} to {financials_currency} - FX rate unavailable")
                logger.warning(f"Could not get FX rate for {dividend_currency}/{financials_currency}")
        
        # Merge financial data with year-specific shares
        logger.info("Merging financial data...")
        history = self.processor.merge_financial_data(balance_sheet, income_statement, 
                                                      dividend_history, shares_outstanding,
                                                      outstanding_shares_by_year=shares_by_year,
                                                      dividends_are_amounts=is_dividend_amounts)
        self._attach_operating_cash_flow(history, fundamentals, financials_currency, warnings)
        
        # Get current price
        price, price_problem = self.processor.get_current_price(quote, currency, warnings=warnings,
                                                                source=fundamentals.source)
        if price_problem:
            raise PriceUnavailableError(f"Current price unavailable for {ticker}: {price_problem}")
        price_source = 'yfinance'
        
        logger.info(f"Current Price: {price} (Source: {price_source})")
        
        # Get most recent EPS for the P/E calculation
        # Need to find the most recent year with actual financial data (not just dividend data)
        most_recent_eps = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            # Find most recent year with financial data
            for year in sorted_years:
                year_data = history[year]
                # Check if year has actual financial data (not just dividend)
                if has_statement_data(year_data):
                    most_recent_eps = year_data.get('eps', 0.0)
                    break
        
        # The price unit follows the yfinance quote currency code (F6): GBp = pence -> ÷100, the
        # London Fix. The vendor's 52-week range comes from the same exchange prices, so it shares the unit
        price_quote_currency = quote.currency
        price, price_currency = self.currency_converter.normalise_quote_unit(price, price_quote_currency)
        week_52_high, _ = to_major_unit(week_52_high, price_quote_currency)
        week_52_low, _ = to_major_unit(week_52_low, price_quote_currency)
        
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
                        warnings.append("Historical FX rates unavailable - using current rate for all years")
        
        # Convert the vendor's per-share dividend and book value to financials currency
        # (their true currency: the adapter corrects vendor labels, e.g. GBX on pound-scale LSE values)
        highlights_dividend_currency = market.per_share_currency
        
        # Each converted on its own: book value no longer depends on a dividend being present (F10)
        if highlights_dividend_currency != financials_currency:
            if dividend_per_share and dividend_per_share > 0:
                converted_dividend, success = self.currency_converter.convert(
                    dividend_per_share, highlights_dividend_currency, financials_currency
                )
                if success:
                    dividend_per_share = converted_dividend
            if book_value_per_share and book_value_per_share > 0:
                converted_book_value, success = self.currency_converter.convert(
                    book_value_per_share, highlights_dividend_currency, financials_currency
                )
                if success:
                    book_value_per_share = converted_book_value
                    logger.info(f"Book Value converted from {highlights_dividend_currency} to {financials_currency}")
        
        # Convert forward dividend rate to financials currency
        if forward_dividend_rate:
            fwd_div_currency = fundamentals.forward_dividend_currency
            if fwd_div_currency != financials_currency:
                converted_fwd_rate, success = self.currency_converter.convert(
                    forward_dividend_rate, fwd_div_currency, financials_currency
                )
                if success:
                    forward_dividend_rate = converted_fwd_rate
        
        # Convert TTM dividend to financials currency
        if ttm_dividend and ttm_dividend > 0:
            ttm_div_currency = ttm_dividend_currency
            
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
                if has_statement_data(year_data):
                    most_recent_year = year
                    break
            
            if most_recent_year:
                most_recent_data = history[most_recent_year]
                # The common's book equity: preferred stock ranks ahead of it (GRAHAM_METHODOLOGY §3.5)
                total_equity = common_equity(most_recent_data.get('total_equity', 0.0),
                                             most_recent_data.get('preferred_stock', 0.0))
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
        validation_warnings = self._cross_validate_metrics(fundamentals, pe_ratio, calculated_bvps, calculated_roe, calculated_roa, calculated_profit_margin,
                                                           api_bvps=book_value_per_share, currency=financials_currency)
        warnings.extend(validation_warnings)
        
        # Validate data quality
        logger.info("Validating data quality...")
        self.processor.validate_data_quality(history, warnings)
        if history:
            staleness_warning = self.processor.check_data_staleness(history)
            if staleness_warning:
                warnings.append(staleness_warning)
        
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
            else:
                # Mixed sources
                dividend_source = 'Mixed'
        
        # Add data quality warning if Cash Flow dividend differs significantly from Forward Rate
        # This indicates potential timing issues or incomplete data for most recent year
        # Note: Skip this warning if using Dividend API (declared dividends are authoritative)
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_year = fiscal_year(sorted_years[0])
                if most_recent_year in dividend_sources:
                    if dividend_sources[most_recent_year] == 'cash_flow' and forward_dividend_rate and forward_dividend_rate > 0:
                        most_recent_div = history[sorted_years[0]].get('dividend', 0.0)
                        if most_recent_div > 0:
                            diff_pct = abs(most_recent_div - forward_dividend_rate) / forward_dividend_rate * 100
                            if diff_pct > DIVIDEND_SOURCE_MAX_DIFF_PCT:
                                warnings.append(f"Dividend Data Quality: {most_recent_year} Cash Flow shows {most_recent_div:.2f} vs Forward Rate {forward_dividend_rate:.2f} ({diff_pct:.1f}% difference) - most recent year may be incomplete due to payment timing")
        
        if warnings:
            logger.warning(f"Found {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        # Parse quarterly data for TTM calculations
        quarterly_balance_sheet = self.processor.parse_quarterly_balance_sheet(fundamentals)
        quarterly_income_statement = self.processor.parse_quarterly_income_statement(fundamentals)
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
            'data_source': fundamentals.source,  # the fundamentals vendor (dossier header)
            'price_source': price_source,  # NEW: Track price source for data quality assessment
            'dividend_source': dividend_source,  # NEW: Track dividend source for data quality assessment
            'fx_rate_used': fx_rate_used,  # NEW: FX rate used for price conversion (for historical prices)
            'historical_fx_rates': historical_fx_rates,  # NEW: Historical FX rates for date-matched conversion
            'price_currency_before_fx': price_currency,  # major currency of the quote, before FX (GBP for GBp)
            'price_quote_currency': price_quote_currency,  # as yfinance quoted it (e.g. GBp); historical prices share it
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
            'api_last_update': fundamentals.updated_at if fundamentals.updated_at is not None else 'Unknown',
            # TTM data
            'quarterly_data': quarterly_data
        }
    
    def _cross_validate_metrics(self, fundamentals: CompanyFundamentals, calculated_pe: float, calculated_bvps: float, 
                                calculated_roe: float, calculated_roa: float, calculated_profit_margin: float,
                                api_bvps: Optional[float] = None, currency: str = "") -> List[str]:
        """
        Cross-validate calculated metrics against API's pre-calculated values.
        Flag significant discrepancies for user review.
        
        Args:
            fundamentals: Company fundamentals (the vendor's market figures are compared)
            calculated_pe: P/E ratio calculated from financials
            calculated_bvps: Book value per share calculated from balance sheet
            calculated_roe: Return on Equity calculated from annual data
            calculated_roa: Return on Assets calculated from annual data
            calculated_profit_margin: Profit Margin calculated from annual data
            api_bvps: The vendor's book value per share converted to the financials currency (None: as reported)
            currency: Financials currency, for the warning text
        
        Returns:
            List of validation warnings
        """
        warnings = []
        # The vendor's figures are 0.0 when missing (not compared)
        market = fundamentals.market
        
        # Check Share Count Consistency: current (market data) vs latest annual statement count
        shares_stats = fundamentals.shares_outstanding
        outstanding_shares_annual = fundamentals.latest_statement_shares
        
        # Compare share counts if they differ significantly
        if shares_stats > 0 and outstanding_shares_annual > 0:
            diff_pct = abs(outstanding_shares_annual - shares_stats) / shares_stats * 100
            if diff_pct > SHARE_COUNT_MAX_DIFF_PCT:
                warnings.append(
                    f"[VALIDATION] Share Count: Using {outstanding_shares_annual:,.0f} shares from financial statements. "
                    f"Market data ({fundamentals.source}) shows {shares_stats:,.0f} shares ({diff_pct:.1f}% difference). "
                    f"Financial statement shares are used for accurate per-share calculations per Graham methodology."
                )
                logger.info(f"Share count difference: Financial statements {outstanding_shares_annual:,.0f} vs Market data {shares_stats:,.0f}")
        
        # Check P/E ratio
        api_pe = market.pe_ratio
        
        # Handle None values - convert to 0 for comparison
        if calculated_pe is None:
            calculated_pe = 0
        
        if api_pe > 0 and calculated_pe > 0:
            pe_diff_pct = abs(calculated_pe - api_pe) / api_pe * 100
            if pe_diff_pct > PE_MAX_DIFF_PCT:
                warnings.append(
                    f"[VALIDATION] P/E Ratio Difference: API shows {api_pe:.2f} (TTM basis), "
                    f"calculated {calculated_pe:.2f} (annual basis) ({pe_diff_pct:.1f}% difference). "
                    f"Using annual EPS from audited financials per Graham methodology."
                )
                logger.info(f"P/E difference: API {api_pe:.2f} (TTM) vs Calculated {calculated_pe:.2f} (Annual)")
        
        # Check Book Value, both sides in the financials currency (F10): the caller passes
        # book value already converted; the value as reported is only a fallback for direct callers
        if api_bvps is None:
            api_bvps = market.book_value_per_share
        
        # Handle None values - convert to 0 for comparison
        if api_bvps is None:
            api_bvps = 0
        if calculated_bvps is None:
            calculated_bvps = 0
        
        if api_bvps > 0 and calculated_bvps > 0:
            bvps_diff_pct = abs(calculated_bvps - api_bvps) / api_bvps * 100
            if bvps_diff_pct > BVPS_MAX_DIFF_PCT:
                warnings.append(
                    f"[VALIDATION] Book Value Discrepancy: API shows {api_bvps:.2f} {currency}, "
                    f"calculated {calculated_bvps:.2f} {currency} ({bvps_diff_pct:.1f}% difference). "
                    f"Calculated value is total equity / that year's shares from the annual balance sheet; "
                    f"the API figure may use a different date, share count or accounting treatment."
                )
                logger.warning(f"Book Value discrepancy detected: API {api_bvps:.2f} vs Calculated {calculated_bvps:.2f} {currency}")
        
        # Check for stale price data
        last_update = fundamentals.updated_at or ''
        if last_update:
            try:
                from datetime import datetime, timezone
                # Handle ISO format with or without 'Z'
                update_date_str = last_update.replace('Z', '+00:00')
                update_date = datetime.fromisoformat(update_date_str)
                
                # Ensure both datetimes are timezone-aware for comparison
                if update_date.tzinfo is None:
                    update_date = update_date.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                days_old = (now - update_date).days
                
                if days_old > API_DATA_MAX_AGE_DAYS:
                    warnings.append(
                        f"[VALIDATION] API data is {days_old} days old (last update: {last_update[:10]}). "
                        f"Price and market data may be stale."
                    )
                    logger.warning(f"API data is {days_old} days old")
            except Exception as e:
                logger.debug(f"Could not parse UpdatedAt date: {e}")
        
        # Validate profitability metrics
        api_roe = market.roe
        api_roa = market.roa
        api_profit_margin = market.profit_margin
        
        # Handle None values for calculated metrics
        if calculated_roe is None:
            calculated_roe = 0
        if calculated_roa is None:
            calculated_roa = 0
        if calculated_profit_margin is None:
            calculated_profit_margin = 0
        
        # Validate ROE
        if api_roe > 0 and calculated_roe > 0:
            roe_diff_pct = abs(calculated_roe - api_roe) / api_roe * 100
            if roe_diff_pct > PROFITABILITY_MAX_DIFF_PCT:
                warnings.append(
                    f"[VALIDATION] ROE Difference: API shows {api_roe*100:.2f}% (TTM basis), "
                    f"calculated {calculated_roe*100:.2f}% (annual basis) ({roe_diff_pct:.1f}% difference). "
                    f"Using annual data from audited financials per Graham methodology."
                )
                logger.info(f"ROE difference: API {api_roe*100:.2f}% (TTM) vs Calculated {calculated_roe*100:.2f}% (Annual)")
        
        # Validate ROA
        if api_roa > 0 and calculated_roa > 0:
            roa_diff_pct = abs(calculated_roa - api_roa) / api_roa * 100
            if roa_diff_pct > PROFITABILITY_MAX_DIFF_PCT:
                warnings.append(
                    f"[VALIDATION] ROA Difference: API shows {api_roa*100:.2f}% (TTM basis), "
                    f"calculated {calculated_roa*100:.2f}% (annual basis) ({roa_diff_pct:.1f}% difference). "
                    f"Using annual data from audited financials per Graham methodology."
                )
                logger.info(f"ROA difference: API {api_roa*100:.2f}% (TTM) vs Calculated {calculated_roa*100:.2f}% (Annual)")
        
        # Validate Profit Margin
        if api_profit_margin > 0 and calculated_profit_margin > 0:
            margin_diff_pct = abs(calculated_profit_margin - api_profit_margin) / api_profit_margin * 100
            if margin_diff_pct > PROFITABILITY_MAX_DIFF_PCT:
                warnings.append(
                    f"[VALIDATION] Profit Margin Difference: API shows {api_profit_margin*100:.2f}% (TTM basis), "
                    f"calculated {calculated_profit_margin*100:.2f}% (annual basis) ({margin_diff_pct:.1f}% difference). "
                    f"Using annual data from audited financials per Graham methodology."
                )
                logger.info(f"Profit Margin difference: API {api_profit_margin*100:.2f}% (TTM) vs Calculated {calculated_profit_margin*100:.2f}% (Annual)")
        
        return warnings
