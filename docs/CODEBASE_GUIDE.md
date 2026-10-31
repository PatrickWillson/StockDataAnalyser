# StockDataAnalyser — Codebase Guide

> **Purpose:** a living reference for how the code works *today*, so future sessions don't need a full deep dive.
> **Keep it current:** any change that adds, removes, renames or changes the behaviour of a module, public function, data key, formula, dossier section or pipeline step must update this file in the same change (see CLAUDE.md → "Codebase Guide Maintenance").
>
> What Graham would do (the methodology the code should follow, and where it currently deviates): `docs/GRAHAM_METHODOLOGY.md`.
>
> Last full audit: 2026-10-25 (commit b90c0ce). Known bugs and refactor plan from that audit: `claude-output/CODEBASE_DEEP_DIVE_2026-10-25.md` (local only, gitignored).

---

## 1. What it is

A CLI that takes a ticker (`SYMBOL.EXCHANGE`, e.g. `AAPL.US`, `YU.LSE`, `RY.TO`), pulls fundamentals from EODHD and prices/FX from yfinance, computes Benjamin Graham valuation metrics and investor tests, and writes a fixed-format Markdown dossier to `data/{TICKER}_DOSSIER.md` (dots → underscores) for LLM consumption.

```
python stock_data_analyser.py AAPL.US [--debug]
```

Requires `EODHD_API_KEY` in `.env`. `--debug` sets DEBUG logging and dumps raw EODHD JSON to `data/{ticker}_raw_api_response.json`.

**Secrets in logs:** the EODHD key travels as the `api_token` query parameter. `configure_logging` keeps urllib3 at WARNING (its DEBUG output prints full request URLs) and attaches `logging_utils.SecretRedactingFilter` to every root handler, which replaces `api_token=…` values and the literal key with `***` in messages and tracebacks. Guarded by `tests/test_log_redaction.py`. Handlers added to the root logger *after* `configure_logging` do not get the filter.

---

## 2. Pipeline (what `main()` does, in order)

| Step | Code | What happens |
|---|---|---|
| 0 | `stock_data_analyser.py` import time | `load_dotenv()`; `API_KEY` read into a module global |
| 1 | `main()` | argparse (`ticker` upper-cased, `--debug`); `configure_logging(debug, secrets=[API_KEY])` (urllib3 logger pinned to WARNING; `SecretRedactingFilter` on root handlers); exit 1 if no key |
| 2 | `ClientFactory` | builds `EODHDClient(api_key, FXClient())` and `YFinanceClient` |
| 3 | `EODHDClient.fetch_all_data(ticker, yf_client)` | client fetches fundamentals + dividend endpoint, then `core.financial_data_assembler.FinancialDataAssembler.assemble(data, dividend_api_data, ticker, yf_client)` parses, currency-normalises, calculates and validates → `financial_data` dict (§4.1); data-quality warnings include `validate_data_quality` and `check_data_staleness` (latest annual report > 9 months old; dividend-only years ignored) |
| 4 | `main()` + `core.historical_prices.apply_year_end_prices` | CLI fetches daily yfinance prices and matches them to fiscal year-ends; `apply_year_end_prices` divides minor-unit prices by 100 (per `price_quote_currency`, e.g. GBp), applies historical FX (current-rate fallback), writes `history[date]['year_end_price']` and adds warnings |
| 5 | `GrahamCalculator(financial_data).compute_all()` | → `metrics` dict (§4.3) |
| 6 | `TTMCalculator(...).compute_all(annual_metrics=metrics)` | only if `quarterly_data` present; wrapped in try/except → `ttm_metrics` (§4.4) |
| 7 | `AnomalyDetector(financial_data).scan()` | → `anomalies: List[str]` |
| 8 | `DossierGenerator(ticker, financial_data, metrics, anomalies, ttm_metrics).generate()` | → Markdown string |
| 9 | `save_dossier` | writes `data/{TICKER}_DOSSIER.md` (path relative to CWD) |

Error handling: clients and the assembler raise typed errors from `core/errors.py` (`DataSourceError` → `EODHDAuthError` (401), `EODHDRateLimitError` (429), `EODHDRequestError` (network / other status / bad JSON), `PriceUnavailableError` (no price from yfinance or EODHD)); no client calls `sys.exit`. `main()` catches `PriceUnavailableError` (fatal banner + troubleshooting), other `DataSourceError` (message) and any other `Exception` (critical), each → exit 1. Exit codes are only 0/1.

