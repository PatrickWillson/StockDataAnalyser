"""companies_house_history: the older years from a company's filed accounts (OCR readings), gated against the years
already held, each year from its own accounts and the next year's comparative (offline: no OCR, no network)."""

from clients.companies_house_history import FilingYears, companies_house_history

K = 1000.0


def filing(end, current, prior, unit=K, currency="GBP", total=None):
    """An accepted reading of the accounts to `end`: (current, prior) net income in thousands."""
    prior_end = f"{int(end[:4]) - 1}{end[4:]}"
    return FilingYears(end, end, prior_end, (current * K, prior * K), unit, currency,
                       tuple(t * K for t in total) if total else None)


# Yahoo's years (net income in currency units): FY2022-FY2025
KNOWN = {"2025-12-31": 900 * K, "2024-12-31": 800 * K, "2023-12-31": 700 * K, "2022-12-31": 600 * K}


def years(history):
    return {r.period_end: r.net_income / K for r in history.income_statements}


def test_older_years_come_from_the_accounts_once_two_overlapping_years_agree():
    readings = [filing("2023-12-31", 700, 600), filing("2022-12-31", 600, 500), filing("2021-12-31", 500, 400),
                filing("2020-12-31", 400, 300)]
    history = companies_house_history(KNOWN, readings, "GBP")
    assert years(history) == {"2021-12-31": 500, "2020-12-31": 400, "2019-12-31": 300}
    assert all(r.revenue is None and r.eps is None for r in history.income_statements)
    assert history.shares_by_year == {"2021": 0.0, "2020": 0.0, "2019": 0.0}
    assert "FY2019-FY2021 (3 years)" in history.notes[0] and "FY2022-FY2023" in history.notes[0]


def test_a_year_restated_in_the_next_accounts_takes_the_restated_figure_flagged():
    readings = [filing("2022-12-31", 600, 520), filing("2021-12-31", 500, 400), filing("2023-12-31", 700, 600)]
    history = companies_house_history(KNOWN, readings, "GBP")
    assert years(history)["2021-12-31"] == 520
    assert any("restated" in n and "FY2021" in n for n in history.notes)


def test_two_readings_of_a_year_more_than_5_percent_apart_refuse_that_year():
    readings = [filing("2023-12-31", 700, 600), filing("2022-12-31", 600, 650), filing("2021-12-31", 500, 400)]
    history = companies_house_history(KNOWN, readings, "GBP")
    assert "2021-12-31" not in years(history) and years(history)["2020-12-31"] == 400
    assert any("FY2021" in n and "not used" in n for n in history.notes)


def test_a_disagreement_with_the_held_years_rules_out_every_year():
    # both readings of FY2022 (as first reported, and as the 2023 comparative) are 610 against Yahoo's 600: 1.7%
    readings = [filing("2023-12-31", 700, 610), filing("2022-12-31", 610, 500)]
    history = companies_house_history(KNOWN, readings, "GBP")
    assert history.income_statements == () and "did not agree" in history.notes[0]


def test_fewer_than_two_overlapping_years_rule_out_every_year():
    history = companies_house_history(KNOWN, [filing("2022-12-31", 600, 500)], "GBP")
    assert history.income_statements == () and "fewer than 2" in history.notes[0]


def test_a_held_year_may_match_the_statements_total_profit_and_another_currency_is_left_out():
    known = dict(KNOWN, **{"2022-12-31": 610 * K})                               # Yahoo's figure includes minorities
    readings = [filing("2023-12-31", 700, 600, total=(700, 610)), filing("2022-12-31", 600, 500, total=(610, 505)),
                filing("2021-12-31", 50, 40, currency="USD")]
    history = companies_house_history(known, readings, "GBP")
    assert years(history) == {"2021-12-31": 500}
    assert any("USD" in n for n in history.notes)


from types import SimpleNamespace  # noqa: E402

from clients.companies_house_client import AccountsFiling  # noqa: E402
from clients.companies_house_history import CompaniesHouseHistorySource, filings_to_read  # noqa: E402
from clients.ocr_statement_reader import OcrReading  # noqa: E402


