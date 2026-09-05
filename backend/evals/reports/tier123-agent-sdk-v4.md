# Eval report — agent-sdk

Run: 2026-09-05T07:38:06Z · **35/38** questions with all expected facts recalled · latency p50 8617 ms / p95 21728 ms / max 24513 ms · est. cost $2.81

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 11010 |
| Q02 | 1 | ✅ |  | get_duty_clock | 7179 |
| Q03 | 1 | ✅ |  | list_flights | 6028 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 7961 |
| Q05 | 1 | ✅ |  | get_flight | 6002 |
| Q06 | 1 | ✅ |  | get_crew | 6755 |
| Q07 | 1 | ✅ |  | get_crew | 6892 |
| Q08 | 1 | ✅ |  | get_pairing | 6928 |
| Q09 | 1 | ✅ |  | list_flights | 6641 |
| Q10 | 1 | ✅ |  | list_flights | 8077 |
| Q11 | 1 | ✅ |  | list_crew | 5833 |
| Q12 | 1 | ✅ |  | schedule_stats | 6306 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 7775 |
| Q14 | 1 | ✅ |  | list_routes | 6456 |
| Q15 | 1 | ✅ |  | find_pairings | 6063 |
| Q16 | 1 | ✅ |  | get_risk_signal | 6268 |
| Q17 | 2 | ✅ |  | declare_unavailable, simulate_crew_removal | 9656 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 10070 |
| Q19 | 2 | ✅ |  | station_closure_impact | 9264 |
| Q20 | 2 | ✅ |  | simulate_delay | 12394 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 10679 |
| Q22 | 2 | ✅ |  | find_pairings, get_crew, check_rostered_legality, get_certifications | 21728 |
| Q23 | 2 | ✅ |  | earliest_next_report | 6150 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 10444 |
| Q25 | 2 | ✅ |  | cancellation_impact | 8056 |
| Q26 | 2 | ✅ |  | crew_near_limits | 9158 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage | 17277 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 10536 |
| Q29 | 2 | ✅ |  | station_closure_impact | 8043 |
| Q30 | 2 | ✅ |  | seats_at_risk | 7779 |
| Q31 | 3 | ✅ |  | recommend_cover | 14784 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 22038 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | resolve_delay_options, simulate_delay | 13092 |
| Q34 | 3 | ✅ |  | get_crew, get_certifications, declare_unavailable, recommend_cover | 16203 |
| Q35 | 3 | ❌ | 5, 3.75, 2.75, 2.25, 1.75 | station_closure_impact | 14011 |
| Q36 | 3 | ✅ |  | draft_callout_notification | 10340 |
| Q37 | 3 | ✅ |  | find_pairings, recommend_cover | 12536 |
| Q38 | 3 | ❌ | crew legality headroom (7d duty) for today's rostered crew, risk_signals for tod | morning_briefing | 24513 |

## Q01 — Who is on reserve at BLR on 2026-09-15, and what are their on-call windows?

**Expected:** `[{"crew_id": "C-3305", "rank": "Captain", "window": {"start": "00:00", "end": "05:30"}}, {"crew_id": "C-3310", "rank": "Captain", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3311", "rank": "First Officer", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3312", "rank": "First Officer", "window": {"start": "00:00", "end": "12:00"}}, {"crew_id": "C-3315", "rank": "Capt`

**Answer:**

