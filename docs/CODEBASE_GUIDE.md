# StockDataAnalyser — Codebase Guide

> **Purpose:** a living reference for how the code works *today*, so future sessions don't need a full deep dive.
> **Keep it current:** any change that adds, removes, renames or changes the behaviour of a module, public function, data key, formula, dossier section or pipeline step must update this file in the same change (see CLAUDE.md → "Codebase Guide Maintenance").
>
> Last full audit: 2026-10-25 (commit b90c0ce). Known bugs and refactor plan from that audit: `claude-output/CODEBASE_DEEP_DIVE_2026-10-25.md` (local only, gitignored).

---

## 1. What it is

A CLI that takes a ticker (`SYMBOL.EXCHANGE`, e.g. `AAPL.US`, `YU.LSE`, `RY.TO`), pulls fundamentals from EODHD and prices/FX from yfinance, computes Benjamin Graham valuation metrics and investor tests, and writes a fixed-format Markdown dossier to `data/{TICKER}_DOSSIER.md` (dots → underscores) for LLM consumption.

```
python stock_data_analyser.py AAPL.US [--debug]
```

Requires `EODHD_API_KEY` in `.env`. `--debug` sets DEBUG logging and dumps raw EODHD JSON to `data/{ticker}_raw_api_response.json`.

---

## 2. Pipeline (what `main()` does, in order)

| Step | Code | What happens |
|---|---|---|
| 0 | `stock_data_analyser.py` import time | `load_dotenv()`; `API_KEY` read into a module global |
| 1 | `main()` | argparse (`ticker` upper-cased, `--debug`); `configure_logging`; exit 1 if no key |
| 2 | `ClientFactory` | builds `EODHDClient(api_key, FXClient())` and `YFinanceClient` |
| 3 | `EODHDClient.fetch_all_data(ticker, yf_client)` | fetch + parse + currency-normalise + some calculations → `financial_data` dict (§4.1) |
| 4 | CLI lines ~125–260 | historical year-end prices from yfinance, matched to fiscal year-ends, GBX÷100, historical FX applied → writes `history[date]['year_end_price']` + warnings |
| 5 | `GrahamCalculator(financial_data).compute_all()` | → `metrics` dict (§4.3) |
| 6 | `TTMCalculator(...).compute_all(annual_metrics=metrics)` | only if `quarterly_data` present; wrapped in try/except → `ttm_metrics` (§4.4) |
| 7 | `AnomalyDetector(financial_data).scan()` | → `anomalies: List[str]` |
| 8 | `DossierGenerator(ticker, financial_data, metrics, anomalies, ttm_metrics).generate()` | → Markdown string |
| 9 | `save_dossier` | writes `data/{TICKER}_DOSSIER.md` (path relative to CWD) |

Error handling: everything after the key check is in one `try/except Exception` → log + exit 1. Clients call `sys.exit(1)` directly on fatal API errors (401, 429, non-200, no price). Exit codes are only 0/1.

---

## 3. Layout and responsibilities

```
stock_data_analyser.py      CLI + orchestration (+ historical price/FX block)
clients/
  base_client.py            BaseAPIClient: requests.Session, urllib3 Retry(3, backoff 1.0, 5xx, GET)
  eodhd_client.py           EODHDClient: fundamentals + dividend endpoint; fetch_all_data (the big one)
  yfinance_client.py        YFinanceClient: EXCHANGE_MAPPING, get_price, historical prices, FYE matching
  fx_client.py              FXClient: yfinance "{A}{B}=X" rates, current + historical, per-instance cache
  factory.py                ClientFactory: builds clients (validates API key)
core/
  financial_data_processor.py  FinancialDataProcessor: raw JSON → per-year history, dividends, price, validation
  currency_converter.py     CurrencyConverter: convert / convert_batch / apply_london_fix, conversion log
  graham_math.py            GrahamCalculator: all Graham formulas, investor tests, verdict
  ttm_calculator.py         TTMCalculator: frequency detection, period selection, TTM metrics
  anomaly_detector.py       AnomalyDetector: EPS growth Z-scores
  data_models.py            dataclasses (NOT used in production — everything is dicts)
config/
  graham_constants.py       GRAHAM_MULTIPLIER=22.5, COST_OF_CAPITAL=0.10 (immutable)
  investor_thresholds.py    DEFENSIVE / ENTERPRISING frozen dataclasses (test thresholds)
  api_config.py             APIConfig (unused in production)
  output_config.py          OutputConfig (unused in production)
output/
  dossier_generator.py      DossierGenerator: header, section assembly, Critical Alerts
  sections/base.py          DossierSection ABC (generate() -> List[str])
  sections/*.py             one module per dossier section (§6)
tests/                      ~112 test files, pytest + Hypothesis; golden baselines in tests/golden/
data/                       generated dossiers (gitignored)
claude-output/              agent-written markdown (gitignored)
```

