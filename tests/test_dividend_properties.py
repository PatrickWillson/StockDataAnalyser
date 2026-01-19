"""
Property-based tests for dividend calculation logic.

Tests correctness properties for Requirements 2.1, 2.2, 2.4:
- Property 5: Dividend Source Priority
- Property 6: Forward Dividend Restriction
"""

import pytest
from hypothesis import given, strategies as st, assume
from core.financial_data_processor import FinancialDataProcessor


@given(
    num_years=st.integers(min_value=1, max_value=10),
    dividends_paid=st.lists(
        st.floats(min_value=100000, max_value=10000000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10
    ),
    shares=st.floats(min_value=100000, max_value=10000000, allow_nan=False, allow_infinity=False),
    forward_rate=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_property_dividend_source_priority(num_years, dividends_paid, shares, forward_rate):
    """
    Property 5: Dividend Source Priority
    
    For any year where Cash Flow dividendsPaid is available, it should be used 
    instead of ForwardAnnualDividendRate.
    
    **Validates: Requirements 2.1, 2.2**
    """
    # Ensure we have enough dividends for the years
    assume(len(dividends_paid) >= num_years)
    assume(shares > 0)
    
    processor = FinancialDataProcessor(debug=False)
    
    # Build mock data with both cash flow and forward rate
    current_year = 2024
    cash_flow_yearly = {}
    shares_data = {}
    
    for i in range(num_years):
        year = current_year - i
        year_key = f"{year}-12-31"
        cash_flow_yearly[year_key] = {'dividendsPaid': -abs(dividends_paid[i])}
        shares_data[str(i)] = {'date': str(year), 'shares': shares}
    
    data = {
        'General': {'CurrencyCode': 'USD'},
        'SplitsDividends': {
            'ForwardAnnualDividendRate': forward_rate
        },
        'Financials': {
            'Cash_Flow': {
                'currency_symbol': 'USD',
                'yearly': cash_flow_yearly
            }
        },
        'outstandingShares': {
            'annual': shares_data
        }
    }
    
    result, _, _, _, sources = processor.parse_dividend_history(data)
    
    # Property: All years with cash flow data should use cash_flow source
    for i in range(num_years):
        year = str(current_year - i)
        if year in result:
            # Should be marked as cash_flow, not forward_rate
            assert sources[year] == 'cash_flow', \
                f"Year {year} should use cash_flow source, not {sources.get(year)}"
            
            # Should match calculated value from cash flow
            expected_div = abs(dividends_paid[i]) / shares
            assert result[year] == pytest.approx(expected_div, rel=0.01), \
                f"Year {year} dividend should be {expected_div}, got {result[year]}"


@given(
    num_historical_years=st.integers(min_value=1, max_value=5),
    forward_rate=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    shares=st.floats(min_value=100000, max_value=10000000, allow_nan=False, allow_infinity=False)
)
def test_property_forward_dividend_restriction(num_historical_years, forward_rate, shares):
    """
    Property 6: Forward Dividend Restriction
    
    For any historical year (not most recent), ForwardAnnualDividendRate should 
    never be used as a substitute.
    
    **Validates: Requirements 2.4**
    """
    assume(shares > 0)
    assume(forward_rate > 0)
    
    processor = FinancialDataProcessor(debug=False)
    
    # Build mock data with NO cash flow but WITH forward rate
    current_year = 2024
    cash_flow_yearly = {}
    shares_data = {}
    
    # Create years with NO dividendsPaid (empty dicts)
    for i in range(num_historical_years + 1):  # +1 for most recent year
        year = current_year - i
        year_key = f"{year}-12-31"
        cash_flow_yearly[year_key] = {}  # No dividendsPaid
        shares_data[str(i)] = {'date': str(year), 'shares': shares}
    
    data = {
        'General': {'CurrencyCode': 'USD'},
        'SplitsDividends': {
            'ForwardAnnualDividendRate': forward_rate
        },
        'Financials': {
            'Cash_Flow': {
                'currency_symbol': 'USD',
                'yearly': cash_flow_yearly
            }
        },
        'outstandingShares': {
            'annual': shares_data
        }
    }
    
    result, _, _, _, sources = processor.parse_dividend_history(data)
    
    # Property: Only most recent year should have forward_rate
    most_recent_year = str(current_year)
    
    if most_recent_year in result:
        # Most recent year CAN use forward rate
        assert sources[most_recent_year] == 'forward_rate', \
            f"Most recent year {most_recent_year} should use forward_rate"
        assert result[most_recent_year] == forward_rate, \
            f"Most recent year should have forward rate value {forward_rate}"
    
    # Historical years should NOT be in result (no forward rate used)
    for i in range(1, num_historical_years + 1):
        historical_year = str(current_year - i)
        assert historical_year not in result, \
            f"Historical year {historical_year} should not use forward rate"
        assert historical_year not in sources, \
            f"Historical year {historical_year} should not have source indicator"


@given(
    has_cash_flow_most_recent=st.booleans(),
    has_cash_flow_historical=st.booleans(),
    dividend_most_recent=st.floats(min_value=100000, max_value=5000000, allow_nan=False, allow_infinity=False),
    dividend_historical=st.floats(min_value=100000, max_value=5000000, allow_nan=False, allow_infinity=False),
    forward_rate=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    shares=st.floats(min_value=100000, max_value=10000000, allow_nan=False, allow_infinity=False)
)
def test_property_source_consistency(has_cash_flow_most_recent, has_cash_flow_historical,
                                     dividend_most_recent, dividend_historical,
                                     forward_rate, shares):
    """
    Property: Source indicators are consistent with actual data sources used.
    
    For any year in the result, the source indicator should accurately reflect
    whether the data came from cash_flow or forward_rate.
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """
    assume(shares > 0)
    assume(forward_rate > 0)
    
    processor = FinancialDataProcessor(debug=False)
    
    # Build mock data
    current_year = 2024
    historical_year = 2023
    
    cash_flow_yearly = {
        f"{current_year}-12-31": {'dividendsPaid': -abs(dividend_most_recent)} if has_cash_flow_most_recent else {},
        f"{historical_year}-12-31": {'dividendsPaid': -abs(dividend_historical)} if has_cash_flow_historical else {}
    }
    
    shares_data = {
        '0': {'date': str(current_year), 'shares': shares},
        '1': {'date': str(historical_year), 'shares': shares}
    }
    
    data = {
        'General': {'CurrencyCode': 'USD'},
        'SplitsDividends': {
            'ForwardAnnualDividendRate': forward_rate
        },
        'Financials': {
            'Cash_Flow': {
                'currency_symbol': 'USD',
                'yearly': cash_flow_yearly
            }
        },
        'outstandingShares': {
            'annual': shares_data
        }
    }
    
    result, _, _, _, sources = processor.parse_dividend_history(data)
    
    # Property: Source indicators match actual data availability
    
    # Most recent year
    if str(current_year) in result:
        if has_cash_flow_most_recent:
            # Should use cash flow
            assert sources[str(current_year)] == 'cash_flow'
            expected = abs(dividend_most_recent) / shares
            assert result[str(current_year)] == pytest.approx(expected, rel=0.01)
        else:
            # Should use forward rate (only for most recent year)
            assert sources[str(current_year)] == 'forward_rate'
            assert result[str(current_year)] == forward_rate
    
    # Historical year
    if str(historical_year) in result:
        # Should ONLY be present if has cash flow
        assert has_cash_flow_historical, \
            f"Historical year {historical_year} should only be in result if has cash flow"
        assert sources[str(historical_year)] == 'cash_flow'
        expected = abs(dividend_historical) / shares
        assert result[str(historical_year)] == pytest.approx(expected, rel=0.01)
    else:
        # If not in result, should not have cash flow (or forward rate shouldn't be used)
        if has_cash_flow_historical:
            # This might happen if dividend is 0 or shares calculation failed
            pass
        else:
            # Correctly omitted - no cash flow and forward rate not used for historical
            assert str(historical_year) not in sources


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
