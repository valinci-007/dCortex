# Eval report — offline

Run: 2026-09-05T05:18:51Z · **37/38** questions with all expected facts recalled · latency p50 1 ms / p95 12 ms / max 23 ms

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 1 |
| Q02 | 1 | ✅ |  | get_crew, get_duty_clock | 1 |
| Q03 | 1 | ✅ |  | list_flights | 0 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 1 |
| Q05 | 1 | ✅ |  | get_flight | 0 |
| Q06 | 1 | ✅ |  | get_crew | 0 |
| Q07 | 1 | ✅ |  | get_crew | 0 |
| Q08 | 1 | ✅ |  | get_pairing | 0 |
| Q09 | 1 | ✅ |  | list_flights | 0 |
| Q10 | 1 | ✅ |  | list_flights | 1 |
| Q11 | 1 | ✅ |  | list_crew | 0 |
| Q12 | 1 | ✅ |  | schedule_stats | 1 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 0 |
| Q14 | 1 | ✅ |  | list_routes | 1 |
| Q15 | 1 | ✅ |  | find_pairings | 1 |
| Q16 | 1 | ✅ |  | get_risk_signal | 0 |
| Q17 | 2 | ✅ |  | simulate_crew_removal | 0 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 1 |
| Q19 | 2 | ✅ |  | station_closure_impact | 3 |
| Q20 | 2 | ✅ |  | simulate_delay | 3 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 2 |
| Q22 | 2 | ✅ |  | check_rostered_legality | 1 |
| Q23 | 2 | ✅ |  | earliest_next_report | 0 |
| Q24 | 2 | ✅ |  | check_assignment_legality | 1 |
| Q25 | 2 | ✅ |  | cancellation_impact | 0 |
| Q26 | 2 | ✅ |  | crew_near_limits | 23 |
| Q27 | 2 | ✅ |  | get_pairing, reserve_coverage | 1 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 1 |
| Q29 | 2 | ✅ |  | station_closure_impact | 1 |
| Q30 | 2 | ✅ |  | seats_at_risk | 1 |
| Q31 | 3 | ✅ |  | recommend_cover | 7 |
| Q32 | 3 | ✅ |  | joint_cover_plan | 9 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | resolve_delay_options | 5 |
| Q34 | 3 | ✅ |  | recommend_cover | 12 |
| Q35 | 3 | ✅ |  | station_closure_impact | 3 |
| Q36 | 3 | ✅ |  | draft_callout_notification | 0 |
| Q37 | 3 | ✅ |  | recommend_cover | 3 |
| Q38 | 3 | ✅ |  | morning_briefing | 12 |

## Q01 — Who is on reserve at BLR on 2026-09-15, and what are their on-call windows?

**Expected:** `[{"crew_id": "C-3305", "rank": "Captain", "window": {"start": "00:00", "end": "05:30"}}, {"crew_id": "C-3310", "rank": "Captain", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3311", "rank": "First Officer", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3312", "rank": "First Officer", "window": {"start": "00:00", "end": "12:00"}}, {"crew_id": "C-3315", "rank": "Capt`

**Answer:**