def accounts(end, kind="group"):
    return AccountsFiling(f"T{end[:4]}", end, f"accounts-with-accounts-type-{kind}", 40, f"https://doc/{end}")


FILINGS = [accounts(f"{y}-12-31") for y in range(2025, 2009, -1)] + [accounts("2018-06-30", "interim")]


def test_the_overlapping_accounts_are_read_then_the_older_ones_newest_first():
    chosen = filings_to_read(FILINGS, KNOWN, 4)
    assert [f.made_up_date[:4] for f in chosen] == ["2023", "2022", "2021", "2020", "2019", "2018"]
    assert all(f.annual for f in chosen)


class FakeClient:
    def __init__(self, tmp_path, number="00000001"):
        self.cache_dir, self.number, self.pdfs = str(tmp_path), number, []

    def company_number(self, name):
        return self.number

    def accounts_filings(self, number):
        return FILINGS

    def fetch_pdf(self, number, filing):
        self.pdfs.append(filing.made_up_date)
        return f"/pdf/{filing.transaction_id}"


def fake_reader(values, refused=()):
    """read_filing stand-in: each year end's (current, prior) in thousands; a year in `refused` does not reconcile."""
    def read(path, made_up_date, single_entity=False):
        current, prior = values[made_up_date[:4]]
        st = SimpleNamespace(period_end=made_up_date, prior_end=f"{int(made_up_date[:4]) - 1}{made_up_date[4:]}",
                             net_income=(current * K, prior * K), unit=K, currency="GBP", total=None)
        return 1, OcrReading(st, verified=made_up_date[:4] not in refused)
    return read


def test_the_source_reads_the_accounts_once_and_never_uses_a_refused_reading(tmp_path):
    values = {"2023": (700, 600), "2022": (600, 500), "2021": (500, 400), "2020": (999, 300), "2019": (300, 200),
              "2018": (200, 100)}
    client = FakeClient(tmp_path)
    source = CompaniesHouseHistorySource(client, read_filing=fake_reader(values, refused={"2020"}))
    history = source.history("Example plc", KNOWN, "GBP", 4)
    # the 2020 accounts (999: refused) are never used; FY2020 is the 2021 accounts' comparative, FY2019 its own accounts'
    assert years(history) == {"2021-12-31": 500, "2020-12-31": 400, "2019-12-31": 300, "2018-12-31": 200,
                              "2017-12-31": 100}
    assert "00000001; 6 accounts read, 5 reconciled" in history.notes[1]
    read_once = len(client.pdfs)
    again = CompaniesHouseHistorySource(client, read_filing=lambda *a, **k: 1 / 0).history("Example plc", KNOWN, "GBP", 4)
    assert years(again) == years(history) and len(client.pdfs) == read_once      # from the cache: no PDF, no OCR


def test_no_company_number_gives_a_note_and_no_years(tmp_path):
    history = CompaniesHouseHistorySource(FakeClient(tmp_path, number=None), read_filing=fake_reader({})).history(
        "Example plc", KNOWN, "GBP", 4)
    assert history.income_statements == () and "no single active plc named 'Example plc'" in history.notes[0]


def test_a_cached_reading_made_by_other_reader_code_is_read_again(tmp_path, monkeypatch):
    import clients.companies_house_history as chh
    values = {"2023": (700, 600), "2022": (600, 500), "2021": (500, 400), "2020": (400, 300), "2019": (300, 200),
              "2018": (200, 100)}
    client = FakeClient(tmp_path)
    CompaniesHouseHistorySource(client, read_filing=fake_reader(values)).history("Example plc", KNOWN, "GBP", 4)
    first = len(client.pdfs)
    monkeypatch.setattr(chh, "READING_VERSION", "other-code")
    CompaniesHouseHistorySource(client, read_filing=fake_reader(values)).history("Example plc", KNOWN, "GBP", 4)
    assert len(client.pdfs) == 2 * first and len(chh._reader_version()) == 16
