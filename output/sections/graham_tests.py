"""Graham tests section generator for dossier.

This module generates the Graham investor tests sections of the stock analysis dossier,
including both defensive and enterprising investor tests.
"""

from typing import List, Dict, Any
from config.graham_constants import GRAHAM_MULTIPLIER
from config.investor_thresholds import DEFENSIVE, ENTERPRISING
from output.sections.base import DossierSection


class GrahamTestsSection(DossierSection):
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
        lines.append(f"   - Criterion: Positive earnings in each of the past {DEFENSIVE.EARNINGS_STABILITY_YEARS} years")
        
        # Test 2: Current Ratio
        current_ratio = defensive_tests.get('current_ratio', 'N/A')
        lines.append(f"2. **Current Ratio**: {current_ratio}")
        public_utility = self.metrics.get('public_utility', False)
        if public_utility:
            lines.append("   - Criterion: Not applied to public utilities (Graham)")
        else:
            lines.append(f"   - Criterion: Current Ratio ≥ {DEFENSIVE.MIN_CURRENT_RATIO:.1f}")
        
        # Test 3: Debt to Assets
        debt_to_assets = defensive_tests.get('debt_to_assets', 'N/A')
        lines.append(f"3. **Debt to Assets**: {debt_to_assets}")
        if public_utility:
            lines.append(f"   - Criterion (public utility): Total debt ≤ {DEFENSIVE.UTILITY_MAX_DEBT_TO_EQUITY:g} × stockholders' equity at book value")
        else:
            lines.append("   - Criterion: Long-term debt ≤ net current assets (current assets − current liabilities)")
        
        # Test 4: Dividend Record
        dividend_record = defensive_tests.get('dividend_record', 'N/A')
        lines.append(f"4. **Dividend Record**: {dividend_record}")
        lines.append(f"   - Criterion: Uninterrupted dividend payments for at least {DEFENSIVE.MIN_DIVIDEND_YEARS} years")
        
        # Test 5: Earnings Growth
        earnings_growth = defensive_tests.get('earnings_growth', 'N/A')
        lines.append(f"5. **Earnings Growth**: {earnings_growth}")
        lines.append(f"   - Criterion: Average EPS of the latest {DEFENSIVE.EARNINGS_GROWTH_AVERAGE_YEARS} reported years "
                     f"at least one-third ({DEFENSIVE.MIN_EARNINGS_GROWTH - 1:.1%}) above the average of the reported "
                     f"years {DEFENSIVE.EARNINGS_GROWTH_BASE_OFFSET}-{DEFENSIVE.EARNINGS_GROWTH_BASE_OFFSET + DEFENSIVE.EARNINGS_GROWTH_AVERAGE_YEARS - 1} back")
        
        # Test 6: P/E Ratio
        pe_ratio = defensive_tests.get('pe_ratio', 'N/A')
        lines.append(f"6. **P/E Ratio**: {pe_ratio}")
        lines.append(f"   - Criterion: Price ≤ {DEFENSIVE.MAX_PE_RATIO:g} × average EPS of the last 3 reported years")
        
        # Test 7: P/B Ratio
        pb_ratio = defensive_tests.get('pb_ratio', 'N/A')
        lines.append(f"7. **P/B Ratio**: {pb_ratio}")
        lines.append(f"   - Criterion: Price ≤ {DEFENSIVE.MAX_PB_RATIO:g} × tangible book value per share, "
                     f"or P/E (3-year average EPS) × P/B ≤ {GRAHAM_MULTIPLIER:g}")
        
        # Test 8: Combined P/E × P/B Test (NEW)
        combined_test = self.metrics.get('combined_pe_pb_test', {})
        if combined_test and isinstance(combined_test, dict):
            result = combined_test.get('result', 'N/A')
            product = combined_test.get('product')
            pe = combined_test.get('pe_ratio')
            pb = combined_test.get('pb_ratio')
            
            lines.append(f"8. **Combined P/E × P/B Test** (criterion 7 alternative): {result}")
            if product != 'N/A' and pe != 'N/A' and pb != 'N/A':
                lines.append(f"   - P/E Ratio (3-year average EPS): {pe:.2f}")
                lines.append(f"   - P/B Ratio (tangible book): {pb:.2f}")
                lines.append(f"   - Product: {product:.2f} (must be ≤ {GRAHAM_MULTIPLIER:g})")
                lines.append(f"   - *Graham: \"a multiplier of earnings below {DEFENSIVE.MAX_PE_RATIO:g} could justify a correspondingly higher multiplier of assets\"; the product should not exceed {GRAHAM_MULTIPLIER:g}. It relaxes the P/B limit only; the P/E limit (criterion 6) still applies.*")
            else:
                lines.append(f"   - Criterion: P/E × P/B ≤ {GRAHAM_MULTIPLIER:g}")
        
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
        lines.append(f"   - Criterion: No deficit in the last {ENTERPRISING.EARNINGS_STABILITY_YEARS} years")
        
        # Test 2: Current Ratio
        current_ratio = enterprising_tests.get('current_ratio', 'N/A')
        lines.append(f"2. **Current Ratio**: {current_ratio}")
        lines.append(f"   - Criterion: Current Ratio ≥ {ENTERPRISING.MIN_CURRENT_RATIO:.1f}")
        
        # Test 3: Debt to Assets
        debt_to_assets = enterprising_tests.get('debt_to_assets', 'N/A')
        lines.append(f"3. **Debt to Assets**: {debt_to_assets}")
        lines.append(f"   - Criterion: Long-term debt ≤ {ENTERPRISING.MAX_DEBT_ASSETS:.0%} of net current assets (current assets − current liabilities)")
        
        # Test 4: Dividend Record
        dividend_record = enterprising_tests.get('dividend_record', 'N/A')
        lines.append(f"4. **Dividend Record**: {dividend_record}")
        lines.append("   - Criterion: Currently pays a dividend (last year > 0)")
        
        # Test 5: Earnings Growth
        earnings_growth = enterprising_tests.get('earnings_growth', 'N/A')
        lines.append(f"5. **Earnings Growth**: {earnings_growth}")
        lines.append(f"   - Criterion: Latest EPS above the EPS {ENTERPRISING.EARNINGS_GROWTH_YEARS} reported years earlier")
        
        # Test 6: Price Test
        price_test = enterprising_tests.get('price_test', 'N/A')
        lines.append(f"6. **Price Test**: {price_test}")
        lines.append(f"   - Criterion: P/E < {ENTERPRISING.MAX_PE_RATIO:g} AND Price < {ENTERPRISING.MAX_PB_RATIO:.0%} of Net Tangible Assets")
        
        lines.append("")
        lines.append("---")
        
        return lines
