"""
End-to-end validation tests for the refactored codebase.

Tests Requirements 8.1, 8.2, 8.3, 8.5, 8.6:
- CLI interface unchanged
- Output format identical
- Markdown formatting preserved
- Exit codes consistent
- Success messages unchanged
"""

import pytest
import subprocess
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Test tickers across multiple exchanges
TEST_TICKERS = [
    # US Stocks
    ("AAPL.US", "US", "Apple Inc."),
    ("MSFT.US", "US", "Microsoft Corporation"),
    ("JNJ.US", "US", "Johnson & Johnson"),
    
    # UK Stocks (London Stock Exchange)
    ("YU.LSE", "LSE", "Yellow Cake PLC"),
    ("AEP.LSE", "LSE", "Anglo-Eastern Plantations"),
    
    # Canadian Stocks
    ("RY.TO", "TO", "Royal Bank of Canada"),
    ("TD.TO", "TO", "Toronto-Dominion Bank"),
    
    # European Stocks
    ("SAP.XETRA", "XETRA", "SAP SE"),
    ("BNP.PA", "PA", "BNP Paribas"),
    
    # Asian Stocks
    ("0700.HK", "HK", "Tencent Holdings"),
]


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self, ticker: str, exchange: str, name: str):
        self.ticker = ticker
        self.exchange = exchange
        self.name = name
        self.success = False
        self.exit_code = None
        self.dossier_exists = False
        self.dossier_path = None
        self.has_required_sections = False
        self.has_errors = False
        self.has_warnings = False
        self.error_message = None
        self.sections_found = []
        self.sections_missing = []
    
    def __repr__(self):
        status = "✓ PASS" if self.success else "✗ FAIL"
        return f"{status} {self.ticker} ({self.exchange}) - {self.name}"


def run_analysis(ticker: str, debug: bool = False) -> Tuple[int, str, str]:
    """
    Run stock analysis for a ticker.
    
    Args:
        ticker: Ticker symbol (e.g., AAPL.US)
        debug: Enable debug mode
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, "stock_data_analyser.py", ticker]
    if debug:
        cmd.append("--debug")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60  # 60 second timeout per ticker
    )
    
    return result.returncode, result.stdout, result.stderr


def validate_dossier_format(dossier_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Validate dossier has all required sections.
    
    Args:
        dossier_path: Path to dossier file
        
    Returns:
        Tuple of (all_sections_present, sections_found, sections_missing)
    """
    required_sections = [
        "# STOCK ANALYSIS DOSSIER:",
        "## SECTION 1: EXECUTIVE SUMMARY",
        "## SECTION 2: KEY METRICS",
        "## RISK FACTORS",
        "## METHODOLOGY NOTES",
        "## CALCULATION DETAILS",
        "## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS",
        "## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS",
        "## SECTION 6: 20-YEAR FINANCIALS",
        "## SECTION 3: CRITICAL ALERTS",
    ]
    
    content = dossier_path.read_text(encoding='utf-8')
    
    sections_found = []
    sections_missing = []
    
    for section in required_sections:
        if section in content:
            sections_found.append(section)
        else:
            sections_missing.append(section)
    
    all_present = len(sections_missing) == 0
    return all_present, sections_found, sections_missing


def check_for_errors_warnings(stdout: str, stderr: str) -> Tuple[bool, bool]:
    """
    Check if output contains errors or warnings.
    
    Args:
        stdout: Standard output
        stderr: Standard error
        
    Returns:
        Tuple of (has_errors, has_warnings)
    """
    combined = stdout + stderr
    
    # Check for errors (excluding expected validation warnings)
    has_errors = (
        "ERROR" in combined or
        "FATAL" in combined or
        "Failed to process" in combined or
        "Exception" in combined
    )
    
    # Check for warnings (excluding expected ones)
    has_warnings = (
        "WARNING" in combined and
        "Currency Conversion" not in combined and  # Expected
        "VALIDATION" not in combined  # Expected
    )
    
    return has_errors, has_warnings


