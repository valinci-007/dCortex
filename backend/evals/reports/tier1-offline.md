# Eval report — offline

Run: 2026-09-04T11:07:41Z · **16/16** questions with all expected facts recalled · latency p50 0 ms / p95 1 ms / max 2 ms

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 1 |
| Q02 | 1 | ✅ |  | get_crew, get_duty_clock | 2 |
| Q03 | 1 | ✅ |  | list_flights | 0 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 1 |
| Q05 | 1 | ✅ |  | get_flight | 0 |
| Q06 | 1 | ✅ |  | get_crew | 0 |
| Q07 | 1 | ✅ |  | get_crew | 0 |
| Q08 | 1 | ✅ |  | get_pairing | 0 |
| Q09 | 1 | ✅ |  | list_flights | 0 |
| Q10 | 1 | ✅ |  | list_flights | 0 |
| Q11 | 1 | ✅ |  | list_crew | 0 |
| Q12 | 1 | ✅ |  | schedule_stats | 1 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 0 |
| Q14 | 1 | ✅ |  | list_routes | 0 |
| Q15 | 1 | ✅ |  | find_pairings | 1 |
| Q16 | 1 | ✅ |  | get_risk_signal | 0 |

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
> - list_reserves(BLR, 2026-09-15) from reserve_pool.json joined to crew.json
> - a reserve may be called out only if the required report time falls inside their on-call window (RULE-BASE-07 for base)
> 
> (offline mode — deterministic router, no language model)

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 (A. Nair, Captain, base BLR) has accrued 20.93h of duty in the 7 calendar days ending 2026-09-14 (window 2026-09-08 → 2026-09-14), leaving 39.07h headroom under RULE-DUTY-02 (limit 60h). Block hours in the 28 days ending 2026-09-14: 64.27h, headroom 35.73h under RULE-FLT-03 (limit 100h). Earliest next report under RULE-REST-04: 2026-09-13T02:00:00Z.
> 
> Reasoning:
> - get_duty_clock(C-1042) — sums from duty_clocks.json daily_history as of 2026-09-14T18:00:00Z
> - headroom = limit − accrued (computed by the tool, not estimated)
> 
> (offline mode — deterministic router, no language model)

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> 1 flight(s) departing DEL on 2026-09-15: DX402.
> - DX402 DEL→BLR dep 06:00Z arr 08:45Z, VT-DXA (162 seats)
> 
> Reasoning:
> - list_flights(departing DEL on 2026-09-15) filtered flights.json; all times UTC
> 
> (offline mode — deterministic router, no language model)

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
> - list_expiring_certifications(2026-09-15, 30 days) over certifications.json; RULE-CERT-06 applies from the expiry date
> 
> (offline mode — deterministic router, no language model)

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> DX412 on 2026-09-15 is operated by VT-DXC (A320, 162 seats), BLR→BOM departing 07:00Z and arriving 08:45Z, block 1.75h. Operated under pairing P-2291 (6 crew).
> 
> Reasoning:
> - get_flight(DX412, 2026-09-15) from flights.json
> 
> (offline mode — deterministic router, no language model)

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 is D. Reddy, Captain based at BLR, rated A320, seniority 9, reachable in 45 minutes, status active. Reserve on-call window 06:00–18:00Z on 7 days this week. No rostered pairings this week. Disruption-risk score 0.17.
> 
> Reasoning:
> - get_crew(C-3310) from crew.json, reserve_pool.json, rosters.json, risk_signals.json
> 
> (offline mode — deterministic router, no language model)

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 is S. Kapoor, Captain based at DEL, rated A320, seniority 2, reachable in 60 minutes, status active. Reserve on-call window 03:00–15:00Z on 7 days this week. No rostered pairings this week. Disruption-risk score 0.03.
> 
> Reasoning:
> - get_crew(C-2210) from crew.json, reserve_pool.json, rosters.json, risk_signals.json
> 
> (offline mode — deterministic router, no language model)

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
> - get_pairing(P-2291) from rosters — crew roles and duty days as rostered
> 
> (offline mode — deterministic router, no language model)

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> 2 flight(s) BLR→BOM on 2026-09-17: DX412, DX431.
> - DX431 BLR→BOM dep 03:30Z arr 05:15Z, VT-DXD (162 seats)
> - DX412 BLR→BOM dep 07:00Z arr 08:45Z, VT-DXC (162 seats)
> 
> Reasoning:
> - list_flights(BLR→BOM on 2026-09-17) filtered flights.json; all times UTC
> 
> (offline mode — deterministic router, no language model)

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
> - list_flights(on 2026-09-16) filtered flights.json; all times UTC
> 
> (offline mode — deterministic router, no language model)

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> 1 Captain based at DEL:
> - C-2210 (S. Kapoor), ratings A320, status active
> 
> Reasoning:
> - list_crew(Captain based at DEL) from crew.json
> 
> (offline mode — deterministic router, no language model)

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> The longest block time in the schedule is 2.75h, flown by DX401, DX402, DX588, DX589. The shortest is 1.0h (DX403, DX404, DX453, DX454). The week has 147 flights across 8 stations with 6 aircraft.
> 
> Reasoning:
> - schedule_stats — max/min of block_hours over flights.json (computed by the tool)
> 
> (offline mode — deterministic router, no language model)

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> C-2087 (R. Iyer, Captain, base BLR) has accrued 51.83h of duty in the 7 calendar days ending 2026-09-14 (window 2026-09-08 → 2026-09-14), leaving 8.17h headroom under RULE-DUTY-02 (limit 60h). Block hours in the 28 days ending 2026-09-14: 23.50h, headroom 76.50h under RULE-FLT-03 (limit 100h). Earliest next report under RULE-REST-04: 2026-09-15T02:00:00Z.
> 
> Reasoning:
> - get_duty_clock(C-2087) — sums from duty_clocks.json daily_history as of 2026-09-14T18:00:00Z
> - headroom = limit − accrued (computed by the tool, not estimated)
> 
> (offline mode — deterministic router, no language model)

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> From BLR the network serves 7 stations nonstop: BOM, CCU, COK, DEL, GOI, HYD, MAA. Flights per destination this week: BOM (10), CCU (11), COK (7), DEL (10), GOI (7), HYD (14), MAA (14).
> 
> Reasoning:
> - list_routes(BLR) — distinct arr_station where dep_station=BLR in flights.json
> 
> (offline mode — deterministic router, no language model)

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> On P-2210 (VT-DXB, 2026-09-16) the Senior Cabin Crew is C-3171 (P. Chandra).
> 
> Reasoning:
> - find_pairings(VT-DXB on 2026-09-16) from rosters.json
> 
> (offline mode — deterministic router, no language model)

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042 has a disruption-risk score of 0.78 (as of 2026-09-14T18:00:00Z). Drivers: short-rest pattern over last 14 days; two fatigue reports this month.
> 
> Reasoning:
> - get_risk_signal — pre-computed signal from risk_signals.json (provided input, not computed here)
> 
> (offline mode — deterministic router, no language model)
