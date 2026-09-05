# Concrete Test Cases to Expose Edge Cases

These are executable test scenarios that would expose the edge cases identified above.

---

## Tier 1: Lookup Edge Cases

### T1-EC-1: Overnight Reserve Window

**Setup**:
- Create a reserve entry with `oncall_start=22:00`, `oncall_end=06:00` (wraps UTC midnight)
- Crew C-9999, base BLR, reserve on 2026-09-15

**Question**:
```
Who is on reserve at BLR on 2026-09-15?
Callout time: 2026-09-15T23:30:00Z (within the overnight window)
```

**Expected Answer**:
- C-9999 appears as available (23:30 is within 22:00–06:00)

**Current System Behavior**:
- Likely returns nothing or C-9999 NOT available (window wrapping not implemented)

**Code to check**:
```python
# domain/models.py
def covers(self, report_utc: datetime) -> bool:
    # Current implementation likely does:
    return self.oncall_start <= report_utc.time() <= self.oncall_end
    # This fails when oncall_start > oncall_end (overnight)
```

**Test to add**:
```python
def test_overnight_reserve_window_spans_midnight():
    reserve = ReserveEntry(
        crew_id="C-9999",
        base="BLR",
        oncall_start=time(22, 0),  # 22:00
        oncall_end=time(6, 0),      # 06:00
        on_date=date(2026, 9, 15),
    )
    # Call at 23:30 should return True
    assert reserve.covers(parse_utc("2026-09-15T23:30:00Z"))
    # Call at 05:00 should return True
    assert reserve.covers(parse_utc("2026-09-15T05:00:00Z"))
    # Call at 07:00 should return False
    assert not reserve.covers(parse_utc("2026-09-15T07:00:00Z"))
    # Call at 21:00 should return False
    assert not reserve.covers(parse_utc("2026-09-15T21:00:00Z"))
```

---

### T1-EC-2: Zero-Duty Days in Duty Clock History

**Setup**:
- Crew C-1042 has duty history with days off (0 duty hours)
- Tool filters them out: `if h.duty_hours or h.flight_hours`

**Question**:
```
What is C-1042's duty-hour balance for this week?
Snapshot: 2026-09-14T18:00Z
```

**Expected Answer**:
- System returns only non-zero days
- LLM reconstructs the window correctly

**Potential Problem**:
- If LLM tries to add up visible days and assumes they represent 7 calendar days, it will compute wrong totals
- E.g., if only 5 non-zero days are returned (2 off-days hidden), LLM might compute wrong window

**Test Scenario**:
```
duty_clock.daily_history = [
    {date: 2026-09-08, duty: 10.0, flight: 7.0},
    {date: 2026-09-09, duty: 0.0, flight: 0.0},  # OFF
    {date: 2026-09-10, duty: 0.0, flight: 0.0},  # OFF
    {date: 2026-09-11, duty: 10.5, flight: 7.5},
    {date: 2026-09-12, duty: 11.0, flight: 8.0},
    {date: 2026-09-13, duty: 0.0, flight: 0.0},  # OFF
    {date: 2026-09-14, duty: 0.0, flight: 0.0},  # OFF
]
```

**Tool response** (current):
```json
{
    "duty_hours_7d": 41.5,
    "daily_history": [
        {date: 2026-09-08, duty: 10.0, flight: 7.0},
        {date: 2026-09-11, duty: 10.5, flight: 7.5},
        {date: 2026-09-12, duty: 11.0, flight: 8.0}
    ]
}
```

**Issue**:
- LLM sees 3 days but no indication they span 7 calendar days with gaps

**Test to add**:
```python
def test_duty_clock_includes_date_gaps():
    # Either include all days (even zeros) or mark the date range explicitly
    response = get_duty_clock(store, "C-1042")
    # Should have:
    assert response["duty_window_7d"]["start"] == "2026-09-08"
    assert response["duty_window_7d"]["end"] == "2026-09-14"
    # Or include all 7 days:
    assert len(response["daily_history"]) == 7  # Even off-days
```