---

## 3. Layout and responsibilities

```
stock_data_analyser.py      CLI + orchestration (+ historical price/FX block)
logging_utils.py            redact(), SecretRedactingFilter, install_secret_redaction — keeps API keys out of logs
clients/
  base_client.py            BaseAPIClient: requests.Session, urllib3 Retry(3, backoff 1.0, 5xx, GET)
  eodhd_client.py           EODHDClient: fetches fundamentals + dividend endpoint (and the --debug raw dump); delegates assembly to core
  yfinance_client.py        YFinanceClient: EXCHANGE_MAPPING, get_quote (price + Yahoo quote currency), historical prices, FYE matching
  fx_client.py              FXClient: yfinance "{A}{B}=X" rates, current + historical, per-instance cache
  factory.py                ClientFactory: builds clients (validates API key)
core/
  price_quote.py            PriceQuote(price, currency); major_currency / same_currency (minor units GBp/GBX→GBP, ZAc→ZAR, ILA→ILS; case-sensitive)
  statement_parsing.py      typed BalanceSheetRow / IncomeStatementRow (Optional fields; None = not reported) for yearly and quarterly statements; holds the raw EODHD key names; as_history_fields() → history-row dicts
  historical_prices.py      apply_year_end_prices(): year-end price currency handling + merge into history
  financial_data_assembler.py  FinancialDataAssembler: raw fundamentals + dividends → financial_data (price, London Fix, FX, ratios, cross-validation, data-quality warnings)
  errors.py                 DataSourceError hierarchy (EODHDAuthError, EODHDRateLimitError, EODHDRequestError, PriceUnavailableError) — raised instead of exiting
  financial_data_processor.py  FinancialDataProcessor: raw JSON → per-year history, dividends, price, validation
  currency_converter.py     CurrencyConverter: convert / convert_batch / try_convert_batch (None = no rate) / normalise_quote_unit (minor-unit quote → major ccy, the London Fix), conversion log
  graham_math.py            GrahamCalculator: all Graham formulas, investor tests, verdict
  history.py                predicates for "this year has real data" (skip dividend-only years) + latest_year()
  ttm_calculator.py         TTMCalculator: frequency detection, period selection, TTM metrics
  anomaly_detector.py       AnomalyDetector: EPS growth Z-scores
  data_models.py            dataclasses (NOT used in production — everything is dicts)
config/
  graham_constants.py       GRAHAM_MULTIPLIER=22.5, COST_OF_CAPITAL=0.10 (immutable)
  investor_thresholds.py    DEFENSIVE / ENTERPRISING frozen dataclasses (test thresholds and windows: earnings stability, dividend record, earnings growth)
  data_quality_config.py    data-check settings: cross-validation % limits, staleness (7 days API, 9 months report), FYE lookback 7 days, min history 10 years, missing-years limit 3, anomaly Z-score 2.0
  risk_thresholds.py        Risk Factors display bands (beta, liquidity, debt/assets, margin volatility, ROE, payout, dividend coverage, MoS, history window); labels only — no calculation, test or verdict uses them
  ttm_config.py             TTM settings: frequency bands (75–105 / 150–210 days), gap tolerances, span checks, period-date limits, TTM-vs-annual warning limits (20% EPS, 50% revenue/NI)
  valuation_config.py       project valuation settings: NORMALIZED_EPS_YEARS (3), EPV_MIN/MAX_YEARS (7/10), DEEP_VALUE_MIN_DISCOUNT_PCT (2.0), STRONG_BUY_MIN_MOS_PCT (20)
  api_config.py             APIConfig (unused in production)
  output_config.py          OutputConfig (unused in production)
output/
  dossier_generator.py      DossierGenerator: header, section assembly, Critical Alerts
  formatting.py             shared formatters (format_price_display) — sections import from here
  sections/base.py          DossierSection ABC (generate() -> List[str])
  sections/*.py             one module per dossier section (§6)
tests/                      ~115 test files, pytest + Hypothesis; syrupy snapshots in tests/__snapshots__/
data/                       generated dossiers (gitignored)
claude-output/              agent-written markdown (gitignored)
```

