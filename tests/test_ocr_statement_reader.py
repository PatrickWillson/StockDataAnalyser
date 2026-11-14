"""ocr_statement_reader: synthetic OCR words (no tesseract) -> rows -> statement, with its checks."""

from clients.ocr_statement_reader import (Word, is_candidate_page, is_statement_page, read_statement, rows_from_words,
                                          unit_token, words_from_tesseract, year_row_from_reread)

H = 30     # word height in pixels


def page(lines, conf=95.0):
    """lines: [(y, [(text, right_edge_x), ...]), ...] -> Words (each word 20 px per character, right-aligned)."""
    words = []
    for n, (y, items) in enumerate(lines):
        for text, right in items:
            width = 20 * len(text)
            words.append(Word(text, right - width, y, width, H, conf, (1, 1, n + 1)))
    return words


LABEL, CUR, PRI = 600, 1400, 1700          # label end, current-year column edge, prior-year column edge


def statement(pat=("2,708", "2,333"), owners=None):
    lines = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]),
             (180, [("2025", CUR), ("2024", PRI)]), (230, [("£'000", CUR), ("£'000", PRI)]),
             (300, [("Revenue", 200), ("50,935", CUR), ("48,947", PRI)]),
             (350, [("Cost", 100), ("of", 160), ("sales", 280), ("(28,440)", CUR), ("(27,292)", PRI)]),
             (400, [("Profit", 140), ("before", 290), ("tax", 370), ("4,089", CUR), ("3,198", PRI)]),
             (450, [("Tax", 80), ("expense", 260), ("(1,381)", CUR), ("(865)", PRI)]),
             (500, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), (pat[0], CUR), (pat[1], PRI)])]
    if owners:
        lines.append((550, [("Attributable", 260), ("to", 320), ("owners", 460), (owners[0], CUR), (owners[1], PRI)]))
    return page(lines)


def test_a_clean_page_reads_the_net_income_with_its_checks():
    reading = read_statement(rows_from_words(statement()), "2025-12-31")
    assert reading.statement.net_income == (2_708_000, 2_333_000)
    assert reading.statement.period_end == "2025-12-31" and reading.arithmetic is True
    assert reading.min_confidence == 95.0


def test_a_thousands_separator_read_as_a_space_is_rejoined():
    words = page([(100, [("Revenue", 200), ("14", 1300), ("476", 1370)])])      # a 10 px gap: a comma
    assert [w.t for w in rows_from_words(words)[0].words] == ["Revenue", "14,476"]


def test_the_arithmetic_check_flags_a_misread_total():
    reading = read_statement(rows_from_words(statement(pat=("2,208", "2,333"))), "2025-12-31")
    assert reading.arithmetic is False


def test_words_come_from_tesseracts_dict():
    data = {"text": ["", "Revenue", "50,935"], "left": [0, 10, 900], "top": [0, 20, 20], "width": [0, 140, 120],
            "height": [0, 30, 30], "conf": ["-1", "96", "91"], "block_num": [0, 1, 1], "par_num": [0, 1, 1],
            "line_num": [0, 3, 3]}
    assert words_from_tesseract(data) == [Word("Revenue", 10, 20, 140, 30, 96.0, (1, 1, 3)),
                                          Word("50,935", 900, 20, 120, 30, 91.0, (1, 1, 3))]


def test_the_statement_page_is_told_from_a_note_that_mentions_it():
    page_text = ("Consolidated income statement\nfor the year ended 31 December 2025\nRevenue 50,935 48,947\n"
                 "Cost of sales (28,440) (27,292)\nProfit before tax 4,089 3,198\nTax (1,381) (865)\n")
    note = "1.20 Inventories\nThe consolidated income statement includes revenue of 50,935 before tax ...\n" * 3
    assert is_statement_page(page_text) and not is_statement_page(note)


def test_a_reading_is_accepted_only_when_its_net_income_reconciles():
    ok = read_statement(rows_from_words(statement(owners=("2,708", "2,333"))), "2025-12-31")
    assert ok.verified and ok.accepted is ok.statement
    # the owners' line misread as 2,208: 2,208 + 0 minorities != 2,708 profit for the year
    bad = read_statement(rows_from_words(statement(owners=("2,208", "2,333"))), "2025-12-31")
    assert bad.statement.net_income[0] == 2_208_000 and not bad.verified and bad.accepted is None
    assert "failed: net income + minorities" in bad.notes[0]


