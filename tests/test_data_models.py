"""
Unit tests for Data Transfer Objects (DTOs).

Tests DTO instantiation, field access, type checking, optional field handling,
and dataclass equality/hashing.
"""

from core.data_models import (
    CompanyInfo,
    CurrencyInfo,
    FinancialData,
    EPVDetails,
    GrahamMetrics
)


class TestCompanyInfo:
    """Tests for CompanyInfo DTO."""
    
    def test_instantiation_with_valid_data(self):
        """Test CompanyInfo can be instantiated with valid data."""
        company = CompanyInfo(
            ticker="AAPL.US",
            exchange="US",
            ceo_name="Tim Cook",
            sector="Technology",
            industry="Consumer Electronics",
            employees=164000
        )
        
        assert company.ticker == "AAPL.US"
        assert company.exchange == "US"
        assert company.ceo_name == "Tim Cook"
        assert company.sector == "Technology"
        assert company.industry == "Consumer Electronics"
        assert company.employees == 164000
    
    def test_field_access(self):
        """Test all fields can be accessed."""
        company = CompanyInfo(
            ticker="YU.LSE",
            exchange="LSE",
            ceo_name="John Doe",
            sector="Utilities",
            industry="Water Utilities",
            employees=5000
        )
        
        # Access each field
        _ = company.ticker
        _ = company.exchange
        _ = company.ceo_name
        _ = company.sector
        _ = company.industry
        _ = company.employees
    
    def test_equality(self):
        """Test dataclass equality."""
        company1 = CompanyInfo(
            ticker="AAPL.US",
            exchange="US",
            ceo_name="Tim Cook",
            sector="Technology",
            industry="Consumer Electronics",
            employees=164000
        )
        
        company2 = CompanyInfo(
            ticker="AAPL.US",
            exchange="US",
            ceo_name="Tim Cook",
            sector="Technology",
            industry="Consumer Electronics",
            employees=164000
        )
        
        company3 = CompanyInfo(
            ticker="MSFT.US",
            exchange="US",
            ceo_name="Satya Nadella",
            sector="Technology",
            industry="Software",
            employees=221000
        )
        
        assert company1 == company2
        assert company1 != company3


class TestCurrencyInfo:
    """Tests for CurrencyInfo DTO."""
    
    def test_instantiation_with_valid_data(self):
        """Test CurrencyInfo can be instantiated with valid data."""
        currency = CurrencyInfo(
            unified_currency="GBP",
            original_stock_currency="GBX",
            financials_currency="GBP",
            dividend_currency="GBP",
            conversion_details=["London Fix applied: GBX → GBP (÷100)"]
        )
        
        assert currency.unified_currency == "GBP"
        assert currency.original_stock_currency == "GBX"
        assert currency.financials_currency == "GBP"
        assert currency.dividend_currency == "GBP"
        assert len(currency.conversion_details) == 1
    
    def test_empty_conversion_details(self):
        """Test CurrencyInfo with empty conversion details list."""
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        assert len(currency.conversion_details) == 0
    
    def test_field_access(self):
        """Test all fields can be accessed."""
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        _ = currency.unified_currency
        _ = currency.original_stock_currency
        _ = currency.financials_currency
        _ = currency.dividend_currency
        _ = currency.conversion_details


class TestEPVDetails:
    """Tests for EPVDetails DTO."""
    
    def test_instantiation_with_valid_data(self):
        """Test EPVDetails can be instantiated with valid data."""
        epv = EPVDetails(
            epv=419456000.0,
            epv_per_share=10.82,
            normalized_earnings=41945600.0,
            years_used=10,
            years_included=["2023-12-31", "2022-12-31", "2021-12-31"],
            net_incomes=[50000000.0, 45000000.0, 40000000.0],
            cost_of_capital=0.10
        )
        
        assert epv.epv == 419456000.0
        assert epv.epv_per_share == 10.82
        assert epv.normalized_earnings == 41945600.0
        assert epv.years_used == 10
        assert len(epv.years_included) == 3
        assert len(epv.net_incomes) == 3
        assert epv.cost_of_capital == 0.10
    
    def test_field_access(self):
        """Test all fields can be accessed."""
        epv = EPVDetails(
            epv=100000.0,
            epv_per_share=5.0,
            normalized_earnings=10000.0,
            years_used=7,
            years_included=["2023-12-31"],
            net_incomes=[10000.0],
            cost_of_capital=0.10
        )
        
        _ = epv.epv
        _ = epv.epv_per_share
        _ = epv.normalized_earnings
        _ = epv.years_used
        _ = epv.years_included
        _ = epv.net_incomes
        _ = epv.cost_of_capital


