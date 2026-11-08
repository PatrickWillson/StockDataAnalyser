# STOCK ANALYSIS DOSSIER: SAP.XETRA
# DATE: 2026-11-01
# SOURCE: SEC EDGAR (20-F/40-F) + Yahoo Finance (Tier 1 Data)
# CEO: Test CEO Four
# SECTOR: Technology | INDUSTRY: Software - Application
# EMPLOYEES: 110,000
# MOST RECENT ANNUAL DATA: 2025
# CURRENCY: EUR

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (margin of safety -505.4%)
- Graham Number (Single-Year EPS): 39.68 EUR
- Graham Number (3-Year Avg EPS): 34.69 EUR
- Intrinsic Value (EPV per share): 37.43 EUR (10-year average EPS)
- Net-Net Value: -4.73 EUR
- Margin of Safety: -505.4% (Capped by Normalized Graham Number)
  - Conservative Intrinsic Value: 34.69 EUR
- Current Price: 210.00 EUR
- Trailing Dividend: 1.92 EUR (Yield: 0.92%) - Declared (Dividend API) [2025]
  - Forward Rate: 2.50 EUR (Yield: 1.19%)
- P/E Ratio (Current Year): 34.20
- P/E Ratio (3-Year Avg): 44.74 (based on avg EPS of 4.69 from 2023-2025)
- Price/Book: 5.49

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 16.06%
- Return on Assets (ROA): 10.18%
- Profit Margin: 19.46%
- Book Value Per Share: 38.24 EUR

### Liquidity Analysis

- **Current Ratio**: 1.16 (Current Assets / Current Liabilities, fiscal year ending 2025-12-31)
- **Quick Ratio**: N/A

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 20,256,000,000.00 EUR
- **Current Liabilities**: 17,416,000,000.00 EUR
- **Net Current Assets**: 2,840,000,000.00 EUR
- **Long-term Debt**: 5,980,000,000.00 EUR
- **Debt Coverage Ratio**: 2.11 (210.56%) - Long-term Debt / NCA

*Graham's defensive test: long-term debt should not exceed net current assets (working capital), i.e. a ratio of at most 1.0.*

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Statements: SEC EDGAR XBRL of SAP (CIK 0001000184) (US listing SAP), latest annual report 20-F filed 2026-02-26; price, dividends and profile from this home listing, so per-share figures are per ordinary share
- No quarterly figures: foreign filers' interim reports (6-K) carry no XBRL, so TTM is N/A
- Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)
- SEC EDGAR: long-term debt: ifrs-full:LongtermBorrowings used (includes the current portion) (FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025)
- SEC EDGAR: long-term debt: includes non-current lease liabilities (leases count as debt) (FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025)
- SEC EDGAR: year-end shares: weighted-average shares of the year (IFRS shares issued include treasury shares, and no treasury-share count is tagged) (FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025)
- SEC EDGAR: share count: weighted-average shares of the year (no balance sheet in the SEC data) (FY2015)
- SEC EDGAR: restated in later filings, latest figure used (first reported -> latest): FY2024 total assets 74,122M -> 74,237M; FY2024 liabilities and equity 74,122M -> 74,237M; FY2024 total liabilities 28,314M -> 28,431M; FY2024 goodwill 31,147M -> 31,264M; FY2024 operating cash flow 5,220M -> 5,207M; FY2023 operating cash flow 6,332M -> 6,246M; FY2022 revenue 30,871M -> 29,520M; FY2021 revenue 27,842M -> 26,953M; FY2018 equity incl. minority interest 28,877M -> 28,807M; FY2017 net income 4,018M -> 4,008M; FY2017 EPS 3.36 -> 3.35; FY2017 equity incl. minority interest 25,540M -> 25,573M; FY2016 net income 3,646M -> 3,642M
- Price Source: yfinance (primary source)
- [VALIDATION] Share Count: Using 1,166,000,000 shares from financial statements. Market data (SEC EDGAR (20-F/40-F) + Yahoo Finance) shows 1,228,504,232 shares (5.1% difference). Financial statement shares are used for accurate per-share calculations per Graham methodology.
- Year 2026-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2015-12-31: Incomplete data (missing: total_equity)
- Year 2014-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2013-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2012-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2011-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2010-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2009-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2008-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Potentially Stale Data: Most recent annual report is from 2025-12-31 (10 months old)
- Historical prices unavailable for 8 fiscal year ends (no trading data within 7-day window). Historical P/E and P/B will show N/A for those years.
- TTM Analysis: Periodic data not available from API
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
- **Current Ratio: 1.16x** - ⚠️ Below Graham's standards (defensive requires 2.0x)
- **Long-Term Debt: 5,980,000,000 EUR** (8.5% of assets) - Conservative
  - Short-term debt and leases: 1,854,000,000 EUR
  - Total debt: 7,834,000,000 EUR (11.1% of assets)
