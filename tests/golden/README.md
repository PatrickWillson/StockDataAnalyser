# Golden Baseline Tests

This directory contains golden baseline files used to validate that refactoring does not introduce behavioral changes.

## Purpose

The golden baseline tests ensure that the refactored code produces **byte-for-byte identical output** to the original implementation. This is critical for maintaining the deterministic nature of Graham methodology calculations.

## Files

- `AAPL_US_baseline.md` - Apple Inc. (US stock, NASDAQ)
- `YU_LSE_baseline.md` - Yu Group PLC (UK stock, London Stock Exchange)
- `RY_TO_baseline.md` - Royal Bank of Canada (Canadian stock, Toronto Stock Exchange)

These three tickers were chosen to cover:
- Different exchanges (US, UK, Canada)
- Different currencies (USD, GBP, CAD)
- Different company characteristics (large cap tech, small cap utility, large cap financial)

## Usage

### Capture Baseline (Before Refactoring)

Run this ONCE before starting refactoring:

```bash
pytest tests/test_golden_baseline.py::test_capture_baseline -v -m golden
```

This will:
1. Fetch live data for all three tickers
2. Run the complete analysis workflow
3. Save the output to golden baseline files

### Verify Output (After Refactoring)

Run this AFTER each refactoring phase:

```bash
pytest tests/test_golden_baseline.py::test_verify_output_unchanged -v -m golden
```

This will:
1. Fetch live data for all three tickers
2. Run the analysis with refactored code
3. Compare output byte-for-byte against baseline
4. Report any differences

### Quick Checks (No API Calls)

Check that golden files exist and contain expected sections:

```bash
pytest tests/test_golden_baseline.py::test_golden_files_exist -v
pytest tests/test_golden_baseline.py::test_golden_files_contain_expected_sections -v
```

## Baseline Capture Date

These baseline files were captured on: **2026-01-21**

## Important Notes

1. **Deterministic Output**: The system must produce identical output for identical input. Any difference indicates a behavioral change.

2. **Date Sensitivity**: The dossier includes the current date in the header. The verification test accounts for this by comparing the substantive content.

3. **API Dependencies**: The verification test makes live API calls, so it requires:
   - Valid EODHD_API_KEY in .env file
   - Network connectivity
   - API rate limits not exceeded

4. **Refactoring Phases**: Run the verification test after each phase:
   - Phase 1: After extracting DTOs, Config, and Logging
   - Phase 2: After extracting Dossier Generator
   - Phase 3: After extracting Currency Converter and Factory
   - Phase 4: Final validation

5. **Failure Handling**: If verification fails:
   - Review the diff output to identify what changed
   - Determine if the change is intentional or a bug
   - Fix the refactored code to match baseline behavior
   - Re-run verification

## Test Statistics

- **Total baseline files**: 3
- **Total lines**: ~1,093 lines
- **Average file size**: ~17 KB
- **Sections per file**: 10+ major sections

## Requirements Validated

- **Requirement 7.9**: Golden test baseline created for 3+ tickers
- **Requirement 7.10**: Output matches baseline exactly (byte-for-byte)
- **Requirement 7.1**: Same input produces same output (deterministic)
- **Requirement 7.8**: All existing tests pass without modification

## Next Steps

1. ✅ Golden baseline files created
2. ✅ Verification tests implemented
3. ⏳ Begin Phase 1 refactoring (DTOs, Config, Logging)
4. ⏳ Run verification after Phase 1
5. ⏳ Continue through remaining phases
6. ⏳ Final validation with all tests passing
