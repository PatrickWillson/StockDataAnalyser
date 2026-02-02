# STOCK ANALYSIS DOSSIER: AAPL.US
# DATE: 2026-02-02
# SOURCE: EODHD (Tier 1 Data)
# CEO: Mr. Timothy D. Cook
# SECTOR: Technology | INDUSTRY: Consumer Electronics
# EMPLOYEES: 150,000
# MOST RECENT ANNUAL DATA: 2025
# CURRENCY: USD

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
- Graham Number (Single-Year EPS): 29.11 USD
- Graham Number (3-Year Avg EPS): 22.66 USD
  - ⚠️ Note: 3-year average (22% lower) reveals earnings peaked in recent year
- Intrinsic Value (EPV): 763,460,000,000.00 USD
- Net-Net Value: -9.29 USD
- Margin of Safety: -1089.3% (Capped by Normalized Graham Number)
  - Conservative Intrinsic Value: 22.66 USD
- Current Price: 269.50 USD
- 52-Week Range: 168.63 USD - 288.62 USD
- Trailing Dividend: 1.03 USD (Yield: 0.38%) - Declared (Dividend API) [2025]
  - Forward Rate: 1.04 USD (Yield: 0.39%)
- P/E Ratio (Current Year): 35.63
- P/E Ratio (3-Year Avg): 40.47 (based on avg EPS of 6.66 from 2023-2025)
- Price/Book: 54.13

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 151.91%
- Return on Assets (ROA): 31.18%
- Profit Margin: 26.92%
- Book Value Per Share: 4.98 USD

### Liquidity Analysis

- Insider Ownership: 1.70%
- Institutional Ownership: 64.93%
- Beta (Volatility): 1.093

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:
- **Beta: 1.093** - Above-market volatility

### Financial Strength Risk:
- **Current Ratio: 0.89x** - ⚠️ Critical liquidity risk
- **Long-Term Debt: $78,328,000,000 USD** (21.8% of assets) - Moderate
  - Short-term debt: $22,446,000,000 USD
  - Total debt: $100,774,000,000 USD (28.1% of assets)

### Operational Stability Risk:
- **Profit Margin Stability: 23.7% average, 2.3% std dev** over 9 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 151.9%** - Strong capital efficiency

### Dividend Sustainability Risk:
- **Payout Ratio: 13.8%** - Conservative (sustainable)
- **Dividend History: 10 consecutive years** - Uninterrupted record (excellent)

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -1089.3%** - Trading above intrinsic value
  - Graham's Standard: 20-30% minimum for defensive investors
  - Assessment: **High valuation risk** - no margin for error
  - Intrinsic Value (Graham): 29.11 USD
  - Current Price: 269.50 USD

### Data Quality Risk:
- **Institutional Ownership: 64.93%** - Verify with regulatory filings
- **Price Source: yfinance** - ⚠️ Using fallback source (EODHD unavailable)

**Graham's Principle on Risk**: *"The essence of investment management is the management of risks, not the management of returns. Returns are the reward for taking risk, but the risk must be measured and managed."*

