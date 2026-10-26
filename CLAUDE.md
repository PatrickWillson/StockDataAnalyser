# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Stock Data Analyser** is a deterministic financial analysis engine implementing Benjamin Graham's value investing methodology. It fetches historical financial data from EODHD API and yfinance, performs strict calculations based on Graham's formulas, and generates Markdown dossiers optimized for LLM analysis.

**Core principle**: Math > Text - Zero hallucinations, pure Python calculations with full transparency.

## Quick Start Commands

```bash
# Install dependencies (Python 3.10+; requirements.txt alone = runtime only)
pip install -r requirements-dev.txt   # runtime + test/dev tools

# Run analysis on a single ticker
python stock_data_analyser.py AAPL.US
python stock_data_analyser.py YU.LSE  # UK stock (London Stock Exchange)
python stock_data_analyser.py RY.TO   # Canadian stock (Toronto)

# Run tests (live API tests excluded by default via pytest.ini; run them with -m live)
pytest tests/ -v

# Coverage (fails below the floor in pyproject.toml) and lint report
pytest --cov
python3 -m ruff check .

# Run only property-based tests
pytest tests/test_*_properties.py -v

# Run with debug output
python stock_data_analyser.py AAPL.US --debug
```

## Architecture Overview

### Layered Architecture
The codebase follows strict separation of concerns:

```
stock_data_analyser.py (CLI entry point)
    ↓
clients/ (Data Acquisition Layer)
    ├── eodhd_client.py - EODHD API integration for fundamentals
    ├── yfinance_client.py - Yahoo Finance for real-time prices
    ├── fx_client.py - Live FX rates
    └── base_client.py - HTTP retry logic & session management
    ↓
core/ (Business Logic Layer)
    ├── graham_math.py - Graham formulas (IMMUTABLE)
    ├── anomaly_detector.py - Z-Score statistical analysis
    ├── ttm_calculator.py - Trailing Twelve Months calculations
    ├── currency_converter.py - FX rate application
    ├── financial_data_processor.py - Data parsing & normalization
    └── data_models.py - Data Transfer Objects (DTOs)
    ↓
output/ (Output Layer)
    ├── dossier_generator.py - Assembles final Markdown
    └── sections/ - Individual dossier sections
        ├── executive_summary.py
        ├── key_metrics.py
        ├── graham_tests.py
        ├── financial_history.py
        ├── ttm_analysis.py
        ├── risk_factors.py
        ├── methodology.py
        └── calculation_details.py
    ↓
data/ (Generated dossiers - gitignored)
claude-output/ (Agent-generated markdown notes - gitignored)
```

### Key Design Principles
- **Never mix API logic with calculation logic** - Each layer has single responsibility
- **Currency unification** - All calculations use a single currency (financials_currency)
- **Graceful degradation** - Missing data triggers warnings, never crashes
- **Transparency over perfection** - Explain all assumptions and conversions
- **Graham methodology is immutable** - Constants in `config/graham_constants.py` are never modified
- **Raw data in, our own calculations out** - Calculations use only raw EODHD statement line items (revenue, net income, equity, liabilities, share counts, dividends paid) and market prices/FX. Every ratio (P/E, P/B, ROE, yields, payout, per-share values) is derived by this code from annual audited data, as Graham would. EODHD pre-computed values (e.g. `PERatio`, `ReturnOnEquityTTM`, `BookValue`, `ForwardAnnualDividendRate`, `NumberDividendsByYear`, market-cap-derived prices) are opaque (forward or trailing? quarterly or annual?) and may appear only as clearly labelled comparisons or display-only market data

## Data Flow & Currency Handling

### Multi-Currency Challenge
Stocks can trade in one currency (e.g., GBX for LSE stocks) while financial statements use another (GBP), and companies may have financials in yet another currency (USD). The system handles this with:

1. **Extract currencies**: Trading currency (from API), financials currency (from balance sheet)
2. **Apply London Fix**: For LSE stocks where P/E > 500, divide price by 100 (GBp→GBP conversion)
3. **Convert all data to unified currency** using live FX rates
4. **Document everything** - Every conversion is logged in warnings for transparency

