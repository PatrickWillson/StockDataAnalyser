# STOCK ANALYSIS DOSSIER: ALCLS.PA
# DATE: 2026-11-01
# SOURCE: SEC EDGAR (20-F/40-F) + Yahoo Finance (Tier 1 Data)
# CEO: Test CEO Seven
# SECTOR: Healthcare | INDUSTRY: Biotechnology
# EMPLOYEES: 230
# MOST RECENT ANNUAL DATA: 2025
# CURRENCY: All values in USD (stock trades in EUR)

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (no earning power: Negative normalized earnings (company unprofitable over cycle))
- Graham Number (Single-Year EPS): N/A
- Graham Number (3-Year Avg EPS): N/A
- Intrinsic Value (EPV per share): N/A (requires 7+ years of annual earnings with a positive average)
- Net-Net Value: -2.48 USD
- Margin of Safety: N/A (no earning power: Negative normalized earnings (company unprofitable over cycle))
- Current Price: 1.18 USD
- Price/Book: 1.55

---

## SECTION 2: KEY METRICS
- Book Value Per Share: 0.76 USD

### Liquidity Analysis

- **Current Ratio**: 0.00 (Current Assets / Current Liabilities, fiscal year ending 2025-12-31)
- **Quick Ratio**: N/A

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 0.00 USD
- **Current Liabilities**: 145,752,000.00 USD
- **Net Current Assets**: -145,752,000.00 USD
- **Long-term Debt**: not identified (the source reports borrowings but no long-term debt figure)
- **Debt Coverage Ratio**: N/A

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Statements: SEC EDGAR XBRL of CLLS (CIK 0001627281) (US listing CLLS), latest annual report 20-F filed 2026-03-20; price, dividends and profile from this home listing, so per-share figures are per ordinary share
- No quarterly figures: foreign filers' interim reports (6-K) carry no XBRL, so TTM is N/A
- Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)
- SEC EDGAR: long-term debt: not identified (ifrs-full:NoncurrentFinancialLiabilities is reported, no long-term debt figure): the debt tests count as not met, no debt is assumed (FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025)
- SEC EDGAR: total liabilities: derived as liabilities and equity - total equity (FY2014, FY2015, FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022)
- SEC EDGAR: revenue: not in the SEC data (the company uses its own tags) (FY2014)
- SEC EDGAR: net income: not available: only ProfitLoss is tagged and the minority interests' share of it is not (FY2014)
- SEC EDGAR: EPS: not in the SEC data (the company uses its own tags); derived from net income / shares where possible (FY2014)
- SEC EDGAR: EPS: filed at 1,000x net income / average shares (a scale error); divided by 1,000 (FY2015, FY2016)
- SEC EDGAR: restated in later filings, latest figure used (first reported -> latest): FY2021 revenue 57M -> 30M; FY2020 revenue 74M -> 51M; FY2020 minority interest 33M -> 25M; FY2020 stockholders' equity 276M -> 284M; FY2020 inventory 2M -> 2M; FY2017 equity incl. minority interest 286M -> 284M; FY2017 stockholders' equity 267M -> 265M; FY2017 current liabilities 44M -> 45M; FY2016 equity incl. minority interest 275M -> 273M; FY2015 equity incl. minority interest 287M -> 285M
- SEC EDGAR: figures a later filing tagged in thousands or millions as units were ignored: ifrs-full:ProfitLossAttributableToOrdinaryEquityHoldersOfParentEntity 2017, ifrs-full:ProfitLossAttributableToOrdinaryEquityHoldersOfParentEntity 2018
- Price Source: yfinance (primary source)
- Currency Conversions: EUR → USD at rate 1.1200
- Year 2014-12-31: Incomplete data (missing: revenue, net_income, eps)
- Potentially Stale Data: Most recent annual report is from 2025-12-31 (10 months old)
- Historical prices converted from EUR to USD using date-matched historical FX rates. This ensures accurate historical P/E and P/B ratios.
- TTM Analysis: Periodic data not available from API
- Negative 3-year average EPS (-0.95) - Company unsuitable for Graham methodology
- Quick Ratio: Cannot calculate - inventory not reported in the annual balance sheet

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:

### Financial Strength Risk:
- **Current Ratio: 0.00x** - ⚠️ Critical liquidity risk
- **Long-Term Debt: not identified** - the source reports borrowings but no long-term debt figure, so Graham's debt tests count as not met (no debt is assumed)
  - Short-term debt and leases identified: 7,701,000 USD

### Operational Stability Risk:
- **Profit Margin Stability: -1634.0% average, 4135.8% std dev** over 10 years
  - ⚠️ High volatility indicates cyclical or unstable business