def test_a_misread_figure_voids_its_line_so_it_is_never_taken():
    """Samuel Heath: '888' read as '$88'; a stray dash beside it must not become 0."""
    words = statement(owners=("2,708", "2,333"))
    words = [Word("$88", w.x, w.y, w.w, w.h, 85.0, w.line) if w.t == "2,708" and w.y == 550 else w for w in words]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert "[unreadable]" in reading.html
    assert reading.accepted is None or reading.accepted.net_income[0] == 2_708_000


def test_a_low_confidence_figure_voids_its_line():
    words = [Word(w.t, w.x, w.y, w.w, w.h, 30.0, w.line) if w.t == "2,708" else w for w in statement()]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert reading.accepted is None


def test_low_resolution_damage_still_makes_a_candidate_and_a_small_company_or_m_page_confirms():
    """At 100 dpi: 'INCOME STATEME!' and a split 'Consol / lated'; at 200 dpi: £m with decimals, a small company."""
    assert is_candidate_page("SAMUEL HEATH\nCONSOLIDATED INCOME STATEME!\nfor the year\n")
    assert is_candidate_page("Consol\nlated income statement\n2024 2023\n")
    assert not is_candidate_page("Company income statement\n2025 2024\n")
    in_m = ("Consolidated income statement\nfor the year ended 30 September 2025\n£m £m\nRevenue 690.1 718.2\n"
            "Cost of sales (380.4) (390.6)\nGross profit 309.7 327.6\nProfit before tax 52.1 70.3\nTaxation (13.2) (17.5)\n"
            "Profit for the year 38.9 52.8\n")
    small = ("Consolidated income statement\n2025 2024\n£000 £000\nRevenue 812 790\nCost of sales (402) (395)\n"
             "Gross profit 410 395\nProfit before taxation 61 57\nTax (12) (11)\nProfit for the year 49 46\n")
    assert is_statement_page(in_m) and is_statement_page(small)


def test_a_cut_heading_or_one_read_below_the_label_column_still_finds_the_page():
    """Ascent 2024 at 100 dpi: 'Consolidated Statement of Comprehen:'. Samuel Heath 2025: two statements on the page,
    tesseract reading the label column first, so the heading is a line of its own far below the top."""
    assert is_candidate_page("Consolidated Statement of Comprehen:\nFor the year ended 31 December 2024\n")
    labels = ["Note", "Revenue 5", "Cost of sales", "Gross profit", "Selling and distribution costs", "Administrative expenses",
              "Other operating income 25", "Operating profit 6", "Finance income 8", "Finance cost 8",
              "Profit before taxation", "Taxation 9", "Profit for the year attributable to owners of the", "Parent Company",
              "Basic and diluted earnings per ordinary share 1", "CONSOLIDATED STATEMENT OF COMPREHENSIVE INCOME",
              "for the year ended 31 March 2025", "SAMUEL HEATH", "CONSOLIDATED INCOME STATEMENT.",
              "for the year ended 31 March 2025", "2025", "£000", "14,769", "(7,930)", "6,839", "(3,711)", "(2,163)", "61",
              "1,026", "137", "1,163", "(275)", "888"]
    assert is_candidate_page("\n".join(labels)) and is_statement_page("\n".join(labels))
    # a heading-only line far down a note's page does not count when it is part of a list (the auditor's '• the ...;')
    listed = "\n".join(labels[:15] + ["• the consolidated income statement;"] + labels[20:])
    assert not is_statement_page(listed)


def test_a_company_without_revenue_still_confirms_by_its_expenses():
    """Ascent 2016, an exploration company: no revenue line, administrative expenses and a loss from operations."""
    text = ("Consolidated Income Statement & Statement of Other Comprehensive\nIncome\nFor the year ended 31 December 2016\n"
            "2016 2015\nNotes £'000s £'000s\nOther administrative expenses (1,382) (1,609)\nTermination payments - (279)\n"
            "Loss from operating activities 3 (1,382) (1,888)\nFinance income 5 159 745\nFinance cost 5 (1,453) (2,501)\n"
            "Loss before taxation (2,676) (3,644)\nLoss for the year (2,676) (3,644)\n")
    assert is_statement_page(text)
    assert not is_statement_page(text.replace("administrative expenses", "items").replace("operating activities", "x"))


