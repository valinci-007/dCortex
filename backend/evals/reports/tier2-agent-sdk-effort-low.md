# Eval report — agent-sdk

Run: 2026-09-04T12:07:41Z · **14/14** questions with all expected facts recalled · latency p50 8942 ms / p95 10714 ms / max 15583 ms · est. cost $0.99

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q17 | 2 | ✅ |  | simulate_crew_removal | 7813 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 9156 |
| Q19 | 2 | ✅ |  | station_closure_impact | 10284 |
| Q20 | 2 | ✅ |  | simulate_delay | 9664 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 10714 |
| Q22 | 2 | ✅ |  | find_pairings, check_rostered_legality | 8954 |
| Q23 | 2 | ✅ |  | earliest_next_report | 5864 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 9799 |
| Q25 | 2 | ✅ |  | cancellation_impact | 6950 |
| Q26 | 2 | ✅ |  | crew_near_limits | 7360 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage, check_assignment_legality | 15583 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 8929 |
| Q29 | 2 | ✅ |  | station_closure_impact | 7660 |
| Q30 | 2 | ✅ |  | seats_at_risk | 6731 |

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Immediately uncrewed (15 Sep, day 1 of P-2291, BLR→DEL): DX412, DX413, DX588 — 486 passengers.
> 
> Also at risk on 16 Sep (DEL→BLR): DX589, DX590, DX591 — another 486 (972 total). Cover must take the full remaining pairing, since the aircraft overnights away from base.
> 
> Reasoning:
> - simulate_crew_removal for C-1042, P-2291, reported 2026-09-15T05:00:00Z: uncovered_now = DX412/DX413/DX588; also_at_risk = DX589/DX590/DX591; cover_must_take_full_pairing = true.
> - Replacement Captain must be A320-rated (RULE-QUAL-05).

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Not legal — C-2087 (R. Iyer, Captain, BLR) breaches RULE-DUTY-02 on both duty days of P-2291.
> 
> - 2026-09-15: 61.33h in 7-day window, over the 60h limit by 1h20m
> - 2026-09-16: 61.08h, over by 1h05m
> - All other rules pass: FDP 9.50h/10.75h vs 12.5h limit (3 sectors); block 37.50h vs 100h (62.50h headroom); rest 12.50h vs 12h min; A320 rated; all 4 certs valid (licence expires 2026-09-18 — tight); own base BLR. Day-off callout cost would be ₹24,000.
> 
> Reasoning:
> - check_assignment_legality for C-2087 on P-2291 from 2026-09-15 returned legal=false, feasible=false, two RULE-DUTY-02 breaches; all seven rules checked.

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights affected, 1,836 passengers, across 6 pairings. 10 of the 13 breach RULE-FDP-01 after the minimum delay and need re-crew or cancellation.
> 
> **Breaching (re-crew from reserves or cancel):**
> - DX453 (+6.5h, FDP 14.75 vs 12) — P-2225
> - DX433 (+6.0h, 15.75 vs 12) — P-2218
> - DX402 (+5.75h, 17.0 vs 12) / DX403 (+5.0h, 16.25) / DX404 (+2.25h, 13.5) — P-2204
> - DX422 (+5.75h, 17.0 vs 12) / DX423 (+5.0h, 16.25) / DX424 (+1.75h, 13.0) — P-2211
> - DX413 (+3.25h, 12.75 vs 12.5) — P-2293
> - DX434 (+2.75h, 12.5 vs 12) — P-2218
> 
> **Delay only, crew legal:** DX462 (11.0 vs 13), DX454 (12.0 vs 12), DX588 (11.75 vs 12.5)
> 
> Reasoning:
> - station_closure_impact BLR 2026-09-17 08:00–14:00Z: 13 affected flights, pairings P-2204, P-2211, P-2218, P-2225, P-2232, P-2293; 1,836 pax.
> - Min delay = reopen + 30 min turnaround; FDP after delay compared to RULE-FDP-01 limit per duty.

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six crew on P-2203 breach RULE-FDP-01: the delayed duty runs 12.75h against a 12.0h limit (4 sectors), 0.75h over. They can legally fly the first three legs; DX404 needs re-crewing or cancellation.
> 
> - Breaching: C-3187 (Capt), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (CC)
> 
> Reasoning:
> - simulate_delay VT-DXA / DX401, 2026-09-16, +1.5h: report 01:30Z, release moves 12:45Z → 14:15Z; FDP 11.25h → 12.75h vs 12.0h limit.
> - All other rules pass for every crew member: RULE-DUTY-02 (max 33.31h/60h), RULE-FLT-03 (max 71.85h/100h), RULE-REST-04, QUAL-05, CERT-06, BASE-07.
> - legal_leg_count 3; legs_needing_recrew: DX404.

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> Yes — C-2210 (S. Kapoor, Captain) is legal on all seven rules for P-2291 from 15 Sep, conditional on RULE-BASE-07 deadhead positioning from DEL.
> 
> Consequence: positioning on DX402 arrives BLR 08:45Z, so report slips 06:00Z → 09:00Z and the first departure is delayed ~3h. Total cost ₹41,200 (callout ₹18,500 + positioning ₹6,500 + delay ₹16,200).
> 
> Reasoning:
> - check_assignment_legality C-2210 / P-2291 from 2026-09-15: legal=true, no issues.
> - FDP 9.50h (15 Sep) and 10.75h (16 Sep) vs 12.5h limit for 3 sectors (RULE-FDP-01).
> - Duty 35.31h/60h (RULE-DUTY-02), block 50.15h/100h (RULE-FLT-03), rest 12.50h vs 12h min — margin only 0.5h (RULE-REST-04).
> - A320 rated (RULE-QUAL-05), all 4 certs valid (RULE-CERT-06); reserve window 03:00–15:00Z covers 09:00Z report.
> - RULE-BASE-07 conditional: base DEL ≠ duty start BLR.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> No — C-5417 (S. Krishnan, Cabin Crew) cannot legally operate P-2213 on VT-DXB, 19 Sep: recurrent training expired 2026-09-17 (RULE-CERT-06). All other six rules pass, so a replacement Cabin Crew or a re-cert before report (02:00Z) is needed.
> 
> Reasoning:
> - find_pairings VT-DXB 2026-09-19 → P-2213, C-5417 rostered as Cabin Crew.
> - check_rostered_legality: breach RULE-CERT-06 only; FDP 11.25h/12h, duty 32.89h/60h, block 58.46h/100h, rest 60.75h/12h, A320 rated, base BLR.

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest report: 2026-09-17T03:30:00Z.
> 
> Reasoning:
> - earliest_next_report on release 2026-09-16T15:30Z → 03:30Z next day, 12h min rest (RULE-REST-04).

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> No — C-3305 (V. Menon, Captain, BLR) cannot cover the full P-2291.
> 
> - **RULE-DUTY-02 breach on day 2 (16 Sep):** 68.25h in the 7-day window vs 60h limit — over by 8h15m. Day 1 alone leaves only 0.50h headroom (59.50h).
> - **Availability:** his reserve on-call window is 00:00–05:30Z, which does not cover the 06:00Z report on 15 Sep.
> - Everything else passes: FDP 9.50h/10.75h vs 12.5h (3 sectors), block 47.60h/100h, rest 12.50h, A320 rated, certs valid, own base BLR. Callout would cost ₹18,500.
> 
> Reasoning:
> - check_assignment_legality C-3305 / P-2291 over 2026-09-15 and 2026-09-16: legal=false, available=false.
> - get_pairing P-2291: 2 duty days, BLR→DEL then DEL→BLR, 3 sectors each.
> - Rules: RULE-DUTY-02 (breach), RULE-BASE-07 on-call window (unavailable).

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> 162 passengers affected; direct cancellation cost ₹250,000. DX404 (MAA–BLR) sits on pairing P-2203, releasing 6 crew: C-3187, C-5375, C-3211, C-2876, C-1542, C-5089.
> 
> Reasoning:
> - cancellation_impact for DX404 on 2026-09-16 returned 162 seats, ₹250,000 direct cost, pairing P-2203 and the released crew list.

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew, both Captains:
> - C-2087 R. Iyer — 51.83h duty/7d, 8.17h headroom (28d block 23.5h)
> - C-3305 V. Menon — 50.0h duty/7d, 10.0h headroom (28d block 33.6h)
> 
> Reasoning:
> - crew_near_limits for 2026-09-15, min_duty_hours 45, returned count 2; planned duty on 15 Sep is 0 for both.
> - Limits per RULE-DUTY-02 (60h/7d) and RULE-FLT-03 (100h/28d).

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> Only one reserve captain covers and qualifies: **C-3315 (M. Pillai)** — BLR, ATR72-rated, on-call 03:00–15:00Z, covers the 03:00Z report for P-2224 (VT-DXE, sick Captain C-3231). Legal on all seven rules; callout ₹18,500.
> 
> - C-3305 V. Menon — window 00:00–05:30Z covers, but A320 only (RULE-QUAL-05).
> - C-3310 D. Reddy — A320 only and window 06:00–18:00Z misses 03:00Z.
> - C-2210 S. Kapoor — window covers, but A320 only and DEL-based (RULE-BASE-07 deadhead).
> 
> Reasoning:
> - find_pairings/get_pairing: VT-DXE on 16 Sep = P-2224, report 03:00Z BLR, 4 sectors, Captain C-3231.
> - reserve_coverage (Captain/ATR72/BLR, 03:00Z): 1 eligible, 3 excluded with reasons.
> - check_assignment_legality C-3315 → P-2224: legal, all rules pass.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> No — not legal. C-5837 (A. Sharma, Captain) passes six rules but breaches RULE-REST-04 downstream: release 2026-09-16T14:45Z off P-2291 leaves only 10.75h before his own P-2204 report at 2026-09-17T01:30Z (min 12h, short by 1.25h). Would only work if P-2204 on 17 Sep is re-crewed; day-off callout cost ₹24,000.
> 
> Reasoning:
> - check_assignment_legality C-5837 / P-2291 (duty days 15–16 Sep): FDP 9.50h and 10.75h vs 12.5h limit (3 sectors) — pass; DUTY-02 tightest 54.00h/60h (6.00h headroom); FLT-03 tightest 77.51h/100h; QUAL-05 A320 rated; CERT-06 all 4 valid; BASE-07 callout from own base BLR.
> - Single breach: RULE-REST-04 on 2026-09-17, margin −1.25h.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two flights affected, both on pairing P-2234, 144 passengers total. No FDP breaches — delay both, crew stay legal.
> 
> - DX461 (arr HYD 06:30Z) — min delay 3.0h, FDP after delay 8.25h vs 13h limit
> - DX462 (dep HYD 07:15Z) — min delay 2.25h, FDP after delay 7.5h vs 13h limit
> 
> Reasoning:
> - station_closure_impact for HYD 2026-09-19 05:00–09:00Z returned 2 affected flights, 72 seats each, one pairing (P-2234).
> - Min delay = reopen + 30 min turnaround; RULE-FDP-01 checked, no breaches.

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any A320 leg — 162 seats at risk (e.g. DX401). No single leg stands out: seats are fixed by aircraft type.
> 
> - A320: 162 seats, 105 legs
> - ATR72: 72 seats, 42 legs
> - Cancellation cost: INR 250,000 per leg either way
> 
> Reasoning:
> - seats_at_risk returned A320 = 162 seats vs ATR72 = 72; exposure is type-driven, so all 105 A320 legs tie at the top.