---

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **P/E Ratio (35.63)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 7.56 USD (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (29.11 USD)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Based on Benjamin Graham's formula from 'The Intelligent Investor'
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 22.66 USD
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This aligns with Graham's actual criterion: *"Price should not exceed"*
  *"15 times average earnings of the past three years."*

  **3-Year EPS**: [2026: 0.00 USD, 2025: 7.56 USD, 2024: 6.19 USD] → Avg: 4.58 USD
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
  - Years: 2016-2025
  - Net Incomes: USD112,010,000,000, USD93,736,000,000, USD96,995,000,000, USD99,803,000,000, USD94,680,000,000, USD57,411,000,000, USD55,256,000,000, USD59,531,000,000, USD48,351,000,000, USD45,687,000,000
  - Normalized Earnings: USD76,346,000,000 (average including losses)
  - EPV: USD763,460,000,000 (USD76,346,000,000 / 10%)
  - EPV Per Share: 51.55 USD

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham's Principle**: *"The concept of 'earning power' implies a fairly confident expectation of certain future results, based on past performance under varying conditions. The record must cover a number of years, first because a continued or repeated performance is always more impressive than a single occurrence and secondly because the average of a fairly long period will tend to absorb and equalize the distorting influences of the business cycle."*

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -1089.3%
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
  - Normalized Graham Number: 22.66 USD
  - EPV per share: 51.55 USD
  - **Intrinsic Value Used**: 22.66 USD (Capped by Normalized Graham Number)

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
- **Shares Outstanding**: 14,810,356,000 shares
- **Source**: Financial statements (outstandingShares.annual for 2025)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: USD73,733,000,000
- **Less: Intangible Assets**: USD0
- **Less: Goodwill**: USD0
- **Tangible Book Value**: USD73,733,000,000
- **Divided by Shares**: 14,810,356,000
- **Tangible Book Value Per Share (TBVPS)**: USD4.98
- **Book Value Per Share (BVPS)**: USD4.98 (without subtracting intangibles)
- **API Book Value**: USD6.00 (17.0% difference)
  - **Explanation**: Differences may be due to:
    - Different share count (API may use basic vs. diluted)
    - Different accounting treatment of intangibles
    - Timing differences (API may use more recent data)
    - Our calculation uses audited financial statement data per Graham methodology

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: USD7.56
- **TBVPS**: USD4.98
- **Calculation**: √(22.5 × 7.56 × 4.98) = √(847.17)
- **Graham Number**: USD29.11
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
   - P/E Ratio: 35.63
   - P/B Ratio: 54.13
   - Product: 1928.65 (must be ≤ 22.5)
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

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares (B) | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2026 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.26 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2025 | 416161000000.0 | 112010000000.0 | 7.562951221429113 | 1.03 | 4.98 | ⚠️ -1.19 | 13.6% | 100.77B | 14.810B | N/A | N/A | N/A |
| 2024 | 391035000000.0 | 93736000000.0 | 6.1868414773677936 | 0.99 | 3.76 | ⚠️ -1.54 | 16.0% | 108.26B | 15.151B | N/A | N/A | N/A |
| 2023 | 383285000000.0 | 96995000000.0 | 6.226952267822055 | 0.95 | 3.99 | ⚠️ -0.11 | 15.3% | 111.09B | 15.577B | N/A | N/A | N/A |
| 2022 | 394328000000.0 | 99803000000.0 | 6.254998991584083 | 0.91 | 3.18 | ⚠️ -1.16 | 14.5% | 120.07B | 15.956B | N/A | N/A | N/A |
| 2021 | 365817000000.0 | 94680000000.0 | 5.731480848663541 | 0.865 | 3.82 | 0.57 | 15.1% | 124.72B | 16.519B | N/A | N/A | N/A |
| 2020 | 274515000000.0 | 57411000000.0 | 3.3546831051261425 | 0.8074999999999999 | 3.82 | 2.24 | 24.1% | 112.44B | 17.114B | N/A | N/A | N/A |
| 2019 | 260174000000.0 | 55256000000.0 | 3.1010612840108793 | 0.76 | 5.08 | 3.20 | 24.5% | 108.05B | 17.818B | N/A | N/A | N/A |
| 2018 | 265595000000.0 | 59531000000.0 | 3.1179476801141024 | 0.705 | 5.61 | 0.76 | 22.6% | 114.48B | 19.093B | N/A | N/A | N/A |
| 2017 | 229234000000.0 | 48351000000.0 | 2.3435923197293724 | 0.615 | 6.5 | 1.35 | 26.2% | 115.68B | 20.631B | N/A | N/A | N/A |
| 2016 | 215639000000.0 | 45687000000.0 | 2.143723858599717 | 0.5574999999999999 | 6.02 | 1.31 | 26.0% | 87.03B | 21.312B | N/A | N/A | N/A |
| 2015 | 233715000000.0 | 53394000000.0 | 2.3861632029448026 | 0.5075000000000001 | 5.33 | 0.39 | 21.3% | 64.46B | 22.377B | N/A | N/A | N/A |
| 2014 | 182795000000.0 | 39510000000.0 | 1.67933200074875 | 0.46142999999999995 | 4.74 | 0.22 | 27.5% | 35.30B | 23.527B | N/A | N/A | N/A |
| 2013 | 170910000000.0 | 37037000000.0 | 1.4673548896668929 | 0.42142999999999997 | 4.89 | 1.17 | 28.7% | 24.64B | 25.241B | N/A | N/A | N/A |
| 2012 | 156508000000.0 | 41733000000.0 | 1.5735193579869087 | 0.18924000000000002 | 4.46 | 0.72 | 12.0% | 6.31B | 26.522B | N/A | N/A | N/A |
| 2011 | 108249000000.0 | 25922000000.0 | 0.98323411729078 | N/A | 2.91 | 0.65 | 0.0% | 5.61B | 26.364B | N/A | N/A | N/A |
| 2010 | 65225000000.0 | 14013000000.0 | 0.536314783748755 | N/A | 1.83 | 0.80 | 0.0% | 2.47B | 26.128B | N/A | N/A | N/A |
| 2009 | 42905000000.0 | 8235000000.0 | 0.31975709798631075 | N/A | 1.08 | 0.66 | 0.0% | 1.95B | 25.754B | N/A | N/A | N/A |
| 2008 | 32479000000.0 | 4834000000.0 | 0.1915074943847182 | N/A | 0.83 | 0.82 | 0.0% | 2.51B | 25.242B | N/A | N/A | N/A |
| 2007 | 24006000000.0 | 3495000000.0 | 0.1386821552611605 | N/A | 0.58 | 0.50 | 0.0% | 1.80B | 25.202B | N/A | N/A | N/A |

**Note on Data Completeness:**
- Years marked '[Data Unavailable]' (2026) show declared dividends but lack complete audited annual financial statements
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
- **Total Debt**: Sum of long-term and short-term debt. Graham emphasized tracking debt trends to distinguish companies that grow through retained earnings vs leverage.
- **Shares (B)**: Common shares outstanding in billions. Tracks shareholder dilution (increasing shares) or buyback programs (decreasing shares).
- **Price**: Year-end stock price on fiscal year end date (or last trading day within 7 days prior). Source: Yahoo Finance via yfinance.
- **P/E**: Historical Price-to-Earnings ratio (Price ÷ EPS). Shows how the market valued earnings power over time. 'Negative' indicates loss year (Graham's method: show losses explicitly).
- **P/B**: Historical Price-to-Book ratio (Price ÷ BVPS). Shows how the market valued net assets over time.

*Note: Historical prices converted to unified currency using current FX rates. Historical FX rates not used - actual historical valuations may differ due to FX fluctuations.*

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Price Source: yfinance (primary source)
- [VALIDATION] Book Value Discrepancy: API shows $6.00, calculated $4.98 (17.0% difference). Calculated value subtracts intangibles/goodwill per Graham methodology. API may use different share count or accounting treatment.
- [VALIDATION] ROA Difference: API shows 24.38% (TTM basis), calculated 31.18% (annual basis) (27.9% difference). Using annual data from audited financials per Graham methodology.
- Year 2026-09-30: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Quick Ratio: Inventory data unavailable - using Current Assets (Technology sector)

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

### Statistical Anomalies (Z-Score Analysis):
*Metrics that deviate significantly from historical patterns*

- Year 2005-09-30: EPS growth Z-Score = 3.31 (Outlier)
- Year 1996-09-30: EPS growth Z-Score = -3.17 (Outlier)

---