def test_a_before_tax_label_wrapped_onto_the_next_line_still_confirms():
    """Vertu 2025: 'Profit /(loss) before  29,319 ...' with 'tax' printed below, then 'Taxation 12 (7,576) ...'."""
    text = ("Consolidated Income Statement\nFor the year ended 28 February 2025\nRevenue 5 4,763,926 - 4,763,926 4,686,280\n"
            "Operating profit 46,486 (4,228) 42,258 52,406\nProfit /(loss) before 29,319 (4,569) 24,750 34,727 (160) 34,567\n"
            "Taxation 12 (7,576) 929 (6,647) (9,012) 158 (8,854)\n")
    assert is_statement_page(text)
    assert not is_statement_page(text.replace("Taxation", "Dividends"))
    vct = ("INCOME STATEMENT\nFOR THE YEAR ENDED 30 NOVEMBER 2025\nRevenue Capital Total\n"
           "Income from investments 2 - 833 817 - 817\nInvestment management fees 3 (1,359) (1,698) (311) (1,243) (1,554)\n"
           "Net return on ordinary activities before 630 588 1,900 2,488\ntaxation\nTax on ordinary activities 5 - - -\n")
    assert is_statement_page(vct, single_entity=True)          # Maven VCT 3 2025: 'return ... before' / 'taxation'


def test_a_plain_income_statement_heading_confirms_only_for_a_single_companys_accounts():
    """Maven VCT 3 2011 (no subsidiaries): 'Income Statement'. In a group's accounts a plain heading could be the parent
    company's own statement, so it is not taken there."""
    text = ("Income Statement\nFor the year ended 30 November 2011\nYear ended 30 November 2011 Year ended 30 November 2010\n"
            "Revenue Capital Total Revenue Capital Total\nGains on investments 8 1,846 1,846 - 1,439 1,439\n"
            "Income from investments 2 1,034 - 1,034 731 - 731\nInvestment management fees 3 (182) (424) (606) (153)\n"
            "Return on ordinary activities before taxation 798 1,422 2,220 513 1,015 1,528\n")
    assert is_statement_page(text, single_entity=True) and not is_statement_page(text)
    rows = [(100, [("Income", 150), ("Statement", 350)]), (180, [("2011", CUR), ("2010", PRI)]),
            (230, [("£'000", CUR), ("£'000", PRI)]), (300, [("Income", 150), ("from", 230), ("investments", 450), ("1,034", CUR), ("731", PRI)]),
            (350, [("Gains", 120), ("on", 170), ("investments", 400), ("1,846", CUR), ("1,439", PRI)]),
            (400, [("Return", 140), ("on", 190), ("ordinary", 360), ("activities", 560), ("before", 690), ("taxation", 870), ("2,220", CUR), ("1,528", PRI)]),
            (450, [("Taxation", 200), ("(66)", CUR), ("(335)", PRI)]),
            (500, [("Return", 140), ("on", 190), ("ordinary", 360), ("activities", 560), ("after", 670), ("taxation", 850), ("2,154", CUR), ("1,193", PRI)])]
    reading = read_statement(rows_from_words(page(rows)), "2011-11-30")
    assert "<p>Income Statement for the year ended 30 November 2011</p>" in reading.html
    assert reading.accepted and reading.accepted.net_income == (2_154_000, 1_193_000)


def test_an_auditors_paragraph_naming_the_statement_does_not_confirm():
    audit = ("Independent auditor's report\nIn our opinion the consolidated income statement gives a true and fair view\n"
             "We have audited revenue 1,234 and profit before tax 5,678 " + "12,345 " * 12)
    assert not is_statement_page(audit)
    # Empresaria 2024: a two-column auditor's report whose short lines name the statement, with revenue, 'loss before
    # tax' and figures (materiality, coverage) further down
    emr = ("Empresaria Annual report and accounts 2024\nIndependent auditor's report\nto the members of Empresaria Group plc\n"
           "Opinion\nWe have audited the financial statements of Empresaria Group Plc\nended 31 December 2024 which comprise\n"
           "consolidated income statement.\nconsolidated statement of comprehensive income,\n"
           "94.7% of group revenue, 81.8% of net fee income, 72.5% of loss before tax " + "12,345 " * 12)
    assert not is_statement_page(emr)


def test_a_tilted_page_keeps_each_printed_line_whole():
    """ALU 2025, tilted 0.74 degrees: a line's right-hand figures sit 25 px lower than its label."""
    tilted = [Word(w.t, w.x, w.y + (25 if w.x > LABEL else 0), w.w, w.h, w.c, w.line) for w in statement()]
    reading = read_statement(rows_from_words(tilted), "2025-12-31")
    assert reading.accepted and reading.accepted.net_income == (2_708_000, 2_333_000)