> 12 reserves at BLR tomorrow (2026-09-15), all active:
> 
> **Flight deck**
> - C-3305 V. Menon — Captain, A320 — 00:00–05:30Z
> - C-3310 D. Reddy — Captain, A320 — 06:00–18:00Z
> - C-3315 M. Pillai — Captain, ATR72 — 03:00–15:00Z
> - C-3311 K. Rao — FO, A320 — 06:00–18:00Z
> - C-3312 P. Sharma — FO, A320 — 00:00–12:00Z
> - C-3316 N. Verma — FO, ATR72 — 03:00–15:00Z
> 
> **Cabin**
> - C-2111 A. Gupta — SCC, A320/ATR72 — 04:00–16:00Z (reachability 90 min)
> - C-3677 M. Iyer — SCC, A320/ATR72 — 04:00–16:00Z
> - C-1329 P. Pillai — CC, A320/ATR72 — 04:00–16:00Z
> - C-2248 H. Reddy — CC, A320/ATR72 — 04:00–16:00Z (60 min)
> - C-4809 M. Das — CC, A320/ATR72 — 00:00–12:00Z
> - C-5418 S. Das — CC, A320/ATR72 — 04:00–16:00Z
> 
> Reachability is 45 min unless noted.
> 
> Reasoning:
> - Reserve roster for BLR on 2026-09-15: 12 reserves, ranks, ratings and on-call windows as listed.
> - A callout is only valid if the required report time falls inside the on-call window; RULE-BASE-07 keeps these BLR-based reserves free of positioning cost for BLR-origin duties.

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 has 20.93 duty hours in the 7 days 2026-09-08 to 2026-09-14, leaving 39.07h headroom under the 60h limit.
> 
> Reasoning:
> - C-1042's duty clock as of 18:00Z: duty 7d = 20.93h, limit 60h, headroom 39.07h (RULE-DUTY-02); contributing days 2026-09-09 (9.99h) and 2026-09-12 (10.94h).
> - Same clock also shows 64.27 block hours in 28 days, 35.73h headroom (RULE-FLT-03).

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> One departure from DEL tomorrow (2026-09-15):
> - DX402 DEL–BLR, off 06:00Z / on 08:45Z, 2.75h block, VT-DXA (A320), 162 seats.
> 
> Reasoning:
> - Flight schedule filtered to DEL departures on 2026-09-15: count 1, total seats 162.

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
> - RULE-CERT-06: certifications must be valid on the duty date — the first three lapse inside the schedule week (2026-09-14 to 2026-09-20), so check their rostered duties after those dates.

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> DX412 on 2026-09-15 (BLR–BOM, 07:00Z–08:45Z) operates on VT-DXC, an A320 with 162 seats.
> 
> Reasoning:
> - Flight schedule for DX412 on 2026-09-15: aircraft VT-DXC, type A320, 162 seats, block 1.75h, pairing P-2291.

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 (D. Reddy, Captain, BLR, A320):
> - On-call window: 06:00–18:00Z, on reserve every day of the week 2026-09-14 to 2026-09-20.
> - Reachability: 45 minutes.
> 
> Reasoning:
> - Reserve roster / crew profile for C-3310: BLR-based reserve, window 06:00–18:00Z, reachability 45 min, no pairings rostered, disruption risk 0.17.
> - A callout is only valid if the required report time falls inside that window (RULE-BASE-07 for base).

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 (S. Kapoor, Captain) is based at DEL and rated on A320.
> 
> Reasoning:
> - Crew record for C-2210: base DEL, ratings [A320], status active.
> - Also a reserve at DEL, on-call 03:00–15:00Z, on reserve all week (2026-09-14 to 2026-09-20), no pairings rostered — relevant under RULE-QUAL-05 and RULE-BASE-07 if considered for cover.

## Q08 — Which crew are assigned to pairing P-2291, and in what roles?

**Expected:** `[{"crew_id": "C-1042", "role": "Captain"}, {"crew_id": "C-1694", "role": "First Officer"}, {"crew_id": "C-3005", "role": "Senior Cabin Crew"}, {"crew_id": "C-4395", "role": "Cabin Crew"}, {"crew_id": "C-4273", "role": "Cabin Crew"}, {"crew_id": "C-1873", "role": "Cabin Crew"}]`

**Answer:**

> P-2291 (VT-DXC, 2026-09-15 to 2026-09-16) is crewed by six:
> 
> - C-1042 A. Nair — Captain
> - C-1694 S. Menon — First Officer
> - C-3005 H. Chandra — Senior Cabin Crew
> - C-4395 V. Rao — Cabin Crew
> - C-4273 P. Menon — Cabin Crew
> - C-1873 K. Joshi — Cabin Crew
> 
> Reasoning:
> - Pairing record P-2291: two duty days (BLR→DEL 2026-09-15, DEL→BLR 2026-09-16), crew list with roles as above.

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> Two BLR→BOM legs on 2026-09-17:
> - DX431 — dep 03:30Z, arr 05:15Z, 1.75h block, VT-DXD (A320), 162 seats
> - DX412 — dep 07:00Z, arr 08:45Z, 1.75h block, VT-DXC (A320), 162 seats
> 
> Reasoning:
> - Flight schedule for 2026-09-17, BLR–BOM: 2 legs, 324 seats total.

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

