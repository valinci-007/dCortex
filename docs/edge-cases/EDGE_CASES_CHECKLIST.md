# Quick Reference: Edge Cases Checklist

## Tier 1 Lookup Edge Cases

| Edge Case | Status | Severity | Notes |
|-----------|--------|----------|-------|
| Overnight reserve windows (22:00–06:00) | ❌ Not tested | HIGH | No test data; window wrapping not verified |
| Off-base crew in multi-base system | ✅ OK | LOW | Each crew has one base; lookup works |
| Zero-duty days in duty_clock history | ✅ Filtered | MED | Off-days excluded; could confuse LLM math |
| "This afternoon" time interpretation | ⚠️ Model-dependent | MED | No system guidance; relies on LLM |
| Invalid station codes (e.g., "ZZZ") | ✅ Silent | LOW | Returns empty list; acceptable |
| Case sensitivity (e.g., "delhi" vs "DEL") | ✅ Converted | LOW | Uppercased; no validation |
| Certification valid_from dates | ❌ Ignored | HIGH | Intentional limitation (acknowledged) |
| Multiple pairings on same day | ✅ OK | LOW | Filtered correctly by release time |
| Relative dates ("next 30 days") | ✅ OK | LOW | Uses snapshot as reference |

---

## Tier 2 Simulation Edge Cases

| Edge Case | Status | Severity | Notes |
|-----------|--------|----------|-------|
| **Sick Call / Crew Removal** | | | |
| Partial day sick call (only afternoon duties) | ✅ OK | LOW | Filtered by `release_utc > reported_utc` |
| Multi-pairing single-day removal | ❌ Not tested | MED | Code supports it; no test case |
| Crew with no duties on removed date | ✅ OK | LOW | Returns note; correct behavior |
| **Substitution Legality** | | | |
| Flight number without pairing context | ⚠️ Ambiguous | MED | Model must resolve to pairing; no validation |
| Partial pairing cover (day 1 vs. day 2) | ❌ Explicitly refused | HIGH | System rejects multi-day splits |
| Downstream rest conflicts | ✅ OK | LOW | Correctly detected (Q28 tests this) |
| Off-base crew without deadhead | ✅ OK | LOW | Computed correctly |
| **Station Closure** | | | |
| Overnight closure (spans UTC midnight) | ❌ Not tested | MED | Code supports datetime range; no test data |
| Rest conflict after delayed flight | ❌ Not checked | HIGH | Delay tool only checks FDP, not rest |
| Turnaround time precision | ⚠️ Implicit | LOW | Uses fixed 30-min turnaround |
| Affected flights at arrival vs. departure | ✅ OK | LOW | Both checked correctly |
| **Delay Propagation** | | | |
| Delayed duty with next-day rest breach | ❌ Not checked | HIGH | Delay tool doesn't check downstream rest |
| Recrew eligibility verification | ✅ Skipped | LOW | Tier 3 responsibility (correct scope) |
| Aircraft utilization after recrew | ✅ Skipped | LOW | Tier 3 responsibility |
| **Reserve Availability** | | | |
| Reserve in mandatory rest period | ❌ Not checked | HIGH | Only checks on-call window, not rest status |
| Overnight on-call window (22:00–06:00) | ❌ Not supported | HIGH | No evidence of window wrapping |
| Window boundary precision (05:59 vs. 06:00) | ⚠️ Implicit | LOW | Likely uses >= and <= correctly |
| **Ratings & Certifications** | | | |
| Valid_from not enforced | ❌ Ignored | HIGH | Acknowledged in docs; intentional |
| Cert expires at 23:59Z on duty date | ✅ OK | LOW | Uses `valid_until >= duty.date` |
| Multiple rating types (ratings vs. certs) | ✅ OK | LOW | All checked via rules engine |
| **Multi-day Pairings** | | | |
| Partial pairing cover (crew hand-off) | ❌ Rejected | HIGH | System forces full-pairing cover |
| Repatriation cost/rest after day 1 | ❌ Not modeled | HIGH | README acknowledges this gap |
| Aircraft overnight location | ✅ Used | LOW | Determines deadhead requirement |
| **Crew Near Limits** | | | |
| "Near limits" threshold definition | ⚠️ Implicit | LOW | Likely 75% of limit; not exposed |
| Crew with zero duties in window | ✅ OK | LOW | Would appear as < threshold |
| Joint plan for multiple sick calls | ✅ Skipped | LOW | Tier 3 responsibility |