def test_three_columns_a_year_and_a_note_column():
    """Underlying | non-underlying | total per year, and a note column of bare references: the totals are taken."""
    N, U1, E1, T1, U2, E2, T2 = 700, 950, 1150, 1350, 1600, 1800, 2000
    rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]),
            (180, [("2025", T1), ("2024", T2)]), (230, [("£'000", U1), ("£'000", E1), ("£'000", T1), ("£'000", U2), ("£'000", E2), ("£'000", T2)]),
            (300, [("Revenue", 200), ("3", N), ("9,000", U1), ("-", E1), ("9,000", T1), ("8,000", U2), ("-", E2), ("8,000", T2)]),
            (350, [("Expenses", 200), ("4", N), ("(6,000)", U1), ("(500)", E1), ("(6,500)", T1), ("(5,500)", U2), ("(200)", E2), ("(5,700)", T2)]),
            (400, [("Profit", 140), ("before", 290), ("tax", 370), ("3,000", U1), ("(500)", E1), ("2,500", T1), ("2,500", U2), ("(200)", E2), ("2,300", T2)]),
            (450, [("Taxation", 200), ("5", N), ("(600)", U1), ("100", E1), ("(500)", T1), ("(500)", U2), ("40", E2), ("(460)", T2)]),
            (500, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), ("2,400", U1), ("(400)", E1), ("2,000", T1), ("2,000", U2), ("(160)", E2), ("1,840", T2)])]
    reading = read_statement(rows_from_words(page(rows)), "2025-06-30")
    assert reading.accepted and reading.accepted.net_income == (2_000_000, 1_840_000)


def test_a_wrapped_label_is_joined_to_its_line():
    """'Profit for the :' / 'year  2,708  2,333' (BMTO 2017): stray punctuation dropped, the lines joined."""
    words = [w for w in statement() if w.y != 500] + page([(500, [("Profit", 140), ("for", 220), ("the", 300), (":", 330)]),
                                                         (530, [("year", 100), ("2,708", CUR), ("2,333", PRI)])])
    words = [Word(w.t, w.x, w.y, w.w, w.h, w.c, (2, 1, w.y)) for w in words]          # a line id per y
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert "<td>Profit for the year</td><td>2,708</td>" in reading.html
    assert reading.accepted and reading.accepted.net_income == (2_708_000, 2_333_000)


def test_a_slash_between_profit_and_loss_is_kept_and_a_7_for_the_apostrophe_is_still_thousands():
    """Plexus 2025: 'Notes  £7000  £7000' and '(Loss) / profit for year'; a stray '/' elsewhere is still dropped."""
    words = [w for w in statement() if w.y not in (230, 500)] + page([
        (230, [("Notes", 1000), ("£7000", CUR), ("£7000", PRI)]),
        (500, [("(Loss)", 120), ("/", 150), ("profit", 280), ("for", 360), ("year", 460), ("2,708", CUR), ("2,333", PRI)])])
    words = [Word(w.t, w.x, w.y, w.w, w.h, w.c, (2, 1, w.y)) for w in words]          # a line id per y
    reading = read_statement(rows_from_words(words), "2025-06-30")
    assert "<td>(Loss) / profit for year</td>" in reading.html
    assert reading.accepted and reading.accepted.net_income == (2_708_000, 2_333_000)
    from clients.ocr_statement_reader import _clean_label
    assert _clean_label(["Profit", "for", "the", "/", "year"]) == "Profit for the year"
    assert _clean_label(["Profit", "/", "(loss)", "for", "the", "year"]) == "Profit / (loss) for the year"


def test_a_nil_dash_read_with_low_confidence_is_still_nil_but_a_wide_one_is_not():
    """Plexus 2025: 'Income tax credit  -  130', the dash at 47% confidence (dashes routinely score low); a misread
    figure is wider than a dash, so a wide low-confidence token still voids its line."""
    rows = [w for w in statement() if w.y not in (400, 450, 500)] + page([
        (400, [("Profit", 140), ("before", 290), ("tax", 370), ("2,708", CUR), ("3,198", PRI)]),
        (450, [("Tax", 80), ("credit", 230), ("-", CUR), ("(865)", PRI)]),
        (500, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), ("2,708", CUR), ("2,333", PRI)])])
    low = [Word(w.t, w.x, w.y, w.w, w.h, 47.0 if w.t == "-" else w.c, (2, 1, w.y)) for w in rows]
    reading = read_statement(rows_from_words(low), "2025-06-30")
    assert "<td>Tax credit</td><td>-</td><td>(865)</td>" in reading.html
    assert reading.accepted and reading.accepted.net_income == (2_708_000, 2_333_000)
    wide = [Word(w.t, w.x - 60, w.y, w.w + 60, w.h, w.c, w.line) if w.t == "-" else w for w in low]
    assert "[unreadable]" in read_statement(rows_from_words(wide), "2025-06-30").html