```python
# Example: YU.LSE (Yu Holdings, LSE)
# Trades in GBX (pence), financials in GBP, calculations in GBP
unified_currency = "GBP"
original_stock_currency = "GBX"
financials_currency = "GBP"
# London Fix applied: 1,650 GBX → 16.50 GBP (price is in pence)
```

## Graham Methodology Constants

All Graham-related constants are **immutable** and located in `config/graham_constants.py`:

```python
GRAHAM_MULTIPLIER = 22.5        # Graham Number formula
COST_OF_CAPITAL = 0.10          # 10% (Earnings Power Value discount rate)
MIN_CURRENT_RATIO = 2.0         # Defensive investor test
MAX_PE_RATIO = 15               # Defensive investor test
MAX_PB_RATIO = 1.5              # Defensive investor test
```

**Do not modify these** - Graham's methodology is specifically calibrated to these values. Create a new calculator class if you need different constants.

## Testing Strategy

### Property-Based Testing (Hypothesis)
All core calculations use property-based tests with 100+ random iterations:

```python
# Example: test_tbvps_calculation_correctness
# Tests that TBVPS = (equity - intangibles - goodwill) / shares_outstanding
# Runs 100+ times with random valid financial data
```

**Test files:**
- `test_*_properties.py` - Property-based tests for all calculations
- `test_*_integration.py` - Live API tests (marked `@pytest.mark.live`)
- `test_end_to_end.py` - Full workflow from fetch to dossier
- `test_dossier_snapshots.py` - Offline end-to-end snapshot tests (syrupy) for refactoring validation; refresh intended output changes with `--snapshot-update`

**When adding new calculations:**
1. Write property-based test first
2. Test edge cases (negative equity, zero shares, missing data)
3. Ensure 100+ test iterations
4. Verify formula correctness

## Common Development Tasks

### Adding a New Graham Calculation

1. **Add formula to `core/graham_math.py`** with docstring showing the calculation
2. **Write property-based test** in `tests/` with 100+ iterations
3. **Handle edge cases** (negative values, missing data, zero denominators)
4. **Add to `compute_all()` method** in GrahamCalculator
5. **Update dossier** in `output/sections/`
6. **Document in METHODOLOGY section** explaining the formula

### Debugging Data Issues

**Enable debug mode:**
```bash
python stock_data_analyser.py AAPL.US --debug
```

This saves the raw API response to `data/[TICKER]_raw_api_response.json` and prints detailed parsing logs.

**Common issues:**

| Issue | Solution |
|-------|----------|
| Wrong CEO name | Check Officers structure in API response - it's a dict with numeric keys ('0', '1'), not a list |
| Currency mismatch | Verify stock_currency vs financials_currency; if P/E > 500 on LSE, London Fix needed |
| Missing dividend data | Check ForwardAnnualDividendRate first, then Cash_Flow yearly data |
| TTM vs Annual mismatch | TTM uses 12-month rolling data; Graham uses annual audited data |

## Key Implementation Details

### Price Fetching Strategy
1. **Primary**: yfinance (no API key required, real-time, no rate limits)
2. **Fallback**: EODHD API (extract from fundamentals data)
3. **Unmapped exchanges**: Attempt without suffix, then fail gracefully

**Exchange code mapping** is in `clients/yfinance_client.py`:
- `US` → '' (no suffix)
- `LSE` → '.L'
- `TO` → '.TO'
- `XETRA` → '.DE'
- etc.

