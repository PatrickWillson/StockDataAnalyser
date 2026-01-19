import argparse
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Import Core Modules (You will create these next)
from clients.eodhd_client import EODHDClient
from clients.alphavantage_client import AlphaVantageClient
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")

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

def generate_dossier_content(ticker, financial_data, metrics, anomalies):
    """
    Generates Markdown-formatted dossier for Perplexity Deep Research.
    Uses proper Markdown syntax with headers, horizontal rules, and tables.
    """
    lines = []
    
    # Extract currency information - now unified to financials_currency
    unified_currency = financial_data.get('currency', 'USD')
    original_stock_currency = financial_data.get('original_stock_currency', unified_currency)
    
    # Dossier Header with CEO name
    ceo_name = financial_data.get('ceo_name', 'N/A')
    sector = financial_data.get('sector', 'N/A')
    industry = financial_data.get('industry', 'N/A')
    employees = financial_data.get('employees', 0)
    
    lines.append(f"# STOCK ANALYSIS DOSSIER: {ticker}")
    lines.append(f"# DATE: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"# SOURCE: EODHD (Tier 1 Data)")
    lines.append(f"# CEO: {ceo_name}")
    lines.append(f"# SECTOR: {sector} | INDUSTRY: {industry}")
    lines.append(f"# EMPLOYEES: {employees:,}" if employees > 0 else "# EMPLOYEES: N/A")
    
    # Add data freshness note
    history = financial_data.get('history', {})
    if history:
        sorted_years = sorted(history.keys(), reverse=True)
        if sorted_years:
            most_recent_year = sorted_years[0].split('-')[0]
            lines.append(f"# MOST RECENT ANNUAL DATA: {most_recent_year}")
    
    # Add currency note if conversion was applied
    if original_stock_currency != unified_currency:
        lines.append(f"# CURRENCY: All values in {unified_currency} (stock trades in {original_stock_currency})")
    else:
        lines.append(f"# CURRENCY: {unified_currency}")
    lines.append("")
    lines.append("---")
    
    # Section 1: Executive Summary
    lines.append("")
    lines.append("## SECTION 1: EXECUTIVE SUMMARY")
    lines.append("*Current metrics (P/E, Price) reflect most recent available data*")
    lines.append("")
    
    # Valuation metrics - all in unified currency
    lines.append(f"- Verdict: **{metrics['verdict']}**")
    
    # Graham number and EPV
    graham_str = metrics['graham_number']
    epv_str = metrics['epv']
    net_net_str = metrics.get('net_net_value', 'N/A')
    
    if graham_str != 'N/A':
        graham_display = format_price_display(float(graham_str), unified_currency, unified_currency)
        lines.append(f"- Intrinsic Value (Graham): {graham_display}")
    else:
        lines.append(f"- Intrinsic Value (Graham): {graham_str}")
    
    if epv_str != 'N/A':
        epv_display = format_price_display(float(epv_str), unified_currency, unified_currency)
        lines.append(f"- Intrinsic Value (EPV): {epv_display}")
    else:
        lines.append(f"- Intrinsic Value (EPV): {epv_str}")
    
    if net_net_str != 'N/A':
        net_net_display = format_price_display(float(net_net_str), unified_currency, unified_currency)
        lines.append(f"- Net-Net Value: {net_net_display}")
    else:
        lines.append(f"- Net-Net Value: {net_net_str}")
    
    lines.append(f"- Margin of Safety: {metrics['margin_of_safety']}")
    
    # Format current price with currency display
    # Price is already in unified_currency after conversions
    current_price_display = format_price_display(
        financial_data['price'], 
        unified_currency,  # Price is in unified currency
        unified_currency
    )
    lines.append(f"- Current Price: {current_price_display}")
    
    # Price ranges - these are still in original currency from API
    week_52_high = financial_data.get('week_52_high', 0)
    week_52_low = financial_data.get('week_52_low', 0)
    if week_52_high > 0 and week_52_low > 0:
        # Convert to unified currency if needed
        if original_stock_currency != unified_currency:
            # Get FX rate for conversion
            from clients.fx_client import FXClient
            fx_client = FXClient()
            fx_rate = fx_client.get_rate(original_stock_currency, unified_currency)
            if fx_rate:
                high_display = format_price_display(week_52_high, original_stock_currency, unified_currency, week_52_high * fx_rate)
                low_display = format_price_display(week_52_low, original_stock_currency, unified_currency, week_52_low * fx_rate)
            else:
                # Fallback if FX rate unavailable
                high_display = format_price_display(week_52_high, original_stock_currency, unified_currency)
                low_display = format_price_display(week_52_low, original_stock_currency, unified_currency)
        else:
            high_display = format_price_display(week_52_high, original_stock_currency, unified_currency)
            low_display = format_price_display(week_52_low, original_stock_currency, unified_currency)
        
        lines.append(f"- 52-Week Range: {low_display} - {high_display}")
    
    # Dividend information - show source and add warning if using forward rate
    # Requirements 2.5, 2.6, 2.7, 2.8
    forward_div = financial_data.get('forward_dividend_rate')
    dividend_source = financial_data.get('dividend_source', 'Unknown')
    source_indicators = financial_data.get('dividend_sources', {})  # Fixed: use 'dividend_sources' not 'dividend_source_indicators'
    
    # Get most recent year to check if it uses forward rate
    history = financial_data.get('history', {})
    most_recent_year = None
    most_recent_div_source = None
    most_recent_div_amount = None
    if history:
        sorted_years = sorted(history.keys(), reverse=True)
        if sorted_years:
            most_recent_year = sorted_years[0].split('-')[0]
            most_recent_div_source = source_indicators.get(most_recent_year, 'unknown')
            most_recent_div_amount = history[sorted_years[0]].get('dividend', 0.0)
    
    # Requirement 2.7: Show both values when both are available for most recent year
    if most_recent_div_source in ['cash_flow', 'dividend_api'] and forward_div and forward_div > 0 and most_recent_div_amount > 0:
        # Both actual dividend and forward rate available - show both
        actual_yield_cf = (most_recent_div_amount / financial_data['price']) * 100
        actual_yield_fwd = (forward_div / financial_data['price']) * 100
        
        cf_display = format_price_display(most_recent_div_amount, unified_currency, unified_currency)
        fwd_display = format_price_display(forward_div, unified_currency, unified_currency)
        
        # Determine label based on actual source
        if most_recent_div_source == 'dividend_api':
            lines.append(f"- Trailing Dividend: {cf_display} (Yield: {actual_yield_cf:.2f}%) - Declared (Dividend API)")
        else:
            lines.append(f"- Trailing Dividend: {cf_display} (Yield: {actual_yield_cf:.2f}%) - Paid (Cash Flow)")
        lines.append(f"  - Forward Rate: {fwd_display} (Yield: {actual_yield_fwd:.2f}%)")
    elif forward_div and forward_div > 0:
        actual_yield = (forward_div / financial_data['price']) * 100
        # Dividend is already in unified currency
        div_display = format_price_display(forward_div, unified_currency, unified_currency)
        
        # Determine label based on source (Requirements 2.6)
        if most_recent_div_source == 'dividend_api':
            # Using Dividend API (declared dividends with exact dates)
            lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Declared (Dividend API)")
        elif most_recent_div_source == 'cash_flow':
            # Using actual cash flow data
            lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Paid (Cash Flow)")
        elif most_recent_div_source == 'forward_rate':
            # Using forward rate - add warning (Requirement 2.5)
            lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Declared (Forward Rate)")
            lines.append(f"  - ⚠️ {most_recent_year} dividend uses forward declared rate (cash flow data unavailable) - this is an estimate, not historical fact")
        else:
            # Unknown source or mixed
            lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%)")
    
    # Valuation ratios
    pe_ratio = financial_data.get('pe_ratio', 0)
    price_to_book = financial_data.get('price_to_book', 0)
    if pe_ratio > 0:
        lines.append(f"- P/E Ratio: {pe_ratio:.2f}")
    if price_to_book > 0:
        lines.append(f"- Price/Book: {price_to_book:.2f}")
    
    lines.append("")
    lines.append("---")
    
    # Section 2.5: Key Metrics
    lines.append("")
    lines.append("## SECTION 2: KEY METRICS")
    
    # Profitability
    roe = financial_data.get('roe', 0)
    roa = financial_data.get('roa', 0)
    profit_margin = financial_data.get('profit_margin', 0)
    if roe > 0:
        lines.append(f"- Return on Equity (ROE): {roe*100:.2f}%")
    if roa > 0:
        lines.append(f"- Return on Assets (ROA): {roa*100:.2f}%")
    if profit_margin > 0:
        lines.append(f"- Profit Margin: {profit_margin*100:.2f}%")
    
    # Book value (calculate from most recent balance sheet data for consistency with table)
    history = financial_data.get('history', {})
    if history:
        sorted_years = sorted(history.keys(), reverse=True)
        if sorted_years:
            most_recent_data = history[sorted_years[0]]
            total_equity = most_recent_data.get('total_equity', 0)
            shares = most_recent_data.get('shares_outstanding', 0)
            if shares > 0 and total_equity > 0:
                book_value = round(total_equity / shares, 2)
                # Book value is already in unified currency
                bvps_display = format_price_display(book_value, unified_currency, unified_currency)
                lines.append(f"- Book Value Per Share: {bvps_display}")
    
    # Ownership
    insider = financial_data.get('insider_ownership', 0)
    institutional = financial_data.get('institutional_ownership', 0)
    if insider > 0:
        lines.append(f"- Insider Ownership: {insider:.2f}%")
    if institutional > 0:
        lines.append(f"- Institutional Ownership: {institutional:.2f}%")
    
    # Risk
    beta = financial_data.get('beta', 0)
    if beta > 0:
        lines.append(f"- Beta (Volatility): {beta:.3f}")
    
    lines.append("")
    lines.append("---")
    
    # NEW SECTION: Methodology Notes
    lines.append("")
    lines.append("## METHODOLOGY NOTES")
    lines.append("*How key metrics are calculated*")
    lines.append("")
    
    # Get EPV details
    epv_details = metrics.get('epv_details', {})
    epv_value = metrics.get('epv', 0)
    epv_per_share = epv_details.get('epv_per_share', 0)
    normalized_earnings = epv_details.get('normalized_earnings', 0)
    years_used = epv_details.get('years_used', 0)
    cost_of_capital = epv_details.get('cost_of_capital', 0.10)
    
    # Get most recent EPS for P/E explanation
    most_recent_eps = 0
    if history and sorted_years:
        most_recent_eps = history[sorted_years[0]].get('eps', 0)
    
    lines.append("### Valuation Metrics:")
    
    if pe_ratio > 0 and most_recent_eps > 0:
        eps_display = format_price_display(most_recent_eps, unified_currency, unified_currency)
        lines.append(f"- **P/E Ratio ({pe_ratio:.2f})**: Current Price / Most Recent Annual EPS")
        lines.append(f"  - Calculated from audited financials, not API pre-calculated ratios")
        lines.append(f"  - EPS: {eps_display} (Net Income / Shares Outstanding)")
    
    graham_number = metrics.get('graham_number', 0)
    if isinstance(graham_number, (int, float)) and graham_number > 0:
        graham_display = format_price_display(graham_number, unified_currency, unified_currency)
        lines.append(f"- **Graham Number ({graham_display})**: √(22.5 × EPS × BVPS)")
        lines.append(f"  - Conservative intrinsic value estimate")
        lines.append(f"  - Based on Benjamin Graham's formula from 'The Intelligent Investor'")
    
    if epv_value > 0:
        lines.append(f"- **EPV - Earnings Power Value**")
        lines.append(f"")
        lines.append(f"  **Graham's Full-Cycle Method:**")
        lines.append(f"  - Uses 7-10 year average of net income")
        lines.append(f"  - **Includes ALL years** (profitable and unprofitable)")
        lines.append(f"  - Loss years reduce the average (real value destruction)")
        lines.append(f"  - Only extraordinary one-time events should be adjusted")
        lines.append(f"")
        lines.append(f"  **Calculation for {ticker}:**")
        lines.append(f"  - Years Used: {years_used}")
        
        # Get the actual years and net incomes from EPV details
        years_included = epv_details.get('years_included', [])
        net_incomes = epv_details.get('net_incomes', [])
        
        if years_included and net_incomes:
            # Format net incomes with currency
            net_income_strs = []
            for ni in net_incomes:
                if ni >= 0:
                    net_income_strs.append(f"{unified_currency}{ni:,.0f}")
                else:
                    net_income_strs.append(f"-{unified_currency}{abs(ni):,.0f}")
            
            # Show years range
            if len(years_included) > 0:
                first_year = years_included[-1].split('-')[0]  # Oldest year
                last_year = years_included[0].split('-')[0]    # Most recent year
                lines.append(f"  - Years: {first_year}-{last_year}")
            
            # Show net incomes
            lines.append(f"  - Net Incomes: {', '.join(net_income_strs)}")
        
        if normalized_earnings > 0:
            lines.append(f"  - Normalized Earnings: {unified_currency}{normalized_earnings:,.0f} (average including losses)")
        
        lines.append(f"  - EPV: {unified_currency}{epv_value:,.0f} ({unified_currency}{normalized_earnings:,.0f} / {cost_of_capital:.0%})")
        
        if epv_per_share > 0:
            epv_per_share_display = format_price_display(epv_per_share, unified_currency, unified_currency)
            lines.append(f"  - EPV Per Share: {epv_per_share_display}")
        
        lines.append(f"")
        
        # Count loss years for the note
        loss_years = [ni for ni in net_incomes if ni < 0]
        if loss_years:
            loss_count = len(loss_years)
            # Identify which years were losses
            loss_year_labels = []
            for i, ni in enumerate(net_incomes):
                if ni < 0 and i < len(years_included):
                    loss_year_labels.append(years_included[i].split('-')[0])
            
            if loss_year_labels:
                loss_years_str = ', '.join(loss_year_labels)
                lines.append(f"  **Note**: The {years_used}-year average includes {loss_count} loss year{'s' if loss_count > 1 else ''} ({loss_years_str}), reflecting the company's full business cycle performance per Graham's methodology.")
            else:
                lines.append(f"  **Note**: The {years_used}-year average includes {loss_count} loss year{'s' if loss_count > 1 else ''}, reflecting the company's full business cycle performance per Graham's methodology.")
        else:
            lines.append(f"  **Note**: All {years_used} years were profitable, demonstrating consistent earnings power.")
        
        lines.append(f"")
        lines.append(f"  **Graham's Principle**: *\"The concept of 'earning power' implies a fairly confident expectation of certain future results, based on past performance under varying conditions. The record must cover a number of years, first because a continued or repeated performance is always more impressive than a single occurrence and secondly because the average of a fairly long period will tend to absorb and equalize the distorting influences of the business cycle.\"*")
    
    net_net = metrics.get('net_net_value', 0)
    if isinstance(net_net, (int, float)) and net_net > 0:
        net_net_display = format_price_display(net_net, unified_currency, unified_currency)
        lines.append(f"- **Net-Net Value ({net_net_display})**: (Current Assets - Total Liabilities) / Shares")
        lines.append(f"  - Conservative liquidation value estimate")
        lines.append(f"  - Graham's 'cigar butt' valuation for distressed situations")
    
    mos = metrics.get('margin_of_safety', 0)
    if isinstance(mos, (int, float)):
        lines.append(f"- **Margin of Safety ({mos:.1f}%)**: (Graham Number - Price) / Graham Number × 100")
        lines.append(f"  - Percentage discount to intrinsic value")
        lines.append(f"  - Graham recommended minimum 20-30% for defensive investors")
    
    lines.append("")
    lines.append("---")
    
    # NEW SECTION: Data Quality & Limitations
    lines.append("")
    lines.append("## DATA QUALITY & LIMITATIONS")
    lines.append("")
    
    # Data sources and timestamps
    api_update = financial_data.get('api_last_update', 'Unknown')
    lines.append("### Data Sources:")
    lines.append(f"- **API Provider**: EODHD (End of Day Historical Data)")
    if api_update != 'Unknown':
        lines.append(f"- **Last API Update**: {api_update}")
    if history and sorted_years:
        most_recent_year = sorted_years[0].split('-')[0]
        lines.append(f"- **Most Recent Financials**: {most_recent_year}")
    
    # Currency conversion info
    if original_stock_currency != unified_currency:
        fx_rate = financial_data.get('fx_rate_used', 0)
        if fx_rate > 0:
            lines.append(f"- **Currency Conversion**: {original_stock_currency} → {unified_currency} at rate {fx_rate:.4f}")
    
    lines.append("")
    lines.append("### Known Limitations:")
    lines.append("- **Dividend Data**: Calculated from Cash Flow statements (dividendsPaid / shares outstanding)")
    lines.append("  - Represents actual cash distributed during fiscal year")
    lines.append("  - May differ from declared dividends due to payment timing")
    lines.append("  - Most recent year may be incomplete if final dividend paid after year-end")
    lines.append("  - Forward Annual Dividend Rate shown for comparison when available")
    lines.append("  - Verify with company filings for investment decisions")
    lines.append("- **52-Week Range**: May reflect stale data; verify against live sources for trading decisions")
    lines.append("- **Quarterly Data**: Not included in analysis; annual data only per Graham methodology")
    lines.append("- **Forward Estimates**: Not included; analysis based on historical audited financials only")
    lines.append("- **Pre-calculated Ratios**: System recalculates all metrics from source data rather than using API's pre-calculated values")
    
    lines.append("")
    lines.append("---")
    
    # NEW SECTION: Data Quality Assessment
    lines.append("")
    lines.append("## DATA QUALITY ASSESSMENT")
    lines.append("")
    
    # Evaluate current price source (Requirements 5.2)
    price_source = financial_data.get('price_source', 'EODHD')
    if price_source == 'EODHD':
        lines.append("- **Current Price**: ✓ From EODHD (primary source)")
    elif price_source == 'Alpha Vantage':
        lines.append("- **Current Price**: ⚠️ From Alpha Vantage (EODHD unavailable)")
    else:
        lines.append("- **Current Price**: ❌ Missing from all sources")
    
    # Evaluate financial statements completeness (Requirements 5.3)
    history = financial_data.get('history', {})
    years_available = len(history)
    if years_available >= 10:
        lines.append(f"- **Financial Statements**: ✓ Complete ({years_available} years available)")
    elif years_available >= 7:
        lines.append(f"- **Financial Statements**: ⚠️ Limited history ({years_available} years, minimum 7 for EPV)")
    else:
        lines.append(f"- **Financial Statements**: ❌ Insufficient history ({years_available} years, minimum 7 required)")
    
    # Evaluate dividend data source (Requirements 5.4)
    dividend_source = financial_data.get('dividend_source', 'Unknown')
    if dividend_source == 'Dividend API':
        lines.append("- **Dividend Data**: ✓ From Dividend API (declared dividends with exact dates)")
    elif dividend_source == 'Cash Flow':
        lines.append("- **Dividend Data**: ✓ From Cash Flow statements (actual paid)")
    elif dividend_source == 'Forward Rate':
        lines.append("- **Dividend Data**: ⚠️ From Forward Rate (estimate, not historical)")
    elif dividend_source == 'Mixed':
        lines.append("- **Dividend Data**: ⚠️ Mixed sources (Cash Flow + Forward Rate for recent year)")
    else:
        lines.append("- **Dividend Data**: ❌ No reliable dividend data available")
    
    # Evaluate ownership data staleness (Requirements 5.5)
    insider_ownership = financial_data.get('insider_ownership', 0)
    institutional_ownership = financial_data.get('institutional_ownership', 0)
    if insider_ownership > 0 or institutional_ownership > 0:
        lines.append("- **Ownership Data**: ✓ Available from API (verify with regulatory filings)")
    else:
        lines.append("- **Ownership Data**: ⚠️ Not available or not disclosed")
    
    lines.append("")
    
    # Include Graham quote about margin of safety (Requirements 5.6)
    lines.append("**Graham's Principle**: *\"The margin of safety is always dependent on the price paid. It will be large at one price, small at some higher price, nonexistent at some still higher price.\"*")
    
    lines.append("")
    
    # Add note about data quality impact (Requirements 5.7)
    critical_issues = []
    if price_source not in ['EODHD', 'Alpha Vantage']:
        critical_issues.append("missing price data")
    if years_available < 7:
        critical_issues.append("insufficient financial history")
    
    if critical_issues:
        lines.append(f"**⚠️ CRITICAL DATA QUALITY ISSUES**: {', '.join(critical_issues).capitalize()}")
        lines.append("These issues significantly impact the reliability of valuation metrics.")
    else:
        lines.append("**Data Quality Summary**: All critical data elements are available for analysis.")
    
    lines.append("")
    lines.append("---")

    # Section 3: Critical Alerts
    lines.append("")
    lines.append("## SECTION 3: CRITICAL ALERTS")
    
    # Combine warnings from financial_data and metrics
    all_warnings = []
    all_warnings.extend(financial_data.get('warnings', []))
    all_warnings.extend(metrics.get('warnings', []))
    
    if not anomalies and not all_warnings:
        lines.append("- No critical data anomalies detected.")
    else:
        for warning in all_warnings:
            lines.append(f"- [!] SYSTEM WARNING: {warning}")
        for alert in anomalies:
            lines.append(f"- [!] DATA ANOMALY: {alert}")
    
    lines.append("")
    lines.append("---")

    # Section 4: Defensive Tests
    lines.append("")
    lines.append("## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS")
    for test, result in metrics['defensive_tests'].items():
        lines.append(f"- {test.replace('_', ' ').title()}: {result}")
    
    lines.append("")
    lines.append("---")
    
    # NEW SECTION: Defensive Investor Verdict (Requirements 6.1-6.5)
    lines.append("")
    lines.append("## GRAHAM DEFENSIVE INVESTOR VERDICT")
    lines.append("")
    
    # Determine if suitable based on test results
    defensive_tests = metrics['defensive_tests']
    failed_tests = []
    
    for test, result in defensive_tests.items():
        # A test fails if it's not PASS and not N/A
        if result != 'PASS' and 'N/A' not in str(result):
            failed_tests.append(test)
    
    # Verdict: SUITABLE if all tests pass (or are N/A for young companies)
    if not failed_tests:
        lines.append("**VERDICT: SUITABLE FOR DEFENSIVE INVESTORS**")
        lines.append("")
        lines.append("This stock meets all of Graham's strict criteria for defensive investors:")
        lines.append("")
        
        # Highlight key strengths (Requirement 6.5)
        for test, result in defensive_tests.items():
            if result == 'PASS':
                lines.append(f"- ✓ {test.replace('_', ' ').title()}")
        
        lines.append("")
        lines.append("**Graham's Guidance**: *\"The defensive investor should confine himself to the shares of important companies with a long record of profitable operations and in strong financial condition.\"*")
        lines.append("")
        lines.append("**Recommendation**: This stock demonstrates the stability, financial strength, and reasonable valuation that Graham prescribed for defensive investors seeking safety and steady returns.")
    else:
        lines.append("**VERDICT: NOT SUITABLE FOR DEFENSIVE INVESTORS**")
        lines.append("")
        lines.append("This stock does not meet Graham's strict criteria for defensive investors.")
        lines.append("")
        lines.append("**Failed Criteria:**")
        
        # List failed criteria with ❌ indicators (Requirements 6.2)
        for test in failed_tests:
            result = defensive_tests[test]
            lines.append(f"- ❌ {test.replace('_', ' ').title()}: {result}")
        
        lines.append("")
        lines.append("**Graham's Guidance**: *\"The defensive investor should confine himself to the shares of important companies with a long record of profitable operations and in strong financial condition.\"*")
        lines.append("")
        
        # Provide clear recommendation (Requirement 6.2, 6.3)
        if len(failed_tests) == 1:
            lines.append("**Recommendation**: This stock fails one of Graham's defensive investor criteria. Defensive investors should avoid this stock and seek companies that meet all seven tests. Enterprising investors may consider this stock if it meets their less stringent criteria (see Enterprising Investor Assessment below).")
        elif len(failed_tests) <= 3:
            lines.append("**Recommendation**: This stock fails multiple Graham defensive investor criteria. Defensive investors should avoid this stock and seek companies with stronger fundamentals and longer track records. Enterprising investors may consider this stock if willing to accept higher risk.")
        else:
            lines.append("**Recommendation**: This stock fails most of Graham's defensive investor tests and is clearly unsuitable for defensive investors seeking safety and stability. Even enterprising investors should proceed with extreme caution.")
    
    lines.append("")
    lines.append("---")
    
    # NEW SECTION: Enterprising Investor Assessment (Requirements 7.1-7.7)
    lines.append("")
    lines.append("## GRAHAM ENTERPRISING INVESTOR ASSESSMENT")
    lines.append("")
    
    # Get data for assessment
    history = financial_data.get('history', {})
    enterprising_tests = metrics.get('enterprising_tests', {})
    
    if history:
        sorted_years = sorted(history.keys(), reverse=True)
        
        # Evaluate recent 3-5 year profitability trends (Requirement 7.2)
        lines.append("### Recent Profitability Trends (Last 3-5 Years):")
        recent_years = sorted_years[:5] if len(sorted_years) >= 5 else sorted_years[:3]
        profitable_years = 0
        recent_net_incomes = []
        
        for year in recent_years:
            net_income = history[year].get('net_income', 0.0)
            recent_net_incomes.append(net_income)
            if net_income > 0:
                profitable_years += 1
        
        if profitable_years == len(recent_years):
            lines.append(f"- ✓ Recent Profitability: {profitable_years} consecutive profitable years ({recent_years[-1].split('-')[0]}-{recent_years[0].split('-')[0]})")
        elif profitable_years >= len(recent_years) * 0.6:
            lines.append(f"- ⚠️ Recent Profitability: {profitable_years} of {len(recent_years)} years profitable ({recent_years[-1].split('-')[0]}-{recent_years[0].split('-')[0]})")
        else:
            lines.append(f"- ❌ Recent Profitability: Only {profitable_years} of {len(recent_years)} years profitable")
        
        # Evaluate current balance sheet strength (Requirement 7.3)
        lines.append("")
        lines.append("### Current Balance Sheet Strength:")
        
        latest_year = sorted_years[0]
        latest_data = history[latest_year]
        
        # Cash position
        cash = latest_data.get('cash', 0.0)
        total_assets = latest_data.get('total_assets', 0.0)
        if cash > 0 and total_assets > 0:
            cash_pct = (cash / total_assets) * 100
            market_cap = financial_data.get('price', 0) * latest_data.get('shares_outstanding', 0)
            if market_cap > 0:
                cash_pct_mc = (cash / market_cap) * 100
                if cash_pct_mc > 30:
                    lines.append(f"- ✓ Cash Position: ${cash:,.0f} {unified_currency} ({cash_pct_mc:.1f}% of market cap)")
                else:
                    lines.append(f"- Cash Position: ${cash:,.0f} {unified_currency} ({cash_pct_mc:.1f}% of market cap)")
            else:
                lines.append(f"- Cash Position: ${cash:,.0f} {unified_currency} ({cash_pct:.1f}% of assets)")
        
        # Debt position
        long_term_debt = latest_data.get('long_term_debt', 0.0)
        if total_assets > 0:
            debt_pct = (long_term_debt / total_assets) * 100
            if debt_pct < 10:
                lines.append(f"- ✓ Debt: ${long_term_debt:,.0f} {unified_currency} (only {debt_pct:.1f}% of assets)")
            elif debt_pct < 30:
                lines.append(f"- Debt: ${long_term_debt:,.0f} {unified_currency} ({debt_pct:.1f}% of assets)")
            else:
                lines.append(f"- ❌ Debt: ${long_term_debt:,.0f} {unified_currency} ({debt_pct:.1f}% of assets - high)")
        
        # Current ratio
        current_assets = latest_data.get('current_assets', 0.0)
        current_liabilities = latest_data.get('current_liabilities', 0.0)
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
            if current_ratio >= 2.0:
                lines.append(f"- ✓ Current Ratio: {current_ratio:.2f}x (strong)")
            elif current_ratio >= 1.5:
                lines.append(f"- ✓ Current Ratio: {current_ratio:.2f}x (adequate for enterprising)")
            else:
                lines.append(f"- ❌ Current Ratio: {current_ratio:.2f}x (below 1.5x minimum)")
        
        # Evaluate recent ROE and ROA trends (Requirement 7.4)
        lines.append("")
        lines.append("### Recent Return Metrics:")
        
        roe = financial_data.get('roe', 0)
        roa = financial_data.get('roa', 0)
        
        if roe > 0:
            if roe > 0.15:
                lines.append(f"- ✓ ROE: {roe*100:.1f}% (strong)")
            elif roe > 0.10:
                lines.append(f"- ✓ ROE: {roe*100:.1f}% (adequate)")
            else:
                lines.append(f"- ⚠️ ROE: {roe*100:.1f}% (below 10%)")
        
        if roa > 0:
            if roa > 0.10:
                lines.append(f"- ✓ ROA: {roa*100:.1f}% (strong)")
            elif roa > 0.05:
                lines.append(f"- ✓ ROA: {roa*100:.1f}% (adequate)")
            else:
                lines.append(f"- ⚠️ ROA: {roa*100:.1f}% (below 5%)")
        
        # Evaluate current valuation (Requirement 7.5)
        lines.append("")
        lines.append("### Current Valuation:")
        
        pe_ratio = financial_data.get('pe_ratio', 0)
        price_to_book = financial_data.get('price_to_book', 0)
        
        if pe_ratio > 0:
            if pe_ratio < 10:
                lines.append(f"- ✓ P/E Ratio: {pe_ratio:.2f}x (attractive)")
            elif pe_ratio < 15:
                lines.append(f"- ✓ P/E Ratio: {pe_ratio:.2f}x (reasonable)")
            else:
                lines.append(f"- ❌ P/E Ratio: {pe_ratio:.2f}x (above Graham's 15x limit)")
        
        if price_to_book > 0:
            if price_to_book < 1.2:
                lines.append(f"- ✓ P/B Ratio: {price_to_book:.2f}x (below enterprising 1.2x limit)")
            elif price_to_book < 1.5:
                lines.append(f"- ⚠️ P/B Ratio: {price_to_book:.2f}x (above enterprising 1.2x, below defensive 1.5x)")
            else:
                lines.append(f"- ❌ P/B Ratio: {price_to_book:.2f}x (above Graham's 1.5x limit)")
        
        lines.append("")
        
        # Determine verdict (Requirements 7.6)
        # Count positive indicators
        positive_indicators = 0
        total_indicators = 0
        
        # Recent profitability
        if profitable_years == len(recent_years):
            positive_indicators += 1
        total_indicators += 1
        
        # Balance sheet strength (current ratio)
        if current_liabilities > 0 and (current_assets / current_liabilities) >= 1.5:
            positive_indicators += 1
        total_indicators += 1
        
        # Debt
        if total_assets > 0 and (long_term_debt / total_assets) < 0.30:
            positive_indicators += 1
        total_indicators += 1
        
        # ROE
        if roe > 0.10:
            positive_indicators += 1
        total_indicators += 1
        
        # Valuation
        if pe_ratio > 0 and pe_ratio < 15:
            positive_indicators += 1
        total_indicators += 1
        
        # Check historical track record
        years_available = len(sorted_years)
        has_short_track_record = years_available < 10
        
        # Determine if suitable
        strength_ratio = positive_indicators / total_indicators if total_indicators > 0 else 0
        
        if strength_ratio >= 0.6 and not has_short_track_record:
            lines.append("**ASSESSMENT: POTENTIAL OPPORTUNITY**")
            lines.append("")
            lines.append("This company shows strong current fundamentals that may interest enterprising investors:")
            lines.append("")
            lines.append("**Key Strengths:**")
            if profitable_years == len(recent_years):
                lines.append(f"- Recent profitability trend ({profitable_years} consecutive years)")
            if current_liabilities > 0 and (current_assets / current_liabilities) >= 1.5:
                lines.append("- Adequate liquidity (current ratio meets enterprising standard)")
            if total_assets > 0 and (long_term_debt / total_assets) < 0.30:
                lines.append("- Conservative debt levels")
            if roe > 0.10:
                lines.append("- Strong return on equity")
            if pe_ratio > 0 and pe_ratio < 15:
                lines.append("- Reasonable valuation")
        elif strength_ratio >= 0.6 and has_short_track_record:
            # Strong current metrics but short history (Requirement 7.7)
            lines.append("**ASSESSMENT: POTENTIAL OPPORTUNITY (WITH CAUTION)**")
            lines.append("")
            lines.append("This company shows strong current fundamentals but has a limited track record:")
            lines.append("")
            lines.append("**Key Strengths:**")
            if profitable_years == len(recent_years):
                lines.append(f"- Recent profitability trend ({profitable_years} consecutive years)")
            if current_liabilities > 0 and (current_assets / current_liabilities) >= 1.5:
                lines.append("- Adequate liquidity")
            if total_assets > 0 and (long_term_debt / total_assets) < 0.30:
                lines.append("- Conservative debt levels")
            if roe > 0.10:
                lines.append("- Strong return on equity")
            
            lines.append("")
            lines.append(f"**⚠️ RISK WARNING**: Company has only {years_available} years of financial history. Graham preferred companies with 10+ year track records to assess performance through full business cycles. Short track records increase uncertainty about how the company will perform during economic downturns.")
        else:
            lines.append("**ASSESSMENT: NOT SUITABLE FOR ENTERPRISING INVESTORS**")
            lines.append("")
            lines.append("This company does not meet the criteria for enterprising investors:")
            lines.append("")
            lines.append("**Concerns:**")
            if profitable_years < len(recent_years):
                lines.append(f"- Inconsistent recent profitability ({profitable_years} of {len(recent_years)} years)")
            if current_liabilities > 0 and (current_assets / current_liabilities) < 1.5:
                lines.append("- Current ratio below 1.5x minimum")
            if total_assets > 0 and (long_term_debt / total_assets) >= 0.30:
                lines.append("- High debt levels")
            if roe <= 0.10:
                lines.append("- Weak return on equity")
            if pe_ratio > 15 or price_to_book > 1.5:
                lines.append("- Valuation above Graham's limits")
        
        lines.append("")
        
        # Include Graham quote (Requirement 7.7)
        lines.append("**Graham's Guidance**: *\"The enterprising investor seeks special situations—bargains, turnarounds, or cyclical companies trading below intrinsic value. Such opportunities require more research and carry higher risk than defensive selections.\"*")
    else:
        lines.append("**ASSESSMENT: NOT SUITABLE**")
        lines.append("")
        lines.append("Insufficient financial data available for enterprising investor assessment.")
    
    lines.append("")
    lines.append("---")
    
    # Section 5: Enterprising Tests
    lines.append("")
    lines.append("## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS")
    for test, result in metrics.get('enterprising_tests', {}).items():
        lines.append(f"- {test.replace('_', ' ').title()}: {result}")
    
    lines.append("")
    lines.append("**Note on Earnings Growth:** Earnings growth is intentionally not required for Enterprising Investors per Graham's methodology. Unlike Defensive Investors (who require 7 tests including ≥33% earnings growth over 10 years), Enterprising Investors require only 6 tests focused on current financial strength and price. Graham's logic: Enterprising investors actively seek bargains, turnarounds, or cyclical companies trading below intrinsic value—situations where historical growth may be absent but current fundamentals and price create opportunity.")
    lines.append("")
    lines.append("---")

    # Section 6: 20-Year Financials Table
    lines.append("")
    lines.append("## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)")
    lines.append(f"*All values in {unified_currency}*")
    lines.append("")
    
    # Determine if dividend data is amounts or counts
    is_dividend_amounts = financial_data.get('is_dividend_amounts', False)
    div_header = "Div/Share" if is_dividend_amounts else "Div Count"
    
    lines.append(f"| Year | Revenue | Net Income | EPS | {div_header} | BVPS |")
    lines.append("|------|---------|------------|-----|-------------|------|")
    
    # Sort years descending - show 20 years for Graham analysis
    history = financial_data.get('history', {})
    sorted_years = sorted(history.keys(), reverse=True)[:20]
    
    for year in sorted_years:
        data = history[year]
        revenue = data.get('revenue', 0.0)
        net_income = data.get('net_income', 0.0)
        eps = data.get('eps', 0.0)
        dividend = data.get('dividend', 0.0)
        
        # Check if this year has actual financial data or just dividend data
        has_financial_data = revenue > 0 or net_income != 0 or eps != 0
        
        # Format values - show "[Data Unavailable]" for years without financial statements
        if not has_financial_data and dividend > 0:
            # Year has dividend but no financial statements yet
            revenue_str = "[Data Unavailable]"
            net_income_str = "[Data Unavailable]"
            eps_str = "[Data Unavailable]"
            dividend_str = str(dividend)
            bvps_str = "[Data Unavailable]"
        else:
            # Normal year with financial data
            revenue_str = str(revenue) if revenue != 0 else 'N/A'
            net_income_str = str(net_income) if net_income != 0 else 'N/A'
            eps_str = str(eps) if eps != 0 else 'N/A'
            dividend_str = str(dividend) if dividend != 0 else 'N/A'
            
            # Calculate BVPS from balance sheet data
            total_equity = data.get('total_equity', 0)
            shares = data.get('shares_outstanding', 0)
            bvps = round(total_equity / shares, 2) if shares > 0 and total_equity > 0 else 'N/A'
            bvps_str = str(bvps)
        
        row = f"| {year} | {revenue_str} | {net_income_str} | {eps_str} | {dividend_str} | {bvps_str} |"
        lines.append(row)
    
    # Add note if showing counts instead of amounts (after the table)
    if not is_dividend_amounts:
        lines.append("")
        lines.append("*Note: Dividend column shows number of payments per year (actual amounts not available from data source)*")

    return "\n".join(lines)