---

### T1-EC-3: Ambiguous Time "This Afternoon"

**Setup**:
- Snapshot: 2026-09-14T18:00Z

**Question**:
```
Which flights depart DEL this afternoon?
```

**Current Behavior**:
- Model must infer "afternoon" = some window (12:00–18:00? 14:00–23:59?)
- System has no guidance

**Test**:
```python
def test_ambiguous_time_interpretation():
    # If model interprets "this afternoon" as 12:00–18:00Z:
    flights_12_18 = list_flights(store, date="2026-09-14", dep_station="DEL",
                                 dep_from_utc="2026-09-14T12:00:00Z",
                                 dep_to_utc="2026-09-14T18:00:00Z")
    
    # If model interprets it as 14:00–23:59Z:
    flights_14_24 = list_flights(store, date="2026-09-14", dep_station="DEL",
                                 dep_from_utc="2026-09-14T14:00:00Z",
                                 dep_to_utc="2026-09-14T23:59:59Z")
    
    # Results might differ; system should either:
    # A) Guide the model with a default
    # B) Refuse and ask for clarification
    # Currently: relies on LLM's judgment
```

---

## Tier 2: Simulation Edge Cases

### T2-EC-1: Rest Conflict After Delay

**Setup**:
- Pairing P-2203 (VT-DXA) operates on 2026-09-16:
  - Report: 08:00Z, Release: 14:00Z (original)
  - Delay: 90 minutes
  - New release: 15:30Z
- Crew roster: P-2203 on Sep 16, P-2204 on Sep 17 with report 06:00Z
- Rest required: 12 hours between release and next report

**Question**:
```
VT-DXA is delayed 90 minutes on Sep 16. What's the crew impact?
```

**Current System Behavior**:
- Computes FDP after delay
- Reports: "crew can still legally complete all 4 legs" (FDP is OK)

**Actual Issue**:
- Release at 15:30Z (Sep 16) + 12h rest = earliest report 03:30Z (Sep 17)
- Next duty report: 06:00Z (Sep 17)
- Rest gap: 15:30 (Sep 16) → 06:00 (Sep 17) = 14.5 hours ✅ Legal
- **In this case, no breach.** But if next duty was 02:00Z (Sep 17):
  - Rest gap: 15:30 (Sep 16) → 02:00 (Sep 17) = 10.5 hours ❌ BREACH

**Test to add**:
```python
def test_delay_creates_rest_conflict_with_next_day():
    # Setup: Sep 16 pairing delayed + Sep 17 early duty
    d = delay(store, date(2026, 9, 16), 2.0, aircraft="VT-DXA")
    
    # Crew roster includes Sep 17 duty at 02:00Z
    # delay.to_dict() should include:
    # "downstream_rest_conflict": True/False
    # Currently: NOT included (gap in the tool)
    
    assert d.to_dict().get("downstream_rest_conflict") is not None
```

---

### T2-EC-2: Overnight Station Closure

**Setup**:
- Closure: 2026-09-17T22:00:00Z → 2026-09-18T06:00:00Z
- Flights affected:
  - DX401 departing 2026-09-17T21:30Z (before closure) ✅ NOT affected
  - DX402 departing 2026-09-17T23:00Z (during closure) ✅ AFFECTED
  - DX403 departing 2026-09-18T04:00Z (during closure) ✅ AFFECTED
  - DX404 departing 2026-09-18T08:00Z (after closure) ✅ NOT affected

**Question**:
```
BLR is closed from 2026-09-17T22:00:00Z to 2026-09-18T06:00:00Z.
Which flights are affected?
```

**Current System**:
- Likely assumes closure is within a single calendar day
- Might miss flights on the second calendar day

