# STOCK ANALYSIS DOSSIER: 7203.TSE
# DATE: 2026-11-01
# SOURCE: SEC EDGAR (20-F/40-F) + Yahoo Finance (Tier 1 Data)
# CEO: Test CEO Six
# SECTOR: Consumer Cyclical | INDUSTRY: Auto Manufacturers
# EMPLOYEES: 380,000
# MOST RECENT ANNUAL DATA: 2026
# CURRENCY: JPY

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (margin of safety -54.8%)
- Graham Number (Single-Year EPS): 4,510.73 JPY
- Graham Number (3-Year Avg EPS): 4,842.29 JPY
- Intrinsic Value (EPV per share): 2,131.19 JPY (10-year average EPS)
- Net-Net Value: -1,747.77 JPY
- Margin of Safety: -54.8% (Capped by EPV)
  - Conservative Intrinsic Value: 2,131.19 JPY
- Current Price: 3,300.00 JPY
- Trailing Dividend: 86.54 JPY (Yield: 2.62%) - Declared (Dividend API) [2026]
  - Forward Rate: 95.00 JPY (Yield: 2.88%)
- P/E Ratio (Current Year): 11.18
- P/E Ratio (3-Year Avg): 9.70 (based on avg EPS of 340.25 from 2024-2026)
- Price/Book: 1.08

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 9.64%
- Return on Assets (ROA): 3.65%
- Profit Margin: 7.59%
- Book Value Per Share: 3,062.82 JPY

### Liquidity Analysis

- **Current Ratio**: 1.27 (Current Assets / Current Liabilities, fiscal year ending 2026-03-31)
- **Quick Ratio**: 1.12 (Acid Test - excludes inventory)

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 42,824,081,000,000.00 JPY
- **Current Liabilities**: 33,605,019,000,000.00 JPY
- **Net Current Assets**: 9,219,062,000,000.00 JPY
- **Long-term Debt**: 26,171,943,000,000.00 JPY
- **Debt Coverage Ratio**: 2.84 (283.89%) - Long-term Debt / NCA

*Graham's defensive test: long-term debt should not exceed net current assets (working capital), i.e. a ratio of at most 1.0.*

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Statements: SEC EDGAR XBRL of TM (CIK 0001094517) (US listing TM), latest annual report 20-F filed 2026-06-10; price, dividends and profile from this home listing, so per-share figures are per ordinary share
- Per-share figures and share counts adjusted to today's share basis for stock splits (Yahoo Finance split history of the home listing): 2021-09-29 5:1
- No quarterly figures: foreign filers' interim reports (6-K) carry no XBRL, so TTM is N/A
- Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)
- SEC EDGAR: long-term debt: ifrs-full:LongtermBorrowings used (includes the current portion) (FY2021, FY2022, FY2023, FY2024, FY2025, FY2026)
- SEC EDGAR: long-term debt: includes non-current lease liabilities (leases count as debt) (FY2020, FY2021, FY2022, FY2023, FY2024, FY2025, FY2026)
- SEC EDGAR: total liabilities: derived as liabilities and equity - total equity (FY2009)
- SEC EDGAR: year-end shares: derived as shares issued - treasury shares (FY2009)
- SEC EDGAR: restated in later filings, latest figure used (first reported -> latest): FY2018 operating cash flow 4,210,009M -> 4,223,128M; FY2017 operating cash flow 3,414,237M -> 3,568,488M
- SEC EDGAR: FY2016 revenue uses SalesRevenueNet (26,549,111,000,000); total Revenues incl. other income is 28,403,118,000,000
- SEC EDGAR: FY2015 revenue uses SalesRevenueNet (25,612,836,000,000); total Revenues incl. other income is 27,234,521,000,000
- SEC EDGAR: FY2014 revenue uses SalesRevenueNet (24,312,644,000,000); total Revenues incl. other income is 25,691,911,000,000
- SEC EDGAR: FY2013 revenue uses SalesRevenueNet (20,914,150,000,000); total Revenues incl. other income is 22,064,192,000,000
- SEC EDGAR: FY2012 revenue uses SalesRevenueNet (17,511,916,000,000); total Revenues incl. other income is 18,583,653,000,000
- SEC EDGAR: FY2011 revenue uses SalesRevenueNet (17,820,520,000,000); total Revenues incl. other income is 18,993,688,000,000
- SEC EDGAR: FY2010 revenue uses SalesRevenueNet (17,724,729,000,000); total Revenues incl. other income is 18,950,973,000,000
- SEC EDGAR: FY2009 revenue uses SalesRevenueNet (19,173,720,000,000); total Revenues incl. other income is 20,529,570,000,000
- SEC EDGAR: FY2008 revenue uses SalesRevenueNet (24,820,510,000,000); total Revenues incl. other income is 26,289,240,000,000
- Price Source: yfinance (primary source)
- Year 2027-03-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2008-03-31: Incomplete data (missing: total_equity)
- Historical prices unavailable for 1 fiscal year ends (no trading data within 7-day window). Historical P/E and P/B will show N/A for those years.
- TTM Analysis: Periodic data not available from API

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

