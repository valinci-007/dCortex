# Eval report — agent-sdk

Run: 2026-09-04T14:16:02Z · **28/30** questions with all expected facts recalled · latency p50 8162 ms / p95 14536 ms / max 18278 ms · est. cost $1.71

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 11724 |
| Q02 | 1 | ✅ |  | get_duty_clock | 7624 |
| Q03 | 1 | ✅ |  | list_flights | 6281 |
| Q04 | 1 | ❌ | medical_class1, recurrent_training, dangerous_goods | list_expiring_certifications | 8284 |
| Q05 | 1 | ✅ |  | get_flight | 6711 |
| Q06 | 1 | ✅ |  | get_crew | 7381 |
| Q07 | 1 | ✅ |  | get_crew | 6651 |
| Q08 | 1 | ✅ |  | get_pairing | 13626 |
| Q09 | 1 | ✅ |  | list_flights | 6776 |
| Q10 | 1 | ✅ |  | list_flights | 6823 |
| Q11 | 1 | ✅ |  | list_crew | 6020 |
| Q12 | 1 | ✅ |  | schedule_stats | 6254 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 8179 |
| Q14 | 1 | ✅ |  | list_routes | 6914 |
| Q15 | 1 | ✅ |  | find_pairings | 6587 |
| Q16 | 1 | ✅ |  | get_risk_signal | 6385 |
| Q17 | 2 | ✅ |  | simulate_crew_removal | 14536 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 11545 |
| Q19 | 2 | ✅ |  | station_closure_impact | 11462 |
| Q20 | 2 | ✅ |  | simulate_delay | 10551 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 14204 |
| Q22 | 2 | ✅ |  | find_pairings, check_rostered_legality | 9586 |
| Q23 | 2 | ❌ | 2026-09-17T03:30:00Z | earliest_next_report | 13587 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 10868 |
| Q25 | 2 | ✅ |  | cancellation_impact | 7244 |
| Q26 | 2 | ✅ |  | crew_near_limits | 8229 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage | 14090 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 18278 |
| Q29 | 2 | ✅ |  | station_closure_impact | 8146 |
| Q30 | 2 | ✅ |  | seats_at_risk | 7577 |

## Q01 — Who is on reserve at BLR on 2026-09-15, and what are their on-call windows?

**Expected:** `[{"crew_id": "C-3305", "rank": "Captain", "window": {"start": "00:00", "end": "05:30"}}, {"crew_id": "C-3310", "rank": "Captain", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3311", "rank": "First Officer", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3312", "rank": "First Officer", "window": {"start": "00:00", "end": "12:00"}}, {"crew_id": "C-3315", "rank": "Capt`

**Answer:**

> 12 reserves at BLR tomorrow (2026-09-15), all active:
> 
> Flight deck
> - C-3305 V. Menon, Captain, A320 — 00:00–05:30Z (45 min)
> - C-3310 D. Reddy, Captain, A320 — 06:00–18:00Z (45 min)
> - C-3315 M. Pillai, Captain, ATR72 — 03:00–15:00Z (45 min)
> - C-3311 K. Rao, First Officer, A320 — 06:00–18:00Z (45 min)
> - C-3312 P. Sharma, First Officer, A320 — 00:00–12:00Z (60 min)
> - C-3316 N. Verma, First Officer, ATR72 — 03:00–15:00Z (45 min)
> 
> Cabin
> - C-2111 A. Gupta, Senior Cabin Crew, A320/ATR72 — 04:00–16:00Z (90 min)
> - C-3677 M. Iyer, Senior Cabin Crew, A320/ATR72 — 04:00–16:00Z (45 min)
> - C-1329 P. Pillai, Cabin Crew, A320/ATR72 — 04:00–16:00Z (45 min)
> - C-2248 H. Reddy, Cabin Crew, A320/ATR72 — 04:00–16:00Z (60 min)
> - C-4809 M. Das, Cabin Crew, A320/ATR72 — 00:00–12:00Z (45 min)
> - C-5418 S. Das, Cabin Crew, A320/ATR72 — 04:00–16:00Z (45 min)
> 
> Reasoning:
> - Reserve roster for BLR on 2026-09-15: 12 reserves, ranks, ratings, on-call windows and reachability as listed; all on reserve every day of the week.
> - A reserve can only be called out if the required report time falls inside their on-call window; base is BLR, so no positioning needed under RULE-BASE-07. Rating must match the type (RULE-QUAL-05).

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 has 20.93 duty hours in the 7 days 2026-09-08 to 2026-09-14, leaving 39.07h headroom under the 60h limit.
> 
> Reasoning:
> - C-1042's duty clock: 20.93h duty in the 7-day window (2026-09-08 → 2026-09-14), from duty days 2026-09-09 (9.99h) and 2026-09-12 (10.94h).
> - RULE-DUTY-02 limit 60h in any 7 calendar days → headroom 39.07h.
> - Same clock also shows 64.27 block hours in the 28 days to 2026-09-14 (RULE-FLT-03), 35.73h headroom.

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> One flight departs DEL on 2026-09-15:
> - DX402 DEL–BLR, dep 06:00Z / arr 08:45Z, VT-DXA (A320), 162 seats, 2.75 block hours
> 
> Reasoning:
> - Flight schedule filtered to departures from DEL on 2026-09-15: 1 leg returned.

