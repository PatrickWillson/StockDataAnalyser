# STOCK ANALYSIS DOSSIER: AAPL.US
# DATE: 2024-03-01
# SOURCE: EODHD (Tier 1 Data)
# CEO: Mr. Timothy D. Cook
# SECTOR: Technology | INDUSTRY: Consumer Electronics
# EMPLOYEES: 164,000
# MOST RECENT ANNUAL DATA: 2023
# CURRENCY: USD

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
- Graham Number (Single-Year EPS): 23.68 USD
- Graham Number (3-Year Avg EPS): 19.35 USD
- Intrinsic Value (EPV per share): 53.64 USD (10-year average earnings)
- Net-Net Value: -9.45 USD
- Margin of Safety: -868.7% (Capped by Normalized Graham Number)
  - Conservative Intrinsic Value: 19.35 USD
- Current Price: 187.45 USD
- 52-Week Range: 124.17 USD - 199.62 USD
- Trailing Dividend: 4.00 USD (Yield: 2.13%) [2023]
- P/E Ratio (Current Year): 30.05
- P/E Ratio (3-Year Avg): 30.79 (based on avg EPS of 6.09 from 2021-2023)
- Price/Book: 46.90

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 156.08%
- Return on Assets (ROA): 27.50%
- Profit Margin: 25.31%
- Book Value Per Share: 4.00 USD

### Liquidity Analysis

- Insider Ownership: 0.07%
- Institutional Ownership: 61.44%
- Beta (Volatility): 1.290

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:
- **Beta: 1.290** - Above-market volatility

### Financial Strength Risk:
- **Current Ratio: 0.99x** - ⚠️ Critical liquidity risk
- **Long-Term Debt: $106,000,000,000 USD** (30.0% of assets) - ⚠️ High leverage
  - Short-term debt: $15,000,000 USD
  - Total debt: $106,015,000,000 USD (30.1% of assets)

### Operational Stability Risk:
- **Profit Margin Stability: 25.7% average, 0.3% std dev** over 6 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 156.1%** - Strong capital efficiency

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -868.7%** - Trading above intrinsic value
  - Graham's Standard: 20-30% minimum for defensive investors
  - Assessment: **High valuation risk** - no margin for error
  - Intrinsic Value (Graham): 23.68 USD
  - Current Price: 187.45 USD

### Data Quality Risk:
- **Institutional Ownership: 61.44%** - Verify with regulatory filings
- **Price Source: yfinance** - ⚠️ Using fallback source (EODHD unavailable)

**Graham's Principle on Risk**: *"The essence of investment management is the management of risks, not the management of returns. Returns are the reward for taking risk, but the risk must be measured and managed."*

---

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **P/E Ratio (30.05)**: Current Price / Most Recent Annual EPS
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
  - Based on Benjamin Graham's formula from 'The Intelligent Investor'
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 19.35 USD
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This aligns with Graham's actual criterion: *"Price should not exceed"*
  *"15 times average earnings of the past three years."*

  **3-Year EPS**: [2023: 6.24 USD, 2022: 0.00 USD, 2022: 6.26 USD] → Avg: 4.17 USD
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Inspired by Graham's emphasis on full-cycle earnings

  **Important**: This is a simplified approach, not Graham's original methodology.
  Graham emphasized earnings power conceptually but didn't prescribe this exact formula.

  **Calculation for AAPL:**
  - Years Used: 10
  - Years: 2014-2023
  - Net Incomes: USD96,995,000,000, USD99,803,000,000, USD94,680,000,000, USD89,946,000,000, USD85,448,700,000, USD81,176,265,000, USD77,117,451,750, USD73,261,579,162, USD69,598,500,204, USD66,118,575,194
  - Normalized Earnings: USD83,414,507,131 (average including losses)
  - EPV: USD834,145,071,310 (USD83,414,507,131 / 10%)
  - EPV Per Share: 53.64 USD

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham's Principle**: *"The concept of 'earning power' implies a fairly confident expectation of certain future results, based on past performance under varying conditions. The record must cover a number of years, first because a continued or repeated performance is always more impressive than a single occurrence and secondly because the average of a fairly long period will tend to absorb and equalize the distorting influences of the business cycle."*

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -868.7%
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
  - Normalized Graham Number: 19.35 USD
  - EPV per share: 53.64 USD
  - **Intrinsic Value Used**: 19.35 USD (Capped by Normalized Graham Number)

  **Interpretation**: Normalized Graham Number is lower than EPV, indicating
  the stock trades at a premium to its asset value despite strong earnings power.
  Graham would prefer to buy at a discount to both metrics.

  **Graham's Principle**: *"The margin of safety is always dependent on the price paid."*
  Graham recommended a minimum 20-30% margin of safety for defensive investors.

### P/E Ratio (3-Year Average)

