# Eval report — agent-sdk

Run: 2026-09-05T05:39:45Z · **33/38** questions with all expected facts recalled · latency p50 9173 ms / p95 17371 ms / max 27190 ms · est. cost $2.53

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 10275 |
| Q02 | 1 | ✅ |  | get_duty_clock | 7351 |
| Q03 | 1 | ✅ |  | list_flights | 6178 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 8726 |
| Q05 | 1 | ✅ |  | get_flight | 6494 |
| Q06 | 1 | ✅ |  | get_crew | 7124 |
| Q07 | 1 | ✅ |  | get_crew | 6729 |
| Q08 | 1 | ✅ |  | get_pairing | 6818 |
| Q09 | 1 | ✅ |  | list_flights | 6790 |
| Q10 | 1 | ✅ |  | list_flights | 6432 |
| Q11 | 1 | ✅ |  | list_crew | 6148 |
| Q12 | 1 | ✅ |  | schedule_stats | 6627 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 7598 |
| Q14 | 1 | ✅ |  | list_routes | 6658 |
| Q15 | 1 | ✅ |  | find_pairings | 5864 |
| Q16 | 1 | ✅ |  | get_risk_signal | 6197 |
| Q17 | 2 | ✅ |  | simulate_crew_removal | 13694 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 11120 |
| Q19 | 2 | ✅ |  | station_closure_impact | 11349 |
| Q20 | 2 | ✅ |  | simulate_delay | 10729 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 10375 |
| Q22 | 2 | ✅ |  | find_pairings, check_rostered_legality | 10127 |
| Q23 | 2 | ✅ |  | earliest_next_report | 6051 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 10654 |
| Q25 | 2 | ✅ |  | cancellation_impact | 12882 |
| Q26 | 2 | ✅ |  | crew_near_limits | 8079 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage | 14756 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 9620 |
| Q29 | 2 | ✅ |  | station_closure_impact | 8088 |
| Q30 | 2 | ✅ |  | seats_at_risk | 6931 |
| Q31 | 3 | ❌ | Cancel all 6 flights of the pairing | recommend_cover | 15563 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 24740 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | simulate_delay, resolve_delay_options | 12638 |
| Q34 | 3 | ✅ |  | get_crew, get_certifications, declare_unavailable, recommend_cover | 17371 |
| Q35 | 3 | ❌ | DX403, DX423, DX434, DX404, DX424 | station_closure_impact | 27190 |
| Q36 | 3 | ❌ | acknowledgement request with deadline, contact for questions | draft_callout_notification | 10116 |
| Q37 | 3 | ✅ |  | find_pairings, recommend_cover | 12828 |
| Q38 | 3 | ❌ | reserve availability by window and rating for the day | morning_briefing | 12848 |

## Q01 — Who is on reserve at BLR on 2026-09-15, and what are their on-call windows?

**Expected:** `[{"crew_id": "C-3305", "rank": "Captain", "window": {"start": "00:00", "end": "05:30"}}, {"crew_id": "C-3310", "rank": "Captain", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3311", "rank": "First Officer", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3312", "rank": "First Officer", "window": {"start": "00:00", "end": "12:00"}}, {"crew_id": "C-3315", "rank": "Capt`

**Answer:**

> 12 reserves at BLR tomorrow (2026-09-15), all active:
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
> - C-2111 A. Gupta, SCC A320/ATR72 — 04:00–16:00Z
> - C-3677 M. Iyer, SCC A320/ATR72 — 04:00–16:00Z
> - C-1329 P. Pillai, CC — 04:00–16:00Z
> - C-2248 H. Reddy, CC — 04:00–16:00Z
> - C-5418 S. Das, CC — 04:00–16:00Z
> - C-4809 M. Das, CC — 00:00–12:00Z
> 
> Reasoning:
> - Reserve roster for BLR on 2026-09-15: 12 reserves, ranks, ratings and on-call windows as listed.
> - A callout only stands if the required report time falls inside the window; RULE-BASE-07 keeps these BLR-based reserves deadhead-free for duties starting at BLR.

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 has 20.93 duty hours in the 7 days 2026-09-08 to 2026-09-14, leaving 39.07h headroom under the 60h limit (RULE-DUTY-02).
> 
> Reasoning:
> - C-1042's duty clock: duty_hours_7d 20.93 over window 2026-09-08 → 2026-09-14; contributing days 2026-09-09 (9.99h) and 2026-09-12 (10.94h).
> - RULE-DUTY-02 limit 60h/7 days → headroom 39.07h.
> - Also on the clock: 64.27 block hours in the 28 days to 2026-09-14, 35.73h headroom under RULE-FLT-03.

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> One flight departs DEL on 2026-09-15:
> - DX402 DEL–BLR, off 06:00Z / on 08:45Z, 2.75h block, VT-DXA (A320), 162 seats.
> 
> Reasoning:
> - Flight schedule filtered to DEL departures on 2026-09-15: 1 leg, 162 seats total.