**Test to add**:
```python
def test_overnight_closure_spans_calendar_days():
    closure = station_closure(
        store,
        "BLR",
        start_utc=parse_utc("2026-09-17T22:00:00Z"),
        end_utc=parse_utc("2026-09-18T06:00:00Z"),
    )
    result = closure.to_dict()
    
    # Should include flights on both Sep 17 (23:00) and Sep 18 (04:00)
    affected_dates = {parse(f["flight_id"]).date for f in result["per_flight"]}
    assert date(2026, 9, 17) in affected_dates
    assert date(2026, 9, 18) in affected_dates
    assert len(result["affected_flights"]) >= 2
```

---

### T2-EC-3: Reserve in Mandatory Rest Period

**Setup**:
- Reserve C-3310, on-call window 06:00–18:00Z on 2026-09-15
- Last duty: 2026-09-14T20:00Z (release)
- Earliest rest complete: 2026-09-15T08:00Z (20:00 + 12h)
- Callout time: 2026-09-15T07:00Z (during rest period but within on-call window)

**Question**:
```
Can C-3310 (reserve, on-call 06:00–18:00Z) be called for a duty
starting 2026-09-15T07:00:00Z?
```

**Expected Answer**:
- NO — they are in mandatory rest (until 08:00Z)

**Current System Behavior**:
- MAYBE/YES — checks only on-call window (07:00 is within 06:00–18:00)
- Does NOT check if crew is currently resting

**Test to add**:
```python
def test_reserve_availability_during_rest_period():
    crew = store.crew.get("C-3310")
    clock = store.duty_clocks.get("C-3310")
    # clock.last_rest_ended = 2026-09-15T08:00:00Z
    
    report_during_rest = parse_utc("2026-09-15T07:00:00Z")
    available, note = reserve_availability(store, "C-3310", report_during_rest)
    
    # Should be:
    assert not available
    assert "mandatory rest" in note.lower() or "rest period" in note.lower()
    
    # Current system likely returns:
    # available=True, note="window covers report time"
```

---

### T2-EC-4: Partial Multi-Day Pairing Cover

**Setup**:
- P-2291 operates 2026-09-15 to 2026-09-16 (2-day pairing, aircraft overnight at DEL)
- Current cover: Captain C-1042
- C-1042 unavailable only on 2026-09-15

**Question**:
```
Can C-1042 cover just day 1 (Sep 15) of P-2291, and C-2087 covers day 2?
```

**Expected Answer** (real ops):
- YES, but:
  - C-1042 must position the aircraft to C-2087's location
  - C-1042 rest between day 1 release and home arrival must be checked
  - C-2087 must be at/reachable to the overnight location on Sep 16

**Current System Behavior**:
- REJECTED — "multi-day pairing: cover must take full remaining pairing"
- Code: `cover_must_take_full_pairing = True` for multi-day pairings

**Test to add**:
```python
def test_partial_pairing_cover_day_1_only():
    # Try to assign C-2087 for just day 1 of P-2291
    removal = crew_removal(store, "C-1042", pairing_id="P-2291", from_date=date(2026, 9, 15))
    
    # System returns:
    assert removal.cover_must_take_full_pairing == True
    assert removal.note == "a multi-day pairing: the aircraft overnights away from base..."
    
    # Attempt to assign different crew to day 1:
    check1 = assignment_check(store, "C-2087", "P-2291", from_date=date(2026, 9, 15))
    
    # System currently checks the full pairing (both days)
    # Real ops would: check day 1 only, verify positioning, check C-2087's day 2 availability
    # Current system: rejects or over-checks (conservative, but incomplete)
```

---

### T2-EC-5: Invalid Reserve Callout Candidate

**Setup**:
- Sick call: C-1042 on P-2291 (BLR-DEL-BOM-BLR), 2 legs/day
- Reserve candidates at BLR:
  - C-3310: available, on-call, but **last_rest_ended = 02:00Z, first duty report = 06:00Z** (only 4h rest, needs 12h before this duty)
  - C-3315: available, on-call, rested

