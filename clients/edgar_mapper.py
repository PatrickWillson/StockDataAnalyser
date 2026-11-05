"""
SEC EDGAR XBRL companyfacts -> annual statement rows for CompanyFundamentals (free resolution path).

The only code that knows US-GAAP tag names. Choices follow docs/GRAHAM_METHODOLOGY.md and the free-path
decisions (claude-output scope, CODEBASE_GUIDE §12):
- Annual figures come from annual filings (10-K, 10-K/A, 10-KT): durations of 350-380 days, instants at
  the fiscal-year end; each fiscal year is keyed by its actual period-end date (52/53-week years).
- A year filed in several reports takes the latest filed value (restatements), and every year/field
  whose value differs from the first-reported one is listed in the notes (GRAHAM_METHODOLOGY §8.7).
- Each field takes the first tag of its chain that has a value for the year; a value derived from other
  tags (e.g. total liabilities = liabilities and equity - equity) is listed in the notes.
- When several tags of a chain carry the year, the most recently filed one wins (a company that switched
  tags restated the year under the new one); a tie goes to chain order.
- Revenue prefers sales-type tags over the broader `Revenues`, which can include other income such as
  equity-affiliate earnings (decision D-F3); utilities (SIC 4900-4999) use `Revenues`, their total
  operating revenues. Short-term debt is the sum of distinct components (D-F4). Year-end shares fall
  back to issued - treasury, then the cover-page count of that year's 10-K (D-F2), then the year's
  weighted-average basic shares.
- Per-share values and share counts are put on today's share basis (GRAHAM_METHODOLOGY §2.4): a value
  filed before a stock split is adjusted by every split after its filing date (splits from yfinance).
Only USD statements are mapped (foreign SEC filers are a later step).
"""

import datetime as dt
import html
import math
import re
import statistics
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from core.fundamentals import BalanceSheetRow, IncomeStatementRow
from core.history import fiscal_year

ANNUAL_FORMS = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})
PERIODIC_FORMS = ANNUAL_FORMS | {"10-Q", "10-Q/A"}
# Duration windows in days: a fiscal year, a quarter, nine months year-to-date
DURATIONS = {"year": (350, 380), "quarter": (80, 100), "nine_months": (260, 285)}
GAAP, DEI = "us-gaap", "dei"
MONEY, PER_SHARE, SHARES = "USD", "USD/shares", "shares"

# Field -> tag chain (first tag with a value for the year wins)
REVENUE = ("RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
           "SalesRevenueNet", "SalesRevenueGoodsNet", "Revenues", "RevenuesNetOfInterestExpense",
           "RegulatedAndUnregulatedOperatingRevenue", "RegulatedOperatingRevenue")   # water and electric utilities
# Banks with no revenue tag: net revenue, as JPMorgan's RevenuesNetOfInterestExpense
NET_INTEREST_INCOME, NONINTEREST_INCOME = ("InterestIncomeExpenseNet", "InterestRevenueExpenseNet"), ("NoninterestIncome",)
NET_INCOME = ("NetIncomeLossAvailableToCommonStockholdersBasic", "NetIncomeLoss")
AVAILABLE_TO_COMMON = NET_INCOME[0]
PREFERRED_DIVIDENDS = ("PreferredStockDividendsAndOtherAdjustments", "PreferredStockDividendsIncomeStatementImpact",
                       "DividendsPreferredStock")
# How far below net income earnings for the common may sit without preferred dividends explaining the gap
# (two-class allocations: Oil-Dri 5%; JPMorgan FY2009 25%, 8,774M of 11,728M), and how far above it (a loss
# shared with participating securities: Hurco FY2020 1%)
COMMON_EARNINGS_MAX_GAP = 1 / 3
COMMON_EARNINGS_MAX_EXCESS = 0.02
PREFERRED_GAP_TOLERANCE = 0.10
# Consolidated profit incl. minority interests: ProfitLoss = NetIncomeLoss + NetIncomeLossAttributableToNoncontrollingInterest
PROFIT_LOSS, NCI_INCOME = ("ProfitLoss",), ("NetIncomeLossAttributableToNoncontrollingInterest",)
# A minority balance below this share of ProfitLoss cannot move it materially (Ethan Allen FY2025: -85K of 51.6M)
MINORITY_IMMATERIAL = 0.01
EPS = ("EarningsPerShareBasic", "EarningsPerShareBasicAndDiluted")
EQUITY = ("StockholdersEquity",)
EQUITY_INCL_NCI = ("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",)
# Water utilities' balance sheets: total capitalization = equity (with preferred) + long-term debt
CAPITALIZATION = ("CapitalizationLongtermDebtAndEquity",)
MINORITY = ("MinorityInterest",)
TEMPORARY_EQUITY = ("TemporaryEquityCarryingAmountAttributableToParent", "RedeemableNoncontrollingInterestEquityCarryingAmount")
GOODWILL = ("Goodwill",)
INTANGIBLES = ("IntangibleAssetsNetExcludingGoodwill",)
FINITE_INTANGIBLES, INDEFINITE_INTANGIBLES = ("FiniteLivedIntangibleAssetsNet",), ("IndefiniteLivedIntangibleAssetsExcludingGoodwill",)
# Indefinite-lived intangibles tagged by kind (Coca-Cola: trademarks, bottlers' franchise rights)
NAMED_INDEFINITE_INTANGIBLES = ("IndefiniteLivedTrademarks", "IndefiniteLivedFranchiseRights",
                                "IndefiniteLivedLicenseAgreements", "IndefiniteLivedTradeNames",
                                "IndefiniteLivedContractualRights")
OTHER_INTANGIBLES = ("OtherIntangibleAssetsNet",)                 # finite + other indefinite, as one line
OTHER_INDEFINITE_INTANGIBLES = ("OtherIndefiniteLivedIntangibleAssets",)
CURRENT_ASSETS, CURRENT_LIABILITIES = ("AssetsCurrent",), ("LiabilitiesCurrent",)
LIABILITIES, ASSETS, LIABILITIES_AND_EQUITY = ("Liabilities",), ("Assets",), ("LiabilitiesAndStockholdersEquity",)
LONG_TERM_DEBT = ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations")
LONG_TERM_DEBT_TOTAL = ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities")
# ^ incl. the current portion; banks report only these (JPMorgan: the second)
# Non-current debt tagged by kind when no non-current total is (Lifetime Brands: term loan + revolver; Village
# Super Market: notes + other). Some filers misuse "other" (Lifetime FY2024: 4,108K of other long-term
# obligations): kept, the conservative reading of an ambiguous tag (GRAHAM_METHODOLOGY §8.4)
LONG_TERM_NOTES = ("LongTermNotesPayable", "LongTermLoansPayable")
LONG_TERM_REVOLVER, OTHER_LONG_TERM_DEBT = ("LongTermLineOfCredit",), ("OtherLongTermDebtNoncurrent",)
# Oil-Dri: senior notes. Citizens & Northern, a bank: FHLB advances 165.45M + senior 14.9M + subordinated 24.83M
SENIOR_NOTES, SUBORDINATED_DEBT = ("SeniorLongTermNotes", "SeniorNotesNoncurrent", "SeniorNotes"), ("SubordinatedDebt",)
FHLB_ADVANCES = ("FederalHomeLoanBankAdvancesLongTerm",)
# Outside LongTermDebt at some banks (Arrow Financial: 20,000K beside term advances), inside it at others
# (JPMorgan), and the tags do not say which: noted, never added
JUNIOR_SUBORDINATED = ("JuniorSubordinatedDebentureOwedToUnconsolidatedSubsidiaryTrust",)
DEBT_CURRENT = ("DebtCurrent",)
SHORT_BORROWINGS, COMMERCIAL_PAPER = ("ShortTermBorrowings",), ("CommercialPaper",)
LTD_CURRENT = ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent", "SeniorNotesCurrent")
INVENTORY = ("InventoryNet",)
UTILITY_INVENTORY = ("EnergyRelatedInventoryNaturalGasInStorage", "EnergyRelatedInventoryOtherFossilFuel",
                     "EnergyRelatedInventoryCoal", "EnergyRelatedInventoryPropaneGas", "OtherInventorySupplies")
