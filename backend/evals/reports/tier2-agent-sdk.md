# Eval report — agent-sdk

Run: 2026-09-04T12:05:20Z · **14/14** questions with all expected facts recalled · latency p50 9684 ms / p95 12931 ms / max 17062 ms · est. cost $0.81

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q17 | 2 | ✅ |  | simulate_crew_removal | 8534 |
| Q18 | 2 | ✅ |  | check_assignment_legality | 9691 |
| Q19 | 2 | ✅ |  | station_closure_impact | 11385 |
| Q20 | 2 | ✅ |  | simulate_delay | 11016 |
| Q21 | 2 | ✅ |  | check_assignment_legality | 10310 |
| Q22 | 2 | ✅ |  | find_pairings, find_pairings, check_rostered_legality | 12931 |
| Q23 | 2 | ✅ |  | earliest_next_report | 6025 |
| Q24 | 2 | ✅ |  | check_assignment_legality, get_pairing | 11483 |
| Q25 | 2 | ✅ |  | cancellation_impact | 6818 |
| Q26 | 2 | ✅ |  | crew_near_limits | 7660 |
| Q27 | 2 | ✅ |  | find_pairings, get_pairing, reserve_coverage, check_assignment_legality | 17062 |
| Q28 | 2 | ✅ |  | check_assignment_legality | 9676 |
| Q29 | 2 | ✅ |  | station_closure_impact | 8525 |
| Q30 | 2 | ✅ |  | seats_at_risk | 9361 |

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Three legs are uncrewed immediately on 15 Sep (486 pax), with three more at risk on 16 Sep.
> 
> - Now: DX412, DX413, DX588 (15 Sep, BLR→…→DEL)
> - At risk: DX589, DX590, DX591 (16 Sep, DEL→…→BLR) — 972 pax total exposure
> 
> Cover must take the full remaining pairing (aircraft overnights at DEL, away from base).
> 
> Reasoning:
> - simulate_crew_removal for C-1042 (A. Nair, Captain) on P-2291, reported 2026-09-15T05:00:00Z: uncovered_now = 3 legs, also_at_risk = 3 legs, cover_must_take_full_pairing = true.
> - Replacement must satisfy RULE-QUAL-05 (type rating); check legality of any candidate before assigning.

## Q18 — If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach? Give the detail.

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)", "RULE-DUTY-02: would exceed 60h/7d by 1h05m on 2026-09-16 (total 61.08h)"]}`

**Answer:**

> Yes — not legal. C-2087 (R. Iyer, Captain) breaches RULE-DUTY-02 on both duty days of P-2291:
> 
> - 2026-09-15: 61.33h in the 7-day window (09-09→09-15) — over 60h by 1h20m
> - 2026-09-16: 61.08h in the 7-day window (09-10→09-16) — over 60h by 1h05m
> 
> Everything else passes: FDP 9.50h / 10.75h vs 12.5h limit (3 sectors), block 37.50h/100h, rest 12.50h vs 12h minimum (only 0.5h margin), A320 rated, all 4 certs valid (licence expires 2026-09-18 — tight), callout from own base BLR. Day-off callout cost would be ₹24,000.
> 
> Reasoning:
> - check_assignment_legality for C-2087 on P-2291 from 2026-09-15: legal=false, feasible=false, duty dates 09-15 and 09-16.
> - Two RULE-DUTY-02 breach verdicts with computed 61.33 and 61.08 vs limit 60.0.
> - All other verdicts pass: RULE-FDP-01, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07.

## Q19 — BLR is closed 08:00–14:00Z on 17 Sep. Which flights are affected?

**Expected:** `["DX402-2026-09-17", "DX422-2026-09-17", "DX462-2026-09-17", "DX453-2026-09-17", "DX433-2026-09-17", "DX403-2026-09-17", "DX413-2026-09-17", "DX423-2026-09-17", "DX454-2026-09-17", "DX434-2026-09-17", "DX404-2026-09-17", "DX424-2026-09-17", "DX588-2026-09-17"]`

**Answer:**

