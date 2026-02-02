# STOCK ANALYSIS DOSSIER: YU.LSE
# DATE: 2026-02-02
# SOURCE: EODHD (Tier 1 Data)
# CEO: Mr. Baljit Bobby Kalar
# SECTOR: Utilities | INDUSTRY: Utilities - Diversified
# EMPLOYEES: 472
# MOST RECENT ANNUAL DATA: 2024
# CURRENCY: All values in GBP (stock trades in GBX)

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
- Graham Number (Single-Year EPS): 12.54 GBP
- Graham Number (3-Year Avg EPS): 10.01 GBP
  - ⚠️ Note: 3-year average (20% lower) reveals earnings peaked in recent year
- Intrinsic Value (EPV): 60,924,571.00 GBP
- Net-Net Value: 2.14 GBP
- Margin of Safety: -413.3% (Capped by EPV)
  - Conservative Intrinsic Value: 3.39 GBP
- Current Price: 17.40 GBP (1,740 pence)
- 52-Week Range: 12.35 GBP - 17.84 GBP
- Trailing Dividend: 0.56 GBP (Yield: 3.22%) - Declared (Dividend API) [2024]
  - Forward Rate: 0.63 GBP (Yield: 3.62%)
- P/E Ratio (Current Year): 9.33
- P/E Ratio (3-Year Avg): 13.69 (based on avg EPS of 1.27 from 2022-2024)
- Price/Book: 4.45

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 47.64%
- Return on Assets (ROA): 15.62%
- Profit Margin: 5.19%
- Book Value Per Share: 3.91 GBP

### Liquidity Analysis

- Insider Ownership: 64.81%
- Institutional Ownership: 13.93%
- Beta (Volatility): 0.668

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:
- **Beta: 0.668** - Below-market volatility

### Financial Strength Risk:
- **Current Ratio: 1.34x** - ⚠️ Below Graham's standards (defensive requires 2.0x)
- **Long-Term Debt: $4,745,000 GBP** (2.2% of assets) - Conservative
  - Short-term debt: $1,116,000 GBP
  - Total debt: $5,861,000 GBP (2.7% of assets)
