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

    def test_null_title_is_treated_as_no_title(self):
        data = _officers({"Name": "A", "Title": None}, {"Name": "B", "Title": "CEO"})
        assert FinancialDataProcessor.extract_ceo_name(data) == "B"

    def test_null_title_on_every_officer_falls_back_to_first(self):
        assert FinancialDataProcessor.extract_ceo_name(_officers({"Name": "A", "Title": None})) == "A"

    def test_null_name_returns_na(self):
        assert FinancialDataProcessor.extract_ceo_name(_officers({"Name": None, "Title": "CEO"})) == "N/A"


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

    def test_declared_future_payments_are_excluded(self, processor):
        total, payments, _ = processor.calculate_ttm_dividend([
            {"paymentDate": "2025-06-01", "value": 1.0},   # declared, not yet paid
            {"paymentDate": "2024-03-01", "value": 1.0},   # day after the reference date
            {"paymentDate": "2024-02-29", "value": 0.5},   # on the reference date: included
        ], reference_date="2024-02-29")
        assert total == 0.5
        assert [p["date"] for p in payments] == ["2024-02-29"]

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

    def test_gap_check_also_applies_to_short_histories(self):
        history = {f"{year}-12-31": _year() for year in (2023, 2019, 2015)}
        assert self._warnings(history) == [
            "Insufficient History Warning: Only 3 years of data available (minimum 10 recommended)",
            "Data Gap Warning: 6 fiscal years missing between 2015 and 2023 (2022, 2021, 2020, 2018, 2017, 2016)"]

    def test_scattered_missing_years_warn(self):
        history = {f"{year}-12-31": _year() for year in (2023, 2021, 2019, 2017, 2015,
                                                          2014, 2013, 2012, 2011, 2010)}
        assert self._warnings(history) == [
            "Data Gap Warning: 4 fiscal years missing between 2010 and 2023 (2022, 2020, 2018, 2016)"]

    def test_single_large_gap_warns(self):
        history = {f"{year}-12-31": _year() for year in (2023, 2015, 2014, 2013, 2012,
                                                          2011, 2010, 2009, 2008, 2007)}
        assert self._warnings(history) == [
            "Data Gap Warning: 7 fiscal years missing between 2007 and 2023 "
            "(2022, 2021, 2020, 2019, 2018, 2017, 2016)"]

    def test_fewer_missing_years_than_the_limit_do_not_warn(self):
        history = {f"{year}-12-31": _year() for year in (2023, 2022, 2020, 2019, 2017, 2016,
                                                          2015, 2014, 2013, 2012)}
        assert self._warnings(history) == []

    def test_dividend_only_years_do_not_fill_a_gap(self):
        dividend_only = {"revenue": 0.0, "net_income": 0.0, "eps": 0.0, "total_equity": 0.0, "dividend": 1.0}
        history = {f"{year}-12-31": _year() for year in (2023, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011)}
        history.update({f"{year}-12-31": dividend_only for year in (2022, 2021, 2020)})
        warnings = self._warnings(history)
        assert "Data Gap Warning: 3 fiscal years missing between 2011 and 2023 (2022, 2021, 2020)" in warnings


class TestMalformedRawValues:
    """JSON nulls and junk values are treated as missing (0.0), never crash, and never discard good data."""

    def test_one_malformed_share_row_keeps_the_others(self):
        data = {"outstandingShares": {"annual": {
            "0": {"date": "2023", "shares": 100},
            "1": {"date": "2022", "shares": "NA"},
            "2": {"date": "2021", "shares": None},
            "3": {"date": "2020", "shares": "abc"},
            "4": {"date": "2019", "shares": 120},
        }}}
        assert FinancialDataProcessor.extract_shares_by_year(data) == {"2023": 100.0, "2019": 120.0}

    def test_non_numeric_dividend_array_amount_is_skipped(self):
        data = {"Financials": {"Cash_Flow": {"yearly": {}}},
                "SplitsDividends": {"Dividends": [{"Date": "2023-11-10", "Value": "abc"},
                                                  {"Date": "2023-08-10", "Value": 0.24},
                                                  {"Date": "2022-11-10", "Value": None}]}}
        processor = FinancialDataProcessor(currency_converter=object())

        dividends, _, is_amounts, _, sources = processor.parse_dividend_history(data, None)

        assert dividends == {"2023": 0.24}
        assert is_amounts is True
        assert sources == {"2023": "dividends_array"}