**Enforced layer rules** (import-linter, `pyproject.toml`, checked by `tests/test_architecture.py` on every test run): layers `output | clients` > `core` > `config` (a lower layer may not import a higher one; `output` and `clients` may not import each other); `core` must not import `clients`; `output` must not import `clients`, even indirectly. There are no exceptions (`ignore_imports`) — never add one. `CurrencyConverter` takes its FX source by injection (`RateSource` protocol); `ClientFactory` supplies the real `FXClient`. The CLI (`stock_data_analyser.py`) and `logging_utils.py` are top-level modules and are not analysed.

**Actual dependency directions:** `clients → core` (eodhd_client & factory use core's processor/converter — allowed by the layers; assembly logic lives in `core/financial_data_assembler.py`); `core` imports nothing from `clients` and makes no network calls of its own: the price is fetched by the client and passed in, and FX rates come through the injected `RateSource` port (`get_rate`, `fetch_historical_rates`); `output → core` (methodology imports FinancialDataProcessor).

---

## 4. Data shapes

### 4.1 `financial_data` (returned by `FinancialDataAssembler.assemble`, via `EODHDClient.fetch_all_data`)
| Key | Meaning |
|---|---|
| `ticker`, `exchange` | `General.Code` (no suffix), `General.Exchange` |
| `currency` | unified calculation currency = financials currency |
| `original_stock_currency`, `financials_currency` | trading ccy (`General.CurrencyCode`), balance-sheet `currency_symbol` |
| `price`, `price_source` | current price **in financials ccy**; always `'yfinance'` (no price → `PriceUnavailableError`, no dossier) |
| `price_quote_currency`, `price_currency_before_fx` | quote currency as yfinance reported it (e.g. `GBp`); its major currency (`GBP`), the price's currency before FX |
| `fx_rate_used`, `historical_fx_rates` | price ccy → financials ccy rate; `{fye_date: rate or None}` |
| `history` | `{ 'YYYY-MM-DD': row }` — see §4.2 |
| `warnings` | `List[str]`, appended to by client, CLI; shown in Critical Alerts |
| `ceo_name`, `sector`, `industry`, `employees` | company info |
| `pe_ratio`, `book_value_per_share`, `price_to_book` | calculated in the client |
| `roe`, `roa`, `profit_margin` | from `calculate_profitability_metrics` (latest financial year) |
| `insider_ownership`, `institutional_ownership`, `beta`, `week_52_high`, `week_52_low`, `average_volume` | Highlights/SharesStats/Technicals (numeric fields sanitised: null/junk → 0.0) |
| `forward_dividend_rate`, `dividend_source`, `dividend_sources`, `is_dividend_amounts` | dividend info (`is_dividend_amounts=False` means values are payment counts) |
| `ttm_dividend`, `ttm_dividend_payments` | last-365-day dividend sum |
| `quarterly_data` | `{'balance_sheet': {date: row}, 'income_statement': {date: row}}` for TTM |
| unused by consumers | `dividend_currency`, `ttm_dividend_currency`, `dividend_per_share`, `dividend_yield`, `enterprise_value`, `api_last_update` |

### 4.2 `history` row (built by `FinancialDataProcessor.merge_financial_data`; statement fields come from `core.statement_parsing` rows via `as_history_fields()`)
`revenue, net_income, eps, dividend, total_equity, intangible_assets, goodwill, current_assets, current_liabilities, total_liabilities, long_term_debt, total_assets, total_debt, shares_outstanding, wcps, payout_ratio, year_end_price`

- Missing numbers are **0.0** (via `sanitize_value`, which also maps JSON null, `"NA"` and non-numeric junk to 0.0), not None. `wcps` may be `"N/A"`; `payout_ratio` is a formatted string (`"12.3%"`, `"0.0%"`, `"N/A"`); `year_end_price` may be None.
- Keys are fiscal year-end dates. **Dividend-only years** (dividend data exists but no statements, often the current/future year) are synthesised with the latest FYE month-day and all statement fields 0.0.
- Shares priority (malformed `outstandingShares.annual` rows are skipped individually): `outstandingShares.annual` → BS `commonStockSharesOutstanding` / `weightedAverageShsOut` / `...Dil` → `SharesStats.SharesOutstanding`.
- EPS: API `eps`/`basicEPS`/`epsBasic`; if 0, fallback `net_income / shares`. Net income prefers `netIncomeFromContinuingOps`.
- Total debt: reported `shortLongTermDebtTotal` (short + long-term debt incl. leases) when > 0, else `longTermDebt + shortTermDebt` (GRAHAM_METHODOLOGY §9). Display only (history table, Risk Factors "short-term debt and leases" = total − long-term); Graham's debt tests use `long_term_debt`.

### 4.3 `metrics` (returned by `GrahamCalculator.compute_all`)
`graham_number, normalized_graham_number, epv, epv_details, net_net_value, nca_details, current_ratio, quick_ratio, three_year_avg_pe, combined_pe_pb_test, margin_of_safety, margin_of_safety_details, defensive_tests, enterprising_tests, verdict, warnings`

Values are floats or `"N/A"`-style strings (also `"N/A - reason"`, `"N/A (Too Young)"`). `epv` is the **total** EPV (not per share); per share is in `epv_details['epv_per_share']`.

### 4.4 `ttm_metrics` (returned by `TTMCalculator.compute_all`)
`ttm_revenue, ttm_net_income, ttm_eps, ttm_tbvps, ttm_graham_number, ttm_net_net, ttm_margin_of_safety, ttm_pe_ratio, ttm_pb_ratio, total_equity, intangible_assets, goodwill, current_assets, total_liabilities, shares_outstanding, reporting_frequency ('quarterly'|'semi-annual'|'irregular'), periods_used, date_range, warnings`
The early-exit (insufficient/irregular data) dict omits some of these.

---

## 5. Calculations

### 5.0 Data-source principle
Calculations use only **raw** EODHD statement line items (revenue, net income, equity, liabilities, share counts, dividends paid) plus market prices and FX rates. Every ratio and per-share value is derived here from annual audited data. EODHD pre-computed values are opaque (forward vs trailing, quarterly vs annual) and may only be shown as clearly labelled comparisons or display-only market data.

Where EODHD pre-computed values are used today:

| EODHD value | Current use | Complies? |
|---|---|---|
| `PERatio`, `ReturnOnEquityTTM`, `ReturnOnAssetsTTM`, `ProfitMargin` | Read, then overwritten by our own calculations; API values only in cross-validation warnings | Yes |
| `Highlights.BookValue` | Shown only as "API BVPS" comparison in Calculation Details | Yes (labelled comparison) |
| `Beta`, `52WeekHigh/Low`, `PercentInsiders/Institutions` | Display; Beta also drives a Risk Factors band | Display-only market data |
| `DividendShare`, `DividendYield`, `EnterpriseValue` | Read, never used | Unused |
| `ForwardAnnualDividendRate` (estimate) | **Inserted into `history` as the latest year's dividend when the cash-flow figure is missing**; used for Risk Factors payout/coverage and Executive Summary "Forward Rate" yield | **No** — known exception |
| `NumberDividendsByYear` (payment counts) | **Used as dividend amounts** when nothing else exists | **No** — known exception |
| `MarketCapitalization`, `SharesOutstanding`, `SharePrice`, `LastPrice` | Never used for the price (removed by F21: yfinance is the only price source) | Yes |

`SharesStats.SharesOutstanding` (a raw current share count) is the last-resort share count for years without an annual figure.

### 5.1 Graham (`core/graham_math.py`, `GrahamCalculator`)
"Latest financial year" = first year (newest first) passing a `core.history` predicate. Four variants exist, each defined once there and kept distinct on purpose (unifying them would change output): `has_statement_data` (revenue>0 or net_income≠0 or equity>0 — used by most code), `has_statement_or_current_assets` (`_get_latest_financial_year`), `has_balance_sheet_data` (current ratio), `has_income_data` (20-year table). `is_dividend_only_year` (statement fields all present and zero, EPS 0) is the stricter rule used by `extract_3year_eps_data` (F2) and `check_data_staleness` (F11).

| Metric | Formula / rule |
|---|---|
| TBVPS | (Equity − \|Intangibles\| − \|Goodwill\|) / Shares; negative → "N/A" + warning |
| Graham Number | √(22.5 × EPS_latest × TBVPS); EPS ≤ 0 → "N/A" |
| Normalized Graham Number | √(22.5 × mean(EPS of the 3 most recent years with statement data) × TBVPS) — uses `FinancialDataProcessor.extract_3year_eps_data`, which skips dividend-only years (revenue, net income, equity all 0.0 and EPS 0); same years as the 3-yr avg P/E |
| Net-Net (NCAV/share) | (Current Assets − Total Liabilities) / Shares |
| NCA details | NCA = CA − Total Liabilities; debt coverage = LTD / NCA |
| Current ratio | CA / CL for the latest year with balance-sheet data; `{'ratio', 'fiscal_year_end'}`; shares `_latest_current_ratio` with the current-ratio investor tests, so display and PASS/FAIL agree |
| Quick ratio | (CA − Inventory) / CL — inventory is never parsed, so sector fallback applies |
| 3-yr avg P/E | price / mean(EPS of 3 latest complete years) |
| Combined P/E×P/B | round(P/E) × round(P/B, BVPS-based) ≤ 22.5 |
| EPV | mean(net income, up to 10 complete years, min 7) / COST_OF_CAPITAL; per share = EPV / latest shares. `compute_epv()` turns N/A into 0.0 |
| Margin of Safety | IV = min(Normalized GN, EPV/share); MoS = (IV − Price)/IV × 100 |
| Verdict | GN "N/A" → "Rely on EPV - Negative Equity"; defensive fail & enterprising pass → "ENTERPRISING BUY"; MoS ≥ 20 → "STRONG BUY (Undervalued)"; > 0 → "UNDERVALUED"; else "OVERVALUED" |

**Defensive tests** (`DEFENSIVE` thresholds): current ratio ≥ 2.0; LTD < CA − CL; earnings stability (positive NI in last 10 years); dividend record (dividend every year up to 20); earnings growth (latest NI / NI 10 financial years ago ≥ 1.33, else "N/A (Too Young)"); P/E < 15; P/B < 1.5.
**Enterprising tests** (`ENTERPRISING`): current ratio ≥ 1.5; LTD < (CA − CL) × 1.10; earnings stability (5 of last 5); current dividend > 0; earnings growth; price: P/E < 10 OR price < TBVPS × 1.20.

### 5.2 TTM (`core/ttm_calculator.py`, `TTMCalculator`)
1. Constructor uses the price exactly as given (already normalised by the client — no second London Fix) and applies optional currency conversion to the periodic data (not triggered from the CLI).
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
2. Dividends: `try_convert_batch` to financials ccy at **current** rate; the "Could not convert dividends" warning is added only when it returns None (no FX rate).
3. Price: `EODHDClient.fetch_all_data` fetches the yfinance `PriceQuote` (I/O); `FinancialDataProcessor.get_current_price(quote, trading_ccy, warnings)` accepts it only if the price is positive **and** the quote currency matches EODHD's `General.CurrencyCode` (`same_currency`, any unit); otherwise it returns a reason and the assembler raises `PriceUnavailableError` (no EODHD price fallback: no price, no dossier). No I/O in core. Then:
   - unit from the **quote currency code** (F6): minor unit (GBp/GBX, ZAc, ILA) → ÷100 to the major currency (London Fix for GBP), logged in the conversion history; no P/E heuristic. EODHD's 52-week range is divided the same way (same exchange prices, same unit)
   - then convert to financials ccy; `fx_rate_used` recorded; historical FX fetched for fiscal year-ends.
4. Highlights dividend/BVPS, forward dividend, TTM dividend: GBX relabelled GBP, then converted.
5. `core.historical_prices.apply_year_end_prices` converts historical year-end prices: same Yahoo listing, so the quote's unit applies (÷100 for a minor unit, falling back to EODHD's trading code when `price_quote_currency` is absent), then historical FX with current-rate fallback.
6. Executive Summary treats the 52-week range as `price_currency_before_fx` and converts it with `fx_rate_used` (the rate already used for the price); no FX calls happen in the output layer.
7. All conversions are logged into `warnings` via `CurrencyConverter.get_consolidated_warning()`.

