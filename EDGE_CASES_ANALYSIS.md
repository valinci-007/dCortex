# Comprehensive Edge Case Analysis: Tier 1 & Tier 2

## Context

The Crew Ops Advisor claims to pass:
- **Tier 1**: 16/16 questions (lookup & retrieval only)
- **Tier 2**: 14/14 questions (consequence & simulation)

This document identifies edge cases that the system may **not** be handling correctly or completely, acting as a hard judge.

---

## Tier 1: Lookup & Retrieval (Mandatory)

### 1. Off-base crew lookup with time-of-day ambiguity

**Edge Case**: "Who's on reserve at BLR tomorrow?"

**Potential Issues**:
- ✗ **Timezone handling at day boundary**: Crew is on reserve with window 06:00-18:00 UTC on day D. If "tomorrow" means UTC midnight-to-midnight but the question is asked at 23:30 UTC on day D, does the system correctly understand "tomorrow" = UTC day D+1?
  - **Code location**: `tools/query_tools.py::list_reserves` → `domain/timeutil.py`
  - **Test**: Q01 asks for reserves on "2026-09-15", snapshot is 2026-09-14T18:00Z. Does it handle the UTC date boundary correctly?
  - **Verdict**: Code uses ISO date boundaries (calendar day), so this is likely OK.

- ✗ **Reserve off-call window misclassification**: A crew member with on-call window 06:00-05:59 (overnight shift, wraps past midnight). Does the system classify this correctly?
  - **Code location**: `domain/models.py::ReserveEntry.covers()`
  - **Test**: No test data shows overnight reserve windows; all windows are contiguous within a UTC calendar day.
  - **Verdict**: **POTENTIAL ISSUE** — overnight windows not tested.

- ✗ **Reserve on multiple stations**: A reserve can only be at one base, but what if the data has duplicates or the system doesn't deduplicate?
  - **Code location**: `data/reserve_pool.json`, `repositories/reserves.py`
  - **Verdict**: Likely OK (single file, single record per crew), but no validation.

### 2. Duty clock / headroom calculation at period boundary

**Edge Case**: "How many duty hours does C-1042 have left this week?"

**Potential Issues**:
- ✗ **Rolling window calculation off by one day**: The 7-day window is "any 7 consecutive calendar days inclusive of the duty date". If today is Sep 14, and the question asks about "this week", does it mean:
  - Sep 14 → Sep 20 (7 days starting today)?
  - Sep 9 → Sep 15 (calendar week, or 7-day window ending today)?
  - The actual rule window is 7 consecutive days **ending on the duty date**.
  
  **Code location**: `rules/checks.py::window_start()` → computes window **ending** on the given day, going back N days.
  - **Test**: Test calls `check_duty_window(duty_by_date, end_date, ruleset)` with `end=today`. Correct.
  - **Verdict**: Likely OK for the tool contract, but the question's phrasing could mislead an LLM into asking the wrong end-date.

- ✗ **Zero-duty days included incorrectly**: If a crew member has no duties on day D (day off), does `daily_history` include it?
  - **Code location**: `tools/query_tools.py::get_duty_clock()` filters: `if h.duty_hours or h.flight_hours`
  - **Verdict**: Off-days are **excluded** from the response. An LLM trying to reconstruct the window could be confused if it assumes every calendar day is present. **Possible issue if LLM does math on a subset of visible days.**

- ✗ **Fractional hour precision**: Duty hours are stored as floats (e.g., 10.23 hours). Does rounding/truncation happen at the wrong layer?
  - **Code location**: `tools/query_tools.py::get_duty_clock()` returns raw floats; `rules/checks.py` rounds to 2 decimal places for comparisons.
  - **Verdict**: OK, but the LLM seeing 51.83h in an answer needs to understand this is compared against a limit of 60.0h with epsilon tolerance.

### 3. Flight lookup with "this afternoon" and ambiguous time

**Edge Case**: "Which flights depart DEL this afternoon?"

**Potential Issues**:
- ✗ **"This afternoon" interpretation**: The snapshot is 2026-09-14T18:00Z. Does "this afternoon" mean:
  - The next 4–6 hours (until midnight)?
  - 12:00–18:00 on 2026-09-14?
  - Or should it refuse because "afternoon" is ambiguous?
  
  **Code location**: `agent/prompts.py` (system prompt) — no explicit instruction on relative-time phrases.
  - **Verdict**: **The model must infer this.** If the model queries flights for 2026-09-14T12:00:00Z to 2026-09-14T23:59:59Z, it will likely get the right set. But if it queries 2026-09-14T18:00:00Z to 2026-09-14T21:00:00Z (literal "afternoon" = last 4h), it will miss earlier flights.
  - **Hard verdict**: **EDGE CASE NOT COVERED** — the repo assumes the model will interpret "this afternoon" sensibly, but doesn't enforce it.

