"""
End-to-end tests for expanded 11-column financial history table.

Tests verify that the complete workflow generates the expanded table correctly
with all new columns (Total Debt, Shares Outstanding, Price, P/E, P/B).
"""

import pytest
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clients.factory import ClientFactory
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from output.dossier_generator import DossierGenerator

# Load environment variables
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")


@pytest.mark.live
def test_expanded_table_has_11_columns():
    """
    Test that the financial history table has 13 columns.
    
    Verifies the table header includes all expected columns in correct order.
    Updated to reflect WCPS and Payout Ratio columns added in graham-metrics-enhancement.
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    ticker = "MSFT.US"
    
    # Fetch data and generate dossier
    client = ClientFactory.create_eodhd_client(API_KEY, debug=False)
    yf_client = ClientFactory.create_yfinance_client(debug=False)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Fetch historical prices
    history_keys = list(financial_data.get('history', {}).keys())
    if history_keys:
        oldest_date = min(history_keys)
        newest_date = max(history_keys)
        daily_prices = yf_client.fetch_historical_prices(ticker, start_date=oldest_date, end_date=newest_date)
        
        if daily_prices:
            year_end_prices = yf_client.match_fiscal_year_end_prices(daily_prices, fiscal_year_ends=history_keys)
            for date_key, price_value in year_end_prices.items():
                if date_key in financial_data['history']:
                    financial_data['history'][date_key]['year_end_price'] = price_value
    
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
    dossier = generator.generate()
    
    # Find the table header line
    lines = dossier.split('\n')
    table_header = None
    for line in lines:
        if line.startswith('| Year |') and 'Revenue' in line:
            table_header = line
            break
    
    assert table_header is not None, "Table header not found"
    
    # Count columns (split by |, exclude empty strings)
    columns = [col.strip() for col in table_header.split('|') if col.strip()]
    
    print(f"\nTable columns found: {len(columns)}")
    print(f"Columns: {columns}")
    
    assert len(columns) == 13, f"Expected 13 columns, found {len(columns)}"
    
    # Verify column order (updated with WCPS and Payout Ratio)
    expected_columns = ['Year', 'Revenue', 'Net Income', 'EPS', 'Div/Share', 'BVPS', 
                       'WCPS', 'Payout Ratio', 'Total Debt', 'Shares (B)', 'Price', 'P/E', 'P/B']
    assert columns == expected_columns, f"Column order mismatch. Expected {expected_columns}, got {columns}"


@pytest.mark.live
def test_expanded_table_columns_populated():
    """
    Test that all new columns are populated with data.
    
    Verifies that WCPS, Payout Ratio, Total Debt, Shares, Price, P/E, and P/B columns contain
    actual values (not all N/A or empty).
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    ticker = "MSFT.US"
    
    # Fetch data and generate dossier
    client = ClientFactory.create_eodhd_client(API_KEY, debug=False)
    yf_client = ClientFactory.create_yfinance_client(debug=False)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Fetch historical prices
    history_keys = list(financial_data.get('history', {}).keys())
    if history_keys:
        oldest_date = min(history_keys)
        newest_date = max(history_keys)
        daily_prices = yf_client.fetch_historical_prices(ticker, start_date=oldest_date, end_date=newest_date)
        
        if daily_prices:
            year_end_prices = yf_client.match_fiscal_year_end_prices(daily_prices, fiscal_year_ends=history_keys)
            for date_key, price_value in year_end_prices.items():
                if date_key in financial_data['history']:
                    financial_data['history'][date_key]['year_end_price'] = price_value
    
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
    dossier = generator.generate()
    
    # Find table rows
    lines = dossier.split('\n')
    table_rows = []
    in_table = False
    
    for line in lines:
        if '| Year |' in line and 'Revenue' in line:
            in_table = True
            continue
        if in_table and line.startswith('|') and '---' not in line:
            table_rows.append(line)
        elif in_table and not line.startswith('|'):
            break
    
    assert len(table_rows) > 0, "No table rows found"
    
    # Check that new columns have data (updated column indices for 13 columns)
    wcps_values = []
    payout_ratio_values = []
    debt_values = []
    shares_values = []
    price_values = []
    pe_values = []
    pb_values = []
    
    for row in table_rows:
        cols = [col.strip() for col in row.split('|') if col.strip()]
        if len(cols) >= 13:
            wcps_values.append(cols[6])  # WCPS
            payout_ratio_values.append(cols[7])  # Payout Ratio
            debt_values.append(cols[8])  # Total Debt
            shares_values.append(cols[9])  # Shares (B)
            price_values.append(cols[10])  # Price
            pe_values.append(cols[11])  # P/E
            pb_values.append(cols[12])  # P/B
    
    print(f"\nRows analyzed: {len(table_rows)}")
    print(f"Sample WCPS values: {wcps_values[:3]}")
    print(f"Sample payout ratio values: {payout_ratio_values[:3]}")
    print(f"Sample debt values: {debt_values[:3]}")
    print(f"Sample shares values: {shares_values[:3]}")
    print(f"Sample price values: {price_values[:3]}")
    print(f"Sample P/E values: {pe_values[:3]}")
    print(f"Sample P/B values: {pb_values[:3]}")
    
    # At least 80% of rows should have WCPS data
    wcps_populated = sum(1 for v in wcps_values if v not in ['N/A', '[Data Unavailable]'])
    assert wcps_populated / len(wcps_values) >= 0.8, f"Only {wcps_populated}/{len(wcps_values)} rows have WCPS data"
    
    # At least 80% of rows should have payout ratio data
    payout_populated = sum(1 for v in payout_ratio_values if v not in ['N/A', '[Data Unavailable]'])
    assert payout_populated / len(payout_ratio_values) >= 0.8, f"Only {payout_populated}/{len(payout_ratio_values)} rows have payout ratio data"
    
    # At least 80% of rows should have debt data (not N/A or [Data Unavailable])
    debt_populated = sum(1 for v in debt_values if v not in ['N/A', '[Data Unavailable]'])
    assert debt_populated / len(debt_values) >= 0.8, f"Only {debt_populated}/{len(debt_values)} rows have debt data"
    
    # At least 80% of rows should have shares data
    shares_populated = sum(1 for v in shares_values if v not in ['N/A', '[Data Unavailable]'])
    assert shares_populated / len(shares_values) >= 0.8, f"Only {shares_populated}/{len(shares_values)} rows have shares data"
    
    # At least 70% of rows should have price data (some gaps acceptable)
    price_populated = sum(1 for v in price_values if v not in ['N/A', '[Data Unavailable]'])
    assert price_populated / len(price_values) >= 0.7, f"Only {price_populated}/{len(price_values)} rows have price data"
    
    # At least 70% of rows should have P/E data
    pe_populated = sum(1 for v in pe_values if v not in ['N/A', '[Data Unavailable]'])
    assert pe_populated / len(pe_values) >= 0.7, f"Only {pe_populated}/{len(pe_values)} rows have P/E data"
    
    # At least 70% of rows should have P/B data
    pb_populated = sum(1 for v in pb_values if v not in ['N/A', '[Data Unavailable]'])
    assert pb_populated / len(pb_values) >= 0.7, f"Only {pb_populated}/{len(pb_values)} rows have P/B data"