Price-unit logic lives in `core/price_quote.py` (`is_minor_unit`, `to_major_unit`). Other GBX logic: `CurrencyConverter.convert` (÷100), `FXClient.get_rate` (GBX treated as GBP, no factor), `convert_batch` (no special case), the assembler, `core.historical_prices`. Change one → check all.

**GBX units (verified against 30 real LSE dossiers in `data/`, 2026-10-31):** EODHD reports LSE *prices* in pence but dividend amounts (Dividend API `value`, Highlights `DividendShare`, `ForwardAnnualDividendRate`) in **pounds** even when labelled GBX (e.g. ABF: £0.90 trailing at £18.73; YU: £0.56 at £17.40). Hence prices are ÷100 while dividend paths treat GBX as GBP with no factor — do not "unify" them.

---

## 7. Price & exchange mapping

- `YFinanceClient.EXCHANGE_MAPPING` maps EODHD exchange codes → Yahoo suffix (US/NYSE/NASDAQ → '', LSE → .L, TO → .TO, XETRA → .DE, AU → .AX, HK → .HK, …; SAU → .SR, IL → .IL; 53 entries). Unmapped → bare symbol (warning); safe only because the quote currency must match.
- `_parse_ticker` splits on the last dot (`BRK.B.US` → `BRK.B`, `US`); `_translate_ticker` turns symbol dots into dashes (`BRK-B`, `BT-A.L`).
- Historical prices: `history(start, end, auto_adjust=False)` → `Close`, split-adjusted but **not** dividend-adjusted (F8); matched to fiscal year-ends with a 7-day backward window (`match_fiscal_year_end_prices`; FX uses an identical `match_fiscal_year_end_rates`).

