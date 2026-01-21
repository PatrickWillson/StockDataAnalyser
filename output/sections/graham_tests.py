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
        
        # List all defensive tests
        for test, result in self.metrics['defensive_tests'].items():
            lines.append(f"- {test.replace('_', ' ').title()}: {result}")
        
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
        
        # List all enterprising tests
        for test, result in self.metrics.get('enterprising_tests', {}).items():
            lines.append(f"- {test.replace('_', ' ').title()}: {result}")
        
        lines.append("")
        lines.append("**Note on Earnings Growth:** Earnings growth is intentionally not required for Enterprising Investors per Graham's methodology. Unlike Defensive Investors (who require 7 tests including ≥33% earnings growth over 10 years), Enterprising Investors require only 6 tests focused on current financial strength and price. Graham's logic: Enterprising investors actively seek bargains, turnarounds, or cyclical companies trading below intrinsic value—situations where historical growth may be absent but current fundamentals and price create opportunity.")
        lines.append("")
        lines.append("---")
        
        return lines