def test_split_year_headers_name_the_year_they_end():
    """ALU 2010: '2009/10  2008/09'."""
    words = [Word("2009/10", w.x, w.y, w.w, w.h, w.c, w.line) if w.t == "2025" else
             Word("2008/09", w.x, w.y, w.w, w.h, w.c, w.line) if w.t == "2024" else w for w in statement()]
    reading = read_statement(rows_from_words(words), "2010-03-31")
    assert "<td>2010</td><td>2009</td>" in reading.html
    assert reading.accepted and reading.accepted.net_income == (2_708_000, 2_333_000)


def test_the_minorities_beside_the_chosen_figure_are_used():
    """ALU 2010: total comprehensive income attributable (owners 703, minorities 10) above the profit attributable
    (owners 2,234, minorities 6); profit for the year 2,240 = 2,234 + 6."""
    rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]), (180, [("2010", CUR), ("2009", PRI)]),
            (230, [("£000", CUR), ("£000", PRI)]), (300, [("Revenue", 200), ("92,972", CUR), ("109,088", PRI)]),
            (350, [("Profit", 140), ("before", 290), ("taxation", 450), ("3,378", CUR), ("1,804", PRI)]),
            (400, [("Tax", 80), ("expense", 260), ("(1,138)", CUR), ("(744)", PRI)]),
            (450, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), ("2,240", CUR), ("1,060", PRI)]),
            (500, [("Total", 120), ("comprehensive", 400), ("income", 540), ("attributable", 780), ("to", 840)]),
            (550, [("Equity", 140), ("holders", 300), ("of", 340), ("the", 410), ("parent", 540), ("703", CUR), ("3,551", PRI)]),
            (600, [("Non-controlling", 300), ("interest", 470), ("10", CUR), ("35", PRI)]),
            (650, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), ("attributable", 640), ("to", 700)]),
            (700, [("Equity", 140), ("holders", 300), ("of", 340), ("the", 410), ("parent", 540), ("2,234", CUR), ("1,052", PRI)]),
            (750, [("Non-controlling", 300), ("interest", 470), ("6", CUR), ("8", PRI)])]
    words = [Word(w.t, w.x, w.y, w.w, w.h, w.c, (3, 1, w.y)) for w in page(rows)]
    reading = read_statement(rows_from_words(words), "2010-06-30")
    assert reading.accepted and reading.accepted.net_income == (2_234_000, 1_052_000)


def test_a_dropped_heading_starts_the_statement_at_the_year_row():
    """ALU 2017: the large heading line is missing from the high-resolution read."""
    words = [w for w in statement() if w.y != 100]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert reading.accepted and reading.accepted.net_income == (2_708_000, 2_333_000)


def test_continuing_and_discontinued_operations_reconcile_to_the_total():
    """ALU 2017: profit before tax + tax = the continuing profit; + discontinued = the total, which is net income."""
    rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]), (180, [("2017", CUR), ("2016", PRI)]),
            (230, [("£000", CUR), ("£000", PRI)]), (300, [("Revenue", 200), ("104,761", CUR), ("92,233", PRI)]),
            (350, [("Profit", 140), ("before", 290), ("taxation", 450), ("8,123", CUR), ("6,759", PRI)]),
            (400, [("Tax", 80), ("expense", 260), ("(1,583)", CUR), ("(1,581)", PRI)]),
            (450, [("Profit", 140), ("for", 220), ("the", 300), ("period", 440), ("6,540", CUR), ("5,178", PRI)]),
            (500, [("Discontinued", 260), ("operations", 480)]),
            (550, [("Profit", 140), ("from", 240), ("discontinued", 500), ("operations", 720), ("-", CUR), ("1,306", PRI)]),
            (600, [("Profit", 140), ("for", 220), ("the", 300), ("period", 440), ("6,540", CUR), ("6,484", PRI)])]
    words = [Word(w.t, w.x, w.y, w.w, w.h, w.c, (4, 1, w.y)) for w in page(rows)]
    reading = read_statement(rows_from_words(words), "2017-06-30")
    assert reading.accepted and reading.accepted.net_income == (6_540_000, 6_484_000)