---

## 8. Dossier

`DossierGenerator.generate()` renders in this **actual** order:

| # | Heading | Source |
|---|---|---|
| – | Header (`# STOCK ANALYSIS DOSSIER`, DATE, CEO/sector/currency) | `_generate_header` |
| 1 | EXECUTIVE SUMMARY | `executive_summary.py` `ExecutiveSummarySection(financial_data, metrics)` |
| 1.5 | TTM ANALYSIS (conditional) | `ttm_analysis.py` `TTMAnalysisSection(ttm_metrics, metrics, financial_data)` |
| 2 | KEY METRICS | `key_metrics.py` `KeyMetricsSection(financial_data, {'current_ratio': …})` — only the current ratio is passed; quick ratio and NCA are withheld until inventory is parsed and NCA uses CA − CL |
| – | RISK FACTORS | `risk_factors.py` `RiskFactorsSection` (`generate()` → `_generate_second_risk_section`) |
| – | METHODOLOGY NOTES | `methodology.py` `MethodologySection` |
| – | CALCULATION DETAILS | `calculation_details.py` `CalculationDetailsSection` |
| 4 / 5 | GRAHAM DEFENSIVE / ENTERPRISING TESTS | `graham_tests.py` `GrahamTestsSection(metrics)` |
| 6 | 20-YEAR FINANCIALS | `financial_history.py` `FinancialHistorySection(financial_data)` |
| 3 | CRITICAL ALERTS | `_generate_critical_alerts` (warnings + anomalies) — rendered **last** |