- ✗ **Case sensitivity**: The tool says `dep_station.upper()`. What if a question says "Delhi" instead of "DEL"?
  - **Code location**: `tools/query_tools.py::list_flights()`
  - **Verdict**: Will fail silently (no match). System should refuse if station is not found.

- ✗ **No validation of station codes**: "Which flights depart ZZZ?" Will the system return empty list or refuse?
  - **Code location**: `tools/query_tools.py::list_flights()` does not validate station codes.
  - **Verdict**: Returns empty list silently. **OK behavior** (no error), but not explicit.

### 4. Crew expiry lookup with "next 30 days" ambiguity

**Edge Case**: "List crew whose licence expires in the next 30 days."

**Potential Issues**:
- ✗ **Next 30 days from when?** Does "next 30 days" mean:
  - 30 days from the snapshot (2026-09-14 → 2026-10-14)?
  - Literally calendar days or working days?
  - The system should use the snapshot as "now".
  
  **Code location**: `tools/query_tools.py::list_expiring_certifications()`
  - **Test**: Likely assumes snapshot date as "today".
  - **Verdict**: Probably OK if the tool uses `store.snapshot_utc.date()` as reference.

- ✗ **"Licence" vs "Certifications"**: The question says "licence", but the tool deals with "certifications". Do they mean the same thing?
  - **Code location**: `domain/models.py::Certification` — includes ratings, recurrent training, medical.
  - **Verdict**: The tool returns ALL expiring certifications (ratings, training, medical). The question might expect only certain types. **AMBIGUITY**, but probably OK.

- ✗ **Already expired vs. will expire**: Does the tool return only future expirations, or include "expired yesterday"?
  - **Code location**: `tools/query_tools.py::list_expiring_certifications()` likely uses `date >= today`.
  - **Verdict**: Probably OK, but implementation detail.

- ✗ **valid_from enforcement**: The README explicitly says "Certification `valid_from` dates are unreliable in the data… we enforce expiry only, as the organiser's validator does."
  - **Implication**: A crew member might have a cert with `valid_from` = 2026-09-15 but `valid_until` = 2026-10-01, and they operate on 2026-09-14. The system does NOT flag this as invalid.
  - **Verdict**: **INTENTIONAL LIMITATION**, acknowledged in docs.

---

## Tier 2: Consequence & Simulation (Strongly Expected)

### 5. Sick-call crew removal: when did they actually call in?

**Edge Case**: "Captain C-1042 just called in sick for tomorrow — which flights are now uncrewed?"

