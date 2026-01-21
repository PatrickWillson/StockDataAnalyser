"""
Golden Baseline Tests for Refactoring Validation

These tests capture the exact output of the system before refactoring
and verify that refactored code produces byte-for-byte identical output.

Requirements: 7.9, 7.10 - Preserve deterministic output
"""

import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clients.eodhd_client import EODHDClient
from clients.yfinance_client import YFinanceClient
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from output.dossier_generator import DossierGenerator

# Golden test tickers - diverse set covering different exchanges and scenarios
GOLDEN_TICKERS = ["AAPL.US", "YU.LSE", "RY.TO"]

# Directory for golden baseline files
GOLDEN_DIR = Path(__file__).parent / "golden"


def get_api_key():
    """Get EODHD API key from environment."""
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("EODHD_API_KEY")
    if not api_key:
        pytest.skip("EODHD_API_KEY not found in environment")
    return api_key


def run_analysis(ticker: str) -> str:
    """
    Run complete analysis for a ticker and return dossier content.
    
    This function replicates the main workflow from stock_data_analyser.py
    to ensure we're testing the exact same code path.
    
    Args:
        ticker: Ticker symbol (e.g., 'AAPL.US')
        
    Returns:
        Complete dossier content as string
    """
    api_key = get_api_key()
    
    # Step 1: Fetch data
    client = EODHDClient(api_key, debug=False)
    yf_client = YFinanceClient(debug=False)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Check if price is available
    price = financial_data.get('price', 0.0)
    if price == 0.0:
        pytest.skip(f"Price unavailable for {ticker} - cannot generate baseline")
    
    # Step 2: Calculate metrics
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    # Step 3: Detect anomalies
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Step 4: Generate dossier
    generator = DossierGenerator(ticker, financial_data, metrics, anomalies)
    dossier_content = generator.generate()
    
    return dossier_content


@pytest.mark.golden
@pytest.mark.live
def test_capture_baseline():
    """
    Capture baseline dossier output before refactoring.
    
    This test should be run ONCE before starting the refactoring process.
    It saves the current output to golden files that will be used for
    comparison after refactoring.
    
    Usage:
        pytest tests/test_golden_baseline.py::test_capture_baseline -v -m golden
    
    Requirements: 7.9 - Create golden test baseline
    """
    # Create golden directory if it doesn't exist
    GOLDEN_DIR.mkdir(exist_ok=True)
    
    print("\n" + "="*80)
    print("CAPTURING GOLDEN BASELINE - Run this BEFORE refactoring")
    print("="*80)
    
    for ticker in GOLDEN_TICKERS:
        print(f"\nProcessing {ticker}...")
        
        try:
            # Run analysis
            output = run_analysis(ticker)
            
            # Save to golden file
            golden_path = GOLDEN_DIR / f"{ticker.replace('.', '_')}_baseline.md"
            golden_path.write_text(output, encoding='utf-8')
            
            print(f"✓ Saved baseline for {ticker} ({len(output)} bytes)")
            print(f"  Location: {golden_path}")
            
        except Exception as e:
            print(f"✗ Failed to capture baseline for {ticker}: {str(e)}")
            # Don't fail the test - we want to capture as many as possible
            continue
    
    print("\n" + "="*80)
    print("BASELINE CAPTURE COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Verify golden files were created in tests/golden/")
    print("2. Review the content to ensure it looks correct")
    print("3. Commit the golden files to version control")
    print("4. Begin refactoring")
    print("5. Run test_verify_output_unchanged to validate refactoring")
    print("="*80 + "\n")