Each section's `generate()` returns `List[str]`; the generator joins with `\n`. Only some sections subclass `DossierSection`. Money amounts are formatted with `output.formatting.format_price_display` (one shared definition), though some sections still format inline (e.g. `USD29.11` in calculation_details). Several sections do their own arithmetic (BVPS, NCA, ratios, yields, risk bands) rather than reading core results. Criterion and formula text in Graham Tests, Methodology and Calculation Details is built from config (`GRAHAM_MULTIPLIER`, `COST_OF_CAPITAL`, `DEFENSIVE`/`ENTERPRISING`, `EPV_MIN/MAX_YEARS`); two enterprising lines ("5 of past 7 years", "Current Ratio > 1.5") are still literal because they misdescribe the code (code: 5 of 5, ≥) — fixed with F20.

---

## 9. Tests

- **Python 3.10+.** `requirements.txt` = runtime only (yfinance pinned to 1.0); `requirements-dev.txt` = runtime + pytest, hypothesis, time-machine, syrupy, import-linter, pytest-cov, coverage, ruff (all pinned).
- Run: `pytest` — live API tests (`@pytest.mark.live`) are excluded by default (`addopts = -m "not live"` in `pytest.ini`); run them with `pytest -m live`.
- Coverage: `pytest --cov` (opt-in, ~50% slower). Config in `pyproject.toml` (`[tool.coverage.*]`), branch coverage, **fails below `fail_under = 80`** — raise it as coverage improves, never lower it.
- Lint: `python3 -m ruff check .` (pyflakes + syntax errors, `[tool.ruff]` in `pyproject.toml`) must report zero findings — enforced by `tests/test_lint.py`.
- Mostly property-based (Hypothesis, 100+ examples) per calculation; section tests build inline dicts; `tests/fixtures_graham_metrics.py` builds processed `financial_data`; `tests/fixtures.py` holds raw API payloads (barely used).
- Markers (`pytest.ini`): `live` (deselected by default), `slow`.
- **Time:** output depends on the current date in 5 places — dossier `# DATE:` header, EODHD "API data is N days old" warning, TTM dividend 365-day window, `check_data_staleness` default, TTM future-date limit. Tests pin it with **time-machine** (`requirements-dev.txt`): `@pytest.mark.time_machine(datetime(..., tzinfo=timezone.utc), tick=False)` or the `time_machine` fixture's `move_to(..., tick=False)`. Use aware UTC times at noon so local timezone can't shift the date. Covered by `tests/test_time_dependence.py`.
- `tests/conftest.py` puts the project root on `sys.path`.
- **Snapshot (characterisation) tests** — `tests/test_dossier_snapshots.py`: runs the real `stock_data_analyser.main()` offline for 13 scenarios (`tests/snapshot_scenarios.py`: US mature/quarterly, US young company, LSE GBX London Fix semi-annual, LSE GBX low P/E, LSE GBX quarterly with one weak quarter, stale annual report, LSE GBP-labelled pence price, TSX CAD, XETRA EUR→USD financials, negative tangible equity, dividend counts only, and two malformed-data scenarios — JSON nulls in General/Highlights/Technicals plus a bad share-count row, and an LSE stock with a null 52-week high and a non-numeric dividend amount — each of which used to crash `main()`). Scenarios are built by deterministically varying `tests/fixtures.py` payloads (`extend_years`, `add_periodic`, `set_currencies`). Fakes replace only the outer boundaries (`tests/snapshot_fakes.py`): `FakeEODHDSession` inside the real `EODHDClient`, and `FakeYFinanceModule` in `sys.modules['yfinance']` for prices and FX. Date pinned to 2024-03-01. Per scenario, syrupy stores the dossier (`.md`) and the `financial_data` / `metrics` / `ttm_metrics` / `anomalies` passed to `DossierGenerator` (`[data].json`) under `tests/__snapshots__/test_dossier_snapshots/`. Snapshots record current behaviour **including known bugs**; after an intended output change, review the diff and run `pytest tests/test_dossier_snapshots.py --snapshot-update`.
- **Characterisation unit tests** — `tests/test_parsing_characterisation.py` (`extract_ceo_name`, `parse_income_statement`, `calculate_ttm_dividend`, `validate_data_quality`) and `tests/test_investor_tests_characterisation.py` (every defensive/enterprising `_test_*` method and `_determine_verdict`, with Hypothesis at each threshold boundary). They pin current behaviour; assertions that encode a known defect are marked `# Known defect:` — when fixing that defect, change the marked assertion in the same commit.
- Note: `tests/fixtures.py` spells goodwill `goodwill`, but EODHD (and the parser) use `goodWill`, so fixture goodwill is never parsed.
- **Network guard** (`tests/conftest.py`, autouse): non-`live` tests cannot reach the network. It blocks `socket` connect/DNS (requests/urllib3 → EODHD) and `curl_cffi` `Curl.perform` (yfinance prices and FX), allows localhost, and fails the test at teardown if any attempt was made — even if application code swallowed the error. Mock clients (e.g. `Mock(spec=FXClient)`, patch `EODHDClient._make_eodhd_request` **and** `_fetch_dividend_history`) or mark the test `@pytest.mark.live`. Guard behaviour is tested in `tests/test_network_guard.py`.
- Status: all non-live tests pass (1236 pass / 20 skip as of 2026-10-31); 89.7% branch coverage; weakest: base_client, yfinance_client.

---

## 10. Where to change things

| To… | Edit |
|---|---|
| add a Graham metric | `core/graham_math.py` (+ `compute_all`), property test, section in `output/sections/`, methodology text, **this guide §4.3/§5.1** |
| add an EODHD field | `financial_data_processor.py` parser + `merge_financial_data`; `FinancialDataAssembler.assemble` return dict; **§4.1/§4.2** |
| add an exchange | `YFinanceClient.EXCHANGE_MAPPING`; **§7** |
| change a threshold | `config/investor_thresholds.py` (Graham constants are immutable) — also hardcoded strings in `graham_tests.py`/`methodology.py` |
| add/reorder a section | `output/dossier_generator.py` + `output/sections/`; **§8** (order is fixed for LLM parsing) |
| change currency logic | every GBX site listed in **§6** |