**Graham's Defensive Criterion #6** states: *"Price should not exceed 15 times average earnings of the past three years."*

We calculate the 3-year average EPS by taking the arithmetic mean of the most recent three years of annual EPS data, **including loss years (negative EPS)**. This provides a more stable valuation metric that smooths out cyclical fluctuations.

**Formula**: P/E (3-Year Avg) = Current Price / ((EPS_Y1 + EPS_Y2 + EPS_Y3) / 3)

**Note**: Loss years are included in the average as negative values, which reduces the average EPS and increases the P/E ratio, reflecting the company's historical volatility.

### Quick Ratio (Acid Test)

The Quick Ratio is a more stringent liquidity test than the Current Ratio. It excludes inventory from current assets, as inventory may not be quickly convertible to cash.

**Formula**: Quick Ratio = (Current Assets - Inventory) / Current Liabilities

A Quick Ratio > 1.0 indicates the company can meet short-term obligations without relying on inventory sales. Graham preferred companies with strong liquidity positions.

**Note**: For Services and Technology companies with minimal inventory, if inventory data is unavailable, we use Current Assets directly (equivalent to Current Ratio).

### Net Current Assets (NCA) and Debt Coverage

Net Current Assets represents the company's liquid net worth after paying all liabilities.

**Formula**: NCA = Current Assets - Total Liabilities

**Debt Coverage Ratio** = Long-term Debt / NCA

Graham's defensive investor test requires long-term debt to be less than NCA (ratio < 1.0). This ensures the company could theoretically pay off all long-term debt using only its liquid assets.

**Note**: For Financial and Utility companies, NCA analysis may not be applicable due to their unique balance sheet structures (high leverage is normal for these sectors).

### Combined P/E × P/B Test

Graham specified that for defensive investors, the product of P/E and P/B ratios should not exceed 22.5. This rule provides flexibility in valuation:

- A company with P/E of 15 can have P/B up to 1.5 (15 × 1.5 = 22.5)
- A company with P/E of 10 can have P/B up to 2.25 (10 × 2.25 = 22.5)
- A company with P/B of 0.5 can have P/E up to 45 (45 × 0.5 = 22.5)

**Formula**: Combined Test = P/E Ratio × P/B Ratio ≤ 22.5