- **Loss Years: 10 of 10** - ⚠️ Earnings not consistently positive

### Valuation Risk (Margin of Safety):
- **Margin of Safety: N/A** - Cannot assess valuation risk

### Data Quality Risk:
- **Price Source: yfinance** (current quote; the only price source)


---

## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS

1. **Earnings Stability**: FAIL
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 2.0
3. **Debt to Assets**: FAIL
   - Criterion: Long-term debt ≤ net current assets (current assets − current liabilities)
4. **Dividend Record**: FAIL
   - Criterion: Uninterrupted dividend payments for at least 20 years
5. **Earnings Growth**: FAIL
   - Criterion: Average EPS of the latest 3 reported years at least one-third (33.3%) above the average of the reported years 9-11 back
6. **P/E Ratio**: FAIL
   - Criterion: Price ≤ 15 × average EPS of the last 3 reported years
7. **P/B Ratio**: FAIL
   - Criterion: Price ≤ 1.5 × tangible book value per share, or P/E (3-year average EPS) × P/B ≤ 22.5
8. **Combined P/E × P/B Test** (criterion 7 alternative): N/A
   - Criterion: P/E × P/B ≤ 22.5

---

## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS

1. **Earnings Stability**: FAIL
   - Criterion: No deficit in the last 5 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 1.5
3. **Debt to Assets**: FAIL
   - Criterion: Long-term debt ≤ 110% of net current assets (current assets − current liabilities)
4. **Dividend Record**: FAIL
   - Criterion: Currently pays a dividend (last year > 0)
5. **Earnings Growth**: PASS
   - Criterion: Latest EPS above the EPS 5 reported years earlier
6. **Price Test**: FAIL
   - Criterion: P/E < 10 AND Price < 120% of Net Tangible Assets

---

## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)
*All values in USD*

| Year | Revenue | Net Income | EPS | Div Count | BVPS | WCPS | Payout Ratio | Total Debt | Shares | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2025 | 72.95M | -67.59M | -0.67 | N/A | 0.76 | ⚠️ -1.45 | N/A | 7.70M | 100.34M | 2.94 | Negative | 3.9 |
| 2024 | 41.51M | -36.76M | -0.41 | N/A | 1.31 | ⚠️ -1.66 | N/A | 8.38M | 100.09M | 4.71 | Negative | 3.6 |
| 2023 | 755,000 | -101.06M | -1.77 | N/A | 1.18 | ⚠️ -2.16 | N/A | 8.50M | 71.75M | 6.48 | Negative | 5.5 |
| 2022 | 19.17M | -106.14M | -2.33 | N/A | 2.58 | 1.62 | N/A | 7.87M | 45.68M | 8.25 | Negative | 3.2 |
| 2021 | 30.35M | -114.20M | -2.55 | N/A | 4.87 | 3.87 | N/A | 8.33M | 45.48M | 10.02 | Negative | 2.1 |
| 2020 | 51.06M | -81.07M | -1.91 | N/A | 6.63 | 6.16 | N/A | 6.70M | 42.78M | 11.79 | Negative | 1.8 |
| 2019 | 15.19M | -102.09M | -2.41 | N/A | 7.42 | 7.75 | N/A | 1.07M | 42.47M | 13.56 | Negative | 1.8 |
| 2018 | 12.73M | -78.69M | -1.93 | N/A | 9.65 | 10.39 | N/A | 0.33M | 42.43M | 15.33 | Negative | 1.6 |
| 2017 | 25.19M | -99.37M | -2.78 | N/A | 7.37 | 7.72 | N/A | N/A | 35.96M | 17.09 | Negative | 2.3 |
| 2016 | 44.81M | -67,255 | -0.0019 | N/A | 7.72 | 7.25 | N/A | N/A | 35.34M | 18.86 | Negative | 2.4 |
| 2015 | 55.86M | -22,796 | -0.0007 | N/A | 8.14 | 7.96 | N/A | N/A | 35.18M | 20.63 | Negative | 2.5 |
| 2014 | N/A | N/A | N/A | N/A | 2.51 | 2.36 | N/A | N/A | 29.45M | 22.40 | N/A | 8.9 |

**Note on Data Completeness:**

*Note: Dividend column shows number of payments per year (actual amounts not available from data source)*

**Graham Trend Analysis Columns:**
- **WCPS (Working Capital Per Share)**: (Current Assets - Current Liabilities) / Shares Outstanding
  - Measures the company's liquid net worth per share
  - Positive values indicate financial strength
  - ⚠️ Negative values indicate current liabilities exceed current assets (liquidity concern)
  - Trend analysis: Increasing WCPS shows improving financial strength