**Actual dependency directions** (not the idealised ones): `clients → core` (eodhd_client & factory import core), `core → clients` (currency_converter imports fx_client; processor calls yfinance), `output → core/clients` (methodology imports FinancialDataProcessor; executive_summary builds a CurrencyConverter → live FX call).

---

## 4. Data shapes

### 4.1 `financial_data` (returned by `EODHDClient.fetch_all_data`)
| Key | Meaning |
|---|---|
| `ticker`, `exchange` | `General.Code` (no suffix), `General.Exchange` |
| `currency` | unified calculation currency = financials currency |
| `original_stock_currency`, `financials_currency` | trading ccy (`General.CurrencyCode`), balance-sheet `currency_symbol` |
| `price`, `price_source` | current price **in financials ccy**; `'yfinance'` / `'EODHD'` / `'Missing'` |
| `fx_rate_used`, `historical_fx_rates` | price ccy → financials ccy rate; `{fye_date: rate or None}` |
| `history` | `{ 'YYYY-MM-DD': row }` — see §4.2 |
| `warnings` | `List[str]`, appended to by client, CLI; shown in Critical Alerts |
| `ceo_name`, `sector`, `industry`, `employees` | company info |
| `pe_ratio`, `book_value_per_share`, `price_to_book` | calculated in the client |
| `roe`, `roa`, `profit_margin` | from `calculate_profitability_metrics` (latest financial year) |
| `insider_ownership`, `institutional_ownership`, `beta`, `week_52_high`, `week_52_low`, `average_volume` | Highlights/SharesStats/Technicals |
| `forward_dividend_rate`, `dividend_source`, `dividend_sources`, `is_dividend_amounts` | dividend info (`is_dividend_amounts=False` means values are payment counts) |
| `ttm_dividend`, `ttm_dividend_payments` | last-365-day dividend sum |
| `quarterly_data` | `{'balance_sheet': {date: row}, 'income_statement': {date: row}}` for TTM |
| unused by consumers | `dividend_currency`, `price_currency_before_fx`, `ttm_dividend_currency`, `dividend_per_share`, `dividend_yield`, `enterprise_value`, `api_last_update` |

### 4.2 `history` row (built by `FinancialDataProcessor.merge_financial_data`)
`revenue, net_income, eps, dividend, total_equity, intangible_assets, goodwill, current_assets, current_liabilities, total_liabilities, long_term_debt, total_assets, total_debt, shares_outstanding, wcps, payout_ratio, year_end_price`

- Missing numbers are **0.0** (via `sanitize_value`), not None. `wcps` may be `"N/A"`; `payout_ratio` is a formatted string (`"12.3%"`, `"0.0%"`, `"N/A"`); `year_end_price` may be None.
- Keys are fiscal year-end dates. **Dividend-only years** (dividend data exists but no statements, often the current/future year) are synthesised with the latest FYE month-day and all statement fields 0.0.
- Shares priority: `outstandingShares.annual` → BS `commonStockSharesOutstanding` / `weightedAverageShsOut` / `...Dil` → `SharesStats.SharesOutstanding`.
- EPS: API `eps`/`basicEPS`/`epsBasic`; if 0, fallback `net_income / shares`. Net income prefers `netIncomeFromContinuingOps`.
- Total debt: `longTermDebt + shortTermDebt` if either > 0, else `shortLongTermDebtTotal`.

### 4.3 `metrics` (returned by `GrahamCalculator.compute_all`)
`graham_number, normalized_graham_number, epv, epv_details, net_net_value, nca_details, quick_ratio, three_year_avg_pe, combined_pe_pb_test, margin_of_safety, margin_of_safety_details, defensive_tests, enterprising_tests, verdict, warnings`

Values are floats or `"N/A"`-style strings (also `"N/A - reason"`, `"N/A (Too Young)"`). `epv` is the **total** EPV (not per share); per share is in `epv_details['epv_per_share']`.

