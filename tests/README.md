# Test Suite - Stock Data Analyser

## Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_fixtures.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Skip live API tests (already skipped by default)
pytest tests/ -v -m "not live"
```

## Test Statistics

- **Total Tests**: 198
- **Passing**: 195
- **Skipped**: 3 (intentional live API tests)
- **Execution Time**: ~11 seconds
- **API Calls Made**: 0 (all mocked)

## Test Structure

```
tests/
├── fixtures.py                    # Reusable mock data (400+ lines)
├── capture_api_responses.py       # Helper to capture real API responses
├── TESTING_GUIDE.md               # Comprehensive testing documentation
├── README.md                      # This file
│
├── test_fixtures.py               # Tests for fixtures module (15 tests)
│
├── test_*_properties.py           # Property-based tests (Hypothesis)
│   ├── test_anomaly_detector_properties.py
│   ├── test_currency_display_properties.py
│   ├── test_dividend_properties.py
│   ├── test_dossier_properties.py
│   ├── test_eodhd_client_properties.py
│   ├── test_graham_calculator_properties.py
│   ├── test_main_cli_properties.py
│   ├── test_price_fallback_properties.py
│   └── test_yfinance_properties.py
│
├── test_*_integration.py          # Integration tests (mocked)
│   ├── test_dividend_display_integration.py
│   └── test_eodhd_client_integration.py
│
├── test_end_to_end.py             # End-to-end workflow tests
│
└── test_*.py                      # Unit tests
    ├── test_currency_display.py
    ├── test_defensive_verdict.py
    ├── test_dividend_api.py
    ├── test_dividend_calculation.py
    ├── test_dividend_currency_fix.py
    ├── test_dividend_display.py
    ├── test_dossier_file_saving.py
    ├── test_enterprising_investor.py
    ├── test_epv_methodology.py
    ├── test_epv_normalized.py
    ├── test_future_year_dividend.py
    ├── test_fx_client.py
    ├── test_fx_client_live.py (skipped)
    ├── test_main_cli.py
    ├── test_price_fallback.py
    ├── test_shares_by_year_fix.py
    └── test_yfinance_client.py
```

## Key Features

### ✅ Zero Real API Calls

All tests use mocks - no network requests are made:

- **EODHD API**: Mocked with `unittest.mock.patch`
- **yfinance**: Mocked Ticker objects for both prices and FX rates

### ✅ Fast Execution

- Complete test suite runs in ~11 seconds
- No network latency
- No API rate limits
- No quota consumption

### ✅ Deterministic

- Same input always produces same output
- No flaky tests
- Reliable CI/CD integration

### ✅ Comprehensive Coverage

Tests cover:
- Unit tests for individual functions
- Integration tests for component interaction
- Property-based tests for universal properties
- End-to-end tests for complete workflows
- Edge cases (negative values, missing data, API errors)

## Using Fixtures

### Import Fixtures

```python
from tests.fixtures import (
    EODHDFixtures,
    YFinanceFixtures,
    FXFixtures,
    create_mock_http_response,
    create_financial_data_dict
)
```

### Example: Mock EODHD API

```python
from unittest.mock import patch
from tests.fixtures import EODHDFixtures, create_mock_http_response

def test_fetch_data():
    client = EODHDClient("test_key")
    mock_data = EODHDFixtures.get_aapl_fundamentals()
    mock_response = create_mock_http_response(200, mock_data)
    
    with patch.object(client.session, 'get', return_value=mock_response):
        result = client.fetch_all_data('AAPL.US')
    
    assert result['ticker'] == 'AAPL'
```

### Example: Mock yfinance

```python
from tests.fixtures import YFinanceFixtures

def test_price_fetch():
    mock_ticker = YFinanceFixtures.get_ticker_mock(price=150.0)
    
    # Use mock in your test
    assert mock_ticker.fast_info.last_price == 150.0
```

### Example: Mock FX Rates

```python
from tests.fixtures import FXFixtures
from unittest.mock import Mock

def test_currency_conversion():
    mock_fx_client = Mock()
    mock_fx_client.get_rate.return_value = 1.27  # GBP to USD
    
    result = convert_price(100.0, 'GBP', 'USD', mock_fx_client)
    assert result == 127.0
```

## Capturing Real API Responses

To create new fixtures based on real API data:

```bash
# Capture responses for a ticker
python tests/capture_api_responses.py AAPL.US

# Output saved to tests/api_responses/ (gitignored)
```

This creates JSON files you can use to build new fixtures:
- `AAPL_US_fundamentals.json`
- `AAPL_US_dividends.json`
- `AAPL_US_yfinance.json`
- `fx_rates.json`

## Test Categories

### 1. Unit Tests
- Test individual functions/methods
- Fast execution
- Isolated from external dependencies

### 2. Integration Tests
- Test multiple components together
- Still use mocks (no real API calls)
- Verify component interaction

### 3. Property-Based Tests
- Test universal properties with random inputs
- Use Hypothesis framework
- Run 100+ iterations per test

### 4. End-to-End Tests
- Test complete workflows
- From data fetch → calculation → dossier generation
- All APIs mocked

## Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_yfinance_client.py -v

# Run tests matching pattern
pytest tests/ -k "dividend" -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run property-based tests only
pytest tests/test_*_properties.py -v

# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -v -x

# Run last failed tests only
pytest tests/ -v --lf
```

## Best Practices

### ✅ DO

1. Use fixtures from `tests/fixtures.py`
2. Mock all external APIs
3. Test edge cases (errors, missing data, negative values)
4. Verify mock calls with `assert_called_once_with()`
5. Add docstrings explaining what each test validates

### ❌ DON'T

1. Don't make real API calls in unit tests
2. Don't hardcode API keys (use `"test_key"`)
3. Don't commit captured API responses
4. Don't skip assertions
5. Don't write flaky tests

## Documentation

- **TESTING_GUIDE.md** - Comprehensive testing documentation
- **fixtures.py** - Reusable mock data with docstrings
- **capture_api_responses.py** - Helper script with usage examples

## Continuous Integration

Tests run automatically on every commit:

- ✅ All tests must pass
- ✅ No real API calls allowed
- ✅ Tests complete in < 30 seconds
- ✅ No external dependencies required

## Adding New Tests

When adding a new feature:

1. Write test first (TDD approach)
2. Add fixtures if new API data needed
3. Mock all external calls
4. Test happy path and edge cases
5. Add property-based test if applicable

## Questions?

- Check `TESTING_GUIDE.md` for detailed examples
- Review `fixtures.py` for available mocks
- See existing tests for patterns
- Consult Python `unittest.mock` documentation

---

**Remember**: Good tests are fast, reliable, and don't depend on external services!