def test_unit_tokens_allow_ocrs_confusions():
    assert [unit_token(t) for t in ("£m", "gm", "&m", "$m", "£000", "£'000", "£°000", "000", "2025", "Revenue")] == \
        ["£m", "£m", "£m", "$m", "£000", "£000", "£000", "£000", None, None]
    # Plexus 2025: the apostrophe of £'000 read as a 7; only after a currency sign (a bare 7000 is a figure)
    assert [unit_token(t) for t in ("£7000", "$7000", "7000", "£70000", "£7,000")] == ["£000", "$000", None, None, None]


def test_a_unit_row_read_gm_still_gives_millions():
    words = [Word("gm", w.x, w.y, 40, w.h, w.c, w.line) if w.t == "£'000" else w for w in statement()]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert reading.statement.unit == 1e6


def test_a_stray_token_between_the_columns_voids_its_line():
    """Samuel Heath 2025: a stray dash 130 px left of the column must not become a figure (0)."""
    words = statement(owners=("2,708", "2,333")) + [Word("-", CUR - 230, 550, 20, H, 0.0, (1, 1, 9))]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert "owners [unreadable]" in reading.html


def test_plain_pounds_over_small_figures_is_not_believed():
    """AST 2009: '£ £' (the '000 lost) over figures like 898 and (10,756): a 1,000x error if taken as pounds."""
    words = [Word("£", w.x + w.w - 20, w.y, 20, w.h, w.c, w.line) if w.t == "£'000" else w for w in statement()]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert reading.statement.unit == 1.0 and reading.accepted is None
    assert "unit unknown" in reading.notes[0]


def test_plain_pounds_over_full_pound_figures_is_believed():
    """Braime 2006 style: exact pounds (11,119,745)."""
    big = {"50,935": "50,935,412", "48,947": "48,947,118", "(28,440)": "(28,440,310)", "(27,292)": "(27,292,004)",
           "4,089": "4,089,377", "3,198": "3,198,250", "(1,381)": "(1,381,101)", "(865)": "(865,050)",
           "2,708": "2,708,276", "2,333": "2,333,200"}
    words = [Word("£", w.x + w.w - 20, w.y, 20, w.h, w.c, w.line) if w.t == "£'000" else
             Word(big.get(w.t, w.t), w.x, w.y, w.w, w.h, w.c, w.line) for w in statement()]
    reading = read_statement(rows_from_words(words), "2025-12-31")
    assert reading.accepted and reading.accepted.net_income == (2_708_276, 2_333_200)


def test_a_year_row_re_read_on_its_own_is_used_only_when_it_names_the_accounts_year():
    """Empresaria 2024: the shaded year row read 'BRE BOBS' with the page, 'AlAtan 2024 2023' on its own. Years that do
    not include the register's year end are not the statement's (a misread), so nothing is substituted."""
    def line(*texts):
        return [Word(t, 1000 + 300 * n, 5, 100, H, 90.0, (1, 1, 1)) for n, t in enumerate(texts)]
    row = year_row_from_reread(line("AlAtan", "2024", "2023"), 400, "2024-12-31")
    assert [w.t for w in row.words] == ["AlAtan", "2024", "2023"] and row.words[1].y == 405
    assert year_row_from_reread(line("2009/10", "2008/09"), 0, "2010-03-31") is not None
    assert year_row_from_reread(line("2019", "2018"), 400, "2024-12-31") is None
    assert year_row_from_reread(line("Note", "£m", "£m"), 400, "2024-12-31") is None


