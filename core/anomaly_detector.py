"""
Anomaly Detector - Statistical outlier detection for financial data.

This module detects statistical anomalies in earnings data using Z-Score analysis.
Anomalies are flagged when EPS growth rates deviate significantly from the mean.
"""

import math
from typing import Dict, List, Any


class AnomalyDetector:
    """
    Detects statistical anomalies in financial data using Z-Score analysis.
    
    Flags years where EPS growth has |Z-Score| > 2.0 as anomalies.
    """
    
    # Z-Score threshold for anomaly detection
    Z_SCORE_THRESHOLD = 2.0
    
    def __init__(self, financial_data: dict):
        """
        Initialize anomaly detector with financial data.
        
        Args:
            financial_data: Dictionary containing ticker, price, currency, history, etc.
        """
        self.data = financial_data
    
    def calculate_z_score(self, value: float, mean: float, std_dev: float) -> float:
        """
        Calculate Z-Score for a value.
        
        Formula: Z-Score = (value - mean) / std_dev
        
        Args:
            value: The value to calculate Z-Score for
            mean: Mean of the dataset
            std_dev: Standard deviation of the dataset
        
        Returns:
            Z-Score value
        """
        if std_dev == 0:
            return 0.0
        
        return (value - mean) / std_dev
    
    def scan(self) -> List[str]:
        """
        Scan EPS history for statistical anomalies.
        
        Detects anomalies by:
        1. Calculating EPS growth rates year-over-year
        2. Computing mean and standard deviation of growth rates
        3. Flagging years with |Z-Score| > 2.0 as anomalies
        
        Returns:
            List of anomaly descriptions, e.g.:
            ["Year 2020: EPS growth Z-Score = 3.2 (Outlier)"]
        """
        anomalies = []
        
        history = self.data.get('history', {})
        if not history:
            return anomalies
        
        # Get years sorted descending (most recent first)
        years = sorted(history.keys(), reverse=True)
        
        # Need at least 3 years to detect anomalies
        if len(years) < 3:
            return anomalies
        
        # Calculate EPS growth rates year-over-year
        growth_rates = []
        growth_years = []
        
        for i in range(len(years) - 1):
            current_year = years[i]
            previous_year = years[i + 1]
            
            current_eps = history[current_year].get('eps', 0.0)
            previous_eps = history[previous_year].get('eps', 0.0)
            
            # Skip if previous EPS is zero or negative (can't calculate growth rate)
            if previous_eps <= 0:
                continue
            
            # Calculate growth rate as percentage change
            growth_rate = ((current_eps - previous_eps) / previous_eps) * 100
            growth_rates.append(growth_rate)
            growth_years.append(current_year)
        
        # Need at least 3 growth rates to calculate meaningful statistics
        if len(growth_rates) < 3:
            return anomalies
        
        # Compute mean and standard deviation
        mean = sum(growth_rates) / len(growth_rates)
        
        # Calculate standard deviation
        variance = sum((x - mean) ** 2 for x in growth_rates) / len(growth_rates)
        std_dev = math.sqrt(variance)
        
        # Flag anomalies where |Z-Score| > 2.0
        for i, growth_rate in enumerate(growth_rates):
            z_score = self.calculate_z_score(growth_rate, mean, std_dev)
            
            if abs(z_score) > self.Z_SCORE_THRESHOLD:
                year = growth_years[i]
                anomalies.append(
                    f"Year {year}: EPS growth Z-Score = {z_score:.2f} (Outlier)"
                )
        
        return anomalies
