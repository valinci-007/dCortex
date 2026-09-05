# Eval report — agent-sdk

Run: 2026-09-04T11:27:33Z · **16/16** questions with all expected facts recalled · latency p50 7002 ms / p95 8724 ms / max 11029 ms · est. cost $0.43

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q01 | 1 | ✅ |  | list_reserves | 11029 |
| Q02 | 1 | ✅ |  | get_duty_clock | 7995 |
| Q03 | 1 | ✅ |  | list_flights | 6660 |
| Q04 | 1 | ✅ |  | list_expiring_certifications | 8724 |
| Q05 | 1 | ✅ |  | get_flight | 6229 |
| Q06 | 1 | ✅ |  | get_crew | 7280 |
| Q07 | 1 | ✅ |  | get_crew | 7654 |
| Q08 | 1 | ✅ |  | get_pairing | 7946 |
| Q09 | 1 | ✅ |  | list_flights | 7085 |
| Q10 | 1 | ✅ |  | list_flights | 6009 |
| Q11 | 1 | ✅ |  | list_crew | 6919 |
| Q12 | 1 | ✅ |  | schedule_stats | 5923 |
| Q13 | 1 | ✅ |  | get_crew, get_duty_clock | 7709 |
| Q14 | 1 | ✅ |  | list_routes | 6126 |
| Q15 | 1 | ✅ |  | find_pairings | 6431 |
| Q16 | 1 | ✅ |  | get_risk_signal | 6734 |

## Q01 — Who is on reserve at BLR on 2026-09-15, and what are their on-call windows?

**Expected:** `[{"crew_id": "C-3305", "rank": "Captain", "window": {"start": "00:00", "end": "05:30"}}, {"crew_id": "C-3310", "rank": "Captain", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3311", "rank": "First Officer", "window": {"start": "06:00", "end": "18:00"}}, {"crew_id": "C-3312", "rank": "First Officer", "window": {"start": "00:00", "end": "12:00"}}, {"crew_id": "C-3315", "rank": "Capt`

**Answer:**

> 12 reserves at BLR on 2026-09-15 (all active, windows UTC):
> 
> Flight deck
> - C-3305 V. Menon, Captain A320 — 00:00–05:30 (45 min)
> - C-3310 D. Reddy, Captain A320 — 06:00–18:00 (45 min)
> - C-3315 M. Pillai, Captain ATR72 — 03:00–15:00 (45 min)
> - C-3311 K. Rao, FO A320 — 06:00–18:00 (45 min)
> - C-3312 P. Sharma, FO A320 — 00:00–12:00 (60 min)
> - C-3316 N. Verma, FO ATR72 — 03:00–15:00 (45 min)
> 
> Cabin
> - C-2111 A. Gupta, SCC A320/ATR72 — 04:00–16:00 (90 min)
> - C-3677 M. Iyer, SCC A320/ATR72 — 04:00–16:00 (45 min)
> - C-1329 P. Pillai, CC — 04:00–16:00 (45 min)
> - C-2248 H. Reddy, CC — 04:00–16:00 (60 min)
> - C-4809 M. Das, CC — 00:00–12:00 (45 min)
> - C-5418 S. Das, CC — 04:00–16:00 (45 min)
> 
> Reasoning:
> - list_reserves for BLR on 2026-09-15 returned count 12; windows, ranks, ratings and reachability taken directly from that result.
> - Callout only valid if required report time falls inside the window; RULE-BASE-07 satisfied since all are BLR-based. RULE-QUAL-05 applies for type (note C-3315/C-3316 are ATR72-only).

## Q02 — As of the snapshot, how many duty hours has C-1042 accrued in the 7 calendar days ending 2026-09-14, and how much headroom does that leave under RULE-DUTY-02?

**Expected:** `{"duty_hours_7d": 20.93, "headroom_hours": 39.07}`

**Answer:**

> C-1042 has 20.93 duty hours in the window 2026-09-08 → 2026-09-14, leaving 39.07h headroom under the 60h limit of RULE-DUTY-02.
> 
> Reasoning:
> - get_duty_clock for C-1042 as of 2026-09-14T18:00:00Z: duty_hours_7d 20.93, limit 60.0, headroom 39.07 (window 09-08 to 09-14).
> - Contributing days in window: 2026-09-09 (9.99h) and 2026-09-12 (10.94h).
> - Also on file: 64.27 block hours /28d, 35.73h headroom under RULE-FLT-03; earliest next report 2026-09-13T02:00:00Z (RULE-REST-04).

## Q03 — Which flights depart DEL on 2026-09-15?

**Expected:** `["DX402"]`

**Answer:**

