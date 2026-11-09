# STOCK ANALYSIS DOSSIER: EXH.XETRA
# DATE: 2026-11-01
# SOURCE: Yahoo Finance statements (+ Eulerpool history) (Tier 1 Data)
# CEO: Test CEO Nine
# SECTOR: Industrials | INDUSTRY: Machinery
# EMPLOYEES: 4,000
# MOST RECENT ANNUAL DATA: 2025
# CURRENCY: EUR

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (margin of safety -76.5%)
- Graham Number (Single-Year EPS): 41.89 EUR
- Graham Number (3-Year Avg EPS): 41.19 EUR
- Intrinsic Value (EPV per share): 25.50 EUR (10-year average EPS)
- Net-Net Value: 6.00 EUR
- Margin of Safety: -76.5% (Capped by EPV)
  - Conservative Intrinsic Value: 25.50 EUR
- Current Price: 45.00 EUR
- Trailing Dividend: 0.86 EUR (Yield: 1.90%) - Declared (Dividend API) [2025]
- P/E Ratio (Current Year): 15.00
- P/E Ratio (3-Year Avg): 15.52 (based on avg EPS of 2.90 from 2023-2025)
- Price/Book: 1.73

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 11.54%
- Return on Assets (ROA): 6.00%
- Profit Margin: 6.67%
- Book Value Per Share: 26.00 EUR

### Liquidity Analysis

- **Current Ratio**: 2.86 (Current Assets / Current Liabilities, fiscal year ending 2025-12-31)
- **Quick Ratio**: 1.67 (Acid Test - excludes inventory)

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 600,000,000.00 EUR
- **Current Liabilities**: 210,000,000.00 EUR
- **Net Current Assets**: 390,000,000.00 EUR
- **Long-term Debt**: 150,000,000.00 EUR
- **Debt Coverage Ratio**: 0.38 (38.46%) - Long-term Debt / NCA

