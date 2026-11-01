# STOCK ANALYSIS DOSSIER: YU.LSE
# DATE: 2024-03-01
# SOURCE: EODHD (Tier 1 Data)
# CEO: Mr. Baljit Bobby Kalar
# SECTOR: Utilities | INDUSTRY: Utilities - Diversified
# EMPLOYEES: 472
# MOST RECENT ANNUAL DATA: 2023
# CURRENCY: All values in GBP (stock trades in GBX)

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (margin of safety -349.6%)
- Graham Number (Single-Year EPS): 12.78 GBP
- Graham Number (3-Year Avg EPS): 8.42 GBP
  - ⚠️ Note: 3-year average (34% lower) reveals earnings peaked in recent year
- Intrinsic Value (EPV per share): 3.67 GBP (10-year average earnings)
- Net-Net Value: 0.06 GBP
- Margin of Safety: -349.6% (Capped by EPV)
  - Conservative Intrinsic Value: 3.67 GBP
- Current Price: 16.50 GBP (1,650 pence)
- Trailing Dividend: 0.28 GBP (Yield: 1.70%) - Paid (Dividend history) [2023]
- P/E Ratio (Current Year): 9.62
- P/E Ratio (3-Year Avg): 22.19 (based on avg EPS of 0.74 from 2021-2023)
- Price/Book: 3.67

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 38.10%
- Return on Assets (ROA): 16.24%
- Profit Margin: 4.98%
- Book Value Per Share: 4.50 GBP

### Liquidity Analysis

- **Current Ratio**: 1.29 (Current Assets / Current Liabilities, fiscal year ending 2023-12-31)
- **Quick Ratio**: 1.20 (Acid Test - excludes inventory)

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 110,000,000.00 GBP
- **Current Liabilities**: 85,000,000.00 GBP
- **Net Current Assets**: 25,000,000.00 GBP
- **Long-term Debt**: 9,500,000.00 GBP
- **Debt Coverage Ratio**: 0.38 (38.0%) - Long-term Debt / NCA

*Graham's defensive test: long-term debt should not exceed net current assets (working capital), i.e. a ratio of at most 1.0.*
- Insider Ownership: 65.00%
- Institutional Ownership: 13.73%
- Beta (Volatility): 0.668

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Price Source: yfinance (primary source)
- Currency Conversions: Batch conversion: 2 values from GBX → GBP at rate 1.0000; London Fix applied (GBp → GBP)
- [VALIDATION] API data is 46 days old (last update: 2024-01-15). Price and market data may be stale.
- [VALIDATION] ROE Difference: API shows 53.08% (TTM basis), calculated 38.10% (annual basis) (28.2% difference). Using annual data from audited financials per Graham methodology.
- [VALIDATION] ROA Difference: API shows 12.50% (TTM basis), calculated 16.24% (annual basis) (29.9% difference). Using annual data from audited financials per Graham methodology.
- TTM Analysis: Periodic data not available from API

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

### Statistical Anomalies (EPS growth, modified Z-Score > 3.5):
*Metrics that deviate significantly from historical patterns*

- Year 2023-12-31: EPS growth modified Z-Score = 364.05 (Outlier: +547.1% vs median +7.4%)

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:
- **Beta: 0.668** - Below-market volatility

