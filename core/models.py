"""
Typed models for the data passed between layers (decision D2, M7).

Core produces these frozen dataclasses; `to_dict()` gives exactly the dict shape the pipeline
has always used (docs/CODEBASE_GUIDE.md §4), and `from_dict()` reads it. Models are read by
attribute only; functions that also receive dicts (unit tests, assembly) normalise with `from_dict()`,
which passes models through.

Conventions:
- A field holding `MISSING` means "key absent" (e.g. a dividend-only history row has no balance
  sheet keys); `to_dict()` leaves such keys out, so round trips are exact.
- `NA` ("N/A") is today's marker for a value that cannot be computed; numeric fields that can be
  unavailable are typed `Number` (float or "N/A").
- Sequences are tuples on the model and lists in `to_dict()`.
"""

from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Dict, Literal, Mapping, Optional, Tuple, Type, Union


class _Missing:
    """Sentinel for a key absent from the dict form."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING: Any = _Missing()


def or_default(value: Any, default: Any) -> Any:
    """`default` when `value` is MISSING (only then: 0, "" and None are kept)."""
    return default if value is MISSING else value

NA = Literal["N/A"]
Number = Union[float, NA]


def _dump(value: Any) -> Any:
    if isinstance(value, Model):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_dump(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _dump(item) for key, item in value.items()}
    return value


def _load(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_load(item) for item in value)
    return value


@dataclass(frozen=True)
class Model:
    """Base: exact dict round trip. Keys the model does not declare are kept in `extra`."""

    extra: Mapping[str, Any] = field(default_factory=dict, compare=False, repr=False)

    # field name -> model class, for nested models / {key: model} mappings
    _nested: ClassVar[Dict[str, Type["Model"]]] = {}
    _nested_maps: ClassVar[Dict[str, Type["Model"]]] = {}

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for f in fields(self):
            if f.name == 'extra':
                continue
            value = getattr(self, f.name)
            if value is MISSING:
                continue
            out[f.name] = _dump(value)
        out.update({key: _dump(value) for key, value in self.extra.items()})
        return out

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]):
        """The model for a dict; `None` or a model is returned as is (lets callers pass either)."""
        if data is None or isinstance(data, cls):
            return data
        names = {f.name for f in fields(cls)} - {'extra'}
        kwargs: Dict[str, Any] = {}
        for name in names:
            if name not in data:
                continue
            value = data[name]
            if name in cls._nested and isinstance(value, Mapping):
                value = cls._nested[name].from_dict(value)
            elif name in cls._nested_maps and isinstance(value, Mapping):
                value = {key: cls._nested_maps[name].from_dict(item) if isinstance(item, Mapping) else item
                         for key, item in value.items()}
            else:
                value = _load(value)
            kwargs[name] = value
        extra = {key: value for key, value in data.items() if key not in names}
        return cls(extra=extra, **kwargs)



# --- Graham calculator results (GrahamCalculator.compute_all) -------------------------------

@dataclass(frozen=True)
class EPVDetails(Model):
    """Earnings power value: average net income (7-10 years) / COST_OF_CAPITAL (F3: N/A, not 0).
    Per share: average of each year's EPS / COST_OF_CAPITAL (GRAHAM_METHODOLOGY §2.4, F22)."""
    epv: Number = MISSING
    epv_per_share: Number = MISSING
    normalized_earnings: Number = MISSING
    normalized_eps: Number = MISSING                 # average EPS of years_included, or "N/A"
    eps_values: Tuple[Optional[float], ...] = MISSING   # each year's EPS (None = not available)
    epv_per_share_reason: str = MISSING              # why epv_per_share is "N/A"
    years_used: int = MISSING
    years_included: Tuple[str, ...] = MISSING        # present when EPV is available
    net_incomes: Tuple[float, ...] = MISSING         # present when EPV is available
    cost_of_capital: float = MISSING
    unavailable_reason: str = MISSING                # present when EPV is unavailable


@dataclass(frozen=True)
class MarginOfSafetyDetails(Model):
    mos_percentage: Number = MISSING
    intrinsic_value_used: Number = MISSING
    limiting_factor: str = MISSING                   # "Normalized Graham Number", "EPV" or "N/A"
    normalized_graham_number: Number = MISSING
    epv_per_share: Number = MISSING
    note: Optional[str] = MISSING                    # why an anchor is missing or the value is 0


@dataclass(frozen=True)
class NCADetails(Model):
    """Working capital and the defensive debt coverage (GRAHAM_METHODOLOGY §4.2)."""
    current_assets: Number = MISSING
    current_liabilities: Number = MISSING
    nca: Number = MISSING
    long_term_debt: Number = MISSING
    debt_coverage_ratio: Number = MISSING
    debt_coverage_pct: str = MISSING                 # "X.XX%" or "N/A"
    warnings: Tuple[str, ...] = MISSING


@dataclass(frozen=True)
class CurrentRatio(Model):
    ratio: Number = MISSING
    fiscal_year_end: Optional[str] = MISSING


@dataclass(frozen=True)
class ThreeYearAvgPE(Model):
    three_year_avg_eps: Number = MISSING
    pe_on_avg: Number = MISSING
    years_used: Tuple[str, ...] = MISSING


@dataclass(frozen=True)
class CombinedPEPBTest(Model):
    """Defensive criterion 4.7 multiples: P/E on 3-year average EPS x P/B on tangible book."""
    pe_ratio: Number = MISSING
    pb_ratio: Number = MISSING
    product: Number = MISSING
    result: str = MISSING                            # "PASS", "FAIL" or "N/A"