# Energy companies tagging a total (ExxonMobil: crude oil, products and merchandise + materials and supplies).
# ExxonMobil's FY2012-13 10-Ks tag the same line InventoryFinishedGoodsAndWorkInProcess; their
# EnergyRelatedInventoryNaturalGasInStorage (300M) is a detail of it, not a separate line
ENERGY_INVENTORY_TOTAL = ("EnergyRelatedInventory", "InventoryFinishedGoodsAndWorkInProcess")
SUPPLIES_INVENTORY = ("OtherInventorySupplies", "InventoryPartsAndComponentsNetOfReserves")
# Carrying value of preferred stock inside equity; the "including additional paid-in capital" tags are the
# full amount (JPMorgan), PreferredStockValue is sometimes par value only
PREFERRED = ("PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount", "PreferredStockIncludingAdditionalPaidInCapital",
             "PreferredStockValue", "PreferredStockValueOutstanding")
PREFERRED_LIQUIDATION = ("PreferredStockLiquidationPreferenceValue",)
SHARES_OUTSTANDING = ("CommonStockSharesOutstanding",)
SHARES_ISSUED, TREASURY_SHARES = ("CommonStockSharesIssued",), ("TreasuryStockCommonShares", "TreasuryStockShares")
COVER_SHARES = ("EntityCommonStockSharesOutstanding",)
CLASS_AXIS = "StatementClassOfStockAxis"
WEIGHTED_SHARES = ("WeightedAverageNumberOfSharesOutstandingBasic",)
UTILITY_SIC = range(4900, 5000)
DIVIDENDS_PAID = ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends", "PaymentsOfOrdinaryDividends")
OPERATING_CASH_FLOW = ("NetCashProvidedByUsedInOperatingActivities",
                       "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations")
