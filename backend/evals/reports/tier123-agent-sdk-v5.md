# Eval report — agent-sdk

Run: 2026-09-05T07:46:26Z · **36/38** questions with all expected facts recalled · latency p50 8732 ms / p95 16491 ms / max 20087 ms · est. cost $2.33

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 10531 |
| Q02 | 1 | ✅ |  | get_duty_clock | 6716 |
| Q03 | 1 | ✅ |  | list_flights | 6226 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 8188 |
| Q05 | 1 | ✅ |  | get_flight | 6072 |
| Q06 | 1 | ✅ |  | get_crew | 6680 |
| Q07 | 1 | ✅ |  | get_crew | 6605 |
| Q08 | 1 | ✅ |  | get_pairing | 7207 |
| Q09 | 1 | ✅ |  | list_flights | 6502 |
| Q10 | 1 | ✅ |  | list_flights | 6344 |
| Q11 | 1 | ✅ |  | list_crew | 6400 |
| Q12 | 1 | ✅ |  | schedule_stats | 6843 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 7801 |
| Q14 | 1 | ✅ |  | list_routes | 6863 |
| Q15 | 1 | ✅ |  | find_pairings | 8814 |
| Q16 | 1 | ✅ |  | get_risk_signal | 6987 |
| Q17 | 2 | ✅ |  | declare_unavailable, simulate_crew_removal | 9688 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 11045 |
| Q19 | 2 | ✅ |  | station_closure_impact | 11462 |
| Q20 | 2 | ✅ |  | simulate_delay | 11061 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 9710 |
| Q22 | 2 | ✅ |  | find_pairings, check_rostered_legality | 9916 |
| Q23 | 2 | ✅ |  | earliest_next_report | 6049 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 10676 |
| Q25 | 2 | ✅ |  | cancellation_impact | 6878 |
| Q26 | 2 | ✅ |  | crew_near_limits | 7931 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage, declare_unavailable | 20087 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 10299 |
| Q29 | 2 | ✅ |  | station_closure_impact | 8649 |
| Q30 | 2 | ✅ |  | seats_at_risk | 7356 |
| Q31 | 3 | ✅ |  | recommend_cover | 14169 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 15265 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | simulate_delay, resolve_delay_options | 12999 |
| Q34 | 3 | ❌ | Assign Cabin Crew C-1385 (day-off callout), C-1385 | get_certifications, find_pairings, declare_unavailable, recommend_cover | 17269 |
| Q35 | 3 | ✅ |  | station_closure_impact | 16491 |
| Q36 | 3 | ✅ |  | draft_callout_notification | 10378 |
| Q37 | 3 | ✅ |  | find_pairings, recommend_cover | 13638 |
| Q38 | 3 | ✅ |  | morning_briefing | 13603 |

## Q01 — Who is on reserve at BLR on 2026-09-15, and what are their on-call windows?

**Expected:** `[{"crew_id": "C-3305", "rank": "Captain", "window": {"start": "00:00", "end": "05:30"}}, {"crew_id": "C-3310", "rank": "Captain", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3311", "rank": "First Officer", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3312", "rank": "First Officer", "window": {"start": "00:00", "end": "12:00"}}, {"crew_id": "C-3315", "rank": "Capt`

**Answer:**

> 12 reserves at BLR tomorrow (2026-09-15):
> 
> Flight deck
> - C-3305 V. Menon, Captain A320 — 00:00–05:30Z
> - C-3310 D. Reddy, Captain A320 — 06:00–18:00Z
> - C-3315 M. Pillai, Captain ATR72 — 03:00–15:00Z
> - C-3311 K. Rao, FO A320 — 06:00–18:00Z
> - C-3312 P. Sharma, FO A320 — 00:00–12:00Z
> - C-3316 N. Verma, FO ATR72 — 03:00–15:00Z
> 
> Cabin
> - C-2111 A. Gupta, SCC A320/ATR72 — 04:00–16:00Z (90 min reachability)
> - C-3677 M. Iyer, SCC A320/ATR72 — 04:00–16:00Z
> - C-1329 P. Pillai, CC — 04:00–16:00Z
> - C-2248 H. Reddy, CC — 04:00–16:00Z (60 min)
> - C-5418 S. Das, CC — 04:00–16:00Z
> - C-4809 M. Das, CC — 00:00–12:00Z
> 
> Reasoning:
> - Reserve roster for BLR on 2026-09-15: 12 reserves, all active, windows as listed; reachability 45 min unless noted.
> - A callout is only valid if the required report time falls inside the on-call window; RULE-BASE-07 satisfied for BLR-based duties.

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 has 20.93 duty hours in the 7 days 2026-09-08 to 2026-09-14, leaving 39.07h headroom under the 60h limit.
> 
> Reasoning:
> - C-1042's duty clock: duty_hours_7d 20.93 over window 2026-09-08 → 2026-09-14; limit 60h, headroom 39.07h (RULE-DUTY-02).
> - Contributing duty days in that window: 2026-09-09 (9.99h) and 2026-09-12 (10.94h).
> - For reference, 28-day block hours stand at 64.27h against the 100h limit (RULE-FLT-03).

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> One flight departs DEL tomorrow (2026-09-15):
> - DX402 DEL–BLR, dep 06:00Z / arr 08:45Z, VT-DXA (A320), 162 seats, 2.75 block hours.
> 
> Reasoning:
> - Flight schedule filtered to DEL departures on 2026-09-15: 1 leg, 162 seats total.