## Q04 — List all certifications expiring within 30 days of 2026-09-15.

**Expected:** `[{"crew_id": "C-2087", "cert_type": "licence", "valid_to": "2026-09-18"}, {"crew_id": "C-2091", "cert_type": "medical_class1", "valid_to": "2026-09-23"}, {"crew_id": "C-5417", "cert_type": "recurrent_training", "valid_to": "2026-09-17"}, {"crew_id": "C-3116", "cert_type": "dangerous_goods", "valid_to": "2026-09-28"}, {"crew_id": "C-5020", "cert_type": "recurrent_training", "valid_to": "2026-10-03"`

**Answer:**

> Six certifications expire between 2026-09-15 and 2026-10-15:
> 
> - C-5417 S. Krishnan (Cabin Crew) — recurrent training, expires 2026-09-17
> - C-2087 R. Iyer (Captain) — licence, expires 2026-09-18
> - C-2091 H. Naidu (Captain) — medical class 1, expires 2026-09-23
> - C-3116 R. Naidu (First Officer) — dangerous goods, expires 2026-09-28
> - C-5020 K. Nair (First Officer) — recurrent training, expires 2026-10-03
> - C-2993 I. Kulkarni (First Officer) — medical class 1, expires 2026-10-08
> 
> Reasoning:
> - Certification expiry list, window 2026-09-15 to 2026-10-15: 6 records, soonest first.
> - RULE-CERT-06: certifications must be valid on the duty date — the two Captains (C-2087, C-2091) and C-5417 lapse inside the schedule week's near horizon, so rostered duties on/after those dates need re-checking.

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> VT-DXC (A320), 162 seats — DX412 BLR-BOM on 2026-09-15, dep 07:00Z / arr 08:45Z.
> 
> Reasoning:
> - Flight schedule for DX412 on 2026-09-15: aircraft VT-DXC, type A320, 162 seats, block 1.75h.
> - Operated under pairing P-2291.

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 (D. Reddy, Captain, BLR, A320):
> - On-call window 06:00–18:00Z, on reserve every day of the schedule week (2026-09-14 to 2026-09-20)
> - Reachability 45 minutes
> 
> Reasoning:
> - Reserve roster / crew profile for C-3310: base BLR, active, A320 rating, seniority 9, disruption risk 0.17, no pairings rostered.
> - A callout is only valid if the required report time falls inside the 06:00–18:00Z window (RULE-BASE-07 applies for base BLR).

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 (S. Kapoor, Captain) is based at DEL and rated on A320 only.
> 
> Reasoning:
> - Crew profile for C-2210: base DEL, ratings [A320], active, reserve with on-call window 03:00–15:00Z.
> - Rating matters for RULE-QUAL-05; base for RULE-BASE-07 (deadhead pay if used away from DEL).

## Q08 — Which crew are assigned to pairing P-2291, and in what roles?

**Expected:** `[{"crew_id": "C-1042", "role": "Captain"}, {"crew_id": "C-1694", "role": "First Officer"}, {"crew_id": "C-3005", "role": "Senior Cabin Crew"}, {"crew_id": "C-4395", "role": "Cabin Crew"}, {"crew_id": "C-4273", "role": "Cabin Crew"}, {"crew_id": "C-1873", "role": "Cabin Crew"}]`