### 4.4 `ttm_metrics` (returned by `TTMCalculator.compute_all`)
`ttm_revenue, ttm_net_income, ttm_eps, ttm_tbvps, ttm_graham_number, ttm_net_net, ttm_margin_of_safety, ttm_pe_ratio, ttm_pb_ratio, total_equity, intangible_assets, goodwill, current_assets, total_liabilities, shares_outstanding, reporting_frequency ('quarterly'|'semi-annual'|'irregular'), periods_used, date_range, warnings`
The early-exit (insufficient/irregular data) dict omits some of these.

---

## 5. Calculations

### 5.1 Graham (`core/graham_math.py`, `GrahamCalculator`)
"Latest financial year" = first year (newest first) with `revenue>0 or net_income≠0 or total_equity>0` (variants exist; several methods inline their own predicate).

| Metric | Formula / rule |
|---|---|
| TBVPS | (Equity − \|Intangibles\| − \|Goodwill\|) / Shares; negative → "N/A" + warning |
| Graham Number | √(22.5 × EPS_latest × TBVPS); EPS ≤ 0 → "N/A" |
| Normalized Graham Number | √(22.5 × mean(EPS of 3 most recent history keys) × TBVPS) — uses `FinancialDataProcessor.extract_3year_eps_data` |
| Net-Net (NCAV/share) | (Current Assets − Total Liabilities) / Shares |
| NCA details | NCA = CA − Total Liabilities; debt coverage = LTD / NCA |
| Quick ratio | (CA − Inventory) / CL — inventory is never parsed, so sector fallback applies |
| 3-yr avg P/E | price / mean(EPS of 3 latest complete years) |
| Combined P/E×P/B | round(P/E) × round(P/B, BVPS-based) ≤ 22.5 |
| EPV | mean(net income, up to 10 complete years, min 7) / COST_OF_CAPITAL; per share = EPV / latest shares. `compute_epv()` turns N/A into 0.0 |
| Margin of Safety | IV = min(Normalized GN, EPV/share); MoS = (IV − Price)/IV × 100 |
| Verdict | GN "N/A" → "Rely on EPV - Negative Equity"; defensive fail & enterprising pass → "ENTERPRISING BUY"; MoS ≥ 20 → "STRONG BUY (Undervalued)"; > 0 → "UNDERVALUED"; else "OVERVALUED" |

**Defensive tests** (`DEFENSIVE` thresholds): current ratio ≥ 2.0; LTD < CA − CL; earnings stability (positive NI in last 10 years); dividend record (dividend every year up to 20); earnings growth (latest NI / NI 10 financial years ago ≥ 1.33, else "N/A (Too Young)"); P/E < 15; P/B < 1.5.
**Enterprising tests** (`ENTERPRISING`): current ratio ≥ 1.5; LTD < (CA − CL) × 1.10; earnings stability (5 of last 5); current dividend > 0; earnings growth; price: P/E < 10 OR price < TBVPS × 1.20.

### 5.2 TTM (`core/ttm_calculator.py`, `TTMCalculator`)
1. Constructor applies its own London Fix (P/E > 500 using latest single-period EPS) and optional currency conversion (not triggered from the CLI).
2. `detect_reporting_frequency`: mean interval of last ≤5 income dates — 75–105 d quarterly, 150–210 d semi-annual, else irregular (TTM aborted).
3. `_select_periods_for_ttm`: 4 quarters or 2 halves; gap check; span check (quarterly 225–315 d, semi 150–210 d).
4. `calculate_ttm_metrics`: sum revenue/NI over periods; balance items from latest balance date; TTM EPS = ΣNI / latest shares.
5. TTM TBVPS / Graham Number / Net-Net / MoS (MoS uses TTM Graham Number only) / P/E / P/B.
6. `DossierGenerator` shows the TTM section only if `ttm_graham_number != "N/A"`.