YEAR_END_TAGS = ("NetIncomeLoss", "ProfitLoss", "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                 "EarningsPerShareBasic")

MIN_DAYS_BETWEEN_YEAR_ENDS = 300
SCALE_ERRORS = (1e3, 1e6)        # filers tagging figures in thousands or millions as units
SCALE_ERROR_TOLERANCE = 0.005
MIN_YEARS_FOR_SHARE_SCALE = 3
MAX_UNREPORTED_FILINGS = 3
MAX_DERIVED_BELOW_COVER = 100
RESTATEMENT_TOLERANCE = 0.001   # relative change below which two filed values are the same figure
PER_SHARE_TOLERANCE = 0.005    # absolute, for per-share values (filed rounded to the cent)


@dataclass(frozen=True)
class Fact:
    value: float
    first_value: float
    tag: str
    restated: bool


@dataclass(frozen=True)
class EdgarAnnualData:
    """Annual statement data mapped from companyfacts (newest first)."""
    balance_sheets: Tuple[BalanceSheetRow, ...]
    income_statements: Tuple[IncomeStatementRow, ...]
    dividends_paid: Mapping[str, float]          # period end -> total cash dividends paid (>= 0)
    operating_cash_flow: Mapping[str, float]     # period end -> net cash from operating activities
    shares_by_year: Mapping[str, float]          # 'YYYY' of the period end -> year-end shares
    latest_cover_shares: float                   # cover-page count of the latest 10-K (0.0 if none)
    notes: Tuple[str, ...]                       # data-quality notes for the dossier


def _days(start: str, end: str) -> int:
    return (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days


def _annual(row: Mapping[str, Any]) -> bool:
    return row.get("form") in ANNUAL_FORMS


def _lasts(row: Mapping[str, Any], kind: str) -> bool:
    low, high = DURATIONS[kind]
    return "start" in row and low <= _days(row["start"], row["end"]) <= high


class _Facts:
    """Index of annual facts: (taxonomy, tag) -> {period end: [(filed, value)]}."""

    def __init__(self, companyfacts: Mapping[str, Any], splits: Sequence[Tuple[str, float]] = (),
                 forms: frozenset = ANNUAL_FORMS):
        self.facts = companyfacts.get("facts", {})
        self.forms = forms
        self.splits = sorted((date, ratio) for date, ratio in splits if ratio and ratio > 0)
        self._cache: Dict[Tuple[str, str, str, str], Dict[str, List[Tuple[str, float]]]] = {}
        self.scale_errors: set = set()

    def split_factor(self, filed: str) -> float:
        """Shares today per share at the filing date: product of the splits after `filed`."""
        factor = 1.0
        for date, ratio in self.splits:
            if date > filed:
                factor *= ratio
        return factor

    def adjusted(self, unit: str, filed: str, value: float) -> float:
        if unit == SHARES:
            return value * self.split_factor(filed)
        if unit == PER_SHARE:
            return value / self.split_factor(filed)
        return value

    def series(self, tag: str, unit: str, kind: str, taxonomy: str = GAAP) -> Dict[str, List[Tuple[str, float]]]:
        key = (taxonomy, tag, unit, kind)
        if key not in self._cache:
            by_end: Dict[str, List[Tuple[str, float]]] = {}
            for row in self.facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get(unit, []):
                if row.get("form") not in self.forms:
                    continue
                if kind == "instant":
                    if "start" in row:
                        continue
                elif not _lasts(row, kind):
                    continue
                by_end.setdefault(row["end"], []).append((row["filed"], row["val"]))
            self._cache[key] = by_end
        return self._cache[key]

    def _without_scale_errors(self, ordered: List[Tuple[str, float]], tag: str, end: str, unit: str,
                              kind: str) -> List[Tuple[str, float]]:
        """
        Drop a figure a filing tagged at the wrong scale, when another filing has it right: an exact 1,000x or
        1,000,000x apart, whichever way. The other years of the tag show which is wrong (Ingles FY2010 assets:
        1,532,358 filed after 1,532,358,110; Berkshire FY2011 average shares: 1,649,891,000,000 before 1,649,891).
        """
        values = [abs(value) for _, value in ordered if value]
        if unit == PER_SHARE or len(values) < 2:
            return ordered
        low, high = min(values), max(values)
        if not any(abs(high / low / scale - 1) <= SCALE_ERROR_TOLERANCE for scale in SCALE_ERRORS):
            return ordered
        others = [abs(rows[-1][1]) for other, rows in self.series(tag, unit, kind).items() if other != end and rows[-1][1]]
        if not others:
            return ordered
        typical = statistics.median(others)
        keep_high = abs(math.log(high / typical)) <= abs(math.log(low / typical))
        wrong = low if keep_high else high
        self.scale_errors.add(f"{tag} {end[:4]}")
        return [(filed, value) for filed, value in ordered if abs(value) != wrong]

    def get(self, chain: Sequence[str], end: str, unit: str, kind: str) -> Optional[Fact]:
        best = None
        for rank, tag in enumerate(chain):
            values = self.series(tag, unit, kind).get(end)
            if values:
                ordered = sorted(values, key=lambda item: item[0])   # by filing date; stable for ties
                key = (ordered[-1][0], -rank)                        # latest filing, then chain order
                if best is None or key > best[0]:
                    best = (key, tag, ordered)
        if best is None:
            return None
        _, tag, ordered = best
        ordered = self._without_scale_errors(ordered, tag, end, unit, kind)
        adjusted = [self.adjusted(unit, filed, value) for filed, value in ordered]
        first, latest = adjusted[0], adjusted[-1]
        # Per-share figures are filed rounded to the cent: within half a cent they are the same figure
        tolerance = PER_SHARE_TOLERANCE if unit == PER_SHARE else RESTATEMENT_TOLERANCE * max(abs(first), 1e-9)
        changed = any(abs(v - first) > tolerance for v in adjusted)
        return Fact(value=float(latest), first_value=float(first), tag=tag, restated=changed)

    def currencies(self, tag: str) -> List[str]:
        return list(self.facts.get(GAAP, {}).get(tag, {}).get("units", {}).keys())


def _shown(value: float, unit: str) -> str:
    """A filed figure for a note: money in millions, shares in millions, per-share to the cent."""
    if unit == PER_SHARE:
        return f"{value:,.2f}"
    return f"{value / 1e6:,.0f}M"


class _Notes:
    """Collects derivation and restatement notes, grouped per field for the dossier."""

    def __init__(self):
        self.derived: Dict[str, List[str]] = {}
        self.restated: List[str] = []
        self.other: List[str] = []

    def derive(self, field: str, how: str, end: str):
        self.derived.setdefault(f"{field}: {how}", []).append(end[:4])

    def fact(self, field: str, end: str, fact: Optional[Fact], unit: str = MONEY):
        if fact is not None and fact.restated:
            self.restated.append(f"FY{end[:4]} {field} {_shown(fact.first_value, unit)} -> {_shown(fact.value, unit)}")

    def render(self) -> Tuple[str, ...]:
        out = [f"SEC EDGAR: {how} (FY{', FY'.join(sorted(set(years)))})" for how, years in self.derived.items()]
        if self.restated:
            out.append("SEC EDGAR: restated in later filings, latest figure used (first reported -> latest): "
                       + "; ".join(self.restated))
        return tuple(out + self.other)


def fiscal_year_ends(facts: _Facts) -> List[str]:
    """
    Period ends of the company's fiscal years (from 1-year income facts in annual filings), newest first.
    Two years cannot end months apart: the one without a balance sheet is a filer's misdated fact (Ethan Allen's
    FY2022 10-K dates June-year revenue 2020-01-01 to 2020-12-31).
    """
    ends = set()
    for tag in YEAR_END_TAGS:
        for unit in (MONEY, PER_SHARE):
            ends.update(facts.series(tag, unit, "year"))
    balance_sheets = facts.series(ASSETS[0], MONEY, "instant")
    return sorted((end for end in ends if end in balance_sheets
                   or not any(other in balance_sheets and 0 < abs(_days(end, other)) < MIN_DAYS_BETWEEN_YEAR_ENDS
                              for other in ends)), reverse=True)


def filer_fiscal_years(facts: _Facts) -> Dict[str, int]:
    """
    Period end -> the fiscal year the company declared for it: `fy` of the annual filing whose own
    (latest) year it is. A fact's `fy` is that of its filing, comparatives included, so only the
    filing's newest period end carries the filing's fiscal year (cf. EdgarTools issue #460).
    """
    newest: Dict[str, Tuple[str, int]] = {}
    for tag in YEAR_END_TAGS:
        for unit in (MONEY, PER_SHARE):
            for row in facts.facts.get(GAAP, {}).get(tag, {}).get("units", {}).get(unit, []):
                if _annual(row) and _lasts(row, "year") and row.get("fy") and row.get("accn"):
                    current = newest.get(row["accn"])
                    if current is None or row["end"] > current[0]:
                        newest[row["accn"]] = (row["end"], int(row["fy"]))
    return {end: fy for end, fy in newest.values()}


def _value(fact: Optional[Fact]) -> Optional[float]:
    return None if fact is None else fact.value


def _sum(facts: _Facts, chain: Sequence[str], end: str, unit: str) -> Tuple[Optional[float], List[str]]:
    """Sum of the tags in `chain` that have a value (each tag once); (None, []) when none."""
    total, used = 0.0, []
    for tag in chain:
        fact = facts.get((tag,), end, unit, "instant")
        if fact is not None:
            total += fact.value
            used.append(tag)
    return (total, used) if used else (None, [])


def _first(facts: _Facts, chain: Sequence[str], end: str) -> Tuple[Optional[float], List[str]]:
    """The first tag of `chain` with an instant value: (value, [tag]) or (None, [])."""
    fact = facts.get(chain, end, MONEY, "instant")
    return (None, []) if fact is None else (fact.value, [fact.tag])


def _repair_share_scale(rows: List[BalanceSheetRow], notes: _Notes) -> List[BalanceSheetRow]:
    """
    Share counts a filer tagged in thousands with no other filing to correct them (Graham Corp FY2011: 10,216 among
    about 10 million a year). Split-adjusted counts of one company do not move 1,000x, so the other years expose
    them. Only share counts: money can (Southern Co's goodwill: 2M in FY2015, 5bn after an acquisition).
    """
    counts = [row.shares_outstanding for row in rows if row.shares_outstanding]
    if len(counts) < MIN_YEARS_FOR_SHARE_SCALE:
        return rows
    typical = statistics.median(counts)
    repaired = []
    for row in rows:
        shares = row.shares_outstanding
        if shares and typical / 2 <= shares * 1000 <= typical * 2:
            notes.derive("share count", "tagged in thousands by the filer; multiplied by 1,000", row.period_end)
            row = replace(row, shares_outstanding=shares * 1000)
        repaired.append(row)
    return repaired


def _long_term_debt(facts: _Facts, end: str, notes: _Notes) -> Tuple[Optional[float], bool]:
    """
    Debt due after a year, as the long-term debt tests want it (GRAHAM_METHODOLOGY §4.2): the non-current
    total, else the larger of its tagged kinds and the total less its current portion (the conservative
    reading, §8.4). Returns (value, includes_current):
    with no current portion tagged the total is used whole, and it is flagged so it is not counted again as
    short-term debt (banks report only this).
    """
    fact = facts.get(LONG_TERM_DEBT, end, MONEY, "instant")
    notes.fact("long-term debt", end, fact)
    if fact is not None:
        return fact.value, False
    used, parts = [], 0.0
    for chain in (LONG_TERM_NOTES, LONG_TERM_REVOLVER, SENIOR_NOTES, SUBORDINATED_DEBT, FHLB_ADVANCES):
        part = facts.get(chain, end, MONEY, "instant")
        notes.fact("long-term debt", end, part)
        if part is not None:
            parts += part.value
            used.append(part.tag)
    other = facts.get(OTHER_LONG_TERM_DEBT, end, MONEY, "instant")
    total = facts.get(LONG_TERM_DEBT_TOTAL, end, MONEY, "instant")
    notes.fact("long-term debt", end, total)
    # "Other" alone is only a detail beside a total (Village FY2018: 6.4M of 48.2M)
    if other is not None and (used or total is None):
        notes.fact("long-term debt", end, other)
        parts += other.value
        used.append(other.tag)
    current, current_used = _first(facts, LTD_CURRENT, end)
    net = None if total is None else total.value - (current or 0.0)
    # The parts can be the whole debt (Lifetime Brands) or one piece of the total (Village FY2018: 6.4M of 48.2M)
    if used and (net is None or parts >= net):
        notes.derive("long-term debt", "derived as the sum of " + ", ".join(used), end)
        return parts, False
    if total is None:
        return None, False
    if facts.get(JUNIOR_SUBORDINATED, end, MONEY, "instant") is not None:
        notes.derive("long-term debt", "junior subordinated debt is tagged separately and may not be included", end)
    if current_used:
        notes.derive("long-term debt", f"derived as {total.tag} - {current_used[0]}", end)
        return net, False
    notes.derive("long-term debt", f"{total.tag} used (includes the current portion)", end)
    return total.value, True


def _intangible_parts(facts: _Facts, end: str) -> Tuple[Optional[float], List[str]]:
    """
    Intangibles excluding goodwill when no total is tagged: the indefinite-lived total, else its named
    kinds (trademarks, franchise rights, ...), plus the "other intangible assets" line (finite + other
    indefinite), else finite-lived + other indefinite-lived. Each figure is counted once.
    """
    indefinite, used = _first(facts, INDEFINITE_INTANGIBLES, end)
    if indefinite is None:
        indefinite, used = _sum(facts, NAMED_INDEFINITE_INTANGIBLES, end, MONEY)
        other, other_used = _first(facts, OTHER_INTANGIBLES, end)
        if other is None:
            finite, finite_used = _first(facts, FINITE_INTANGIBLES, end)
            other_indefinite, oi_used = _first(facts, OTHER_INDEFINITE_INTANGIBLES, end)
            parts = [v for v in (finite, other_indefinite) if v is not None]
            other, other_used = (sum(parts) if parts else None), finite_used + oi_used
    else:
        other, other_used = _first(facts, FINITE_INTANGIBLES, end)
        if other is None:
            # Preformed Line Products: indefinite-lived 0, other intangible assets 10.1M. Separate lines at Graham Corp;
            # JPMorgan's "other" likely includes its 600M: the sum errs on the conservative side (GRAHAM_METHODOLOGY §8.4)
            other, other_used = _first(facts, OTHER_INTANGIBLES, end)
    values = [v for v in (indefinite, other) if v is not None]
    return (sum(values) if values else None), used + other_used


_INTANGIBLE_TAG = re.compile(r"Intangible|Trademark|FranchiseRights|LicenseAgreements|TradeNames")
# Tags about intangibles that are not the balance-sheet amount (taxes, amortisation, acquisitions'
# purchase-price allocations, gross amounts, ...)
_NOT_A_BALANCE = re.compile(r"Tax|Amortization|Impairment|Disposal|Acquired|Acquisition|Useful|Payments|Proceeds|"
                            r"Gross|Accumulated|Expected|Increase|Decrease|Weighted|Percentage|Goodwill")
_MAPPED_INTANGIBLES = set(INTANGIBLES + FINITE_INTANGIBLES + INDEFINITE_INTANGIBLES + NAMED_INDEFINITE_INTANGIBLES
                          + OTHER_INTANGIBLES + OTHER_INDEFINITE_INTANGIBLES)


def _note_unmapped_intangibles(facts: _Facts, end: str, notes: _Notes) -> None:
    """List intangible-asset tags with a value at `end` that the mapping does not read (a gap to fix)."""
    for tag, concept in facts.facts.get(GAAP, {}).items():
        if tag in _MAPPED_INTANGIBLES or not _INTANGIBLE_TAG.search(tag) or _NOT_A_BALANCE.search(tag):
            continue
        values = facts.series(tag, MONEY, "instant").get(end)
        if values and any(v for _, v in values):
            notes.derive("intangibles", f"{tag} is tagged but not included (check the intangibles total)", end)


def _balance_row(facts: _Facts, end: str, notes: _Notes, period_kind: str = "year") -> Optional[BalanceSheetRow]:
    assets = facts.get(ASSETS, end, MONEY, "instant")
    liabilities_and_equity = facts.get(LIABILITIES_AND_EQUITY, end, MONEY, "instant")
    if assets is None and liabilities_and_equity is None:
        return None   # no balance sheet for this year (e.g. only comparatives of income items)
    for name, fact in (("total assets", assets), ("liabilities and equity", liabilities_and_equity)):
        notes.fact(name, end, fact)

    def field(name: str, chain: Sequence[str], unit: str = MONEY) -> Optional[float]:
        fact = facts.get(chain, end, unit, "instant")
        notes.fact(name, end, fact, unit)
        return _value(fact)

    minority = field("minority interest", MINORITY)
    equity_incl = field("equity incl. minority interest", EQUITY_INCL_NCI)
    equity = field("stockholders' equity", EQUITY)
    if equity is None and equity_incl is not None:
        equity = equity_incl - (minority or 0.0)
        notes.derive("stockholders' equity", "derived as equity incl. minority interest - minority interest", end)
    if equity is None:
        # Middlesex Water FY2015: 342,038 - 132,908 = 209,130, common equity 206,694 + preferred 2,436
        capitalization = facts.get(CAPITALIZATION, end, MONEY, "instant")
        noncurrent_debt = facts.get(LONG_TERM_DEBT[:1], end, MONEY, "instant")
        if capitalization is not None and noncurrent_debt is not None:
            equity = capitalization.value - noncurrent_debt.value
            notes.derive("stockholders' equity", "derived as total capitalization - long-term debt", end)

    liabilities = field("total liabilities", LIABILITIES)
    if liabilities is None and liabilities_and_equity is not None and (equity_incl is not None or equity is not None):
        temporary, _ = _sum(facts, TEMPORARY_EQUITY, end, MONEY)
        base = equity_incl if equity_incl is not None else equity + (minority or 0.0)
        liabilities = liabilities_and_equity.value - base - (temporary or 0.0)
        notes.derive("total liabilities", "derived as liabilities and equity - total equity"
                     + (" - temporary equity" if temporary else ""), end)

    intangibles = field("intangibles", INTANGIBLES)
    if intangibles is None:
        intangibles, used = _intangible_parts(facts, end)
        if used:
            notes.derive("intangibles (ex goodwill)", "derived as the sum of " + ", ".join(used), end)
    _note_unmapped_intangibles(facts, end, notes)

    long_term_debt, includes_current = _long_term_debt(facts, end, notes)

    debt_current = field("short-term debt", DEBT_CURRENT)
    if debt_current is None:
        parts = [field("short-term debt", SHORT_BORROWINGS) or field("short-term debt", COMMERCIAL_PAPER)]
        if not includes_current:   # the current portion is already in a long-term total
            parts.append(field("short-term debt", LTD_CURRENT))
        if any(p is not None for p in parts):
            debt_current = sum(p or 0.0 for p in parts)

    inventory = field("inventory", INVENTORY)
    if inventory is None:
        energy = facts.get(ENERGY_INVENTORY_TOTAL, end, MONEY, "instant")
        if energy is not None:
            supplies, supplies_used = _first(facts, SUPPLIES_INVENTORY, end)
            inventory = energy.value + (supplies or 0.0)
            used = [energy.tag] + supplies_used
        else:
            inventory, used = _sum(facts, UTILITY_INVENTORY, end, MONEY)
        if used:
            notes.derive("inventory", "derived as the sum of " + ", ".join(used), end)

    shares = field("shares outstanding", SHARES_OUTSTANDING, SHARES)
    if shares is None:
        issued = field("shares issued", SHARES_ISSUED, SHARES)
        treasury = field("treasury shares", TREASURY_SHARES, SHARES)
        cover = _cover_shares(facts, end)
        derived = None if issued is None else issued - (treasury or 0.0)
        # Some filers tag issued and treasury counts rounded to millions (Southern Co: "1.1 billion"):
        # the cover-page count is then the precise figure
        rounded = derived is not None and issued % 1e6 == 0 and (treasury or 0.0) % 1e6 == 0
        # Or the issued tag holds something else (Unitil FY2010: 41,455, with 10.9 million on the cover)
        implausible = derived is not None and cover is not None and derived * MAX_DERIVED_BELOW_COVER < cover
        if derived is not None and not ((rounded or implausible) and cover is not None):
            shares = derived
            notes.derive("year-end shares", "derived as shares issued - treasury shares", end)
        elif cover is not None:
            shares = cover
            notes.derive("year-end shares", "cover-page count of the filing (dated after the period end)"
                         + ("; issued and treasury counts are tagged rounded to millions" if rounded else ""), end)
        else:
            weighted = facts.get(WEIGHTED_SHARES, end, SHARES, period_kind)
            if weighted is not None:
                shares = weighted.value
                notes.derive("year-end shares", "weighted-average basic shares of the period (no period-end count tagged)", end)

    # Preferred stock inside equity, at the higher of its carrying value and its liquidation preference:
    # Graham deducts it at "par (plus back dividends) or market, whichever is higher" (§3.5); market
    # value is not in the filings
    carrying = field("preferred stock", PREFERRED)
    liquidation = field("preferred stock", PREFERRED_LIQUIDATION)
    preferred = max((v for v in (carrying, liquidation) if v is not None), default=None)
    if liquidation is not None and (carrying is None or liquidation > carrying):
        notes.derive("preferred stock", "at its liquidation preference (above its carrying value)", end)

    return BalanceSheetRow(
        period_end=end,
        total_equity=equity,
        intangible_assets=intangibles,
        goodwill=field("goodwill", GOODWILL),
        current_assets=field("current assets", CURRENT_ASSETS),
        current_liabilities=field("current liabilities", CURRENT_LIABILITIES),
        total_liabilities=liabilities,
        long_term_debt=long_term_debt,
        short_term_debt=debt_current,
        total_debt_reported=None,
        total_assets=_value(assets),
        inventory=inventory,
        noncontrolling_interest=minority,
        shares_outstanding=shares,
        preferred_stock=preferred,
    )


def _cover_shares(facts: _Facts, end: str) -> Optional[float]:
    """dei:EntityCommonStockSharesOutstanding of the filing for the period ending `end` (dated 0-150 days later)."""
    candidates = []
    for row in facts.facts.get(DEI, {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get(SHARES, []):
        if row.get("form") in facts.forms and 0 <= _days(end, row["end"]) <= 150:
            candidates.append((row["filed"], row["end"], facts.adjusted(SHARES, row["filed"], row["val"])))
    if not candidates:
        return None
    # The 10-K for this year: the earliest filing; a company with several share classes reports one row
    # per class on the same date, which are added
    filed = min(c[0] for c in candidates)
    same_filing = [c for c in candidates if c[0] == filed]
    date = min(c[1] for c in same_filing)
    return float(sum(c[2] for c in same_filing if c[1] == date))


def _sound_common_earnings(available: Fact, net: Fact, preferred: Optional[Fact]) -> bool:
    """
    Earnings for the common are net income less what ranks ahead (GRAHAM_METHODOLOGY §2.3). Filers also use the
    tag for continuing operations only, above net income or not (Hooker FY2026: -12.9M, net loss 27.0M), or for a
    small allocation (Arrow FY2012: -0.5M, net income 22.2M). A large gap needs preferred dividends to explain it
    (Bank of America FY2009: -2.2bn, net income 6.3bn, preferred dividends 8.5bn).
    """
    gap = net.value - available.value
    if gap < -COMMON_EARNINGS_MAX_EXCESS * abs(net.value):
        return False
    if gap <= COMMON_EARNINGS_MAX_GAP * abs(net.value):
        return True
    return preferred is not None and abs(gap - preferred.value) <= PREFERRED_GAP_TOLERANCE * abs(preferred.value)


def _net_income(facts: _Facts, end: str, kind: str, notes: Optional["_Notes"] = None) -> Optional[Fact]:
    """
    Net income for the common: the NET_INCOME chain, else ProfitLoss minus the minority interests'
    share (US-GAAP: ProfitLoss = NetIncomeLoss + NetIncomeLossAttributableToNoncontrollingInterest),
    else ProfitLoss when no minority interest is reported at the period end (Johnson & Johnson tagged
    FY2007-09 only as ProfitLoss). None when the minority share cannot be taken out.
    """
    fact = facts.get(NET_INCOME, end, MONEY, kind)
    if fact is not None:
        if fact.tag == AVAILABLE_TO_COMMON:
            net = facts.get(NET_INCOME[1:], end, MONEY, kind)
            if net is not None and not _sound_common_earnings(fact, net, facts.get(PREFERRED_DIVIDENDS, end, MONEY, kind)):
                if notes is not None:
                    notes.derive("net income", f"NetIncomeLoss used: {AVAILABLE_TO_COMMON} is not net income less "
                                 "preferred dividends", end)
                fact = net
        if notes is not None:
            notes.fact("net income", end, fact)
        return fact
    profit = facts.get(PROFIT_LOSS, end, MONEY, kind)
    if profit is None:
        return None
    minority_share = facts.get(NCI_INCOME, end, MONEY, kind)
    if minority_share is not None:
        how, value = "derived as ProfitLoss - the minority interests' share", profit.value - minority_share.value
    elif not _value(facts.get(MINORITY, end, MONEY, "instant")):
        how, value = "ProfitLoss used (no minority interest reported)", profit.value
    elif abs(_value(facts.get(MINORITY, end, MONEY, "instant"))) < MINORITY_IMMATERIAL * abs(profit.value):
        how, value = "ProfitLoss used (minority interest immaterial)", profit.value
    else:
        if notes is not None:
            notes.derive("net income", "not available: only ProfitLoss is tagged and the minority interests' "
                         "share of it is not", end)
        return None
    if notes is not None:
        notes.derive("net income", how, end)
    return Fact(value=value, first_value=value, tag=profit.tag, restated=False)


def _revenue(facts: _Facts, end: str, kind: str, utility: bool) -> Tuple[Optional[Fact], Optional[Fact]]:
    """(revenue fact, total `Revenues` fact) for the period."""
    total = facts.get(("Revenues",), end, MONEY, kind)
    revenue = (total if utility and total is not None else None) or facts.get(REVENUE, end, MONEY, kind)
    if revenue is None:
        interest, other = facts.get(NET_INTEREST_INCOME, end, MONEY, kind), facts.get(NONINTEREST_INCOME, end, MONEY, kind)
        if interest is not None and other is not None:
            revenue = Fact(value=interest.value + other.value, first_value=interest.value + other.value,
                           tag=f"{interest.tag} + {other.tag}", restated=False)
    return revenue, total


def _income_row(facts: _Facts, end: str, notes: _Notes, utility: bool = False) -> IncomeStatementRow:
    def field(name: str, chain: Sequence[str], unit: str = MONEY) -> Optional[float]:
        fact = facts.get(chain, end, unit, "year")
        notes.fact(name, end, fact, unit)
        return _value(fact)

    revenue_fact, total = _revenue(facts, end, "year", utility)
    notes.fact("revenue", end, revenue_fact)
    if revenue_fact is None:
        notes.derive("revenue", "not in the SEC data (the company uses its own tags)", end)
    elif " + " in revenue_fact.tag:
        notes.derive("revenue", f"derived as {revenue_fact.tag} (net revenue of a bank)", end)
    if revenue_fact is not None and total is not None and revenue_fact.tag != "Revenues" and total.value > 0 \
            and abs(total.value - revenue_fact.value) > 0.01 * total.value:
        notes.other.append(f"SEC EDGAR: FY{end[:4]} revenue uses {revenue_fact.tag} ({revenue_fact.value:,.0f}); "
                           f"total Revenues incl. other income is {total.value:,.0f}")
    return IncomeStatementRow(
        period_end=end,
        revenue=_value(revenue_fact),
        net_income=_value(_net_income(facts, end, "year", notes)),
        eps=field("EPS", EPS, PER_SHARE),
    )


def annual_data(companyfacts: Mapping[str, Any], splits: Sequence[Tuple[str, float]] = (),
                sic: Optional[str] = None) -> EdgarAnnualData:
    """
    Map a company's XBRL companyfacts to annual statement rows.

    Args:
        splits: (date 'YYYY-MM-DD', shares after / shares before) for every stock split, e.g. yfinance's
        sic: the company's SIC code (submissions); utilities take `Revenues` as revenue

    Raises:
        ValueError: the company does not report in USD (not supported yet)
    """
    facts = _Facts(companyfacts, splits)
    utility = bool(sic) and str(sic).isdigit() and int(sic) in UTILITY_SIC
    ends = fiscal_year_ends(facts)
    if not ends:
        currencies = sorted({c for tag in YEAR_END_TAGS for c in facts.currencies(tag)} - {PER_SHARE})
        if currencies and MONEY not in currencies:
            raise ValueError(f"statements are reported in {', '.join(currencies)}; only USD is supported")
    notes = _Notes()
    balance, income, dividends, operating = [], [], {}, {}
    for end in ends:
        income.append(_income_row(facts, end, notes, utility))
        row = _balance_row(facts, end, notes)
        if row is not None:
            balance.append(row)
        if row is not None and not row.shares_outstanding:
            notes.derive("share count", "not in the SEC data (the company uses its own tags); per-share figures N/A", end)
        if income[-1].eps is None:
            notes.derive("EPS", "not in the SEC data (the company uses its own tags); derived from net income / shares where possible", end)
        paid = facts.get(DIVIDENDS_PAID, end, MONEY, "year")
        notes.fact("dividends paid", end, paid)
        if paid is not None:
            dividends[end] = abs(paid.value)
        cash = facts.get(OPERATING_CASH_FLOW, end, MONEY, "year")
        notes.fact("operating cash flow", end, cash)
        if cash is not None:
            operating[end] = cash.value
    balance = _repair_share_scale(balance, notes)
    shares_by_year = {fiscal_year(row.period_end): row.shares_outstanding for row in reversed(balance) if row.shares_outstanding}
    if facts.scale_errors:
        notes.other.append("SEC EDGAR: figures a later filing tagged in thousands or millions as units were ignored: "
                           + ", ".join(sorted(facts.scale_errors)))
    # The company's current labelling convention (older filings are not always consistent: Walmart's
    # 10-Ks for FY2010-14 declared the year they started in, later ones the year they end in)
    declared = filer_fiscal_years(facts)
    if ends and ends[0] in declared and str(declared[ends[0]]) != fiscal_year(ends[0]):
        notes.other.append(f"SEC EDGAR: the company calls the year ending {ends[0]} fiscal {declared[ends[0]]}; "
                           f"years are labelled here by the fiscal year of their period end ({fiscal_year(ends[0])})")
    latest_cover = _cover_shares(facts, ends[0]) if ends else None
    return EdgarAnnualData(
        balance_sheets=tuple(balance),
        income_statements=tuple(income),
        dividends_paid=dividends,
        operating_cash_flow=operating,
        shares_by_year=shares_by_year,
        latest_cover_shares=latest_cover or 0.0,
        notes=notes.render(),
    )


@dataclass(frozen=True)
class EdgarPeriodicData:
    """Quarterly statement rows for TTM figures (newest first)."""
    balance_sheets: Tuple[BalanceSheetRow, ...]
    income_statements: Tuple[IncomeStatementRow, ...]
    notes: Tuple[str, ...]


def _fiscal_q4(facts: _Facts, year_end: str, chain: Sequence[str], unit: str,
               utility: bool = False) -> Optional[float]:
    """
    A fiscal fourth quarter, which 10-K filers do not tag as its own 3-month period: the year minus the
    nine months to the third quarter's end (from the third-quarter 10-Q).
    """
    if chain is REVENUE:
        year, _ = _revenue(facts, year_end, "year", utility)
    else:
        year = facts.get(chain, year_end, unit, "year")
    if year is None:
        return None
    start = _year_start(facts, year_end)
    if start is None:
        return None
    for tag in ([year.tag] + [t for t in chain if t != year.tag]):
        for nine_end, values in facts.series(tag, unit, "nine_months").items():
            rows = [r for r in facts.facts.get(GAAP, {}).get(tag, {}).get("units", {}).get(unit, [])
                    if r["end"] == nine_end and r.get("start") == start and r.get("form") in facts.forms]
            if rows and nine_end < year_end:
                latest = max(rows, key=lambda r: r["filed"])
                return year.value - latest["val"]
    return None


def _year_start(facts: _Facts, year_end: str) -> Optional[str]:
    """Start date of the fiscal year ending `year_end` (from any 1-year income fact)."""
    for tag in YEAR_END_TAGS:
        for unit in (MONEY, PER_SHARE):
            for row in facts.facts.get(GAAP, {}).get(tag, {}).get("units", {}).get(unit, []):
                if row["end"] == year_end and _lasts(row, "year"):
                    return row["start"]
    return None


def periodic_data(companyfacts: Mapping[str, Any], splits: Sequence[Tuple[str, float]] = (),
                  sic: Optional[str] = None, quarters: int = 8) -> EdgarPeriodicData:
    """
    The latest `quarters` fiscal quarters: 3-month income figures (fourth quarters derived as the year
    minus nine months) and the balance sheet at each quarter end, from 10-Q and 10-K filings.
    """
    facts = _Facts(companyfacts, splits, forms=PERIODIC_FORMS)
    utility = bool(sic) and str(sic).isdigit() and int(sic) in UTILITY_SIC
    year_ends = set(fiscal_year_ends(_Facts(companyfacts, splits)))
    quarter_ends = set()
    for tag in YEAR_END_TAGS:
        quarter_ends.update(facts.series(tag, MONEY, "quarter"))
    ends = sorted(quarter_ends | year_ends, reverse=True)[:quarters]
    notes = _Notes()
    income, balance = [], []
    for end in ends:
        revenue, _ = _revenue(facts, end, "quarter", utility)
        net_income = _net_income(facts, end, "quarter")
        eps = facts.get(EPS, end, PER_SHARE, "quarter")
        row_revenue, row_income = _value(revenue), _value(net_income)
        if end in year_ends and (revenue is None or net_income is None):
            row_revenue = row_revenue if revenue is not None else _fiscal_q4(facts, end, REVENUE, MONEY, utility)
            row_income = row_income if net_income is not None else _fiscal_q4(facts, end, NET_INCOME, MONEY)
            if row_revenue is not None or row_income is not None:
                notes.derive("fourth quarter", "derived as the fiscal year minus the first nine months", end)
        if row_revenue is not None or row_income is not None:
            income.append(IncomeStatementRow(period_end=end, revenue=row_revenue, net_income=row_income,
                                             eps=_value(eps)))
        row = _balance_row(facts, end, _Notes(), period_kind="year" if end in year_ends else "quarter")
        if row is not None:
            balance.append(row)
    balance = _repair_share_scale(balance, notes)
    return EdgarPeriodicData(balance_sheets=tuple(balance), income_statements=tuple(income),
                             notes=notes.render())


def merge_companyfacts(successor: Mapping[str, Any], predecessors: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """
    One companyfacts for a company and the filers it succeeded (holding-company reorganisations,
    config SEC_PREDECESSOR_CIKS). Fact rows are pooled per concept and unit; where both report a
    period, the successor's later filing wins through the usual latest-filed rule.
    """
    merged: Dict[str, Any] = {"cik": successor.get("cik"), "entityName": successor.get("entityName"), "facts": {}}
    for source in [successor, *predecessors]:
        for taxonomy, concepts in source.get("facts", {}).items():
            target = merged["facts"].setdefault(taxonomy, {})
            for tag, concept in concepts.items():
                units = target.setdefault(tag, {"units": {}})["units"]
                for unit, rows in concept.get("units", {}).items():
                    units.setdefault(unit, []).extend(rows)
    return merged


def exhibit_filename(sgml_header: str, exhibit_type: str) -> Optional[str]:
    """The file name of a filing's `exhibit_type` document (e.g. EX-31.1) from its SGML header."""
    text = html.unescape(sgml_header)
    match = re.search(r"<TYPE>" + re.escape(exhibit_type) + r"\b.*?<FILENAME>([^\s<]+)", text, re.S)
    return match.group(1) if match else None


def unreported_annual_filings(annual: EdgarAnnualData, submissions: Mapping[str, Any]) -> List[Tuple[str, str, str]]:
    """10-Ks filed for years after the latest one in companyfacts (Seneca's FY2026 10-K was never in it)."""
    latest = annual.income_statements[0].period_end if annual.income_statements else ""
    return [filing for filing in annual_filings(submissions) if filing[0] > latest
            and (not latest or _days(latest, filing[0]) > MIN_DAYS_BETWEEN_YEAR_ENDS)][:MAX_UNREPORTED_FILINGS]


def instance_companyfacts(instance_xml: str, form: str, filed: str, accession: str) -> Dict[str, Any]:
    """A filing's XBRL instance as companyfacts: company-wide figures only, as companyfacts itself keeps."""
    def local(name: str) -> str:
        return name.split("}")[-1]

    root = ET.fromstring(instance_xml)
    periods: Dict[Optional[str], Tuple[Optional[str], str]] = {}
    for context in (e for e in root if local(e.tag) == "context"):
        if any(local(e.tag) in ("explicitMember", "typedMember") for e in context.iter()):
            continue
        dates = {local(e.tag): (e.text or "").strip() for e in context.iter()}
        if dates.get("instant"):
            periods[context.get("id")] = (None, dates["instant"])
        elif dates.get("endDate"):
            periods[context.get("id")] = (dates.get("startDate"), dates["endDate"])
    units: Dict[Optional[str], str] = {}
    for unit in (e for e in root if local(e.tag) == "unit"):
        measures = [(e.text or "").strip().split(":")[-1] for e in unit.iter() if local(e.tag) == "measure"]
        units[unit.get("id")] = "/".join(measures)
    facts: Dict[str, Dict[str, Any]] = {GAAP: {}, DEI: {}}
    for fact in root:
        taxonomy = next((t for t in (GAAP, DEI) if f"/{t}/" in fact.tag), None)
        period, unit = periods.get(fact.get("contextRef")), units.get(fact.get("unitRef"))
        if taxonomy is None or period is None or unit is None or not (fact.text or "").strip():
            continue
        try:
            value = float(fact.text)
        except ValueError:
            continue
        row = {"end": period[1], "val": value, "filed": filed, "form": form, "accn": accession}
        if period[0]:
            row["start"] = period[0]
        rows = facts[taxonomy].setdefault(local(fact.tag), {"units": {}})["units"].setdefault(unit, [])
        if row not in rows:
            rows.append(row)
    return {"facts": facts}


def missing_latest_shares(annual: EdgarAnnualData) -> bool:
    """No share count for the latest year: companyfacts leaves out figures reported per share class."""
    return bool(annual.balance_sheets) and not annual.balance_sheets[0].shares_outstanding


def annual_filings(submissions: Mapping[str, Any]) -> List[Tuple[str, str, str]]:
    """(period end, filing date, accession number) of each 10-K with XBRL, newest first."""
    recent = submissions.get("filings", {}).get("recent", {})
    return [(end, filed, accession) for form, end, filed, accession, xbrl in
            zip(recent.get("form", []), recent.get("reportDate", []), recent.get("filingDate", []),
                recent.get("accessionNumber", []), recent.get("isXBRL", []))
            if form == "10-K" and xbrl and end]


def instance_filename(names: Sequence[str]) -> Optional[str]:
    """A filing's XBRL instance among its files: name_htm.xml (inline XBRL), else ticker-YYYYMMDD.xml."""
    return next((n for n in names if n.endswith("_htm.xml")),
                next((n for n in names if re.fullmatch(r"[A-Za-z0-9-]+-\d{8}\.xml", n)), None))


def class_share_counts(instance_xml: str) -> Tuple[Dict[str, float], Optional[float]]:
    """
    From a filing's XBRL instance: {balance date: shares outstanding, all classes added}, and the cover page's
    total of the classes (None when not reported per class). Only dates with two or more classes count.
    """
    def local(name: str) -> str:
        return name.split("}")[-1]

    root = ET.fromstring(instance_xml)
    contexts = {}
    for context in (e for e in root if local(e.tag) == "context"):
        members = [m for m in context.iter() if local(m.tag) == "explicitMember"]
        instant = next((e.text for e in context.iter() if local(e.tag) == "instant"), None)
        if len(members) == 1 and members[0].get("dimension", "").endswith(CLASS_AXIS) and instant:
            contexts[context.get("id")] = (instant.strip(), members[0].text.strip())
    outstanding: Dict[Tuple[str, str], float] = {}
    cover: Dict[Tuple[str, str], float] = {}
    for fact in root:
        if fact.get("contextRef") not in contexts or not (fact.text or "").strip():
            continue
        target = {SHARES_OUTSTANDING[0]: outstanding, COVER_SHARES[0]: cover}.get(local(fact.tag))
        if target is not None:
            target[contexts[fact.get("contextRef")]] = float(fact.text)

    def by_date(values: Mapping[Tuple[str, str], float]) -> Dict[str, List[float]]:
        dates: Dict[str, List[float]] = {}
        for (date, _), value in values.items():
            dates.setdefault(date, []).append(value)
        return {date: counts for date, counts in dates.items() if len(counts) >= 2}

    latest_cover = by_date(cover)
    return ({date: sum(counts) for date, counts in by_date(outstanding).items()},
            sum(latest_cover[max(latest_cover)]) if latest_cover else None)


def split_adjusted_shares(companyfacts: Mapping[str, Any], splits: Sequence[Tuple[str, float]], filed: str, count: float) -> float:
    """A share count from a filing, on today's share basis."""
    return _Facts(companyfacts, splits).adjusted(SHARES, filed, count)


def without_other_share_bases(annual: EdgarAnnualData, total: float) -> EdgarAnnualData:
    """
    Clear yearly counts far below today's total: another basis (Berkshire FY2011: 1.65M Class A equivalents, against
    2.1bn Class B equivalents), which would make per-share history incomparable with the price.
    """
    rows = tuple(replace(row, shares_outstanding=None)
                 if row.shares_outstanding and row.shares_outstanding * MAX_DERIVED_BELOW_COVER < total else row
                 for row in annual.balance_sheets)
    return replace(annual, balance_sheets=rows, shares_by_year={
        fiscal_year(row.period_end): row.shares_outstanding for row in reversed(rows) if row.shares_outstanding})


def with_shares_for_quarters(periodic: EdgarPeriodicData, shares: float) -> EdgarPeriodicData:
    """Quarters without a share count take `shares`, for the TTM per-share figures."""
    return replace(periodic, balance_sheets=tuple(row if row.shares_outstanding else replace(row, shares_outstanding=shares)
                                                  for row in periodic.balance_sheets))


def with_class_shares(annual: EdgarAnnualData, periodic: EdgarPeriodicData, totals: Mapping[str, float],
                      cover: Optional[float]) -> Tuple[EdgarAnnualData, EdgarPeriodicData]:
    """
    Annual rows with the share totals of all classes (replacing a count that is one class only, as Village's
    untagged one is: 4.2M Class B of 14.8M). Quarters without a count take the latest year's, for the TTM per-share
    figures. Classes are added one for one: dollar figures per class differ slightly at some of these companies.
    """
    notes = _Notes()
    balance = _repair_share_scale([replace(row, shares_outstanding=totals.get(row.period_end, row.shares_outstanding))
                                   for row in annual.balance_sheets], notes)
    latest = balance[0].shares_outstanding if balance else None
    notes.other.append("SEC EDGAR: share counts are per class in this company's filings: all classes added one for "
                       "one, from each 10-K's XBRL (dividends and voting rights can differ between classes; EPS "
                       "derived on the total)")
    return (replace(annual, balance_sheets=tuple(balance), latest_cover_shares=cover or annual.latest_cover_shares,
                    shares_by_year={fiscal_year(row.period_end): row.shares_outstanding
                                    for row in reversed(balance) if row.shares_outstanding},
                    notes=annual.notes + notes.render()),
            with_shares_for_quarters(periodic, latest))


def certifying_officer(exhibit_html: str) -> Optional[str]:
    """The signer of a Sarbanes-Oxley s.302 certification: "I, <name>, certify that ..."."""
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", exhibit_html)))
    match = re.search(r"\bI,\s+([A-Z][^,]{2,80}?),\s+certify", text)
    return match.group(1).strip() if match else None