- **Debt Coverage: ✓** Long-term debt < Net Current Assets (passes Graham's defensive test)

### Operational Stability Risk:
- **Profit Margin Stability: -0.1% average, 5.6% std dev** over 9 years
  - Moderate volatility
- **Loss Years: 4 of 10** - ⚠️ Earnings not consistently positive
- **Return on Equity: 47.6%** - Strong capital efficiency

### Dividend Sustainability Risk:
- **Payout Ratio: 33.8%** - Conservative (sustainable)
- **Dividend History: 6 of 10 years** - ⚠️ Inconsistent payment history

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -413.3%** - Trading above intrinsic value
  - Graham's Standard: 20-30% minimum for defensive investors
  - Assessment: **High valuation risk** - no margin for error
  - Intrinsic Value (Graham): 12.54 GBP
  - Current Price: 17.40 GBP

### Data Quality Risk:
- **Institutional Ownership: 13.93%** - Verify with regulatory filings
- **Price Source: yfinance** - ⚠️ Using fallback source (EODHD unavailable)

**Graham's Principle on Risk**: *"The essence of investment management is the management of risks, not the management of returns. Returns are the reward for taking risk, but the risk must be measured and managed."*

---

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **P/E Ratio (9.33)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 1.86 GBP (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (12.54 GBP)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Based on Benjamin Graham's formula from 'The Intelligent Investor'
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 10.01 GBP
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This aligns with Graham's actual criterion: *"Price should not exceed"*
  *"15 times average earnings of the past three years."*

  **3-Year EPS**: [2025: 0.00 GBP, 2024: 1.86 GBP, 2023: 1.70 GBP] → Avg: 1.19 GBP
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Inspired by Graham's emphasis on full-cycle earnings

  **Important**: This is a simplified approach, not Graham's original methodology.
  Graham emphasized earnings power conceptually but didn't prescribe this exact formula.

  **Calculation for YU:**
  - Years Used: 10
  - Years: 2015-2024
  - Net Incomes: GBP33,499,000, GBP30,860,000, GBP4,769,000, GBP4,451,000, -GBP1,165,000, -GBP4,968,000, -GBP6,267,000, GBP1,804,000, -GBP1,359,000, -GBP699,429
  - Normalized Earnings: GBP6,092,457 (average including losses)
  - EPV: GBP60,924,571 (GBP6,092,457 / 10%)
  - EPV Per Share: 3.39 GBP

  **Note**: The 10-year average includes 5 loss years (2020, 2019, 2018, 2016, 2015), reflecting the company's full business cycle performance per Graham's methodology.

  **Graham's Principle**: *"The concept of 'earning power' implies a fairly confident expectation of certain future results, based on past performance under varying conditions. The record must cover a number of years, first because a continued or repeated performance is always more impressive than a single occurrence and secondly because the average of a fairly long period will tend to absorb and equalize the distorting influences of the business cycle."*
- **Net-Net Value (2.14 GBP)**: (Current Assets - Total Liabilities) / Shares
  - Conservative liquidation value estimate
  - Graham's 'cigar butt' valuation for distressed situations

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -413.3%
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
  - Normalized Graham Number: 10.01 GBP
  - EPV per share: 3.39 GBP
  - **Intrinsic Value Used**: 3.39 GBP (Capped by EPV)

  **Interpretation**: EPV is lower than Normalized Graham Number, indicating
  that long-term earnings power is weaker than asset-based valuation suggests.
  This is a red flag - the company may be destroying value over the full cycle.

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
- **Shares Outstanding**: 17,970,900 shares
- **Source**: Financial statements (outstandingShares.annual for 2024)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: GBP70,324,000
- **Less: Intangible Assets**: GBP2,777,000
- **Less: Goodwill**: GBP216,000
- **Tangible Book Value**: GBP67,331,000
- **Divided by Shares**: 17,970,900
- **Tangible Book Value Per Share (TBVPS)**: GBP3.75
- **Book Value Per Share (BVPS)**: GBP3.91 (without subtracting intangibles)
- **API Book Value**: GBP4.82 (18.8% difference)
  - **Explanation**: Differences may be due to:
    - Different share count (API may use basic vs. diluted)
    - Different accounting treatment of intangibles
    - Timing differences (API may use more recent data)
    - Our calculation uses audited financial statement data per Graham methodology

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: GBP1.86
- **TBVPS**: GBP3.75
- **Calculation**: √(22.5 × 1.86 × 3.75) = √(157.14)
- **Graham Number**: GBP12.54
- **Note**: Uses unrounded intermediate values for precision

### Net-Net Value Calculation:
- **Current Assets**: GBP182,688,000
- **Total Liabilities**: GBP144,147,000
- **Net Current Assets**: GBP38,541,000
- **Divided by Shares**: 17,970,900
- **Net-Net Value Per Share**: GBP2.14
- **Formula Used**: NCAV (Net Current Asset Value) = (Current Assets - Total Liabilities) / Shares
  - **Note**: This is the standard 'Net-Net' formula used by most value investors
  - **Alternative**: Graham's more conservative NNWC formula applies haircuts to current assets
    - NNWC = (Cash + 0.75×AR + 0.5×Inventory - Total Liabilities) / Shares
    - We use NCAV for consistency with common practice

### Currency Conversion Details:
- **Stock Trading Currency**: GBX (pence)
- **Financial Statements Currency**: GBP
- **London Fix Applied**: Yes (GBX → GBP conversion)
  - LSE stocks trade in pence (GBX) but financials are in pounds (GBP)
  - Price divided by 100 when P/E ratio > 500 (indicates pence vs pounds mismatch)
  - Example: 1,650 GBX = 16.50 GBP
- **Why Currency Unification Matters**:
  - Ensures all per-share calculations use the same currency
  - Prevents mixing GBX prices with GBP financials (100x error)
  - Allows accurate comparison of price to intrinsic value

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

1. **Earnings Stability**: FAIL
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio ≥ 2.0
3. **Debt to Assets**: PASS
   - Criterion: Long-term Debt < Net Current Assets
4. **Dividend Record**: FAIL
   - Criterion: Uninterrupted dividend payments for at least 20 years
5. **Earnings Growth**: FAIL
   - Criterion: Earnings growth ≥ 33% over 10 years
6. **P/E Ratio**: PASS
   - Criterion: P/E Ratio < 15
7. **P/B Ratio**: FAIL
   - Criterion: Price/Book Ratio < 1.5
8. **Combined P/E × P/B Test**: FAIL
   - P/E Ratio: 9.33
   - P/B Ratio: 4.45
   - Product: 41.52 (must be ≤ 22.5)
   - *Graham specified that P/E × P/B should not exceed 22.5. This provides flexibility: a company can have a higher P/E if it has a low P/B, or vice versa.*

---

## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS

1. **Earnings Stability**: FAIL
   - Criterion: Profitability in most recent year and 5 of past 7 years
2. **Current Ratio**: FAIL
   - Criterion: Current Ratio > 1.5
3. **Debt to Assets**: PASS
   - Criterion: Debt < 110% of Net Current Assets
4. **Dividend Record**: PASS
   - Criterion: Currently pays a dividend (last year > 0)
5. **Earnings Growth**: N/A - Not Required
6. **Price Test**: PASS
   - Criterion: P/E < 10 OR Price < 120% of Net Tangible Assets

**Note on Earnings Growth:** Earnings growth is intentionally not required for Enterprising Investors per Graham's methodology. Unlike Defensive Investors (who require 7 tests including ≥33% earnings growth over 10 years), Enterprising Investors require only 6 tests focused on current financial strength and price. Graham's logic: Enterprising investors actively seek bargains, turnarounds, or cyclical companies trading below intrinsic value—situations where historical growth may be absent but current fundamentals and price create opportunity.

---

## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)
*All values in GBP*

| Year | Revenue | Net Income | EPS | Div/Share | BVPS | WCPS | Payout Ratio | Total Debt | Shares (B) | Price | P/E | P/B |
|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|
| 2025 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 0.63 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2024 | 645456000.0 | 33499000.0 | 1.8640691339888376 | 0.56 | 3.91 | 2.57 | 30.0% | 5.86M | 17.97M | N/A | N/A | N/A |
| 2023 | 460001000.0 | 30860000.0 | 1.6992082108207518 | 0.06 | 2.58 | 1.78 | 3.5% | 0.71M | 18.16M | N/A | N/A | N/A |
| 2022 | 278587000.0 | 4769000.0 | 0.2484734176687577 | N/A | 0.77 | 0.07 | 0.0% | 0.11M | 19.19M | N/A | N/A | N/A |
| 2021 | 155423000.0 | 4451000.0 | 0.2585761175821303 | N/A | 0.54 | ⚠️ -0.13 | 0.0% | 0.11M | 17.21M | N/A | N/A | N/A |
| 2020 | 101527000.0 | -1165000.0 | -0.06422023405932516 | N/A | 0.25 | ⚠️ -0.08 | N/A | 0.10M | 18.14M | N/A | N/A | N/A |
| 2019 | 111613000.0 | -4968000.0 | -0.3051390876537826 | 0.012 | 0.33 | 0.01 | N/A | 0.15M | 16.28M | N/A | N/A | N/A |
| 2018 | 80635000.0 | -6267000.0 | -0.4354563015050237 | 0.03 | 0.73 | 0.46 | N/A | N/A | 14.39M | N/A | N/A | N/A |
| 2017 | 45631000.0 | 1804000.0 | 0.11976524948880686 | 0.0225 | 0.42 | 0.30 | 18.8% | N/A | 15.06M | N/A | N/A | N/A |
| 2016 | 16264000.0 | -1359000.0 | -0.09647945818158585 | N/A | 0.38 | 0.34 | N/A | N/A | 14.09M | N/A | N/A | N/A |
| 2015 | 3325715.0 | -699429.0 | -0.0699429 | N/A | N/A | ⚠️ -0.14 | N/A | 0.25M | 10.00M | N/A | N/A | N/A |
| 2014 | 495692.0 | -132000.0 | -0.0078596284646448 | N/A | N/A | ⚠️ -0.03 | N/A | 0.25M | 12.03M | N/A | N/A | N/A |
| 2013 | 12923.0 | -24923.0 | -0.0017733615101642936 | N/A | N/A | -0.00 | N/A | 0.06M | 14.05M | N/A | N/A | N/A |

**Note on Data Completeness:**
- Years marked '[Data Unavailable]' (2025) show declared dividends but lack complete audited annual financial statements
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
- Currency Conversions: London Fix applied (GBp → GBP)
- [VALIDATION] Share Count: Using 18,360,000 shares from financial statements. Market data (SharesStats) shows 16,794,687 shares (9.3% difference). Financial statement shares are used for accurate per-share calculations per Graham methodology.
- [VALIDATION] Book Value Discrepancy: API shows $4.82, calculated $3.91 (18.8% difference). Calculated value subtracts intangibles/goodwill per Graham methodology. API may use different share count or accounting treatment.
- [VALIDATION] ROA Difference: API shows 12.50% (TTM basis), calculated 15.62% (annual basis) (25.0% difference). Using annual data from audited financials per Graham methodology.
- Year 2025-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Quick Ratio: Cannot calculate - inventory data unavailable for Utilities sector

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

---