**Answer:**

> P-2291 (VT-DXC, duty days 2026-09-15 and 2026-09-16) is crewed by six:
> 
> - C-1042 A. Nair — Captain
> - C-1694 S. Menon — First Officer
> - C-3005 H. Chandra — Senior Cabin Crew
> - C-4395 V. Rao — Cabin Crew
> - C-4273 P. Menon — Cabin Crew
> - C-1873 K. Joshi — Cabin Crew
> 
> Reasoning:
> - Pairing record P-2291: day 1 starts BLR and ends DEL (3 sectors), day 2 starts DEL and ends BLR (3 sectors).
> - Crew list and roles as rostered on that pairing.

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> Two legs on 2026-09-17:
> - DX431 — 03:30Z BLR / 05:15Z BOM, VT-DXD (A320), 162 seats, 1.75h block
> - DX412 — 07:00Z BLR / 08:45Z BOM, VT-DXC (A320), 162 seats, 1.75h block
> 
> Reasoning:
> - Flight schedule, BLR→BOM on 2026-09-17: 2 legs, 324 seats total.

## Q10 — How many flights operate on 2026-09-16 in total?

**Expected:** `21`

**Answer:**

> 21 flights operate on 2026-09-16, across all six aircraft, totalling 2,862 seats.
> 
> Reasoning:
> - Flight schedule for 2026-09-16: 21 legs (DX401–DX404, DX421–DX424, DX431–DX434, DX451–DX454, DX461/462, DX589–DX591).
> - Lines flown by VT-DXA/B/C/D (A320) and VT-DXE/F (ATR72).

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> One captain is based at DEL:
> - C-2210 S. Kapoor — A320 rated, active, seniority 2, reachable in 60 min.
> 
> Reasoning:
> - Crew list filtered to base DEL, rank Captain: count 1.

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> Longest block time in the schedule is 2.75 h, flown by DX401, DX402, DX588 and DX589.
> 
> Reasoning:
> - Flight schedule stats for the week 2026-09-14 to 2026-09-20 (147 legs): longest block 2.75 h on those four flight numbers; shortest is 1.0 h (DX403/DX404/DX453/DX454).

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> - C-2087 (R. Iyer): Captain, based BLR, A320-rated.
> - Block hours in the 28 days ending 2026-09-14 (window 2026-08-18 to 2026-09-14): 23.5h, against the 100h limit — 76.5h headroom.
> 
> Reasoning:
> - Crew profile for C-2087: rank Captain, base BLR, rating A320, status active.
> - C-2087's duty clock: 28-day block total 23.5h vs RULE-FLT-03 limit 100h; 7-day duty 51.83h vs RULE-DUTY-02 limit 60h (8.17h headroom).

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> BLR serves all seven other stations nonstop this week (73 departures total):
> - HYD 14, MAA 14, CCU 11, BOM 10, DEL 10, COK 7, GOI 7
> 
> Reasoning:
> - Flight schedule, nonstop destinations from BLR for the week 2026-09-14 to 2026-09-20, with per-destination departure counts.

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> P. Chandra (C-3171) is the Senior Cabin Crew on VT-DXB's pairing P-2210 on 2026-09-16.
> 
> Reasoning:
> - Pairing lookup for VT-DXB on 2026-09-16: one pairing, P-2210, four legs DX421–DX424.
> - Crew list on P-2210 shows C-3171 in the Senior Cabin Crew role.

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042's disruption-risk score is 0.78, driven by:
> - short-rest pattern over the last 14 days
> - two fatigue reports this month
> 
> Reasoning:
> - Risk signal for C-1042 (provided input, as of 18:00Z): score 0.78 with the two drivers listed.

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Immediately uncrewed on 2026-09-15 (Captain slot, P-2291, BLR→…→DEL): DX412, DX413, DX588 — 486 passengers exposed.
> 
> Also at risk on 2026-09-16 (day 2, DEL→…→BLR): DX589, DX590, DX591 — a further 486 pax, 972 total. The pairing overnights away from base, so any cover must take the full remaining pairing.
> 
> Reasoning:
> - Removal impact for C-1042 (A. Nair, Captain) on P-2291 from 2026-09-15: day 1 legs DX412/DX413/DX588, day 2 legs DX589/DX590/DX591.
> - Multi-day pairing ending back at BLR on 2026-09-16; cover must be qualified on type (RULE-QUAL-05).

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Yes — not legal. C-2087 (R. Iyer) breaches RULE-DUTY-02 on both duty days of P-2291:
> - 2026-09-15: 61.33h in the 7-day window (2026-09-09 to 09-15) — over the 60h limit by 1h20m
> - 2026-09-16: 61.08h in the window (2026-09-10 to 09-16) — over by 1h05m
> 
> Everything else passes: FDP 9.50h (15th) and 10.75h (16th) against a 12.5h limit for 3 sectors (RULE-FDP-01); 37.50h block in 28 days, 62.50h headroom (RULE-FLT-03); 12.50h rest between the two duty days, minimum 12h (RULE-REST-04); A320 rated (RULE-QUAL-05); all 4 certifications valid both days (RULE-CERT-06 — note licence expires 2026-09-18); day-off callout from own base BLR, no deadhead (RULE-BASE-07). Callout cost would be INR 24,000.
> 
> Reasoning:
> - Legality check of C-2087 against P-2291 from 2026-09-15, all seven rules over both duty days.
> - Duty clock daily history in the check: 09-09 11.0h, 09-10 10.5h, 09-11 8.0h, 09-12 12.0h, 09-13 6.0h, 09-14 4.33h, plus the pairing's 9.5h on 09-15 and 10.75h on 09-16.
> - Cost from the cost table: day-off callout, pilot.

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights across 6 pairings, 1,836 passengers exposed; 10 of the 13 breach RULE-FDP-01 after the minimum reopen delay.
> 
> Breaching (re-crew tail legs from reserves or cancel):
> - DX453 (P-2225, dep 08:00Z, +6.5h, FDP 14.75 vs 12.0)
> - DX433 (P-2218, dep 08:30Z, +6.0h, 15.75 vs 12.0)
> - DX402 (P-2204, arr 08:45Z, +5.75h, 17.0 vs 12.0)
> - DX422 (P-2211, arr 08:45Z, +5.75h, 17.0 vs 12.0)
> - DX403 (P-2204, dep 09:30Z, +5.0h, 16.25 vs 12.0)
> - DX423 (P-2211, dep 09:30Z, +5.0h, 16.25 vs 12.0)
> - DX413 (P-2293, arr 11:15Z, +3.25h, 12.75 vs 12.5)
> - DX434 (P-2218, arr 11:45Z, +2.75h, 12.5 vs 12.0)
> - DX404 (P-2204, arr 12:15Z, +2.25h, 13.5 vs 12.0)
> - DX424 (P-2211, arr 12:45Z, +1.75h, 13.0 vs 12.0)
> 
> Delay only, crew legal: DX462 (P-2232, +5.75h), DX454 (P-2225, +3.75h), DX588 (P-2293, +2.25h).
> 
> Reasoning:
> - Closure impact for BLR 2026-09-17 08:00–14:00Z: 13 legs touching BLR, minimum delay = reopen + 30 min turnaround.
> - Pairings affected: P-2204, P-2211, P-2218, P-2225, P-2232, P-2293.
> - FDP after delay compared against each duty's RULE-FDP-01 limit (12.0–13.0h depending on sectors).

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six crew on P-2203 breach RULE-FDP-01 if they fly all four legs: the delayed duty runs 12.75h against a 12.0h limit (4 sectors), 0.75h over.
> 
> - Legal for the first 3 legs (DX401, DX402, DX403); DX404 needs re-crewing or cancelling.
> - Affected: C-3187 (Capt), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (CC).
> - No other limit is touched — 7-day duty, 28-day block, rest, rating and certifications all pass for every crew member.
> 
> Reasoning:
> - Delay simulation for VT-DXA on 2026-09-16, 1.5h before DX401: report 01:30Z unchanged, release moves 12:45Z → 14:15Z; FDP 11.25h → 12.75h vs 12.0h limit (RULE-FDP-01).
> - Full seven-rule check on each rostered crew member of P-2203: only RULE-FDP-01 in breach; RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07 all pass.
> - Legal leg count from the same check: 3 of 4.

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> Yes — C-2210 (S. Kapoor, Captain) is legal on P-2291 from 2026-09-15, conditional on RULE-BASE-07 deadhead positioning from DEL to BLR.
> 
> Operational consequence:
> - Positions on DX402, arriving BLR 08:45Z; report slips from 06:00Z to 09:00Z → first departure delayed ~3h.
> - Total cost INR 41,200 = callout 18,500 + deadhead positioning 6,500 + delay 16,200.
> - Tightest margins on the pairing: RULE-REST-04 12.50h vs 12h minimum between the 15th and 16th duties; FDP 10.75h vs 12.5h limit on 2026-09-16.
> 
> Reasoning:
> - Legality check for C-2210 on P-2291 from 2026-09-15 (duty days 15–16 Sep): all seven rules checked — RULE-FDP-01 pass (9.50h/12.5h on the 15th, 10.75h/12.5h on the 16th, 3 sectors each), RULE-DUTY-02 pass (35.31h of 60h, headroom 24.69h), RULE-FLT-03 pass (50.15h of 100h), RULE-REST-04 pass (12.50h, margin 0.5h), RULE-QUAL-05 pass (A320 rated), RULE-CERT-06 pass (all 4 certs valid), RULE-BASE-07 conditional (base DEL ≠ duty start BLR).
> - Reserve roster: on-call window 03:00–15:00Z covers the revised 09:00Z report.
> - Cost table figures as quoted in the check.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> No — C-5417 (S. Krishnan, Cabin Crew) cannot legally operate P-2213 on VT-DXB on 2026-09-19: recurrent training expired 2026-09-17 (RULE-CERT-06 breach). All six other rules pass, so the duty needs a Cabin Crew replacement unless the training is revalidated before report at 02:00Z.
> 
> Reasoning:
> - C-5417's roster for 2026-09-19: P-2213 on VT-DXB, 4 sectors DX421–DX424, report 02:00Z / release 13:15Z at BLR.
> - Legality check on the rostered duty: RULE-FDP-01 11.25h vs 12.0h limit, RULE-DUTY-02 32.89h/60h, RULE-FLT-03 58.46h/100h, RULE-REST-04 60.75h vs 12h min, RULE-QUAL-05 rated A320, RULE-BASE-07 n/a (rostered) — all pass.
> - Certification record: recurrent_training valid to 2026-09-17 → expired on the duty date (RULE-CERT-06).

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest report: 2026-09-17T03:30Z.
> 
> Reasoning:
> - Rest lookup for a 15:30Z release on 2026-09-16 returns earliest report 2026-09-17T03:30Z, with minimum rest 12h.
> - Rulebook: RULE-REST-04.
> 
> ⚠ Unverified: 2026-09-17T03:30Z — not found in any data result; treat as unconfirmed.

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> No — C-3305 cannot cover the full P-2291.
> 
> - Day 2 (2026-09-16) breaches RULE-DUTY-02: 68.25h duty in the 7 days ending 2026-09-16, 8h15m over the 60h limit.
> - Also an availability issue: his reserve on-call window is 00:00–05:30Z, which does not cover the 06:00Z report on 2026-09-15.
> - Day 1 alone (2026-09-15) checks out on the rules — FDP 9.5h vs 12.5h limit, 59.5h/60h duty (0.5h headroom), rest, A320 rating, certs and BLR base all pass — but the on-call window still doesn't reach 06:00Z.
> 
> Reasoning:
> - Legality check of C-3305 against P-2291, both duty days: one breach (RULE-DUTY-02 on 2026-09-16), all other rules pass; reserve roster window 00:00–05:30Z vs required report 06:00Z.
> - Pairing P-2291 (VT-DXC): 2026-09-15 report 06:00Z/release 15:30Z BLR–DEL, 3 sectors; 2026-09-16 report 04:00Z/release 14:45Z DEL–BLR, 3 sectors.
> - Callout cost if it were usable: ₹18,500 (cost table).

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> Cancelling DX404 (MAA–BLR) on 2026-09-16 affects 162 passengers at a direct cancellation cost of INR 250,000. It releases pairing P-2203's crew: C-3187, C-5375, C-3211, C-2876, C-1542, C-5089.
> 
> Reasoning:
> - Flight schedule/cancellation impact for DX404 on 2026-09-16: route MAA-BLR, 162 seats booked-at-risk.
> - Cost table: cancellation per flight = INR 250,000.
> - Roster: pairing P-2203 operates the leg; its six crew are freed.

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew are at or above 45 duty hours in the 7 days ending 2026-09-15:
> 
> - C-2087 R. Iyer (Captain) — 51.83h duty, 8.17h headroom; 23.5h block/28d
> - C-3305 V. Menon (Captain) — 50.0h duty, 10.0h headroom; 33.6h block/28d
> 
> Neither has planned duty on 2026-09-15 itself, and both remain under the 60h limit.
> 
> Reasoning:
> - Rolling-limit check for the 7-day window ending 2026-09-15, threshold 45h, counting history plus rostered duty: 2 crew returned.
> - RULE-DUTY-02 (60h/7 days) drives the headroom figures; RULE-FLT-03 (100h/28 days) block hours shown for context — both well inside.

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> One reserve captain works: **C-3315 (M. Pillai)** — window 03:00–15:00Z covers the 03:00Z report, BLR-based, ATR72-rated.
> 
> - C-3305 (V. Menon): window 00:00–05:30Z covers it, but A320 only — no ATR72 rating (RULE-QUAL-05).
> - C-3310 (D. Reddy): window 06:00–18:00Z does not cover 03:00Z, and no ATR72 rating.
> - C-2210 (S. Kapoor): window covers it but no ATR72 rating and DEL-based (RULE-BASE-07 deadhead required).
> 
> Reasoning:
> - VT-DXE on 2026-09-16 operates pairing P-2224 (DX451–DX454), Captain C-3231 (L. Verma); report 03:00Z BLR, release 11:15Z, 4 sectors.
> - Reserve roster checked against report 03:00Z, rank Captain, ATR72, BLR: 1 eligible, 3 excluded as above.
> - Rules applied: RULE-QUAL-05 (rating), RULE-BASE-07 (own base), plus on-call window coverage for reserve callout.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> **No — not legal.** C-5837 (A. Sharma, Captain, BLR) fails RULE-REST-04 downstream: only 10.75h rest before P-2204 on 2026-09-17, against the 12h minimum (margin −1.25h).
> 
> Everything else passes — FDP 9.50h on 15 Sep and 10.75h on 16 Sep vs the 12.5h limit for 3 sectors, duty 54.00h in the tightest 7-day window (limit 60h), block 77.51h/100h, A320 rated, all 4 certifications valid, own-base callout from BLR. Day-off callout cost would be ₹24,000.
> 
> Reasoning:
> - Legality check of C-5837 against P-2291 (duty days 2026-09-15 and 2026-09-16), all seven rules over his full timeline.
> - Single breach: RULE-REST-04 on 2026-09-17, computed 10.75h against the 12h limit.
> - Note the intra-pairing rest into 16 Sep is also thin at 12.50h (margin 0.5h) — a delay on 15 Sep would break that too.
> - To use him, P-2204 on 17 Sep would need re-crewing; otherwise take the next-ranked cover option.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two legs affected, both on pairing P-2234 — 144 seats total. No FDP breaches; both delay with the rostered crew legal.
> 
> - DX461 (arrival HYD 06:30Z): min delay 3.0h, crew FDP after delay 8.25h vs 13.0h limit
> - DX462 (departure HYD 07:15Z): min delay 2.25h, crew FDP after delay 7.5h vs 13.0h limit
> 
> Reasoning:
> - Closure impact for HYD on 2026-09-19, 05:00–09:00Z: 2 affected flights, both in pairing P-2234, 72 seats each.
> - Minimum delay = reopen + 30 min turnaround; FDP after delay checked against RULE-FDP-01 (13.0h) — no breach either leg, so no re-crewing or cancellation needed.

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> No single leg stands out — every A320 leg carries the maximum exposure at 162 seats (e.g. DX401), versus 72 seats on an ATR72 leg (e.g. DX451). Cancellation cost is 250,000 INR per leg either way.
> 
> Reasoning:
> - Seats-at-risk view: seats are fixed by aircraft type, so all 105 A320 legs tie at 162 seats; the 42 ATR72 legs sit at 72.
> - Cost table: cancellation is a flat 250,000 INR per flight, so the differentiator is passenger exposure, not cost.
