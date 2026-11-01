# STOCK ANALYSIS DOSSIER: SO.US
# DATE: 2026-11-01
# SOURCE: SEC EDGAR + Yahoo Finance (Tier 1 Data)
# CEO: Test CEO One
# SECTOR: Utilities | INDUSTRY: Utilities - Regulated Electric
# EMPLOYEES: 28,000
# MOST RECENT ANNUAL DATA: 2025
# CURRENCY: USD

---

## SECTION 1: EXECUTIVE SUMMARY
*Current metrics (P/E, Price) reflect most recent available data*

- Verdict: **OVERVALUED**
  - Price is not below conservative intrinsic value (margin of safety -207.7%)
- Graham Number (Single-Year EPS): 49.19 USD
- Graham Number (3-Year Avg EPS): 48.73 USD
- Intrinsic Value (EPV per share): 28.60 USD (10-year average earnings)
- Net-Net Value: -97.18 USD
- Margin of Safety: -207.7% (Capped by EPV)
  - Conservative Intrinsic Value: 28.60 USD
- Current Price: 88.00 USD
- Trailing Dividend: 2.68 USD (Yield: 3.05%) - Declared (Dividend API) [2025]
  - Forward Rate: 2.96 USD (Yield: 3.36%)
- P/E Ratio (Current Year): 22.34
- P/E Ratio (3-Year Avg): 22.76 (based on avg EPS of 3.87 from 2023-2025)
- Price/Book: 2.74

---

## SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS
*TTM calculations provide more current metrics using the most recent 12 months of periodic data*

- Reporting Frequency: Quarterly
- Period Covered: Q2 2025 through Q1 2026

- TTM Graham Number: 51.60 USD (Annual: 49.19 USD, Diff: +4.9%)
- TTM Tangible Book Value Per Share: 30.57 USD (Annual: 27.30 USD, Diff: +12.0%)
- TTM Net-Net Value: -95.06 USD (Annual: -97.18 USD, Diff: +2.2%)
- TTM Margin of Safety: -70.5% (vs the TTM Graham Number; the annual margin of safety uses the lower of the normalized Graham Number and EPV)
- TTM P/E Ratio: 22.74 (Annual: 22.34, Diff: +1.8%)
- TTM P/B Ratio: 2.49 (Annual: 2.74, Diff: -9.0%)

- TTM Dividend (Last 12 Months): 2.74 USD (Yield: 3.12%)
  - Based on 4 payment(s):
    - 2026-08-15: 0.6908 USD
    - 2026-05-15: 0.6908 USD
    - 2026-02-15: 0.6908 USD
    - 2025-11-15: 0.6706 USD
  - FY2025 Dividend: 2.68 USD (Yield: 3.05%, Diff: +2.3%)

---

## SECTION 2: KEY METRICS
- Return on Equity (ROE): 12.05%
- Return on Assets (ROA): 2.79%
- Profit Margin: 14.69%
- Book Value Per Share: 32.17 USD

### Liquidity Analysis

- **Current Ratio**: 0.65 (Current Assets / Current Liabilities, fiscal year ending 2025-12-31)
- **Quick Ratio**: 0.45 (Acid Test - excludes inventory)

### Net Current Assets (Working Capital) and Debt

- **Current Assets**: 10,917,000,000.00 USD
- **Current Liabilities**: 16,888,000,000.00 USD
- **Net Current Assets**: -5,971,000,000.00 USD
- **Long-term Debt**: 65,649,000,000.00 USD
- **Debt Coverage Ratio**: N/A
- Institutional Ownership: 68.00%
- Beta (Volatility): 0.450

---

## SECTION 3: CRITICAL ALERTS

