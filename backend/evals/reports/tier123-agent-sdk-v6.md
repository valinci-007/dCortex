# Eval report — agent-sdk

Run: 2026-09-05T07:53:49Z · **37/38** questions with all expected facts recalled · latency p50 8447 ms / p95 14996 ms / max 18285 ms · est. cost $2.65

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 11076 |
| Q02 | 1 | ✅ |  | get_duty_clock | 7098 |
| Q03 | 1 | ✅ |  | list_flights | 6317 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 10224 |
| Q05 | 1 | ✅ |  | get_flight | 6370 |
| Q06 | 1 | ✅ |  | get_crew | 7240 |
| Q07 | 1 | ✅ |  | get_crew | 7312 |
| Q08 | 1 | ✅ |  | get_pairing | 6990 |
| Q09 | 1 | ✅ |  | list_flights | 6809 |
| Q10 | 1 | ✅ |  | list_flights | 6090 |
| Q11 | 1 | ✅ |  | list_crew | 6500 |
| Q12 | 1 | ✅ |  | schedule_stats | 6984 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 7372 |
| Q14 | 1 | ✅ |  | list_routes | 6535 |
| Q15 | 1 | ✅ |  | find_pairings | 6913 |
| Q16 | 1 | ✅ |  | get_risk_signal | 6317 |
| Q17 | 2 | ✅ |  | simulate_crew_removal | 8049 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 11643 |
| Q19 | 2 | ✅ |  | station_closure_impact | 12586 |
| Q20 | 2 | ✅ |  | simulate_delay | 10626 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 10894 |
| Q22 | 2 | ✅ |  | find_pairings, get_crew, check_rostered_legality, get_certifications | 13051 |
| Q23 | 2 | ✅ |  | earliest_next_report | 6099 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 11447 |
| Q25 | 2 | ✅ |  | cancellation_impact | 6924 |
| Q26 | 2 | ✅ |  | crew_near_limits | 8086 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage | 14187 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 10707 |
| Q29 | 2 | ✅ |  | station_closure_impact | 8809 |
| Q30 | 2 | ✅ |  | seats_at_risk | 7542 |
| Q31 | 3 | ✅ |  | recommend_cover | 14214 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 16470 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | resolve_delay_options, simulate_delay | 12525 |
| Q34 | 3 | ✅ |  | get_certifications, find_pairings, declare_unavailable, recommend_cover | 18285 |
| Q35 | 3 | ✅ |  | station_closure_impact | 14996 |
| Q36 | 3 | ✅ |  | draft_callout_notification | 9814 |
| Q37 | 3 | ✅ |  | find_pairings, recommend_cover | 13329 |
| Q38 | 3 | ✅ |  | morning_briefing | 13407 |

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
> - C-1329 P. Pillai, CC A320/ATR72 — 04:00–16:00Z
> - C-2248 H. Reddy, CC A320/ATR72 — 04:00–16:00Z
> - C-4809 M. Das, CC A320/ATR72 — 00:00–12:00Z
> - C-5418 S. Das, CC A320/ATR72 — 04:00–16:00Z
> 
> Reasoning:
> - Reserve roster for BLR on 2026-09-15: 12 reserves, ranks, ratings and on-call windows as listed; all on reserve every day of the schedule week.
> - A callout only holds if the required report time falls inside the window, and RULE-BASE-07 keeps these BLR-based reserves cost-free for duties starting at BLR.

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 has 20.93 duty hours in the 7 days 2026-09-08 to 2026-09-14, leaving 39.07h headroom under the 60h limit.
> 
> Reasoning:
> - C-1042's duty clock: duty_hours_7d 20.93 against the RULE-DUTY-02 limit of 60h, headroom 39.07h; window 2026-09-08 to 2026-09-14.
> - Contributing days in that window: 2026-09-09 (9.99h) and 2026-09-12 (10.94h).
> - Same clock also shows 64.27 block hours in 28 days against RULE-FLT-03 (100h), 35.73h headroom.

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> One flight departs DEL tomorrow (2026-09-15):
> - DX402 DEL–BLR, dep 06:00Z / arr 08:45Z, VT-DXA (A320), 162 seats, 2.75 block hours
> 
> Reasoning:
> - Flight schedule for 2026-09-15 filtered on DEL departures: 1 leg, 162 seats total.

## Q04 — List all certifications expiring within 30 days of 2026-09-15.

**Expected:** `[{"crew_id": "C-2087", "cert_type": "licence", "valid_to": "2026-09-18"}, {"crew_id": "C-2091", "cert_type": "medical_class1", "valid_to": "2026-09-23"}, {"crew_id": "C-5417", "cert_type": "recurrent_training", "valid_to": "2026-09-17"}, {"crew_id": "C-3116", "cert_type": "dangerous_goods", "valid_to": "2026-09-28"}, {"crew_id": "C-5020", "cert_type": "recurrent_training", "valid_to": "2026-10-03"`