> 13 flights across 6 pairings, 1,836 seats exposed. 10 of the 13 breach RULE-FDP-01 after the minimum reopen delay and need re-crewing or cancellation.
> 
> **FDP breaches (re-crew or cancel):**
> - DX453 (P-2225, +6.5h, FDP 14.75 vs 12.0)
> - DX433 (P-2218, +6.0h, 15.75 vs 12.0)
> - DX402 (P-2204, +5.75h, 17.0 vs 12.0)
> - DX422 (P-2211, +5.75h, 17.0 vs 12.0)
> - DX403 (P-2204, +5.0h, 16.25 vs 12.0)
> - DX423 (P-2211, +5.0h, 16.25 vs 12.0)
> - DX413 (P-2293, +3.25h, 12.75 vs 12.5)
> - DX434 (P-2218, +2.75h, 12.5 vs 12.0)
> - DX404 (P-2204, +2.25h, 13.5 vs 12.0)
> - DX424 (P-2211, +1.75h, 13.0 vs 12.0)
> 
> **Delay only, crew stays legal:** DX462 (+5.75h, 11.0/13.0), DX454 (+3.75h, 12.0/12.0 — at the limit), DX588 (+2.25h, 11.75/12.5)
> 
> Reasoning:
> - station_closure_impact BLR 2026-09-17 08:00–14:00Z: 13 affected legs, 1,836 pax, pairings P-2204, P-2211, P-2218, P-2225, P-2232, P-2293.
> - Min delay = reopen 14:00Z + 30 min turnaround − scheduled time; FDP after delay compared to RULE-FDP-01 limit per duty.
> - Worst exposure is the P-2204 / P-2211 A320 chains (three legs each, 162 seats per leg).

## Q20 — VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit if they fly all four legs?

**Expected:** `{"breach": true, "fdp_after_delay": 12.75, "fdp_limit": 12.0}`

**Answer:**

> Yes — all six crew on P-2203 breach RULE-FDP-01 if they fly all four legs: FDP goes from 11.25h to 12.75h against a 12.0h limit for 4 sectors (−0.75h margin). They can legally complete only the first 3 legs; DX404 needs re-crewing or cancelling.
> 
> - Breaching: C-3187 (Capt), C-5375 (FO), C-3211 (SCC), C-2876, C-1542, C-5089 (CC)
> - All other rules pass (DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07)
> 
> Reasoning:
> - simulate_delay VT-DXA / DX401 on 2026-09-16, +1.5h: report 01:30Z unchanged, release slips 12:45Z → 14:15Z; fdp_after_delay 12.75 vs limit 12.0, breach=true, legal_leg_count 3, legs_needing_recrew ["DX404"].
> - Per-crew checks in the same result show RULE-FDP-01 breach for all six, every other rule pass (largest 7-day duty 33.31h vs 60h; smallest 28-day headroom 28.15h; rest ≥23.5h).

## Q21 — Can C-2210 (DEL base) legally cover P-2291 if positioned to BLR on the morning of 15 Sep? What is the operational consequence?

**Expected:** `{"legal": true, "consequence": "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; RULE-BASE-07 deadhead cost applies."}`

**Answer:**

> **Yes — legal, but with a 3-hour delay penalty.** C-2210 (S. Kapoor, Captain) passes all seven rules; the only condition is RULE-BASE-07 deadhead positioning from DEL.
> 
> Operational consequence:
> - Positions on DX402, arriving BLR 08:45Z → report slips 06:00Z to 09:00Z
> - **First departure of P-2291 delayed ~3.0h**
> - Total cost ₹41,200 (callout ₹18,500 + positioning ₹6,500 + delay ₹16,200)
> 
> Reasoning:
> - check_assignment_legality C-2210 / P-2291: legal=true, feasible=true, no issues; reserve on-call 03:00–15:00Z covers the 09:00Z report.
> - RULE-FDP-01 pass both days (9.50h and 10.75h vs 12.5h for 3 sectors); RULE-DUTY-02 35.31h/60h; RULE-FLT-03 50.15h/100h; RULE-REST-04 12.50h vs 12h min (only 0.5h margin between 15 and 16 Sep); RULE-QUAL-05 A320 rated; RULE-CERT-06 all 4 certs valid.
> - RULE-BASE-07 conditional: base DEL ≠ duty start BLR.

## Q22 — Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?

**Expected:** `{"legal": false, "rule": "RULE-CERT-06", "detail": "recurrent_training expired 2026-09-17"}`

**Answer:**