**Potential Issues**:
- ✗ **Reported time vs. duty date ambiguity**: If C-1042 calls in at 2026-09-15T05:00Z saying "I'm sick tomorrow", does that mean:
  - Tomorrow = 2026-09-16 (24h from now), OR
  - Tomorrow = calendar day 2026-09-16 (even if it's 23:59 UTC on 2026-09-15)?
  
  **Code location**: `simulation/engine.py::crew_removal()` uses `reported_utc.date()` or explicit `from_date` parameter.
  - **Test**: Q17/S2 has `reported_utc=2026-09-15T05:00:00Z` and expects flights on 2026-09-15 to be covered. So the question's "tomorrow" = 2026-09-15 (same day at 05:00Z).
  - **Verdict**: Implementation is correct, but the **model must correctly parse the call-in time** from the question. If the question is ambiguous, the model could use the wrong time.

- ✗ **Partial day vs. full pairing**: If C-1042 is sick at 05:00Z on a day he has two pairings (one in the morning, one in evening), does he lose:
  - Just the morning pairing?
  - Just the flights after 05:00Z?
  - The whole day's duties?
  
  **Code location**: `simulation/engine.py::crew_removal()` filters by `d.release_utc > reported_utc`.
  - **Test**: No test shows partial-day removal within a single pairing.
  - **Verdict**: **The code handles this correctly** (filters by release time), but the question's phrasing is ambiguous.

- ✗ **Crew with multiple pairings same day**: If a crew operates two separate pairings on the same day (e.g., P-2203 08:00–13:00 and P-2204 15:00–20:00), and calls in sick at 12:00Z:
  - Does the system correctly identify both as affected if they both have release_utc > 12:00Z?
  - Or does it stop after the first affected pairing?
  
  **Code location**: `simulation/engine.py::crew_removal()` — no `break` statement, so it continues.
  - **Verdict**: Should be OK, but untested scenario.

- ✗ **No duty that day**: "C-1042 just called in sick for tomorrow" — but C-1042 has no rostered duties tomorrow. What does the system return?
  - **Code location**: `simulation/engine.py::crew_removal()` sets `note = "no rostered duties on or after {date}"`.
  - **Verdict**: Correctly returns empty days list with a note.

### 6. Substitution legality: narrow down-stream conflicts

**Edge Case**: "If I move FO C-2087 onto DX412, does anyone breach a duty limit?"

**Potential Issues**:
- ✗ **Which day does DX412 operate?** The question doesn't specify. Does the system:
  - Assume "today" (snapshot)?
  - Ask for clarification?
  - Try all occurrences of DX412 in the schedule?
  
  **Code location**: `tools/query_tools.py::find_pairings()` — not clear if this supports "by flight number" queries.
  - **Verdict**: **The tool contract requires `pairing_id`**, not flight number. The model must resolve "DX412" → a pairing. If there are multiple pairings with DX412 legs, which one? **EDGE CASE NOT FULLY COVERED** — the model must infer or ask.

- ✗ **Just the one leg vs. the whole pairing**: "Move FO C-2087 onto DX412" — does this mean:
  - Just operate DX412 on that date, keeping other rostered duties?
  - Full pairing cover (replacing the current crew)?
  
  **Code location**: `simulation/engine.py::assignment_check()` checks the full pairing from `from_date` onward.
  - **Verdict**: System checks full pairing cover, which is the conservative/safe choice. But if the question means "just this one leg", the system will over-check.

- ✗ **Downstream conflicts: what counts?** C-2087 is assigned to cover P-2291 (Sep 15–16). He's also rostered on P-2204 (Sep 17). Does the system check:
  - Just the 7-day duty window?
  - Rest gaps with the 17-Sep duty?
  - All collisions up to 28 days?
  
  **Code location**: `rules/engine.py::evaluate_duties()` composes all seven rules over the full timeline (existing + proposed).
  - **Verdict**: **Correctly includes downstream conflicts** (Q28 test: C-5837 gets flagged for rest conflict with Sep 17 duty). Good.

- ✗ **Cost model for substitution**: The tool returns cost, but for a "move onto a pairing", is that:
  - The callout cost (reserve or day-off)?
  - Deadhead if off-base?
  - Or is the question asking only about legality (no cost)?
  
  **Code location**: `simulation/engine.py::assignment_check()` always computes cost.
  - **Verdict**: System always includes cost, which is helpful extra info. OK.

### 7. Station closure: simultaneous impact on crews at that station

**Edge Case**: "Station BLR is closed 14:00–20:00 — what's the crew impact?"

**Potential Issues**:
- ✗ **Closure affects departures, arrivals, or both?** If a flight is scheduled to arrive at 15:00 during closure, can it land?
  - **Code location**: `simulation/engine.py::station_closure()` — let me check the semantics.
  - **Test**: S3 test checks `affected_flights` list and per-flight assessments. The closure is used to compute minimum delay based on reopen time.
  - **Verdict**: The code assumes closure blocks departures (and turnaround at the station), computing the minimum delay as (reopen_time + turnaround_min) - scheduled_time. This is correct for a closure. But the question "what's the crew impact" is broader — does it include:
    - FDP breach impact?
    - Rest impact if a flight is delayed so much it pushes into next-day duties?
    - Passenger impact?
  
  **Hard verdict**: The tool returns per-flight FDP assessments but does **NOT** check rest conflicts with the day after. **EDGE CASE NOT COVERED** — if the delay pushes release past midnight and the crew has an early next-day duty, the system might miss the rest violation.

- ✗ **Closure window precision**: "14:00–20:00" — is this exactly 14:00:00Z to 20:00:00Z, or 14:00:00Z to 20:00:00Z inclusive? A flight departing at 20:00:01Z — is it blocked?
  - **Code location**: `simulation/engine.py::station_closure()` — uses simple time comparisons.
  - **Verdict**: Likely uses `dep_utc >= start and dep_utc <= end`, so edge-case times might be borderline. Not critical, but imprecise.

- ✗ **Overnight closures**: "BLR closed 22:00 on Sep 17 through 06:00 on Sep 18" — does the system handle multi-calendar-day closures?
  - **Code location**: `simulation/engine.py::station_closure()` takes `start_utc` and `end_utc` (both datetime). Should handle it, but no test data.
  - **Verdict**: **LIKELY UNTESTED** — no overnight closure scenario in test data.

### 8. Delay propagation: cascading into next duties

**Edge Case**: "VT-DXA is delayed 90 minutes on Sep 16; which legs can it still legally fly?"

**Potential Issues**:
- ✗ **Recrew vs. cancel**: The system computes `legal_leg_count` (how many of the 4 legs can the rostered crew still legally complete after delay). But:
  - Is "legal" computed with the delayed duty ending, or the original?
  - If legal_leg_count=3, can the system just recrew leg 4, or is it more complex?
  
  **Code location**: `simulation/engine.py::delay()` → computes FDP after delay, subtracts sectors until FDP is within limit.
  - **Verdict**: The logic is sound but assumes a simple binary: fly the prefix, recrew the tail. Real ops might have more nuance (passenger revenue impact, crew availability, etc.).

- ✗ **Rest impact after delay**: If a pairing is delayed until 23:00Z and the crew has an early next-day duty at 06:00Z, does the system recheck rest?
  - **Code location**: `simulation/engine.py::delay()` does NOT evaluate rest against next duties; it only computes FDP.
  - **Verdict**: **EDGE CASE NOT COVERED** — the delay might create a rest violation downstream that the system doesn't report.

- ✗ **Aircraft availability for recrew**: If the tail legs need recrew, does the system check:
  - Are there eligible reserves?
  - Can they reach the station in time?
  - Or does it just say "recrew is needed" without validation?
  
  **Code location**: `simulation/engine.py::delay()` does NOT enumerate candidates.
  - **Verdict**: Correctly stops at "recrew needed"; full cover planning is Tier 3.

### 9. Reserve availability: on-call window interpretation

**Edge Case**: "Can C-3310 (reserve, window 06:00–18:00Z) be called for a duty with report 05:55Z?"

**Potential Issues**:
- ✗ **Window boundary precision**: Is "06:00" inclusive or exclusive?
  - **Code location**: `domain/models.py::ReserveEntry.covers()` likely uses `>=` and `<` or `<=`.
  - **Test**: Q24 test checks "window 06:00-18:00Z does not cover required report 03:00Z" — this passes because 03:00 is before 06:00.
  - **Verdict**: Seems to work, but edge case (05:59Z vs 06:00Z) is not tested.

- ✗ **Reserve called during rest period**: A reserve has window 06:00–18:00Z but is resting (last duty ended at 02:00Z, 12h rest until 14:00Z). Can they be called at 07:00Z?
  - **Code location**: `simulation/engine.py::reserve_availability()` checks only the on-call window, NOT rest status.
  - **Verdict**: **EDGE CASE NOT COVERED** — a reserve in their mandatory rest period is not callable, but the system doesn't check this. The rules engine (RULE-REST-04) would catch it downstream, but the availability check is incomplete.

- ✗ **Overnight windows**: A reserve on-call 22:00–06:00 (overnight). Does the system handle wrapping?
  - **Code location**: `domain/models.py::ReserveEntry` — no evidence of overnight window support.
  - **Test data**: All reserves have daytime windows (e.g., 06:00–18:00).
  - **Verdict**: **LIKELY NOT SUPPORTED** — overnight on-call windows are not tested.

### 10. Rating/certification check: valid_from not enforced

**Edge Case**: "C-1042 is assigned to an A320 pairing, but his A320 rating is not yet valid (valid_from = 2026-09-16, duty is 2026-09-15)."

**Potential Issues**:
- ✗ **valid_from ignored**: The README explicitly states this is intentional, but it's still a real-world issue.
  - **Code location**: `rules/checks.py::check_rating()` does not check `valid_from`.
  - **Verdict**: **INTENTIONALLY UNCOVERED**, acknowledged in failure-cases docs.

- ✗ **Expired cert after end date**: A cert expires 2026-09-17 23:59Z. A duty on 2026-09-17 (ends release at 20:00Z) — is this legal?
  - **Code location**: `rules/checks.py::check_certifications()` uses `cert.valid_until >= duty.date`.
  - **Verdict**: A cert valid **until** Sep 17 is legal **on** Sep 17. This is correct.

### 11. Multi-day pairing with partial cover

**Edge Case**: "C-3310 covers just day 1 of P-2291 (2-day pairing), and someone else covers day 2."

**Potential Issues**:
- ✗ **Partial pairing enforcement**: The README admits: "Partial cover of a multi-day pairing is under-modelled."
  - **Code location**: `simulation/engine.py::crew_removal()` sets `cover_must_take_full_pairing=true` for multi-day pairings.
  - **Verdict**: The system **refuses** to split multi-day pairings, which is conservative. But the README notes that the offline grader "misses" some valid partial covers.
  
  **Edge case not covered**: Repatriating a crew member from a non-base station (aircraft overnight there). The system doesn't compute repatriation cost or next-day rest impact.

### 12. Crew near limits: inclusion criteria

**Edge Case**: "List all crew near their duty limit."

**Potential Issues**:
- ✗ **"Near limits" definition**: The tool likely returns crew with duty_hours > some threshold (e.g., 45h out of 60h). But:
  - Why 45h? Is this 75% of 60h?
  - What if a crew is at 59.9h? (1 hour headroom)
  - Does the system include all crew or just those who will breach if they pick up one more duty?
  
  **Code location**: `simulation/engine.py::near_limits()` — need to check threshold.
  - **Test**: Q26 checks for crew at 45h+. The implementation likely uses `duty_hours_7d >= some_threshold`.
  - **Verdict**: The exact threshold is implicit, not visible to the model.

### 13. Joint plans: simultaneous sick calls

**Edge Case**: "Captains C-1042 AND C-1600 are both out; which crew can cover BOTH pairings?"

**Potential Issues**:
- ✗ **Joint plan enumeration**: The README says Tier 3 handles "joint plans when several crew are out (no one assigned twice, cheapest total)."
  - **Tier 2 scope**: Tier 2 should handle individual sick-call simulations. Tier 3 is where you combine them.
  - **Verdict**: Not a Tier 2 issue, but worth noting that the offline router might struggle with this.

---

## Summary of Edge Cases by Severity

### Critical (Should definitely be handled, but aren't clearly):

1. **Overnight reserve on-call windows** — not tested, likely not supported.
2. **Overnight station closures** (across calendar day boundary) — not tested.
3. **Rest conflict detection after delay** — delay tool does not check downstream rest.
4. **Reserve rest status** — available-window check doesn't verify crew isn't in mandatory rest.
5. **Partial multi-day pairing cover** — explicitly unsupported; system refuses it.
6. **Repatriation cost/rest for multi-day pairings** — under-modelled.

### High (Edge case behavior but tested and working):

7. **Downstream duty conflicts** — handled correctly (Q28 tests this).
8. **Timezone/date boundary precision** — likely handled correctly but relies on model input.
9. **Empty query results** — returned silently instead of error (usually OK).
10. **Case sensitivity for station codes** — converted to upper case, but no validation.

### Medium (Implicit behavior, documented limitations):

11. **valid_from certification dates** — intentionally ignored (acknowledged).
12. **Duty clock zero-day filtering** — off-days excluded from response; could confuse LLM math.
13. **"This afternoon" interpretation** — no system guidance; relies on model.
14. **"Near limits" threshold** — implicit, not user-visible.

### Low (Likely OK, defensive):

15. **Fractional hour rounding** — handled with epsilon tolerance.
16. **Multiple pairings same day** — correctly filtered by release time.
17. **Crew with no duties on removed date** — correctly returns note.

---

## Recommendations for Testing (What to add)

1. **Overnight reserve windows** — create a test with `oncall_start > oncall_end` (wraps UTC midnight).
2. **Overnight closure** — closure start on Sep 17, end on Sep 18; verify all affected flights are found.
3. **Delayed duty with next-day conflict** — delay pushes release past midnight; next-day duty has rest conflict.
4. **Reserve in rest period** — call out a reserve during their 12h mandatory rest; should be refused.
5. **Partial pairing cover** — attempt to assign different crew to day 1 vs. day 2 of a 2-day pairing.
6. **Invalid station code** — query flights from "ZZZ"; should refuse or return empty with note.
7. **Duty clock with all zero-duty days** — crew on vacation; should return only non-zero history.
8. **Cert valid_from future date** — cert not yet valid but assigned; system does not catch (intentional).

---

## Final Verdict: Do Tier 1 & 2 Pass "Hard Judge" Inspection?

**Tier 1: Mostly yes, with small gaps**
- Lookup tools are deterministic and correct.
- **Gaps**: Overnight windows, case validation, ambiguous time interpretation (model's job, but system doesn't guide).
- **Verdict**: **STRONG** — 16/16 pass, but edge cases exist.

**Tier 2: Yes for tested scenarios, gaps in real-world edge cases**
- Simulation tools work correctly for the dataset's test cases.
- **Gaps**: Rest conflicts after delay, overnight closures, partial pairing, reserve rest status, repatriation modeling.
- **Verdict**: **GOOD** — 14/14 pass, but several real-world edge cases not covered.

**Overall**: The system is well-engineered for the challenge dataset but would need hardening for production (as the README acknowledges).