class TestDataStalenessIgnoresDividendOnlyYears:
    """The staleness check uses the latest annual report, not dividend-only placeholder years."""

    REPORT = {"revenue": 100.0, "net_income": 10.0, "eps": 1.0, "total_equity": 50.0}
    DIVIDEND_ONLY = {"revenue": 0.0, "net_income": 0.0, "eps": 0.0, "total_equity": 0.0, "dividend": 0.5}

    def test_future_dividend_only_year_is_not_reported_as_future_data(self):
        history = {"2024-09-30": self.DIVIDEND_ONLY, "2023-09-30": self.REPORT}
        assert FinancialDataProcessor.check_data_staleness(history, datetime(2024, 3, 1)) is None

    def test_stale_report_behind_a_dividend_only_year_still_warns(self):
        history = {"2024-12-31": self.DIVIDEND_ONLY, "2022-12-31": self.REPORT}
        warning = FinancialDataProcessor.check_data_staleness(history, datetime(2024, 3, 1))
        assert warning == "Potentially Stale Data: Most recent annual report is from 2022-12-31 (13 months old)"

    def test_only_dividend_only_years_means_no_history(self):
        history = {"2024-12-31": self.DIVIDEND_ONLY}
        assert FinancialDataProcessor.check_data_staleness(history, datetime(2024, 3, 1)) == \
            "No financial history available"


class TestEpsFallbackShares:
    """When EPS is missing, it is net income / that year's shares — never today's share count first."""

    BS = {"2021-12-31": {"shares_outstanding": 200.0}, "2023-12-31": {"shares_outstanding": 150.0}}
    IS = {"2021-12-31": {"net_income": 400.0, "eps": 0.0, "revenue": 1.0},
          "2023-12-31": {"net_income": 300.0, "eps": 0.0, "revenue": 1.0}}

    def test_uses_balance_sheet_shares_when_no_year_specific_count(self):
        history = FinancialDataProcessor.merge_financial_data(self.BS, self.IS, {}, 100.0, {"2023": 150.0})
        assert history["2023-12-31"]["eps"] == 2.0          # 300 / 150 (outstandingShares)
        assert history["2021-12-31"]["eps"] == 2.0          # 400 / 200 (balance sheet), not 400 / 100 (current)
        assert history["2021-12-31"]["shares_outstanding"] == 200.0

    def test_falls_back_to_current_shares_only_without_any_year_count(self):
        bs = {"2021-12-31": {"shares_outstanding": 0.0}}
        is_ = {"2021-12-31": {"net_income": 400.0, "eps": 0.0, "revenue": 1.0}}
        history = FinancialDataProcessor.merge_financial_data(bs, is_, {}, 100.0, {})
        assert history["2021-12-31"]["eps"] == 4.0          # 400 / 100

    def test_reported_eps_is_kept(self):
        is_ = {"2021-12-31": {"net_income": 400.0, "eps": 1.5, "revenue": 1.0}}
        history = FinancialDataProcessor.merge_financial_data(self.BS, is_, {}, 100.0, {})
        assert history["2021-12-31"]["eps"] == 1.5


class TestTotalDebtWithOneComponentMissing:
    """A single reported debt component is a partial figure; the reported total wins over it."""

    @staticmethod
    def _total_debt(year_data):
        processor = FinancialDataProcessor(currency_converter=object())
        data = {"Financials": {"Balance_Sheet": {"yearly": {"2022-12-31": year_data}}}}
        return processor.parse_balance_sheet(data)["2022-12-31"]["total_debt"]

    def test_long_term_only_uses_reported_total(self):
        assert self._total_debt({"longTermDebt": 98_959, "shortLongTermDebtTotal": 120_069}) == 120_069

    def test_short_term_only_uses_reported_total(self):
        assert self._total_debt({"shortTermDebt": 5_000, "shortLongTermDebtTotal": 20_000}) == 20_000

    def test_single_component_without_total_is_used(self):
        assert self._total_debt({"longTermDebt": 98_959}) == 98_959

    def test_both_components_are_summed(self):
        assert self._total_debt({"longTermDebt": 100, "shortTermDebt": 50, "shortLongTermDebtTotal": 200}) == 150