### 5.3 Anomalies (`core/anomaly_detector.py`)
YoY EPS growth % (skip prev EPS ≤ 0), population SD, flag |z| > 2.0. Needs ≥ 3 growth rates (in practice can't flag with < 6).

---

## 6. Currency handling

1. Trading ccy = `General.CurrencyCode`; financials ccy = balance-sheet `currency_symbol`; unified = financials.
2. Dividends: `convert_batch` to financials ccy at **current** rate.
3. Price: yfinance → EODHD fallbacks (`get_current_price`). Then:
   - LSE & P/E > 500 → ÷100, label GBP (London Fix, also adjusts 52-week range)
   - else GBX (not from market cap) → ÷100
   - then convert to financials ccy; `fx_rate_used` recorded; historical FX fetched for fiscal year-ends.
4. Highlights dividend/BVPS, forward dividend, TTM dividend: GBX relabelled GBP, then converted.
5. CLI converts historical year-end prices (GBX÷100 for LSE, then historical FX, fallback to current).
6. Executive Summary converts the 52-week range itself (new FX call).
7. All conversions are logged into `warnings` via `CurrencyConverter.get_consolidated_warning()` (except the plain GBX÷100 path).

GBX logic lives in several places: `CurrencyConverter.convert` (÷100), `FXClient.get_rate` (GBX treated as GBP, no factor), `convert_batch` (no special case), `eodhd_client`, CLI, `TTMCalculator._apply_london_fix`, `executive_summary`. Change one → check all.

---

## 7. Price & exchange mapping

- `YFinanceClient.EXCHANGE_MAPPING` maps EODHD exchange codes → Yahoo suffix (US/NYSE/NASDAQ → '', LSE → .L, TO → .TO, XETRA → .DE, AU → .AX, HK → .HK, …; 53 entries). Unmapped → bare symbol (warning).
- `_parse_ticker` requires exactly one dot.
- Historical prices: `history(start, end, auto_adjust=True)`; matched to fiscal year-ends with a 7-day backward window (`match_fiscal_year_end_prices`; FX uses an identical `match_fiscal_year_end_rates`).

---

## 8. Dossier

`DossierGenerator.generate()` renders in this **actual** order:

| # | Heading | Source |
|---|---|---|
| – | Header (`# STOCK ANALYSIS DOSSIER`, DATE, CEO/sector/currency) | `_generate_header` |
| 1 | EXECUTIVE SUMMARY | `executive_summary.py` `ExecutiveSummarySection(financial_data, metrics)` |
| 1.5 | TTM ANALYSIS (conditional) | `ttm_analysis.py` `TTMAnalysisSection(ttm_metrics, metrics, financial_data)` |
| 2 | KEY METRICS | `key_metrics.py` `KeyMetricsSection(financial_data)` (metrics not passed) |
| – | RISK FACTORS | `risk_factors.py` `RiskFactorsSection` (only `_generate_second_risk_section` is live) |
| – | METHODOLOGY NOTES | `methodology.py` `MethodologySection` |
| – | CALCULATION DETAILS | `calculation_details.py` `CalculationDetailsSection` |
| 4 / 5 | GRAHAM DEFENSIVE / ENTERPRISING TESTS | `graham_tests.py` `GrahamTestsSection(metrics)` |
| 6 | 20-YEAR FINANCIALS | `financial_history.py` `FinancialHistorySection(financial_data)` |
| 3 | CRITICAL ALERTS | `_generate_critical_alerts` (warnings + anomalies) — rendered **last** |

Each section's `generate()` returns `List[str]`; the generator joins with `\n`. Only some sections subclass `DossierSection`. `format_price_display` is duplicated in several section modules and the CLI. Several sections do their own arithmetic (BVPS, NCA, ratios, yields, risk bands) rather than reading core results.

---

## 9. Tests

- Run: `pytest tests/ -v` (live API tests marked `@pytest.mark.live`, deselected by `pytest.ini`).
- Mostly property-based (Hypothesis, 100+ examples) per calculation; section tests build inline dicts; `tests/fixtures_graham_metrics.py` builds processed `financial_data`; `tests/fixtures.py` holds raw API payloads (barely used).
- Golden baselines `tests/golden/{AAPL_US,YU_LSE,RY_TO}_baseline.md` + `test_golden_baseline.py`: the verify test is **live** and not deterministic (date header, live data) — not an offline regression guard.
- Status at last audit: 1029 pass / 6 fail (stale assertions + one test rounding bug) / 20 skip; ~78% branch coverage; weakest: CLI, yfinance_client, risk_factors.

---

## 10. Where to change things

| To… | Edit |
|---|---|
| add a Graham metric | `core/graham_math.py` (+ `compute_all`), property test, section in `output/sections/`, methodology text, **this guide §4.3/§5.1** |
| add an EODHD field | `financial_data_processor.py` parser + `merge_financial_data`; `fetch_all_data` return dict; **§4.1/§4.2** |
| add an exchange | `YFinanceClient.EXCHANGE_MAPPING`; **§7** |
| change a threshold | `config/investor_thresholds.py` (Graham constants are immutable) — also hardcoded strings in `graham_tests.py`/`methodology.py` |
| add/reorder a section | `output/dossier_generator.py` + `output/sections/`; **§8** (order is fixed for LLM parsing) |
| change currency logic | every GBX site listed in **§6** |