This test recognizes that a low price relative to book value can compensate for higher earnings multiples, and vice versa.

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
- **Total Stockholder Equity**: USD62,146,000,000
- **Less: Intangible Assets**: USD0
- **Less: Goodwill**: USD0
- **Tangible Book Value**: USD62,146,000,000
- **Divided by Shares**: 15,550,061,000
- **Tangible Book Value Per Share (TBVPS)**: USD4.00
- **Book Value Per Share (BVPS)**: USD4.00 (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: USD6.24
- **TBVPS**: USD4.00
- **Calculation**: √(22.5 × 6.24 × 4.00) = √(560.89)
- **Graham Number**: USD23.68
- **Note**: Uses unrounded intermediate values for precision

### EPV Methodology Clarification:
- **Approach Used**: Simplified Earnings Capitalization
- **Formula**: Average Net Income (7-10 years) / 10%
- **Inspiration**: Graham's emphasis on full-cycle earnings (not a direct Graham formula)
- **Cost of Capital**: 10% (conservative fixed rate for simplicity)
- **Includes Loss Years**: Yes (full business cycle)

**This Differs From Graham's Original Work**:
- Graham discussed 'earning power' conceptually but didn't provide this specific formula
- Graham Number (√(22.5 × EPS × BVPS)) is Graham's actual intrinsic value formula
- Our EPV is a simplified interpretation of Graham's principles

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

## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 2.0
3. **Debt to Assets**: FAIL
   - Criterion: Long-term Debt < Net Current Assets
4. **Dividend Record**: FAIL
   - Criterion: Uninterrupted dividend payments for at least 20 years
5. **Earnings Growth**: PASS
   - Criterion: Earnings growth ≥ 33% over 10 years
6. **P/E Ratio**: FAIL
   - Criterion: P/E Ratio < 15
7. **P/B Ratio**: FAIL
   - Criterion: Price/Book Ratio < 1.5
8. **Combined P/E × P/B Test**: FAIL
   - P/E Ratio: 30.05
   - P/B Ratio: 46.90
   - Product: 1409.35 (must be ≤ 22.5)
   - *Graham specified that P/E × P/B should not exceed 22.5. This provides flexibility: a company can have a higher P/E if it has a low P/B, or vice versa.*

---

## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: Profitability in most recent year and 5 of past 7 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio > 1.5
3. **Debt to Assets**: FAIL
   - Criterion: Debt < 110% of Net Current Assets
4. **Dividend Record**: PASS
   - Criterion: Currently pays a dividend (last year > 0)
5. **Earnings Growth**: N/A - Not Required
6. **Price Test**: FAIL
   - Criterion: P/E < 10 OR Price < 120% of Net Tangible Assets

**Note on Earnings Growth:** Earnings growth is intentionally not required for Enterprising Investors per Graham's methodology. Unlike Defensive Investors (who require 7 tests including ≥33% earnings growth over 10 years), Enterprising Investors require only 6 tests focused on current financial strength and price. Graham's logic: Enterprising investors actively seek bargains, turnarounds, or cyclical companies trading below intrinsic value—situations where historical growth may be absent but current fundamentals and price create opportunity.

---

## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)
*All values in USD*

| Year | Revenue | Net Income | EPS | Div Count | BVPS | WCPS | Payout Ratio | Total Debt | Shares (B) | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2023 | 383285000000.0 | 96995000000.0 | 6.237596109751595 | 4.0 | 4.0 | ⚠️ -0.11 | 64.1% | 106.02B | 15.550B | 187.45 | 30.1 | 46.9 |
| 2022 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 4.0 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2022 | 394328000000.0 | 99803000000.0 | 6.259821838783072 | 4.0 | 3.18 | ⚠️ -1.17 | 63.9% | 98.96B | 15.943B | 172.45 | 27.5 | 54.2 |
| 2021 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 4.0 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2021 | 365817000000.0 | 94680000000.0 | 5.763756829850952 | 4.0 | 3.84 | 0.57 | 69.4% | 109.11B | 16.427B | 158.66 | 27.5 | 41.3 |
| 2020 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 4.0 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2020 | 347526150000.0 | 89946000000.0 | 5.298183169547693 | 4.0 | 3.53 | 0.52 | 75.5% | 103.65B | 16.977B | 145.97 | 27.6 | 41.3 |
| 2019 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 4.0 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2019 | 330149842500.0 | 85448700000.0 | 4.807796614899591 | 4.0 | 3.2 | 0.48 | 83.2% | 98.47B | 17.773B | 134.29 | 27.9 | 42.0 |
| 2018 | 313642350375.0 | 81176265000.0 | 4.477849788386874 | N/A | 2.98 | 0.44 | 0.0% | 93.54B | 18.128B | 123.54 | 27.6 | 41.5 |
| 2017 | 297960232856.0 | 77117451750.0 | 4.170546371672121 | N/A | 2.78 | 0.41 | 0.0% | 88.87B | 18.491B | 113.66 | 27.3 | 40.9 |
| 2016 | 283062221213.0 | 73261579162.0 | 3.8843324049086845 | N/A | 2.59 | 0.38 | 0.0% | 84.42B | 18.861B | 104.57 | 26.9 | 40.4 |
| 2015 | 268909110153.0 | 69598500204.0 | 3.617760573227029 | N/A | 2.41 | 0.36 | 0.0% | 80.20B | 19.238B | 96.20 | 26.6 | 39.9 |
| 2014 | 255463654645.0 | 66118575194.0 | 3.3694828868839335 | N/A | 2.25 | 0.33 | 0.0% | 76.19B | 19.623B | 88.51 | 26.3 | 39.3 |

**Note on Data Completeness:**
- Years marked '[Data Unavailable]' (2022, 2021, 2020, 2019) show declared dividends but lack complete audited annual financial statements
- **Graham's Principle**: Analysis and valuations use only complete annual data from audited financial statements
- Declared dividends are shown for income investors but excluded from historical calculations

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
- **Total Debt**: Sum of long-term and short-term debt. Graham emphasized tracking debt trends to distinguish companies that grow through retained earnings vs leverage.
- **Shares (B)**: Common shares outstanding in billions. Tracks shareholder dilution (increasing shares) or buyback programs (decreasing shares).
- **Price**: Year-end stock price on fiscal year end date (or last trading day within 7 days prior). Source: Yahoo Finance via yfinance.
- **P/E**: Historical Price-to-Earnings ratio (Price ÷ EPS). Shows how the market valued earnings power over time. 'Negative' indicates loss year (Graham's method: show losses explicitly).
- **P/B**: Historical Price-to-Book ratio (Price ÷ BVPS). Shows how the market valued net assets over time.

*Note: Historical prices converted to unified currency using current FX rates. Historical FX rates not used - actual historical valuations may differ due to FX fluctuations.*

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Price Source: yfinance (primary source)
- [VALIDATION] API data is 46 days old (last update: 2024-01-15). Price and market data may be stale.
- [VALIDATION] ROA Difference: API shows 22.40% (TTM basis), calculated 27.50% (annual basis) (22.8% difference). Using annual data from audited financials per Graham methodology.
- Year 2022-09-30: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2021-09-30: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2020-09-30: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2019-09-30: Incomplete data (missing: revenue, net_income, eps, total_equity)
- TTM Analysis: Periodic data not available from API
- Quick Ratio: Inventory data unavailable - using Current Assets (Technology sector)

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

---