@pytest.mark.live
def test_pe_column_shows_negative_for_losses():
    """
    Test that P/E column shows "Negative" for loss years.
    
    This is Graham's methodology: show losses explicitly, don't hide them.
    We'll use a company known to have loss years.
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    # Use a ticker that might have loss years (or create synthetic data)
    # For now, we'll verify the logic works by checking MSFT's 2018 data
    # (which had lower earnings due to tax reform)
    
    ticker = "MSFT.US"
    
    # Fetch data and generate dossier
    client = ClientFactory.create_eodhd_client(API_KEY, debug=False)
    yf_client = ClientFactory.create_yfinance_client(debug=False)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Manually inject a loss year for testing
    history = financial_data.get('history', {})
    if history:
        # Find a year and make it a loss year
        test_year = sorted(history.keys(), reverse=True)[5]  # Pick 6th most recent year
        history[test_year]['eps'] = -2.5  # Make it a loss
        history[test_year]['year_end_price'] = 100.0  # Set a price
    
    # Fetch historical prices
    history_keys = list(financial_data.get('history', {}).keys())
    if history_keys:
        oldest_date = min(history_keys)
        newest_date = max(history_keys)
        daily_prices = yf_client.fetch_historical_prices(ticker, start_date=oldest_date, end_date=newest_date)
        
        if daily_prices:
            year_end_prices = yf_client.match_fiscal_year_end_prices(daily_prices, fiscal_year_ends=history_keys)
            for date_key, price_value in year_end_prices.items():
                if date_key in financial_data['history']:
                    # Don't overwrite our test year
                    if date_key != test_year:
                        financial_data['history'][date_key]['year_end_price'] = price_value
    
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
    dossier = generator.generate()
    
    # Check that "Negative" appears in the dossier
    assert "Negative" in dossier, "Expected 'Negative' to appear in P/E column for loss year"
    
    print("\n✓ 'Negative' found in dossier for loss year (Graham's methodology)")


@pytest.mark.live
def test_graham_trend_analysis_documentation_present():
    """
    Test that Graham Trend Analysis documentation is present in dossier.
    
    Verifies that the new columns are explained with Graham's reasoning.
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    ticker = "MSFT.US"
    
    # Fetch data and generate dossier
    client = ClientFactory.create_eodhd_client(API_KEY, debug=False)
    yf_client = ClientFactory.create_yfinance_client(debug=False)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Fetch historical prices
    history_keys = list(financial_data.get('history', {}).keys())
    if history_keys:
        oldest_date = min(history_keys)
        newest_date = max(history_keys)
        daily_prices = yf_client.fetch_historical_prices(ticker, start_date=oldest_date, end_date=newest_date)
        
        if daily_prices:
            year_end_prices = yf_client.match_fiscal_year_end_prices(daily_prices, fiscal_year_ends=history_keys)
            for date_key, price_value in year_end_prices.items():
                if date_key in financial_data['history']:
                    financial_data['history'][date_key]['year_end_price'] = price_value
    
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
    dossier = generator.generate()
    
    # Check for documentation section
    assert "Graham Trend Analysis Columns:" in dossier, "Graham Trend Analysis documentation not found"
    
    # Check that all 5 new columns are documented
    assert "**Total Debt**:" in dossier, "Total Debt documentation not found"
    assert "**Shares (B)**:" in dossier, "Shares documentation not found"
    assert "**Price**:" in dossier, "Price documentation not found"
    assert "**P/E**:" in dossier, "P/E documentation not found"
    assert "**P/B**:" in dossier, "P/B documentation not found"
    
    # Check for Graham's reasoning
    assert "Graham emphasized" in dossier, "Graham's reasoning not mentioned"
    assert "retained earnings vs leverage" in dossier, "Debt reasoning not explained"
    assert "dilution" in dossier or "buyback" in dossier, "Shares reasoning not explained"
    
    # Check for currency conversion note
    assert "Historical prices converted" in dossier or "current FX rates" in dossier, "Currency conversion note not found"
    
    print("\n✓ All Graham Trend Analysis documentation present")


