"""Graham tests section generator for dossier.

This module generates the Graham investor tests sections of the stock analysis dossier,
including both defensive and enterprising investor tests.
"""

from typing import List, Dict, Any


class GrahamTestsSection:
    """Generates the Graham investor tests sections of the dossier.
    
    This section includes:
    - Section 4: Graham Defensive Investor Tests
    - Section 5: Graham Enterprising Investor Tests
    
    Requirements: 2.6
    """
    
    def __init__(self, metrics: Dict[str, Any]):
        """Initialize Graham tests section.
        
        Args:
            metrics: Dictionary containing Graham metrics (GrahamMetrics DTO)
        """
        self.metrics = metrics
    
    def generate(self) -> List[str]:
        """Generate Graham tests sections content.
        
        Returns:
            List[str]: List of markdown lines for Graham tests sections
        """
        lines = []
        
        # Section 4: Defensive Tests
        lines.extend(self._generate_defensive_tests())
        
        # Section 5: Enterprising Tests
        lines.extend(self._generate_enterprising_tests())
        
        return lines
    
    def _generate_defensive_tests(self) -> List[str]:
        """Generate Section 4: Graham Defensive Investor Tests.
        
        Returns:
            List[str]: List of markdown lines for defensive tests section
        """
        lines = []
        
        lines.append("")
        lines.append("## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS")
        lines.append("")
        
        # Get test results
        defensive_tests = self.metrics.get('defensive_tests', {})
        
        # Test 1: Earnings Stability
        earnings_stability = defensive_tests.get('earnings_stability', 'N/A')
        lines.append(f"1. **Earnings Stability**: {earnings_stability}")
        lines.append("   - Criterion: Positive earnings in each of the past 10 years")
        
        # Test 2: Current Ratio
        current_ratio = defensive_tests.get('current_ratio', 'N/A')
        lines.append(f"2. **Current Ratio**: {current_ratio}")
        lines.append("   - Criterion: Current Ratio ≥ 2.0")
        
        # Test 3: Debt to Assets
        debt_to_assets = defensive_tests.get('debt_to_assets', 'N/A')
        lines.append(f"3. **Debt to Assets**: {debt_to_assets}")
        lines.append("   - Criterion: Long-term Debt < Net Current Assets")
        
        # Test 4: Dividend Record
        dividend_record = defensive_tests.get('dividend_record', 'N/A')
        lines.append(f"4. **Dividend Record**: {dividend_record}")
        lines.append("   - Criterion: Uninterrupted dividend payments for at least 20 years")
        
        # Test 5: Earnings Growth
        earnings_growth = defensive_tests.get('earnings_growth', 'N/A')
        lines.append(f"5. **Earnings Growth**: {earnings_growth}")
        lines.append("   - Criterion: Earnings growth ≥ 33% over 10 years")
        
        # Test 6: P/E Ratio
        pe_ratio = defensive_tests.get('pe_ratio', 'N/A')
        lines.append(f"6. **P/E Ratio**: {pe_ratio}")
        lines.append("   - Criterion: P/E Ratio < 15")
        
        # Test 7: P/B Ratio
        pb_ratio = defensive_tests.get('pb_ratio', 'N/A')
        lines.append(f"7. **P/B Ratio**: {pb_ratio}")
        lines.append("   - Criterion: Price/Book Ratio < 1.5")
        
        # Test 8: Combined P/E × P/B Test (NEW)
        combined_test = self.metrics.get('combined_pe_pb_test', {})
        if combined_test and isinstance(combined_test, dict):
            result = combined_test.get('result', 'N/A')
            product = combined_test.get('product')
            pe = combined_test.get('pe_ratio')
            pb = combined_test.get('pb_ratio')
            
            lines.append(f"8. **Combined P/E × P/B Test**: {result}")
            if product != 'N/A' and pe != 'N/A' and pb != 'N/A':
                lines.append(f"   - P/E Ratio: {pe:.2f}")
                lines.append(f"   - P/B Ratio: {pb:.2f}")
                lines.append(f"   - Product: {product:.2f} (must be ≤ 22.5)")
                lines.append("   - *Graham specified that P/E × P/B should not exceed 22.5. This provides flexibility: a company can have a higher P/E if it has a low P/B, or vice versa.*")
            else:
                lines.append("   - Criterion: P/E × P/B ≤ 22.5")
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _generate_enterprising_tests(self) -> List[str]:
        """Generate Section 5: Graham Enterprising Investor Tests.
        
        Returns:
            List[str]: List of markdown lines for enterprising tests section
        """
        lines = []
        
        lines.append("")
        lines.append("## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS")
        lines.append("")
        
        # Get test results
        enterprising_tests = self.metrics.get('enterprising_tests', {})
        
        # Test 1: Earnings Stability
        earnings_stability = enterprising_tests.get('earnings_stability', 'N/A')
        lines.append(f"1. **Earnings Stability**: {earnings_stability}")
        lines.append("   - Criterion: Profitability in most recent year and 5 of past 7 years")
        
        # Test 2: Current Ratio
        current_ratio = enterprising_tests.get('current_ratio', 'N/A')
        lines.append(f"2. **Current Ratio**: {current_ratio}")
        lines.append("   - Criterion: Current Ratio > 1.5")
        
        # Test 3: Debt to Assets
        debt_to_assets = enterprising_tests.get('debt_to_assets', 'N/A')
        lines.append(f"3. **Debt to Assets**: {debt_to_assets}")
        lines.append("   - Criterion: Debt < 110% of Net Current Assets")
        
        # Test 4: Dividend Record
        dividend_record = enterprising_tests.get('dividend_record', 'N/A')
        lines.append(f"4. **Dividend Record**: {dividend_record}")
        lines.append("   - Criterion: Currently pays a dividend (last year > 0)")
        
        # Test 5: Earnings Growth
        earnings_growth = enterprising_tests.get('earnings_growth', 'N/A - Not Required')
        lines.append(f"5. **Earnings Growth**: {earnings_growth}")
        
        # Test 6: Price Test
        price_test = enterprising_tests.get('price_test', 'N/A')
        lines.append(f"6. **Price Test**: {price_test}")
        lines.append("   - Criterion: P/E < 10 OR Price < 120% of Net Tangible Assets")
        
        lines.append("")
        lines.append("**Note on Earnings Growth:** Earnings growth is intentionally not required for Enterprising Investors per Graham's methodology. Unlike Defensive Investors (who require 7 tests including ≥33% earnings growth over 10 years), Enterprising Investors require only 6 tests focused on current financial strength and price. Graham's logic: Enterprising investors actively seek bargains, turnarounds, or cyclical companies trading below intrinsic value—situations where historical growth may be absent but current fundamentals and price create opportunity.")
        lines.append("")
        lines.append("---")
        
        return lines
