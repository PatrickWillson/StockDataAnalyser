# Stock Data Analyser

A deterministic financial analysis engine that implements Benjamin Graham's value investing methodology with mathematical precision.

## Overview

The Stock Data Analyser fetches historical financial data from EODHD API, performs strict calculations based on Graham's formulas, detects statistical anomalies, and generates a structured Markdown dossier optimized for downstream LLM analysis.

## Features

- **Multi-Exchange Support**: Analyze stocks from US, UK, Canadian, European, and Asian markets
- **Graham Methodology**: Calculate Graham Number, Net-Net Value, and Earnings Power Value (EPV)
- **Defensive Investor Tests**: Evaluate stocks against Graham's seven criteria
- **Anomaly Detection**: Statistical analysis using Z-Score to identify data quality issues
- **Structured Output**: Generate Markdown dossiers optimized for LLM parsing

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your EODHD API key in `.env`:
```
EODHD_API_KEY=your_api_key_here
```

## Usage

```bash
python stock_data_analyser.py AAPL.US
python stock_data_analyser.py VOD.L
python stock_data_analyser.py RY.TO
```

## Output

The system generates a structured Markdown file (`[TICKER]_DOSSIER.md`) containing:
- Executive Summary with intrinsic values and margin of safety
- Critical Alerts for data quality issues
- Graham Defensive Tests results
- 10-Year Financial History table

## Requirements

- Python 3.9+
- EODHD API key (get one at https://eodhd.com/)

## License

MIT
