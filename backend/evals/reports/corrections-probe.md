# Eval report — agent-sdk

Run: 2026-09-05T07:34:40Z · **3/4** questions with all expected facts recalled · latency p50 13907 ms / p95 29434 ms / max 29434 ms · est. cost $0.38

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q17 | 2 | ✅ |  | declare_unavailable, simulate_crew_removal | 9776 |
| Q25 | 2 | ✅ |  | cancellation_impact | 12657 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 15156 |
| Q35 | 3 | ❌ | 3.75 | station_closure_impact | 29434 |

## Q17 — Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?

**Expected:** `{"day1": ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"], "day2_also_at_risk": ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"], "passengers_day1": 486}`

**Answer:**

> Three flights lose their Captain immediately on 2026-09-15 (486 pax), all on VT-DXC / P-2291:
> - DX412 — 2026-09-15
> - DX413 — 2026-09-15
> - DX588 — 2026-09-15
> 
> Also at risk on 2026-09-16 (another 486 pax): DX589, DX590, DX591 — the aircraft overnights at DEL, so a cover must take the full remaining pairing.
> 
> Reasoning:
> - C-1042 (A. Nair, Captain) recorded unavailable from 2026-09-15 (sick); both P-2291 duty days are now vacant on the working scenario.
> - Removal impact for P-2291: day 1 BLR→DEL, day 2 DEL→BLR; 972 pax exposed in total.
> - Cover must hold the rating for the pairing (RULE-QUAL-05); full legality check runs when an option is applied.

## Q25 — If DX404 on 16 Sep is cancelled, how many passengers are affected and what is the direct cancellation cost?

**Expected:** `{"passengers": 162, "cost_inr": 250000}`

**Answer:**

> **162 passengers affected; direct cancellation cost INR 250000.** DX404 on 2026-09-16 is MAA–BLR, operated on P-2203; cancelling releases 6 crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089).
> 
> Reasoning:
> - Flight schedule for DX404 on 2026-09-16: route MAA-BLR, 162 passengers affected.
> - Cancellation impact lookup: direct cancellation cost INR 250000.
> - Roster: pairing P-2203, crew released as listed.

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> Optimal joint plan — total ₹42,500, all legs covered, no delay, both legal on all seven rules:
> 
> - **P-2205 (VT-DXA, DX401–DX404)** — Captain **C-3305**, reserve callout, ₹18,500. BLR-based, A320-rated, on-call 00:00–05:30Z, reachable in 45 min; RULE-DUTY-02 headroom 22.8h.
> - **P-2212 (VT-DXB, DX421–DX424)** — Captain **C-1017**, day-off callout, ₹24,000. BLR-based, A320-rated, free on the cover day, reachable in 75 min; RULE-DUTY-02 headroom 18.7h.
> 
> Reasoning:
> - Rosters for 2026-09-18: VT-DXA = P-2205 (Capt C-3940), VT-DXB = P-2212 (Capt C-1938); 4 legs each, both slots vacant from 00:30Z.
> - Joint cover ranking: only one reserve captain (C-3305) is eligible at either report time (C-3310's on-call 06:00–18:00Z misses reports of 01:30Z / 02:00Z), so the reserve goes to P-2205 and the cheapest remaining day-off captain (C-1017, ₹24,000) takes P-2212 — cheapest combination with nobody assigned twice.
> - Backups at the same ₹24,000: C-1042, C-1526, C-2087. C-2143 is legal but tight on RULE-REST-04 (0.2–0.8h headroom). C-5566 excluded on RULE-REST-04; several captains excluded on RULE-QUAL-05 (no A320 rating).
> - Nothing committed yet — say the word and I'll apply both covers.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> **BLR 08:00–14:00Z closure, 2026-09-17 — 13 flights, 6 pairings, 1,836 seats exposed. 10 of 13 legs breach RULE-FDP-01 once delayed, so most pairings need the tail re-crewed or cancelled.**
> 
> Recovery by pairing:
> - **P-2204** (DX402/403/404, 162 seats each) — worst hit: delays 5.75h / 5.0h / 2.25h, FDP 17.0h, 16.25h, 13.5h vs 12.0h limit. Rostered crew cannot fly any of it post-delay; re-crew the whole day from reserves or cancel.
> - **P-2211** (DX422/423/424, 162 seats each) — delays 5.75h / 5.0h / 1.75h, FDP 17.0h, 16.25h, 13.0h vs 12.0h. Same treatment: full re-crew or cancel.
> - **P-2218** (DX433/434, 162 seats each) — delays 6.0h / 2.75h, FDP 15.75h and 12.5h vs 12.0h. Both legs breach; re-crew.
> - **P-2225** (DX453/454, 72 seats each) — DX453 delayed 6.5h, FDP 14.75h vs 12.0h → breach; DX454 at 12.0h vs 12.0h is legal. Re-crew the DX453 departure; DX454 can stay with the rostered crew.
> - **P-2293** (DX413/DX588, 162 seats each) — DX413 delayed 3.25h, FDP 12.75h vs 12.5h → marginal breach; DX588 at 11.75h vs 12.5h is legal. Smallest gap of the day.
> - **P-2232** (DX462, 72 seats) — delayed 5.75h, FDP 11.0h vs 13.0h. No breach; delay only, no crew action.
> 
> Suggested sequencing: protect P-2293 and P-2232 (legal or marginal), commit reserves first to P-2204 and P-2211 (six legs at 162 seats each), then P-2218 and the DX453 leg. If reserve depth runs short, the cancellation candidates with least seat exposure are the 72-seat legs rather than the 162-seat legs.
> 
> Reasoning:
> - Station closure impact for BLR on 2026-09-17 08:00–14:00Z: 13 affected flights, 6 pairings, 1,836 passengers; minimum delay = reopen + 30 min turnaround.
> - FDP after delay vs limit per leg from the same result; RULE-FDP-01 breaches flagged on DX453, DX433, DX402, DX422, DX403, DX423, DX413, DX434, DX404, DX424.
> - Non-breaching legs per the result: DX462 (11.0h/13.0h), DX454 (12.0h/12.0h), DX588 (11.75h/12.5h).
> - Seat counts per leg from the same result; no reserve availability checked yet — say the word and I'll rank cover options per pairing.