### TTM vs Annual Calculations
- **Annual**: Uses most recent audited year (Graham's preference)
- **TTM**: Uses most recent 12 months of periodic data
- **Frequency detection**: System automatically detects if company reports quarterly (4 periods) or semi-annually (2 periods)

The dossier includes both for comparison.

### Dividend Data Sourcing

Priority order:
1. ForwardAnnualDividendRate from EODHD
2. Historical dividends from SplitsDividends
3. Cash flow statement dividendsPaid
4. Forward estimate used with fallback warning

## Output Format

Dossier format is **fixed** and optimized for LLM parsing:

```markdown
# STOCK ANALYSIS DOSSIER: [TICKER]

[Metadata: CEO, Sector, Industry, Currency, Data Date]

## SECTION 1: EXECUTIVE SUMMARY
[Verdict, intrinsic values, margin of safety, price, dividend]

## SECTION 1.5: TTM ANALYSIS (if available)
[TTM versions of key metrics]

## SECTION 2: KEY METRICS
[Profitability, ownership, risk metrics]

## SECTION 3: CRITICAL ALERTS
[Warnings, anomalies, data quality issues]

## SECTION 4: GRAHAM DEFENSIVE TESTS
[7 tests with pass/fail verdicts]

## SECTION 5: GRAHAM ENTERPRISING TESTS
[6 tests with pass/fail verdicts]

## SECTION 6: 20-YEAR FINANCIALS
[Table with 11 columns: Year, Revenue, Net Income, EPS, Div/Share, BVPS, Total Debt, Shares, Price, P/E, P/B]

## METHODOLOGY & DETAILED CALCULATIONS
[Formulas, assumptions, and step-by-step calculations]

## DATA QUALITY & LIMITATIONS
[Sources, currency conversions, known issues]
```

**Critical**: This structure is fixed for LLM parsing. Don't reorder sections.

## Documentation Organization

- **Root**: `README.md` (user-facing), `requirements.txt`, config files
- **`.kiro/steering/`**: `stock-data-analyser-architecture.md` (detailed architecture guide)
- **`.kiro/documentation/`**: Generated reports, investigation summaries, fix documentation
  - Example: `TTM_IMPLEMENTATION_SUMMARY.md`, `CURRENCY_UNIFICATION_VERIFICATION.md`
- **`claude-output/`**: **All agent-written markdown goes here** — scratch notes, research summaries, investigation logs, planning docs, or any `.md` file an agent produces during a session. This directory is gitignored. Do not write agent-generated markdown to the repo root or any other directory. **Exceptions:** the version-controlled references in `docs/` — `docs/CODEBASE_GUIDE.md` and `docs/GRAHAM_METHODOLOGY.md` (see below).
- **Tests**: Serve as executable documentation of expected behavior

## File Organization Quick Reference

| Path | Purpose |
|------|---------|
| `stock_data_analyser.py` | CLI entry point, main orchestration |
| `clients/eodhd_client.py` | EODHD API client, data fetching |
| `clients/yfinance_client.py` | Yahoo Finance client, price & FX rates |
| `core/graham_math.py` | Graham formula calculations (IMMUTABLE) |
| `core/ttm_calculator.py` | Trailing Twelve Months calculations |
| `core/anomaly_detector.py` | Z-Score analysis for data outliers |
| `core/financial_data_processor.py` | Data parsing, normalization, validation |
| `output/dossier_generator.py` | Orchestrates dossier assembly |
| `output/sections/*.py` | Individual dossier sections |
| `config/graham_constants.py` | Immutable Graham methodology constants |
| `claude-output/` | Agent-generated markdown scratch files (gitignored) |
| `docs/CODEBASE_GUIDE.md` | Living codebase reference (version-controlled) |
| `docs/GRAHAM_METHODOLOGY.md` | What Graham would do: sourced reference for formulas, tests, verdicts, data rules |

## Codebase Guide Maintenance

`docs/CODEBASE_GUIDE.md` is the version-controlled living reference for how the code currently works (pipeline, module responsibilities, data shapes, formulas, currency handling, dossier sections, tests). **Read it first** instead of re-exploring the codebase.

**Always update it in the same change** whenever you:
- add, remove, rename or move a module, class or public function
- add, remove or rename a key in `financial_data`, a `history` row, `metrics` or `ttm_metrics`
- add or change a formula, threshold, investor test or verdict rule
- change currency/FX/London Fix behaviour or the exchange mapping
- add, remove or reorder a dossier section, or change a pipeline step in `main()`
- change test infrastructure (fixtures, snapshots, markers)

Update the "Last full audit" line only after a full re-audit. Keep the guide describing the code as it *is*, not as planned; known bugs and refactor plans belong in `claude-output/CODEBASE_DEEP_DIVE_*.md` (local, gitignored).

## Graham Methodology Reference

`docs/GRAHAM_METHODOLOGY.md` records what Benjamin Graham actually prescribed (from his own Columbia lectures and 1976 interview, plus quoted and summarised passages of *The Intelligent Investor* and *Security Analysis*), with every claim labelled by source quality, and lists where the code currently deviates (§9).

**Before changing any formula, threshold, investor test, verdict rule or data source:**
1. Read the relevant section of `docs/GRAHAM_METHODOLOGY.md` and follow it.
2. Cite the section in the change description (e.g. "per GRAHAM_METHODOLOGY §4.6").
3. If the change fixes or introduces a deviation from Graham, update §9 in the same change.
4. If Graham's position is unclear or a choice is needed, ask the user rather than guessing, and record the decision in the document.

## Error Handling Philosophy

**Graceful degradation**: The system never crashes on bad data.

- **API Errors**: Print error message, exit with code 1 - don't continue with incomplete data
- **Missing Data**: Return "N/A" or 0.0, add warning to dossier, continue processing
- **Calculation Errors**: Return "N/A", add warning, show fallback (e.g., EPV if Graham Number fails)
- **Edge Cases**: Handle explicitly (negative equity, zero shares, young companies)

**Warning system**: All issues are accumulated and displayed in the dossier's CRITICAL ALERTS section.

## Supported Exchanges

The system supports 50+ stock exchanges via EODHD. Use format `SYMBOL.EXCHANGE`:

**Most commonly used:**
- `US` - United States (AAPL.US, MSFT.US)
- `LSE` - London Stock Exchange (YU.LSE, VOD.LSE)
- `TO` - Toronto Stock Exchange (RY.TO, BMO.TO)
- `XETRA` - Germany (SAP.XETRA, SIE.XETRA)
- `PA` - Euronext Paris (BNP.PA, ASML.PA)
- `HK` - Hong Kong (0700.HK, 1398.HK)
- `AU` - Australia (BHP.AU, WBC.AU)

See `README.md` for complete list.

## Critical "Never" Rules

- ❌ **Never modify Graham methodology constants** - These are immutable
- ❌ **Never skip currency conversion** - Always apply FX rates and document conversions
- ❌ **Never assume currencies match** - Explicitly handle each currency pair
- ❌ **Never crash on bad data** - Return "N/A", add warning, continue
- ❌ **Never mix API logic with calculation logic** - Strict layer separation
- ❌ **Never hardcode API keys** - Use `.env` file
- ❌ **Never modify dossier section order** - Structure is optimized for LLM parsing
- ❌ **Never use TTM for Graham tests** - Graham used annual audited data
- ❌ **Never use EODHD pre-computed ratios or estimates in calculations** - Derive them from raw annual statement data; API-derived values only as labelled comparisons/display (see `docs/CODEBASE_GUIDE.md` §5 for known current exceptions)
- ❌ **Never write agent-generated markdown to the repo root** - Use `claude-output/` for all scratch notes, research docs, investigation summaries, and planning files (only exceptions: `docs/CODEBASE_GUIDE.md`, `docs/GRAHAM_METHODOLOGY.md`)

## Performance Notes

- EODHD: 20 requests/second rate limit (free tier)
- yfinance: No rate limit, no API key required
- FX rates are cached per session
- Typical dossier: ~50KB, includes 20 years of history
- Single API call per ticker (yfinance doesn't require API calls for price)

## Environment Setup

```bash
# Copy example env file
cp .env.example .env

# Add your EODHD API key
EODHD_API_KEY=your_api_key_here
```

**Required EODHD Packages:**
- Fundamentals Package (required) - Balance sheet, income statement, cash flow
- EOD Historical Data - All World Package (optional) - Enhanced dividend history

The tool functions with Fundamentals Package alone; the All World Package provides better dividend coverage.

## Getting Help

- **Graham methodology questions**: See `docs/GRAHAM_METHODOLOGY.md`
- **How the code works**: See `docs/CODEBASE_GUIDE.md`
- **Architecture questions**: See `.kiro/steering/stock-data-analyser-architecture.md`
- **Recent changes**: See `.kiro/documentation/` for implementation summaries
- **Code examples**: Test files (`tests/`) serve as executable documentation
- **API integration**: Check `clients/eodhd_client.py` and `clients/yfinance_client.py`