- **Debt Coverage: ⚠️** Long-term debt is 211% of Net Current Assets (fails Graham's defensive test)

### Operational Stability Risk:
- **Profit Margin Stability: 15.6% average, 4.4% std dev** over 10 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 16.1%** - Strong capital efficiency

### Dividend Sustainability Risk:
- **Payout Ratio: 31.3%** - Conservative (sustainable)
- **Dividend Coverage: 4.1x** from operating cash flow - Well covered
- **Dividend History: 10 consecutive years** - Uninterrupted record (excellent)

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -505.4%** - Trading above conservative intrinsic value
  - Assessment: **High valuation risk** - no margin of safety
  - Conservative Intrinsic Value: 34.69 EUR
  - Current Price: 210.00 EUR

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
5. **Earnings Growth**: N/A (Too Young)
   - Criterion: Average EPS of the latest 3 reported years at least one-third (33.3%) above the average of the reported years 9-11 back
6. **P/E Ratio**: FAIL
   - Criterion: Price ≤ 15 × average EPS of the last 3 reported years
7. **P/B Ratio**: FAIL
   - Criterion: Price ≤ 1.5 × tangible book value per share, or P/E (3-year average EPS) × P/B ≤ 22.5
8. **Combined P/E × P/B Test** (criterion 7 alternative): FAIL
   - P/E Ratio (3-year average EPS): 44.74
   - P/B Ratio (tangible book): 18.42
   - Product: 824.39 (must be ≤ 22.5)
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
*All values in EUR*

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2026 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 2.00 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2025 | 36.80B | 7.16B | 6.14 | 1.92 | 38.24 | 2.44 | 31.3% | 7.83B | 1.166B | 196.36 | 32.0 | 5.1 |
| 2024 | 34.18B | 3.12B | 2.68 | 1.85 | 38.97 | 1.99 | 69.0% | 11.10B | 1.166B | 182.73 | 68.2 | 4.7 |
| 2023 | 31.21B | 6.14B | 5.26 | 1.78 | 36.98 | 5.08 | 33.8% | 9.38B | 1.167B | 169.09 | 32.1 | 4.6 |
| 2022 | 29.52B | 2.28B | 1.95 | 1.71 | 34.35 | 0.91 | 87.7% | 13.90B | 1.170B | 155.45 | 79.7 | 4.5 |
| 2021 | 26.95B | 5.26B | 4.46 | 1.64 | 32.93 | 3.31 | 36.9% | 15.24B | 1.180B | 141.82 | 31.8 | 4.3 |
| 2020 | 27.34B | 5.14B | 4.35 | 1.58 | 25.14 | 1.88 | 36.3% | 15.40B | 1.182B | 128.18 | 29.5 | 5.1 |
| 2019 | 27.55B | 3.32B | 2.78 | 1.52 | 25.75 | 0.63 | 54.7% | 15.87B | 1.194B | 114.55 | 41.2 | 4.4 |
| 2018 | 24.71B | 4.08B | 3.42 | 1.46 | 24.15 | 5.14 | 42.7% | 11.33B | 1.194B | 100.91 | 29.5 | 4.2 |
| 2017 | 23.46B | 4.01B | 3.35 | 1.41 | 21.29 | 1.44 | 41.9% | 6.26B | 1.197B | 87.27 | 26.1 | 4.1 |
| 2016 | 22.06B | 3.64B | 3.04 | 1.35 | 22.02 | 1.58 | 44.4% | 7.83B | 1.198B | 73.64 | 24.2 | 3.3 |
| 2015 | 20.79B | 3.06B | 2.56 | 1.30 | N/A | 0.00 | 50.8% | N/A | 1.197B | 60.00 | 23.4 | N/A |
| 2014 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 1.25 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2013 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 1.20 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2012 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 1.16 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2011 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 1.11 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2010 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 1.07 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2009 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 1.03 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2008 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.99 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |

**Note on Data Completeness:**
- Years marked '[Data Unavailable]' (2026, 2014, 2013, 2012, 2011, 2010, 2009, 2008) show declared dividends but lack complete audited annual financial statements
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
- **P/E Ratio (34.20)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 6.14 EUR (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (39.68 EUR)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ 15) and 7 (P/B ≤ 1.5), as 15 × 1.5 = 22.5
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 34.69 EUR
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This follows Graham's sixth defensive criterion: price not more than
  15 times average earnings of the past three years.

  **3-Year EPS**: [2025: 6.14 EUR, 2024: 2.68 EUR, 2023: 5.26 EUR] → Avg: 4.69 EUR
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Per share: the same years' average EPS (each year's earnings over that year's shares), capitalized the same way
  - Graham's method: average past earnings capitalised at a multiplier kept "within a reasonable range of variation"; in 1976 he set a maximum multiple of 10

  **Note**: Dividing by 10% is a multiplier of 10. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).

  **Calculation for SAP:**
  - Years Used: 10
  - Years: 2016-2025
  - Net Incomes: 7,161,000,000 EUR, 3,124,000,000 EUR, 6,139,000,000 EUR, 2,284,000,000 EUR, 5,256,000,000 EUR, 5,145,000,000 EUR, 3,321,000,000 EUR, 4,083,000,000 EUR, 4,008,000,000 EUR, 3,642,000,000 EUR
  - Normalized Earnings: 4,416,300,000 EUR (average including losses)
  - EPV: 44,163,000,000 EUR (4,416,300,000 EUR / 10%)
  - EPS: 6.14, 2.68, 5.26, 1.95, 4.46, 4.35, 2.78, 3.42, 3.35, 3.04 EUR
  - EPV Per Share: 37.43 EUR (average EPS 3.74 EUR / 10%)

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham on earning power**: *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -505.4%
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
  - Normalized Graham Number: 34.69 EUR
  - EPV per share: 37.43 EUR
  - **Intrinsic Value Used**: 34.69 EUR (Capped by Normalized Graham Number)

  **Interpretation**: Normalized Graham Number is lower than EPV, indicating
  the stock trades at a premium to its asset value despite strong earnings power.
  Graham would prefer to buy at a discount to both metrics.

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
- **Shares Outstanding**: 1,166,000,000 shares
- **Source**: Financial statements (outstandingShares.annual for 2025)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 44,586,000,000 EUR
- **Less: Intangible Assets**: 2,282,000,000 EUR
- **Less: Goodwill**: 29,014,000,000 EUR
- **Tangible Book Value**: 13,290,000,000 EUR
- **Divided by Shares**: 1,166,000,000
- **Tangible Book Value Per Share (TBVPS)**: 11.40 EUR
- **Book Value Per Share (BVPS)**: 38.24 EUR (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: 6.14 EUR
- **TBVPS**: 11.40 EUR
- **Calculation**: √(22.5 × 6.14 × 11.40) = √(1574.63)
- **Graham Number**: 39.68 EUR
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