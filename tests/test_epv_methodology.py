"""
Unit tests for EPV methodology section in dossier.

Requirements 8.1-8.6:
- 8.1: Explain Graham's "earning power" concept as full-cycle average
- 8.2: Explain why loss years are included (reflect true cyclical risk)
- 8.3: Show formula: Average Net Income (7-10 years) / Cost of Capital
- 8.4: List all years included with their net income values
- 8.5: Show normalized earnings amount
- 8.6: Include Graham quote about including deficits
"""

from output.dossier_generator import DossierGenerator


def test_epv_methodology_includes_full_cycle_explanation():
    """
    Test that EPV methodology explains Graham's full-cycle concept.
    
    Validates: Requirement 8.1
    """
    # Arrange: Create financial data with EPV details
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
            '2023-12-31': {'revenue': 900000, 'net_income': 45000, 'eps': 4.5, 'dividend': 1.0, 'total_equity': 95000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for methodology explanation
    assert "**Methodology:**" in dossier
    assert "Uses 7-10 year average of net income" in dossier
    assert "Includes ALL years" in dossier
    assert "profitable and unprofitable" in dossier


def test_epv_methodology_explains_loss_years():
    """
    Test that EPV methodology explains why loss years are included.
    
    Validates: Requirement 8.2
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for explanation of loss years
    assert "Loss years reduce the average" in dossier
    assert "real value destruction" in dossier


def test_epv_methodology_shows_formula():
    """
    Test that EPV methodology shows the formula.
    
    Validates: Requirement 8.3
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for formula
    assert "USD50,000 / 10%" in dossier or "50000 / 10%" in dossier
    assert "EPV:" in dossier


def test_epv_methodology_lists_net_incomes():
    """
    Test that EPV methodology lists all years with their net income values.
    
    Validates: Requirement 8.4
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check that net incomes are listed
    assert "Net Incomes:" in dossier
    # Check for positive values
    assert "USD50,000" in dossier or "50000" in dossier
    # Check for negative values (loss years)
    assert "-USD10,000" in dossier or "-10000" in dossier


def test_epv_methodology_shows_normalized_earnings():
    """
    Test that EPV methodology shows normalized earnings amount.
    
    Validates: Requirement 8.5
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for normalized earnings
    assert "Normalized Earnings:" in dossier
    assert "average including losses" in dossier
    assert "USD50,000" in dossier or "50000" in dossier


def test_epv_methodology_includes_graham_quote():
    """
    Test that EPV methodology includes Graham quote about earning power.
    
    Validates: Requirement 8.6
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for Graham quote
    assert "Graham's Principle" in dossier
    assert "earning power" in dossier
    assert "past performance under varying conditions" in dossier or "business cycle" in dossier


def test_epv_methodology_notes_loss_years():
    """
    Test that EPV methodology notes which years were losses.
    
    Validates: Requirements 8.2, 8.4
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, -10000, -5000, 30000, 25000, 20000, 15000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check that loss years are noted
    assert "loss year" in dossier
    assert "2020" in dossier  # One of the loss years
    assert "2019" in dossier  # Another loss year
    assert "full business cycle performance" in dossier


def test_epv_methodology_all_profitable_years():
    """
    Test EPV methodology when all years are profitable.
    
    Validates: Requirements 8.1, 8.4
    """
    # Arrange
    financial_data = {
        'price': 100.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'history': {
            '2024-12-31': {'revenue': 1000000, 'net_income': 50000, 'eps': 5.0, 'dividend': 1.0, 'total_equity': 100000, 'shares_outstanding': 10000},
        },
        'warnings': []
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 50.0,
        'epv': 500000.0,
        'epv_details': {
            'epv': 500000.0,
            'epv_per_share': 50.0,
            'normalized_earnings': 50000.0,
            'years_used': 10,
            'years_included': ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31', '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31', '2015-12-31'],
            'net_incomes': [50000, 45000, 40000, 35000, 30000, 25000, 20000, 15000, 10000, 5000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 'N/A',
        'margin_of_safety': 50.0,
        'defensive_tests': {},
        'enterprising_tests': {},
        'warnings': []
    }
    
    anomalies = []
    
    # Act
    dossier = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for note about all profitable years
    assert "All 10 years were profitable" in dossier
    assert "consistent earnings power" in dossier
