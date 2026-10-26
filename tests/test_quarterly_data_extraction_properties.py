"""
Property-based tests for quarterly data extraction.

Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction

**Validates: Requirements 1.1, 1.2, 1.4, 1.5**

For any EODHD API response containing quarterly data, extracting balance sheet 
and income statement data should produce dictionaries with date keys in descending 
chronological order, and all "NA" or null values should be sanitized to 0.0.
"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from core.financial_data_processor import FinancialDataProcessor


# Strategy for generating valid date strings in YYYY-MM-DD format
@st.composite
def date_strings(draw, min_year=2020, max_year=2025):
    """Generate valid date strings for quarterly periods."""
    year = draw(st.integers(min_value=min_year, max_value=max_year))
    # Typical quarter end dates: 03-31, 06-30, 09-30, 12-31
    month_day = draw(st.sampled_from(['03-31', '06-30', '09-30', '12-31']))
    return f"{year}-{month_day}"


# Strategy for generating quarterly balance sheet data
@st.composite
def quarterly_balance_sheet_data(draw, num_periods=None):
    """
    Generate random quarterly balance sheet data with various value types.
    
    Includes:
    - Valid numeric values
    - "NA" strings
    - None values
    - Empty strings
    - Zero values
    """
    if num_periods is None:
        num_periods = draw(st.integers(min_value=1, max_value=8))
    
    # Generate unique dates in descending order
    dates = []
    base_year = 2025
    for i in range(num_periods):
        quarter = (4 - (i % 4))  # 4, 3, 2, 1, 4, 3, ...
        year = base_year - (i // 4)
        month_day = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[quarter]
        dates.append(f"{year}-{month_day}")
    
    quarterly_data = {}
    
    for date in dates:
        # Generate random values including NA, None, empty string, and valid numbers
        value_strategy = st.one_of(
            st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
            st.just('NA'),
            st.just('N/A'),
            st.just(None),
            st.just(''),
            st.just(0),
            st.just(0.0)
        )
        
        quarterly_data[date] = {
            'totalStockholderEquity': draw(value_strategy),
            'intangibleAssets': draw(value_strategy),
            'goodWill': draw(value_strategy),
            'totalCurrentAssets': draw(value_strategy),
            'totalCurrentLiabilities': draw(value_strategy),
            'totalLiab': draw(value_strategy),
            'longTermDebt': draw(value_strategy),
            'shortTermDebt': draw(value_strategy),
            'totalAssets': draw(value_strategy),
            'commonStockSharesOutstanding': draw(value_strategy),
        }
    
    return quarterly_data


# Strategy for generating quarterly income statement data
@st.composite
def quarterly_income_statement_data(draw, num_periods=None):
    """
    Generate random quarterly income statement data with various value types.
    
    Includes:
    - Valid numeric values
    - "NA" strings
    - None values
    - Empty strings
    - Zero values
    """
    if num_periods is None:
        num_periods = draw(st.integers(min_value=1, max_value=8))
    
    # Generate unique dates in descending order
    dates = []
    base_year = 2025
    for i in range(num_periods):
        quarter = (4 - (i % 4))  # 4, 3, 2, 1, 4, 3, ...
        year = base_year - (i // 4)
        month_day = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[quarter]
        dates.append(f"{year}-{month_day}")
    
    quarterly_data = {}
    
    for date in dates:
        # Generate random values including NA, None, empty string, and valid numbers
        value_strategy = st.one_of(
            st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
            st.just('NA'),
            st.just('N/A'),
            st.just(None),
            st.just(''),
            st.just(0),
            st.just(0.0)
        )
        
        quarterly_data[date] = {
            'totalRevenue': draw(value_strategy),
            'netIncome': draw(value_strategy),
            'eps': draw(value_strategy),
        }
    
    return quarterly_data


class TestQuarterlyDataExtractionProperties:
    """Property-based tests for quarterly data extraction."""
    
    @given(quarterly_data=quarterly_balance_sheet_data())
    def test_balance_sheet_extraction_produces_date_keyed_dict(self, quarterly_data):
        """
        Property: Extracting quarterly balance sheet data produces a dictionary
        with date strings as keys.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.1, 1.4
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Verify result is a dictionary
        assert isinstance(result, dict)
        
        # Verify all keys are date strings in YYYY-MM-DD format
        for key in result.keys():
            assert isinstance(key, str)
            # Verify date format
            try:
                datetime.strptime(key, '%Y-%m-%d')
            except ValueError:
                pytest.fail(f"Key '{key}' is not in YYYY-MM-DD format")
    
    @given(quarterly_data=quarterly_balance_sheet_data())
    def test_balance_sheet_extraction_descending_order(self, quarterly_data):
        """
        Property: Quarterly balance sheet data is sorted by date in descending order
        (most recent first).
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.4
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Skip if no data
        if len(result) == 0:
            return
        
        # Verify dates are in descending order
        dates = list(result.keys())
        for i in range(len(dates) - 1):
            date1 = datetime.strptime(dates[i], '%Y-%m-%d')
            date2 = datetime.strptime(dates[i + 1], '%Y-%m-%d')
            assert date1 > date2, f"Dates not in descending order: {dates[i]} should be after {dates[i+1]}"
    
    @given(quarterly_data=quarterly_balance_sheet_data())
    def test_balance_sheet_sanitizes_na_values(self, quarterly_data):
        """
        Property: All "NA", "N/A", None, and empty string values in quarterly
        balance sheet data are sanitized to 0.0.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.5
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Verify all values are numeric (float)
        for period, data in result.items():
            for field, value in data.items():
                assert isinstance(value, (int, float)), \
                    f"Period {period}, field {field}: expected numeric, got {type(value)}"
                assert not (isinstance(value, float) and (value != value)), \
                    f"Period {period}, field {field}: NaN value detected"
    
    @given(quarterly_data=quarterly_income_statement_data())
    def test_income_statement_extraction_produces_date_keyed_dict(self, quarterly_data):
        """
        Property: Extracting quarterly income statement data produces a dictionary
        with date strings as keys.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.2, 1.4
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Verify result is a dictionary
        assert isinstance(result, dict)
        
        # Verify all keys are date strings in YYYY-MM-DD format
        for key in result.keys():
            assert isinstance(key, str)
            # Verify date format
            try:
                datetime.strptime(key, '%Y-%m-%d')
            except ValueError:
                pytest.fail(f"Key '{key}' is not in YYYY-MM-DD format")
    
    @given(quarterly_data=quarterly_income_statement_data())
    def test_income_statement_extraction_descending_order(self, quarterly_data):
        """
        Property: Quarterly income statement data is sorted by date in descending order
        (most recent first).
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.4
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Skip if no data
        if len(result) == 0:
            return
        
        # Verify dates are in descending order
        dates = list(result.keys())
        for i in range(len(dates) - 1):
            date1 = datetime.strptime(dates[i], '%Y-%m-%d')
            date2 = datetime.strptime(dates[i + 1], '%Y-%m-%d')
            assert date1 > date2, f"Dates not in descending order: {dates[i]} should be after {dates[i+1]}"
    
    @given(quarterly_data=quarterly_income_statement_data())
    def test_income_statement_sanitizes_na_values(self, quarterly_data):
        """
        Property: All "NA", "N/A", None, and empty string values in quarterly
        income statement data are sanitized to 0.0.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.5
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Verify all values are numeric (float)
        for period, data in result.items():
            for field, value in data.items():
                assert isinstance(value, (int, float)), \
                    f"Period {period}, field {field}: expected numeric, got {type(value)}"
                assert not (isinstance(value, float) and (value != value)), \
                    f"Period {period}, field {field}: NaN value detected"
    
    @given(
        balance_sheet=quarterly_balance_sheet_data(num_periods=4),
        income_statement=quarterly_income_statement_data(num_periods=4)
    )
    def test_merge_quarterly_data_structure(self, balance_sheet, income_statement):
        """
        Property: merge_quarterly_data produces a dict with 'balance_sheet' and
        'income_statement' keys, each containing the respective data.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.1, 1.2
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Parse the data first
        mock_bs_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': balance_sheet
                }
            }
        }
        mock_is_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': income_statement
                }
            }
        }
        
        parsed_bs = processor.parse_quarterly_balance_sheet(mock_bs_data)
        parsed_is = processor.parse_quarterly_income_statement(mock_is_data)
        
        # Merge the data
        result = processor.merge_quarterly_data(parsed_bs, parsed_is)
        
        # Verify structure
        assert isinstance(result, dict)
        assert 'balance_sheet' in result
        assert 'income_statement' in result
        assert isinstance(result['balance_sheet'], dict)
        assert isinstance(result['income_statement'], dict)
    
    def test_merge_quarterly_data_handles_missing_data(self):
        """
        Property: merge_quarterly_data handles missing data gracefully by
        returning empty dicts.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.3
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Test with None values
        result = processor.merge_quarterly_data(None, None)
        assert result == {'balance_sheet': {}, 'income_statement': {}}
        
        # Test with empty dicts
        result = processor.merge_quarterly_data({}, {})
        assert result == {'balance_sheet': {}, 'income_statement': {}}
        
        # Test with one missing
        result = processor.merge_quarterly_data({'2025-09-30': {}}, None)
        assert result['balance_sheet'] == {'2025-09-30': {}}
        assert result['income_statement'] == {}
    
    @given(
        num_periods=st.integers(min_value=1, max_value=8)
    )
    def test_extraction_preserves_period_count(self, num_periods):
        """
        Property: The number of periods in the result equals the number of
        periods in the input data.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.1, 1.2
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Generate data with specific number of periods
        dates = []
        base_year = 2025
        for i in range(num_periods):
            quarter = (4 - (i % 4))
            year = base_year - (i // 4)
            month_day = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[quarter]
            dates.append(f"{year}-{month_day}")
        
        quarterly_data = {}
        for date in dates:
            quarterly_data[date] = {
                'totalStockholderEquity': 1000000.0,
                'totalLiab': 500000.0,
                'totalAssets': 1500000.0,
            }
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': quarterly_data
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Verify period count is preserved
        assert len(result) == num_periods, \
            f"Expected {num_periods} periods, got {len(result)}"
    
    @given(
        value=st.one_of(
            st.just('NA'),
            st.just('N/A'),
            st.just(None),
            st.just(''),
            st.just('null')
        )
    )
    def test_sanitize_value_converts_all_na_variants(self, value):
        """
        Property: sanitize_value converts all variants of "NA" to 0.0.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.5
        """
        result = FinancialDataProcessor.sanitize_value(value)
        assert result == 0.0, f"Expected 0.0 for value '{value}', got {result}"
    
    @given(
        value=st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False)
    )
    def test_sanitize_value_preserves_valid_numbers(self, value):
        """
        Property: sanitize_value preserves valid numeric values.
        
        Feature: ttm-graham-calculations, Property 1: Periodic Data Extraction
        Validates: Requirements 1.5
        """
        result = FinancialDataProcessor.sanitize_value(value)
        assert abs(result - value) < 0.01, \
            f"Expected {value}, got {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