## Q04 — List all certifications expiring within 30 days of 2026-09-15.

**Expected:** `[{"crew_id": "C-2087", "cert_type": "licence", "valid_to": "2026-09-18"}, {"crew_id": "C-2091", "cert_type": "medical_class1", "valid_to": "2026-09-23"}, {"crew_id": "C-5417", "cert_type": "recurrent_training", "valid_to": "2026-09-17"}, {"crew_id": "C-3116", "cert_type": "dangerous_goods", "valid_to": "2026-09-28"}, {"crew_id": "C-5020", "cert_type": "recurrent_training", "valid_to": "2026-10-03"`

**Answer:**

> Six certifications expire between 2026-09-15 and 2026-10-15:
> 
> - C-5417 (S. Krishnan, Cabin Crew) — recurrent training, expires 2026-09-17
> - C-2087 (R. Iyer, Captain) — licence, expires 2026-09-18
> - C-2091 (H. Naidu, Captain) — medical class 1, expires 2026-09-23
> - C-3116 (R. Naidu, First Officer) — dangerous goods, expires 2026-09-28
> - C-5020 (K. Nair, First Officer) — recurrent training, expires 2026-10-03
> - C-2993 (I. Kulkarni, First Officer) — medical class 1, expires 2026-10-08
> 
> Reasoning:
> - Certification register, window 2026-09-15 to 2026-10-15: 6 entries, soonest first.
> - RULE-CERT-06: any duty rostered after these dates is illegal until renewal — the first three fall inside this schedule week.

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> VT-DXC (A320), 162 seats — DX412 BLR–BOM on 2026-09-15, dep 07:00Z / arr 08:45Z.
> 
> Reasoning:
> - Flight schedule for DX412 on 2026-09-15: aircraft VT-DXC, type A320, seats 162, operated on pairing P-2291.

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 (D. Reddy, Captain, BLR, A320): on-call 06:00–18:00Z, reachability 45 minutes.
> 
> Reasoning:
> - Reserve roster: C-3310 on reserve every day of the week 2026-09-14 to 2026-09-20, window 06:00–18:00Z, base BLR.
> - Crew profile: reachability 45 min, active, A320 rated, no pairings rostered.
> - A callout is only valid if the required report time falls inside that window (RULE-BASE-07 applies to base).

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 (S. Kapoor, Captain) is based at DEL and rated A320 only.
> 
> Reasoning:
> - Crew record for C-2210: base DEL, ratings [A320], status active.
> - Also on the reserve roster all week (2026-09-14 to 2026-09-20), on-call 03:00–15:00Z; RULE-BASE-07 applies for any callout outside DEL.

## Q08 — Which crew are assigned to pairing P-2291, and in what roles?

**Expected:** `[{"crew_id": "C-1042", "role": "Captain"}, {"crew_id": "C-1694", "role": "First Officer"}, {"crew_id": "C-3005", "role": "Senior Cabin Crew"}, {"crew_id": "C-4395", "role": "Cabin Crew"}, {"crew_id": "C-4273", "role": "Cabin Crew"}, {"crew_id": "C-1873", "role": "Cabin Crew"}]`

**Answer:**

> P-2291 (VT-DXC, 2026-09-15 to 2026-09-16) is crewed by six:
> - C-1042 A. Nair — Captain
> - C-1694 S. Menon — First Officer
> - C-3005 H. Chandra — Senior Cabin Crew
> - C-4395 V. Rao — Cabin Crew
> - C-4273 P. Menon — Cabin Crew
> - C-1873 K. Joshi — Cabin Crew
> 
> Reasoning:
> - Pairing record for P-2291: 2 duty days (BLR–DEL 15 Sep, DEL–BLR 16 Sep), 3 sectors each, crew list with roles as above.

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> Two BLR→BOM legs on 2026-09-17:
> - DX431 — dep 03:30Z / arr 05:15Z, VT-DXD (A320), 162 seats, 1.75h block
> - DX412 — dep 07:00Z / arr 08:45Z, VT-DXC (A320), 162 seats, 1.75h block
> 
> Reasoning:
> - Flight schedule, BLR→BOM on 2026-09-17: 2 legs, 324 seats total.

