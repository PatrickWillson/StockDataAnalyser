"""
Characterisation tests for FinancialDataProcessor functions that had no direct tests:
extract_ceo_name, parse_income_statement, calculate_ttm_dividend, validate_data_quality.

These pin CURRENT behaviour, including known defects (marked "Known defect"), so the
refactor cannot change them silently. When a defect is fixed deliberately, update the
marked assertion in the same commit.
"""

from datetime import datetime, timezone

import pytest

from core.financial_data_processor import FinancialDataProcessor


def _officers(*officers):
    return {"General": {"Officers": {str(i): o for i, o in enumerate(officers)}}}


class TestExtractCeoName:
    def test_finds_chief_executive_by_title(self):
        data = _officers({"Name": "A", "Title": "CFO"}, {"Name": "B", "Title": "Chief Executive Officer"})
        assert FinancialDataProcessor.extract_ceo_name(data) == "B"

    def test_title_match_is_case_insensitive_and_matches_ceo_abbreviation(self):
        data = _officers({"Name": "A", "Title": "CFO"}, {"Name": "B", "Title": "Co-Founder & ceo"})
        assert FinancialDataProcessor.extract_ceo_name(data) == "B"

    def test_falls_back_to_first_officer_when_no_ceo_title(self):
        data = _officers({"Name": "A", "Title": "Chairman"}, {"Name": "B", "Title": "CFO"})
        assert FinancialDataProcessor.extract_ceo_name(data) == "A"

    def test_missing_name_returns_na(self):
        assert FinancialDataProcessor.extract_ceo_name(_officers({"Title": "CEO"})) == "N/A"

    @pytest.mark.parametrize("officers", [None, {}, [], [{"Name": "A", "Title": "CEO"}], "text"])
    def test_missing_or_non_dict_officers_return_na(self, officers):
        assert FinancialDataProcessor.extract_ceo_name({"General": {"Officers": officers}}) == "N/A"

    def test_non_dict_officer_entries_are_skipped(self):
        data = {"General": {"Officers": {"0": {"Name": "A", "Title": "CFO"}, "1": "junk",
                                         "2": {"Name": "C", "Title": "CEO"}}}}
        assert FinancialDataProcessor.extract_ceo_name(data) == "C"

    def test_non_dict_first_officer_returns_na(self):
        data = {"General": {"Officers": {"0": "junk", "1": {"Name": "B", "Title": "CFO"}}}}
        assert FinancialDataProcessor.extract_ceo_name(data) == "N/A"

    def test_no_general_section_returns_na(self):
        assert FinancialDataProcessor.extract_ceo_name({}) == "N/A"

    def test_known_defect_ceo_substring_matches_unrelated_titles(self):
        # Known defect: 'ceo' is matched as a substring, so e.g. "herbaCEOus" matches
        data = _officers({"Name": "A", "Title": "Chairman"}, {"Name": "B", "Title": "Head of Herbaceous Products"})
        assert FinancialDataProcessor.extract_ceo_name(data) == "B"

    def test_known_defect_null_title_raises(self):
        # Known defect: a JSON null Title raises AttributeError (only KeyError/TypeError are caught)
        with pytest.raises(AttributeError):
            FinancialDataProcessor.extract_ceo_name(_officers({"Name": "A", "Title": None}))


def _income(yearly):
    return {"Financials": {"Income_Statement": {"yearly": yearly}}}


