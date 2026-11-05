# STOCK ANALYSIS DOSSIER: AAPL.XETRA
# DATE: 2024-03-01
# SOURCE: EODHD (Tier 1 Data)
# CEO: Mr. Timothy D. Cook
# SECTOR: N/A | INDUSTRY: Consumer Electronics
# EMPLOYEES: 164,000
# MOST RECENT ANNUAL DATA: 2023
# CURRENCY: All values in USD (stock trades in EUR)

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (margin of safety -701.2%)
- Graham Number (Single-Year EPS): 23.68 USD
- Graham Number (3-Year Avg EPS): 23.40 USD
- Intrinsic Value (EPV per share): 47.89 USD (10-year average EPS)
- Net-Net Value: -9.46 USD
- Margin of Safety: -701.2% (Capped by Normalized Graham Number)
  - Conservative Intrinsic Value: 23.40 USD
- Current Price: 187.49 USD
- 52-Week Range: 124.17 EUR (134.41 USD) - 199.62 EUR (216.09 USD)
- Trailing Dividend: 0.95 USD (Yield: 0.51%) - Paid (Cash Flow) [2023]
  - Forward Rate: 1.04 USD (Yield: 0.55%)
- P/E Ratio (Current Year): 30.06
- P/E Ratio (3-Year Avg): 30.80 (based on avg EPS of 6.09 from 2021-2023)
- Price/Book: 46.91

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 156.08%
- Return on Assets (ROA): 27.50%
- Profit Margin: 25.31%
- Book Value Per Share: 4.00 USD

### Liquidity Analysis

- **Current Ratio**: 0.99 (Current Assets / Current Liabilities, fiscal year ending 2023-09-30)
- **Quick Ratio**: 0.94 (Acid Test - excludes inventory)

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 143,566,000,000.00 USD
- **Current Liabilities**: 145,308,000,000.00 USD
- **Net Current Assets**: -1,742,000,000.00 USD
- **Long-term Debt**: 106,000,000,000.00 USD
- **Debt Coverage Ratio**: N/A
- Insider Ownership: 0.07%
- Institutional Ownership: 61.44%

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Price Source: yfinance (primary source)
- Currency Conversions: EUR → USD at rate 1.0825; EUR → USD at rate 1.0825; EUR → USD at rate 1.0825
- [VALIDATION] API data is 46 days old (last update: 2024-01-15). Price and market data may be stale.
- [VALIDATION] ROA Difference: API shows 22.40% (TTM basis), calculated 27.50% (annual basis) (22.8% difference). Using annual data from audited financials per Graham methodology.
- Historical prices converted from EUR to USD using date-matched historical FX rates. This ensures accurate historical P/E and P/B ratios.
- TTM Analysis: Periodic data not available from API

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

### Statistical Anomalies (EPS growth, modified Z-Score > 3.5):
*Metrics that deviate significantly from historical patterns*

- Year 2023-09-30: EPS growth modified Z-Score = -5.21 (Outlier: -0.4% vs median +7.4%)

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:

### Financial Strength Risk:
- **Current Ratio: 0.99x** - ⚠️ Critical liquidity risk
- **Long-Term Debt: 106,000,000,000 USD** (30.0% of assets) - ⚠️ High leverage
  - Short-term debt and leases: 5,088,000,000 USD
  - Total debt: 111,088,000,000 USD (31.5% of assets)

### Operational Stability Risk:
- **Profit Margin Stability: 25.8% average, 0.2% std dev** over 10 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 156.1%** - Strong capital efficiency

### Dividend Sustainability Risk:
- **Payout Ratio: 15.3%** - Conservative (sustainable)
- **Dividend Coverage: 7.4x** from operating cash flow - Well covered
- **Dividend History: 9 of 10 years** - Mostly consistent

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -701.2%** - Trading above conservative intrinsic value
  - Assessment: **High valuation risk** - no margin of safety
  - Conservative Intrinsic Value: 23.40 USD
  - Current Price: 187.49 USD