### Data Quality & Limitations:
- Dividends per year bucketed by ex-dividend date (Yahoo Finance has no payment dates)
- Statements as filed with the SEC; latest 10-K/10-Q filed 2026-07-30
- SEC EDGAR: inventory: derived as the sum of EnergyRelatedInventoryNaturalGasInStorage, EnergyRelatedInventoryOtherFossilFuel, OtherInventorySupplies (FY2015, FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025)
- SEC EDGAR: year-end shares: cover-page count of the filing (dated after the period end); issued and treasury counts are tagged rounded to millions (FY2012, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025)
- SEC EDGAR: year-end shares: derived as shares issued - treasury shares (FY2008, FY2009, FY2010, FY2011, FY2013, FY2014, FY2015, FY2016, FY2017)
- SEC EDGAR: inventory: derived as the sum of EnergyRelatedInventoryOtherFossilFuel, OtherInventorySupplies (FY2008, FY2009, FY2010, FY2011, FY2012, FY2013, FY2014)
- SEC EDGAR: stockholders' equity: derived as equity incl. minority interest - minority interest (FY2008, FY2009, FY2010, FY2011)
- SEC EDGAR: restated in later filings, latest figure used (first reported -> latest): FY2014 total assets 70,923M -> 70,233M; FY2014 liabilities and equity 70,923M -> 70,233M; FY2014 total liabilities 49,583M -> 48,893M; FY2014 long-term debt 20,841M -> 20,644M; FY2014 short-term debt 3,333M -> 3,329M; FY2014 current assets 6,370M -> 5,864M; FY2013 total assets 64,546M -> 64,264M; FY2013 current assets 5,599M -> 5,614M; FY2013 current liabilities 5,536M -> 5,525M
- SEC EDGAR: fourth quarter: derived as the fiscal year minus the first nine months (FY2024, FY2025)
- Price Source: yfinance (primary source)
- Year 2026-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2007-12-31: Incomplete data (missing: total_equity)
- Year 2006-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2005-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2004-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Year 2003-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)
- Potentially Stale Data: Most recent annual report is from 2025-12-31 (10 months old)
- Historical prices unavailable for 5 fiscal year ends (no trading data within 7-day window). Historical P/E and P/B will show N/A for those years.

### Normalized Graham Number Requirements:
- **3-Year Data Requirement**: Normalized Graham Number calculation requires 3 consecutive years of annual EPS data
- **Fallback Strategy**: When insufficient data is available, the system falls back to EPV (Earnings Power Value) for Margin of Safety calculation
- **Staleness Detection**: Annual reports older than 9 months trigger a data staleness warning
- **Data Quality**: All 3 years must have non-null, numeric EPS values for normalized calculation to proceed

### Statistical Anomalies (EPS growth, modified Z-Score > 3.5):
*Metrics that deviate significantly from historical patterns*

- Year 2019-12-31: EPS growth modified Z-Score = 6.28 (Outlier: +107.8% vs median +6.7%)
- Year 2018-12-31: EPS growth modified Z-Score = 9.49 (Outlier: +159.5% vs median +6.7%)
- Year 2017-12-31: EPS growth modified Z-Score = -4.60 (Outlier: -67.3% vs median +6.7%)

---

## RISK FACTORS
*Quantifiable risks based on Graham's investment criteria*

### Market & Liquidity Risk:
- **Beta: 0.450** - Low volatility relative to market
  - Note: Beta varies by calculation period and benchmark. Market sources report 0.33-0.50 range.
  - Low beta may reflect limited liquidity and defensive sector characteristics

### Financial Strength Risk:
- **Current Ratio: 0.65x** - ⚠️ Critical liquidity risk
- **Long-Term Debt: 65,649,000,000 USD** (42.2% of assets) - ⚠️ High leverage
  - Short-term debt and leases: 6,942,000,000 USD
  - Total debt: 72,591,000,000 USD (46.6% of assets)

### Operational Stability Risk:
- **Profit Margin Stability: 13.2% average, 4.9% std dev** over 10 years
  - Low volatility indicates stable operations
- **Loss Years: 0 of 10** - Consistent profitability (excellent)
- **Return on Equity: 12.1%** - Adequate returns

### Dividend Sustainability Risk:
- **Payout Ratio: 68.1%** - Moderate
- **Dividend History: 10 consecutive years** - Uninterrupted record (excellent)

### Valuation Risk (Margin of Safety):
- **Margin of Safety: -207.7%** - Trading above conservative intrinsic value
  - Assessment: **High valuation risk** - no margin of safety
  - Conservative Intrinsic Value: 28.60 USD
  - Current Price: 88.00 USD

### Data Quality Risk:
- **Institutional Ownership: 68.00%** - Verify with regulatory filings
- **Price Source: yfinance** (current quote; the only price source)


---

## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS

1. **Earnings Stability**: PASS
   - Criterion: Positive earnings in each of the past 10 years
2. **Current Ratio**: NOT APPLICABLE (public utility)
   - Criterion: Not applied to public utilities (Graham)
3. **Debt to Assets**: FAIL
   - Criterion (public utility): Total debt ≤ 2 × stockholders' equity at book value
4. **Dividend Record**: PASS
   - Criterion: Uninterrupted dividend payments for at least 20 years
5. **Earnings Growth**: PASS
   - Criterion: Average EPS of the latest 3 reported years at least one-third (33.3%) above the average of the reported years 9-11 back
