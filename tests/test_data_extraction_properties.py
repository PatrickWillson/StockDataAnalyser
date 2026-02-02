"""
Property-based tests for data extraction functions using Hypothesis.

Tests universal properties for extract_3year_eps_data() and check_data_staleness()
functions used in normalized Graham Number calculations.

Each test runs 100+ iterations with randomly generated data to verify correctness
across all valid inputs and edge cases.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from core.financial_data_processor import FinancialDataProcessor


# Feature: normalized-margin-of-safety, Property 14: Most Recent Years Selection
# Validates: Requirements 7.4, 8.4
@settings(max_examples=100)
@given(
    # Generate 10-20 years of EPS data
    num_years=st.integers(min_value=10, max_value=20),
    eps_values=st.lists(
        st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=10,
        max_size=20
    )
)
def test_most_recent_years_selection(num_years, eps_values):
    """
    Property 14: Most Recent Years Selection
    
    For any financial history with more than 3 years of data, the system should
    use exactly the 3 most recent consecutive fiscal years for the normalized
    calculation, in descending chronological order.
    
    **Validates: Requirements 7.4, 8.4**
    """
    # Ensure we have enough EPS values for the number of years
    assume(len(eps_values) >= num_years)
    
    # Arrange: Create history with num_years of data
    history = {}
    for i in range(num_years):
        year = f"{2024 - i}-12-31"
        history[year] = {'eps': eps_values[i]}
    
    # Act: Extract 3-year EPS data
    result = FinancialDataProcessor.extract_3year_eps_data(history)
    
    # Assert: Should select exactly the 3 most recent years
    assert result['valid'] is True, f"Expected valid=True for {num_years} years of data"
    assert len(result['eps_values']) == 3, f"Expected 3 EPS values, got {len(result['eps_values'])}"
    assert len(result['years']) == 3, f"Expected 3 years, got {len(result['years'])}"
    
    # Verify the 3 most recent years are selected
    expected_years = ['2024-12-31', '2023-12-31', '2022-12-31']
    assert result['years'] == expected_years, \
        f"Expected years {expected_years}, got {result['years']}"
    
    # Verify the corresponding EPS values are selected (first 3 from eps_values)
    expected_eps = eps_values[:3]
    assert result['eps_values'] == expected_eps, \
        f"Expected EPS values {expected_eps}, got {result['eps_values']}"
    
    # Verify years are in descending chronological order (most recent first)
    years_as_dates = [datetime.strptime(y, '%Y-%m-%d') for y in result['years']]
    assert years_as_dates == sorted(years_as_dates, reverse=True), \
        "Years should be in descending chronological order"


# Feature: normalized-margin-of-safety, Property 13: Null EPS Detection
# Validates: Requirements 7.1, 7.2, 7.3
@settings(max_examples=100)
@given(
    # Generate position of null EPS (0, 1, or 2 for first, second, or third year)
    null_position=st.integers(min_value=0, max_value=2),
    # Generate valid EPS values for non-null positions
    valid_eps_1=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    valid_eps_2=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate type of null value (None, "NA", "N/A", "", or non-numeric string)
    null_type=st.sampled_from([None, "NA", "N/A", "", "invalid"])
)
def test_null_eps_detection(null_position, valid_eps_1, valid_eps_2, null_type):
    """
    Property 13: Null EPS Detection
    
    For any financial history where any of the 3 most recent years has null or
    missing EPS data, the system should return "N/A" for normalized Graham Number
    and include a warning specifying which years have missing data.
    
    **Validates: Requirements 7.1, 7.2, 7.3**
    """
    # Arrange: Create history with one null EPS value
    eps_values = [valid_eps_1, valid_eps_2, 0.0]  # Placeholder for third value
    eps_values[null_position] = null_type  # Replace with null value
    
    history = {
        '2024-12-31': {'eps': eps_values[0]},
        '2023-12-31': {'eps': eps_values[1]},
        '2022-12-31': {'eps': eps_values[2]}
    }
    
    # Act: Extract 3-year EPS data
    result = FinancialDataProcessor.extract_3year_eps_data(history)
    
    # Assert: Should detect null EPS and return invalid result
    assert result['valid'] is False, \
        f"Expected valid=False when EPS at position {null_position} is {null_type}"
    
    assert result['warning'] is not None, \
        "Expected warning when EPS is null/missing"
    
    assert "Missing EPS data for years:" in result['warning'], \
        f"Expected 'Missing EPS data for years:' in warning, got: {result['warning']}"
    
    # Verify the warning specifies which year has missing data
    year_with_null = ['2024-12-31', '2023-12-31', '2022-12-31'][null_position]
    assert year_with_null in result['warning'], \
        f"Expected year {year_with_null} in warning, got: {result['warning']}"
    
    # Verify eps_values and years are still populated (for audit trail)
    assert len(result['eps_values']) == 3, \
        "EPS values should be populated even when invalid"
    assert len(result['years']) == 3, \
        "Years should be populated even when invalid"
    
    # Verify the null position has None in eps_values
    assert result['eps_values'][null_position] is None, \
        f"Expected None at position {null_position}, got {result['eps_values'][null_position]}"


# Feature: normalized-margin-of-safety, Property 13 (Multiple Nulls): Multiple Null EPS Detection
# Validates: Requirements 7.1, 7.2, 7.3
@settings(max_examples=100)
@given(
    # Generate number of null positions (1-3)
    num_nulls=st.integers(min_value=1, max_value=3),
    # Generate valid EPS for non-null positions
    valid_eps=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate type of null value
    null_type=st.sampled_from([None, "NA", "N/A", ""])
)
def test_multiple_null_eps_detection(num_nulls, valid_eps, null_type):
    """
    Property 13 (Multiple Nulls): Multiple Null EPS Detection
    
    For any financial history where multiple years have null/missing EPS data,
    the system should return invalid result and list all years with missing data.
    
    **Validates: Requirements 7.1, 7.2, 7.3**
    """
    # Arrange: Create history with multiple null EPS values
    # Randomly select which positions to make null
    import random
    random.seed(hash((num_nulls, valid_eps, null_type)))  # Deterministic for Hypothesis
    positions = random.sample([0, 1, 2], num_nulls)
    
    eps_values = [valid_eps, valid_eps, valid_eps]
    for pos in positions:
        eps_values[pos] = null_type
    
    history = {
        '2024-12-31': {'eps': eps_values[0]},
        '2023-12-31': {'eps': eps_values[1]},
        '2022-12-31': {'eps': eps_values[2]}
    }
    
    # Act: Extract 3-year EPS data
    result = FinancialDataProcessor.extract_3year_eps_data(history)
    
    # Assert: Should detect null EPS and return invalid result
    assert result['valid'] is False, \
        f"Expected valid=False when {num_nulls} years have null EPS"
    
    assert result['warning'] is not None, \
        "Expected warning when multiple years have null EPS"
    
    assert "Missing EPS data for years:" in result['warning'], \
        f"Expected 'Missing EPS data for years:' in warning, got: {result['warning']}"
    
    # Verify all years with null data are mentioned in warning
    years = ['2024-12-31', '2023-12-31', '2022-12-31']
    for pos in positions:
        assert years[pos] in result['warning'], \
            f"Expected year {years[pos]} in warning, got: {result['warning']}"


# Feature: normalized-margin-of-safety, Property 15: Staleness Detection
# Validates: Requirements 7.6, 7.7
@settings(max_examples=100)
@given(
    # Generate months difference (0-24 months)
    months_old=st.floats(min_value=0.0, max_value=24.0, allow_nan=False, allow_infinity=False)
)
def test_staleness_detection(months_old):
    """
    Property 15: Staleness Detection
    
    For any financial history where the most recent annual report date is more
    than 9 months before the current date, the system should add a warning
    flagging "Potentially Stale Data" and include the report date in the warning.
    
    **Validates: Requirements 7.6, 7.7**
    """
    # Arrange: Create history with report date months_old months ago
    current_date = datetime(2025, 6, 1)
    
    # Calculate report date using 30.44 days per month (365.25 / 12)
    days_old = int(months_old * 30.44)
    report_date = current_date - timedelta(days=days_old)
    report_date_str = report_date.strftime('%Y-%m-%d')
    
    history = {
        report_date_str: {'eps': 5.00, 'revenue': 1000000}
    }
    
    # Act: Check data staleness
    result = FinancialDataProcessor.check_data_staleness(history, current_date)
    
    # Assert: Should detect staleness based on 9-month threshold
    # Calculate actual months as the implementation does: days / 30.44
    actual_months = days_old / 30.44
    
    if actual_months > 9.0:
        # Data is stale - should return warning
        assert result is not None, \
            f"Expected warning for data {actual_months:.1f} months old"
        
        assert "Potentially Stale Data" in result, \
            f"Expected 'Potentially Stale Data' in warning, got: {result}"
        
        assert report_date_str in result, \
            f"Expected report date {report_date_str} in warning, got: {result}"
        
        assert "months old" in result, \
            f"Expected 'months old' in warning, got: {result}"
        
        # Verify the calculated months is in the warning
        # Using int() to match the implementation's formatting
        expected_months = int(actual_months)
        assert f"{expected_months} months old" in result, \
            f"Expected '{expected_months} months old' in warning, got: {result}"
    else:
        # Data is fresh - should return None
        assert result is None, \
            f"Expected no warning for data {actual_months:.1f} months old, got: {result}"


# Feature: normalized-margin-of-safety, Property 15 (Boundary): Staleness Boundary Test
# Validates: Requirements 7.6, 7.7
@settings(max_examples=100)
@given(
    # Generate days around the 9-month boundary (274 days = 9 months using 30.44 days/month)
    days_offset=st.integers(min_value=-5, max_value=5)
)
def test_staleness_boundary(days_offset):
    """
    Property 15 (Boundary): Staleness Boundary Test
    
    Verify that the 9-month threshold is correctly applied at the boundary.
    9 months = 274 days (using 30.44 days/month).
    
    **Validates: Requirements 7.6, 7.7**
    """
    # Arrange: Create history with report date near 9-month boundary
    current_date = datetime(2025, 6, 1)
    
    # 9 months = 274 days (9 * 30.44 = 273.96 ≈ 274)
    boundary_days = 274
    days_old = boundary_days + days_offset
    
    report_date = current_date - timedelta(days=days_old)
    report_date_str = report_date.strftime('%Y-%m-%d')
    
    history = {
        report_date_str: {'eps': 5.00}
    }
    
    # Act: Check data staleness
    result = FinancialDataProcessor.check_data_staleness(history, current_date)
    
    # Assert: Verify boundary behavior
    months_old = days_old / 30.44
    
    if months_old > 9.0:
        # Should trigger warning
        assert result is not None, \
            f"Expected warning for {days_old} days ({months_old:.2f} months)"
        assert "Potentially Stale Data" in result
    else:
        # Should not trigger warning
        assert result is None, \
            f"Expected no warning for {days_old} days ({months_old:.2f} months), got: {result}"


# Feature: normalized-margin-of-safety, Property 15 (Multiple Years): Staleness with Multiple Years
# Validates: Requirements 7.6, 7.7
@settings(max_examples=100)
@given(
    # Generate number of years (3-10)
    num_years=st.integers(min_value=3, max_value=10),
    # Generate months old for most recent year
    most_recent_months_old=st.floats(min_value=0.0, max_value=24.0, allow_nan=False, allow_infinity=False)
)
def test_staleness_with_multiple_years(num_years, most_recent_months_old):
    """
    Property 15 (Multiple Years): Staleness with Multiple Years
    
    For any financial history with multiple years, the staleness check should
    use only the most recent year, regardless of how old the older years are.
    
    **Validates: Requirements 7.6, 7.7**
    """
    # Arrange: Create history with multiple years
    current_date = datetime(2025, 6, 1)
    
    history = {}
    for i in range(num_years):
        # Most recent year uses most_recent_months_old
        # Older years are progressively older
        months_old = most_recent_months_old + (i * 12)
        days_old = int(months_old * 30.44)
        report_date = current_date - timedelta(days=days_old)
        report_date_str = report_date.strftime('%Y-%m-%d')
        
        history[report_date_str] = {'eps': 5.00 + i}
    
    # Act: Check data staleness
    result = FinancialDataProcessor.check_data_staleness(history, current_date)
    
    # Assert: Should only consider most recent year
    if most_recent_months_old > 9.0:
        # Most recent year is stale - should return warning
        assert result is not None, \
            f"Expected warning when most recent year is {most_recent_months_old:.1f} months old"
        
        assert "Potentially Stale Data" in result
        
        # Verify the most recent year's date is in the warning
        most_recent_date = (current_date - timedelta(days=int(most_recent_months_old * 30.44))).strftime('%Y-%m-%d')
        assert most_recent_date in result, \
            f"Expected most recent date {most_recent_date} in warning, got: {result}"
    else:
        # Most recent year is fresh - should return None
        assert result is None, \
            f"Expected no warning when most recent year is {most_recent_months_old:.1f} months old"


# Feature: normalized-margin-of-safety, Property 14 (Descending Order): Years in Descending Order
# Validates: Requirements 7.4, 8.4
@settings(max_examples=100)
@given(
    # Generate random order of years
    year_offsets=st.permutations([0, 1, 2, 3, 4])
)
def test_years_in_descending_order(year_offsets):
    """
    Property 14 (Descending Order): Years in Descending Order
    
    For any financial history provided in any order, the system should return
    the 3 most recent years in descending chronological order (most recent first).
    
    **Validates: Requirements 7.4, 8.4**
    """
    # Arrange: Create history with years in random order
    history = {}
    for offset in year_offsets:
        year = f"{2024 - offset}-12-31"
        history[year] = {'eps': 10.0 + offset}
    
    # Act: Extract 3-year EPS data
    result = FinancialDataProcessor.extract_3year_eps_data(history)
    
    # Assert: Should return 3 most recent years in descending order
    assert result['valid'] is True
    
    expected_years = ['2024-12-31', '2023-12-31', '2022-12-31']
    assert result['years'] == expected_years, \
        f"Expected years {expected_years} in descending order, got {result['years']}"
    
    # Verify EPS values correspond to the correct years
    assert result['eps_values'] == [10.0, 11.0, 12.0], \
        f"Expected EPS [10.0, 11.0, 12.0], got {result['eps_values']}"


# Feature: normalized-margin-of-safety, Property 13 (String Numeric): String Numeric EPS Handling
# Validates: Requirements 7.1, 7.2
@settings(max_examples=100)
@given(
    # Generate numeric EPS values as floats
    eps_1=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    eps_2=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    eps_3=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_string_numeric_eps_handling(eps_1, eps_2, eps_3):
    """
    Property 13 (String Numeric): String Numeric EPS Handling
    
    For any financial history where EPS values are provided as numeric strings
    (e.g., "5.00" instead of 5.00), the system should successfully convert them
    to floats and return valid result.
    
    **Validates: Requirements 7.1, 7.2**
    """
    # Arrange: Create history with EPS as numeric strings
    history = {
        '2024-12-31': {'eps': str(eps_1)},
        '2023-12-31': {'eps': str(eps_2)},
        '2022-12-31': {'eps': str(eps_3)}
    }
    
    # Act: Extract 3-year EPS data
    result = FinancialDataProcessor.extract_3year_eps_data(history)
    
    # Assert: Should successfully convert strings to floats
    assert result['valid'] is True, \
        f"Expected valid=True for numeric string EPS, got valid={result['valid']}"
    
    assert len(result['eps_values']) == 3
    
    # Verify values are converted to floats
    assert result['eps_values'][0] == pytest.approx(eps_1, rel=1e-6), \
        f"Expected {eps_1}, got {result['eps_values'][0]}"
    assert result['eps_values'][1] == pytest.approx(eps_2, rel=1e-6), \
        f"Expected {eps_2}, got {result['eps_values'][1]}"
    assert result['eps_values'][2] == pytest.approx(eps_3, rel=1e-6), \
        f"Expected {eps_3}, got {result['eps_values'][2]}"


# Feature: normalized-margin-of-safety, Property 15 (Future Date): Future Date Detection
# Validates: Requirements 7.6, 7.7
@settings(max_examples=100)
@given(
    # Generate days in the future (1-365 days)
    days_in_future=st.integers(min_value=1, max_value=365)
)
def test_future_date_detection(days_in_future):
    """
    Property 15 (Future Date): Future Date Detection
    
    For any financial history where the report date is in the future (clock skew),
    the system should return a warning indicating the data date is in the future.
    
    **Validates: Requirements 7.6, 7.7**
    """
    # Arrange: Create history with future date
    current_date = datetime(2025, 6, 1)
    future_date = current_date + timedelta(days=days_in_future)
    future_date_str = future_date.strftime('%Y-%m-%d')
    
    history = {
        future_date_str: {'eps': 5.00}
    }
    
    # Act: Check data staleness
    result = FinancialDataProcessor.check_data_staleness(history, current_date)
    
    # Assert: Should detect future date
    assert result is not None, \
        f"Expected warning for future date {days_in_future} days ahead"
    
    assert "Data date is in the future" in result, \
        f"Expected 'Data date is in the future' in warning, got: {result}"
    
    assert future_date_str in result, \
        f"Expected future date {future_date_str} in warning, got: {result}"


# Feature: normalized-margin-of-safety, Property 14 (Non-December): Non-December Fiscal Year
# Validates: Requirements 7.4
@settings(max_examples=100)
@given(
    # Generate fiscal year end month (1-12)
    fiscal_month=st.integers(min_value=1, max_value=12),
    # Generate fiscal year end day (1-28 to avoid invalid dates)
    fiscal_day=st.integers(min_value=1, max_value=28),
    # Generate number of years (3-10)
    num_years=st.integers(min_value=3, max_value=10)
)
def test_non_december_fiscal_year(fiscal_month, fiscal_day, num_years):
    """
    Property 14 (Non-December): Non-December Fiscal Year
    
    For any financial history with non-December fiscal year ends (e.g., June 30
    for Microsoft), the system should correctly select the 3 most recent years
    regardless of the fiscal year end date.
    
    **Validates: Requirements 7.4**
    """
    # Arrange: Create history with non-December fiscal year ends
    history = {}
    for i in range(num_years):
        year = 2024 - i
        fiscal_date = f"{year}-{fiscal_month:02d}-{fiscal_day:02d}"
        history[fiscal_date] = {'eps': 10.0 + i}
    
    # Act: Extract 3-year EPS data
    result = FinancialDataProcessor.extract_3year_eps_data(history)
    
    # Assert: Should select 3 most recent years
    assert result['valid'] is True, \
        f"Expected valid=True for non-December fiscal year"
    
    assert len(result['years']) == 3
    
    # Verify most recent 3 years are selected
    expected_years = [
        f"2024-{fiscal_month:02d}-{fiscal_day:02d}",
        f"2023-{fiscal_month:02d}-{fiscal_day:02d}",
        f"2022-{fiscal_month:02d}-{fiscal_day:02d}"
    ]
    assert result['years'] == expected_years, \
        f"Expected years {expected_years}, got {result['years']}"
    
    # Verify EPS values
    assert result['eps_values'] == [10.0, 11.0, 12.0], \
        f"Expected EPS [10.0, 11.0, 12.0], got {result['eps_values']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