### Data Quality Risk:
- **Institutional Ownership: 61.44%** - Verify with regulatory filings
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
   - P/E Ratio (3-year average EPS): 30.80
   - P/B Ratio (tangible book): 46.91
   - Product: 1444.98 (must be ≤ 22.5)
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
*All values in USD*

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2023 | 383.29B | 97.00B | 6.24 | 0.95 | 4.00 | ⚠️ -0.11 | 15.3% | 111.09B | 15.550B | 173.20 | 27.8 | 43.3 |
| 2022 | 394.33B | 99.80B | 6.26 | 0.93 | 3.18 | ⚠️ -1.17 | 14.8% | 120.07B | 15.943B | 188.03 | 30.0 | 59.1 |
| 2021 | 365.82B | 94.68B | 5.76 | N/A | 3.84 | 0.57 | 0.0% | 109.11B | 16.427B | 168.59 | 29.2 | 43.9 |
| 2020 | 347.53B | 89.95B | 5.30 | 0.81 | 3.53 | 0.52 | 15.3% | 103.65B | 16.977B | 151.05 | 28.5 | 42.8 |
| 2019 | 330.15B | 85.45B | 4.81 | 0.73 | 3.20 | 0.48 | 15.3% | 98.47B | 17.773B | 135.25 | 28.1 | 42.3 |
| 2018 | 313.64B | 81.18B | 4.48 | 0.68 | 2.98 | 0.44 | 15.3% | 93.54B | 18.128B | 121.00 | 27.0 | 40.6 |
| 2017 | 297.96B | 77.12B | 4.17 | 0.64 | 2.78 | 0.41 | 15.3% | 88.87B | 18.491B | 108.17 | 25.9 | 38.9 |
| 2016 | 283.06B | 73.26B | 3.88 | 0.59 | 2.59 | 0.38 | 15.3% | 84.42B | 18.861B | 96.62 | 24.9 | 37.3 |
| 2015 | 268.91B | 69.60B | 3.62 | 0.55 | 2.41 | 0.36 | 15.3% | 80.20B | 19.238B | 104.89 | 29.0 | 43.5 |
| 2014 | 255.46B | 66.12B | 3.37 | 0.51 | 2.25 | 0.33 | 15.3% | 76.19B | 19.623B | 94.05 | 27.9 | 41.8 |

**Note on Data Completeness:**

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
- **P/E Ratio (30.06)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 6.24 USD (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (23.68 USD)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ 15) and 7 (P/B ≤ 1.5), as 15 × 1.5 = 22.5
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 23.40 USD
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This follows Graham's sixth defensive criterion: price not more than
  15 times average earnings of the past three years.

  **3-Year EPS**: [2023: 6.24 USD, 2022: 6.26 USD, 2021: 5.76 USD] → Avg: 6.09 USD
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Per share: the same years' average EPS (each year's earnings over that year's shares), capitalized the same way
  - Graham's method: average past earnings capitalised at a multiplier kept "within a reasonable range of variation"; in 1976 he set a maximum multiple of 10

  **Note**: Dividing by 10% is a multiplier of 10. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).

  **Calculation for AAPL:**
  - Years Used: 10
  - Years: 2014-2023
  - Net Incomes: 96,995,000,000 USD, 99,803,000,000 USD, 94,680,000,000 USD, 89,946,000,000 USD, 85,448,700,000 USD, 81,176,265,000 USD, 77,117,451,750 USD, 73,261,579,162 USD, 69,598,500,204 USD, 66,118,575,194 USD
  - Normalized Earnings: 83,414,507,131 USD (average including losses)
  - EPV: 834,145,071,310 USD (83,414,507,131 USD / 10%)
  - EPS: 6.24, 6.26, 5.76, 5.30, 4.81, 4.48, 4.17, 3.88, 3.62, 3.37 USD
  - EPV Per Share: 47.89 USD (average EPS 4.79 USD / 10%)

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham on earning power**: *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -701.2%
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
  - Normalized Graham Number: 23.40 USD
  - EPV per share: 47.89 USD
  - **Intrinsic Value Used**: 23.40 USD (Capped by Normalized Graham Number)

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
- **Shares Outstanding**: 15,550,061,000 shares
- **Source**: Financial statements (outstandingShares.annual for 2023)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 62,146,000,000 USD
- **Less: Intangible Assets**: 0 USD
- **Less: Goodwill**: 0 USD
- **Tangible Book Value**: 62,146,000,000 USD
- **Divided by Shares**: 15,550,061,000
- **Tangible Book Value Per Share (TBVPS)**: 4.00 USD
- **Book Value Per Share (BVPS)**: 4.00 USD (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: 6.24 USD
- **TBVPS**: 4.00 USD
- **Calculation**: √(22.5 × 6.24 × 4.00) = √(560.89)
- **Graham Number**: 23.68 USD
- **Note**: Uses unrounded intermediate values for precision

### Currency Conversion Details:
- **FX Conversion Rate**: 1.0825 (EUR → USD)
- **Source**: Live FX rates from Frankfurter API (ECB data)
- **What Was Converted**:
  - Current stock price
  - Dividend amounts (if from Dividend API)
  - All values unified to USD for consistent analysis
- **Why Currency Unification Matters**:
  - Ensures all per-share calculations use the same currency
  - Prevents mixing GBX prices with GBP financials (100x error)
  - Allows accurate comparison of price to intrinsic value

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