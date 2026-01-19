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
python stock_data_analyser.py YU.LSE
python stock_data_analyser.py RY.TO
```

## Supported Stock Exchanges

The Stock Data Analyser supports 50+ stock exchanges worldwide through EODHD API. When EODHD price data is unavailable, the system automatically falls back to Alpha Vantage API with automatic exchange code translation.

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

1. **Primary Source**: EODHD API (real-time and historical data)
2. **Fallback Source**: Alpha Vantage API (when EODHD price unavailable)

Exchange code translation between EODHD and Alpha Vantage formats is handled automatically. When Alpha Vantage is used, a data quality note is added to the dossier.

### Alpha Vantage Configuration (Optional)

To enable price fallback, add your Alpha Vantage API key to `.env`:

```
ALPHAVANTAGE_API_KEY=your_alpha_vantage_key_here
```

**Note**: Alpha Vantage fallback is optional. If the API key is not configured and EODHD price data is unavailable, the system will display a fatal error rather than proceeding with incomplete data (following Graham's principle: "No data is better than wrong data").

## Output

The system generates a structured Markdown file (`[TICKER]_DOSSIER.md`) containing:
- Executive Summary with intrinsic values and margin of safety
- Critical Alerts for data quality issues
- Graham Defensive Tests results
- 10-Year Financial History table

## Requirements

- Python 3.9+
- EODHD API key (get one at [https://eodhd.com?via=patrick](https://eodhd.com?via=patrick))