### Financial Strength Risk:
- **Current Ratio: 1.29x** - ⚠️ Below Graham's standards (defensive requires 2.0x)
- **Long-Term Debt: 9,500,000 GBP** (5.0% of assets) - Conservative
- **Debt Coverage: ✓** Long-term debt ≤ net current assets (passes Graham's defensive test)

### Operational Stability Risk:
- **Profit Margin Stability: 1.2% average, 1.3% std dev** over 10 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 38.1%** - Strong capital efficiency

### Dividend Sustainability Risk:
- **Payout Ratio: 16.3%** - Conservative (sustainable)
- **Dividend History: 2 of 10 years** - ⚠️ Inconsistent payment history

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -349.6%** - Trading above conservative intrinsic value
  - Assessment: **High valuation risk** - no margin of safety
  - Conservative Intrinsic Value: 3.67 GBP
  - Current Price: 16.50 GBP

### Data Quality Risk:
- **Institutional Ownership: 13.73%** - Verify with regulatory filings
- **Price Source: yfinance** (current quote; the only price source)


---

## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 2.0
3. **Debt to Assets**: PASS
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
   - P/E Ratio (3-year average EPS): 22.19
   - P/B Ratio (tangible book): 3.90
   - Product: 86.47 (must be ≤ 22.5)
   - *Graham: "a multiplier of earnings below 15 could justify a correspondingly higher multiplier of assets"; the product should not exceed 22.5. It relaxes the P/B limit only; the P/E limit (criterion 6) still applies.*

---

## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: No deficit in the last 5 years
2. **Current Ratio**: FAIL
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
*All values in GBP*

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2023 | 620.00M | 30.86M | 1.71 | 0.28 | 4.50 | 1.39 | 16.3% | 9.50M | 18.00M | 16.50 | 9.6 | 3.7 |
| 2022 | 600.00M | 4.77M | 0.26 | 0.25 | 4.17 | 1.11 | 94.4% | 9.00M | 18.00M | 15.18 | 57.3 | 3.6 |
| 2021 | 570.00M | 4.53M | 0.25 | N/A | 3.96 | 1.06 | 0.0% | 8.55M | 18.00M | 13.97 | 55.5 | 3.5 |
| 2020 | 541.50M | 4.30M | 0.23 | N/A | 3.69 | 0.98 | 0.0% | 8.12M | 18.36M | 12.85 | 54.8 | 3.5 |
| 2019 | 514.42M | 4.09M | 0.22 | N/A | 3.43 | 0.92 | 0.0% | 7.72M | 18.73M | 11.82 | 54.1 | 3.4 |
| 2018 | 488.70M | 3.88M | 0.20 | N/A | 3.20 | 0.85 | 0.0% | 7.33M | 19.10M | 10.87 | 53.5 | 3.4 |
| 2017 | 464.27M | 3.69M | 0.19 | N/A | 2.98 | 0.79 | 0.0% | 6.96M | 19.48M | 10.00 | 52.8 | 3.4 |
| 2016 | 441.06M | 3.51M | 0.18 | N/A | 2.77 | 0.74 | 0.0% | 6.62M | 19.87M | 9.20 | 52.2 | 3.3 |
| 2015 | 419.00M | 3.33M | 0.16 | N/A | 2.58 | 0.69 | 0.0% | 6.29M | 20.27M | 8.47 | 51.5 | 3.3 |
| 2014 | 398.05M | 3.16M | 0.15 | N/A | 2.41 | 0.64 | 0.0% | 5.97M | 20.68M | 7.79 | 50.9 | 3.2 |

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

*Note: Historical prices converted to unified currency using current FX rates. Historical FX rates not used - actual historical valuations may differ due to FX fluctuations.*

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **P/E Ratio (9.62)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 1.71 GBP (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (12.78 GBP)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ 15) and 7 (P/B ≤ 1.5), as 15 × 1.5 = 22.5
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 8.42 GBP
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This follows Graham's sixth defensive criterion: price not more than
  15 times average earnings of the past three years.

  **3-Year EPS**: [2023: 1.71 GBP, 2022: 0.26 GBP, 2021: 0.25 GBP] → Avg: 0.74 GBP
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Graham's method: average past earnings capitalised at a multiplier kept "within a reasonable range of variation"; in 1976 he set a maximum multiple of 10

  **Note**: Dividing by 10% is a multiplier of 10. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).

  **Calculation for YU:**
  - Years Used: 10
  - Years: 2014-2023
  - Net Incomes: 30,860,000 GBP, 4,769,000 GBP, 4,530,550 GBP, 4,304,022 GBP, 4,088,821 GBP, 3,884,380 GBP, 3,690,161 GBP, 3,505,653 GBP, 3,330,371 GBP, 3,163,852 GBP
  - Normalized Earnings: 6,612,681 GBP (average including losses)
  - EPV: 66,126,810 GBP (6,612,681 GBP / 10%)
  - EPV Per Share: 3.67 GBP

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham on earning power**: *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)
- **Net-Net Value (0.06 GBP)**: (Current Assets - Total Liabilities - minority interests and other claims ahead of the common) / Shares
  - Graham's net current asset value: "current assets alone, minus all liabilities and claims ahead of the issue"
  - Graham bought at no more than two-thirds of it, as a diversified group

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -349.6%
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
  - Normalized Graham Number: 8.42 GBP
  - EPV per share: 3.67 GBP
  - **Intrinsic Value Used**: 3.67 GBP (Capped by EPV)

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
- **Shares Outstanding**: 18,000,000 shares
- **Source**: Financial statements (outstandingShares.annual for 2023)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 81,000,000 GBP
- **Less: Intangible Assets**: 4,800,000 GBP
- **Less: Goodwill**: 0 GBP
- **Tangible Book Value**: 76,200,000 GBP
- **Divided by Shares**: 18,000,000
- **Tangible Book Value Per Share (TBVPS)**: 4.23 GBP
- **Book Value Per Share (BVPS)**: 4.50 GBP (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: 1.71 GBP
- **TBVPS**: 4.23 GBP
- **Calculation**: √(22.5 × 1.71 × 4.23) = √(163.30)
- **Graham Number**: 12.78 GBP
- **Note**: Uses unrounded intermediate values for precision

### Net-Net Value Calculation:
- **Current Assets**: 110,000,000 GBP
- **Total Liabilities**: 109,000,000 GBP
- **Net Current Assets**: 1,000,000 GBP
- **Divided by Shares**: 18,000,000
- **Net-Net Value Per Share**: 0.06 GBP
- **Formula Used**: NCAV (Net Current Asset Value) = (Current Assets - Total Liabilities - claims ahead of the common) / Shares
  - **Note**: Graham's own measure: "current assets alone, minus all liabilities and claims ahead of the issue"
  - **Stricter alternative**: Graham's liquidating-value haircuts (Security Analysis ch. 43): cash 100%,
    receivables 75-90%, inventories 50-75%, fixed assets 1-50% (not applied here)

### Currency Conversion Details:
- **Stock Trading Currency**: GBX (price quoted in GBp)
- **Financial Statements Currency**: GBP
- **London Fix Applied**: Yes (GBp → GBP conversion)
  - The quote currency GBp is a minor unit (1/100 of GBP)
  - Current price, 52-week range and historical prices divided by 100
  - Example: 1,650 GBp = 16.50 GBP
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