## Q10 — How many flights operate on 2026-09-16 in total?

**Expected:** `21`

**Answer:**

> 21 flights operate on 2026-09-16, across all six aircraft, 2,862 seats in total.
> 
> Reasoning:
> - Flight schedule for 2026-09-16: count 21, total_seats 2,862, DX401 through DX591 on VT-DXA/B/C/D (A320) and VT-DXE/F (ATR72).

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> One Captain is based at DEL:
> - C-2210 — S. Kapoor, A320 rated, active, reachable in 60 min, seniority 2.
> 
> Reasoning:
> - Crew list filtered to base DEL, rank Captain: count 1.

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> Longest block time is 2.75h, flown by DX401, DX402, DX588 and DX589.
> 
> Reasoning:
> - Flight schedule stats for the week 2026-09-14 to 2026-09-20 (147 flights): longest block 2.75h on those four flight numbers; shortest is 1.0h (DX403, DX404, DX453, DX454).

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> C-2087 (R. Iyer) is a Captain, BLR based, A320 rated — 23.5 block hours in the 28 days ending 2026-09-14 (76.5h headroom under the 100h limit).
> 
> Reasoning:
> - Crew profile for C-2087: rank Captain, base BLR, rating A320, status active.
> - C-2087's duty clock: flight hours 28d = 23.5 over window 2026-08-18 to 2026-09-14, limit 100h (RULE-FLT-03); 7-day duty 51.83h with 8.17h headroom (RULE-DUTY-02).

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> BLR serves seven nonstop destinations this week (2026-09-14 to 2026-09-20), 73 departures in total:
> - HYD — 14
> - MAA — 14
> - CCU — 11
> - BOM — 10
> - DEL — 10
> - COK — 7
> - GOI — 7
> 
> Reasoning:
> - Flight schedule, nonstop destinations from BLR across the schedule week: 7 stations, flight counts as listed, total 73.

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> P. Chandra (C-3171) is the Senior Cabin Crew on P-2210, VT-DXB's pairing on 2026-09-16.
> 
> Reasoning:
> - Pairing search for VT-DXB on 2026-09-16: one pairing, P-2210 (DX421–DX424), crew list as rostered.

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042's disruption-risk score is 0.78. Drivers:
> - Short-rest pattern over the last 14 days
> - Two fatigue reports this month
> 
> Reasoning:
> - Risk signal for C-1042 (provided input, as of 18:00Z): score 0.78 with the two drivers listed.

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Immediately uncrewed (Captain slot, P-2291, VT-DXC, 2026-09-15, BLR→DEL): DX412, DX413, DX588 — 486 passengers.
> Also at risk on 2026-09-16 (DEL→BLR): DX589, DX590, DX591 — total exposure 972 passengers. The pairing overnights away from base, so the cover must take the full remaining pairing.
> 
> Reasoning:
> - C-1042 (A. Nair, Captain) recorded unavailable from 2026-09-15 (sick); both P-2291 duty days now vacant in the working scenario.
> - Removal impact: uncovered now = DX412/DX413/DX588 on 15 Sep; at risk = DX589/DX590/DX591 on 16 Sep; passengers_now 486, passengers_at_risk_total 972.
> - Cover must hold a valid A320 rating (RULE-QUAL-05); full legality check runs when a cover is applied.

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Yes — not legal. C-2087 (R. Iyer, Captain) breaches RULE-DUTY-02 on both duty days of P-2291:
> - 2026-09-15: 61.33h in the 7-day window (2026-09-09→15), over the 60h limit by 1h20m
> - 2026-09-16: 61.08h in the 7-day window (2026-09-10→16), over by 1h05m
> 
> Everything else passes:
> - RULE-FDP-01: 9.50h on 15 Sep and 10.75h on 16 Sep, both within the 12.5h limit for 3 sectors
> - RULE-FLT-03: 37.50h block in 28 days, 62.50h headroom
> - RULE-REST-04: 12.50h between release 15 Sep 15:30Z and report 16 Sep 04:00Z (min 12h); pre-duty rest complete 02:00Z, 4h before the 06:00Z report
> - RULE-QUAL-05: rated A320
> - RULE-CERT-06: all 4 certifications valid both days (note licence expires 2026-09-18 — tight for anything later)
> - RULE-BASE-07: day-off callout from own base BLR, no deadhead
> 
> Callout cost would have been ₹24,000 as a day-off callout, but the assignment can't be applied as it stands.
> 
> Reasoning:
> - Legality check on C-2087 against P-2291 from 2026-09-15, all seven rules over both duty days.
> - Duty clock daily totals in the 7-day windows drive the RULE-DUTY-02 breaches; cost from the cost table (day-off callout).

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights across 6 pairings are affected, 1,836 passengers exposed; 10 legs breach RULE-FDP-01 after the minimum delay.
> 
> - P-2204: DX402 (+5.75h, FDP 17.0 vs 12.0 ✗), DX403 (+5.0h, 16.25 ✗), DX404 (+2.25h, 13.5 ✗) — 486 seats
> - P-2211: DX422 (+5.75h, 17.0 ✗), DX423 (+5.0h, 16.25 ✗), DX424 (+1.75h, 13.0 ✗) — 486 seats
> - P-2218: DX433 (+6.0h, 15.75 vs 12.0 ✗), DX434 (+2.75h, 12.5 ✗) — 324 seats
> - P-2225: DX453 (+6.5h, 14.75 vs 12.0 ✗), DX454 (+3.75h, 12.0 — legal) — 144 seats
> - P-2293: DX413 (+3.25h, 12.75 vs 12.5 ✗), DX588 (+2.25h, 11.75 — legal) — 324 seats
> - P-2232: DX462 (+5.75h, 11.0 vs 13.0 — legal) — 72 seats
> 
> Reasoning:
> - Closure impact for BLR on 2026-09-17, 08:00–14:00Z: 13 legs at BLR (departures and arrivals), minimum delay = reopen + 30 min turnaround.
> - FDP after delay checked per leg against RULE-FDP-01 (13h minus 0.5h per sector beyond the 2nd); breaching legs need re-crewing from reserves or cancellation.
> - Passenger total 1,836 quoted from the closure result.

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six rostered crew on P-2203 breach RULE-FDP-01 if they fly all four legs: the delayed duty runs 12.75h against a 12.0h limit (4 sectors), release slipping from 12:45Z to 14:15Z. They can legally do the first three legs; DX404 needs re-crewing or cancelling.
> 
> - Breaching: C-3187 (Captain), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (Cabin Crew)
> - All other rules pass for everyone — duty 7-day, 28-day block, rest, rating, certifications, base.
> 
> Reasoning:
> - Delay simulation for VT-DXA on 2026-09-16, DX401 +1.5h: pairing P-2203, report 01:30Z, new release 14:15Z, FDP 12.75h vs 12.0h limit, breach flagged, legal_leg_count 3, legs needing re-crew: DX404.
> - Per-crew legality checks on all seven rules: only RULE-FDP-01 fails; RULE-DUTY-02 headroom 26–39h, RULE-FLT-03 headroom 28–46h, RULE-REST-04 ≥23.5h before report, RULE-QUAL-05 all A320-rated, RULE-CERT-06 all valid on 2026-09-16.

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> Yes — C-2210 (S. Kapoor, Captain, DEL) is legal on P-2291 from 2026-09-15, conditional on RULE-BASE-07 deadhead positioning.
> 
> - Positions on DX402, arriving BLR 08:45Z; report slips from 06:00Z to 09:00Z → first departure delayed ~3h.
> - Total cost 41,200 INR (callout 18,500 + positioning 6,500 + delay 16,200).
> - Reserve on-call window 03:00–15:00Z covers the 09:00Z report.
> 
> Reasoning:
> - Legality check on C-2210 for P-2291 (duty days 15–16 Sep): all seven rules pass; RULE-BASE-07 conditional only.
> - Tightest margins: FDP 10.75h vs 12.5h limit (16 Sep, 3 sectors); RULE-REST-04 12.50h vs 12h minimum between the two duty days — only 0.5h slack, so any release slip on 15 Sep breaks the 16 Sep report.
> - 7-day duty 35.31h of 60h; 28-day block 50.15h of 100h — ample headroom. A320 rating and all 4 certifications valid both days.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> No — C-5417 (S. Krishnan, Cabin Crew) cannot legally operate P-2213 on VT-DXB on 2026-09-19: recurrent training expired 2026-09-17, breaching RULE-CERT-06. All other six rules pass.
> 
> Reasoning:
> - Pairing lookup for VT-DXB on 2026-09-19: P-2213, four sectors DX421–DX424, report 02:00Z / release 13:15Z; C-5417 rostered as Cabin Crew.
> - Legality check on C-5417's rostered duty: RULE-FDP-01 11.25h vs 12.0h limit, RULE-DUTY-02 32.89h/60h (27.11h headroom), RULE-FLT-03 58.46h/100h, RULE-REST-04 60.75h rest, RULE-QUAL-05 A320 rated, RULE-BASE-07 n/a for rostered — all pass.
> - Certification record: recurrent_training valid to 2026-09-17 only; licence, medical and dangerous goods still valid.
> - Say the word and I'll pull cover options for the Cabin Crew slot on P-2213.

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest next report: 2026-09-17T03:30Z.
> 
> Reasoning:
> - Rest calculation on a 15:30Z release on 2026-09-16: minimum rest 12h (RULE-REST-04).

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> No — C-3305 cannot take the full two-day P-2291.
> 
> - Two blockers: his reserve on-call window 00:00–05:30Z does not cover the 06:00Z report on 2026-09-15, and day 2 breaches RULE-DUTY-02 — 68.25h in the 7 days ending 2026-09-16, 8h15m over the 60h limit.
> - Everything else passes: FDP 9.50h/10.75h vs 12.5h for 3 sectors (RULE-FDP-01), 47.60h block/28d (RULE-FLT-03), 12.50h rest between days (RULE-REST-04), A320 rated (RULE-QUAL-05), all 4 certifications valid (RULE-CERT-06), own base BLR (RULE-BASE-07).
> - Day 1 alone would sit at 59.50h/60h — only 0.50h headroom — so even a single-day cover leaves nothing spare.
> 
> Reasoning:
> - Legality check for C-3305 on P-2291 (both duty days 2026-09-15/16): verdict not legal, not available; callout cost ₹18,500.
> - P-2291 in the roster: VT-DXC, day 1 BLR→DEL report 06:00Z, day 2 DEL→BLR report 04:00Z.
> - Binding rules: RULE-DUTY-02 breach; reserve window from the reserve roster.

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> Cancelling DX404 (MAA–BLR) on 2026-09-16 affects 162 passengers at a direct cancellation cost of INR 250,000. It releases pairing P-2203 and its six crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089).
> 
> Reasoning:
> - Cancellation impact for DX404 on 2026-09-16 from the flight schedule and cost table: 162 seats sold/affected, INR 250,000 per-leg cancellation cost.
> - Crew released are the rostered crew on P-2203.

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew are at or above 45 duty hours for the 7 days ending 2026-09-15:
> 
> - C-2087 R. Iyer (Captain) — 51.83h duty, 8.17h headroom; 23.5h block/28d
> - C-3305 V. Menon (Captain) — 50.0h duty, 10.0h headroom; 33.6h block/28d
> 
> Neither has planned duty on 2026-09-15 (0h each), so both stay under the limit.
> 
> Reasoning:
> - Rolling-limit check for 2026-09-15 at the 45h threshold: 2 crew returned, history plus rostered duty through that date.
> - Limits applied: RULE-DUTY-02 (60h/7d) and RULE-FLT-03 (100h/28d); both remain within both limits.

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> Only one reserve captain both covers the 03:00Z report and is qualified: **C-3315 (M. Pillai)** — BLR base, ATR72 rated, on call 03:00–15:00Z, 45 min to reach.
> 
> The other three fail:
> - C-3305 (V. Menon) — window 00:00–05:30Z covers it, but A320 only (RULE-QUAL-05).
> - C-3310 (D. Reddy) — A320 only, and window 06:00–18:00Z misses the 03:00Z report.
> - C-2210 (S. Kapoor) — A320 only, and DEL-based so deadhead positioning needed (RULE-BASE-07).
> 
> Reasoning:
> - VT-DXE on 2026-09-16 is pairing P-2224, Captain C-3231 (L. Verma); day reports 03:00Z at BLR, releases 11:15Z, 4 sectors, 8.25 duty hours.
> - Recorded C-3231 sick from 2026-09-16 — P-2224 Captain slot vacant, DX451/452/453/454, 288 passengers exposed (P-2227 on 2026-09-19 also shows vacant).
> - Reserve roster at 03:00Z report, Captain / ATR72 / BLR: 1 eligible, 3 excluded as above (RULE-QUAL-05, RULE-BASE-07).
> - Note: eligibility here is window/rating/base only; say the word and I'll run the full seven-rule check and cost on C-3315 for P-2224.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> No — C-5837 (A. Sharma, Captain, BLR) is **not legal** for P-2291.
> 
> - Breach: RULE-REST-04 — release from P-2291 on 2026-09-16 at 14:45Z leaves only 10.75h before reporting for P-2204 at 2026-09-17T01:30Z (minimum 12h). Downstream conflict.
> - Everything else passes: FDP 9.50h/10.75h vs 12.5h limits, 7-day duty peaks 54.00h vs 60h, 28-day block 77.51h vs 100h, A320 rated, all 4 certifications valid, own-base callout at BLR. Day-off callout cost would have been ₹24,000.
> - Note: his rostered line here shows 14/15/16/17/20 Sep involvement, not just 14/17/20 — the 17 Sep pairing P-2204 is what blocks it.
> 
> Reasoning:
> - Legality check of C-5837 against P-2291 (2026-09-15 to 2026-09-16), all seven rules over his full timeline.
> - Rulebook: RULE-REST-04 (12h min rest), RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two flights, both on pairing P-2234, 144 passengers exposed. No FDP breaches — both delay legally, no re-crewing needed.
> 
> - DX461 (arrival HYD, sched 06:30Z): min delay 3.0h, crew FDP after delay 8.25h vs 13h limit, 72 seats
> - DX462 (departure HYD, sched 07:15Z): min delay 2.25h, crew FDP after delay 7.5h vs 13h limit, 72 seats
> 
> Reasoning:
> - Closure impact for HYD 2026-09-19 05:00–09:00Z: 2 affected legs, reopen + 30 min turnaround drives the minimum delays.
> - Both legs sit on P-2234; per_pairing shows 2 legs, 144 seats, max delay 3.0h, 0 FDP breaches.
> - RULE-FDP-01 checked on the operating crew after delay — both under the 13h limit, action is "delay (crew legal)".

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any A320 leg — 162 seats at risk, e.g. DX401. No single leg stands above the rest: exposure is set by aircraft type, and all 105 A320 legs carry the same 162 seats, versus 72 seats on each of the 42 ATR72 legs. Cancellation cost is INR 250,000 per leg either way.
> 
> Reasoning:
> - Seats-at-risk view of the flight schedule: A320 = 162 seats × 105 legs (example DX401); ATR72 = 72 seats × 42 legs (example DX451).
> - Cost table: cancellation INR 250,000 per flight, flat regardless of type.

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> **Recommended: Option 1 — reserve callout C-3310, ₹18,500, no delay, covers both duty days.**
> 
> P-2291 is a two-day pairing (BLR→…→DEL overnight, back 16 Sep); the cover must take the full remaining pairing — 6 legs, 972 passengers at risk.
> 
> Ranked options:
> - **1. C-3310 — reserve callout — ₹18,500, 0h delay, all 2 duty days.** BLR-based, A320-rated, on-call 06:00–18:00Z, reachable in 45 min; all seven rules pass, RULE-DUTY-02 headroom 39.8h.
> - **2. C-1526 — day-off callout — ₹24,000, 0h delay,** BLR-based, A320-rated, reachable in 90 min; legal, headroom 10.3h.
> - **3. C-3983 — day-off callout — ₹24,000, 0h delay,** BLR-based, reachable in 45 min; legal, headroom 10.1h.
> - **4. C-5566 — day-off callout — ₹24,000, 0h delay,** reachable in 60 min; legal, headroom 19.5h.
> - **5. C-2210 — reserve + deadhead from DEL — ₹41,200** (callout 18,500 + positioning 6,500 + delay 16,200), ~3.0h delay to DX412 (deadheads on DX402, arr 08:45Z vs report 09:00Z); RULE-BASE-07 positioning required.
> - **6. Cancel all 6 legs — ₹15,00,000, 972 passengers stranded.** Last resort.
> 
> Reasoning:
> - Cover options for P-2291 Captain from 2026-09-15, required report 06:00Z: 24 candidates screened on rating → reserve window → all seven rules, ranked by cost then delay.
> - Uncovered legs: DX412/DX413/DX588 (15 Sep), DX589/DX590/DX591 (16 Sep); passengers at risk 972.
> - Notable exclusions: C-3305 (reserve window 00:00–05:30Z misses 06:00Z report), C-2087 and C-2143 (RULE-DUTY-02 breach), several with no A320 rating (RULE-QUAL-05), several with RULE-REST-04 conflicts.
> - Nothing committed yet — say the word and I'll apply the cover.

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> Optimal joint plan for 2026-09-18, total ₹42,500, all legs covered, no delay, no one double-assigned:
> 
> - **P-2205 (VT-DXA, DX401/402/403/404)** — C-3940 out: assign **C-3305**, reserve callout, ₹18,500. All seven rules pass; RULE-DUTY-02 headroom 22.8h.
> - **P-2212 (VT-DXB, DX421/422/423/424)** — C-1938 out: assign **C-1017**, day-off callout, ₹24,000. All seven rules pass; RULE-DUTY-02 headroom 18.7h on 2026-09-19.
> 
> Reasoning:
> - Aircraft lines for 2026-09-18: VT-DXA = P-2205 (Capt C-3940), VT-DXB = P-2212 (Capt C-1938); each 4 legs.
> - Joint cover plan with both sick calls reported 2026-09-18T00:30Z: only one reserve Captain (C-3305) is eligible at these report times, so he takes the cheaper slot and the next-best legal option (C-1017, ₹24,000 day-off) takes the other; total ₹42,500 from the cost table.
> - Excluded per the rulebook: C-3310 (reserve window 06:00–18:00Z misses report 01:30Z/02:00Z), C-5566 and C-1443 (RULE-REST-04), and several Captains without A320 rating (RULE-QUAL-05).
> - Backups if either declines: C-1042, C-1526, C-2087 at ₹24,000 each; C-2143 is legal but RULE-REST-04 tight (0.2–0.8h).
> - Nothing committed yet — say the word to apply.

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> Recommendation: keep the rostered crew of P-2203 on DX401–DX403 (delayed) and re-crew DX404 with a full reserve set — legal, ₹75,000.
> 
> - Option 1 (recommended): reserves report 11:45Z for DX404 — C-3310 (CPT), C-3311 (FO), C-3677 (SCC), C-1329 / C-4809 / C-5418 (CC). Cost ₹75,000.
> - Option 2: cancel DX404 — legal but ₹250,000 and 162 passengers stranded.
> 
> Reasoning:
> - Delay on VT-DXA 2026-09-16 (P-2203, DX401–DX404): report 01:30Z, release slips 12:45Z → 14:15Z; FDP 11.25h → 12.75h against a 12.0h limit at 4 sectors — RULE-FDP-01 breach for all six rostered crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089).
> - Only DX404 needs re-crewing; the crew can legally fly 3 legs (delayed 3-leg duty 11.0h vs 12.5h limit).
> - Reserve set checked clear on callout window and RULE-REST-04 (12h rest), FDP 2.50h for the tail leg.
> - Duty/block clocks (RULE-DUTY-02, RULE-FLT-03), ratings (RULE-QUAL-05) and certifications (RULE-CERT-06) all pass for the rostered crew.
> 
> Say the word and I'll commit the reserve cover on the working scenario.

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> **C-5417 (S. Krishnan, Cabin Crew) is off P-2213 on 2026-09-19** — recurrent training expired 2026-09-17, so RULE-CERT-06 fails. Recommended cover: **C-4809, reserve callout, ₹9,500, no delay, all 4 legs (DX421–DX424, 648 pax)**.
> 
> - Rank 1 — C-4809 (reserve): ₹9,500, all seven rules pass
> - Rank 2 — C-1021 (day-off callout): ₹12,500
> - Last resort — cancel all 4 legs: ₹1,000,000, 648 pax stranded
> 
> Say the word and I'll apply C-4809 and draft the callout.
> 
> Reasoning:
> - C-5417's certification record: recurrent_training valid to 2026-09-17, invalid on 2026-09-19 (RULE-CERT-06); licence, medical and DG remain valid.
> - Roster: C-5417 is Cabin Crew on P-2213 (VT-DXB, 2026-09-19, DX421/422/423/424), report 02:00Z at BLR. Recorded unavailable from 2026-09-18 — the slot is now vacant in the working scenario.
> - Cover ranking over 29 candidates, checked against all seven rules: C-4809 BLR-based, A320-rated, on-call 00:00–12:00Z, reachable in 45 min, RULE-DUTY-02 headroom 48.8h.
> - Excluded notables: C-1329/C-2248/C-5418 reserve windows start 04:00Z (after the 02:00Z report); several blocked by RULE-REST-04 or RULE-QUAL-05.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> **BLR closed 08:00–14:00Z, 17 Sep — 13 legs, 6 pairings, 1,836 passengers affected.** 10 of the 13 legs breach RULE-FDP-01 after the minimum delay (reopen + 30 min turnaround), so each of those pairings needs a re-crew of its tail legs or cancellation.
> 
> Per pairing, worst-first:
> 
> - **P-2204** (DX402/403/404) — 3 legs, 486 seats, all 3 breach; delays 5.75h / 5.0h / 2.25h, FDP after delay 17.0 / 16.25 / 13.5 vs 12.0 limit. Whole day re-crewed from reserves, or cancel the tail.
> - **P-2211** (DX422/423/424) — 3 legs, 486 seats, all 3 breach; delays 5.75h / 5.0h / 1.75h, FDP 17.0 / 16.25 / 13.0 vs 12.0. Same treatment.
> - **P-2218** (DX433/434) — 2 legs, 324 seats, both breach; delays 6.0h and 2.75h, FDP 15.75 and 12.5 vs 12.0.
> - **P-2225** (DX453/454) — 2 legs, 144 seats; DX453 breaches (delay 6.5h, FDP 14.75 vs 12.0), DX454 legal at exactly 12.0 after 3.75h delay.
> - **P-2293** (DX413/588) — 2 legs, 324 seats; DX413 breaches marginally (delay 3.25h, FDP 12.75 vs 12.5), DX588 legal (11.75 vs 12.5) after 2.25h.
> - **P-2232** (DX462) — 1 leg, 72 seats, no breach: 5.75h delay, FDP 11.0 vs 13.0. Delay only, keep rostered crew.
> 
> Recovery sequence I'd work: P-2232 needs nothing but a delay message; P-2293 and P-2225 need one leg re-crewed each (smallest reserve draw); P-2218 needs two; P-2204 and P-2211 are the heavy items — each a full 3-leg re-crew, 486 seats apiece, and the likeliest cancellation candidates if reserves run out. Say the word and I'll rank reserve options leg by leg, or price the cancellation side for comparison.
> 
> Reasoning:
> - Station closure impact for BLR on 2026-09-17, 08:00–14:00Z: 13 affected legs, 1,836 passengers, 6 pairings; minimum delay = reopen + 30 min turnaround.
> - Per-leg FDP after delay vs limit taken from that same result; breach flags on DX453, DX433, DX402, DX422, DX403, DX423, DX413, DX434, DX404, DX424 (RULE-FDP-01).
> - Seats and leg counts per pairing quoted from the per-pairing totals in the result.
> - Sequencing above is my ordering by re-crew size and seats at risk; costs and reserve availability not yet looked up.

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Callout drafted for C-3310 (D. Reddy, Captain) on P-2291 (VT-DXC), two duty days, acknowledgement by 2026-09-14T18:30Z.
> 
> **CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291**
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> - Day 1 (2026-09-15): report 06:00Z at BLR crew room; flights DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z. Overnight at DEL — hotel arranged.
> - Day 2 (2026-09-16): report 04:00Z at DEL crew room; flights DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> - Acknowledge by 2026-09-14T18:30Z (30 minutes): reply ACK P-2291.
> - Contact: Crew Control desk, BLR.
> 
> Reasoning:
> - Roster detail for P-2291: report/release times, flights per day, DEL overnight with hotel arranged.
> - Crew record for C-3310: D. Reddy, Captain.
> - Draft only — nothing committed to the roster; say the word and I'll apply the cover (full seven-rule check runs first).

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> Cheapest legal cover for FO C-4520 (R. Sharma) on P-2235, VT-DXF, 2026-09-20: **reserve callout C-3316 — 18,500 INR, no delay, all legs covered.**
> 
> - Next best: day-off callouts C-1313 / C-1317 / C-2085 / C-3057 at 24,000 INR each.
> - Last resort: cancel both legs (DX461, DX462) — 500,000 INR, 144 passengers stranded.
> 
> Reasoning:
> - Pairing lookup for VT-DXF on 2026-09-20: P-2235, FO slot held by C-4520; legs DX461 and DX462, report 2026-09-20T04:00Z, 144 passengers exposed.
> - Cover ranking (26 candidates, sick call at 03:30Z): C-3316 is BLR-based, ATR72-rated, on-call 03:00–15:00Z, reachable in 45 min; all seven rules pass (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07), RULE-DUTY-02 headroom 54.8h.
> - 21 candidates excluded on RULE-QUAL-05 (no ATR72 rating); C-3136 excluded on RULE-REST-04 (overlap with P-2228).
> - Nothing committed — say the word and I'll apply C-3316 and draft the callout.

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Three per line, and they're exactly what the standing briefing carries:
> 
> - **Tightest 7-day duty headroom (plus cert validity) across that line's rostered crew** — tells you if the line can absorb a delay before RULE-DUTY-02 or RULE-CERT-06 bites. Tomorrow (2026-09-15) the tightest is VT-DXA at 27.83h on C-3988; all certs valid on every line.
> - **Highest disruption-risk score on the line** — flags where a sick call is most likely, so you pre-position cover. Tomorrow: VT-DXC 0.78 (C-1042), VT-DXA 0.71 (C-3940), VT-DXB 0.69 (C-1938).
> - **Eligible reserves at that line's report time** — the cover depth if the line breaks, already filtered by on-call window, rating and base (RULE-QUAL-05 / RULE-BASE-07). Tomorrow VT-DXC has 9 eligible at 06:00Z report; VT-DXA, VT-DXB and VT-DXD have only 3 each at their early reports (01:30–02:30Z).
> 
> Together they answer: can this line take a hit, how likely is a hit, and who covers it.
> 
> Reasoning:
> - Morning briefing for 2026-09-15, six aircraft lines with today's pairing and report time; it surfaces duty headroom, reserve availability by on-call window/rating, and provided risk signals per line.
> - Headroom figures and risk scores read straight off each line's crew rows; eligible-reserve lists counted from the same rows.
> - Rules in play: RULE-DUTY-02 (60h/7d), RULE-CERT-06, RULE-QUAL-05, RULE-BASE-07.