**Answer:**

> Six certifications expire between 2026-09-15 and 2026-10-15:
> 
> - C-5417 (S. Krishnan, Cabin Crew) — recurrent_training, expires 2026-09-17
> - C-2087 (R. Iyer, Captain) — licence, expires 2026-09-18
> - C-2091 (H. Naidu, Captain) — medical_class1, expires 2026-09-23
> - C-3116 (R. Naidu, First Officer) — dangerous_goods, expires 2026-09-28
> - C-5020 (K. Nair, First Officer) — recurrent_training, expires 2026-10-03
> - C-2993 (I. Kulkarni, First Officer) — medical_class1, expires 2026-10-08
> 
> Reasoning:
> - Certification register, window 2026-09-15 to 2026-10-15: 6 records, soonest first.
> - RULE-CERT-06: any duty rostered after the expiry date is illegal until renewal — the three inside the schedule week (C-5417, C-2087, C-2091) are the near-term exposure.

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> VT-DXC (A320), 162 seats — DX412 BLR–BOM on 2026-09-15, dep 07:00Z / arr 08:45Z, on pairing P-2291.
> 
> Reasoning:
> - Flight schedule for DX412 on 2026-09-15: aircraft VT-DXC, type A320, seats 162, block 1.75h.

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 (D. Reddy, Captain, BLR, A320) is on reserve 06:00–18:00Z, every day of the schedule week (2026-09-14 to 2026-09-20), with reachability 45 minutes.
> 
> Reasoning:
> - Reserve roster: BLR reserve, on-call window 06:00–18:00Z, reserve dates 2026-09-14 through 2026-09-20; no pairings rostered.
> - Crew profile: rank Captain, A320 rating, active, reachability 45 min, disruption risk 0.17 (baseline).
> - A callout is only valid if the required report time falls inside that window (RULE-BASE-07 for base, RULE-QUAL-05 for rating).

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

> P-2291 (VT-DXC, 2026-09-15 to 2026-09-16) carries six crew:
> 
> - C-1042 — Captain — A. Nair
> - C-1694 — First Officer — S. Menon
> - C-3005 — Senior Cabin Crew — H. Chandra
> - C-4395 — Cabin Crew — V. Rao
> - C-4273 — Cabin Crew — P. Menon
> - C-1873 — Cabin Crew — K. Joshi
> 
> Reasoning:
> - Pairing record for P-2291: two duty days, BLR–DEL then DEL–BLR, 3 sectors each day.
> - Crew list and roles as rostered on that pairing.

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> Two BLR→BOM legs on 2026-09-17:
> - DX431 — dep 03:30Z, arr 05:15Z, 1.75h block, VT-DXD (A320), 162 seats
> - DX412 — dep 07:00Z, arr 08:45Z, 1.75h block, VT-DXC (A320), 162 seats
> 
> Reasoning:
> - Flight schedule, BLR→BOM on 2026-09-17: 2 legs, 324 seats total.

## Q10 — How many flights operate on 2026-09-16 in total?

**Expected:** `21`

**Answer:**

> 21 flights operate on 2026-09-16, totalling 2,862 seats across all six aircraft.
> 
> Reasoning:
> - Flight schedule for 2026-09-16: count 21, total seats 2,862, spanning VT-DXA/B/C/D (A320) and VT-DXE/F (ATR72).

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> One Captain is based at DEL:
> - C-2210 — S. Kapoor, A320 rated, active, seniority 2, reachable in 60 min
> 
> Reasoning:
> - Crew list filtered to base DEL, rank Captain: count 1.

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> Longest block time in the week's schedule is 2.75h, flown by four flight numbers:
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