> **No.** C-5417 (S. Krishnan, Cabin Crew) is rostered on P-2213 / VT-DXB on 19 Sep (DX421–DX424), but the duty is **not legal**: RULE-CERT-06 breach — recurrent_training expired 2026-09-17. All six other rules pass, so a replacement Cabin Crew is needed for that pairing unless the training is revalidated before report at 02:00Z.
> 
> Reasoning:
> - find_pairings (crew C-5417 / VT-DXB, 2026-09-19) → single pairing P-2213, 4 sectors, report 02:00Z, release 13:15Z.
> - check_rostered_legality → legal: false; only breach RULE-CERT-06 (recurrent_training valid to 2026-09-17).
> - Passing: RULE-FDP-01 11.25h vs 12.0h limit (4 sectors); RULE-DUTY-02 32.89h/60h; RULE-FLT-03 58.46h/100h; RULE-REST-04 60.75h rest; RULE-QUAL-05 A320 rated; RULE-BASE-07 n/a (rostered, BLR).

## Q23 — A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?

**Expected:** `"2026-09-17T03:30:00Z"`

**Answer:**

> Earliest next report: **2026-09-17T03:30:00Z**.
> 
> Reasoning:
> - earliest_next_report for release 2026-09-16T15:30:00Z returned 03:30Z next day, min rest 12h.
> - RULE-REST-04 (12h minimum rest between release and next report).

## Q24 — Can reserve C-3305 cover the FULL pairing P-2291 (both days)? Why or why not?

**Expected:** `{"legal": false, "issues": ["RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"]}`

**Answer:**

> **No — C-3305 (V. Menon, Captain, BLR) cannot cover the full P-2291.** Two blockers: his reserve on-call window is 00:00–05:30Z, which does not cover the 06:00Z report on 15 Sep; and day 2 breaches RULE-DUTY-02 — 68.25h duty in the 7 days ending 16 Sep, 8h15m over the 60h limit.
> 
> - Day 1 (15 Sep) alone would sit at 59.50h/60h — only 0.50h headroom.
> - Everything else passes: FDP 9.50h/10.75h vs 12.5h, block 47.60h/100h, rest 12.50h, A320 rating, all 4 certs valid, own-base callout (BLR, no deadhead). Callout cost ₹18,500.
> 
> Reasoning:
> - check_assignment_legality C-3305 / P-2291 over both duty days (2026-09-15, 2026-09-16): legal=false, available=false, one breach — RULE-DUTY-02, margin −8.25h on 16 Sep.
> - Availability note: reserve window 00:00–05:30Z vs required report 06:00Z (RULE-BASE-07 base check itself passes).
> - get_pairing P-2291 confirms the two duty days, 3 sectors each, VT-DXC, BLR→DEL→BLR.

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> DX404 (MAA–BLR) on 2026-09-16: 162 passengers affected, direct cancellation cost ₹250,000.
> 
> Reasoning:
> - cancellation_impact for DX404 on 2026-09-16 returned 162 seats/pax and ₹250,000 direct cost.
> - Same call shows pairing P-2203 released with 6 crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089) — available for re-tasking.

## Q26 — Which crew have 45 or more duty hours in the 7 days ending 2026-09-15 (including any planned duty that day)?

**Expected:** `[{"crew_id": "C-2087", "duty_hours_7d_incl_15sep_plan": 51.83}, {"crew_id": "C-3305", "duty_hours_7d_incl_15sep_plan": 50.0}]`

**Answer:**

> Two crew are at or above 45 duty hours in the 7 days ending 2026-09-15:
> 
> - C-2087 R. Iyer (Captain) — 51.83h duty / 8.17h headroom; 23.5h block in 28d
> - C-3305 V. Menon (Captain) — 50.0h duty / 10.0h headroom; 33.6h block in 28d
> 
> Neither has planned duty on 2026-09-15 itself.
> 
> Reasoning:
> - crew_near_limits for 2026-09-15 with min_duty_hours 45 returned count 2, including history plus rostered duty through that date.
> - Limits applied: RULE-DUTY-02 (60h/7d) and RULE-FLT-03 (100h/28d) — both still have headroom under each.

## Q27 — The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout, and are they qualified?

**Expected:** `{"eligible": ["C-3315"], "excluded_examples": [{"crew_id": "C-3305", "reason": "RULE-QUAL-05: no ATR72 rating"}, {"crew_id": "C-3310", "reason": "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"}]}`