### Statistical Anomalies (EPS growth, modified Z-Score > 3.5):
*Metrics that deviate significantly from historical patterns*

- Year 2013-03-31: EPS growth modified Z-Score = 5.33 (Outlier: +236.8% vs median +10.4%)

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:

### Financial Strength Risk:
- **Current Ratio: 1.27x** - ⚠️ Below Graham's standards (defensive requires 2.0x)
- **Long-Term Debt: 26,171,943,000,000 JPY** (24.8% of assets) - Moderate
  - Short-term debt and leases: 17,744,539,000,000 JPY
  - Total debt: 43,916,482,000,000 JPY (41.6% of assets)
- **Debt Coverage: ⚠️** Long-term debt is 284% of Net Current Assets (fails Graham's defensive test)

### Operational Stability Risk:
- **Profit Margin Stability: 8.0% average, 1.6% std dev** over 10 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 9.6%** - ⚠️ Below 10% threshold

### Dividend Sustainability Risk:
- **Payout Ratio: 29.3%** - Conservative (sustainable)
- **Dividend Coverage: 4.9x** from operating cash flow - Well covered
- **Dividend History: 10 consecutive years** - Uninterrupted record (excellent)

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -54.8%** - Trading above conservative intrinsic value
  - Assessment: **High valuation risk** - no margin of safety
  - Conservative Intrinsic Value: 2,131.19 JPY
  - Current Price: 3,300.00 JPY

### Data Quality Risk:
- **Price Source: yfinance** (current quote; the only price source)


---

## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 2.0
3. **Debt to Assets**: FAIL
   - Criterion: Long-term debt ≤ net current assets (current assets − current liabilities)
4. **Dividend Record**: FAIL
   - Criterion: Uninterrupted dividend payments for at least 20 years
5. **Earnings Growth**: PASS
   - Criterion: Average EPS of the latest 3 reported years at least one-third (33.3%) above the average of the reported years 9-11 back
6. **P/E Ratio**: PASS
   - Criterion: Price ≤ 15 × average EPS of the last 3 reported years
7. **P/B Ratio**: PASS
   - Criterion: Price ≤ 1.5 × tangible book value per share, or P/E (3-year average EPS) × P/B ≤ 22.5
8. **Combined P/E × P/B Test** (criterion 7 alternative): PASS
   - P/E Ratio (3-year average EPS): 9.70
   - P/B Ratio (tangible book): 1.08
   - Product: 10.45 (must be ≤ 22.5)
   - *Graham: "a multiplier of earnings below 15 could justify a correspondingly higher multiplier of assets"; the product should not exceed 22.5. It relaxes the P/B limit only; the P/E limit (criterion 6) still applies.*

---

## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: No deficit in the last 5 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 1.5
3. **Debt to Assets**: FAIL
   - Criterion: Long-term debt ≤ 110% of net current assets (current assets − current liabilities)
4. **Dividend Record**: PASS
   - Criterion: Currently pays a dividend (last year > 0)
5. **Earnings Growth**: PASS
   - Criterion: Latest EPS above the EPS 5 reported years earlier
6. **Price Test**: FAIL
   - Criterion: P/E < 10 AND Price < 120% of Net Tangible Assets

---

## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)
*All values in JPY*

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2027 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 90.00 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2026 | 50684.95B | 3848.10B | 295.25 | 86.54 | 3062.82 | 707.34 | 29.3% | 43916.48B | 13.033B | 3157.89 | 10.7 | 1.0 |
| 2025 | 48036.70B | 4765.09B | 359.56 | 83.21 | 2753.09 | 585.83 | 23.1% | 39326.23B | 13.049B | 3015.79 | 8.4 | 1.1 |
| 2024 | 45095.32B | 4944.93B | 365.94 | 80.01 | 2539.75 | 410.89 | 21.9% | 37024.35B | 13.474B | 2873.68 | 7.9 | 1.1 |
| 2023 | 37154.30B | 2451.32B | 179.47 | 76.93 | 2089.08 | 184.30 | 42.9% | 29836.39B | 13.565B | 2731.58 | 15.2 | 1.3 |
| 2022 | 31379.51B | 2850.11B | 205.23 | 73.97 | 1904.88 | 136.46 | 36.0% | 26917.29B | 13.778B | 2589.47 | 12.6 | 1.4 |
| 2021 | 27214.59B | 2245.26B | 160.65 | 71.13 | 1674.18 | 94.16 | 44.3% | 26020.53B | 13.980B | 2447.37 | 15.2 | 1.5 |
| 2020 | 29866.55B | 2036.14B | 145.49 | 68.39 | 1490.80 | 59.37 | 47.0% | 21189.65B | 13.831B | 2305.26 | 15.8 | 1.5 |
| 2019 | 30225.68B | 1868.09B | 130.11 | 65.76 | 1366.18 | 46.06 | 50.5% | 20150.18B | 14.162B | 2163.16 | 16.6 | 1.6 |
| 2018 | 29379.51B | 2481.69B | 168.40 | 63.23 | 1287.73 | 24.45 | 37.5% | 19347.56B | 14.550B | 2021.05 | 12.0 | 1.6 |
| 2017 | 27597.19B | 1821.31B | 121.09 | 60.80 | 1177.58 | 34.61 | 50.2% | 19155.73B | 14.874B | 1878.95 | 15.5 | 1.6 |
| 2016 | 26549.11B | 2306.61B | 148.27 | 58.46 | 1102.61 | 137.28 | 39.4% | 18293.15B | 15.188B | 1736.84 | 11.7 | 1.6 |
| 2015 | 25612.84B | 2173.34B | 137.60 | 56.21 | 1066.99 | 95.65 | 40.9% | 18977.89B | 15.734B | 1594.74 | 11.6 | 1.5 |
| 2014 | 24312.64B | 1823.12B | 115.06 | 54.05 | 912.95 | 65.43 | 47.0% | 16327.39B | 15.849B | 1452.63 | 12.6 | 1.6 |
| 2013 | 20914.15B | 962.16B | 60.76 | 51.97 | 767.06 | 55.08 | 85.5% | 14131.78B | 15.837B | 1310.53 | 21.6 | 1.7 |
| 2012 | 17511.92B | 283.56B | 18.04 | 49.97 | 666.30 | 34.08 | 277.0% | 12005.55B | 15.834B | 1168.42 | 64.8 | 1.8 |
| 2011 | 17820.52B | 408.18B | 26.03 | 48.05 | 659.02 | 66.25 | 184.6% | 12401.06B | 15.678B | 1026.32 | 39.4 | 1.6 |
| 2010 | 17724.73B | 209.46B | 13.36 | 46.20 | 660.70 | 152.26 | 345.9% | 12513.41B | 15.680B | 884.21 | 66.2 | 1.3 |
| 2009 | 19173.72B | -436.94B | -27.83 | 44.43 | 641.68 | 45.26 | N/A | 12618.65B | 15.679B | 742.11 | Negative | 1.2 |
| 2008 | 24820.51B | 1717.88B | 108.13 | N/A | N/A | 0.00 | 0.0% | N/A | 13.034B | 600.00 | 5.5 | N/A |

**Note on Data Completeness:**
- Years marked '[Data Unavailable]' (2027) show declared dividends but lack complete audited annual financial statements
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
- **P/E Ratio (11.18)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 295.25 JPY (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (4,510.73 JPY)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ 15) and 7 (P/B ≤ 1.5), as 15 × 1.5 = 22.5
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 4,842.29 JPY
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This follows Graham's sixth defensive criterion: price not more than
  15 times average earnings of the past three years.

  **3-Year EPS**: [2026: 295.25 JPY, 2025: 359.56 JPY, 2024: 365.94 JPY] → Avg: 340.25 JPY
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Per share: the same years' average EPS (each year's earnings over that year's shares), capitalized the same way
  - Graham's method: average past earnings capitalised at a multiplier kept "within a reasonable range of variation"; in 1976 he set a maximum multiple of 10

  **Note**: Dividing by 10% is a multiplier of 10. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).

  **Calculation for 7203:**
  - Years Used: 10
  - Years: 2017-2026
  - Net Incomes: 3,848,098,000,000 JPY, 4,765,086,000,000 JPY, 4,944,933,000,000 JPY, 2,451,318,000,000 JPY, 2,850,110,000,000 JPY, 2,245,261,000,000 JPY, 2,036,140,000,000 JPY, 1,868,085,000,000 JPY, 2,481,692,000,000 JPY, 1,821,314,000,000 JPY
  - Normalized Earnings: 2,931,203,700,000 JPY (average including losses)
  - EPV: 29,312,037,000,000 JPY (2,931,203,700,000 JPY / 10%)
  - EPS: 295.25, 359.56, 365.94, 179.47, 205.23, 160.65, 145.49, 130.11, 168.40, 121.09 JPY
  - EPV Per Share: 2,131.19 JPY (average EPS 213.12 JPY / 10%)

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham on earning power**: *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -54.8%
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
  - Normalized Graham Number: 4,842.29 JPY
  - EPV per share: 2,131.19 JPY
  - **Intrinsic Value Used**: 2,131.19 JPY (Capped by EPV)

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
- **Shares Outstanding**: 13,033,384,000 shares
- **Source**: Financial statements (outstandingShares.annual for 2026)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 39,918,854,000,000 JPY
- **Less: Intangible Assets**: 0 JPY
- **Less: Goodwill**: 0 JPY
- **Tangible Book Value**: 39,918,854,000,000 JPY
- **Divided by Shares**: 13,033,384,000
- **Tangible Book Value Per Share (TBVPS)**: 3062.82 JPY
- **Book Value Per Share (BVPS)**: 3062.82 JPY (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: 295.25 JPY
- **TBVPS**: 3062.82 JPY
- **Calculation**: √(22.5 × 295.25 × 3062.82) = √(20346667.99)
- **Graham Number**: 4510.73 JPY
- **Note**: Uses unrounded intermediate values for precision

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