6. **P/E Ratio**: FAIL
   - Criterion: Price ≤ 15 × average EPS of the last 3 reported years
7. **P/B Ratio**: FAIL
   - Criterion: Price ≤ 1.5 × tangible book value per share, or P/E (3-year average EPS) × P/B ≤ 22.5
8. **Combined P/E × P/B Test** (criterion 7 alternative): FAIL
   - P/E Ratio (3-year average EPS): 22.76
   - P/B Ratio (tangible book): 3.22
   - Product: 73.37 (must be ≤ 22.5)
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
| 2026 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | 2.07 | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] | [Data Unavailable] |
| 2025 | 29.55B | 4.34B | 3.94 | 2.68 | 32.17 | ⚠️ -5.33 | 68.1% | 72.59B | 1.119B | 85.47 | 21.7 | 2.7 |
| 2024 | 26.72B | 4.40B | 4.02 | 2.60 | 30.28 | ⚠️ -4.83 | 64.8% | 64.82B | 1.097B | 82.95 | 20.6 | 2.7 |
| 2023 | 25.25B | 3.98B | 3.64 | 2.53 | 28.82 | ⚠️ -2.78 | 69.5% | 62.00B | 1.091B | 80.42 | 22.1 | 2.8 |
| 2022 | 29.28B | 3.52B | 3.28 | 2.45 | 27.93 | ⚠️ -4.87 | 74.8% | 57.55B | 1.089B | 77.89 | 23.7 | 2.8 |
| 2021 | 23.11B | 2.39B | 2.26 | 2.38 | 26.29 | ⚠️ -1.84 | 105.5% | 53.72B | 1.060B | 75.37 | 33.3 | 2.9 |
| 2020 | 20.38B | 3.12B | 2.95 | 2.31 | 26.47 | ⚠️ -3.28 | 78.4% | 49.19B | 1.057B | 72.84 | 24.7 | 2.8 |
| 2019 | 21.42B | 4.74B | 4.53 | 2.25 | 26.09 | ⚠️ -2.59 | 49.6% | 46.84B | 1.054B | 70.32 | 15.5 | 2.7 |
| 2018 | 23.50B | 2.23B | 2.18 | 2.18 | 23.90 | ⚠️ -4.55 | 100.1% | 46.85B | 1.035B | 67.79 | 31.1 | 2.8 |
| 2017 | 23.03B | 842.00M | 0.84 | 2.12 | 24.19 | ⚠️ -3.53 | 252.1% | 50.79B | 999.10M | 65.26 | 77.7 | 2.7 |
| 2016 | 19.90B | 2.45B | 2.57 | 2.06 | 25.00 | ⚠️ -3.23 | 80.0% | 47.46B | 990.20M | 62.74 | 24.4 | 2.5 |
| 2015 | 17.49B | 2.37B | 2.60 | 2.00 | 22.59 | ⚠️ -2.86 | 76.8% | 28.74B | 911.60M | 60.21 | 23.2 | 2.7 |
| 2014 | 18.47B | 1.96B | 2.19 | 1.94 | 21.96 | ⚠️ -3.41 | 88.5% | 24.78B | 908.30M | 57.68 | 26.3 | 2.6 |
| 2013 | 17.09B | 1.64B | 1.88 | 1.88 | 21.42 | 0.10 | 100.1% | 23.30B | 887.30M | 55.16 | 29.3 | 2.6 |
| 2012 | 16.54B | 2.35B | 2.70 | 1.83 | 21.06 | ⚠️ -0.98 | 67.7% | 22.43B | 868.97M | 52.63 | 19.5 | 2.5 |
| 2011 | 17.66B | 2.20B | 2.57 | 1.77 | 20.31 | ⚠️ -0.35 | 69.0% | 21.22B | 865.50M | 50.11 | 19.5 | 2.5 |
| 2010 | 17.46B | 1.98B | 2.37 | 1.72 | 19.21 | ⚠️ -0.70 | 72.7% | 20.75B | 843.50M | 47.58 | 20.1 | 2.5 |
| 2009 | 15.74B | 1.64B | 2.07 | 1.67 | 18.15 | 0.35 | 80.8% | 19.88B | 819.50M | 45.05 | 21.8 | 2.5 |
| 2008 | 17.13B | 1.74B | 2.26 | 1.62 | 17.07 | 0.17 | 71.8% | 18.39B | 777.60M | 42.53 | 18.8 | 2.5 |
| 2007 | 15.35B | 1.73B | 2.29 | 1.58 | N/A | 0.00 | 68.8% | N/A | 1.119B | 40.00 | 17.5 | N/A |

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
- **Total Debt**: Reported total debt (short- and long-term, including lease obligations), else the sum of long- and short-term debt.
- **Shares**: Common shares outstanding (B = billions, M = millions). Tracks shareholder dilution (increasing shares) or buyback programs (decreasing shares).
- **Price**: Year-end stock price on fiscal year end date (or last trading day within 7 days prior). Source: Yahoo Finance via yfinance.
- **P/E**: Historical Price-to-Earnings ratio (Price ÷ EPS). Shows how the market valued earnings power over time. 'Negative' indicates a loss year.
- **P/B**: Historical Price-to-Book ratio (Price ÷ BVPS). Shows how the market valued net assets over time.

