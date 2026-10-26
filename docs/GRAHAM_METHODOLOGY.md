# Graham Methodology Reference

> **Purpose:** the reference agents use to decide *what Graham would do* before changing any formula, threshold, investor test, verdict rule or data source in this codebase.
> **How to use it:** find the relevant section, apply its rule, and cite the section (e.g. "GRAHAM_METHODOLOGY §4.6") in the change description. If the code and this document disagree, the code is wrong unless a decision recorded here says otherwise (§9).
> Compiled 2026-10-25. Graham's books are under copyright and were not available in full text; this document therefore relies on Graham's own published lectures and interviews where possible and labels every claim by source quality.

**Source labels**
- **[P]** Primary — Graham's own words: *Current Problems in Security Analysis*, Columbia lectures 1946–47 (published by Columbia Business School); *An Hour with Mr. Graham*, March 1976 interview (in Kahn & Milne, *Benjamin Graham: The Father of Financial Analysis*, CFA Institute Research Foundation, 1977).
- **[Q]** A verbatim quotation of *The Intelligent Investor* (4th ed., 1973) or *Security Analysis* reproduced by a secondary source.
- **[S]** Consensus of secondary summaries (no verbatim text).
- **[I]** This project's interpretation — a decision, not Graham's text.

---

## 1. Core philosophy

1. **Investment vs speculation.** An investment operation promises safety of principal and an adequate return after thorough analysis; anything else is speculation. **[S]**
2. **Margin of safety is the central concept** (*Intelligent Investor* ch. 20). For a common stock bought at a sensible price, the margin of safety is the excess of its earnings yield (earnings ÷ price) over the bond interest rate: *"Over a ten year period, the typical excess of stock earning power over bond interest may aggregate 50% of the price paid. This is sufficient to provide a very real margin of safety."* **[Q]** For bargain issues the margin is the discount of price below appraised value. **[S]**
3. **Simple, conservative criteria beat forecasts.** In 1976 Graham said he had lost interest in elaborate security analysis: *"I think we can do it successfully with a few techniques and simple principles. The main point is to have the right general principles and the character to stick to them."* He favoured applying *"some simple criterion for being undervalued"* to groups of stocks, and noted *"people do not succeed in forecasting what's going to happen to the stock market."* **[P]**
4. **Facts from the record, not projections.** Graham's valuations rest on past audited results averaged over a stated period; growth projections are treated as unreliable (see §6). **[P]/[S]**

## 2. Earning power (earnings measures)

1. **Definition.** *"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past."* Future earning power is ordinarily *"the average earnings over the next five years."* **[P]** (Lecture 4)
2. **Security Analysis:** look at profits for *"not less than five years, preferably seven or ten years."* (1934, p. 452) **[Q]**
3. **Never one year alone.** *The Intelligent Investor* ch. 12 warns not to take a single year's earnings seriously, to watch for special (non-recurring) charges, and to use an average over the previous seven to ten years. **[S]**
4. **Per-share basis, adjusted for capital changes.** Graham works in per-share figures and adjusts for capital transactions: *"That gain should be adjusted for items that do not relate to earnings … The transfer to a per share basis can be made at any convenient time."* **[P]** (Lecture 2)
5. **Balance-sheet check on reported earnings.** *"Subtract the balance sheet value shown at the beginning from that at the end of the period, and add back the dividends. This sum — adjusted for capital transactions — will give you the earnings that were actually realized by the company over the period."* He used it to expose earnings hidden or overstated by reserves. **[P]** (Lectures 1 and 2)
6. **Capitalising earning power.** Value = earning power × a multiplier *"which has to be kept within a reasonable range of variation."* Multipliers of 4 versus 40 for liked/disliked companies are *"not … admissible security-analysis technique."* **[P]** (Lecture 4)
7. **Buying multiple (1976).** *"I want to double the interest rate in terms of earnings return … A maximum multiple of 10 even when interest rates are under five percent, and a maximum multiple of 7 times even when interest rates are above seven percent."* I.e. buy when the earnings yield ≥ 2 × AAA bond yield, with P/E capped between 7 and 10. **[P]**

**Rules for this project [I]:**
- Multi-year earnings measures average **reported fiscal years only** (never placeholder or dividend-only rows), and the dossier **states the period used**.
- If fewer years exist than the method needs, show **N/A with the reason** — never 0 and never an average over a shorter period than the method allows.
- Average **per-share** earnings (each year's earnings ÷ that year's shares), not total earnings ÷ today's share count.
- Use annual audited statements; TTM is supplementary only and never feeds Graham tests.

## 3. Asset values