- **Payout Ratio**: (Dividend / EPS) × 100
  - Percentage of earnings paid as dividends
  - Values > 100% indicate unsustainable dividends (paying more than earned)
  - Values < 50% indicate conservative dividend policy with room for growth
  - 'N/A' shown for years with zero or negative earnings
- **Total Debt**: Reported total debt (short- and long-term, including lease obligations), else the sum of long- and short-term debt.
- **Shares**: Common shares outstanding (B = billions, M = millions). Tracks shareholder dilution (increasing shares) or buyback programs (decreasing shares).
- **Price**: Year-end stock price on fiscal year end date (or last trading day within 7 days prior). Source: Yahoo Finance via yfinance.
- **P/E**: Historical Price-to-Earnings ratio (Price ÷ EPS). Shows how the market valued earnings power over time. 'Negative' indicates a loss year.
- **P/B**: Historical Price-to-Book ratio (Price ÷ BVPS). Shows how the market valued net assets over time.

*Note: Historical prices converted to unified currency using date-matched historical FX rates from yfinance. This ensures accurate historical P/E and P/B ratios that reflect actual market conditions at the time.*

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **Profitability Metrics (ROE, ROA, Profit Margin)**:
  - **ROE (Return on Equity)**: Net Income / Total Stockholder Equity
    - Calculated from most recent annual audited data
    - Measures how efficiently company uses shareholder equity to generate profit
  - **ROA (Return on Assets)**: Net Income / Total Assets
    - Calculated from most recent annual audited data
    - Measures how efficiently company uses all assets to generate profit
  - **Profit Margin**: Net Income / Revenue
    - Calculated from most recent annual audited data
    - Measures what percentage of revenue becomes profit
  - **Why Annual Data vs TTM:**
    - Annual data comes from audited financial statements (verified)
    - TTM data may include estimates and unaudited quarters
    - Consistency: All Graham metrics (P/E, P/B, BVPS, ROE, ROA, Margin) use same fiscal year
    - Comparability: Annual data allows year-over-year comparison of audited results

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: N/A
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps'

  **3-Year EPS**: [2025: -0.67 USD, 2024: -0.41 USD, 2023: -1.77 USD] → Avg: -0.95 USD

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: N/A
  - **Formula**: ((Intrinsic Value - Current Price) / Intrinsic Value) × 100

  **Conservative Dual-Anchor Methodology**:

  This system uses the **lower** of two valuation methods as the intrinsic value:
  1. **Normalized Graham Number** (3-year average EPS)
  2. **EPV per share** (7-10 year normalized earnings)

  **Why This Is Conservative** (Graham's Philosophy):
  - Graham emphasized buying with a margin of safety
  - Using the lower value ensures we don't overpay
  - If a company looks cheap on assets (Graham Number) but has poor earnings
    power (EPV), the EPV reveals the true value
  - If a company has strong earnings (EPV) but trades above asset value
    (Graham Number), we use the more conservative asset-based valuation

  **For This Stock**:
  - Normalized Graham Number: N/A
  - EPV per share: 0.00 USD
  - **Intrinsic Value Used**: 0.00 USD (EPV only)

  **Interpretation**: Only the EPV is available (no earning power: Negative normalized earnings (company unprofitable over cycle)).

  **Graham's Principle**: *"The margin of safety is always dependent on the price paid."*
  Graham counted an issue a bargain when its indicated value was at least 50% above the price (price at most
  two-thirds of value), and a net-current-asset issue at no more than two-thirds of NCAV.

### P/E Ratio (3-Year Average)

**Graham's Defensive Criterion #6** states: *"Price should not exceed 15 times average earnings of the past three years."*

We calculate the 3-year average EPS by taking the arithmetic mean of the most recent three years of annual EPS data, **including loss years (negative EPS)**. This provides a more stable valuation metric that smooths out cyclical fluctuations.

**Formula**: P/E (3-Year Avg) = Current Price / ((EPS_Y1 + EPS_Y2 + EPS_Y3) / 3)

**Note**: Loss years are included in the average as negative values, which reduces the average EPS and increases the P/E ratio, reflecting the company's historical volatility.

### Quick Ratio (Acid Test)

The Quick Ratio is a more stringent liquidity test than the Current Ratio. It excludes inventory from current assets, as inventory may not be quickly convertible to cash.

**Formula**: Quick Ratio = (Current Assets - Inventory) / Current Liabilities

A Quick Ratio > 1.0 indicates the company can meet short-term obligations without relying on inventory sales. It is shown for information only: Graham's criteria use the current ratio.

**Note**: When inventory is not reported in the annual balance sheet, the Quick Ratio is N/A (never estimated).

### Net Current Assets (Working Capital) and Debt Coverage

Net current assets here are working capital, as in Graham's defensive debt test (not the net-net value, which deducts all liabilities).

**Formula**: NCA = Current Assets - Current Liabilities

**Debt Coverage Ratio** = Long-term Debt / NCA

Graham's defensive investor test: long-term debt "should not exceed the net current assets (or working capital)" (ratio at most 1.0).

**Note**: For regulated utilities Graham uses debt ≤ 2 × stock equity instead; for financial companies NCA analysis may not be applicable.

### Combined P/E × P/B Test

Graham: "a multiplier of earnings below 15 could justify a correspondingly higher multiplier of assets ... the product of the multiplier times the ratio of price to book value should not exceed 22.5" (The Intelligent Investor, ch. 14). So criterion 7 (P/B ≤ 1.5) is also met when the product is within 22.5:

- P/E of 15 allows P/B up to 1.5
- P/E of 9 allows P/B up to 2.5 (Graham's example: "9 times earnings and 2.5 times asset value")
- It relaxes the P/B limit only: the P/E must still be ≤ 15 (criterion 6)

**Formula**: P/E (3-year average EPS) × P/B (tangible book value per share) ≤ 22.5

### Historical Trend Metrics

**Working Capital Per Share (WCPS)**: (Current Assets - Current Liabilities) / Shares Outstanding
- Measures the company's liquid net worth per share
- Positive values indicate financial strength; negative values indicate liquidity concerns
- Trend analysis: Increasing WCPS shows improving financial strength over time

**Payout Ratio**: (Dividend / EPS) × 100
- Percentage of earnings paid as dividends
- Values > 100% indicate unsustainable dividends (paying more than earned)
- Values < 50% indicate conservative dividend policy with room for growth
- 'N/A' shown for years with zero or negative earnings (cannot assess sustainability against losses)


### TTM (Trailing Twelve Months) Calculations:

TTM calculations provide more current financial metrics by using the most recent 12 months of periodic data:

**Income Statement Items** (Revenue, Net Income, EPS):
- **Quarterly reporters**: Sum of last 4 quarters
- **Semi-annual reporters**: Sum of last 2 periods (H1 + H2)
- **EPS Calculation**: TTM EPS = Sum(Net Income) / Most Recent Shares Outstanding
  - **Important**: Do NOT sum EPS values directly (incorrect when share count changes)
  - Example: If shares increase from 50M to 55M during the year, summing EPS overstates earnings power

**Balance Sheet Items** (Assets, Liabilities, Equity):
- Use most recent period value (not summed)
- Balance sheet represents point-in-time snapshot, not cumulative

**Reporting Frequency Detection**:
- Average interval ~90 days (±15 days) → Quarterly
- Average interval ~180 days (±30 days) → Semi-annual
- Irregular intervals → Warning + attempt to use most recent continuous 12-month period

**TTM vs Annual**:
- **TTM**: More current (includes most recent quarter)
  - Reflects recent business performance
  - May include unaudited quarterly data
  - Better for fast-changing businesses
- **Annual**: More stable (full fiscal year, audited)
  - Verified by external auditors
  - Smooths out seasonal variations
  - Graham's preferred methodology
- Both are valuable for different reasons

**Limitations**:
- TTM data may be unaudited (quarterly reports)
- Seasonal businesses may show distortions
- Currency conversion uses current rate (not historical)
- Requires sufficient periodic data (4 quarters or 2 semi-annual periods)
- Data gaps or irregular reporting may prevent TTM calculation

---

## CALCULATION DETAILS
*Detailed breakdown of key calculations for transparency and verification*

### Share Count Used:
- **Shares Outstanding**: 100,339,441 shares
- **Source**: Financial statements (outstandingShares.annual for 2025)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 75,901,000 USD
- **Less: Intangible Assets**: 535,000 USD
- **Less: Goodwill**: 0 USD
- **Tangible Book Value**: 75,366,000 USD
- **Divided by Shares**: 100,339,441
- **Tangible Book Value Per Share (TBVPS)**: 0.75 USD
- **Book Value Per Share (BVPS)**: 0.76 USD (without subtracting intangibles)

### Currency Conversion Details:
- **FX Conversion Rate**: 1.1200 (EUR → USD)
- **Source**: Live FX rates from Frankfurter API (ECB data)
- **What Was Converted**:
  - Current stock price
  - Dividend amounts (if from Dividend API)
  - All values unified to USD for consistent analysis
- **Why Currency Unification Matters**:
  - Ensures all per-share calculations use the same currency
  - Prevents mixing GBX prices with GBP financials (100x error)
  - Allows accurate comparison of price to intrinsic value


---