@pytest.mark.golden
@pytest.mark.live
def test_verify_output_unchanged():
    """
    Verify refactored output matches baseline exactly (byte-for-byte).
    
    This test should be run AFTER refactoring to ensure no behavioral changes.
    It compares current output against the golden baseline files.
    
    Usage:
        pytest tests/test_golden_baseline.py::test_verify_output_unchanged -v -m golden
    
    Requirements: 7.10 - Verify output matches baseline exactly
    """
    # Check if golden files exist
    if not GOLDEN_DIR.exists():
        pytest.fail(
            "Golden baseline directory not found. "
            "Run test_capture_baseline first to create baseline files."
        )
    
    print("\n" + "="*80)
    print("VERIFYING OUTPUT AGAINST GOLDEN BASELINE")
    print("="*80)
    
    all_passed = True
    results = []
    
    for ticker in GOLDEN_TICKERS:
        print(f"\nVerifying {ticker}...")
        
        # Load golden file
        golden_path = GOLDEN_DIR / f"{ticker.replace('.', '_')}_baseline.md"
        
        if not golden_path.exists():
            print(f"✗ Golden baseline not found for {ticker}")
            print(f"  Expected: {golden_path}")
            all_passed = False
            results.append((ticker, "MISSING_BASELINE", None))
            continue
        
        try:
            expected = golden_path.read_text(encoding='utf-8')
            
            # Run analysis with current code
            actual = run_analysis(ticker)
            
            # Byte-for-byte comparison
            if actual == expected:
                print(f"✓ Output matches baseline ({len(actual)} bytes)")
                results.append((ticker, "PASS", None))
            else:
                print(f"✗ Output differs from baseline")
                print(f"  Expected: {len(expected)} bytes")
                print(f"  Actual:   {len(actual)} bytes")
                
                # Find first difference for debugging
                for i, (c1, c2) in enumerate(zip(expected, actual)):
                    if c1 != c2:
                        context_start = max(0, i - 50)
                        context_end = min(len(expected), i + 50)
                        print(f"\n  First difference at position {i}:")
                        print(f"  Expected: ...{repr(expected[context_start:context_end])}...")
                        print(f"  Actual:   ...{repr(actual[context_start:context_end])}...")
                        break
                
                all_passed = False
                results.append((ticker, "FAIL", f"Output differs at position {i}"))
                
        except Exception as e:
            print(f"✗ Error running analysis: {str(e)}")
            all_passed = False
            results.append((ticker, "ERROR", str(e)))
    
    # Print summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    for ticker, status, detail in results:
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"{status_symbol} {ticker}: {status}")
        if detail:
            print(f"  {detail}")
    
    print("="*80 + "\n")
    
    # Fail test if any ticker failed
    if not all_passed:
        pytest.fail(
            "Output verification failed. Refactoring has introduced behavioral changes. "
            "Review the differences above and fix the refactored code."
        )


@pytest.mark.golden
def test_golden_files_exist():
    """
    Verify that golden baseline files exist and are not empty.
    
    This is a quick sanity check that can be run without API calls.
    
    Requirements: 7.9 - Verify golden files are created
    """
    if not GOLDEN_DIR.exists():
        pytest.skip("Golden baseline directory not found - run test_capture_baseline first")
    
    for ticker in GOLDEN_TICKERS:
        golden_path = GOLDEN_DIR / f"{ticker.replace('.', '_')}_baseline.md"
        
        assert golden_path.exists(), f"Golden baseline file not found for {ticker}: {golden_path}"
        
        content = golden_path.read_text(encoding='utf-8')
        assert len(content) > 0, f"Golden baseline file is empty for {ticker}"
        assert f"STOCK ANALYSIS DOSSIER: {ticker}" in content, \
            f"Golden baseline file does not contain expected header for {ticker}"
        
        print(f"✓ {ticker}: {len(content)} bytes")


@pytest.mark.golden
def test_golden_files_contain_expected_sections():
    """
    Verify that golden baseline files contain all expected sections.
    
    This validates that the baseline capture was successful and complete.
    
    Requirements: 7.9 - Verify golden files contain expected content
    """
    if not GOLDEN_DIR.exists():
        pytest.skip("Golden baseline directory not found - run test_capture_baseline first")
    
    # Expected sections in every dossier
    expected_sections = [
        "STOCK ANALYSIS DOSSIER:",
        "EXECUTIVE SUMMARY",
        "KEY METRICS",
        "RISK FACTORS",
        "METHODOLOGY NOTES",
        "Data Quality & Limitations",  # Match actual section name (title case)
        "CRITICAL ALERTS",
        "DEFENSIVE INVESTOR TESTS",
        "ENTERPRISING INVESTOR TESTS",
        "20-YEAR FINANCIALS"
    ]
    
    for ticker in GOLDEN_TICKERS:
        golden_path = GOLDEN_DIR / f"{ticker.replace('.', '_')}_baseline.md"
        
        if not golden_path.exists():
            pytest.skip(f"Golden baseline not found for {ticker}")
        
        content = golden_path.read_text(encoding='utf-8')
        
        print(f"\nVerifying sections in {ticker}:")
        for section in expected_sections:
            assert section in content, \
                f"Golden baseline for {ticker} missing section: {section}"
            print(f"  ✓ {section}")


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    print("Golden Baseline Test Suite")
    print("=" * 80)
    print("\nTo capture baseline:")
    print("  pytest tests/test_golden_baseline.py::test_capture_baseline -v -m golden")
    print("\nTo verify after refactoring:")
    print("  pytest tests/test_golden_baseline.py::test_verify_output_unchanged -v -m golden")
    print("\nTo check golden files exist:")
    print("  pytest tests/test_golden_baseline.py::test_golden_files_exist -v -m golden")
    print("=" * 80)