def save_dossier(ticker, content):
    """Saves the Markdown dossier to the data/ directory."""
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{ticker.replace('.', '_')}_DOSSIER.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n[SUCCESS] Dossier generated: {filename}")
    print(f"Action: Upload this file to Perplexity Deep Research.")

def main():
    parser = argparse.ArgumentParser(description="Stock Data Analyser - Financial Analysis Engine")
    parser.add_argument("ticker", type=str, help="Ticker symbol (e.g., AAPL.US, VOD.L)")
    args = parser.parse_args()
    
    ticker = args.ticker.upper()

    if not API_KEY:
        print("[ERROR] EODHD_API_KEY not found in .env file.")
        sys.exit(1)

    print(f"--- Stock Data Analyser Starting for {ticker} ---")

    try:
        # 1. Fetch Data
        print(f"[1/4] Fetching Fundamentals from EODHD...")
        client = EODHDClient(API_KEY, debug=True)
        av_client = AlphaVantageClient(debug=True)
        financial_data = client.fetch_all_data(ticker, av_client=av_client)
        
        # Check if price is available - fatal error if not
        price = financial_data.get('price', 0.0)
        if price == 0.0:
            print("\n" + "="*80)
            print("[FATAL ERROR] Current price unavailable from all sources")
            print("="*80)
            print("\nGraham's Principle: 'No data is better than wrong data.'")
            print("\nThe system cannot generate a reliable valuation without current price data.")
            print("Please verify the ticker symbol or try again later.")
            print("\nData sources attempted:")
            print("  1. EODHD API (Highlights.SharePrice, General.SharePrice, General.LastPrice)")
            print("  2. Alpha Vantage API (GLOBAL_QUOTE)")
            print("\nBoth sources failed to provide current price data.")
            print("="*80 + "\n")
            sys.exit(1)
        
        # 2. Compute Metrics
        print(f"[2/4] Calculating Graham Metrics (Strict Rules)...")
        calculator = GrahamCalculator(financial_data)
        metrics = calculator.compute_all()
        
        # 3. Detect Anomalies (Statistical)
        print(f"[3/4] Scanning for Statistical Anomalies...")
        detector = AnomalyDetector(financial_data)
        anomalies = detector.scan()
        
        # 4. Generate Output
        print(f"[4/4] Generating Dossier...")
        dossier_content = generate_dossier_content(ticker, financial_data, metrics, anomalies)
        save_dossier(ticker, dossier_content)

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to process {ticker}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
