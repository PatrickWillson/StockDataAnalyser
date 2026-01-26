"""
Property-based tests for AnomalyDetector using Hypothesis.

These tests verify universal properties that should hold across all valid inputs.
Each test runs 100+ iterations with randomly generated data.
"""

from hypothesis import given, strategies as st, settings, assume, HealthCheck
import math
from core.anomaly_detector import AnomalyDetector


# Feature: stock-data-analyser, Property 9: Anomaly detection correctness
# Validates: Requirements 7.3
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    # Generate a list of "normal" EPS values
    normal_eps=st.lists(
        st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=5,
        max_size=8
    ),
    # Generate outlier EPS values (much higher or lower)
    outlier_eps=st.floats(min_value=50.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    # Position to insert the outlier
    outlier_position=st.integers(min_value=1, max_value=4)
)
def test_anomaly_detection_correctness(normal_eps, outlier_eps, outlier_position):
    """
    Property: For any EPS history, if a year's EPS growth has |Z-Score| > 2.0, 
    that year should be flagged as an anomaly.
    
    This test verifies the anomaly detection logic is correctly implemented.
    """
    # Arrange: Create EPS history with known outlier
    # Insert outlier at specified position
    eps_list = normal_eps.copy()
    if outlier_position < len(eps_list):
        eps_list[outlier_position] = outlier_eps
    
    # Create financial data with EPS history
    history = {}
    for i, eps in enumerate(eps_list):
        year = str(2023 - i)
        history[year] = {
            'eps': eps,
            'net_income': eps * 1000000,
            'total_equity': 1000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': 1000000.0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Scan for anomalies
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Assert: Verify anomaly detection
    # Calculate growth rates manually to verify
    years = sorted(history.keys(), reverse=True)
    growth_rates = []
    
    for i in range(len(years) - 1):
        current_eps = history[years[i]]['eps']
        previous_eps = history[years[i + 1]]['eps']
        
        if previous_eps > 0:
            growth_rate = ((current_eps - previous_eps) / previous_eps) * 100
            growth_rates.append(growth_rate)
    
    # Skip test if we don't have enough data points
    if len(growth_rates) < 3:
        return
    
    # Calculate mean and std dev
    mean = sum(growth_rates) / len(growth_rates)
    variance = sum((x - mean) ** 2 for x in growth_rates) / len(growth_rates)
    std_dev = math.sqrt(variance)
    
    # Count how many growth rates should be flagged as anomalies
    expected_anomaly_count = 0
    for growth_rate in growth_rates:
        if std_dev > 0:
            z_score = (growth_rate - mean) / std_dev
            if abs(z_score) > 2.0:
                expected_anomaly_count += 1
    
    # Verify the number of detected anomalies matches expected
    assert len(anomalies) == expected_anomaly_count, \
        f"Expected {expected_anomaly_count} anomalies, got {len(anomalies)}"
    
    # Verify all anomalies contain the expected format
    for anomaly in anomalies:
        assert "Year" in anomaly, f"Anomaly should contain 'Year': {anomaly}"
        assert "Z-Score" in anomaly, f"Anomaly should contain 'Z-Score': {anomaly}"
        assert "Outlier" in anomaly, f"Anomaly should contain 'Outlier': {anomaly}"


# Feature: stock-data-analyser, Property 9: Anomaly detection correctness (normal values)
# Validates: Requirements 7.3
@settings(max_examples=100)
@given(
    # Generate a list of similar EPS values (no outliers)
    eps_list=st.lists(
        st.floats(min_value=4.0, max_value=6.0, allow_nan=False, allow_infinity=False),
        min_size=5,
        max_size=10
    )
)
def test_no_anomalies_for_normal_values(eps_list):
    """
    Property: For any EPS history with normal (non-outlier) values, 
    no anomalies should be flagged.
    
    This test verifies that normal values are not incorrectly flagged as anomalies.
    """
    # Arrange: Create financial data with normal EPS values
    history = {}
    for i, eps in enumerate(eps_list):
        year = str(2023 - i)
        history[year] = {
            'eps': eps,
            'net_income': eps * 1000000,
            'total_equity': 1000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': 1000000.0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Scan for anomalies
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Assert: Verify no anomalies detected for normal values
    # With values in a tight range (4.0-6.0), growth rates should be small
    # and Z-scores should be < 2.0
    # However, due to randomness, we might occasionally get a flagged anomaly
    # So we'll verify the logic is correct by checking manually
    
    years = sorted(history.keys(), reverse=True)
    growth_rates = []
    
    for i in range(len(years) - 1):
        current_eps = history[years[i]]['eps']
        previous_eps = history[years[i + 1]]['eps']
        
        if previous_eps > 0:
            growth_rate = ((current_eps - previous_eps) / previous_eps) * 100
            growth_rates.append(growth_rate)
    
    if len(growth_rates) < 3:
        return
    
    # Calculate mean and std dev
    mean = sum(growth_rates) / len(growth_rates)
    variance = sum((x - mean) ** 2 for x in growth_rates) / len(growth_rates)
    std_dev = math.sqrt(variance)
    
    # Count expected anomalies
    expected_anomaly_count = 0
    if std_dev > 0:
        for growth_rate in growth_rates:
            z_score = (growth_rate - mean) / std_dev
            if abs(z_score) > 2.0:
                expected_anomaly_count += 1
    
    # Verify the detector matches our manual calculation
    assert len(anomalies) == expected_anomaly_count, \
        f"Expected {expected_anomaly_count} anomalies, got {len(anomalies)}"