@dataclass(frozen=True)
class GrahamResult(Model):
    """Everything GrahamCalculator.compute_all returns (docs/CODEBASE_GUIDE.md §4.3)."""
    tbvps: Number = MISSING
    verdict: str = MISSING
    verdict_reason: str = MISSING
    public_utility: bool = MISSING
    graham_number: Number = MISSING
    normalized_graham_number: Number = MISSING
    epv: Number = MISSING
    epv_details: EPVDetails = MISSING
    net_net_value: Number = MISSING
    margin_of_safety: Number = MISSING
    margin_of_safety_details: MarginOfSafetyDetails = MISSING
    nca_details: NCADetails = MISSING
    current_ratio: CurrentRatio = MISSING
    quick_ratio: Number = MISSING
    three_year_avg_pe: ThreeYearAvgPE = MISSING
    combined_pe_pb_test: CombinedPEPBTest = MISSING
    defensive_tests: Mapping[str, str] = MISSING     # criterion -> "PASS" / "FAIL" / "N/A ..."
    enterprising_tests: Mapping[str, str] = MISSING
    warnings: Tuple[str, ...] = MISSING

    _nested: ClassVar[Dict[str, Type[Model]]] = {
        'epv_details': EPVDetails, 'margin_of_safety_details': MarginOfSafetyDetails,
        'nca_details': NCADetails, 'current_ratio': CurrentRatio,
        'three_year_avg_pe': ThreeYearAvgPE, 'combined_pe_pb_test': CombinedPEPBTest,
    }


# --- TTM results (TTMCalculator.compute_all) -------------------------------------------------

@dataclass(frozen=True)
class TTMResult(Model):
    """docs/CODEBASE_GUIDE.md §4.4; every value "N/A" when no TTM metrics could be built."""
    ttm_revenue: Number = MISSING
    ttm_net_income: Number = MISSING
    ttm_eps: Number = MISSING
    ttm_graham_number: Number = MISSING
    ttm_tbvps: Number = MISSING
    ttm_net_net: Number = MISSING
    ttm_margin_of_safety: Number = MISSING
    ttm_pe_ratio: Number = MISSING
    ttm_pb_ratio: Number = MISSING
    reporting_frequency: str = MISSING               # 'quarterly' | 'semi-annual' | 'irregular'
    date_range: str = MISSING
    periods_used: Tuple[str, ...] = MISSING
    currency: str = MISSING
    warnings: Tuple[str, ...] = MISSING


# --- Assembled financial data (FinancialDataAssembler.assemble) ------------------------------

@dataclass(frozen=True)
class HistoryRow(Model):
    """One fiscal year (docs/CODEBASE_GUIDE.md §4.2); dividend-only rows carry fewer keys."""
    revenue: float = MISSING
    net_income: float = MISSING
    eps: float = MISSING
    dividend: float = MISSING                        # per share, or a payment count (is_dividend_amounts)
    total_equity: float = MISSING
    intangible_assets: float = MISSING
    goodwill: float = MISSING
    current_assets: float = MISSING
    current_liabilities: float = MISSING
    total_liabilities: float = MISSING
    long_term_debt: float = MISSING
    total_assets: float = MISSING
    total_debt: float = MISSING
    inventory: Optional[float] = MISSING             # None = not reported
    claims_outside_equity: float = MISSING
    preferred_stock: float = MISSING                 # preferred stock inside equity (deducted for the common)
    shares_outstanding: float = MISSING
    wcps: Number = MISSING
    payout_ratio: str = MISSING                      # "34.0%" or "N/A"
    year_end_price: Optional[float] = MISSING        # added by core.historical_prices
    operating_cash_flow: float = MISSING             # annual net cash from operations (cash-flow currency converted); absent if not reported


@dataclass(frozen=True)
class FinancialData(Model):
    """docs/CODEBASE_GUIDE.md §4.1. Keys not declared here are kept in `extra`."""
    ticker: str = MISSING
    exchange: str = MISSING
    currency: str = MISSING                          # unified calculation currency
    original_stock_currency: str = MISSING
    financials_currency: str = MISSING
    dividend_currency: str = MISSING
    price: float = MISSING
    data_source: str = MISSING                       # fundamentals vendor, e.g. "EODHD"
    price_source: str = MISSING
    price_quote_currency: Optional[str] = MISSING
    price_currency_before_fx: Optional[str] = MISSING
    fx_rate_used: Optional[float] = MISSING
    historical_fx_rates: Mapping[str, Optional[float]] = MISSING
    dividend_source: str = MISSING
    dividend_sources: Mapping[str, str] = MISSING
    ceo_name: str = MISSING
    sector: Optional[str] = MISSING
    industry: Optional[str] = MISSING
    employees: int = MISSING
    history: Mapping[str, HistoryRow] = MISSING
    warnings: Tuple[str, ...] = MISSING
    forward_dividend_rate: Optional[float] = MISSING
    is_dividend_amounts: bool = MISSING
    ttm_dividend: float = MISSING
    ttm_dividend_payments: Tuple[Mapping[str, Any], ...] = MISSING
    ttm_dividend_currency: Optional[str] = MISSING
    dividend_per_share: float = MISSING
    dividend_yield: float = MISSING
    pe_ratio: float = MISSING
    book_value_per_share: float = MISSING
    roe: float = MISSING
    roa: float = MISSING
    profit_margin: float = MISSING
    price_to_book: float = MISSING
    enterprise_value: float = MISSING
    insider_ownership: float = MISSING
    institutional_ownership: float = MISSING
    beta: float = MISSING
    week_52_high: float = MISSING
    week_52_low: float = MISSING
    average_volume: float = MISSING
    api_last_update: str = MISSING
    quarterly_data: Mapping[str, Mapping[str, Mapping[str, Any]]] = MISSING

    _nested_maps: ClassVar[Dict[str, Type[Model]]] = {'history': HistoryRow}