*Graham's defensive test: long-term debt should not exceed net current assets (working capital), i.e. a ratio of at most 1.0.*

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Statements: Yahoo Finance annual statements for FY2022-FY2025 (a statistical service, not the company's filings: no SEC or ESEF XBRL on the free routes); price, dividends and profile from this listing
- History before FY2022: Eulerpool (vendor data, not filings) for FY2014-FY2021 (8 years), checked only against Yahoo Finance. Used field by field, only where it agreed against Yahoo Finance's statements in FY2022-FY2025 (within 1.0%, or 1.1M for whole millions) in every overlapping year: revenue, net income, total assets, equity, current assets, current liabilities, total liabilities, inventory, year-end shares, operating cash flow, dividends paid. Never rescaled to fit; EPS for those years is net income / Eulerpool's year-end share count (its own EPS is not used); no intangibles (tangible book overstated); whole millions
- Eulerpool (vendor data, not filings): not used for the earlier years (disagreed with Yahoo Finance's statements in an overlapping year, or too few years to check): goodwill, long-term debt, short-term debt; long-term debt is then unknown in those years, not zero
- No quarterly figures: TTM is N/A
- Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)
- Price Source: yfinance (primary source)
- Year 2026-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2013-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2012-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2011-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2010-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2009-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2008-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Potentially Stale Data: Most recent annual report is from 2025-12-31 (10 months old)
- Historical prices unavailable for 7 fiscal year ends (no trading data within 7-day window). Historical P/E and P/B will show N/A for those years.
- TTM Analysis: Periodic data not available from API

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
- **Current Ratio: 2.86x** - Strong liquidity (meets Graham's 2.0x defensive standard)
- **Long-Term Debt: 150,000,000 EUR** (15.0% of assets) - Moderate
- **Debt Coverage: ✓** Long-term debt ≤ net current assets (passes Graham's defensive test)

### Operational Stability Risk:
- **Profit Margin Stability: 6.3% average, 0.3% std dev** over 10 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 11.5%** - Adequate returns

### Dividend Sustainability Risk:
- **Payout Ratio: 28.6%** - Conservative (sustainable)
- **Dividend Coverage: 4.7x** from operating cash flow - Well covered
- **Dividend History: 10 consecutive years** - Uninterrupted record (excellent)

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -76.5%** - Trading above conservative intrinsic value
  - Assessment: **High valuation risk** - no margin of safety
  - Conservative Intrinsic Value: 25.50 EUR
  - Current Price: 45.00 EUR

### Data Quality Risk:
- **Price Source: yfinance** (current quote; the only price source)


---

## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: PASS
   - Criterion: Current Ratio ≥ 2.0
3. **Debt to Assets**: PASS
   - Criterion: Long-term debt ≤ net current assets (current assets − current liabilities)
4. **Dividend Record**: FAIL
   - Criterion: Uninterrupted dividend payments for at least 20 years
5. **Earnings Growth**: PASS
   - Criterion: Average EPS of the latest 3 reported years at least one-third (33.3%) above the average of the reported years 9-11 back
6. **P/E Ratio**: FAIL
   - Criterion: Price ≤ 15 × average EPS of the last 3 reported years
7. **P/B Ratio**: FAIL
   - Criterion: Price ≤ 1.5 × tangible book value per share, or P/E (3-year average EPS) × P/B ≤ 22.5
8. **Combined P/E × P/B Test** (criterion 7 alternative): FAIL
   - P/E Ratio (3-year average EPS): 15.52
   - P/B Ratio (tangible book): 1.73
   - Product: 26.86 (must be ≤ 22.5)
   - *Graham: "a multiplier of earnings below 15 could justify a correspondingly higher multiplier of assets"; the product should not exceed 22.5. It relaxes the P/B limit only; the P/E limit (criterion 6) still applies.*

---

## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: No deficit in the last 5 years
2. **Current Ratio**: PASS
   - Criterion: Current Ratio ≥ 1.5
3. **Debt to Assets**: PASS
   - Criterion: Long-term debt ≤ 110% of net current assets (current assets − current liabilities)
4. **Dividend Record**: PASS
   - Criterion: Currently pays a dividend (last year > 0)
5. **Earnings Growth**: PASS
   - Criterion: Latest EPS above the EPS 5 reported years earlier
6. **Price Test**: FAIL
   - Criterion: P/E < 10 AND Price < 120% of Net Tangible Assets

---

## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)
*All values in EUR*

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2026 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.90 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2025 | 900.00M | 60.00M | 3.00 | 0.86 | 26.00 | 19.50 | 28.6% | 150.00M | 20.00M | 42.92 | 14.3 | 1.7 |
| 2024 | 880.00M | 58.00M | 2.90 | 0.82 | 25.25 | 19.50 | 28.1% | 150.00M | 20.00M | 40.83 | 14.1 | 1.6 |
| 2023 | 860.00M | 56.00M | 2.80 | 0.78 | 24.50 | 19.50 | 27.8% | 150.00M | 20.00M | 38.75 | 13.8 | 1.6 |
| 2022 | 840.00M | 54.00M | 2.70 | 0.74 | 23.75 | 19.50 | 27.4% | 150.00M | 20.00M | 36.67 | 13.6 | 1.5 |
| 2021 | 820.00M | 52.00M | 2.60 | 0.71 | 23.00 | 19.50 | 27.1% | N/A | 20.00M | 34.58 | 13.3 | 1.5 |
| 2020 | 800.00M | 50.00M | 2.50 | 0.67 | 22.25 | 19.50 | 26.9% | N/A | 20.00M | 32.50 | 13.0 | 1.5 |
| 2019 | 780.00M | 48.00M | 2.40 | 0.64 | 21.50 | 19.50 | 26.7% | N/A | 20.00M | 30.42 | 12.7 | 1.4 |
| 2018 | 760.00M | 46.00M | 2.30 | 0.61 | 20.75 | 19.50 | 26.5% | N/A | 20.00M | 28.33 | 12.3 | 1.4 |
| 2017 | 740.00M | 44.00M | 2.20 | 0.58 | 20.00 | 19.50 | 26.4% | N/A | 20.00M | 26.25 | 11.9 | 1.3 |
| 2016 | 720.00M | 42.00M | 2.10 | 0.55 | 19.25 | 19.50 | 26.3% | N/A | 20.00M | 24.17 | 11.5 | 1.3 |
| 2015 | 700.00M | 40.00M | 2.00 | 0.53 | 18.50 | 19.50 | 26.3% | N/A | 20.00M | 22.08 | 11.0 | 1.2 |
| 2014 | 680.00M | 38.00M | 1.90 | 0.50 | 17.75 | 19.50 | 26.4% | N/A | 20.00M | 20.00 | 10.5 | 1.1 |
| 2013 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.48 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2012 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.45 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2011 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.43 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2010 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.41 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2009 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.39 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2008 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.37 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |

**Note on Data Completeness:**
- Years marked '[Data Unavailable]' (2026, 2013, 2012, 2011, 2010, 2009, 2008) show declared dividends but lack complete audited annual financial statements
- **Graham's Principle**: Analysis and valuations use only complete annual data from audited financial statements
- Declared dividends are shown for income investors but excluded from historical calculations

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

*Note: Historical prices converted to unified currency using current FX rates. Historical FX rates not used - actual historical valuations may differ due to FX fluctuations.*

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **P/E Ratio (15.00)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 3.00 EUR (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (41.89 EUR)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ 15) and 7 (P/B ≤ 1.5), as 15 × 1.5 = 22.5
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 41.19 EUR
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This follows Graham's sixth defensive criterion: price not more than
  15 times average earnings of the past three years.

  **3-Year EPS**: [2025: 3.00 EUR, 2024: 2.90 EUR, 2023: 2.80 EUR] → Avg: 2.90 EUR
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Per share: the same years' average EPS (each year's earnings over that year's shares), capitalized the same way
  - Graham's method: average past earnings capitalised at a multiplier kept "within a reasonable range of variation"; in 1976 he set a maximum multiple of 10

  **Note**: Dividing by 10% is a multiplier of 10. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).

  **Calculation for EXH:**
  - Years Used: 10
  - Years: 2016-2025
  - Net Incomes: 60,000,000 EUR, 58,000,000 EUR, 56,000,000 EUR, 54,000,000 EUR, 52,000,000 EUR, 50,000,000 EUR, 48,000,000 EUR, 46,000,000 EUR, 44,000,000 EUR, 42,000,000 EUR
  - Normalized Earnings: 51,000,000 EUR (average including losses)
  - EPV: 510,000,000 EUR (51,000,000 EUR / 10%)
  - EPS: 3.00, 2.90, 2.80, 2.70, 2.60, 2.50, 2.40, 2.30, 2.20, 2.10 EUR
  - EPV Per Share: 25.50 EUR (average EPS 2.55 EUR / 10%)

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham on earning power**: *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)
- **Net-Net Value (6.00 EUR)**: (Current Assets - Total Liabilities - minority interests and other claims ahead of the common) / Shares
  - Graham's net current asset value: "current assets alone, minus all liabilities and claims ahead of the issue"
  - Graham bought at no more than two-thirds of it, as a diversified group

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -76.5%
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
  - Normalized Graham Number: 41.19 EUR
  - EPV per share: 25.50 EUR
  - **Intrinsic Value Used**: 25.50 EUR (Capped by EPV)

  **Interpretation**: EPV is lower than Normalized Graham Number, indicating
  that long-term earnings power is weaker than asset-based valuation suggests.
  This is a red flag - the company may be destroying value over the full cycle.

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
- **Shares Outstanding**: 20,000,000 shares
- **Source**: Financial statements (outstandingShares.annual for 2025)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 520,000,000 EUR
- **Less: Intangible Assets**: 0 EUR
- **Less: Goodwill**: 0 EUR
- **Tangible Book Value**: 520,000,000 EUR
- **Divided by Shares**: 20,000,000
- **Tangible Book Value Per Share (TBVPS)**: 26.00 EUR
- **Book Value Per Share (BVPS)**: 26.00 EUR (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: 3.00 EUR
- **TBVPS**: 26.00 EUR
- **Calculation**: √(22.5 × 3.00 × 26.00) = √(1755.00)
- **Graham Number**: 41.89 EUR
- **Note**: Uses unrounded intermediate values for precision

### Net-Net Value Calculation:
- **Current Assets**: 600,000,000 EUR
- **Total Liabilities**: 480,000,000 EUR
- **Net Current Assets**: 120,000,000 EUR
- **Divided by Shares**: 20,000,000
- **Net-Net Value Per Share**: 6.00 EUR
- **Formula Used**: NCAV (Net Current Asset Value) = (Current Assets - Total Liabilities - claims ahead of the common) / Shares
  - **Note**: Graham's own measure: "current assets alone, minus all liabilities and claims ahead of the issue"
  - **Stricter alternative**: Graham's liquidating-value haircuts (Security Analysis ch. 43): cash 100%,
    receivables 75-90%, inventories 50-75%, fixed assets 1-50% (not applied here)

### EPV Methodology Clarification:
- **Approach Used**: Simplified Earnings Capitalization
- **Formula**: Average Net Income (7-10 years) / 10%
- **Basis**: Graham capitalised average past earnings at a multiplier kept within a reasonable range (maximum 10 in 1976); dividing by 10% is a multiplier of 10
- **Cost of Capital**: 10% (conservative fixed rate for simplicity)
- **Includes Loss Years**: Yes (full business cycle)

**Relation to Graham's Work**:
- Graham defined past earning power as average earnings over a stated period (five, seven or ten years)
- The Graham Number (√(22.5 × EPS × TBVPS)) is not a formula Graham published; it is derived from his defensive criteria 6 and 7
- This EPV uses net income, including loss years and special items, over 7-10 years

**This Differs From Modern EPV (Greenwald, 2001)**:
- Modern EPV uses normalized EBIT, not net income
- Modern EPV subtracts maintenance CapEx
- Modern EPV uses company-specific WACC (typically 8-12%)
- Modern EPV is more precise but requires more estimation

**Why We Use This Simplified Approach**:
- Deterministic (no WACC estimation required)
- Conservative (uses net income, not EBIT)
- Consistent with other Graham-inspired metrics
- Transparent and auditable
- Provides reasonable valuation estimate for comparison

---