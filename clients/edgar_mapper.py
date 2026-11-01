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
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from core.fundamentals import BalanceSheetRow, IncomeStatementRow

ANNUAL_FORMS = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})
PERIODIC_FORMS = ANNUAL_FORMS | {"10-Q", "10-Q/A"}
# Duration windows in days: a fiscal year, a quarter, nine months year-to-date
DURATIONS = {"year": (350, 380), "quarter": (80, 100), "nine_months": (260, 285)}
GAAP, DEI = "us-gaap", "dei"
MONEY, PER_SHARE, SHARES = "USD", "USD/shares", "shares"

# Field -> tag chain (first tag with a value for the year wins)
REVENUE = ("RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
           "SalesRevenueNet", "SalesRevenueGoodsNet", "Revenues", "RevenuesNetOfInterestExpense")
NET_INCOME = ("NetIncomeLossAvailableToCommonStockholdersBasic", "NetIncomeLoss")
EPS = ("EarningsPerShareBasic", "EarningsPerShareBasicAndDiluted")
EQUITY = ("StockholdersEquity",)
EQUITY_INCL_NCI = ("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",)
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
DEBT_CURRENT = ("DebtCurrent",)
SHORT_BORROWINGS, COMMERCIAL_PAPER = ("ShortTermBorrowings",), ("CommercialPaper",)
LTD_CURRENT = ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent")
INVENTORY = ("InventoryNet",)
UTILITY_INVENTORY = ("EnergyRelatedInventoryNaturalGasInStorage", "EnergyRelatedInventoryOtherFossilFuel",
                     "EnergyRelatedInventoryCoal", "EnergyRelatedInventoryPropaneGas", "OtherInventorySupplies")
# Energy companies tagging a total (ExxonMobil: crude oil, products and merchandise + materials and supplies)
ENERGY_INVENTORY_TOTAL = ("EnergyRelatedInventory",)
SUPPLIES_INVENTORY = ("OtherInventorySupplies", "InventoryPartsAndComponentsNetOfReserves")
PREFERRED = ("PreferredStockValue", "PreferredStockValueOutstanding")
SHARES_OUTSTANDING = ("CommonStockSharesOutstanding",)
SHARES_ISSUED, TREASURY_SHARES = ("CommonStockSharesIssued",), ("TreasuryStockCommonShares", "TreasuryStockShares")
COVER_SHARES = ("EntityCommonStockSharesOutstanding",)
WEIGHTED_SHARES = ("WeightedAverageNumberOfSharesOutstandingBasic",)
UTILITY_SIC = range(4900, 5000)
DIVIDENDS_PAID = ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends", "PaymentsOfOrdinaryDividends")
YEAR_END_TAGS = ("NetIncomeLoss", "ProfitLoss", "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                 "EarningsPerShareBasic")

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
    """Period ends of the company's fiscal years (from 1-year income facts in annual filings), newest first."""
    ends = set()
    for tag in YEAR_END_TAGS:
        for unit in (MONEY, PER_SHARE):
            ends.update(facts.series(tag, unit, "year"))
    return sorted(ends, reverse=True)


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
    values = [v for v in (indefinite, other) if v is not None]
    return (sum(values) if values else None), used + other_used


_INTANGIBLE_TAG = re.compile(r"Intangible|Trademark|FranchiseRights|LicenseAgreements|TradeNames")
_NOT_A_BALANCE = re.compile(r"Tax|Amortization|Impairment|Disposal|Acquired|Useful|Payments|Proceeds|Gross|"
                            r"Accumulated|Expected|Increase|Decrease|Weighted|Percentage|Goodwill")
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

    long_term_debt = field("long-term debt", LONG_TERM_DEBT)
    includes_current = False
    if long_term_debt is None:
        total_fact = facts.get(LONG_TERM_DEBT_TOTAL, end, MONEY, "instant")
        notes.fact("long-term debt", end, total_fact)
        if total_fact is not None:
            long_term_debt, includes_current = total_fact.value, True
            notes.derive("long-term debt", f"{total_fact.tag} used (includes the current portion)", end)

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
        if derived is not None and not (rounded and cover is not None):
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


def _revenue(facts: _Facts, end: str, kind: str, utility: bool) -> Tuple[Optional[Fact], Optional[Fact]]:
    """(revenue fact, total `Revenues` fact) for the period."""
    total = facts.get(("Revenues",), end, MONEY, kind)
    return (total if utility and total is not None else None) or facts.get(REVENUE, end, MONEY, kind), total


def _income_row(facts: _Facts, end: str, notes: _Notes, utility: bool = False) -> IncomeStatementRow:
    def field(name: str, chain: Sequence[str], unit: str = MONEY) -> Optional[float]:
        fact = facts.get(chain, end, unit, "year")
        notes.fact(name, end, fact, unit)
        return _value(fact)

    revenue_fact, total = _revenue(facts, end, "year", utility)
    notes.fact("revenue", end, revenue_fact)
    if revenue_fact is not None and total is not None and revenue_fact.tag != "Revenues" and total.value > 0 \
            and abs(total.value - revenue_fact.value) > 0.01 * total.value:
        notes.other.append(f"SEC EDGAR: FY{end[:4]} revenue uses {revenue_fact.tag} ({revenue_fact.value:,.0f}); "
                           f"total Revenues incl. other income is {total.value:,.0f}")
    return IncomeStatementRow(
        period_end=end,
        revenue=_value(revenue_fact),
        net_income=field("net income", NET_INCOME),
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
    balance, income, dividends, shares_by_year = [], [], {}, {}
    for end in ends:
        income.append(_income_row(facts, end, notes, utility))
        row = _balance_row(facts, end, notes)
        if row is not None:
            balance.append(row)
            if row.shares_outstanding:
                shares_by_year[end[:4]] = row.shares_outstanding
        if row is not None and not row.shares_outstanding:
            notes.derive("share count", "not in the SEC data (the company uses its own tags); per-share figures N/A", end)
        if income[-1].eps is None:
            notes.derive("EPS", "not in the SEC data (the company uses its own tags); derived from net income / shares where possible", end)
        paid = facts.get(DIVIDENDS_PAID, end, MONEY, "year")
        notes.fact("dividends paid", end, paid)
        if paid is not None:
            dividends[end] = abs(paid.value)
    latest_cover = _cover_shares(facts, ends[0]) if ends else None
    return EdgarAnnualData(
        balance_sheets=tuple(balance),
        income_statements=tuple(income),
        dividends_paid=dividends,
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
        net_income = facts.get(NET_INCOME, end, MONEY, "quarter")
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
    return EdgarPeriodicData(balance_sheets=tuple(balance), income_statements=tuple(income),
                             notes=notes.render())
