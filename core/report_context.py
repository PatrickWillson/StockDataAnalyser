"""
The dossier's view model: values the output sections display, derived once in core so that
sections only format (M5). Built by DossierGenerator and passed to every section; a section
built on its own (e.g. in a unit test) builds it from the same inputs.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from core.history import has_statement_data, latest_year


@dataclass(frozen=True)
class ReportContext:
    latest_year: Optional[str]                 # newest history key with statement data ('YYYY-MM-DD')
    latest_row: Mapping[str, Any] = field(default_factory=dict)

    @property
    def latest_year_label(self) -> Optional[str]:
        """The latest reported year as 'YYYY', or None."""
        return self.latest_year.split('-')[0] if self.latest_year else None


def build_report_context(financial_data: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None) -> ReportContext:
    """Derive the display values from the assembled financial data (and metrics)."""
    history = financial_data.get('history') or {}
    year = latest_year(history, sorted(history.keys(), reverse=True), has_statement_data)
    return ReportContext(latest_year=year, latest_row=history[year] if year else {})
