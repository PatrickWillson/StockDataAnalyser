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

**Note**: yfinance (Yahoo Finance) is used for real-time price data and does not require an API key. Only the EODHD API key is required for fundamental financial data.

### EODHD API Package Requirements

To use this tool, you need to purchase the following EODHD API packages:

- **Fundamentals Package** (Required) - Provides balance sheet, income statement, cash flow, and company fundamentals data
- **EOD Historical Data - All World Package** (Optional) - Provides more accurate and complete dividend history across all exchanges

Without the Fundamentals Package, the tool will not be able to fetch the necessary financial data. The All World Package is recommended for investors who need comprehensive dividend data, but the tool can function with the Fundamentals Package alone (using forward dividend rates as fallback).

## Usage

```bash
python stock_data_analyser.py AAPL.US
python stock_data_analyser.py YU.LSE
python stock_data_analyser.py RY.TO
```

## Supported Stock Exchanges

The Stock Data Analyser supports 50+ stock exchanges worldwide through EODHD API. When EODHD price data is unavailable, the system automatically falls back to yfinance (Yahoo Finance) with automatic exchange code translation.

### Ticker Format

Use the format `SYMBOL.EXCHANGE` where:
- `SYMBOL` is the stock ticker (e.g., "AAPL", "YU", "RY")
- `EXCHANGE` is the EODHD exchange code (see below)

**Examples:**
- `AAPL.US` - Apple Inc. on US exchanges
- `YU.LSE` - Yu Group on London Stock Exchange
- `RY.TO` - Royal Bank of Canada on Toronto Stock Exchange
- `VOD.LSE` - Vodafone on London Stock Exchange

### Exchange Codes by Region

#### North America
- **US** - United States (NYSE, NASDAQ, AMEX)
- **TO** - Toronto Stock Exchange (Canada)
- **V** - TSX Venture Exchange (Canada)
- **MX** - Mexican Stock Exchange

#### Europe
- **LSE** - London Stock Exchange (UK) ⭐ Most commonly used
- **IL** - London International Exchange
- **XETRA** - XETRA (Germany) ⭐ Most commonly used
- **F** - Frankfurt Stock Exchange
- **BE** - Berlin Stock Exchange
- **PA** - Euronext Paris (France) ⭐ Most commonly used
- **AS** - Euronext Amsterdam (Netherlands)
- **BR** - Euronext Brussels (Belgium)
- **LS** - Euronext Lisbon (Portugal)
- **MC** - Madrid Stock Exchange (Spain)
- **MI** - Milan Stock Exchange (Italy)
- **SW** - SIX Swiss Exchange (Switzerland)
- **VI** - Vienna Stock Exchange (Austria)
- **IR** - Irish Stock Exchange
- **ST** - Stockholm Stock Exchange (Sweden)
- **OL** - Oslo Stock Exchange (Norway)
- **CO** - Copenhagen Stock Exchange (Denmark)
- **HE** - Helsinki Stock Exchange (Finland)
- **IC** - Iceland Stock Exchange
- **WAR** - Warsaw Stock Exchange (Poland)
- **BUD** - Budapest Stock Exchange (Hungary)
- **PR** - Prague Stock Exchange (Czech Republic)
- **MCX** - Moscow Exchange (Russia)
- **IS** - Istanbul Stock Exchange (Turkey)
- **AT** - Athens Stock Exchange (Greece)

#### Asia Pacific
- **AU** - Australian Securities Exchange ⭐ Most commonly used
- **TSE** - Tokyo Stock Exchange (Japan)
- **HK** - Hong Kong Stock Exchange ⭐ Most commonly used
- **SHG** - Shanghai Stock Exchange (China)
- **SHE** - Shenzhen Stock Exchange (China)
- **NSE** - National Stock Exchange of India
- **BSE** - Bombay Stock Exchange (India)
- **KO** - Korea Stock Exchange
- **KQ** - KOSDAQ (Korea)
- **TW** - Taiwan Stock Exchange
- **SG** - Singapore Exchange
- **BK** - Stock Exchange of Thailand (Bangkok)
- **JK** - Indonesia Stock Exchange (Jakarta)
- **KLSE** - Bursa Malaysia (Kuala Lumpur)

#### Other Regions
- **SA** - B3 (Brazil)
- **JSE** - Johannesburg Stock Exchange (South Africa)
- **SR** - Saudi Stock Exchange (Tadawul)
- **TA** - Tel Aviv Stock Exchange (Israel)

⭐ **Most Commonly Used Exchanges**: US, LSE, TO, XETRA, PA, HK, AU

### Price Data Fallback

The system uses a two-tier approach for price data:

1. **Primary Source**: yfinance (Yahoo Finance - real-time prices, no API key required)
2. **Fallback Source**: EODHD API (extracted from fundamentals data)

Exchange code translation between EODHD and yfinance formats is handled automatically. yfinance provides current market prices without requiring API keys or rate limits.

## Output

The system generates a structured Markdown file (`[TICKER]_DOSSIER.md`) containing:
- Executive Summary with intrinsic values and margin of safety
- Critical Alerts for data quality issues
- Graham Defensive Tests results
- 10-Year Financial History table

## Requirements

- Python 3.9+
- EODHD API key with Fundamentals Package (get one at [https://eodhd.com?via=patrick](https://eodhd.com?via=patrick))
  - **Required**: Fundamentals Package
  - **Optional**: EOD Historical Data - All World Package (for enhanced dividend history)
