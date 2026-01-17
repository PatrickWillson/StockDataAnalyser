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
    
    # Dossier Header with CEO name
    ceo_name = financial_data.get('ceo_name', 'N/A')
    lines.append(f"# STOCK ANALYSIS DOSSIER: {ticker}")
    lines.append(f"# DATE: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"# SOURCE: EODHD (Tier 1 Data)")
    lines.append(f"# CEO: {ceo_name}")
    lines.append("")
    lines.append("---")
    
    # Section 1: Executive Summary
    lines.append("")
    lines.append("## SECTION 1: EXECUTIVE SUMMARY")
    lines.append(f"- Verdict: **{metrics['verdict']}**")
    lines.append(f"- Intrinsic Value (Graham): {metrics['graham_number']}")
    lines.append(f"- Intrinsic Value (EPV): {metrics['epv']}")
    lines.append(f"- Net-Net Value: {metrics.get('net_net_value', 'N/A')}")
    lines.append(f"- Margin of Safety: {metrics['margin_of_safety']}")
    lines.append(f"- Current Price: {financial_data['price']} {financial_data['currency']}")
    lines.append("")
    lines.append("---")
    
    # Section 2: Critical Alerts
    lines.append("")
    lines.append("## SECTION 2: CRITICAL ALERTS")
    
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

    # Section 3: Defensive Tests
    lines.append("")
    lines.append("## SECTION 3: GRAHAM DEFENSIVE INVESTOR TESTS")
    for test, result in metrics['defensive_tests'].items():
        lines.append(f"- {test.replace('_', ' ').title()}: {result}")
    
    lines.append("")
    lines.append("---")
    
    # Section 4: Enterprising Tests
    lines.append("")
    lines.append("## SECTION 4: GRAHAM ENTERPRISING INVESTOR TESTS")
    for test, result in metrics.get('enterprising_tests', {}).items():
        lines.append(f"- {test.replace('_', ' ').title()}: {result}")
    
    lines.append("")
    lines.append("---")

    # Section 5: 10-Year Financials Table
    lines.append("")
    lines.append("## SECTION 5: 10-YEAR FINANCIALS (STANDARDIZED)")
    lines.append("| Year | Revenue | Net Income | EPS | Div | BVPS |")
    lines.append("|------|---------|------------|-----|-----|------|")
    
    # Sort years descending
    history = financial_data.get('history', {})
    sorted_years = sorted(history.keys(), reverse=True)[:10]
    
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
        client = EODHDClient(API_KEY)
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
