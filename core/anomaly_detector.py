"""
Anomaly Detector - Statistical outlier detection for financial data.

Flags years whose EPS growth is an outlier among the company's own growth rates, using the
modified Z-score 0.6745 × (x − median) / MAD (Iglewicz & Hoaglin, 1993; NIST/SEMATECH
e-Handbook of Statistical Methods §1.3.5.17), flagged above 3.5. Median and MAD are not pulled
by the outlier itself, unlike the mean and standard deviation, so a single extreme year can be
detected even in a short history. Data-quality information only; not a Graham criterion.
"""

import statistics
from typing import List

from config.data_quality_config import (ANOMALY_MIN_DATA_POINTS, ANOMALY_MIN_SPREAD_PP,
                                        ANOMALY_Z_SCORE_THRESHOLD, FINANCIAL_HISTORY_YEARS)
from core.history import has_income_data

# Scales MAD to the standard deviation of normally distributed data
MAD_SCALE = 0.6745


class AnomalyDetector:
    """Detects outlying EPS growth years with the modified Z-score."""

    Z_SCORE_THRESHOLD = ANOMALY_Z_SCORE_THRESHOLD

    def __init__(self, financial_data: dict):
        """
        Args:
            financial_data: Dictionary containing ticker, price, currency, history, etc.
        """
        self.data = financial_data

    @staticmethod
    def modified_z_scores(values: List[float]) -> List[float]:
        """Modified Z-score of each value (values in percentage points)."""
        median = statistics.median(values)
        # MAD floored at ANOMALY_MIN_SPREAD_PP: near-constant growth must not make immaterial
        # differences look extreme (and a zero MAD must not divide by zero)
        mad = max(statistics.median(abs(v - median) for v in values), ANOMALY_MIN_SPREAD_PP)
        return [MAD_SCALE * (v - median) / mad for v in values]

    def scan(self) -> List[str]:
        """
        Year-over-year EPS growth between consecutive reported years shown in the financial
        history table (dividend-only placeholder rows skipped), flagged when |modified Z| > 3.5.

        Returns:
            Descriptions such as "Year 2020-12-31: EPS growth modified Z-Score = 4.10 (Outlier: +250.0%
            vs median +8.0%)"
        """
        history = self.data.get('history', {})
        table_years = sorted(history.keys(), reverse=True)[:FINANCIAL_HISTORY_YEARS]
        years = [year for year in table_years if has_income_data(history[year])]
        if len(years) < ANOMALY_MIN_DATA_POINTS:
            return []

        growth_rates = []
        growth_years = []
        for current_year, previous_year in zip(years, years[1:]):
            previous_eps = history[previous_year].get('eps', 0.0)
            # Growth from a zero or negative base is not meaningful
            if previous_eps <= 0:
                continue
            current_eps = history[current_year].get('eps', 0.0)
            growth_rates.append((current_eps - previous_eps) / previous_eps * 100)
            growth_years.append(current_year)

        if len(growth_rates) < ANOMALY_MIN_DATA_POINTS:
            return []

        median_growth = statistics.median(growth_rates)
        anomalies = []
        for year, growth, z_score in zip(growth_years, growth_rates, self.modified_z_scores(growth_rates)):
            if abs(z_score) > self.Z_SCORE_THRESHOLD:
                anomalies.append(f"Year {year}: EPS growth modified Z-Score = {z_score:.2f} "
                                 f"(Outlier: {growth:+.1f}% vs median {median_growth:+.1f}%)")
        return anomalies
