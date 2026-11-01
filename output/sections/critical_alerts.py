"""Section 3: Critical Alerts — warnings from data assembly and metrics, plus EPS-growth anomalies."""

from typing import Any, Dict, List

from config.data_quality_config import ANNUAL_REPORT_MAX_AGE_MONTHS
from output.sections.base import DossierSection


class CriticalAlertsSection(DossierSection):
    """All accumulated warnings and statistical anomalies."""

    def __init__(self, financial_data: Dict[str, Any], metrics: Dict[str, Any], anomalies: List[str]):
        self.financial_data = financial_data
        self.metrics = metrics
        self.anomalies = anomalies

    def generate(self) -> List[str]:
        """Generate critical alerts section.
        
        This section includes:
        - Data quality warnings
        - Currency conversion details
        - Validation discrepancies
        - Statistical anomalies (modified Z-Score outliers)
        - Data requirements for normalized calculations
        
        Returns:
            List[str]: List of markdown lines for critical alerts section
        """
        lines = []
        
        lines.append("")
        lines.append("## SECTION 3: CRITICAL ALERTS")
        lines.append("")
        
        # Get warnings from financial data and metrics
        warnings = self.financial_data.get('warnings', [])
        metric_warnings = self.metrics.get('warnings', [])
        all_warnings = warnings + metric_warnings
        
        # Display warnings
        if all_warnings:
            lines.append("### Data Quality & Limitations:")
            for warning in all_warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        # Add normalized Graham Number data requirements
        lines.append("### Normalized Graham Number Requirements:")
        lines.append("- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data")
        lines.append("- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation")
        lines.append(f"- **Staleness Detection**: Annual reports older than {ANNUAL_REPORT_MAX_AGE_MONTHS:g} months trigger a data staleness warning")
        lines.append("- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed")
        lines.append("")
        
        # Display anomalies
        if self.anomalies:
            lines.append("### Statistical Anomalies (EPS growth, modified Z-Score > 3.5):")
            lines.append("*Metrics that deviate significantly from historical patterns*")
            lines.append("")
            for anomaly in self.anomalies:
                lines.append(f"- {anomaly}")
            lines.append("")
        
        # If no warnings or anomalies
        if not all_warnings and not self.anomalies:
            lines.append("No critical alerts or anomalies detected.")
            lines.append("")
        
        lines.append("---")
        
        return lines