## Q04 — List all certifications expiring within 30 days of 2026-09-15.

**Expected:** `[{"crew_id": "C-2087", "cert_type": "licence", "valid_to": "2026-09-18"}, {"crew_id": "C-2091", "cert_type": "medical_class1", "valid_to": "2026-09-23"}, {"crew_id": "C-5417", "cert_type": "recurrent_training", "valid_to": "2026-09-17"}, {"crew_id": "C-3116", "cert_type": "dangerous_goods", "valid_to": "2026-09-28"}, {"crew_id": "C-5020", "cert_type": "recurrent_training", "valid_to": "2026-10-03"`

**Answer:**

> Six certifications lapse between 2026-09-15 and 2026-10-15:
> 
> - C-5417 S. Krishnan (Cabin Crew) — recurrent training, expires 2026-09-17
> - C-2087 R. Iyer (Captain) — licence, expires 2026-09-18
> - C-2091 H. Naidu (Captain) — medical class 1, expires 2026-09-23
> - C-3116 R. Naidu (First Officer) — dangerous goods, expires 2026-09-28
> - C-5020 K. Nair (First Officer) — recurrent training, expires 2026-10-03
> - C-2993 I. Kulkarni (First Officer) — medical class 1, expires 2026-10-08
> 
> Reasoning:
> - Certification register, window 2026-09-15 to 2026-10-15: 6 records, soonest first.
> - RULE-CERT-06 — any duty on or after the expiry date is illegal; C-5417 and C-2087 fall inside the current schedule week (to 2026-09-20).

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> VT-DXC (A320), 162 seats — DX412 BLR–BOM on 2026-09-15, dep 07:00Z / arr 08:45Z.
> 
> Reasoning:
> - Flight schedule, DX412 on 2026-09-15: aircraft VT-DXC, type A320, 162 seats, block 1.75h, operated on pairing P-2291.

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 (D. Reddy, Captain, BLR, A320) is on reserve 06:00–18:00Z, reachable in 45 minutes.
> 
> Reasoning:
> - Reserve roster: C-3310 on-call window 06:00–18:00Z, reserve every day 2026-09-14 through 2026-09-20, base BLR.
> - Crew profile: reachability 45 min, active, A320 rated, no pairings rostered; disruption risk 0.17 (baseline).
> - Callout report time must fall inside that window, and RULE-BASE-07 applies for duties starting away from BLR.

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 (S. Kapoor, Captain) is based at DEL and rated on A320 only.
> 
> Reasoning:
> - Crew profile for C-2210: base DEL, ratings [A320], status active.
> - Also a reserve at DEL, on-call 03:00–15:00Z, all seven days of the week — relevant to RULE-QUAL-05 and RULE-BASE-07 if considered for cover.

## Q08 — Which crew are assigned to pairing P-2291, and in what roles?

**Expected:** `[{"crew_id": "C-1042", "role": "Captain"}, {"crew_id": "C-1694", "role": "First Officer"}, {"crew_id": "C-3005", "role": "Senior Cabin Crew"}, {"crew_id": "C-4395", "role": "Cabin Crew"}, {"crew_id": "C-4273", "role": "Cabin Crew"}, {"crew_id": "C-1873", "role": "Cabin Crew"}]`

**Answer:**

> P-2291 (VT-DXC, 2026-09-15 to 2026-09-16) carries six crew:
> - C-1042 A. Nair — Captain
> - C-1694 S. Menon — First Officer
> - C-3005 H. Chandra — Senior Cabin Crew
> - C-4395 V. Rao — Cabin Crew
> - C-4273 P. Menon — Cabin Crew
> - C-1873 K. Joshi — Cabin Crew
> 
> Reasoning:
> - Pairing record for P-2291: aircraft VT-DXC, two duty days (BLR→DEL 15 Sep, DEL→BLR 16 Sep), crew list with roles as above.

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> Two BLR→BOM legs on 2026-09-17:
> - DX431 — dep 03:30Z, arr 05:15Z, VT-DXD (A320), 162 seats, 1.75h block
> - DX412 — dep 07:00Z, arr 08:45Z, VT-DXC (A320), 162 seats, 1.75h block
> 
> Reasoning:
> - Flight schedule for 2026-09-17, BLR→BOM: 2 legs, 324 seats total.