@pytest.mark.live
def test_table_markdown_syntax_valid():
    """
    Test that the table has valid markdown syntax.
    
    Verifies that all rows have the same number of columns as the header.
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    ticker = "MSFT.US"
    
    # Fetch data and generate dossier
    client = ClientFactory.create_eodhd_client(API_KEY, debug=False)
    yf_client = ClientFactory.create_yfinance_client(debug=False)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Fetch historical prices
    history_keys = list(financial_data.get('history', {}).keys())
    if history_keys:
        oldest_date = min(history_keys)
        newest_date = max(history_keys)
        daily_prices = yf_client.fetch_historical_prices(ticker, start_date=oldest_date, end_date=newest_date)
        
        if daily_prices:
            year_end_prices = yf_client.match_fiscal_year_end_prices(daily_prices, fiscal_year_ends=history_keys)
            for date_key, price_value in year_end_prices.items():
                if date_key in financial_data['history']:
                    financial_data['history'][date_key]['year_end_price'] = price_value
    
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
    dossier = generator.generate()
    
    # Find table lines
    lines = dossier.split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        if '| Year |' in line and 'Revenue' in line:
            in_table = True
        if in_table and line.startswith('|'):
            table_lines.append(line)
        elif in_table and not line.startswith('|'):
            break
    
    assert len(table_lines) > 2, "Table should have header, separator, and data rows"
    
    # Count columns in each line
    header_cols = len([c for c in table_lines[0].split('|') if c.strip()])
    
    for i, line in enumerate(table_lines):
        cols = len([c for c in line.split('|') if c.strip()])
        assert cols == header_cols, f"Row {i} has {cols} columns, expected {header_cols}"
    
    print(f"\n✓ All {len(table_lines)} table rows have {header_cols} columns (valid markdown)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
