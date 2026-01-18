import argparse
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Import Core Modules (You will create these next)
from clients.eodhd_client import EODHDClient
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")

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
        lines.append(f"- Intrinsic Value (Graham): {graham_str} {unified_currency}")
    else:
        lines.append(f"- Intrinsic Value (Graham): {graham_str}")
    
    if epv_str != 'N/A':
        lines.append(f"- Intrinsic Value (EPV): {epv_str} {unified_currency}")
    else:
        lines.append(f"- Intrinsic Value (EPV): {epv_str}")
    
    if net_net_str != 'N/A':
        lines.append(f"- Net-Net Value: {net_net_str} {unified_currency}")
    else:
        lines.append(f"- Net-Net Value: {net_net_str}")
    
    lines.append(f"- Margin of Safety: {metrics['margin_of_safety']}")
    lines.append(f"- Current Price: {financial_data['price']:.2f} {unified_currency}")
    
    # Price ranges
    week_52_high = financial_data.get('week_52_high', 0)
    week_52_low = financial_data.get('week_52_low', 0)
    if week_52_high > 0 and week_52_low > 0:
        # Note: These are still in original currency from API
        lines.append(f"- 52-Week Range: {week_52_low:.2f} - {week_52_high:.2f} {original_stock_currency}")
    
    # Dividend information - use Forward Annual Dividend Rate as best proxy for trailing
    # (API's "Forward" rate often represents most recent trailing 12 months)
    forward_div = financial_data.get('forward_dividend_rate')
    
    if forward_div and forward_div > 0:
        actual_yield = (forward_div / financial_data['price']) * 100
        lines.append(f"- Trailing Dividend: {forward_div:.4f} {unified_currency} (Yield: {actual_yield:.2f}%)")
    
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
                lines.append(f"- Book Value Per Share: {book_value:.2f} {unified_currency}")
    
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
        lines.append(f"- **P/E Ratio ({pe_ratio:.2f})**: Current Price / Most Recent Annual EPS")
        lines.append(f"  - Calculated from audited financials, not API pre-calculated ratios")
        lines.append(f"  - EPS: ${most_recent_eps:.2f} {unified_currency} (Net Income / Shares Outstanding)")
    
    graham_number = metrics.get('graham_number', 0)
    if isinstance(graham_number, (int, float)) and graham_number > 0:
        lines.append(f"- **Graham Number (${graham_number:.2f})**: √(22.5 × EPS × BVPS)")
        lines.append(f"  - Conservative intrinsic value estimate")
        lines.append(f"  - Based on Benjamin Graham's formula from 'The Intelligent Investor'")
    
    if epv_value > 0:
        lines.append(f"- **EPV - Earnings Power Value (${epv_value:,.0f})**: {years_used}-Year Avg Net Income / {cost_of_capital:.0%} Cost of Capital")
        lines.append(f"  - Represents enterprise value based on normalized earnings")
        if epv_per_share > 0:
            lines.append(f"  - Per share: ${epv_per_share:.2f} {unified_currency}")
        if normalized_earnings > 0:
            lines.append(f"  - Normalized earnings: ${normalized_earnings:,.0f} {unified_currency}")
        lines.append(f"  - Uses {years_used}-year average to smooth cyclical volatility")
    
    net_net = metrics.get('net_net_value', 0)
    if isinstance(net_net, (int, float)) and net_net > 0:
        lines.append(f"- **Net-Net Value (${net_net:.2f})**: (Current Assets - Total Liabilities) / Shares")
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
    lines.append("- **52-Week Range**: May reflect stale data; verify against live sources for trading decisions")
    lines.append("- **Quarterly Data**: Not included in analysis; annual data only per Graham methodology")
    lines.append("- **Forward Estimates**: Not included; analysis based on historical audited financials only")
    lines.append("- **Pre-calculated Ratios**: System recalculates all metrics from source data rather than using API's pre-calculated values")
    
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
    
    # Section 5: Enterprising Tests
    lines.append("")
    lines.append("## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS")
    for test, result in metrics.get('enterprising_tests', {}).items():
        lines.append(f"- {test.replace('_', ' ').title()}: {result}")
    
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
        revenue = data.get('revenue', 'N/A')
        net_income = data.get('net_income', 'N/A')
        eps = data.get('eps', 'N/A')
        dividend = data.get('dividend', 'N/A')
        
        # Calculate BVPS from balance sheet data
        total_equity = data.get('total_equity', 0)
        shares = data.get('shares_outstanding', 0)
        bvps = round(total_equity / shares, 2) if shares > 0 else 'N/A'
        
        row = f"| {year} | {revenue} | {net_income} | {eps} | {dividend} | {bvps} |"
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
        financial_data = client.fetch_all_data(ticker)
        
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