1. **Tangible equity** is what a buyer gets for his money: in Lecture 1 Graham values a prospectus by comparing price with *"$1,350,000 worth of tangible equity. Hence he was paying three times the amount of money invested in the business."* **[P]**
2. **Working capital and net current assets.** Graham repeatedly cites companies selling below working capital (*"Curtiss-Wright selling at two thirds or less of its working capital alone"*). **[P]**
3. **Net-net (bargain) issues.** Buying at two-thirds of net current asset value, as a diversified group: *"if a stock with $50 working capital sells at $32, that would be an interesting stock. If you buy 30 companies of that sort, you're bound to make money … if you buy stocks at two-thirds of the working capital value, you have a dependable indication of group undervaluation."* **[P]** (1976) Net current asset value = current assets − **all** liabilities (and preferred stock). **[S]**
4. **Book value in the defensive test** is *"the book value last reported."* **[Q]** Asset tests elsewhere (enterprising price test, net-nets) use **net tangible assets**. **[S]**

## 4. Defensive investor — the seven criteria (*Intelligent Investor* ch. 14)

| # | Criterion | Graham's rule | Label |
|---|---|---|---|
| 4.1 | Adequate size | Industrials ≥ $100m annual sales; utilities ≥ $50m total assets (1972 dollars) | [S] |
| 4.2 | Strong financial condition | Industrials: current assets ≥ 2 × current liabilities **and** long-term debt ≤ net current assets (working capital = CA − CL). Utilities: current ratio test dropped | [S] |
| 4.3 | Earnings stability | Some earnings (no deficit) in each of the past 10 years | [S] |
| 4.4 | Dividend record | Uninterrupted payments for at least the past 20 years | [S] |
| 4.5 | Earnings growth | Per-share earnings up at least one-third over 10 years, **using three-year averages at the beginning and end** | [S] |
| 4.6 | Moderate P/E | *Current price not more than 15 × average earnings of the past three years* | [S] (consistent across sources) |
| 4.7 | Moderate price-to-assets | *"Current price should not be more than 1½ times the book value last reported."* But *"a multiplier of earnings below 15 could justify a correspondingly higher multiplier of assets"*: *"the product of the multiplier times the ratio of price to book value should not exceed 22.5."* | [Q] |

Graham frames these as a *"minimum of quality"* plus a *"minimum of quantity"* (earnings and assets per dollar of price), providing a *"factor of safety"*. **[Q]**

**The "Graham Number"** √(22.5 × EPS × BVPS) is not a formula Graham published; it is derived from 4.6 × 4.7 (15 × 1.5 = 22.5) and is the highest price passing both. Faithful to Graham, EPS is the **three-year average**. **[S]**

## 5. Enterprising investor (*Intelligent Investor* ch. 15)

| # | Criterion | Graham's rule | Label |
|---|---|---|---|
| 5.1 | Primary filter | Low multiple: P/E below 9–10 on trailing earnings; for cyclical companies use **average earnings of the last three years** | [S] (AAII) |
| 5.2 | Financial condition | Current ratio ≥ 1.5; long-term debt ≤ 110% of net current assets | [S] |
| 5.3 | Earnings stability | No deficit in the last five years | [S] |
| 5.4 | Dividend record | Some current dividend | [S] |
| 5.5 | Earnings growth | Last year's earnings higher than those of about five years earlier (1966 in the 1972 text) | [S] |
| 5.6 | Price | Less than 120% of net tangible assets | [S] |

All criteria apply **together** (AND); the low-P/E filter is a starting screen, not an alternative to the asset test. No minimum size for the enterprising investor. **[S]**

## 6. Growth-stock formula (use with care)

V = EPS × (8.5 + 2g) (1962/1973), revised 1974 to V = EPS × (8.5 + 2g) × 4.4 / Y, where g = expected 7–10 year growth and Y = current AAA yield. Graham warned the material was *"for illustrative purposes only"*, that projections are unreliable, and to *"limit your appraisals to enterprises of investment quality."* **[Q]** **Project rule [I]:** do not use it for verdicts; it depends on a forecast.

## 7. Margin of safety and the verdict (project design, D8)

Graham's principles applied to a verdict **[I]**:
- A purchase needs **both** a qualifying company (passing the investor's criteria) **and** a margin of safety; "N/A" is never evidence of quality.
- Net-current-asset bargains (price ≤ ⅔ NCAV per share) are their own category (§3.3).
- A price above conservative value is never a buy, whatever other tests say.
- Thresholds such as "≥ 20% margin = strong buy" are not Graham's and should not drive verdicts.

The ordered verdict rules are in `claude-output/REFACTOR_SCOPE.md` (D8) and will move into code in F20.

**This codebase's EPV** = average net income (7–10 years) ÷ 10% is a simplified *capitalised past earning power* (§2.1, §2.6): a multiplier of 10, within Graham's range. "EPV" as a name comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, WACC). **[I]**

