"""ocr_statement_reader: synthetic OCR words (no tesseract) -> rows -> statement, with its checks."""

from clients.ocr_statement_reader import (Word, is_candidate_page, is_statement_page, read_statement, rows_from_words,
                                          unit_token, words_from_tesseract)

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


def test_an_auditors_paragraph_naming_the_statement_does_not_confirm():
    audit = ("Independent auditor's report\nIn our opinion the consolidated income statement gives a true and fair view\n"
             "We have audited revenue 1,234 and profit before tax 5,678 " + "12,345 " * 12)
    assert not is_statement_page(audit)


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