> C-2087 (R. Iyer) is a **Captain**, BLR-based, A320-rated.
> 
> - Block hours in the 28 days ending 2026-09-14 (window 2026-08-18 → 2026-09-14): **23.5h**, against the 100h limit — 76.5h headroom.
> 
> Reasoning:
> - C-2087's crew record: rank Captain, base BLR, rating A320, active.
> - C-2087's duty clock: flight_hours_28d 23.5, limit 100.0 (RULE-FLT-03); note 7-day duty is 51.83h with only 8.17h headroom (RULE-DUTY-02).

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> BLR serves 7 nonstop destinations this week (73 departures total):
> - HYD — 14
> - MAA — 14
> - CCU — 11
> - BOM — 10
> - DEL — 10
> - COK — 7
> - GOI — 7
> 
> Reasoning:
> - Flight schedule, routes from BLR for the schedule week 2026-09-14 to 2026-09-20: 7 destinations, counts as listed.

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> C-3171 (P. Chandra) is the Senior Cabin Crew on VT-DXB's pairing P-2210 on 2026-09-16.
> 
> Reasoning:
> - Pairing lookup for VT-DXB on 2026-09-16: single pairing P-2210, legs DX421–DX424, crew list as rostered.

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042's disruption-risk score is 0.78. Drivers:
> - Short-rest pattern over the last 14 days
> - Two fatigue reports this month
> 
> Reasoning:
> - Risk signal for C-1042 (provided input, as of 18:00Z): score 0.78 with the two drivers listed; it is supplied to the desk, not calculated here.

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Immediately uncrewed on 2026-09-15 (Captain slot, P-2291): DX412, DX413, DX588 — 486 passengers exposed.
> 
> Also at risk on 2026-09-16: DX589, DX590, DX591 — total exposure 972 passengers.
> 
> Reasoning:
> - P-2291 removal impact for C-1042 (A. Nair, Captain), reported 2026-09-15T05:00Z: day 1 BLR→DEL, day 2 DEL→BLR.
> - Multi-day pairing overnighting at DEL, so the cover must take the full remaining pairing.
> - Rating requirement applies to any cover (RULE-QUAL-05).

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Not legal — C-2087 (R. Iyer, Captain, BLR) breaches RULE-DUTY-02 on both duty days of P-2291:
> 
> - 2026-09-15: 61.33h duty in the 7 days to 15 Sep — over the 60h limit by 1h20m
> - 2026-09-16: 61.08h duty in the 7 days to 16 Sep — over by 1h05m
> 
> Everything else passes:
> - RULE-FDP-01: FDP 9.50h (15 Sep) and 10.75h (16 Sep) against a 12.5h limit for 3 sectors
> - RULE-FLT-03: 37.50h block in the 28 days to 16 Sep, headroom 62.50h
> - RULE-REST-04: 12.50h rest between the two duty days (min 12h); pre-duty rest complete 4h before the 06:00Z report on 15 Sep
> - RULE-QUAL-05: rated A320 · RULE-CERT-06: all 4 certifications valid both days (note licence expires 2026-09-18) · RULE-BASE-07: own base BLR, no deadhead
> 
> Cost if it were flown: ₹24,000 day-off callout (not a reserve).
> 
> Reasoning:
> - Legality check of C-2087 against P-2291 from 2026-09-15, all seven rules over both duty days.
> - Duty clock in the check: 09 Sep 11.0h, 10 Sep 10.5h, 11 Sep 8.0h, 12 Sep 12.0h, 13 Sep 6.0h, 14 Sep 4.33h, plus 9.5h on 15 Sep — that is what tips the 7-day window past 60h.
> - Cost from the cost table (day-off callout, pilot).

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights on 2026-09-17, 1,836 passengers affected, across 6 pairings. 10 of the 13 breach RULE-FDP-01 after the minimum delay and need re-crewing or cancellation.
> 
> Breaching legs (min delay → crew FDP vs limit):
> - DX453 dep 08:00Z, P-2225 — 6.5h → 14.75 vs 12.0
> - DX433 dep 08:30Z, P-2218 — 6.0h → 15.75 vs 12.0
> - DX402 arr 08:45Z, P-2204 — 5.75h → 17.0 vs 12.0
> - DX422 arr 08:45Z, P-2211 — 5.75h → 17.0 vs 12.0
> - DX403 dep 09:30Z, P-2204 — 5.0h → 16.25 vs 12.0
> - DX423 dep 09:30Z, P-2211 — 5.0h → 16.25 vs 12.0
> - DX413 arr 11:15Z, P-2293 — 3.25h → 12.75 vs 12.5
> - DX434 arr 11:45Z, P-2218 — 2.75h → 12.5 vs 12.0
> - DX404 arr 12:15Z, P-2204 — 2.25h → 13.5 vs 12.0
> - DX424 arr 12:45Z, P-2211 — 1.75h → 13.0 vs 12.0
> 
> Delayed but crew legal:
> - DX462 arr 08:45Z, P-2232 — 5.75h → 11.0 vs 13.0
> - DX454 arr 10:45Z, P-2225 — 3.75h → 12.0 vs 12.0
> - DX588 dep 12:15Z, P-2293 — 2.25h → 11.75 vs 12.5
> 
> Reasoning:
> - Closure impact for BLR 08:00–14:00Z on 2026-09-17: 13 legs at the station, minimum delay = reopen + 30 min turnaround.
> - Pairings hit: P-2204 (3 legs, 486 seats), P-2211 (3 legs, 486), P-2218 (2 legs, 324), P-2293 (2 legs, 324), P-2225 (2 legs, 144), P-2232 (1 leg, 72).
> - Legality per the rulebook, RULE-FDP-01: FDP after delay vs each duty's limit; breaches need reserve re-crew of the tail legs or cancellation.

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six on P-2203 breach RULE-FDP-01 if they fly all four legs: duty runs 12.75h against a 12.0h limit (4 sectors), 0.75h over. They can legally do the first 3 legs; DX404 needs re-crewing or cancelling.
> 
> - Breaching: C-3187 (Captain), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (Cabin Crew)
> - No other rule fails for anyone — duty 7-day, 28-day block, rest, rating and certifications all pass.
> 
> Reasoning:
> - Delay simulation for VT-DXA on 2026-09-16, 1.5h before DX401: report 01:30Z unchanged, release moves 12:45Z → 14:15Z; FDP 11.25h → 12.75h vs 12.0h limit (RULE-FDP-01, 13h less 0.5h per sector beyond the 2nd, 4 sectors).
> - Legal leg count 3 of 4; DX404 flagged as needing re-crew.
> - Each crew member's checks show RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07 all pass; tightest duty headroom is 26.69h (C-5375).

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> Yes — C-2210 (S. Kapoor, Captain, DEL) is legal on P-2291 from 2026-09-15, conditional on deadhead positioning under RULE-BASE-07. Total cost ₹41,200 (callout ₹18,500 + positioning ₹6,500 + delay ₹16,200).
> 
> Operational consequence: he positions BLR on DX402, arriving 08:45Z, so report shifts from 06:00Z to 09:00Z — the first departure slips about 3 hours, and that delay knocks on through the day's 3 sectors.
> 
> Reasoning:
> - Legality check on C-2210 for P-2291 (duty days 2026-09-15 and 16): all seven rules checked, six pass, RULE-BASE-07 conditional.
> - RULE-FDP-01: 9.50h (15 Sep) and 10.75h (16 Sep) against a 12.5h limit for 3 sectors.
> - RULE-DUTY-02: 35.31h in the 7 days to 16 Sep, headroom 24.69h. RULE-FLT-03: 50.15h block, headroom 49.85h.
> - RULE-REST-04: tightest is 12.50h between the two duty days, 0.5h margin — no room if day 1 releases late.
> - RULE-QUAL-05 A320 rated; RULE-CERT-06 all four certifications valid both days.
> - His reserve on-call window 03:00–15:00Z covers the revised 09:00Z report.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> No — C-5417 (S. Krishnan, Cabin Crew) cannot legally operate P-2213 on VT-DXB on 2026-09-19: recurrent training expires 2026-09-17, so RULE-CERT-06 is breached. All six other rules pass.
> 
> Reasoning:
> - Pairing lookup: VT-DXB on 2026-09-19 is P-2213, C-5417 rostered as Cabin Crew (4 sectors, report 02:00Z, release 13:15Z).
> - Legality re-check on P-2213: RULE-CERT-06 breach — recurrent_training expired 2026-09-17.
> - Certification record: licence, medical class 1 and dangerous goods valid on the date; recurrent training not.
> - Passing: RULE-FDP-01 (11.25h vs 12.0h for 4 sectors), RULE-DUTY-02 (32.89h/60h, 27.11h headroom), RULE-FLT-03 (58.46h/100h), RULE-REST-04 (60.75h after P-2210), RULE-QUAL-05 (A320 rated), RULE-BASE-07 (rostered, BLR).
> - Their 2026-09-16 duty on P-2210 is before the expiry, so it is unaffected.

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest next report: 2026-09-17T03:30Z.
> 
> Reasoning:
> - RULE-REST-04: minimum 12h rest after release at 2026-09-16T15:30Z.

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> No — C-3305 cannot take the full P-2291 (2026-09-15 and 2026-09-16). Two blockers:
> 
> - **RULE-DUTY-02 breach on day 2**: 68.25h duty in the 7 days ending 2026-09-16 — 8h15m over the 60h limit (headroom on day 1 is only 0.50h).
> - **Reserve availability**: their on-call window is 00:00–05:30Z, which does not cover the 06:00Z report on 2026-09-15.
> 
> Everything else passes: FDP 9.50h/10.75h vs 12.5h for 3 sectors, block 47.60h of 100h, rest 12.50h between the two duty days, A320 rated, all 4 certifications valid, callout from own base BLR. Callout cost would have been ₹18,500.
> 
> Reasoning:
> - Legality check for C-3305 on P-2291, all seven rules over both duty days.
> - Pairing record: day 1 BLR→DEL report 06:00Z / release 15:30Z, 3 sectors; day 2 DEL→BLR report 04:00Z / release 14:45Z, 3 sectors.
> - Blocking rules: RULE-DUTY-02 (60h/7d) and the reserve on-call window under the reserve callout terms.
> - If day 1 only is needed, that day alone sits inside the duty limit with 0.50h headroom — but the 06:00Z report is still outside their window.

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> DX404 on 2026-09-16 (MAA–BLR): 162 passengers affected, direct cancellation cost ₹250,000.
> 
> Reasoning:
> - Flight schedule/cancellation impact for DX404 on 2026-09-16: passengers_affected 162, cost from the cost table ₹250,000.
> - Pairing P-2203 is released, freeing crew C-3187, C-5375, C-3211, C-2876, C-1542, C-5089.

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew are at 45h or more for the 7 days ending 2026-09-15:
> 
> - **C-2087** R. Iyer, Captain — 51.83h duty (8.17h headroom); 23.5h block/28d (76.5h headroom)
> - **C-3305** V. Menon, Captain — 50.00h duty (10.0h headroom); 33.6h block/28d (66.4h headroom)
> 
> Reasoning:
> - Rolling-limit check for 2026-09-15 counting history plus rostered duty through that date; both show 0 planned duty hours on 2026-09-15 itself.
> - Limits per the rulebook: RULE-DUTY-02 (60h/7d) and RULE-FLT-03 (100h/28d) — neither is in breach, but both are inside 10h of the duty limit.

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> **One reserve captain covers and qualifies: C-3315 (M. Pillai).** The sick captain is C-3231 (L. Verma) on P-2224, report 03:00Z at BLR on 2026-09-16.
> 
> - C-3315 — BLR, window 03:00–15:00Z covers 03:00Z, ATR72 rated → eligible
> - C-3305 — window 00:00–05:30Z covers report, but A320 only, no ATR72 (RULE-QUAL-05)
> - C-3310 — window 06:00–18:00Z does not cover 03:00Z, and A320 only
> - C-2210 — window 03:00–15:00Z covers, but A320 only and based DEL (RULE-BASE-07 deadhead required)
> 
> Reasoning:
> - VT-DXE on 2026-09-16 is pairing P-2224, single day BLR–BLR, report 03:00Z / release 11:15Z, 4 sectors; Captain slot is C-3231.
> - Reserve roster checked at report time 03:00Z, Captain / ATR72 / BLR: 4 candidates, 1 eligible.
> - Rules applied: RULE-QUAL-05 (rating), RULE-BASE-07 (own base).
> - Note: this is a window/qualification screen only — I have not yet run C-3315's full seven-rule legality check or costed the callout. Say the word and I'll rank cover options.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> **Not legal.** C-5837 (A. Sharma, Captain, BLR) fails RULE-REST-04 on the downstream side: P-2291 releases 2026-09-16T14:45Z and his own P-2204 reports 2026-09-17T01:30Z — only 10.75h rest against the 12h minimum (short by 1.25h). Day-off callout cost would have been ₹24,000.
> 
> Reasoning:
> - Legality check on C-5837 for P-2291 (2026-09-15 to 2026-09-16): six of seven rules pass — FDP 9.50h/10.75h vs 12.5h limit (3 sectors), duty 54.00h vs 60h at the tightest window, block 77.51h vs 100h, A320 rated (RULE-QUAL-05), all 4 certifications valid (RULE-CERT-06), own-base BLR callout (RULE-BASE-07).
> - The only breach is RULE-REST-04 at the 2026-09-17 handover into P-2204; note the in-pairing rest 15→16 Sep is already thin at 12.50h.
> - Fix would require releasing him from P-2204 on 2026-09-17 or covering only 2026-09-15 — say the word and I'll re-check a single-day cover or rank alternatives for the Captain slot.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two flights, both on pairing P-2234, 144 seats exposed — no FDP breaches, both can be delayed with the rostered crew.
> 
> - DX461 (arrival HYD 06:30Z) — min delay 3.0h, crew FDP after delay 8.25h vs 13.0h limit → delay, crew legal
> - DX462 (departure HYD 07:15Z) — min delay 2.25h, crew FDP after delay 7.5h vs 13.0h limit → delay, crew legal
> 
> Reasoning:
> - Closure impact for HYD on 2026-09-19, 05:00–09:00Z: 2 affected legs, both P-2234, 72 seats each, 144 passengers affected.
> - Minimum delays are reopen + 30 min turnaround against the scheduled time at the station.
> - RULE-FDP-01 checked on the delayed duty: 0 breaches, so no re-crewing or cancellation needed.

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any A320 leg — 162 seats at risk, e.g. DX401. There is no single worst leg: exposure is set by aircraft type, and all 105 A320 legs carry the same 162 seats.
> 
> Reasoning:
> - Seats-at-risk view: A320 = 162 seats across 105 legs; ATR72 = 72 seats across 42 legs.
> - Cancellation cost from the cost table: INR 250,000 per leg, regardless of type.
> - So the differentiator is fleet type only — an A320 leg exposes 90 more seats than an ATR72 leg (e.g. DX451).

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> Ranked options to cover the Captain slot on P-2291 (2026-09-15 → 2026-09-16, 6 legs, 972 pax at risk; cover must take the full pairing, report 2026-09-15T06:00Z at BLR):
> 
> - **1. C-3310 — reserve callout — ₹18,500 — no delay** — covers both duty days
> - **2. C-1526 — day-off callout — ₹24,000 — no delay** — covers both duty days
> - **3. C-3983 — day-off callout — ₹24,000 — no delay** — covers both duty days
> - **4. C-5566 — day-off callout — ₹24,000 — no delay** — covers both duty days
> - **5. C-2210 — reserve callout + deadhead from DEL — ₹41,200 — 3.0h delay** — covers both duty days
> - **6. Cancel all 6 legs — ₹15,00,000 — last resort**, 972 passengers stranded
> 
> Recommend rank 1 (C-3310).
> 
> Reasoning:
> - Removal impact: C-1042 (A. Nair, Captain) off P-2291 — DX412/DX413/DX588 on 15 Sep (486 pax) and DX589/DX590/DX591 on 16 Sep; aircraft overnights at DEL, so the cover takes the whole remaining pairing.
> - 24 candidates checked against all seven rules over their full timelines; ranked by cost, then delay.
> - C-3310: BLR-based, A320-rated, on-call 06:00–18:00Z, reachable in 45 min; RULE-DUTY-02 headroom 39.8h on 16 Sep — comfortable margin.
> - C-2210 costs more under RULE-BASE-07 (base DEL ≠ BLR): ₹18,500 callout + ₹6,500 positioning + ₹16,200 delay, deadheading on DX402 arriving 08:45Z against a 09:00Z report.
> - Main exclusions: no A320 rating (RULE-QUAL-05) for C-1600, C-1671, C-2091, C-2221, C-3231, C-3315, C-3721, C-5392; rest/overlap conflicts (RULE-REST-04) for C-1017, C-1443, C-1938, C-3187, C-3940, C-5647, C-5820, C-5837; 60h/7d breaches (RULE-DUTY-02) for C-2087 and C-2143; C-3305's on-call window 00:00–05:30Z misses the 06:00Z report.

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> **Optimal joint plan — total ₹42,500, no delay, all legs covered, no one assigned twice:**
> - P-2205 (VT-DXA, C-3940 out): **C-3305** — reserve callout, ₹18,500, 0h delay, all legs
> - P-2212 (VT-DXB, C-1938 out): **C-1017** — day-off callout, ₹24,000, 0h delay, all legs
> 
> Ranked alternates for either slot (same list both pairings, all legal, 0h delay, all legs):
> 1. C-3305 — reserve callout, ₹18,500
> 2. C-1017 — day-off callout, ₹24,000
> 3. C-1042 — day-off callout, ₹24,000
> 4. C-1526 — day-off callout, ₹24,000
> 5. C-2087 — day-off callout, ₹24,000
> 6. C-2143 — day-off callout, ₹24,000 (RULE-REST-04 headroom only 0.2h on P-2205 / 0.8h on P-2212 — tight)
> 
> Reasoning:
> - Rosters for 2026-09-18: P-2205 (VT-DXA, DX401–DX404, Captain C-3940) and P-2212 (VT-DXB, DX421–DX424, Captain C-1938).
> - Joint cover ranking: cheapest combination is the single BLR reserve captain C-3305 (on-call 00:00–05:30Z, covers report 01:30Z, reachable 45 min) on one pairing, then the cheapest day-off callout on the other; C-3305 can only be used once.
> - All options checked against all seven rules (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07); margins comfortable except C-2143 on rest.
> - Excluded: C-3310 (reserve window 06:00–18:00Z doesn't cover the 01:30Z/02:00Z report), C-5566 and C-1443 (RULE-REST-04), and C-1600, C-1671, C-2091, C-2221, C-3231, C-3315, C-3721, C-5392 (RULE-QUAL-05, no A320 rating).
> - Nothing has been recorded — say the word and I'll declare both captains unavailable and commit the two covers.

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> VT-DXA / P-2203 on 2026-09-16: the 90-min delay pushes the duty to 12.75h against a 12.0h limit for 4 sectors (RULE-FDP-01) — the rostered crew can legally fly DX401–DX403 only; DX404 needs re-crewing.
> 
> Ranked options:
> - **1 — Rostered crew operate DX401–DX403 (delayed); full reserve set takes DX404** — legal, ₹75,000, no cancellation. Reserves: CPT C-3310, FO C-3311, SCC C-3677, CC C-1329 / C-4809 / C-5418 (report 11:45Z, FDP 2.50h).
> - **2 — Cancel DX404** — legal, ₹250,000, 162 passengers stranded.
> 
> Recommend option 1.
> 
> Reasoning:
> - Delay assessment for VT-DXA on 2026-09-16: report 01:30Z, release moves 12:45Z → 14:15Z; FDP 11.25h → 12.75h vs 12.0h limit (4 sectors) — breach of RULE-FDP-01, legal leg count 3, DX404 needs re-crew.
> - All six rostered crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089) fail only on RULE-FDP-01; RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07 all pass.
> - Option 1: the 3-leg delayed duty runs 11.0h vs 12.5h limit — legal; reserve set's callout windows and 12h rest satisfied (RULE-REST-04, RULE-BASE-07).
> - Costs from the cost table: ₹75,000 reserve callouts vs ₹250,000 cancellation.

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> C-5417's recurrent training expired 2026-09-17, so they are illegal for P-2213 on 2026-09-19 (RULE-CERT-06). I've recorded them unavailable from 2026-09-18; their Cabin Crew slot on P-2213 (VT-DXB, DX421/422/423/424, report 02:00Z, 648 pax) is vacant. Ranked legal covers:
> 
> - 1. C-4809 — reserve callout — ₹9,500 — 0h delay — all legs
> - 2. C-1021 — day-off callout — ₹12,500 — 0h delay — all legs
> - 3. C-1385 — day-off callout — ₹12,500 — 0h delay — all legs
> - 4. C-1414 — day-off callout — ₹12,500 — 0h delay — all legs
> - 5. C-1569 — day-off callout — ₹12,500 — 0h delay — all legs
> - 6. C-1748 — day-off callout — ₹12,500 — 0h delay — all legs
> - 7. C-1873 — day-off callout — ₹12,500 — 0h delay — all legs
> - 8. C-1970 — day-off callout — ₹12,500 — 0h delay — all legs
> - 9. Cancel all 4 legs — ₹1,000,000 — 648 passengers stranded (last resort)
> 
> Recommended: C-4809. Say the word and I'll apply it.
> 
> Reasoning:
> - C-5417's certification record: recurrent_training valid to 2026-09-17, not valid on 2026-09-19; licence, medical and DG all valid — RULE-CERT-06 fails only on training.
> - Roster: C-5417 is Cabin Crew on P-2213 (2026-09-19), four legs on VT-DXB, 648 passengers exposed.
> - Cover ranking over 29 candidates, all seven rules checked; C-4809 is BLR-based, A320-rated, on-call 00:00–12:00Z covering the 02:00Z report, reachable in 45 min, RULE-DUTY-02 headroom 48.8h.
> - Notable exclusions: C-1329, C-2248, C-5418 (reserve windows start 04:00Z, after report); several on RULE-QUAL-05 (no A320) or RULE-REST-04.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> BLR closure 08:00–14:00Z on 2026-09-17 hits 13 legs across 6 pairings, 1,836 passengers exposed; 10 legs breach RULE-FDP-01 after the minimum reopen delay, so those tails need re-crewing or cancellation.
> 
> Per pairing (min delay → FDP after delay vs limit):
> - **P-2204** (3 legs, 486 seats, 3 breaches): DX402 +5.75h → 17.0 vs 12.0; DX403 +5.0h → 16.25; DX404 +2.25h → 13.5. All three breach — re-crew the whole day from reserves or cancel.
> - **P-2211** (3 legs, 486 seats, 3 breaches): DX422 +5.75h → 17.0; DX423 +5.0h → 16.25; DX424 +1.75h → 13.0. Same picture as P-2204.
> - **P-2218** (2 legs, 324 seats, 2 breaches): DX433 +6.0h → 15.75 vs 12.0; DX434 +2.75h → 12.5.
> - **P-2293** (2 legs, 324 seats, 1 breach): DX413 +3.25h → 12.75 vs 12.5 (breach); DX588 +2.25h → 11.75, crew legal.
> - **P-2225** (2 legs, 144 seats, 1 breach): DX453 +6.5h → 14.75 vs 12.0 (breach); DX454 +3.75h → 12.0, at the limit but legal.
> - **P-2232** (1 leg, 72 seats, 0 breaches): DX462 +5.75h → 11.0 vs 13.0 — delay only, no crew action.
> 
> Suggested sequencing: P-2232 and DX588 absorb the delay as-is; P-2225 and P-2293 need only their first breaching leg re-crewed; P-2204, P-2211 and P-2218 are full re-crew or cancellation candidates and carry the largest seat exposure (486/486/324). Say the word and I'll rank reserve options leg by leg, or price the cancellations.
> 
> Reasoning:
> - Station closure impact for BLR on 2026-09-17, 08:00–14:00Z: 13 flights, 6 pairings, passengers_affected 1,836; minimum delay = reopen + 30 min turnaround.
> - FDP after delay vs limit per leg from the same result; RULE-FDP-01 breaches flagged on DX453, DX433, DX402, DX422, DX403, DX423, DX413, DX434, DX404, DX424.
> - Per-pairing legs/seats/breach counts quoted as returned; no cover options or costs looked up yet.

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Callout drafted for C-3310 (D. Reddy, Captain) on P-2291 (VT-DXC), ack by 2026-09-14T18:30Z.
> 
> **CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291**
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> - Day 1 (2026-09-15): report 06:00Z at BLR crew room; flights DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z. Overnight at DEL — hotel arranged.
> - Day 2 (2026-09-16): report 04:00Z at DEL crew room; flights DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> - Acknowledgement: reply ACK P-2291 by 2026-09-14T18:30Z (30 minutes).
> - Contact: Crew Control desk, BLR.
> 
> Reasoning:
> - Report/release times, flights, overnight station and hotel taken from the P-2291 roster detail for both duty days.
> - Crew record: C-3310 is D. Reddy, Captain; pairing operates VT-DXC.
> - Nothing committed yet — say the word and I'll apply the cover (full seven-rule check runs first).

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> **Cheapest legal cover: reserve C-3316 at ₹18,500, no delay.** The out FO is C-4520 on P-2235 (DX461/DX462, 144 pax, report 04:00Z).
> 
> Ranked options:
> - 1. C-3316 — reserve callout — ₹18,500 — 0h delay — all legs
> - 2. C-1313 — day-off callout — ₹24,000 — 0h delay — all legs
> - 3. C-1317 — day-off callout — ₹24,000 — 0h delay — all legs
> - 4. C-2085 — day-off callout — ₹24,000 — 0h delay — all legs
> - 5. C-3057 — day-off callout — ₹24,000 — 0h delay — all legs
> - 6. Cancel both legs — ₹500,000 — 144 passengers stranded
> 
> Reasoning:
> - Pairing lookup: VT-DXF on 2026-09-20 runs P-2235, FO slot held by C-4520 (R. Sharma).
> - Cover ranking over 26 candidates: C-3316 is BLR-based, ATR72-rated, on call 03:00–15:00Z, reachable in 45 min; all seven rules pass (RULE-FDP-01 … RULE-BASE-07), RULE-DUTY-02 headroom 54.8h.
> - 21 candidates excluded on RULE-QUAL-05 (no ATR72 rating); C-3136 excluded on RULE-REST-04 (overlaps P-2228).
> - Nothing committed — say the word and I'll apply C-3316 and draft the callout.

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Three per aircraft line, exactly what the standing briefing surfaces:
> 
> - **Tightest 7-day duty headroom on the line** (with certification status alongside it) — the binding legality margin. Tomorrow (2026-09-15): VT-DXA 27.83h, VT-DXB 28.77h, VT-DXC 29.29h, VT-DXD 30.74h, VT-DXE 30.79h, VT-DXF 34.90h; all certs valid on every line.
> - **Highest disruption-risk score on the line** — where a sick call is most likely. VT-DXC 0.78 (C-1042), VT-DXA 0.71 (C-3940), VT-DXB 0.69 (C-1938); the rest 0.31 or lower.
> - **Reserves eligible at that line's report time** — the cover depth if it breaks. VT-DXC (report 06:00Z) has 9 eligible; VT-DXA/B/D (01:30–02:30Z) only 3 each; VT-DXE 3, VT-DXF 8.
> 
> Reasoning:
> - Briefing for 2026-09-15 returns one line per aircraft with pairing, report time and flights, plus these three as its surfaced data points.
> - Headroom is against RULE-DUTY-02 (60h/7d) and cert validity against RULE-CERT-06 — together they say whether the rostered crew can legally fly the day.
> - Risk score is a provided input, not computed here; it flags exposure before it happens.
> - Eligible reserves are filtered by on-call window, rating (RULE-QUAL-05) and base (RULE-BASE-07) at the line's report time — the early lines are thinnest, so VT-DXA's combination of tightest headroom, 0.71 risk and only 3 reserves at 01:30Z is the one to watch.
