# Edge Case Test Suite Setup & Execution

**For**: Your colleague's PC (with Claude API key access)  
**Goal**: Run edge case tests and report results back to you

---

## Pre-requisites

Before running these tests, ensure your colleague has:

```bash
# Check Python version (need 3.11+)
python3 --version

# Set Claude API key
export ANTHROPIC_API_KEY="sk-ant-xxxxx"  # Your colleague's actual key

# Verify key is set
echo $ANTHROPIC_API_KEY  # Should show the key (not empty)
```

---

## Quick Start (3 steps)

### Step 1: Pull Your Latest Code
```bash
cd /Users/umashankar/Desktop/dCortex
git pull origin rajesh-dev
```

### Step 2: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Run the Edge Case Tests

**Tier 1 tests** (lookups and query tools):
```bash
python -m pytest tests/integration/test_edge_cases_tier1.py -v
```

**Tier 2 tests** (simulations and consequences):
```bash
python -m pytest tests/integration/test_edge_cases_tier2.py -v
```

**Run both together**:
```bash
python -m pytest tests/integration/test_edge_cases_tier1.py tests/integration/test_edge_cases_tier2.py -v
```

---

## Expected Output

When tests run, output will look like:

```
tests/integration/test_edge_cases_tier1.py::TestTier1EdgeCases::test_overnight_reserve_window_wraps_midnight PASSED
tests/integration/test_edge_cases_tier1.py::TestTier1EdgeCases::test_zero_duty_days_excluded_from_history PASSED
tests/integration/test_edge_cases_tier1.py::TestTier1EdgeCases::test_station_code_validation_error_handling PASSED
...
tests/integration/test_edge_cases_tier2.py::TestTier2EdgeCases::test_rest_conflict_after_delay_not_detected FAILED
tests/integration/test_edge_cases_tier2.py::TestTier2EdgeCases::test_reserve_rest_status_verification_incomplete FAILED
...

===== 13 passed, 6 failed, 1 skipped in 45.23s =====
```

---

## What Each Test Checks

### Tier 1 Tests (13 total) — Lookups & Query Tools

1. **test_overnight_reserve_window_wraps_midnight** — Checks if 22:00-06:00 window works
2. **test_zero_duty_days_excluded_from_history** — Verifies off-days filtered correctly
3. **test_station_code_validation_error_handling** — Invalid codes return errors
4. **test_ambiguous_relative_time_parsing** — Relative times (e.g., "afternoon") handled
5. **test_crew_with_multiple_pairings_same_day** — Multiple pairings per day supported
6. **test_certification_valid_from_date_enforcement** — Cert dates returned
7. **test_crew_reachability_status_field** — Reachability included in crew record
8. **test_reserve_window_boundary_precision** — 05:59 vs 06:00 boundary behavior
9. **test_near_limits_threshold_definition** — "Near limit" defined numerically
10. **test_query_tool_schema_validation_rejects_invalid_input** — Bad input rejected
11. **test_duty_clock_7day_window_precision** — 7-day window clearly defined
12. **test_flight_time_28day_window_precision** — 28-day window clearly defined
13. **test_multiple_certifications_per_crew_same_type** — Multiple certs returned

### Tier 2 Tests (13 total) — Simulations & Consequences

1. **test_rest_conflict_after_delay_not_detected** — **KNOWN FAIL** — Delay tool doesn't check downstream rest
2. **test_reserve_rest_status_verification_incomplete** — **KNOWN FAIL** — Reserve rest period not checked
3. **test_overnight_station_closure_spans_calendar_days** — Closure detection across days
4. **test_partial_multi_day_pairing_covers_rejected** — **KNOWN FAIL** — System rejects valid partial covers
5. **test_repatriation_logic_missing_for_partial_covers** — **KNOWN FAIL** — Repatriation not implemented
6. **test_crew_removal_with_downstream_pairings** — Cascading removal impact
7. **test_delay_impact_with_multiple_rule_violations** — Multiple rules checked on delay
8. **test_cancellation_impact_on_following_connections** — Cancellation cascades
9. **test_reserve_coverage_exhaustion** — Reserve pool depletion handling
10. **test_legality_evidence_objects_structure** — Verdicts have complete structure
11. **test_simulation_tool_output_consistency** — Tools return consistent JSON
12. **test_duty_clock_updates_after_simulation** — Clock state accurate after simulation
13. **test_grounding_check_enforces_evidence_requirement** — All numbers grounded in evidence

---

## Interpreting Results

### PASSED ✅
Test ran successfully, no edge case detected. System handles this scenario correctly.

### FAILED ❌
Test exposed an edge case. One of these:
- **Known gap**: Already documented in analysis (rest-after-delay, reserve-rest, partial covers, repatriation)
- **Unexpected issue**: Something we didn't anticipate; needs investigation

### SKIPPED ⊘
Test couldn't run (e.g., feature not yet implemented). Check test file comments for reason.

---

## Detailed Output (For Troubleshooting)

To see **full error messages** and stack traces:

```bash
python -m pytest tests/integration/test_edge_cases_tier1.py -vv
```

(Note: `-vv` = very verbose, shows all assertions and errors)

To run **just one specific test**:

```bash
python -m pytest tests/integration/test_edge_cases_tier1.py::TestTier1EdgeCases::test_overnight_reserve_window_wraps_midnight -v
```

To **capture full output to a file**:

```bash
python -m pytest tests/integration/test_edge_cases_tier1.py tests/integration/test_edge_cases_tier2.py -v > test_results.txt 2>&1
```

Then send `test_results.txt` back to you.

---

## If Tests Fail

1. **Check API key**: `echo $ANTHROPIC_API_KEY`
2. **Check database**: Verify `backend/data/*.json` files exist
3. **Check dependencies**: `pip install -r requirements.txt` again
4. **Check Python version**: Need Python 3.11+

If still failing, run with debug output:

```bash
python -m pytest tests/integration/test_edge_cases_tier1.py -vv --tb=long
```

---

## What to Report Back

After running tests, your colleague should send you:

1. **Test output** (pass/fail counts)
2. **Failed test names** (which specific tests failed)
3. **Error messages** (full stack traces for any failures)
4. **Python version** (output of `python3 --version`)
5. **Environment confirmation** (that `ANTHROPIC_API_KEY` was set)

This info will help diagnose whether failures are:
- Expected (known gaps we already identified)
- Unexpected (new issues we need to fix)
- Environmental (API key, dependencies, version issues)

---

## Summary Commands (Copy-Paste)

```bash
# Full setup in one block:
cd /Users/umashankar/Desktop/dCortex
git pull origin rajesh-dev
cd backend
pip install -r requirements.txt

# Run all edge case tests:
export ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"
python -m pytest tests/integration/test_edge_cases_tier1.py tests/integration/test_edge_cases_tier2.py -v

# Save results to file:
python -m pytest tests/integration/test_edge_cases_tier1.py tests/integration/test_edge_cases_tier2.py -v > edge_case_test_results.txt 2>&1
echo "Results saved to edge_case_test_results.txt"
```

---

## Questions?

If tests don't run or produce unexpected results:
1. Check the error message carefully
2. Verify API key is set: `echo $ANTHROPIC_API_KEY`
3. Run a single test with verbose output
4. Share the error with you for diagnosis

**Expected result**: Some tests will FAIL (the known gaps we documented). This is expected and confirms our analysis was correct.