## Q10 — How many flights operate on 2026-09-16 in total?

**Expected:** `21`

**Answer:**

> 21 flights operate on 2026-09-16, totalling 2,862 seats across all six aircraft.
> 
> Reasoning:
> - Flight schedule for 2026-09-16: 21 legs (DX401–404, DX421–424, DX431–434, DX451–454, DX461/462, DX589–591), all on VT-DXA/B/C/D (A320) and VT-DXE/F (ATR72).

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> One captain is based at DEL:
> - C-2210 — S. Kapoor, A320-rated, active, seniority 2, reachable in 60 min.
> 
> Reasoning:
> - Crew list filtered to base DEL, rank Captain: count 1.

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> Longest block time in the week's schedule is 2.75h, on four flight numbers:
> - DX401
> - DX402
> - DX588
> - DX589
> 
> Reasoning:
> - Flight schedule stats for the week 2026-09-14 to 2026-09-20 (147 legs): longest block 2.75h on DX401/DX402/DX588/DX589; shortest is 1.0h (DX403/DX404/DX453/DX454).

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> C-2087 (R. Iyer) is a Captain, BLR-based, A320-rated. Block hours in the 28 days ending 2026-09-14: 23.5h, leaving 76.5h headroom under the 100h limit.
> 
> Reasoning:
> - Crew profile for C-2087: rank Captain, base BLR, rating A320, active.
> - C-2087's duty clock: 28-day window 2026-08-18 to 2026-09-14, 23.5 block hours vs 100h limit (RULE-FLT-03).
> - Same clock shows 51.83 duty hours in the 7-day window, 8.17h headroom (RULE-DUTY-02) — tighter constraint if you're planning cover.

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> BLR serves all seven other stations nonstop — 73 departures across the week (2026-09-14 to 2026-09-20):
> - HYD 14, MAA 14, CCU 11, BOM 10, DEL 10, COK 7, GOI 7
> 
> Reasoning:
> - Flight schedule, nonstop destinations from BLR: 7 destinations, counts as listed, 73 total flights in the schedule week.

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> C-3171 (P. Chandra) is the Senior Cabin Crew on P-2210, VT-DXB's pairing on 2026-09-16.
> 
> Reasoning:
> - Pairing search for VT-DXB on 2026-09-16: single pairing P-2210, flights DX421–DX424, crew list as rostered.

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042's disruption-risk score is 0.78, driven by:
> - short-rest pattern over the last 14 days
> - two fatigue reports this month
> 
> Reasoning:
> - Risk signal for C-1042 as of 18:00Z: score 0.78 with the two drivers listed; this is a provided input, not a computed figure.

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Immediately uncrewed on 2026-09-15 (Captain slot, P-2291): DX412, DX413, DX588 — 486 passengers exposed.
> 
> - Also at risk on 2026-09-16: DX589, DX590, DX591 (another 486 pax; 972 total).
> - P-2291 overnights DEL, so the cover must take the full remaining pairing.
> 
> Reasoning:
> - Removal impact for C-1042 (A. Nair, Captain) on P-2291 from 2026-09-15: day 1 BLR→DEL legs uncovered now, day 2 DEL→BLR legs at risk.
> - Cover candidate must hold the aircraft rating for the pairing (RULE-QUAL-05).
> - Not yet recorded on the working scenario — say the word and I'll declare him unavailable and rank cover options.

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Not legal — C-2087 (R. Iyer) breaches RULE-DUTY-02 on both duty days of P-2291:
> - 2026-09-15: 61.33h in the 7 days to 15 Sep — over the 60h limit by 1h20m
> - 2026-09-16: 61.08h in the 7 days to 16 Sep — over by 1h05m
> 
> Everything else passes: FDP 9.50h (15 Sep) and 10.75h (16 Sep) against a 12.5h limit for 3 sectors; 37.50h block in 28 days (70.25h/62.50h headroom); 12.50h rest between the two duty days (min 12h); A320 rated; all 4 certifications valid both days (note licence expires 2026-09-18); day-off callout from own base BLR, so no positioning needed. Callout cost would be ₹24,000 — but the cover would be refused as illegal.
> 
> Reasoning:
> - Legality check of C-2087 against P-2291 from 2026-09-15, all seven rules over both duty days.
> - RULE-DUTY-02 daily duty in the rolling window: 09-09 11.0, 09-10 10.5, 09-11 8.0, 09-12 12.0, 09-13 4.33 (14th), plus 9.5 on 15 Sep and 10.75 on 16 Sep — pushing both windows past 60h.
> - Cost from the cost table: day-off Captain callout ₹24,000.

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights on 2026-09-17, 1,836 passengers exposed, across 6 pairings. 10 of the 13 breach RULE-FDP-01 after the minimum reopen delay and need re-crewing or cancellation.
> 
> Breaching (flight — min delay — FDP vs limit):
> - DX453 — 6.5h — 14.75 vs 12.0 (P-2225)
> - DX433 — 6.0h — 15.75 vs 12.0 (P-2218)
> - DX402 — 5.75h — 17.0 vs 12.0 (P-2204)
> - DX422 — 5.75h — 17.0 vs 12.0 (P-2211)
> - DX403 — 5.0h — 16.25 vs 12.0 (P-2204)
> - DX423 — 5.0h — 16.25 vs 12.0 (P-2211)
> - DX413 — 3.25h — 12.75 vs 12.5 (P-2293)
> - DX434 — 2.75h — 12.5 vs 12.0 (P-2218)
> - DX404 — 2.25h — 13.5 vs 12.0 (P-2204)
> - DX424 — 1.75h — 13.0 vs 12.0 (P-2211)
> 
> Crew still legal on the delay: DX462 (5.75h, 11.0/13.0), DX454 (3.75h, 12.0/12.0), DX588 (2.25h, 11.75/12.5).
> 
> Reasoning:
> - Closure impact for BLR, 2026-09-17 08:00–14:00Z: 13 legs at BLR (departures and arrivals), min delay = reopen + 30 min turnaround.
> - Pairings affected: P-2204 (DX402/403/404), P-2211 (DX422/423/424), P-2218 (DX433/434), P-2225 (DX453/454), P-2232 (DX462), P-2293 (DX413/DX588).
> - FDP after delay compared against RULE-FDP-01 (13h base, less 0.5h per sector beyond the 2nd) per pairing.

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six crew on P-2203 breach RULE-FDP-01 if they fly all four legs. The delayed duty runs 12.75h against a 12.0h limit (4 sectors), report 01:30Z, new release 14:15Z. They can legally do the first three legs; DX404 needs re-crewing or cancelling.
> 
> - Breaching: C-3187 (Capt), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (CC) — same breach, −0.75h margin each.
> - All other rules pass for all six.
> 
> Reasoning:
> - Delay simulation for VT-DXA on 2026-09-16, 1.5h before DX401: pairing P-2203, FDP 11.25h → 12.75h vs 12.0h limit (RULE-FDP-01), legal leg count 3, DX404 needs re-crew.
> - Per-crew legality checks: RULE-DUTY-02 (max 33.31h/60h), RULE-FLT-03 (max 71.85h/100h), RULE-REST-04, RULE-QUAL-05 (all A320-rated), RULE-CERT-06 (all valid on 2026-09-16), RULE-BASE-07 all pass.

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> Yes — C-2210 (S. Kapoor, Captain, DEL) is legal on P-2291 from 2026-09-15, conditional on paid deadhead positioning under RULE-BASE-07. All seven rules pass; the operational consequence is a ~3h delay to the first departure and ₹41,200 total cost.
> 
> - Positioning on DX402, arrives BLR 08:45Z; report slips from 06:00Z to 09:00Z → first departure delayed ~3.0h.
> - Cost: callout ₹18,500 + deadhead ₹6,500 + delay ₹16,200 = ₹41,200.
> 
> Reasoning:
> - Legality check for C-2210 on P-2291 (duty days 15–16 Sep): FDP 9.50h/10.75h vs 12.5h limit (3 sectors, RULE-FDP-01); 7-day duty 35.31h of 60h (RULE-DUTY-02); 28-day block 50.15h of 100h (RULE-FLT-03); rest 12.50h vs 12h minimum, margin only 0.5h between the two duty days (RULE-REST-04); A320 rated (RULE-QUAL-05); all 4 certifications valid both days (RULE-CERT-06).
> - Reserve on-call window 03:00–15:00Z covers the revised 09:00Z report.
> - RULE-BASE-07 conditional: base DEL ≠ duty start BLR, so positioning is required and chargeable.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> No — C-5417 (S. Krishnan, Cabin Crew) cannot legally operate P-2213 on VT-DXB on 2026-09-19: recurrent training expired 2026-09-17 (RULE-CERT-06). All six other rules pass, so the certification is the only blocker.
> 
> Reasoning:
> - Pairing lookup for VT-DXB on 2026-09-19: P-2213, four sectors DX421–DX424, report 02:00Z / release 13:15Z; C-5417 rostered as Cabin Crew.
> - C-5417's rostered legality check on 2026-09-19: RULE-CERT-06 breach (recurrent_training expiry 2026-09-17).
> - Passing: RULE-FDP-01 (11.25h vs 12.0h for 4 sectors), RULE-DUTY-02 (32.89h/60h), RULE-FLT-03 (58.46h/100h), RULE-REST-04 (60.75h rest), RULE-QUAL-05 (A320 rated), RULE-BASE-07 (rostered, BLR).

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
> - Day 1 (2026-09-15) alone is legal on the rules, but day 2 (2026-09-16) breaches RULE-DUTY-02: 68.25h duty in the 7 days ending 16 Sep, 8h15m over the 60h limit.
> - Separately, his reserve on-call window (00:00–05:30Z) does not cover the 06:00Z report on 15 Sep, so a straight reserve callout isn't available either.
> 
> Reasoning:
> - Legality check of C-3305 against P-2291 (2026-09-15 → 2026-09-16), all seven rules: FDP-01 pass (9.50h and 10.75h vs 12.5h for 3 sectors), FLT-03 pass (47.60h/100h), REST-04 pass (12.50h between days), QUAL-05 pass (A320), CERT-06 pass, BASE-07 pass (own base BLR).
> - Only breach: RULE-DUTY-02 on 2026-09-16 — headroom on 15 Sep is just 0.50h (59.50h), so the second duty day tips him over.
> - Reserve roster window 00:00–05:30Z vs pairing report 06:00Z on day 1.
> - Callout cost if it were legal: ₹18,500 (cost table).

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> **DX404 on 2026-09-16 (MAA–BLR): 162 passengers affected, direct cancellation cost INR 250,000.** Cancelling releases pairing P-2203's six crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089).
> 
> Reasoning:
> - Cancellation impact for DX404 on 2026-09-16: route MAA-BLR, 162 passengers affected.
> - Cost table: direct cancellation cost 250,000 INR for this leg — direct cost only.
> - Pairing P-2203 crew listed as released by the cancellation.

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew are at 45h or more for the 7 days ending 2026-09-15:
> 
> - C-2087 R. Iyer (Captain) — 51.83h duty, 8.17h headroom; 23.5h block/28d
> - C-3305 V. Menon (Captain) — 50.0h duty, 10.0h headroom; 33.6h block/28d
> 
> Neither has planned duty on 2026-09-15 itself, so these totals are history-driven.
> 
> Reasoning:
> - Rolling-limit check for 2026-09-15 at the 45h threshold: 2 crew returned, with 7-day duty and 28-day block totals as listed.
> - RULE-DUTY-02 (60h/7 days) — both still have headroom; RULE-FLT-03 (100h/28 days) — no concern (76.5h and 66.4h headroom).

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> VT-DXE on 2026-09-16 is P-2224, Captain C-3231 (L. Verma), report 03:00Z at BLR. Only one reserve captain both covers the window and is qualified:
> 
> - **C-3315 (M. Pillai)** — BLR, on-call 03:00–15:00Z (covers 03:00Z report), ATR72 rated, 45 min reachability. Eligible.
> - C-3305 (V. Menon) — window 00:00–05:30Z does cover 03:00Z, but A320 only, no ATR72 rating (RULE-QUAL-05).
> - C-3310 (D. Reddy) — window 06:00–18:00Z does not cover 03:00Z, and no ATR72 rating.
> - C-2210 (S. Kapoor) — window covers, but no ATR72 rating and based DEL, so deadhead positioning required (RULE-BASE-07).
> 
> Reasoning:
> - Pairing lookup for VT-DXE on 2026-09-16: P-2224, single duty day, report 03:00Z / release 11:15Z, 4 sectors, BLR–BLR.
> - Reserve roster for BLR at report 03:00Z, Captain / ATR72: 1 eligible, 3 excluded with reasons as listed.
> - Rules applied: RULE-QUAL-05 (rating), RULE-BASE-07 (own base), plus reserve on-call window check.
> - Note the sick call at 01:30Z on 16 Sep has not been recorded on the desk scenario — say the word and I'll declare C-3231 unavailable and rank full cover options.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> **No — not legal.** C-5837 (A. Sharma, Captain, BLR) fails RULE-REST-04 downstream: releasing P-2291 at 2026-09-16T14:45Z leaves only 10.75h before his own P-2204 report at 2026-09-17T01:30Z (minimum 12h). Everything else passes; day-off callout cost would have been ₹24,000.
> 
> Reasoning:
> - Legality check on C-5837 against P-2291 (2026-09-15 to 16), all seven rules over his full timeline.
> - RULE-FDP-01 pass (9.50h and 10.75h vs 12.5h limit, 3 sectors each day).
> - RULE-DUTY-02 pass, tightest 54.00h/60h in the 7 days ending 2026-09-20 (6.00h headroom); RULE-FLT-03 pass, tightest 77.51h/100h.
> - RULE-REST-04 breach on 2026-09-17 (10.75h vs 12h, margin −1.25h) — the conflict is with his rostered P-2204, not the cover days themselves.
> - RULE-QUAL-05 (A320 rated), RULE-CERT-06 (all 4 certifications valid), RULE-BASE-07 (own base BLR) all pass.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two flights, both on pairing P-2234, 144 seats exposed — both can be delayed, no re-crew needed.
> 
> - DX461 (arrival HYD 06:30Z): min delay 3.0h, crew FDP after delay 8.25h vs 13h limit — legal
> - DX462 (departure HYD 07:15Z): min delay 2.25h, crew FDP after delay 7.5h vs 13h limit — legal
> 
> Reasoning:
> - Closure impact for HYD on 2026-09-19, 05:00–09:00Z: 2 affected legs, 72 seats each, both on P-2234.
> - Minimum delay = reopen + 30 min turnaround; FDP after delay checked against RULE-FDP-01 (13h) — no breaches, so no tail legs need re-crewing or cancellation.

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any A320 leg — 162 seats at risk, e.g. DX401. No single leg stands out above the others.
> 
> Reasoning:
> - Seats-at-risk view: seat count is fixed by aircraft type — A320 legs carry 162 seats (105 legs in the week), ATR72 legs 72 seats (42 legs).
> - So every A320 leg has identical maximum exposure; cancellation cost is ₹250,000 per leg from the cost table regardless of type.

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> **Recommended: Option 1 — call out reserve Captain C-3310 (₹18,500, no delay, all six legs covered).** P-2291 is a two-day pairing overnighting at DEL, so the cover must take both days (972 passengers exposed); report 2026-09-15T06:00Z at BLR.
> 
> | # | Option | Cost (INR) | Delay | Coverage |
> |---|---|---|---|---|
> | 1 | C-3310 — reserve callout, BLR, A320, on-call 06:00–18:00Z, reachable 45 min | 18,500 | 0 | both days |
> | 2 | C-1526 — day-off callout, BLR, A320, reachable 90 min | 24,000 | 0 | both days |
> | 3 | C-3983 — day-off callout, BLR, A320, reachable 45 min | 24,000 | 0 | both days |
> | 4 | C-5566 — day-off callout, BLR, A320, reachable 60 min | 24,000 | 0 | both days |
> | 5 | C-2210 — DEL reserve + deadhead on DX402 (arr 08:45Z) | 41,200 (18,500 callout + 6,500 positioning + 16,200 delay) | 3.0h on DX412 | both days |
> | 6 | Cancel all 6 legs — last resort | 1,500,000 | — | none; 972 pax stranded |
> 
> Reasoning:
> - Cover options ranked by cost, then delay: 24 Captains considered; all five crew options pass all seven rules (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07).
> - Uncovered legs: DX412/DX413/DX588 on 15 Sep (BLR→…→DEL), DX589/DX590/DX591 on 16 Sep (DEL→…→BLR).
> - C-3310's tightest margin is RULE-DUTY-02 with 39.8h headroom on 16 Sep — comfortable.
> - Option 5 carries RULE-BASE-07 positioning (base DEL ≠ duty start BLR) and pushes DX412 ~3h.
> - Notable exclusions: C-2087 and C-2143 breach RULE-DUTY-02 (60h/7d); C-3305's on-call window 00:00–05:30Z misses the 06:00Z report; six Captains have no A320 rating (RULE-QUAL-05); several blocked on RULE-REST-04 downstream conflicts.
> - Nothing committed yet — say the word and I'll apply the cover.

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> Optimal joint plan — total ₹42,500, all legs covered, no delay, both legal on all seven rules:
> 
> - **P-2205** (VT-DXA) — Captain **C-3305**, reserve callout, ₹18,500. BLR-based, A320-rated, on-call 00:00–05:30Z, reachable in 45 min; duty headroom 22.8h.
> - **P-2212** (VT-DXB) — Captain **C-1017**, day-off callout, ₹24,000. BLR-based, A320-rated, free on the cover days, reachable in 75 min; duty headroom 18.7h.
> 
> Only one reserve captain (C-3305) is eligible at these report times, so the second slot must take the cheapest day-off callout. Say the word and I'll commit both.
> 
> Reasoning:
> - Rosters for 2026-09-18: P-2205/VT-DXA Captain C-3940, P-2212/VT-DXB Captain C-1938 — both out at 00:30Z, four legs vacant on each pairing.
> - Joint cover plan: cheapest combination with no person assigned twice; both options pass RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07.
> - Reserve C-3310 excluded (on-call 06:00–18:00Z does not cover report 01:30Z/02:00Z); C-1443, C-5566 excluded on RULE-REST-04; six others excluded on RULE-QUAL-05 (no A320 rating).
> - Next-best backups at ₹24,000 each: C-1042, C-1526, C-2087; C-2143 is legal but tight on RULE-REST-04 (0.2–0.8h).

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> **Recommended: run the rostered crew of P-2203 on DX401–DX403 (delayed) and re-crew DX404 with a full reserve set — ₹75,000.** The 90-min delay pushes the 4-sector duty to 12.75h against a 12.0h FDP limit (RULE-FDP-01), so the rostered crew can legally fly only the first 3 legs.
> 
> - Option 1 (₹75,000): reserves C-3310 (CPT), C-3311 (FO), C-3677 (SCC), C-1329 / C-4809 / C-5418 (CC) take DX404, report 11:45Z, FDP 2.50h — legal.
> - Option 2 (₹250,000): cancel DX404 — legal but ~3.3x costlier and 162 passengers stranded.
> 
> Reasoning:
> - Delay assessment for VT-DXA on 2026-09-16 (P-2203): report 01:30Z, release moves 12:45Z → 14:15Z; FDP 11.25h → 12.75h vs 12.0h limit at 4 sectors — RULE-FDP-01 breach for all six rostered crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089); all other rules pass for them.
> - Legal leg count 3; only DX404 needs re-crewing.
> - Reserve set on the 3-leg prefix: FDP 11.0h vs 12.5h limit; reserve callout window and RULE-REST-04 12h rest satisfied.
> - Costs from the cost table: reserve callouts ₹75,000 vs cancellation ₹250,000.
> 
> Say the word and I'll commit the reserve set onto DX404.

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> **C-5417's recurrent training expires 2026-09-17**, so their Cabin Crew slot on P-2213 (2026-09-19, VT-DXB, DX421/422/423/424, 648 pax) is invalid under RULE-CERT-06. Recorded as unavailable from 2026-09-18 — their 16 Sep pairing P-2210 is unaffected.
> 
> Recommended cover (report 2026-09-19T02:00Z, BLR):
> - **Option 1 — C-4809, reserve callout, ₹9,500, no delay, all 4 legs.** BLR-based, A320-rated, on-call 00:00–12:00Z, reachable in 45 min; all seven rules pass.
> - Option 2 — C-1021, day-off callout, ₹12,500, all legs.
> - Option 3 — C-1385, day-off callout, ₹12,500, all legs.
> - Last resort — cancel all 4 legs, ₹1,000,000, 648 pax stranded.
> 
> Say the word and I'll commit C-4809 and draft the callout.
> 
> Reasoning:
> - C-5417's certification record: recurrent_training valid to 2026-09-17, invalid on 2026-09-19 (RULE-CERT-06); licence, medical and DG all valid.
> - Their roster: P-2210 (16 Sep) and P-2213 (19 Sep) — only the 19 Sep duty falls after expiry.
> - Cover ranking over 29 candidates, screened on rating → reserve window → all seven rules; costs from the cost table.
> - Notable exclusions: C-1329, C-2248, C-5418 (on-call 04:00–16:00Z misses the 02:00Z report); several blocked by RULE-REST-04 or RULE-QUAL-05.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> **BLR closure 2026-09-17 08:00–14:00Z — 13 legs, 6 pairings, 1,836 seats exposed.** Ten legs breach RULE-FDP-01 once the reopen delay (+30 min turnaround) is applied, so those tails need re-crewing from reserves or cancellation; three legs can simply be delayed.
> 
> Recovery by pairing:
> - **P-2204 (DX402/403/404)** — worst hit: delays 5.75h/5.0h/2.25h, FDP 17.0 / 16.25 / 13.5 vs 12.0 limit; 162 seats per leg. All three breach → re-crew the whole post-reopen tail or cancel.
> - **P-2211 (DX422/423/424)** — delays 5.75h/5.0h/1.75h, FDP 17.0 / 16.25 / 13.0 vs 12.0; 162 seats per leg. All three breach → same treatment.
> - **P-2218 (DX433/434)** — delays 6.0h/2.75h, FDP 15.75 and 12.5 vs 12.0; 162 seats per leg. Both breach → re-crew.
> - **P-2225 (DX453/454)** — DX453 delayed 6.5h, FDP 14.75 vs 12.0 → breach (72 seats); DX454 at 3.75h delay comes out exactly at the 12.0 limit, legal. Re-crew or cancel DX453, delay DX454.
> - **P-2293 (DX413/DX588)** — DX413 delayed 3.25h, FDP 12.75 vs 12.5 → marginal breach (162 seats); DX588 at 2.25h delay is FDP 11.75, legal. Only DX413 needs a fix.
> - **P-2232 (DX462)** — delay 5.75h, FDP 11.0 vs 13.0 → crew stay legal, pure delay, no crew action.
> 
> Suggested sequencing: protect the two three-leg lines P-2204 and P-2211 with reserve sets first, then P-2218, then the single marginal legs DX453 and DX413. Say the word and I'll rank cover options per pairing and price reserve vs cancellation.
> 
> Reasoning:
> - Station closure impact for BLR on 2026-09-17 08:00–14:00Z: 13 affected flights, 6 pairings, 1,836 passengers; min delay = reopen +30 min turnaround.
> - FDP after delay vs limit and seats per leg from the same result; breaches flagged under RULE-FDP-01 (13h minus 0.5h per sector beyond the 2nd — limits shown as 12.0/12.5/13.0 by sector count).
> - Non-breach legs: DX462, DX454, DX588 — delay only, crew legal.

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Callout drafted for C-3310 (D. Reddy, Captain) on P-2291 (VT-DXC), 2 duty days, ACK due 2026-09-14T18:30Z.
> 
> **CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291**
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> 
> - **Day 1 (2026-09-15):** report 06:00Z at BLR crew room; DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z. Overnight DEL — hotel arranged.
> - **Day 2 (2026-09-16):** report 04:00Z at DEL crew room; DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> 
> Acknowledgement: reply ACK P-2291 by 2026-09-14T18:30Z (30 minutes).
> Contact: Crew Control desk, BLR.
> 
> Reasoning:
> - Roster detail for P-2291: aircraft VT-DXC, report/release and flights per duty day as listed.
> - Crew record for C-3310: D. Reddy, Captain.
> - Draft not committed — say the word and I'll apply the cover (full seven-rule check runs first).

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> **Call out reserve FO C-3316 — ₹18,500, no delay, covers both legs.** That's the FO slot on P-2235 (VT-DXF, DX461/DX462 on 2026-09-20, report 04:00Z), vacated by C-4520. Next best is a day-off callout at ₹24,000 (C-1313); cancelling both legs would be ₹500,000 and strand 144 passengers.
> 
> Reasoning:
> - Pairing lookup: VT-DXF on 2026-09-20 = P-2235, FO C-4520 (R. Sharma), legs DX461/DX462, 144 pax.
> - Cover ranking for the FO slot from 2026-09-20 (reported 03:30Z): 26 candidates; C-3316 is BLR-based, ATR72-rated, on-call 03:00–15:00Z, reachable in 45 min, all seven rules pass (RULE-DUTY-02 headroom 54.8h).
> - 21 candidates excluded on RULE-QUAL-05 (no ATR72 rating), C-3136 on RULE-REST-04.
> - Costs from the cost table as returned in the ranking.
> - Nothing committed — say the word and I'll apply it.

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Three per line, as the standing briefing already surfaces them:
> 
> - **Tightest 7-day duty headroom on the line** — the binding constraint under RULE-DUTY-02; e.g. for tomorrow (2026-09-15) VT-DXA is tightest at 27.83h (C-3988), VT-DXF loosest at 34.90h. Also flags whether all certs on the line are valid (RULE-CERT-06 — all six lines clean tomorrow).
> - **Highest disruption-risk score among the rostered crew** — tells you which line is most likely to need a cover: VT-DXC 0.78 (C-1042, Captain), VT-DXA 0.71, VT-DXB 0.69; VT-DXF only 0.15.
> - **Eligible reserves at that line's report time** — depth of cover if the line breaks: VT-DXC (report 06:00Z) has 9 eligible; VT-DXA/B/D (01:30–02:30Z reports) have only 3 each, VT-DXE 3.
> 
> Reasoning:
> - Morning briefing for 2026-09-15 returns exactly these per aircraft line: pairing and report time, per-crew 7-day duty headroom and cert status, risk scores, and reserves eligible at report.
> - Headroom cites RULE-DUTY-02 (60h/7d); cert flag cites RULE-CERT-06; reserve eligibility is on-call window plus rating and base (RULE-QUAL-05, RULE-BASE-07).
> - Risk score is a provided input on the roster, not a computed figure.
