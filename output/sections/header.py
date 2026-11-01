"""Dossier header: ticker, date, source, company metadata, latest annual data year, currency."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from output.sections.base import DossierSection
from core.models import FinancialData, or_default
from core.report_context import ReportContext, build_report_context


class HeaderSection(DossierSection):
    """The '# STOCK ANALYSIS DOSSIER' block at the top of the dossier."""

    def __init__(self, ticker: str, financial_data: Dict[str, Any], context: Optional[ReportContext] = None):
        self.ticker = ticker
        self.financial_data = FinancialData.from_dict(financial_data)
        self.context = context or build_report_context(financial_data)

    def generate(self) -> List[str]:
        """Generate dossier header with metadata.
        
        The header includes:
        - Ticker symbol
        - Generation date
        - Data source
        - CEO name
        - Sector and industry
        - Employee count
        - Most recent annual data year
        - Currency information
        
        Returns:
            List[str]: List of markdown lines for the header
        """
        lines = []
        
        # Extract metadata
        unified_currency = or_default(self.financial_data.currency, 'USD')
        original_stock_currency = or_default(self.financial_data.original_stock_currency, unified_currency)
        ceo_name = or_default(self.financial_data.ceo_name, 'N/A')
        sector = or_default(self.financial_data.sector, 'N/A')
        industry = or_default(self.financial_data.industry, 'N/A')
        employees = or_default(self.financial_data.employees, 0)
        data_source = or_default(self.financial_data.data_source, 'N/A')
        
        # Title and basic metadata
        lines.append(f"# STOCK ANALYSIS DOSSIER: {self.ticker}")
        lines.append(f"# DATE: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"# SOURCE: {data_source} (Tier 1 Data)")
        lines.append(f"# CEO: {ceo_name}")
        lines.append(f"# SECTOR: {sector} | INDUSTRY: {industry}")
        lines.append(f"# EMPLOYEES: {employees:,}" if employees > 0 else "# EMPLOYEES: N/A")
        
        # Add data freshness note - use most recent year with actual financial data
        if self.context.latest_year_label:
            lines.append(f"# MOST RECENT ANNUAL DATA: {self.context.latest_year_label}")
        
        # Add currency note if conversion was applied
        if original_stock_currency != unified_currency:
            lines.append(f"# CURRENCY: All values in {unified_currency} (stock trades in {original_stock_currency})")
        else:
            lines.append(f"# CURRENCY: {unified_currency}")
        
        lines.append("")
        lines.append("---")
        
        return lines