def test_a_lost_decimal_point_is_restored_in_a_statement_in_tenths_and_must_still_tie_out():
    """Empresaria 2024 (£m, one decimal): minorities read '15' and '16' for 1.5 and 1.6. The point is restored where
    nearly every figure has one decimal, noted, and the reading is accepted only because it then reconciles."""
    def tenths(minorities):
        rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]), (180, [("2024", CUR), ("2023", PRI)]),
                (230, [("£m", CUR), ("£m", PRI)]), (300, [("Revenue", 200), ("246.2", CUR), ("250.3", PRI)]),
                (350, [("Cost", 100), ("of", 160), ("sales", 280), ("(195.8)", CUR), ("(192.8)", PRI)]),
                (400, [("Loss", 120), ("before", 270), ("tax", 350), ("(5.2)", CUR), ("0.1", PRI)]),
                (450, [("Taxation", 200), ("(3.7)", CUR), ("(1.4)", PRI)]),
                (500, [("Loss", 120), ("for", 200), ("the", 280), ("year", 380), ("(8.9)", CUR), ("(1.3)", PRI)]),
                (550, [("Attributable", 300), ("to:", 360)]),
                (600, [("Owners", 160), ("of", 210), ("the", 280), ("Company", 450), ("(10.4)", CUR), ("(2.9)", PRI)]),
                (650, [("Non-controlling", 330), ("interests", 520), minorities[0], minorities[1]])]
        return read_statement(rows_from_words(page(rows)), "2024-12-31")
    reading = tenths((("15", CUR), ("16", PRI)))
    assert reading.accepted and reading.accepted.net_income == (-10_400_000, -2_900_000)
    assert any("decimal point restored in 2 figures" in n for n in reading.notes)
    # restored, but wrong (the true figures were 2.5 and 1.6): it does not tie, so it is not accepted
    assert tenths((("25", CUR), ("16", PRI))).accepted is None
    # a £000 statement whose only decimals are the pence of earnings per share is left alone
    from clients.ocr_statement_reader import restore_decimals
    pence = "<table>" + "".join(f"<tr><td>Line</td><td>{a}</td><td>{b}</td></tr>" for a, b in
                                [("1,234", "1,100"), ("(567)", "(500)"), ("667", "600"), ("(120)", "(100)"), ("547", "500"),
                                 ("4.62", "5.48"), ("4.29", "5.10")]) + "</table>"
    assert restore_decimals(pence) == (pence, 0)


def test_with_no_tax_line_the_net_income_ties_to_total_comprehensive_income():
    """Braime 2010: the tax line unreadable; below, the statement of comprehensive income: profit 945,138 + other
    comprehensive income (64,254) = total comprehensive income 880,884 (2009: 387,087 - 180,605 = 206,482)."""
    def soci(tci):
        rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]), (180, [("2010", CUR), ("2009", PRI)]),
                (230, [("£", CUR), ("£", PRI)]), (300, [("Revenue", 200), ("18,057,661", CUR), ("15,685,218", PRI)]),
                (350, [("Depreciation", 300), ("(286,938)", CUR), ("(302,865)", PRI)]),
                (400, [("Profit", 140), ("before", 290), ("tax", 370), ("1,361,378", CUR), ("624,992", PRI)]),
                (450, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), ("attributable", 640), ("to", 700),
                       ("equity", 820), ("shareholders", 1050), ("945,138", CUR), ("387,087", PRI)]),
                (550, [("Actuarial", 220), ("gains", 330), ("(168,000)", CUR), ("76,000", PRI)]),
                (600, [("Other", 120), ("comprehensive", 380), ("income", 520), ("for", 600), ("the", 680), ("year", 780),
                       ("(64,254)", CUR), ("(180,605)", PRI)]),
                (650, [("Total", 120), ("comprehensive", 380), ("income", 520), ("for", 600), ("the", 680), ("year", 780),
                       (tci, CUR), ("206,482", PRI)])]
        return read_statement(rows_from_words(page(rows)), "2010-12-31")
    reading = soci("880,884")
    assert reading.accepted and reading.accepted.net_income == (945_138, 387_087)
    assert "net income + minorities + other comprehensive income = total comprehensive income" in reading.notes[0]
    assert soci("880,084").accepted is None


def test_a_note_number_printed_before_a_label_does_not_hide_the_tax_line():
    """Fletcher King 2018: '8 Taxation (65) (159)' and 'Profit and total comprehensive income for the year attributable
    to equity shareholders 209 579': 274 - 65 = 209."""
    rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]), (180, [("2018", CUR), ("2017", PRI)]),
            (230, [("£000", CUR), ("£000", PRI)]), (300, [("4", 40), ("Revenue", 200), ("3,080", CUR), ("4,094", PRI)]),
            (350, [("Other", 120), ("expenses", 300), ("(1,181)", CUR), ("(1,214)", PRI)]),
            (400, [("Profit", 140), ("before", 290), ("taxation", 450), ("274", CUR), ("738", PRI)]),
            (450, [("8", 40), ("Taxation", 230), ("(65)", CUR), ("(159)", PRI)]),
            (500, [("Profit", 140), ("and", 210), ("total", 300), ("comprehensive", 560), ("income", 700), ("for", 780),
                   ("the", 860), ("year", 960), ("attributable", 1200), ("to", 1260), ("equity", 1380),
                   ("shareholders", 1600), ("209", CUR), ("579", PRI)])]
    reading = read_statement(rows_from_words(page(rows)), "2018-04-30")
    assert reading.accepted and reading.accepted.net_income == (209_000, 579_000)