> 12 crew on reserve at BLR on 2026-09-15:
> - C-1329 — Cabin Crew (P. Pillai), on call 04:00–16:00Z, reachable in 45 min, ratings A320/ATR72
> - C-2111 — Senior Cabin Crew (A. Gupta), on call 04:00–16:00Z, reachable in 90 min, ratings A320/ATR72
> - C-2248 — Cabin Crew (H. Reddy), on call 04:00–16:00Z, reachable in 60 min, ratings A320/ATR72
> - C-3305 — Captain (V. Menon), on call 00:00–05:30Z, reachable in 45 min, ratings A320
> - C-3310 — Captain (D. Reddy), on call 06:00–18:00Z, reachable in 45 min, ratings A320
> - C-3311 — First Officer (K. Rao), on call 06:00–18:00Z, reachable in 45 min, ratings A320
> - C-3312 — First Officer (P. Sharma), on call 00:00–12:00Z, reachable in 60 min, ratings A320
> - C-3315 — Captain (M. Pillai), on call 03:00–15:00Z, reachable in 45 min, ratings ATR72
> - C-3316 — First Officer (N. Verma), on call 03:00–15:00Z, reachable in 45 min, ratings ATR72
> - C-3677 — Senior Cabin Crew (M. Iyer), on call 04:00–16:00Z, reachable in 45 min, ratings A320/ATR72
> - C-4809 — Cabin Crew (M. Das), on call 00:00–12:00Z, reachable in 45 min, ratings A320/ATR72
> - C-5418 — Cabin Crew (S. Das), on call 04:00–16:00Z, reachable in 45 min, ratings A320/ATR72
> 
> Reasoning:
> - the reserve roster (BLR, 2026-09-15) from the reserve roster joined to the crew roster
> - a reserve may be called out only if the required report time falls inside their on-call window (RULE-BASE-07 for base)
> 
> (offline mode — answered by the desk's rule-based router)

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 (A. Nair, Captain, base BLR) has accrued 20.93h of duty in the 7 calendar days ending 2026-09-14 (window 2026-09-08 → 2026-09-14), leaving 39.07h headroom under RULE-DUTY-02 (limit 60h). Block hours in the 28 days ending 2026-09-14: 64.27h, headroom 35.73h under RULE-FLT-03 (limit 100h). Earliest next report under RULE-REST-04: 2026-09-13T02:00:00Z.
> 
> Reasoning:
> - the duty clock (C-1042) — sums from the duty clocks daily_history as of 2026-09-14T18:00:00Z
> - headroom = limit − accrued (computed by the tool, not estimated)
> 
> (offline mode — answered by the desk's rule-based router)

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> 1 flight(s) departing DEL on 2026-09-15: DX402.
> - DX402 DEL→BLR dep 06:00Z arr 08:45Z, VT-DXA (162 seats)
> 
> Reasoning:
> - the flight schedule (departing DEL on 2026-09-15) filtered the flight schedule; all times UTC
> 
> (offline mode — answered by the desk's rule-based router)

## Q04 — List all certifications expiring within 30 days of 2026-09-15.

**Expected:** `[{"crew_id": "C-2087", "cert_type": "licence", "valid_to": "2026-09-18"}, {"crew_id": "C-2091", "cert_type": "medical_class1", "valid_to": "2026-09-23"}, {"crew_id": "C-5417", "cert_type": "recurrent_training", "valid_to": "2026-09-17"}, {"crew_id": "C-3116", "cert_type": "dangerous_goods", "valid_to": "2026-09-28"}, {"crew_id": "C-5020", "cert_type": "recurrent_training", "valid_to": "2026-10-03"`

**Answer:**

> 6 certification(s) expire within 30 days of 2026-09-15 (to 2026-10-15):
> - C-5417 (Cabin Crew): recurrent_training expires 2026-09-17
> - C-2087 (Captain): licence expires 2026-09-18
> - C-2091 (Captain): medical_class1 expires 2026-09-23
> - C-3116 (First Officer): dangerous_goods expires 2026-09-28
> - C-5020 (First Officer): recurrent_training expires 2026-10-03
> - C-2993 (First Officer): medical_class1 expires 2026-10-08
> 
> Reasoning:
> - the certification records (2026-09-15, 30 days) over the certification records; RULE-CERT-06 applies from the expiry date
> 
> (offline mode — answered by the desk's rule-based router)

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> DX412 on 2026-09-15 is operated by VT-DXC (A320, 162 seats), BLR→BOM departing 07:00Z and arriving 08:45Z, block 1.75h. Operated under pairing P-2291 (6 crew).
> 
> Reasoning:
> - the flight schedule (DX412, 2026-09-15) from the flight schedule
> 
> (offline mode — answered by the desk's rule-based router)

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 is D. Reddy, Captain based at BLR, rated A320, seniority 9, reachable in 45 minutes, status active. Reserve on-call window 06:00–18:00Z on 7 days this week. No rostered pairings this week. Disruption-risk score 0.17.
> 
> Reasoning:
> - the crew roster (C-3310) from the crew roster, the reserve roster, the pairing roster, the disruption-risk signals
> 
> (offline mode — answered by the desk's rule-based router)

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 is S. Kapoor, Captain based at DEL, rated A320, seniority 2, reachable in 60 minutes, status active. Reserve on-call window 03:00–15:00Z on 7 days this week. No rostered pairings this week. Disruption-risk score 0.03.
> 
> Reasoning:
> - the crew roster (C-2210) from the crew roster, the reserve roster, the pairing roster, the disruption-risk signals
> 
> (offline mode — answered by the desk's rule-based router)

## Q08 — Which crew are assigned to pairing P-2291, and in what roles?

**Expected:** `[{"crew_id": "C-1042", "role": "Captain"}, {"crew_id": "C-1694", "role": "First Officer"}, {"crew_id": "C-3005", "role": "Senior Cabin Crew"}, {"crew_id": "C-4395", "role": "Cabin Crew"}, {"crew_id": "C-4273", "role": "Cabin Crew"}, {"crew_id": "C-1873", "role": "Cabin Crew"}]`

**Answer:**

> Pairing P-2291 operates VT-DXC over 2 day(s) with 6 crew:
> - C-1042 — Captain (A. Nair)
> - C-1694 — First Officer (S. Menon)
> - C-3005 — Senior Cabin Crew (H. Chandra)
> - C-4395 — Cabin Crew (V. Rao)
> - C-4273 — Cabin Crew (P. Menon)
> - C-1873 — Cabin Crew (K. Joshi)
> 
> Duty days:
> - 2026-09-15: DX412, DX413, DX588 (BLR→DEL), report 06:00Z, release 15:30Z, 9.50h duty, 3 sectors
> - 2026-09-16: DX589, DX590, DX591 (DEL→BLR), report 04:00Z, release 14:45Z, 10.75h duty, 3 sectors
> 
> Reasoning:
> - the pairing roster (P-2291) from rosters — crew roles and duty days as rostered
> 
> (offline mode — answered by the desk's rule-based router)

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> 2 flight(s) BLR→BOM on 2026-09-17: DX412, DX431.
> - DX431 BLR→BOM dep 03:30Z arr 05:15Z, VT-DXD (162 seats)
> - DX412 BLR→BOM dep 07:00Z arr 08:45Z, VT-DXC (162 seats)
> 
> Reasoning:
> - the flight schedule (BLR→BOM on 2026-09-17) filtered the flight schedule; all times UTC
> 
> (offline mode — answered by the desk's rule-based router)

## Q10 — How many flights operate on 2026-09-16 in total?

**Expected:** `21`

**Answer:**

> 21 flight(s) on 2026-09-16: DX401, DX402, DX403, DX404, DX421, DX422, DX423, DX424, DX431, DX432, DX433, DX434, DX451, DX452, DX453, DX454, DX461, DX462, DX589, DX590, DX591.
> - DX401 BLR→DEL dep 02:30Z arr 05:15Z, VT-DXA (162 seats)
> - DX421 BLR→CCU dep 03:00Z arr 05:30Z, VT-DXB (162 seats)
> - DX431 BLR→BOM dep 03:30Z arr 05:15Z, VT-DXD (162 seats)
> - DX451 BLR→COK dep 04:00Z arr 05:15Z, VT-DXE (72 seats)
> - DX461 BLR→HYD dep 05:00Z arr 06:30Z, VT-DXF (72 seats)
> - DX589 DEL→BLR dep 05:00Z arr 07:45Z, VT-DXC (162 seats)
> - DX402 DEL→BLR dep 06:00Z arr 08:45Z, VT-DXA (162 seats)
> - DX432 BOM→BLR dep 06:00Z arr 07:45Z, VT-DXD (162 seats)
> - DX452 COK→BLR dep 06:00Z arr 07:15Z, VT-DXE (72 seats)
> - DX422 CCU→BLR dep 06:15Z arr 08:45Z, VT-DXB (162 seats)
> - DX462 HYD→BLR dep 07:15Z arr 08:45Z, VT-DXF (72 seats)
> - DX453 BLR→MAA dep 08:00Z arr 09:00Z, VT-DXE (72 seats)
> - DX433 BLR→GOI dep 08:30Z arr 09:45Z, VT-DXD (162 seats)
> - DX590 BLR→CCU dep 08:30Z arr 11:00Z, VT-DXC (162 seats)
> - DX403 BLR→MAA dep 09:30Z arr 10:30Z, VT-DXA (162 seats)
> - DX423 BLR→HYD dep 09:30Z arr 10:45Z, VT-DXB (162 seats)
> - DX454 MAA→BLR dep 09:45Z arr 10:45Z, VT-DXE (72 seats)
> - DX434 GOI→BLR dep 10:30Z arr 11:45Z, VT-DXD (162 seats)
> - DX404 MAA→BLR dep 11:15Z arr 12:15Z, VT-DXA (162 seats)
> - DX424 HYD→BLR dep 11:30Z arr 12:45Z, VT-DXB (162 seats)
> - DX591 CCU→BLR dep 11:45Z arr 14:15Z, VT-DXC (162 seats)
> 
> Reasoning:
> - the flight schedule (on 2026-09-16) filtered the flight schedule; all times UTC
> 
> (offline mode — answered by the desk's rule-based router)

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> 1 Captain based at DEL:
> - C-2210 (S. Kapoor), ratings A320, status active
> 
> Reasoning:
> - the crew roster (Captain based at DEL) from the crew roster
> 
> (offline mode — answered by the desk's rule-based router)

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> The longest block time in the schedule is 2.75h, flown by DX401, DX402, DX588, DX589. The shortest is 1.0h (DX403, DX404, DX453, DX454). The week has 147 flights across 8 stations with 6 aircraft.
> 
> Reasoning:
> - the flight schedule — max/min of block_hours over the flight schedule (computed by the tool)
> 
> (offline mode — answered by the desk's rule-based router)

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> C-2087 (R. Iyer, Captain, base BLR) has accrued 51.83h of duty in the 7 calendar days ending 2026-09-14 (window 2026-09-08 → 2026-09-14), leaving 8.17h headroom under RULE-DUTY-02 (limit 60h). Block hours in the 28 days ending 2026-09-14: 23.50h, headroom 76.50h under RULE-FLT-03 (limit 100h). Earliest next report under RULE-REST-04: 2026-09-15T02:00:00Z.
> 
> Reasoning:
> - the duty clock (C-2087) — sums from the duty clocks daily_history as of 2026-09-14T18:00:00Z
> - headroom = limit − accrued (computed by the tool, not estimated)
> 
> (offline mode — answered by the desk's rule-based router)

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> From BLR the network serves 7 stations nonstop: BOM, CCU, COK, DEL, GOI, HYD, MAA. Flights per destination this week: BOM (10), CCU (11), COK (7), DEL (10), GOI (7), HYD (14), MAA (14).
> 
> Reasoning:
> - the route network (BLR) — distinct arr_station where dep_station=BLR in the flight schedule
> 
> (offline mode — answered by the desk's rule-based router)

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> On P-2210 (VT-DXB, 2026-09-16) the Senior Cabin Crew is C-3171 (P. Chandra).
> 
> Reasoning:
> - the pairing roster (VT-DXB on 2026-09-16) from the pairing roster
> 
> (offline mode — answered by the desk's rule-based router)

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042 has a disruption-risk score of 0.78 (as of 2026-09-14T18:00:00Z). Drivers: short-rest pattern over last 14 days; two fatigue reports this month.
> 
> Reasoning:
> - the disruption-risk signals — pre-computed signal from the disruption-risk signals (provided input, not computed here)
> 
> (offline mode — answered by the desk's rule-based router)

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Immediately uncrewed: DX412, DX413, DX588 on 2026-09-15 (P-2291, Captain slot) — 486 passengers. Also at risk: DX589, DX590, DX591 on 2026-09-16 — the same pairing continues, so the cover must take the full remaining pairing (972 passengers in total).
> 
> Reasoning:
> - the sick-call impact assessment (C-1042) from the pairing roster: A. Nair is rostered as Captain on P-2291
> - passengers = seats of the uncovered legs (the flight schedule)
> - a multi-day pairing: the aircraft overnights away from base, so the cover must take the full remaining pairing
> 
> (offline mode — answered by the desk's rule-based router)

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> C-2087 covering P-2291 is not legal: RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h); RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h). Callout cost 24000 INR (dayoff callout).
>   ✓ RULE-FDP-01: FDP 10.75h within the 12.5h limit for 3 sectors [2 checks, tightest shown]
>   ✗ RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)
>   ✗ RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)
>   ✓ RULE-FLT-03: 37.50h block in the 28 days ending 2026-09-16 (limit 100h, headroom 62.50h) [2 checks, tightest shown]
>   ✓ RULE-REST-04: 12.50h rest between P-2291 (2026-09-15) and P-2291 (2026-09-16); minimum 12h [2 checks, tightest shown]
>   ✓ RULE-QUAL-05: rated on A320
>   ✓ RULE-CERT-06: all 4 certifications valid on 2026-09-15 [2 checks, tightest shown]
>   ✓ RULE-BASE-07: callout from own base BLR
> 
> Reasoning:
> - the legality check (C-2087 → P-2291): seven rules over the crew member's full timeline (28-day history + rostered week + the proposed duty days 2026-09-15, 2026-09-16)
> 
> (offline mode — answered by the desk's rule-based router)

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights are affected at BLR (08:00–14:00Z): DX453, DX433, DX402, DX422, DX462, DX403, DX423, DX454, DX413, DX434, DX404, DX588, DX424; 1836 seats exposed; 10 of them push their crew past RULE-FDP-01 (DX453, DX433, DX402, DX422, DX403, DX423, DX413, DX434, DX404, DX424).
> - DX453 (departure 08:00Z, P-2225): min delay 6.5h → FDP 14.75h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX433 (departure 08:30Z, P-2218): min delay 6h → FDP 15.75h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX402 (arrival 08:45Z, P-2204): min delay 5.75h → FDP 17.00h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX422 (arrival 08:45Z, P-2211): min delay 5.75h → FDP 17.00h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX462 (arrival 08:45Z, P-2232): min delay 5.75h → FDP 11.00h vs 13.0h limit — delay (crew legal)
> - DX403 (departure 09:30Z, P-2204): min delay 5h → FDP 16.25h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX423 (departure 09:30Z, P-2211): min delay 5h → FDP 16.25h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX454 (arrival 10:45Z, P-2225): min delay 3.75h → FDP 12.00h vs 12.0h limit — delay (crew legal)
> - DX413 (arrival 11:15Z, P-2293): min delay 3.25h → FDP 12.75h vs 12.5h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX434 (arrival 11:45Z, P-2218): min delay 2.75h → FDP 12.50h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX404 (arrival 12:15Z, P-2204): min delay 2.25h → FDP 13.50h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX588 (departure 12:15Z, P-2293): min delay 2.25h → FDP 11.75h vs 12.5h limit — delay (crew legal)
> - DX424 (arrival 12:45Z, P-2211): min delay 1.75h → FDP 13.00h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> 
> Reasoning:
> - the station-closure assessment: any flight departing or arriving the station inside the window is affected
> - minimum delay = reopen time + 30 min turnaround − scheduled time at the station; FDP after delay = rostered duty length + that delay
> 
> (offline mode — answered by the desk's rule-based router)

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — a 1.5h delay pushes the 4-sector duty to 12.75h against a 12.0h RULE-FDP-01 limit, so the rostered crew cannot legally complete all 4 legs. They can legally complete the first 3; DX404 needs a reserve crew or cancellation.
> 
> Reasoning:
> - the delay assessment for VT-DXA on 2026-09-16 (P-2203): report 01:30Z unchanged, release 12:45Z → 14:15Z
> - FDP before 11.25h, after 12.75h, limit 12.0h (13h − 0.5h per sector beyond the 2nd)
> - all rostered crew re-evaluated against the seven rules with the delayed duty
> 
> (offline mode — answered by the desk's rule-based router)

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> C-2210 covering P-2291 is legal subject to: RULE-BASE-07: base DEL ≠ duty start BLR; deadhead positioning required (cost applies). Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies. Cost 41200 INR (callout 18500, deadhead_positioning 6500, delay 16200).
>   ✓ RULE-FDP-01: FDP 10.75h within the 12.5h limit for 3 sectors [2 checks, tightest shown]
>   ✓ RULE-DUTY-02: 35.31h duty in the 7 days ending 2026-09-16 (limit 60h, headroom 24.69h) [2 checks, tightest shown]
>   ✓ RULE-FLT-03: 50.15h block in the 28 days ending 2026-09-16 (limit 100h, headroom 49.85h) [2 checks, tightest shown]
>   ✓ RULE-REST-04: 12.50h rest between P-2291 (2026-09-15) and P-2291 (2026-09-16); minimum 12h [2 checks, tightest shown]
>   ✓ RULE-QUAL-05: rated on A320
>   ✓ RULE-CERT-06: all 4 certifications valid on 2026-09-15 [2 checks, tightest shown]
>   ~ RULE-BASE-07: base DEL ≠ duty start BLR; deadhead positioning required (cost applies)
> 
> Reasoning:
> - the legality check (C-2210 → P-2291): seven rules over the crew member's full timeline (28-day history + rostered week + the proposed duty days 2026-09-15, 2026-09-16)
> - deadhead: earliest positioning flight from base, report = arrival + 15 min, delay costed per duty hour
> 
> (offline mode — answered by the desk's rule-based router)

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> C-5417's rostered duty on P-2213 is not legal: RULE-CERT-06: recurrent_training expired 2026-09-17.
>   ✓ RULE-FDP-01: FDP 11.25h within the 12.0h limit for 4 sectors
>   ✓ RULE-DUTY-02: 32.89h duty in the 7 days ending 2026-09-19 (limit 60h, headroom 27.11h)
>   ✓ RULE-FLT-03: 58.46h block in the 28 days ending 2026-09-19 (limit 100h, headroom 41.54h)
>   ✓ RULE-REST-04: 60.75h rest between P-2210 (2026-09-16) and P-2213 (2026-09-19); minimum 12h
>   ✓ RULE-QUAL-05: rated on A320
>   ✗ RULE-CERT-06: recurrent_training expired 2026-09-17
>   ✓ RULE-BASE-07: rostered duty — base rule applies to callouts only
> 
> Reasoning:
> - the legality check: all seven rules evaluated over the crew member's full timeline
> 
> (offline mode — answered by the desk's rule-based router)

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest next report is 2026-09-17T03:30:00Z — release 2026-09-16T15:30:00Z plus the 12h minimum rest.
> 
> Reasoning:
> - RULE-REST-04: report ≥ release + 12h (computed by the rest calculation)
> 
> (offline mode — answered by the desk's rule-based router)

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> C-3305 covering P-2291 is not legal: RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h). Callout cost 18500 INR (reserve callout). Availability: reserve on-call window 00:00-05:30Z does not cover required report 06:00Z.
>   ✓ RULE-FDP-01: FDP 10.75h within the 12.5h limit for 3 sectors [2 checks, tightest shown]
>   ✗ RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)
>   ✓ RULE-FLT-03: 47.60h block in the 28 days ending 2026-09-16 (limit 100h, headroom 52.40h) [2 checks, tightest shown]
>   ✓ RULE-REST-04: 12.50h rest between P-2291 (2026-09-15) and P-2291 (2026-09-16); minimum 12h [2 checks, tightest shown]
>   ✓ RULE-QUAL-05: rated on A320
>   ✓ RULE-CERT-06: all 4 certifications valid on 2026-09-15 [2 checks, tightest shown]
>   ✓ RULE-BASE-07: callout from own base BLR
> 
> Reasoning:
> - the legality check (C-3305 → P-2291): seven rules over the crew member's full timeline (28-day history + rostered week + the proposed duty days 2026-09-15, 2026-09-16)
> 
> (offline mode — answered by the desk's rule-based router)

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> Cancelling DX404 on 2026-09-16 (MAA-BLR) affects 162 passengers and costs 250000 INR in direct cancellation cost; it releases the 6 crew of P-2203 from that leg.
> 
> Reasoning:
> - the cancellation assessment: seats from the flight schedule; cancellation_per_flight from the cost table
> 
> (offline mode — answered by the desk's rule-based router)

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> 2 crew have 45 or more duty hours in the 7 days ending 2026-09-15:
> - C-2087 (R. Iyer, Captain): 51.83h duty / 7d (headroom 8.17h), 23.50h block / 28d, planned 0.00h that day
> - C-3305 (V. Menon, Captain): 50.00h duty / 7d (headroom 10.00h), 33.60h block / 28d, planned 0.00h that day
> 
> Reasoning:
> - the duty-limit watchlist: rolling calendar-day windows over the duty clocks history plus rostered duties (RULE-DUTY-02 60h/7d, RULE-FLT-03 100h/28d)
> 
> (offline mode — answered by the desk's rule-based router)

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> 1 reserve Captain(s) can take P-2224 (VT-DXE, ATR72) reporting 03:00Z on 2026-09-16: C-3315.
> - C-3315 (M. Pillai): window 03:00-15:00Z, rated ATR72, reachable in 45 min
> Excluded:
> - C-3305: RULE-QUAL-05: no ATR72 rating
> - C-3310: RULE-QUAL-05: no ATR72 rating; reserve on-call window 06:00-18:00Z does not cover required report 03:00Z
> - C-2210: RULE-QUAL-05: no ATR72 rating; RULE-BASE-07: based at DEL, duty starts at BLR (deadhead positioning required)
> 
> Reasoning:
> - the reserve coverage check: callout must fall inside the on-call window; RULE-QUAL-05 rating and RULE-BASE-07 base checked
> - required report time is the pairing's rostered report 2026-09-16T03:00:00Z
> 
> (offline mode — answered by the desk's rule-based router)

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> C-5837 covering P-2291 is not legal: RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict). Callout cost 24000 INR (dayoff callout).
>   ✓ RULE-FDP-01: FDP 10.75h within the 12.5h limit for 3 sectors [2 checks, tightest shown]
>   ✓ RULE-DUTY-02: 54.00h duty in the 7 days ending 2026-09-20 (limit 60h, headroom 6.00h) [4 checks, tightest shown]
>   ✓ RULE-FLT-03: 77.51h block in the 28 days ending 2026-09-16 (limit 100h, headroom 22.49h) [4 checks, tightest shown]
>   ✗ RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)
>   ✓ RULE-QUAL-05: rated on A320
>   ✓ RULE-CERT-06: all 4 certifications valid on 2026-09-15 [2 checks, tightest shown]
>   ✓ RULE-BASE-07: callout from own base BLR
> 
> Reasoning:
> - the legality check (C-5837 → P-2291): seven rules over the crew member's full timeline (28-day history + rostered week + the proposed duty days 2026-09-15, 2026-09-16)
> 
> (offline mode — answered by the desk's rule-based router)

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> 2 flights are affected at HYD (05:00–09:00Z): DX461, DX462; 144 seats exposed; 0 of them push their crew past RULE-FDP-01 (none).
> - DX461 (arrival 06:30Z, P-2234): min delay 3h → FDP 8.25h vs 13.0h limit — delay (crew legal)
> - DX462 (departure 07:15Z, P-2234): min delay 2.25h → FDP 7.50h vs 13.0h limit — delay (crew legal)
> 
> Reasoning:
> - the station-closure assessment: any flight departing or arriving the station inside the window is affected
> - minimum delay = reopen time + 30 min turnaround − scheduled time at the station; FDP after delay = rostered duty length + that delay
> 
> (offline mode — answered by the desk's rule-based router)

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any a320 leg (162 seats) — versus ATR72 legs (72 seats). Seats are fixed by aircraft type; every leg of the larger type carries the same exposure; direct cancellation cost is 250000 INR per leg regardless of type.
> 
> Reasoning:
> - the flight schedule: seats per aircraft type from the flight schedule; cancellation_per_flight from the cost table
> 
> (offline mode — answered by the desk's rule-based router)

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> Recommended: Assign Captain C-3310 (reserve callout) — 18500 INR. BLR-based, A320-rated, on-call 06:00-18:00Z, reachable in 45 min; all seven rules pass. This covers P-2291 (Captain slot, 2026-09-15, 2026-09-16: DX412, DX413, DX588, DX589, DX590, DX591; 972 passengers at risk).
> 
> Ranked options:
> 1. Assign Captain C-3310 (reserve callout) — 18500 INR, legal. BLR-based, A320-rated, on-call 06:00-18:00Z, reachable in 45 min; all seven rules pass.
> 2. Assign Captain C-1526 (day-off callout) — 24000 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 90 min; all seven rules pass.
> 3. Assign Captain C-3983 (day-off callout) — 24000 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 45 min; all seven rules pass.
> 4. Assign Captain C-5566 (day-off callout) — 24000 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 60 min; all seven rules pass.
> 5. Assign Captain C-2210 (reserve callout + deadhead from DEL (first departure delayed ~3.0h)) — 41200 INR, legal, delay 3h. Legal but incurs deadhead on DX402 (arr 08:45Z, report 09:00Z) and ~3.0h delay to DX412.
> 6. Cancel all 6 flights of the pairing — 1500000 INR, legal. Last resort: 6 legs × 250000 INR; 972 passengers stranded.
> 
> Excluded candidates:
> - C-1017: RULE-REST-04: only 11.00h rest before P-2217 on 2026-09-16 (downstream conflict); RULE-REST-04: P-2291 on 2026-09-16 overlaps P-2217 (no rest)
> - C-1443: RULE-REST-04: P-2291 on 2026-09-15 overlaps P-2216 (no rest)
> - C-1600: RULE-QUAL-05: no A320 rating
> - C-1671: RULE-QUAL-05: no A320 rating
> - C-1938: RULE-REST-04: P-2291 on 2026-09-15 overlaps P-2209 (no rest)
> - C-2087: RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h); RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)
> - C-2091: RULE-QUAL-05: no A320 rating
> - C-2143: RULE-DUTY-02: would exceed 60h/7d by 2h29m on 2026-09-17 (total 62.48h); RULE-DUTY-02: would exceed 60h/7d by 2h46m on 2026-09-20 (total 62.76h); RULE-REST-04: only 11.25h rest before P-2211 on 2026-09-17 (downstream conflict)
> - … and 11 more
> 
> Reasoning:
> - the cover-option ranking: 24 candidates of rank Captain considered; rules checked on the recommended option: RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07
> - candidates = every active crew of the rank; checked rating → reserve window → all seven rules over their full timeline; ranked by cost, then delay, then crew id
> - costs from the cost table: reserve/day-off callout, deadhead positioning + delay per duty hour, cancellation per leg
> 
> (offline mode — answered by the desk's rule-based router)

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> Optimal joint plan — total 42500 INR:
> - P-2205 (Captain): Assign Captain C-3305 (reserve callout) — 18500 INR, legal (rules checked: RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07). BLR-based, A320-rated, on-call 00:00-05:30Z, reachable in 45 min; all seven rules pass.
> - P-2212 (Captain): Assign Captain C-1017 (day-off callout) — 24000 INR, legal (rules checked: RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07). BLR-based, A320-rated, not rostered on the cover days, reachable in 75 min; all seven rules pass.
> 
> Per-duty ranked options:
> - P-2205 (C-3940 out): 1. Assign Captain C-3305 (reserve callout) (18500); 2. Assign Captain C-1017 (day-off callout) (24000); 3. Assign Captain C-1042 (day-off callout) (24000); 4. Assign Captain C-1526 (day-off callout) (24000)
> - P-2212 (C-1938 out): 1. Assign Captain C-3305 (reserve callout) (18500); 2. Assign Captain C-1017 (day-off callout) (24000); 3. Assign Captain C-1042 (day-off callout) (24000); 4. Assign Captain C-1526 (day-off callout) (24000)
> 
> Reasoning:
> - the joint cover plan: options ranked per duty, then the cheapest combination with no person assigned twice
> - cheapest combination with no person assigned twice; equal-cost plans are equally valid
> 
> (offline mode — answered by the desk's rule-based router)

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> RULE-FDP-01: delayed duty runs 12.75h vs 12.0h limit (4 sectors) — the rostered crew cannot legally complete DX404. Options:
> 1. Original crew operates DX401–DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404 — 75000 INR, legal. Delayed 3-leg duty FDP 11.0h vs 12.5h limit — legal. Reserve set covers the last sector (report 11:45Z, FDP 2.50h; callout window and 12h rest satisfied).
> 2. Cancel DX404 — 250000 INR, legal. Legal but ~3.3x more expensive than re-crewing; 162 passengers stranded.
> 
> Reasoning:
> - the delay-recovery options for VT-DXA on 2026-09-16: FDP 12.75h vs 12.0h limit after a 1.5h delay
> - reserve set cost = full complement at reserve callout rates; cancellation per leg from the cost table
> 
> (offline mode — answered by the desk's rule-based router)

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> Recommended: Assign Cabin Crew C-4809 (reserve callout) — 9500 INR. BLR-based, A320/ATR72-rated, on-call 00:00-12:00Z, reachable in 45 min; all seven rules pass. This covers P-2213 (Cabin Crew slot, 2026-09-19: DX421, DX422, DX423, DX424; 648 passengers at risk).
> 
> Ranked options:
> 1. Assign Cabin Crew C-4809 (reserve callout) — 9500 INR, legal. BLR-based, A320/ATR72-rated, on-call 00:00-12:00Z, reachable in 45 min; all seven rules pass.
> 2. Assign Cabin Crew C-1021 (day-off callout) — 12500 INR, legal. BLR-based, A320/ATR72-rated, not rostered on the cover days, reachable in 90 min; all seven rules pass.
> 3. Assign Cabin Crew C-1385 (day-off callout) — 12500 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 60 min; all seven rules pass.
> 4. Assign Cabin Crew C-1414 (day-off callout) — 12500 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 90 min; all seven rules pass.
> 5. Assign Cabin Crew C-1569 (day-off callout) — 12500 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 45 min; all seven rules pass.
> 6. Assign Cabin Crew C-1748 (day-off callout) — 12500 INR, legal. BLR-based, A320/ATR72-rated, not rostered on the cover days, reachable in 45 min; all seven rules pass.
> 7. Assign Cabin Crew C-1873 (day-off callout) — 12500 INR, legal. BLR-based, A320-rated, not rostered on the cover days, reachable in 45 min; all seven rules pass.
> 8. Assign Cabin Crew C-1970 (day-off callout) — 12500 INR, legal. BLR-based, A320/ATR72-rated, not rostered on the cover days, reachable in 90 min; all seven rules pass.
> 9. Cancel all 4 flights of the pairing — 1000000 INR, legal. Last resort: 4 legs × 250000 INR; 648 passengers stranded.
> 
> Excluded candidates:
> - C-1329: reserve on-call window 04:00-16:00Z does not cover required report 02:00Z
> - C-1542: RULE-REST-04: P-2213 on 2026-09-19 overlaps P-2206 (no rest)
> - C-1568: RULE-QUAL-05: no A320 rating
> - C-1594: RULE-QUAL-05: no A320 rating
> - C-2100: RULE-QUAL-05: no A320 rating
> - C-2248: reserve on-call window 04:00-16:00Z does not cover required report 02:00Z
> - C-2352: RULE-REST-04: P-2295 on 2026-09-19 overlaps P-2213 (no rest)
> - C-2876: RULE-REST-04: P-2213 on 2026-09-19 overlaps P-2206 (no rest)
> - … and 13 more
> 
> Reasoning:
> - the cover-option ranking: 29 candidates of rank Cabin Crew considered; rules checked on the recommended option: RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07
> - candidates = every active crew of the rank; checked rating → reserve window → all seven rules over their full timeline; ranked by cost, then delay, then crew id
> - costs from the cost table: reserve/day-off callout, deadhead positioning + delay per duty hour, cancellation per leg
> 
> (offline mode — answered by the desk's rule-based router)

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> 13 flights are affected at BLR (08:00–14:00Z): DX453, DX433, DX402, DX422, DX462, DX403, DX423, DX454, DX413, DX434, DX404, DX588, DX424; 1836 seats exposed; 10 of them push their crew past RULE-FDP-01 (DX453, DX433, DX402, DX422, DX403, DX423, DX413, DX434, DX404, DX424).
> - DX453 (departure 08:00Z, P-2225): min delay 6.5h → FDP 14.75h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX433 (departure 08:30Z, P-2218): min delay 6h → FDP 15.75h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX402 (arrival 08:45Z, P-2204): min delay 5.75h → FDP 17.00h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX422 (arrival 08:45Z, P-2211): min delay 5.75h → FDP 17.00h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX462 (arrival 08:45Z, P-2232): min delay 5.75h → FDP 11.00h vs 13.0h limit — delay (crew legal)
> - DX403 (departure 09:30Z, P-2204): min delay 5h → FDP 16.25h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX423 (departure 09:30Z, P-2211): min delay 5h → FDP 16.25h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX454 (arrival 10:45Z, P-2225): min delay 3.75h → FDP 12.00h vs 12.0h limit — delay (crew legal)
> - DX413 (arrival 11:15Z, P-2293): min delay 3.25h → FDP 12.75h vs 12.5h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX434 (arrival 11:45Z, P-2218): min delay 2.75h → FDP 12.50h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX404 (arrival 12:15Z, P-2204): min delay 2.25h → FDP 13.50h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> - DX588 (departure 12:15Z, P-2293): min delay 2.25h → FDP 11.75h vs 12.5h limit — delay (crew legal)
> - DX424 (arrival 12:45Z, P-2211): min delay 1.75h → FDP 13.00h vs 12.0h limit — delay exceeds crew FDP — re-crew tail legs from reserves or cancel
> 
> Reasoning:
> - the station-closure assessment: any flight departing or arriving the station inside the window is affected
> - minimum delay = reopen time + 30 min turnaround − scheduled time at the station; FDP after delay = rostered duty length + that delay
> 
> (offline mode — answered by the desk's rule-based router)

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Draft callout notification:
> 
> CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> Day 1 (2026-09-15): report 06:00Z at BLR crew room; flights DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z.
>   Overnight at DEL — hotel arranged.
> Day 2 (2026-09-16): report 04:00Z at DEL crew room; flights DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> Acknowledgement request — deadline 2026-09-14T18:30:00Z (30 minutes): reply ACK P-2291.
> Contact for questions: Crew Control desk, BLR.
> 
> Included: crew id and pairing id; report time/place per day; flights per day; overnight and hotel; acknowledgement request with deadline; contact for questions.
> 
> Reasoning:
> - the callout draft (C-3310, P-2291): every time and flight from the pairing roster/the flight schedule
> 
> (offline mode — answered by the desk's rule-based router)

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> Recommended: Assign First Officer C-3316 (reserve callout) — 18500 INR. BLR-based, ATR72-rated, on-call 03:00-15:00Z, reachable in 45 min; all seven rules pass. This covers P-2235 (First Officer slot, 2026-09-20: DX461, DX462; 144 passengers at risk).
> 
> Ranked options:
> 1. Assign First Officer C-3316 (reserve callout) — 18500 INR, legal. BLR-based, ATR72-rated, on-call 03:00-15:00Z, reachable in 45 min; all seven rules pass.
> 2. Assign First Officer C-1313 (day-off callout) — 24000 INR, legal. BLR-based, ATR72-rated, not rostered on the cover days, reachable in 75 min; all seven rules pass.
> 3. Assign First Officer C-1317 (day-off callout) — 24000 INR, legal. BLR-based, ATR72-rated, not rostered on the cover days, reachable in 90 min; all seven rules pass.
> 4. Assign First Officer C-2085 (day-off callout) — 24000 INR, legal. BLR-based, ATR72-rated, not rostered on the cover days, reachable in 75 min; all seven rules pass.
> 5. Assign First Officer C-3057 (day-off callout) — 24000 INR, legal. BLR-based, ATR72-rated, not rostered on the cover days, reachable in 90 min; all seven rules pass.
> 6. Cancel all 2 flights of the pairing — 500000 INR, legal. Last resort: 2 legs × 250000 INR; 144 passengers stranded.
> 
> Excluded candidates:
> - C-1510: RULE-QUAL-05: no ATR72 rating
> - C-1694: RULE-QUAL-05: no ATR72 rating
> - C-1895: RULE-QUAL-05: no ATR72 rating
> - C-2295: RULE-QUAL-05: no ATR72 rating
> - C-2341: RULE-QUAL-05: no ATR72 rating
> - C-2791: RULE-QUAL-05: no ATR72 rating
> - C-2875: RULE-QUAL-05: no ATR72 rating
> - C-2888: RULE-QUAL-05: no ATR72 rating
> - … and 13 more
> 
> Reasoning:
> - the cover-option ranking: 26 candidates of rank First Officer considered; rules checked on the recommended option: RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07
> - candidates = every active crew of the rank; checked rating → reserve window → all seven rules over their full timeline; ranked by cost, then delay, then crew id
> - costs from the cost table: reserve/day-off callout, deadhead positioning + delay per duty hour, cancellation per leg
> 
> (offline mode — answered by the desk's rule-based router)

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Morning briefing for 2026-09-15 — surface three data points per aircraft line:
> 1. crew legality headroom (7d duty) for today's rostered crew
> 2. reserve availability by on-call window and rating for the day
> 3. risk signals for today's rostered crew (provided input)
> 
> Today's lines:
> - VT-DXA (A320, P-2202, report 01:30Z): tightest 7-day duty headroom 27.83h; highest risk 0.71; certs all valid; eligible reserves at report: C-3305, C-4809, C-3312
> - VT-DXB (A320, P-2209, report 02:00Z): tightest 7-day duty headroom 28.77h; highest risk 0.69; certs all valid; eligible reserves at report: C-3305, C-4809, C-3312
> - VT-DXC (A320, P-2291, report 06:00Z): tightest 7-day duty headroom 29.29h; highest risk 0.78; certs all valid; eligible reserves at report: C-1329, C-3310, C-3311, C-3677, C-4809, C-5418, C-2248, C-3312, C-2111
> - VT-DXD (A320, P-2216, report 02:30Z): tightest 7-day duty headroom 30.74h; highest risk 0.31; certs all valid; eligible reserves at report: C-3305, C-4809, C-3312
> - VT-DXE (ATR72, P-2223, report 03:00Z): tightest 7-day duty headroom 30.79h; highest risk 0.29; certs all valid; eligible reserves at report: C-3315, C-3316, C-4809
> - VT-DXF (ATR72, P-2230, report 04:00Z): tightest 7-day duty headroom 34.90h; highest risk 0.15; certs all valid; eligible reserves at report: C-1329, C-3315, C-3316, C-3677, C-4809, C-5418, C-2248, C-2111
> 
> Reasoning:
> - headroom from duty_clocks history + roster (RULE-DUTY-02); reserves from reserve_pool windows and ratings; risk from the disruption-risk signals
> - why these three: legality headroom is what breaks first under a delay, reserve availability is what fixes it, and risk signals say where to look first
> 
> (offline mode — answered by the desk's rule-based router)