> One captain is based at DEL:
> - C-2210 — S. Kapoor, A320 rated, active, seniority 2, reachable in 60 min.
> 
> Reasoning:
> - Crew list filtered to base DEL, rank Captain: count 1.

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> Longest block time in the week is 2.75h, flown by DX401, DX402, DX588 and DX589.
> 
> Reasoning:
> - Flight schedule stats for the week 2026-09-14 to 2026-09-20 (147 flights): longest block 2.75h on those four flight numbers; shortest is 1.0h (DX403, DX404, DX453, DX454).

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> C-2087 (R. Iyer) is a Captain, BLR-based, A320-rated. Block hours in the 28 days ending 2026-09-14: 23.5h against the 100h limit — 76.5h headroom.
> 
> Reasoning:
> - Crew profile for C-2087: rank Captain, base BLR, rating A320, active.
> - C-2087's duty clock: flight_hours_28d 23.5 over window 2026-08-18 to 2026-09-14, limit 100h (RULE-FLT-03), headroom 76.5h.
> - Same clock also shows 51.83h duty in the 7 days to 2026-09-14 — 8.17h headroom under RULE-DUTY-02.

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> BLR serves all seven other stations nonstop this week (73 departures total):
> - HYD — 14
> - MAA — 14
> - CCU — 11
> - BOM — 10
> - DEL — 10
> - COK — 7
> - GOI — 7
> 
> Reasoning:
> - Flight schedule, nonstop destinations from BLR across the schedule week (2026-09-14 to 2026-09-20): 7 destinations, counts as listed.

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> C-3171, P. Chandra, on pairing P-2210 (VT-DXB, 2026-09-16).
> 
> Reasoning:
> - Pairing lookup for VT-DXB on 2026-09-16: single pairing P-2210, legs DX421–DX424, Senior Cabin Crew slot held by C-3171.

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