class TestParseIncomeStatement:
    @pytest.fixture
    def processor(self):
        return FinancialDataProcessor(currency_converter=object())

    def test_maps_fields_and_sorts_newest_first(self, processor):
        result = processor.parse_income_statement(_income({
            "2022-12-31": {"totalRevenue": 100, "netIncomeFromContinuingOps": 10, "eps": 1.0},
            "2023-12-31": {"totalRevenue": 120, "netIncomeFromContinuingOps": 12, "eps": 1.2},
        }))
        assert list(result) == ["2023-12-31", "2022-12-31"]
        assert result["2023-12-31"] == {"revenue": 120.0, "net_income": 12.0, "eps": 1.2}

    @pytest.mark.parametrize("missing_eps", [None, "NA", ""])
    def test_eps_falls_back_to_basic_eps_then_eps_basic(self, processor, missing_eps):
        result = processor.parse_income_statement(_income({
            "2023-12-31": {"eps": missing_eps, "basicEPS": None, "epsBasic": 2.5, "netIncome": 5},
        }))
        assert result["2023-12-31"]["eps"] == 2.5

    def test_basic_eps_preferred_over_eps_basic(self, processor):
        result = processor.parse_income_statement(_income({
            "2023-12-31": {"eps": None, "basicEPS": 3.0, "epsBasic": 2.5},
        }))
        assert result["2023-12-31"]["eps"] == 3.0

    def test_zero_eps_is_kept_not_replaced_by_fallback(self, processor):
        result = processor.parse_income_statement(_income({
            "2023-12-31": {"eps": 0, "basicEPS": 3.0},
        }))
        assert result["2023-12-31"]["eps"] == 0.0

    @pytest.mark.parametrize("missing_ni", [None, "NA", ""])
    def test_net_income_prefers_continuing_ops_then_net_income(self, processor, missing_ni):
        result = processor.parse_income_statement(_income({
            "2023-12-31": {"netIncomeFromContinuingOps": missing_ni, "netIncome": 7},
        }))
        assert result["2023-12-31"]["net_income"] == 7.0

    def test_continuing_ops_used_when_both_present(self, processor):
        result = processor.parse_income_statement(_income({
            "2023-12-31": {"netIncomeFromContinuingOps": 9, "netIncome": 7},
        }))
        assert result["2023-12-31"]["net_income"] == 9.0

    def test_missing_values_become_zero(self, processor):
        result = processor.parse_income_statement(_income({"2023-12-31": {}}))
        assert result["2023-12-31"] == {"revenue": 0.0, "net_income": 0.0, "eps": 0.0}

    @pytest.mark.parametrize("data", [{}, _income({}), _income([]), _income(["not-a-dict"]),
                                      {"Financials": {"Income_Statement": {}}}])
    def test_missing_or_malformed_section_returns_empty(self, processor, data):
        assert processor.parse_income_statement(data) == {}