> One flight departs DEL on 2026-09-15:
> - DX402 DEL–BLR, dep 06:00Z / arr 08:45Z, block 2.75h, VT-DXA (A320), 162 seats.
> 
> Reasoning:
> - list_flights for date 2026-09-15, dep_station DEL returned count 1 (DX402).

## Q04 — List all certifications expiring within 30 days of 2026-09-15.

**Expected:** `[{"crew_id": "C-2087", "cert_type": "licence", "valid_to": "2026-09-18"}, {"crew_id": "C-2091", "cert_type": "medical_class1", "valid_to": "2026-09-23"}, {"crew_id": "C-5417", "cert_type": "recurrent_training", "valid_to": "2026-09-17"}, {"crew_id": "C-3116", "cert_type": "dangerous_goods", "valid_to": "2026-09-28"}, {"crew_id": "C-5020", "cert_type": "recurrent_training", "valid_to": "2026-10-03"`

**Answer:**

> 6 certifications expire in the window 2026-09-15 → 2026-10-15:
> 
> - C-5417 S. Krishnan (Cabin Crew) — recurrent_training, expires 2026-09-17
> - C-2087 R. Iyer (Captain) — licence, expires 2026-09-18
> - C-2091 H. Naidu (Captain) — medical_class1, expires 2026-09-23
> - C-3116 R. Naidu (First Officer) — dangerous_goods, expires 2026-09-28
> - C-5020 K. Nair (First Officer) — recurrent_training, expires 2026-10-03
> - C-2993 I. Kulkarni (First Officer) — medical_class1, expires 2026-10-08
> 
> Reasoning:
> - list_expiring_certifications from 2026-09-15, 30 days → count 6, soonest first.
> - RULE-CERT-06: crew may not operate on a duty date after their certification expiry — C-5417 and C-2087 are the near-term rostering risks.
> - Note: C-2087's licence record shows valid_from 2028-11-06, a data anomaly worth flagging to records.

## Q05 — Which aircraft operates DX412 on 2026-09-15, and how many seats does it have?

**Expected:** `{"aircraft": "VT-DXC", "aircraft_type": "A320", "seats": 162}`

**Answer:**

> VT-DXC (A320), 162 seats. DX412 operates BLR–BOM, dep 07:00Z / arr 08:45Z, 1.75h block, on pairing P-2291.
> 
> Reasoning:
> - get_flight DX412 on 2026-09-15 returned aircraft VT-DXC, type A320, seats 162, pairing P-2291.

## Q06 — What is C-3310's reserve on-call window and reachability?

**Expected:** `{"window": {"start": "06:00", "end": "18:00"}, "reachability_minutes": 45}`

**Answer:**

> C-3310 (D. Reddy, Captain, BLR, A320) is on reserve 06:00–18:00 UTC, every day of the schedule week (2026-09-14 to 2026-09-20), with reachability of 45 minutes.
> 
> Reasoning:
> - get_crew for C-3310: is_reserve true, on-call window 06:00–18:00 UTC, reserve dates 2026-09-14…2026-09-20, reachability_minutes 45, base BLR.
> - Callout must have report time inside that window; RULE-BASE-07 applies (BLR base unless deadhead positioning paid).

## Q07 — What is C-2210's base and rating?

**Expected:** `{"base": "DEL", "ratings": ["A320"]}`

**Answer:**

> C-2210 (S. Kapoor, Captain) is based at DEL and rated on A320 only. He is a reserve all week, on-call 03:00–15:00Z.
> 
> Reasoning:
> - get_crew for C-2210: base DEL, ratings [A320], status active, seniority 2, reachability 60 min.
> - RULE-QUAL-05 (rating) and RULE-BASE-07 (callout from own base, DEL) apply if you're considering him for cover.

## Q08 — Which crew are assigned to pairing P-2291, and in what roles?

**Expected:** `[{"crew_id": "C-1042", "role": "Captain"}, {"crew_id": "C-1694", "role": "First Officer"}, {"crew_id": "C-3005", "role": "Senior Cabin Crew"}, {"crew_id": "C-4395", "role": "Cabin Crew"}, {"crew_id": "C-4273", "role": "Cabin Crew"}, {"crew_id": "C-1873", "role": "Cabin Crew"}]`

**Answer:**

> P-2291 (VT-DXC, 2 duty days, 15–16 Sep) is crewed by six:
> 
> - C-1042 A. Nair — Captain
> - C-1694 S. Menon — First Officer
> - C-3005 H. Chandra — Senior Cabin Crew
> - C-4395 V. Rao — Cabin Crew
> - C-4273 P. Menon — Cabin Crew
> - C-1873 K. Joshi — Cabin Crew
> 
> Reasoning:
> - get_pairing P-2291 returned the crew block with roles and names as listed.
> - Same call shows aircraft VT-DXC, day 1 BLR→DEL (9.5h duty, 3 sectors), day 2 DEL→BLR (10.75h duty, 3 sectors).