> Three legs on 2026-09-15 lose their Captain immediately — DX412, DX413, DX588 (BLR out, ending DEL), 486 passengers exposed.
> 
> Also at risk on 2026-09-16: DX589, DX590, DX591 (DEL back to BLR) — 972 passengers at risk in total. VT-DXC overnights at DEL, so the cover must take the full remaining pairing.
> 
> Reasoning:
> - C-1042 (A. Nair, Captain) recorded unavailable from 2026-09-15 (sick); P-2291 Captain slot now vacant for both duty days.
> - Removal impact on P-2291: uncovered now DX412/DX413/DX588 on 2026-09-15; later legs DX589/DX590/DX591 on 2026-09-16 at risk.
> - Any replacement must hold the A320 rating (RULE-QUAL-05).

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Not legal — C-2087 (R. Iyer) breaches RULE-DUTY-02 on both duty days of P-2291:
> - 2026-09-15: 61.33h in the 7 days to 15 Sep — over the 60h limit by 1h20m
> - 2026-09-16: 61.08h in the 7 days to 16 Sep — over by 1h05m
> 
> Everything else passes: FDP 9.50h (15th) and 10.75h (16th) against a 12.5h limit for 3 sectors; 37.50h block in 28 days (70.25h/62.50h headroom); rest 12.50h between the two duty days and rest complete 4h before report on the 15th; A320 rated; all 4 certifications valid (licence runs to 2026-09-18); day-off callout from own base BLR. Callout cost would be ₹24,000, but the assignment is refused as it stands.
> 
> Reasoning:
> - Legality check for C-2087 on P-2291 from 2026-09-15, all seven rules, duty days 15–16 Sep.
> - Breaches driven by the daily duty history 09–14 Sep already logged on his duty clock, plus 9.50h and 10.75h from the pairing.
> - This would be a day-off callout, not a reserve callout.

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights across 6 pairings are hit, 1,836 passengers affected; 10 of the 13 breach RULE-FDP-01 after the minimum reopen delay.
> 
> - P-2204: DX402, DX403, DX404 — all breach (max delay 5.75h, 486 seats)
> - P-2211: DX422, DX423, DX424 — all breach (max delay 5.75h, 486 seats)
> - P-2218: DX433, DX434 — both breach (max delay 6.0h, 324 seats)
> - P-2225: DX453 breaches (delay 6.5h); DX454 legal (3.75h)
> - P-2293: DX413 breaches (3.25h); DX588 legal (2.25h)
> - P-2232: DX462 only, crew legal on 5.75h delay
> 
> Reasoning:
> - Station closure impact for BLR 2026-09-17 08:00–14:00Z: 13 affected legs, minimum delay = reopen + 30 min turnaround.
> - FDP after delay vs limit per pairing from the same result; breaching tails need re-crewing from reserves or cancellation (RULE-FDP-01).

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six crew on P-2203 breach RULE-FDP-01 if they fly all four legs: with the 90-minute delay the duty runs 12.75h against a 12.0h limit (4 sectors), release slipping from 12:45Z to 14:15Z. They can legally complete the first three legs only; DX404 needs re-crewing or cancellation.
> 
> - Breaching crew: C-3187 (CP), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (CC)
> - All other rules pass for every one of them (duty 7-day, block 28-day, rest, rating, certifications, base).
> 
> Reasoning:
> - Delay simulation for VT-DXA / DX401 on 2026-09-16, pairing P-2203: FDP 11.25h before, 12.75h after, limit 12.0h at 4 sectors — margin −0.75h (RULE-FDP-01).
> - Legality check on each rostered crew member: single issue is RULE-FDP-01; RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07 all pass.
> - Legal leg count 3; legs needing re-crew: DX404.

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> Yes — legal on all seven rules, but conditional on RULE-BASE-07 deadhead positioning, and it costs a ~3h delay to the first departure.
> 
> - Positioning: DX402 DEL→BLR, arrives 2026-09-15T08:45Z; report slips from 06:00Z to 09:00Z → first departure delayed ~3.0h.
> - Cost ₹41,200 total: callout ₹18,500 + deadhead ₹6,500 + delay ₹16,200.
> 
> Reasoning:
> - Legality check for C-2210 (Capt, DEL, A320) on P-2291 from 2026-09-15: legal=true, no breaches; duty days 15–16 Sep.
> - RULE-FDP-01 pass both days (9.50h and 10.75h vs 12.5h limit, 3 sectors); RULE-DUTY-02 35.31h/60h; RULE-FLT-03 50.15h/100h; RULE-REST-04 12.50h vs 12h minimum — only 0.5h margin between the two duty days; RULE-QUAL-05 A320 rated; RULE-CERT-06 all four certifications valid.
> - RULE-BASE-07 conditional: base DEL ≠ duty start BLR, so positioning is paid — figures above from the check's deadhead plan and cost breakdown.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> No — C-5417 (S. Krishnan, Cabin Crew) cannot legally operate P-2213 on VT-DXB on 2026-09-19. Recurrent training expires 2026-09-17, so RULE-CERT-06 is breached; all six other rules pass.
> 
> Reasoning:
> - Pairing lookup: VT-DXB on 2026-09-19 is P-2213 (4 sectors), C-5417 rostered as Cabin Crew.
> - Legality check on P-2213: RULE-FDP-01 11.25h vs 12.0h limit (4 sectors), RULE-DUTY-02 32.89h/60h, RULE-FLT-03 58.46h/100h, RULE-REST-04 60.75h rest, RULE-QUAL-05 rated A320, RULE-BASE-07 n/a (rostered) — all pass.
> - Certification record: recurrent_training valid to 2026-09-17 → invalid on the duty date (RULE-CERT-06 breach). Their earlier duty P-2210 on 2026-09-16 is unaffected.

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest next report: 2026-09-17T03:30Z.
> 
> Reasoning:
> - Rest calculation on a 15:30Z release on 2026-09-16: minimum rest 12h (RULE-REST-04), giving report no earlier than 03:30Z the next day.

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> No — C-3305 cannot take the full P-2291 (2026-09-15 + 2026-09-16). Two blockers:
> - RULE-DUTY-02 breach on day 2: 68.25h duty in the 7 days ending 2026-09-16, 8h15m over the 60h limit (day 1 alone leaves only 0.50h headroom at 59.50h).
> - Reserve availability: his on-call window is 00:00–05:30Z, which does not cover the 06:00Z report on 2026-09-15.
> 
> Everything else passes: FDP 9.50h/10.75h vs 12.5h for 3 sectors, block 47.60h/100h, rest 12.50h between days, A320 rated, all 4 certifications valid, BLR own-base callout (₹18,500 if it were usable).
> 
> Reasoning:
> - Legality check for C-3305 on P-2291 across both duty days: 7 rules checked, one breach (RULE-DUTY-02) plus availability note from the reserve roster.
> - Pairing record P-2291 (VT-DXC): day 1 BLR→DEL report 06:00Z/release 15:30Z, day 2 DEL→BLR report 04:00Z/release 14:45Z — so the cover must hold both days.

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> DX404 on 2026-09-16 (MAA-BLR): 162 passengers affected, direct cancellation cost INR 250,000.
> 
> Reasoning:
> - Cancellation impact for DX404 on 2026-09-16: passengers_affected 162, cost from the cost table INR 250,000.
> - Pairing P-2203 is released, freeing 6 crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089).

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew are at 45h or more:
> 
> - C-2087 (R. Iyer, Captain) — 51.83h duty in 7d, 8.17h headroom; 23.5h block in 28d
> - C-3305 (V. Menon, Captain) — 50.0h duty in 7d, 10.0h headroom; 33.6h block in 28d
> 
> Neither has planned duty on 2026-09-15 itself.
> 
> Reasoning:
> - Rolling-limit check for the 7 days ending 2026-09-15, threshold 45h, counting history plus rostered duty through that date: 2 crew returned.
> - Limits applied: RULE-DUTY-02 (60h/7d) and RULE-FLT-03 (100h/28d); both remain under limit but C-2087 has the thinnest headroom.

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> **One reserve captain is both in-window and qualified: C-3315 (M. Pillai).** VT-DXE on 2026-09-16 is P-2224, Captain C-3231 (L. Verma), report 03:00Z at BLR.
> 
> - **C-3315** — window 03:00–15:00Z covers the 03:00Z report; ATR72-rated, BLR-based, reachable in 45 min. **Eligible.**
> - **C-3305** — window 00:00–05:30Z does cover 03:00Z, but A320 only, no ATR72 (RULE-QUAL-05). Not eligible.
> - **C-3310** — window 06:00–18:00Z does not cover 03:00Z, and no ATR72 rating. Not eligible.
> - **C-2210** — window 03:00–15:00Z covers, but no ATR72 rating and DEL-based against a BLR start (RULE-BASE-07 deadhead). Not eligible.
> 
> Reasoning:
> - Pairing lookup for VT-DXE on 2026-09-16: P-2224, single duty day, report 03:00Z / release 11:15Z, 4 sectors, BLR–BLR.
> - Reserve roster screened at report 03:00Z for Captain / ATR72 / BLR: 1 eligible, 3 excluded with reasons as listed.
> - Rules applied: RULE-QUAL-05 (rating), RULE-BASE-07 (own base), plus the on-call window test for reserve callout.
> - I have not recorded the sick call or committed a cover — say the word and I'll declare C-3231 unavailable from 2026-09-16 and run full legality/cost on C-3315.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> **No — C-5837 (A. Sharma, Captain) covering P-2291 is not legal.** The two P-2291 duty days themselves check out, but the release at 2026-09-16T14:45Z leaves only 10.75h before their next rostered pairing P-2204 reports at 2026-09-17T01:30Z — a RULE-REST-04 breach (minimum 12h). Note their rostered days include 17 Sep (P-2204), not just 14/17/20 as framed.
> 
> Reasoning:
> - Legality check on C-5837 for P-2291 (day-off callout, from 2026-09-15, duty days 15–16 Sep): 6 of 7 rules pass — RULE-FDP-01 9.50h/10.75h vs 12.5h limit; RULE-DUTY-02 tightest 54.00h vs 60h; RULE-FLT-03 tightest 77.51h vs 100h; RULE-QUAL-05 A320 rated; RULE-CERT-06 all 4 certifications valid; RULE-BASE-07 own base BLR.
> - RULE-REST-04 breach downstream: 10.75h rest, margin −1.25h, between P-2291 release 16 Sep 14:45Z and P-2204 report 17 Sep 01:30Z.
> - Callout cost had it been legal: ₹24,000 from the cost table.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two flights, both on P-2234, 144 passengers exposed — no FDP breaches, delay only.
> 
> - DX461 (arrival HYD 06:30Z) — min delay 3.0h, crew FDP after delay 8.25h vs 13h limit
> - DX462 (departure HYD 07:15Z) — min delay 2.25h, crew FDP after delay 7.5h vs 13h limit
> 
> Reasoning:
> - Closure impact for HYD on 2026-09-19, 05:00–09:00Z: 2 affected legs, 144 seats, pairing P-2234 (max delay 3.0h).
> - Minimum delay = reopen + 30 min turnaround; both crews stay legal under RULE-FDP-01, so action is delay, no re-crewing or cancellation.

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any A320 leg — 162 seats at risk, e.g. DX401. No single leg stands out above the rest: exposure is set by aircraft type, and all 105 A320 legs carry the same 162 seats, versus 72 seats on each of the 42 ATR72 legs. Cancellation cost is INR 250,000 per leg either way.
> 
> Reasoning:
> - Seats-at-risk view of the flight schedule: A320 = 162 seats × 105 legs (example DX401); ATR72 = 72 seats × 42 legs (example DX451).
> - Cost table: cancellation INR 250,000 per flight, flat by leg.

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> **Recommend option 1: reserve callout C-3310 — ₹18,500, no delay, full pairing covered.** P-2291 is a two-day out-and-back (BLR→DEL 15 Sep, DEL→BLR 16 Sep), 6 legs, 972 passengers at risk; the cover must take the whole remaining pairing.
> 
> Ranked options:
> - **1. C-3310 — reserve callout, ₹18,500, 0h delay.** BLR-based, A320-rated, on-call 06:00–18:00Z, reachable 45 min. All seven rules pass; RULE-DUTY-02 headroom 39.8h.
> - **2. C-1526 — day-off callout, ₹24,000, 0h delay.** BLR, A320, reachable 90 min. All rules pass; headroom 10.3h on 2026-09-20.
> - **3. C-3983 — day-off callout, ₹24,000, 0h delay.** BLR, A320, reachable 45 min; headroom 10.1h on 2026-09-16.
> - **4. C-5566 — day-off callout, ₹24,000, 0h delay.** BLR, A320, reachable 60 min; headroom 19.5h on 2026-09-18.
> - **5. C-2210 — reserve + deadhead from DEL, ₹41,200, 3.0h delay** (callout 18,500 + positioning 6,500 + delay 16,200). RULE-BASE-07 positioning required; deadheads on DX402 arr 08:45Z for 09:00Z report.
> - **6. Cancel all 6 legs — ₹1,500,000, 972 passengers stranded.** Last resort.
> 
> Reasoning:
> - Cover ranking for C-1042 on P-2291 from 2026-09-15: required report 06:00Z at BLR, 24 candidates checked, ranked by cost then delay.
> - Uncovered now: DX412/DX413/DX588 on 15 Sep (486 pax); also at risk DX589/DX590/DX591 on 16 Sep — 972 total.
> - Notable exclusions: C-3305 reserve window 00:00–05:30Z misses the 06:00Z report; C-2087 and C-2143 breach RULE-DUTY-02; several breach RULE-REST-04; six captains lack A320 (RULE-QUAL-05).
> - Nothing committed yet — say the word and I'll apply C-3310 and draft the callout.

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> Optimal joint plan — total ₹42,500, no delay, all 8 legs covered legally:
> - **P-2205** (VT-DXA, Capt C-3940 out): **C-3305** — reserve callout, ₹18,500, all legs.
> - **P-2212** (VT-DXB, Capt C-1938 out): **C-1017** — day-off callout, ₹24,000, all legs.
> 
> Reasoning:
> - Pairing lookup for 2026-09-18: VT-DXA = P-2205 (DX401–DX404, Capt C-3940); VT-DXB = P-2212 (DX421–DX424, Capt C-1938).
> - Joint cover plan (both out): cheapest combination with no one assigned twice; total_cost_inr 42,500, 0 delay hours.
> - Both options pass all seven rules (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07); both BLR-based and A320-rated, margins "comfortable".
> - Only one reserve captain (C-3305) fits — reserve C-3310's on-call window 06:00–18:00Z misses the 01:30Z/02:00Z reports, so the second slot must go to a day-off callout (C-1017 cheapest at ₹24,000; C-1042/C-1526/C-2087 equal cost as alternates).
> - Nothing has been committed — say the word and I'll apply both covers.

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> **Recommendation: run P-2203's rostered crew on DX401–DX403 (delayed), and call out a full reserve set for DX404 — ₹75,000, legal.**
> 
> - Breach: delayed duty runs 12.75h vs the 12.0h limit for 4 sectors (RULE-FDP-01); release slips from 12:45Z to 14:15Z. All six rostered crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089) fail only that rule; DX404 is the leg needing re-crew.
> - Reserve set for DX404 (report 11:45Z, FDP 2.50h): CPT C-3310, FO C-3311, SCC C-3677, CC C-1329 / C-4809 / C-5418.
> - Fallback: cancel DX404 — legal but ₹250,000 and 162 passengers stranded.
> 
> Reasoning:
> - Delay assessment for VT-DXA on 2026-09-16 (pairing P-2203, DX401–DX404): FDP 11.25h → 12.75h vs 12.0h limit, 3 legal legs, DX404 to re-crew (RULE-FDP-01).
> - Full seven-rule check on each rostered crew member: only RULE-FDP-01 breaches; duty/block/rest/qual/cert all pass.
> - Ranked delay options: rank 1 prefix + reserve tail ₹75,000; rank 2 cancellation ₹250,000, per the cost table.
> - Nothing committed — say the word and I'll apply the reserve set.

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> **Recommended: call out reserve C-4809 for the Cabin Crew slot on P-2213, 2026-09-19 — ₹9,500, no delay, all four legs covered.**
> 
> - C-5417's recurrent training expires 2026-09-17, so they are illegal on 19 Sep under RULE-CERT-06; recorded unavailable from 2026-09-18. Their 16 Sep pairing P-2210 is unaffected.
> - Vacancy: P-2213 (VT-DXB), DX421/422/423/424 on 2026-09-19, report 02:00Z, 648 passengers exposed.
> - Next best: day-off callouts C-1021 / C-1385 at ₹12,500. Cancelling all four legs would be ₹10,00,000.
> 
> Reasoning:
> - C-5417's certification record: recurrent_training valid to 2026-09-17, invalid on 2026-09-19 (RULE-CERT-06); licence, medical and DG all valid.
> - Cover ranking for the P-2213 Cabin Crew slot: 29 candidates checked against all seven rules; C-4809 is BLR-based, A320-rated, on-call 00:00–12:00Z, reachable in 45 min, RULE-DUTY-02 headroom 48.8h.
> - Excluded per the ranking: reserves C-1329/C-2248/C-5418 (window starts 04:00Z, after the 02:00Z report), several on RULE-REST-04 overlaps, several on RULE-QUAL-05 (no A320).
> 
> Say the word and I'll commit C-4809 and draft the callout.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> BLR closed 08:00–14:00Z on 2026-09-17 hits 13 legs across 6 pairings, 1,836 passengers, with 10 legs breaching RULE-FDP-01 after the minimum reopen delay.
> 
> Recovery plan, worst first:
> - **P-2204 (DX402/403/404)** — 486 seats, all 3 legs breach (FDP 17.0 / 16.25 / 13.5 vs 12.0 limit), max delay 5.75h. Re-crew the whole day from reserves; the rostered crew cannot take any leg after the reopen.
> - **P-2211 (DX422/423/424)** — 486 seats, all 3 legs breach (17.0 / 16.25 / 13.0 vs 12.0), max delay 5.75h. Same treatment: full re-crew or cancel the tail.
> - **P-2218 (DX433/DX434)** — 324 seats, both legs breach (15.75 and 12.5 vs 12.0), max delay 6.0h. Re-crew both legs.
> - **P-2293 (DX413/DX588)** — 324 seats, DX413 breaches (12.75 vs 12.5, delay 3.25h); DX588 stays legal at 11.75. Re-crew DX413 only.
> - **P-2225 (DX453/DX454)** — 144 seats, DX453 breaches (14.75 vs 12.0, delay 6.5h); DX454 is legal at exactly 12.0. Re-crew DX453.
> - **P-2232 (DX462)** — 72 seats, no breach: delay 5.75h, FDP 11.0 vs 13.0. Delay only, crew stays.
> 
> Reasoning:
> - Station closure impact for BLR on 2026-09-17, 08:00–14:00Z: 13 affected legs, passengers_affected 1,836, six pairings listed with per-pairing legs/seats/breach counts.
> - Minimum delay per leg = reopen + 30 min turnaround; FDP after delay compared against RULE-FDP-01 limit (13h minus 0.5h per sector beyond the 2nd) per leg in that result.
> - Legs flagged breach carry the action "re-crew tail legs from reserves or cancel"; DX462, DX454 and DX588 are flagged crew-legal.
> - Next step if you want it: rank reserve cover for the specific breaching pairings, or price the cancel option per leg.

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Callout drafted for C-3310 (D. Reddy, Captain) on P-2291 (VT-DXC), 2 duty days, ack by 2026-09-14T18:30Z.
> 
> **CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291**
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> - Day 1 (2026-09-15): report 06:00Z at BLR crew room; DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z. Overnight at DEL — hotel arranged.
> - Day 2 (2026-09-16): report 04:00Z at DEL crew room; DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> - Acknowledgement deadline 2026-09-14T18:30Z (30 minutes): reply ACK P-2291.
> - Contact: Crew Control desk, BLR.
> 
> Reasoning:
> - Roster detail for P-2291: report/release times, flights per day, DEL overnight with hotel arranged.
> - Crew record for C-3310: D. Reddy, Captain.
> - Draft only — nothing committed to the roster; say the word and I'll apply the cover (runs the seven-rule check first).

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> Cheapest legal cover: reserve callout of **C-3316** for the First Officer slot on P-2235 (VT-DXF, 2026-09-20) — 18,500 INR, no delay, all legs covered.
> 
> - Next best: C-1313 / C-1317 / C-2085 / C-3057 day-off callouts at 24,000 INR each.
> - Last resort: cancelling both legs, 500,000 INR, 144 passengers.
> 
> Reasoning:
> - VT-DXF on 2026-09-20 runs P-2235 (DX461, DX462), FO C-4520 R. Sharma; required report 2026-09-20T04:00Z, 144 passengers exposed.
> - Cover ranking for that FO slot: C-3316 is BLR-based, ATR72-rated, on-call 03:00–15:00Z, reachable in 45 min; all seven rules pass (RULE-FDP-01 … RULE-BASE-07), RULE-DUTY-02 headroom 54.8h.
> - 21 candidates excluded on RULE-QUAL-05 (no ATR72 rating), C-3136 on RULE-REST-04 (overlaps P-2228).
> - Nothing has been recorded on the working scenario — say the word to declare C-4520 out and apply C-3316.

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Three per line, as the standing briefing is built:
> 
> - **Tightest 7-day duty headroom on the line (plus cert validity)** — shows how much room the line has before RULE-DUTY-02 bites, and RULE-CERT-06 flags anyone who can't legally operate. E.g. tomorrow (2026-09-15) VT-DXA is tightest at 27.83h headroom (C-3988); all lines show certs valid.
> - **Highest disruption-risk score among the rostered crew** — one number telling you which line is most likely to need a cover. Tomorrow: VT-DXC 0.78 (C-1042, Captain), VT-DXA 0.71, VT-DXB 0.69; VT-DXF lowest at 0.15.
> - **Eligible reserves at that line's report time** — whether a replacement exists before you need one, filtered by on-call window, rating and base (RULE-QUAL-05, RULE-BASE-07). VT-DXC at 06:00Z has 9 eligible; the early lines (VT-DXA 01:30Z, VT-DXB 02:00Z, VT-DXD 02:30Z) have only 3 each — thinnest cover exactly when risk is high.
> 
> Reasoning:
> - Morning briefing for 2026-09-15, six aircraft lines (VT-DXA…VT-DXF) with pairing, report time, per-crew headroom, cert status, risk score and eligible reserves.
> - The three points pair exposure (risk) with capacity to absorb it (headroom, reserves); the combination that stands out is VT-DXA/VT-DXB — early report, 27.83h and 28.77h tightest headroom, risk 0.71 and 0.69, only 3 reserves in window.
> - Rules referenced: RULE-DUTY-02, RULE-CERT-06, RULE-QUAL-05, RULE-BASE-07.