---

## Test Coverage Matrix

### Tier 1 Questions (16 total)

| ID | Question | Edge Cases Covered |
|----|----------|-------------------|
| Q01 | Reserves at BLR on date | ✅ Basic window lookup |
| Q02–Q10 | Various lookups (flights, crew, duty, certs) | ✅ Basic queries |
| Q11–Q16 | More lookups (routes, risk, etc.) | ✅ Basic aggregations |

**Missing**: Overnight windows, invalid codes, time-of-day ambiguity.

### Tier 2 Questions (14 total)

| ID | Question | Edge Cases Covered |
|----|----------|-------------------|
| Q17–Q22 | Sick calls, assignment legality, closures | ✅ Tested |
| Q23–Q30 | Delay, cancellation, reserves, timings | ✅ Tested |

**Missing**: Overnight closures, rest after delay, reserve during rest period, partial pairing cover.

---

## Severity Distribution

### By Severity:
- **Critical (not covered)**: 6 edge cases
  - Overnight windows (reserve & closure)
  - Rest after delay
  - Reserve in rest period
  - Partial pairing cover (rejected)
  - Repatriation model
  - valid_from enforcement

- **High (not covered)**: 3 edge cases (listed above overlap with critical)

- **Medium (edge case but OK)**: 5 edge cases
  - Downstream conflicts ✅ (tested)
  - Multi-pairing removal (untested but likely works)
  - Case sensitivity (converted)
  - "Near limits" threshold (implicit)
  - Relative time interpretation (model's job)

- **Low (likely OK)**: 8 edge cases
  - Silent empty results
  - Cert boundary dates
  - Fractional hour rounding
  - etc.

---

## What the README Says (vs. Reality)

| Claim | Reality |
|-------|---------|
| "Tier 1 16/16 & Tier 2 14/14 pass" | ✅ True for dataset answer keys |
| "Every non-trivial answer carries reasoning" | ✅ True; grounding check enforces |
| "Legality is exact arithmetic" | ✅ True; rules engine is pure |
| "Multi-day pairings handled correctly" | ⚠️ Partial; full cover forced |
| "Deterministic core is stateless" | ✅ True |
| "Closes to production grade" | ❌ Gap: rest after delay, overnight windows, partial covers |

---

## For Hard Judges

### Would a Hard Judge Pass Tier 1?
- **Raw score**: 16/16 ✅
- **Quality**: Good, but
  - Overnight windows untested
  - Case validation missing
  - Time interpretation vague
- **Verdict**: **PASS with reservations**

### Would a Hard Judge Pass Tier 2?
- **Raw score**: 14/14 ✅
- **Quality**: Good, but
  - Rest after delay not checked (HIGH SEVERITY)
  - Overnight closures untested (MED)
  - Reserve rest status not verified (HIGH)
  - Partial pairing rejected, not handled (HIGH)
- **Verdict**: **PASS, but with significant edge-case gaps**

### Production Readiness?
- **Not ready** for real airline ops.
- **Why**: Real disruptions include overnight closures, rest conflicts, partial covers, and reserve fatigue rules that the system doesn't fully model.
- **What's needed**: +2–3 weeks to add the 6 critical gaps.

---

## Next Steps to Close Gaps

If you want to harden the system to production-grade:

1. **Add overnight window support** (1 day)
   - File: `domain/models.py::ReserveEntry.covers()`
   - Change: Implement wrapping window logic

2. **Rest-after-delay check** (2 days)
   - File: `simulation/engine.py::delay()`
   - Add: Evaluate rest against next-day duties

3. **Reserve rest status check** (1 day)
   - File: `simulation/engine.py::reserve_availability()`
   - Add: Compare reserve rest window with duty timeline

4. **Overnight closure support** (1 day)
   - File: `simulation/engine.py::station_closure()`
   - Test: Add test data with overnight closure

5. **Partial pairing modeling** (3 days)
   - File: `simulation/options.py`
   - Change: Enumerate partial covers, compute repatriation

6. **Valid_from enforcement** (1 day)
   - File: `rules/checks.py::check_certifications()`
   - Change: Add `valid_from <= duty.date` check

**Total effort**: ~1 week to close all critical gaps.