class TestGrahamMetrics:
    """Tests for GrahamMetrics DTO."""
    
    def test_instantiation_with_valid_data(self):
        """Test GrahamMetrics can be instantiated with valid data."""
        epv_details = EPVDetails(
            epv=419456000.0,
            epv_per_share=10.82,
            normalized_earnings=41945600.0,
            years_used=10,
            years_included=["2023-12-31"],
            net_incomes=[41945600.0],
            cost_of_capital=0.10
        )
        
        metrics = GrahamMetrics(
            graham_number=15.50,
            epv=419456000.0,
            epv_details=epv_details,
            net_net_value=12.30,
            margin_of_safety=25.5,
            verdict="STRONG BUY (Undervalued)",
            defensive_tests={
                'earnings_stability': 'PASS',
                'current_ratio': 'PASS',
                'debt_to_assets': 'PASS',
                'dividend_record': 'PASS',
                'earnings_growth': 'PASS',
                'pe_ratio': 'PASS',
                'pb_ratio': 'PASS'
            },
            enterprising_tests={
                'earnings_stability': 'PASS',
                'current_ratio': 'PASS',
                'debt_to_assets': 'PASS',
                'dividend_record': 'PASS',
                'earnings_growth': 'N/A - Not Required',
                'price_test': 'PASS'
            },
            warnings=[]
        )
        
        assert metrics.graham_number == 15.50
        assert metrics.epv == 419456000.0
        assert isinstance(metrics.epv_details, EPVDetails)
        assert metrics.net_net_value == 12.30
        assert metrics.margin_of_safety == 25.5
        assert metrics.verdict == "STRONG BUY (Undervalued)"
        assert len(metrics.defensive_tests) == 7
        assert len(metrics.enterprising_tests) == 6
        assert len(metrics.warnings) == 0
    
    def test_instantiation_with_na_values(self):
        """Test GrahamMetrics with N/A string values."""
        epv_details = EPVDetails(
            epv=0.0,
            epv_per_share=0.0,
            normalized_earnings=0.0,
            years_used=0,
            years_included=[],
            net_incomes=[],
            cost_of_capital=0.10
        )
        
        metrics = GrahamMetrics(
            graham_number="N/A",
            epv=0.0,
            epv_details=epv_details,
            net_net_value="N/A",
            margin_of_safety="N/A",
            verdict="Rely on EPV - Negative Equity",
            defensive_tests={},
            enterprising_tests={},
            warnings=["Negative Tangible Book Value - Company has negative equity"]
        )
        
        assert metrics.graham_number == "N/A"
        assert metrics.net_net_value == "N/A"
        assert metrics.margin_of_safety == "N/A"
        assert len(metrics.warnings) == 1
    
    def test_field_access(self):
        """Test all fields can be accessed."""
        epv_details = EPVDetails(
            epv=100000.0,
            epv_per_share=5.0,
            normalized_earnings=10000.0,
            years_used=7,
            years_included=[],
            net_incomes=[],
            cost_of_capital=0.10
        )
        
        metrics = GrahamMetrics(
            graham_number=10.0,
            epv=100000.0,
            epv_details=epv_details,
            net_net_value=8.0,
            margin_of_safety=20.0,
            verdict="UNDERVALUED",
            defensive_tests={},
            enterprising_tests={},
            warnings=[]
        )
        
        _ = metrics.graham_number
        _ = metrics.epv
        _ = metrics.epv_details
        _ = metrics.net_net_value
        _ = metrics.margin_of_safety
        _ = metrics.verdict
        _ = metrics.defensive_tests
        _ = metrics.enterprising_tests
        _ = metrics.warnings