## 8. Data rules derived from Graham (for this project) [I]

1. Use **raw annual audited statement data**; derive every ratio here (CLAUDE.md "Raw data in, our own calculations out"; guide §5.0).
2. Multi-year figures: reported fiscal years only, stated period, N/A below the method's minimum (§2).
3. Per-share figures use each year's own share count; adjust for splits and capital transactions (§2.4).
4. Prefer conservative choices when data is ambiguous (e.g. exclude, don't impute).
5. TTM data is informational; Graham tests use annual data only.
6. Document every assumption and conversion in the dossier.

## 9. Current code vs Graham (kept in sync with the refactor plan)

| Area | Graham | Code today | Status / plan |
|---|---|---|---|
| Normalized Graham Number EPS years | 3 reported years (§4.6) | Reported years only | **Fixed (F2)** |
| EPV display | Per share, stated period (§2.1) | Per share with years | **Fixed (F1)** |
| EPV per share | Average per-share earnings (§2.4) | Average total NI ÷ today's shares | F22 |
| Missing EPV | N/A, not zero (§2) | Becomes 0.0 and forces MoS to N/A | F3 |
| Defensive P/E (4.6) | 15 × 3-year average EPS | Single-year EPS | F20 |
| Defensive earnings growth (4.5) | Per-share, 3-year averages at both ends | Single-year total net income vs 10th year | F20 |
| Defensive dividend record (4.4) | 20 uninterrupted years | Passes with fewer years if all paid | F20 |
| Defensive P/B (4.7) | ≤ 1.5 × book, or P/E × P/B ≤ 22.5 | ≤ 1.5 × BVPS; 22.5 product computed but not used in the test | F20 |
| Book value for Graham Number | "Book value last reported" (§3.4) | Tangible book (TBVPS) | **Open decision** (BVPS vs TBVPS) |
| Adequate size (4.1) | Required | Not implemented | Ignored by decision D7 |
| Enterprising price (5.1, 5.6) | Low P/E **and** < 120% net tangible assets | P/E < 10 **or** price < 1.2 × TBVPS | F20 (AND) |
| Enterprising earnings growth (5.5) | Required (≈5-year) | "N/A - Not Required" | F20 |
| Verdict (§7) | Quality **and** margin of safety | ENTERPRISING BUY can override a negative MoS; N/A counts as pass | F20 (D8) |
| Pre-computed EODHD values | Raw data (§8.1) | Forward dividend in history, dividend counts as amounts, market-cap price fallback | F21 |

## 10. Sources

- Graham, *Current Problems in Security Analysis*, Lectures 1–10 (1946–47), Columbia Business School: e.g. [Lecture 4](https://business.columbia.edu/sites/default/files-efs/imce-uploads/Graham_Sept1946Feb1947_CurrentProblemsinSecurityAnalysis_Lecture4.pdf) (replace the number for other lectures).
- Kahn & Milne, [*Benjamin Graham: The Father of Financial Analysis*](https://www.ivey.uwo.ca/media/3065497/ben-graham-father-financial-analysis.pdf) (CFA Institute Research Foundation, 1977), incl. "An Hour with Mr. Graham, March 1976".
- [Graham number — Wikipedia](https://en.wikipedia.org/wiki/Graham_number) (quotes ch. 14 criterion 7).
- [Benjamin Graham formula — Wikipedia](https://en.wikipedia.org/wiki/Benjamin_Graham_formula).
- [GuruFocus: *The Intelligent Investor* Chapter 14 reviewed](https://www.gurufocus.com/news/704217/the-intelligent-investor-chapter-14-reviewed).
- [AAII: Adjusting the Benjamin Graham Enterprising Investor Screen](https://www.aaii.com/files/journal/pdf/adjusting-the-benjamin-graham-enterprising-investor-screen.pdf) (Oct 2012).
- [York University: The Long-Term P/E](https://www-users.york.ac.uk/~ka536/ltpe.htm) and [Calculated Risk](https://calculatedriskblog.com/2009/12/leonhardt-on-long-term-pes.html) (*Security Analysis* 1934 p. 452).
- [Motley Fool: Earnings, Dividends and the Intelligent Investor](https://www.fool.com/investing/general/2012/02/28/earnings-dividends-and-the-intelligent-investor.aspx) (ch. 12).
- Ch. 20 margin-of-safety quotes via secondary sources: [Livewire](https://livewiremarkets.com/wires/the-secret-of-sound-investment-in-three-words), [Shortform](https://www.shortform.com/blog/margin-of-safety-stocks/).

When the books themselves are available, verify the [S] items against the 1973 *Intelligent Investor* (chapters 12, 14, 15, 20) and *Security Analysis* (chapters on earnings, book value and current-asset value), and upgrade labels to [Q].