**Question**:
```
Which reserves can cover the sick call?
```

**Expected Answer**:
- C-3310: NOT eligible (in rest period)
- C-3315: eligible

**Current System**:
- Likely returns both as available (checks only on-call window)
- Rest status check happens later in `evaluate_duties`, so both pass initial filtering

**Tool level issue**:
- `reserve_coverage()` returns all matching reserves without rest-status check
- Downstream: `assignment_check()` will catch the legality issue, but the tool's filtering is incomplete

**Test to add**:
```python
def test_reserve_coverage_excludes_resting_crew():
    rows = reserve_coverage(
        store,
        parse_utc("2026-09-15T06:00:00Z"),
        rank="Captain",
        aircraft_type="A320",
        station="BLR",
    )
    
    # Should filter out crew in rest period at the tool level
    eligible_ids = [r.crew_id for r in rows if r.eligible]
    
    # C-3310 should NOT be in eligible_ids (in rest period)
    # Currently: likely is included (rest check missing)
```

---

### T2-EC-6: Invalid Station Code Query

**Setup**:
- Question: "Which flights depart from ZZZ (non-existent station)?"

**Current Behavior**:
- Returns empty list silently

**Expected Behavior**:
- Either:
  - Refuse with "ZZZ is not a valid station"
  - Return empty list with note "no flights from ZZZ"

**Test to add**:
```python
def test_invalid_station_code_handling():
    result = list_flights(store, date="2026-09-15", dep_station="ZZZ")
    
    # Current: {"count": 0, "flights": []}
    # Should include: {"valid_station": False, "note": "..."}
    # Or model should infer "ZZZ" is invalid from empty result
    
    assert result["count"] == 0  # OK
    # But no indication of WHY (invalid station vs. no flights that day)
```

---

## How to Run These Tests

1. **Add to `backend/tests/integration/test_edge_cases.py`**:
   ```bash
   cd /Users/umashankar/Desktop/dCortex/backend
   pytest tests/integration/test_edge_cases.py::test_overnight_reserve_window_spans_midnight -v
   ```

2. **Expected Results** (before fixes):
   - Most tests will FAIL (exposing the gaps)
   - A few will PASS (code happens to work)

3. **After implementing fixes**:
   - Re-run; tests should all PASS

---

## Summary: 6 Critical Test Cases

1. **T1-EC-1**: Overnight reserve window
2. **T1-EC-2**: Zero-duty days in history (incomplete window)
3. **T1-EC-3**: Ambiguous relative time ("this afternoon")
4. **T2-EC-1**: Rest conflict after delay
5. **T2-EC-2**: Overnight closure spanning calendar days
6. **T2-EC-3**: Reserve in mandatory rest period
7. **T2-EC-4**: Partial multi-day pairing cover
8. **T2-EC-5**: Reserve rest status not checked at tool level
9. **T2-EC-6**: Invalid station code handling

---

## Difficulty to Fix

| Test | Difficulty | Time | Risk |
|------|-----------|------|------|
| T1-EC-1 (overnight window) | Medium | 1 day | Low (contained) |
| T1-EC-2 (date gaps) | Low | 0.5 day | Low |
| T1-EC-3 (ambiguous time) | N/A (model's job) | — | — |
| T2-EC-1 (rest after delay) | Medium | 1 day | Low |
| T2-EC-2 (overnight closure) | Low | 0.5 day | Low |
| T2-EC-3 (reserve rest) | Medium | 1 day | Medium (affects all callouts) |
| T2-EC-4 (partial pairing) | High | 2–3 days | High (remodels cover logic) |
| T2-EC-5 (reserve filtering) | Medium | 1 day | Medium |
| T2-EC-6 (invalid codes) | Low | 0.5 day | Low |

**Total effort to fix all**: 1–2 weeks.