**Answer:**

> Sick captain is C-3231 (L. Verma) on pairing P-2224, VT-DXE, report 03:00Z at BLR. Only one reserve captain both covers the window and is qualified:
> 
> - **C-3315 M. Pillai** — BLR base, ATR72 rated, on-call 03:00–15:00Z (covers 03:00Z), reachable in 45 min. Legal on all seven rules; callout ₹18,500.
> - C-3305 V. Menon — window 00:00–05:30Z covers, but A320 only (RULE-QUAL-05 fail).
> - C-3310 D. Reddy — A320 only and window 06:00–18:00Z misses 03:00Z.
> - C-2210 S. Kapoor — window covers, but A320 only and DEL-based (RULE-BASE-07 deadhead).
> 
> Reasoning:
> - find_pairings/get_pairing: VT-DXE on 2026-09-16 = P-2224, 4 sectors, report 03:00Z / release 11:15Z at BLR, Captain C-3231.
> - reserve_coverage (Captain, ATR72, BLR, 03:00Z): 1 eligible, 3 excluded with reasons above.
> - check_assignment_legality C-3315 → P-2224: legal=true, FDP 8.25h vs 12.0h, 7-day duty 23.40h, 28-day block 50.72h, rest 25.00h, certs valid.

## Q28 — Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291. Legal?

**Expected:** `{"legal": false, "issues": ["RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"]}`

**Answer:**

> **Not legal.** C-5837 (A. Sharma, Capt) clears six of seven rules for P-2291 (15–16 Sep) but breaches RULE-REST-04 downstream: release 16 Sep 14:45Z, next report P-2204 on 17 Sep 01:30Z = only 10.75h rest vs 12h minimum. Would only work if P-2204 on 17 Sep is re-crewed or retimed; day-off callout cost ₹24,000.
> 
> Reasoning:
> - check_assignment_legality C-5837 / P-2291: legal=false, single issue RULE-REST-04 (10.75h, margin −1.25h).
> - Passes: RULE-FDP-01 (9.50h/10.75h vs 12.5h, 3 sectors), RULE-DUTY-02 (tightest 54.00h, headroom 6.00h), RULE-FLT-03 (tightest 77.51h, headroom 22.49h), RULE-QUAL-05 (A320 rated), RULE-CERT-06 (all 4 certs valid), RULE-BASE-07 (own base BLR).
> - Intra-pairing rest 15→16 Sep is 12.50h — only 0.5h margin, so any delay on 15 Sep also bites.

## Q29 — Station HYD is closed 05:00–09:00Z on 19 Sep. Which flights are affected?

**Expected:** `["DX461-2026-09-19", "DX462-2026-09-19"]`

**Answer:**

> Two flights affected, both on pairing P-2234, 144 seats exposed — no re-crewing needed, delay only.
> 
> - DX461 (arr HYD 06:30Z) — min delay 3.0h, crew FDP after delay 8.25h vs 13.0h limit, legal
> - DX462 (dep HYD 07:15Z) — min delay 2.25h, crew FDP after delay 7.5h vs 13.0h limit, legal
> 
> Reasoning:
> - station_closure_impact for HYD 2026-09-19 05:00–09:00Z returned count 2, both on P-2234, 144 passengers.
> - No RULE-FDP-01 breaches (fdp_breaches empty); action for both legs is "delay (crew legal)".
> - Min delay = reopen + 30 min turnaround vs scheduled time at station.

## Q30 — Which single flight leg has the most seats at risk if cancelled, and why?

**Expected:** `{"flights": "any A320 leg (162 seats)", "vs": "ATR72 legs (72 seats)"}`

**Answer:**

> Any A320 leg — 162 seats at risk, e.g. DX401. No single leg is worse than another within the type; exposure is set purely by aircraft size.
> 
> - A320: 162 seats, 105 legs (example DX401)
> - ATR72: 72 seats, 42 legs (example DX451)
> - Cancellation cost: ₹250,000 per leg regardless of type
> 
> Reasoning:
> - seats_at_risk returned max exposure "any A320 leg (162 seats)" vs ATR72 at 72 seats; seats are fixed by aircraft type, so all 105 A320 legs tie at the top.
> - Same tool gave cancellation cost 250,000 INR per leg.