## Q09 — Which flights fly BLR→BOM on 2026-09-17?

**Expected:** `["DX431", "DX412"]`

**Answer:**

> Two BLR→BOM legs on 2026-09-17:
> - DX431 — dep 03:30Z, arr 05:15Z, VT-DXD (A320), 1.75h block
> - DX412 — dep 07:00Z, arr 08:45Z, VT-DXC (A320), 1.75h block
> 
> Reasoning:
> - list_flights (date 2026-09-17, BLR→BOM) returned count 2: DX431, DX412; times, aircraft and block hours quoted directly from that result.

## Q10 — How many flights operate on 2026-09-16 in total?

**Expected:** `21`

**Answer:**

> 21 flights operate on 2026-09-16, across all six aircraft (2,862 seats total).
> 
> Reasoning:
> - list_flights for date 2026-09-16 with no other filters returned count = 21 (DX401–DX404, DX421–DX424, DX431–DX434, DX451–DX454, DX461/DX462, DX589–DX591).

## Q11 — How many captains are based at DEL, and who are they?

**Expected:** `["C-2210"]`

**Answer:**

> One Captain is based at DEL.
> 
> - C-2210 — S. Kapoor, A320 rated, active, seniority 2, reachable in 60 min.
> 
> Reasoning:
> - list_crew (base=DEL, rank=Captain) returned count 1, no status filter applied.
> - Rating matters for RULE-QUAL-05 if you're covering an ATR72 leg — C-2210 is A320 only.

## Q12 — What is the longest block time in the schedule, and which flights have it?

**Expected:** `{"block_hours": 2.75, "flights": ["DX401", "DX402", "DX588", "DX589"]}`

**Answer:**

> Longest block time is 2.75h, flown by four flight numbers:
> - DX401
> - DX402
> - DX588
> - DX589
> 
> Reasoning:
> - schedule_stats returned longest_block = 2.75 block hours with flight_numbers DX401, DX402, DX588, DX589 (147 flights across the 2026-09-14 to 2026-09-20 week).

## Q13 — What is C-2087's rank, and total flight hours over the 28 days ending 2026-09-14?

**Expected:** `{"rank": "Captain", "flight_hours_28d": 23.5}`

**Answer:**

> C-2087 (R. Iyer) is a **Captain**, BLR base, A320-rated. Block hours over the 28 days 2026-08-18 → 2026-09-14: **23.5 h**, leaving 76.5 h headroom under the 100 h limit.
> 
> Reasoning:
> - get_crew C-2087: rank Captain, base BLR, rating A320, active, no pairings this week.
> - get_duty_clock C-2087: flight_hours_28d 23.5 in window 2026-08-18 to 2026-09-14, limit 100 (RULE-FLT-03), headroom 76.5. Also 51.83 duty h/7d vs 60 (RULE-DUTY-02).

## Q14 — Which stations does the network serve nonstop from BLR?

**Expected:** `["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]`

**Answer:**

> BLR serves all 7 other network stations nonstop this week (73 departures total):
> - HYD — 14
> - MAA — 14
> - CCU — 11
> - BOM — 10
> - DEL — 10
> - COK — 7
> - GOI — 7
> 
> Reasoning:
> - list_routes for BLR returned 7 destinations and 73 total flights across the schedule week 2026-09-14 to 2026-09-20, with per-destination counts as listed.

## Q15 — Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?

**Expected:** `"C-3171"`

**Answer:**

> P. Chandra (C-3171) is the Senior Cabin Crew on pairing P-2210, VT-DXB on 2026-09-16.
> 
> Reasoning:
> - find_pairings for VT-DXB on 2026-09-16 returned 1 pairing, P-2210 (DX421–DX424), with C-3171 rostered as Senior Cabin Crew.

## Q16 — What is the disruption-risk score for C-1042 and what drives it?

**Expected:** `{"score": 0.78, "drivers": ["short-rest pattern over last 14 days", "two fatigue reports this month"]}`

**Answer:**

> C-1042's disruption-risk score is **0.78** as of the snapshot. Drivers:
> - Short-rest pattern over the last 14 days
> - Two fatigue reports this month
> 
> Reasoning:
> - get_risk_signal for C-1042 returned score 0.78 as_of 2026-09-14T18:00:00Z with those two drivers.
> - Score is a provided input signal, not computed here; it is not a legality determination (see RULE-REST-04 for actual rest checks).