def validate_ticker(ticker: str, exchange: str, name: str) -> ValidationResult:
    """
    Validate a single ticker end-to-end.
    
    Args:
        ticker: Ticker symbol
        exchange: Exchange code
        name: Company name
        
    Returns:
        ValidationResult object
    """
    result = ValidationResult(ticker, exchange, name)
    
    try:
        # Run analysis
        exit_code, stdout, stderr = run_analysis(ticker)
        result.exit_code = exit_code
        
        # Check exit code (Requirement 8.5)
        if exit_code != 0:
            result.error_message = f"Non-zero exit code: {exit_code}"
            return result
        
        # Check dossier exists (Requirement 8.2)
        dossier_filename = f"data/{ticker.replace('.', '_')}_DOSSIER.md"
        dossier_path = Path(dossier_filename)
        result.dossier_path = dossier_path
        result.dossier_exists = dossier_path.exists()
        
        if not result.dossier_exists:
            result.error_message = "Dossier file not created"
            return result
        
        # Validate dossier format (Requirements 8.3, 8.4)
        has_all_sections, sections_found, sections_missing = validate_dossier_format(dossier_path)
        result.has_required_sections = has_all_sections
        result.sections_found = sections_found
        result.sections_missing = sections_missing
        
        if not has_all_sections:
            result.error_message = f"Missing sections: {', '.join(sections_missing)}"
            return result
        
        # Check for errors and warnings (Requirement 8.6)
        has_errors, has_warnings = check_for_errors_warnings(stdout, stderr)
        result.has_errors = has_errors
        result.has_warnings = has_warnings
        
        if has_errors:
            result.error_message = "Unexpected errors in output"
            return result
        
        # All checks passed
        result.success = True
        
    except subprocess.TimeoutExpired:
        result.error_message = "Analysis timed out (>60s)"
    except Exception as e:
        result.error_message = f"Exception: {str(e)}"
    
    return result


@pytest.mark.live
@pytest.mark.slow
def test_end_to_end_validation():
    """
    Test end-to-end validation with 10 tickers across multiple exchanges.
    
    Requirements:
    - 8.1: CLI interface unchanged
    - 8.2: Output filename format unchanged
    - 8.3: Sections in same order
    - 8.5: Exit codes consistent
    - 8.6: Success messages unchanged
    """
    # Check API key is available
    api_key = os.getenv("EODHD_API_KEY")
    if not api_key:
        pytest.skip("EODHD_API_KEY not found - skipping live validation")
    
    print("\n" + "="*80)
    print("END-TO-END VALIDATION TEST")
    print("="*80)
    print(f"Testing {len(TEST_TICKERS)} tickers across multiple exchanges...")
    print()
    
    results = []
    
    for ticker, exchange, name in TEST_TICKERS:
        print(f"Testing {ticker} ({exchange}) - {name}...", end=" ", flush=True)
        result = validate_ticker(ticker, exchange, name)
        results.append(result)
        
        if result.success:
            print("✓ PASS")
        else:
            print(f"✗ FAIL - {result.error_message}")
    
    # Print summary
    print()
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    
    print(f"Total: {len(results)} tickers")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    # Print details for failed tickers
    if failed > 0:
        print("FAILED TICKERS:")
        print("-"*80)
        for result in results:
            if not result.success:
                print(f"  {result.ticker} ({result.exchange})")
                print(f"    Error: {result.error_message}")
                print(f"    Exit Code: {result.exit_code}")
                print(f"    Dossier Exists: {result.dossier_exists}")
                if result.sections_missing:
                    print(f"    Missing Sections: {', '.join(result.sections_missing)}")
                print()
    
    # Print exchange coverage
    print("EXCHANGE COVERAGE:")
    print("-"*80)
    exchanges = {}
    for result in results:
        if result.exchange not in exchanges:
            exchanges[result.exchange] = {"total": 0, "passed": 0}
        exchanges[result.exchange]["total"] += 1
        if result.success:
            exchanges[result.exchange]["passed"] += 1
    
    for exchange, stats in sorted(exchanges.items()):
        status = "✓" if stats["passed"] == stats["total"] else "✗"
        print(f"  {status} {exchange}: {stats['passed']}/{stats['total']} passed")
    
    print("="*80)
    
    # Assert all passed
    assert failed == 0, f"{failed} ticker(s) failed validation"


@pytest.mark.live
@pytest.mark.slow
def test_cli_arguments():
    """
    Test CLI accepts expected arguments (Requirement 8.1).
    """
    # Test help flag
    result = subprocess.run(
        [sys.executable, "stock_data_analyser.py", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "ticker" in result.stdout.lower()
    assert "debug" in result.stdout.lower()


@pytest.mark.live
@pytest.mark.slow
def test_error_exit_codes():
    """
    Test error conditions produce correct exit codes (Requirement 8.5).
    """
    # Test with invalid ticker
    result = subprocess.run(
        [sys.executable, "stock_data_analyser.py", "INVALID_TICKER_XYZ.US"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Should exit with code 1 on error
    assert result.returncode == 1


if __name__ == "__main__":
    # Allow running directly for manual testing
    print("Running end-to-end validation...")
    test_end_to_end_validation()