class TestCalculateTtmDividend:
    @pytest.fixture
    def processor(self):
        return FinancialDataProcessor(currency_converter=object())

    @pytest.mark.parametrize("data", [None, []])
    def test_no_data_returns_zero_and_usd(self, processor, data):
        assert processor.calculate_ttm_dividend(data) == (0.0, [], "USD")

    def test_sums_payments_within_365_days_of_reference_date(self, processor):
        total, payments, currency = processor.calculate_ttm_dividend([
            {"paymentDate": "2024-02-15", "value": 0.25, "currency": "GBP"},
            {"paymentDate": "2023-03-01", "value": 0.25, "currency": "GBP"},  # exactly the cutoff: included
            {"paymentDate": "2023-02-28", "value": 0.25, "currency": "GBP"},  # one day too old
        ], reference_date="2024-02-29")
        assert total == 0.5
        assert [p["date"] for p in payments] == ["2024-02-15", "2023-03-01"]
        assert currency == "GBP"

    def test_uses_ex_date_when_payment_date_missing(self, processor):
        total, payments, _ = processor.calculate_ttm_dividend(
            [{"date": "2024-01-10", "value": 0.4}], reference_date="2024-02-29")
        assert total == 0.4
        assert payments == [{"date": "2024-01-10", "value": 0.4, "currency": "USD"}]

    def test_skips_zero_negative_and_missing_values(self, processor):
        total, payments, _ = processor.calculate_ttm_dividend([
            {"paymentDate": "2024-01-10", "value": 0},
            {"paymentDate": "2024-01-11", "value": -1},
            {"paymentDate": "2024-01-12"},
            {"paymentDate": "2024-01-13", "value": "NA"},
        ], reference_date="2024-02-29")
        assert (total, payments) == (0.0, [])

    def test_payments_sorted_newest_first(self, processor):
        _, payments, _ = processor.calculate_ttm_dividend([
            {"paymentDate": "2023-06-01", "value": 1.0},
            {"paymentDate": "2024-01-01", "value": 1.0},
            {"paymentDate": "2023-09-01", "value": 1.0},
        ], reference_date="2024-02-29")
        assert [p["date"] for p in payments] == ["2024-01-01", "2023-09-01", "2023-06-01"]

    def test_currency_taken_from_first_record_only(self, processor):
        _, payments, currency = processor.calculate_ttm_dividend([
            {"paymentDate": "2024-01-01", "value": 1.0, "currency": "EUR"},
            {"paymentDate": "2023-12-01", "value": 1.0, "currency": "USD"},
        ], reference_date="2024-02-29")
        assert currency == "EUR"
        assert [p["currency"] for p in payments] == ["EUR", "USD"]

    def test_known_defect_future_payments_are_included(self, processor):
        # Known defect: there is no upper date bound, so declared future payments count
        total, _, _ = processor.calculate_ttm_dividend(
            [{"paymentDate": "2025-06-01", "value": 1.0}], reference_date="2024-02-29")
        assert total == 1.0

    @pytest.mark.time_machine(datetime(2024, 2, 29, 12, 0, tzinfo=timezone.utc), tick=False)
    def test_invalid_reference_date_falls_back_to_today(self, processor):
        total, _, _ = processor.calculate_ttm_dividend([
            {"paymentDate": "2024-01-01", "value": 1.0},
            {"paymentDate": "2022-01-01", "value": 1.0},
        ], reference_date="29/02/2024")
        assert total == 1.0


def _year(**fields):
    base = {"revenue": 100.0, "net_income": 10.0, "eps": 1.0, "total_equity": 50.0}
    base.update(fields)
    return base


class TestValidateDataQuality:
    def _warnings(self, history):
        warnings = []
        FinancialDataProcessor.validate_data_quality(history, warnings)
        return warnings

    def test_empty_history(self):
        assert self._warnings({}) == ["No financial history data available"]

    def test_fewer_than_ten_years_warns(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(9)}
        assert self._warnings(history) == [
            "Insufficient History Warning: Only 9 years of data available (minimum 10 recommended)"]

    def test_ten_complete_consecutive_years_has_no_warnings(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(10)}
        assert self._warnings(history) == []

    def test_zero_valued_required_fields_reported_as_missing(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(10)}
        history["2023-12-31"] = _year(revenue=0.0, eps=0.0)
        assert self._warnings(history) == ["Year 2023-12-31: Incomplete data (missing: revenue, eps)"]

    def test_missing_keys_reported_as_missing(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(10)}
        history["2020-12-31"] = {"dividend": 1.0}
        assert self._warnings(history) == [
            "Year 2020-12-31: Incomplete data (missing: revenue, net_income, eps, total_equity)"]

    def test_gap_check_skipped_for_three_or_fewer_years(self):
        history = {f"{year}-12-31": _year() for year in (2023, 2019, 2015)}
        assert self._warnings(history) == [
            "Insufficient History Warning: Only 3 years of data available (minimum 10 recommended)"]

    def test_three_consecutive_gaps_warn(self):
        history = {f"{year}-12-31": _year() for year in (2023, 2021, 2019, 2017, 2015,
                                                          2014, 2013, 2012, 2011, 2010)}
        assert "Data Gap Warning: Multiple consecutive years missing" in self._warnings(history)

    def test_known_defect_single_large_gap_not_flagged(self):
        # Known defect: one multi-year hole (2023 -> 2015) counts as a single gap, so no warning
        history = {f"{year}-12-31": _year() for year in (2023, 2015, 2014, 2013, 2012,
                                                          2011, 2010, 2009, 2008, 2007)}
        assert self._warnings(history) == []