*Note: Historical prices converted to unified currency using current FX rates. Historical FX rates not used - actual historical valuations may differ due to FX fluctuations.*

## METHODOLOGY NOTES
*How key metrics are calculated*

### Valuation Metrics:
- **P/E Ratio (22.34)**: Current Price / Most Recent Annual EPS
  - Calculated from audited financials, not API pre-calculated ratios
  - EPS: 3.94 USD (Net Income / Shares Outstanding)
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
- **Graham Number - Single-Year EPS (49.19 USD)**: √(22.5 × EPS × TBVPS)
  - Conservative intrinsic value estimate
  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ 15) and 7 (P/B ≤ 1.5), as 15 × 1.5 = 22.5
  - Uses most recent annual EPS

- **Graham Number - 3-Year Average EPS (Normalized)**:
  - **Value**: 48.73 USD
  - **Formula**: √(22.5 × EPS_3yr_avg × TBVPS)

  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year
  makes a cyclical company appear undervalued despite being a value destroyer over the
  full business cycle. This follows Graham's sixth defensive criterion: price not more than
  15 times average earnings of the past three years.

  **3-Year EPS**: [2025: 3.94 USD, 2024: 4.02 USD, 2023: 3.64 USD] → Avg: 3.87 USD
- **EPV - Simplified Earnings Power Estimate**

  **Methodology:**
  - Uses 7-10 year average of net income
  - **Includes ALL years** (profitable and unprofitable)
  - Loss years reduce the average (real value destruction)
  - Capitalizes earnings at 10% discount rate
  - Graham's method: average past earnings capitalised at a multiplier kept "within a reasonable range of variation"; in 1976 he set a maximum multiple of 10

  **Note**: Dividing by 10% is a multiplier of 10. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).

  **Calculation for SO:**
  - Years Used: 10
  - Years: 2016-2025
  - Net Incomes: 4,341,000,000 USD, 4,401,000,000 USD, 3,976,000,000 USD, 3,524,000,000 USD, 2,393,000,000 USD, 3,119,000,000 USD, 4,739,000,000 USD, 2,226,000,000 USD, 842,000,000 USD, 2,448,000,000 USD
  - Normalized Earnings: 3,200,900,000 USD (average including losses)
  - EPV: 32,009,000,000 USD (3,200,900,000 USD / 10%)
  - EPV Per Share: 28.60 USD

  **Note**: All 10 years were profitable, demonstrating consistent earnings power.

  **Graham on earning power**: *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)

- **Margin of Safety - Conservative Dual-Anchor Approach**:
  - **Value**: -207.7%
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
  - Normalized Graham Number: 48.73 USD
  - EPV per share: 28.60 USD
  - **Intrinsic Value Used**: 28.60 USD (Capped by EPV)

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
- **Shares Outstanding**: 1,119,391,291 shares
- **Source**: Financial statements (outstandingShares.annual for 2025)
- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations
- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)
  - Graham methodology requires using shares from the same period as the financial statements
  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%

### Book Value Per Share (BVPS) Calculation:
- **Total Stockholder Equity**: 36,016,000,000 USD
- **Less: Intangible Assets**: 300,000,000 USD
- **Less: Goodwill**: 5,161,000,000 USD
- **Tangible Book Value**: 30,555,000,000 USD
- **Divided by Shares**: 1,119,391,291
- **Tangible Book Value Per Share (TBVPS)**: 27.30 USD
- **Book Value Per Share (BVPS)**: 32.17 USD (without subtracting intangibles)

### Graham Number Calculation:
- **Formula**: √(22.5 × EPS × TBVPS)
- **EPS**: 3.94 USD
- **TBVPS**: 27.30 USD
- **Calculation**: √(22.5 × 3.94 × 27.30) = √(2419.80)
- **Graham Number**: 49.19 USD
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