def test_the_statutory_profit_before_tax_is_preferred_to_an_adjusted_one():
    """Vertu 2011: 'Profit before tax, amortisation, share based payments charge and total exceptional charges 8,369'
    comes first; 'Profit before tax 5,251' - 1,227 tax = 4,024 is the one that ties."""
    rows = [(100, [("Consolidated", 300), ("income", 450), ("statement", 650)]), (180, [("2011", CUR), ("2010", PRI)]),
            (230, [("£000", CUR), ("£000", PRI)]), (300, [("Revenue", 200), ("998,926", CUR), ("818,922", PRI)]),
            (350, [("Profit", 140), ("before", 290), ("tax,", 380), ("amortisation", 640), ("and", 720),
                   ("exceptional", 960), ("charges", 1120), ("8,369", CUR), ("6,856", PRI)]),
            (400, [("Total", 120), ("exceptional", 360), ("charges", 520), ("(2,763)", CUR), ("(1,902)", PRI)]),
            (450, [("Profit", 140), ("before", 290), ("tax", 370), ("5,251", CUR), ("4,626", PRI)]),
            (500, [("Taxation", 200), ("(1,227)", CUR), ("(844)", PRI)]),
            (550, [("Profit", 140), ("for", 220), ("the", 300), ("year", 400), ("attributable", 640), ("to", 700),
                   ("equity", 820), ("holders", 980), ("4,024", CUR), ("3,782", PRI)])]
    reading = read_statement(rows_from_words(page(rows)), "2011-02-28")
    assert reading.accepted and reading.accepted.net_income == (4_024_000, 3_782_000)


def test_an_unconfirmed_reading_is_retried_finer_and_only_a_confirmed_pass_replaces_it():
    """RWS 2010: at 300 dpi '476' for 14,476 (refused); at 400 dpi read right and reconciled. Each pass must pass the
    checks on its own; when none does, the first reading stands."""
    from clients.ocr_statement_reader import OcrReading, reread_finer
    first = OcrReading(None, notes=("failed",))
    passes = {400: OcrReading(None, notes=("failed",)), 450: OcrReading(None, notes=("held",), verified=True)}
    asked = []

    def read_at(dpi):
        asked.append(dpi)
        return passes[dpi]
    got = reread_finer(read_at, first)
    assert got.verified and got.notes == ("held", "read at 450 dpi") and asked == [400, 450]
    assert reread_finer(lambda dpi: OcrReading(None, notes=("failed",)), first) is first
    assert reread_finer(read_at, passes[450]) is passes[450]           # already confirmed: no second pass


def test_a_heading_wrapped_over_two_lines_or_in_the_other_word_order_is_found():
    """Ortac 2025: 'Statement of consolidated' / 'comprehensive income'; NAHL 2025: 'CONSOLIDATED STATEMENT OF' /
    'COMPREHENSIVE INCOME'."""
    body = ("Year ended 31 December 2025 Year ended 31 December 2024\nRevenue 12 40,043 38,805\n"
            "Administration expenses 7 (1,501) (1,529)\nOperating loss (634) (1,071)\nLoss before taxation (225) (2,221)\n"
            "Taxation - -\nLoss for the year (225) (2,221)\n")
    for heading in ("Statement of consolidated\ncomprehensive income\n", "CONSOLIDATED STATEMENT OF\nCOMPREHENSIVE INCOME\n",
                    "Statement of consolidated comprehensive income\n"):
        assert is_candidate_page(heading + body) and is_statement_page(heading + body), heading
    rows = [(100, [("Statement", 200), ("of", 250), ("consolidated", 500)]), (150, [("comprehensive", 280), ("income", 420)]),
            (180, [("2025", CUR), ("2024", PRI)]), (230, [("£000", CUR), ("£000", PRI)]),
            (300, [("Revenue", 200), ("4,089", CUR), ("3,198", PRI)]), (350, [("Expenses", 200), ("(4,314)", CUR), ("(5,419)", PRI)]),
            (400, [("Loss", 120), ("before", 270), ("taxation", 430), ("(225)", CUR), ("(2,221)", PRI)]),
            (450, [("Taxation", 200), ("-", CUR), ("-", PRI)]),
            (500, [("Loss", 120), ("for", 200), ("the", 280), ("year", 380), ("(225)", CUR), ("(2,221)", PRI)])]
    reading = read_statement(rows_from_words(page(rows)), "2025-12-31")
    assert "<p>Statement of consolidated comprehensive income for the year ended 31 December 2025</p>" in reading.html
    assert reading.accepted and reading.accepted.net_income == (-225_000, -2_221_000)