class TestFinancialData:
    """Tests for FinancialData DTO."""
    
    def test_instantiation_with_valid_data(self):
        """Test FinancialData can be instantiated with valid data."""
        company = CompanyInfo(
            ticker="AAPL.US",
            exchange="US",
            ceo_name="Tim Cook",
            sector="Technology",
            industry="Consumer Electronics",
            employees=164000
        )
        
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        financial_data = FinancialData(
            company=company,
            currency=currency,
            price=150.50,
            price_source="yfinance",
            history={
                "2023-12-31": {
                    "revenue": 383285000000.0,
                    "net_income": 96995000000.0,
                    "eps": 6.13,
                    "dividend": 0.96,
                    "total_equity": 62146000000.0,
                    "shares_outstanding": 15821900000.0
                }
            },
            warnings=[],
            dividend_per_share=0.96,
            dividend_yield=0.0064,
            pe_ratio=24.55,
            book_value_per_share=3.93,
            roe=0.156,
            roa=0.089,
            profit_margin=0.253,
            price_to_book=6.25,
            enterprise_value=2900000000000.0,
            insider_ownership=0.07,
            institutional_ownership=60.5,
            beta=1.25,
            week_52_high=199.62,
            week_52_low=124.17,
            forward_dividend_rate=1.00,
            dividend_source="cash_flow",
            dividend_sources={"2023": "cash_flow"}
        )
        
        assert financial_data.company.ticker == "AAPL.US"
        assert financial_data.currency.unified_currency == "USD"
        assert financial_data.price == 150.50
        assert financial_data.price_source == "yfinance"
        assert len(financial_data.history) == 1
        assert financial_data.dividend_per_share == 0.96
        assert financial_data.pe_ratio == 24.55
    
    def test_optional_field_handling(self):
        """Test FinancialData with optional forward_dividend_rate as None."""
        company = CompanyInfo(
            ticker="TEST.US",
            exchange="US",
            ceo_name="Test CEO",
            sector="Test",
            industry="Test",
            employees=100
        )
        
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        financial_data = FinancialData(
            company=company,
            currency=currency,
            price=10.0,
            price_source="EODHD",
            history={},
            warnings=[],
            dividend_per_share=0.0,
            dividend_yield=0.0,
            pe_ratio=0.0,
            book_value_per_share=0.0,
            roe=0.0,
            roa=0.0,
            profit_margin=0.0,
            price_to_book=0.0,
            enterprise_value=0.0,
            insider_ownership=0.0,
            institutional_ownership=0.0,
            beta=0.0,
            week_52_high=0.0,
            week_52_low=0.0,
            forward_dividend_rate=None,  # Optional field
            dividend_source="unknown",
            dividend_sources={}
        )
        
        assert financial_data.forward_dividend_rate is None
    
    def test_field_access(self):
        """Test all fields can be accessed."""
        company = CompanyInfo(
            ticker="TEST.US",
            exchange="US",
            ceo_name="Test",
            sector="Test",
            industry="Test",
            employees=0
        )
        
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        financial_data = FinancialData(
            company=company,
            currency=currency,
            price=0.0,
            price_source="Missing",
            history={},
            warnings=[],
            dividend_per_share=0.0,
            dividend_yield=0.0,
            pe_ratio=0.0,
            book_value_per_share=0.0,
            roe=0.0,
            roa=0.0,
            profit_margin=0.0,
            price_to_book=0.0,
            enterprise_value=0.0,
            insider_ownership=0.0,
            institutional_ownership=0.0,
            beta=0.0,
            week_52_high=0.0,
            week_52_low=0.0,
            forward_dividend_rate=None,
            dividend_source="unknown",
            dividend_sources={}
        )
        
        # Access all fields
        _ = financial_data.company
        _ = financial_data.currency
        _ = financial_data.price
        _ = financial_data.price_source
        _ = financial_data.history
        _ = financial_data.warnings
        _ = financial_data.dividend_per_share
        _ = financial_data.dividend_yield
        _ = financial_data.pe_ratio
        _ = financial_data.book_value_per_share
        _ = financial_data.roe
        _ = financial_data.roa
        _ = financial_data.profit_margin
        _ = financial_data.price_to_book
        _ = financial_data.enterprise_value
        _ = financial_data.insider_ownership
        _ = financial_data.institutional_ownership
        _ = financial_data.beta
        _ = financial_data.week_52_high
        _ = financial_data.week_52_low
        _ = financial_data.forward_dividend_rate
        _ = financial_data.dividend_source
        _ = financial_data.dividend_sources
    
    def test_equality(self):
        """Test dataclass equality for nested structures."""
        company1 = CompanyInfo(
            ticker="AAPL.US",
            exchange="US",
            ceo_name="Tim Cook",
            sector="Technology",
            industry="Consumer Electronics",
            employees=164000
        )
        
        company2 = CompanyInfo(
            ticker="AAPL.US",
            exchange="US",
            ceo_name="Tim Cook",
            sector="Technology",
            industry="Consumer Electronics",
            employees=164000
        )
        
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        financial_data1 = FinancialData(
            company=company1,
            currency=currency,
            price=150.0,
            price_source="yfinance",
            history={},
            warnings=[],
            dividend_per_share=0.0,
            dividend_yield=0.0,
            pe_ratio=0.0,
            book_value_per_share=0.0,
            roe=0.0,
            roa=0.0,
            profit_margin=0.0,
            price_to_book=0.0,
            enterprise_value=0.0,
            insider_ownership=0.0,
            institutional_ownership=0.0,
            beta=0.0,
            week_52_high=0.0,
            week_52_low=0.0,
            forward_dividend_rate=None,
            dividend_source="unknown",
            dividend_sources={}
        )
        
        financial_data2 = FinancialData(
            company=company2,
            currency=currency,
            price=150.0,
            price_source="yfinance",
            history={},
            warnings=[],
            dividend_per_share=0.0,
            dividend_yield=0.0,
            pe_ratio=0.0,
            book_value_per_share=0.0,
            roe=0.0,
            roa=0.0,
            profit_margin=0.0,
            price_to_book=0.0,
            enterprise_value=0.0,
            insider_ownership=0.0,
            institutional_ownership=0.0,
            beta=0.0,
            week_52_high=0.0,
            week_52_low=0.0,
            forward_dividend_rate=None,
            dividend_source="unknown",
            dividend_sources={}
        )
        
        assert financial_data1 == financial_data2
    
    def test_history_structure(self):
        """Test that history dictionary has correct structure."""
        company = CompanyInfo(
            ticker="TEST.US",
            exchange="US",
            ceo_name="Test",
            sector="Test",
            industry="Test",
            employees=0
        )
        
        currency = CurrencyInfo(
            unified_currency="USD",
            original_stock_currency="USD",
            financials_currency="USD",
            dividend_currency="USD",
            conversion_details=[]
        )
        
        history = {
            "2023-12-31": {
                "revenue": 1000000.0,
                "net_income": 100000.0,
                "eps": 1.0,
                "dividend": 0.5,
                "total_equity": 500000.0,
                "shares_outstanding": 100000.0,
                "current_assets": 300000.0,
                "current_liabilities": 100000.0,
                "total_liabilities": 200000.0,
                "long_term_debt": 100000.0
            },
            "2022-12-31": {
                "revenue": 900000.0,
                "net_income": 90000.0,
                "eps": 0.9,
                "dividend": 0.45,
                "total_equity": 450000.0,
                "shares_outstanding": 100000.0,
                "current_assets": 270000.0,
                "current_liabilities": 90000.0,
                "total_liabilities": 180000.0,
                "long_term_debt": 90000.0
            }
        }
        
        financial_data = FinancialData(
            company=company,
            currency=currency,
            price=10.0,
            price_source="EODHD",
            history=history,
            warnings=[],
            dividend_per_share=0.5,
            dividend_yield=0.05,
            pe_ratio=10.0,
            book_value_per_share=5.0,
            roe=0.2,
            roa=0.1,
            profit_margin=0.1,
            price_to_book=2.0,
            enterprise_value=1000000.0,
            insider_ownership=10.0,
            institutional_ownership=50.0,
            beta=1.0,
            week_52_high=12.0,
            week_52_low=8.0,
            forward_dividend_rate=0.5,
            dividend_source="cash_flow",
            dividend_sources={"2023": "cash_flow", "2022": "cash_flow"}
        )
        
        assert len(financial_data.history) == 2
        assert "2023-12-31" in financial_data.history
        assert "2022-12-31" in financial_data.history
        assert financial_data.history["2023-12-31"]["revenue"] == 1000000.0
        assert financial_data.history["2022-12-31"]["eps"] == 0.9
