# Eval report — agent-sdk

Run: 2026-09-05T09:11:34Z · **6/8** questions with all expected facts recalled · latency p50 14241 ms / p95 27308 ms / max 27308 ms · est. cost $1.05

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q31 | 3 | ✅ |  | recommend_cover | 14502 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 15913 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | simulate_delay, resolve_delay_options | 13282 |
| Q34 | 3 | ✅ |  | get_crew, get_certifications, declare_unavailable, recommend_cover | 17736 |
| Q35 | 3 | ✅ |  | station_closure_impact | 27308 |
| Q36 | 3 | ✅ |  | draft_callout_notification | 10240 |
| Q37 | 3 | ✅ |  | find_pairings, recommend_cover | 13981 |
| Q38 | 3 | ❌ | crew legality headroom (7d duty) for today's rostered crew | morning_briefing | 13478 |

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> Captain slot on P-2291 (2026-09-15 to 2026-09-16, 6 legs, 972 passengers at risk); cover must take the full remaining pairing, report 2026-09-15T06:00Z at BLR.
> 
> - Rank 1 — C-3310, reserve callout, ₹18,500, no delay, covers both duty days
> - Rank 2 — C-1526, day-off callout, ₹24,000, no delay, covers both duty days
> - Rank 3 — C-3983, day-off callout, ₹24,000, no delay, covers both duty days
> - Rank 4 — C-5566, day-off callout, ₹24,000, no delay, covers both duty days
> - Rank 5 — C-2210, reserve callout + deadhead from DEL on DX402 (arr 08:45Z, report 09:00Z), ₹41,200, 3.0h delay to DX412
> - Rank 6 — cancel all 6 legs, ₹1,500,000, 972 passengers stranded (last resort)
> 
> Reasoning:
> - Cover ranking for the Captain role on P-2291 from 2026-09-15: 24 candidates considered, ranked by cost, then delay.
> - All five crew options pass all seven rules (RULE-FDP-01, RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07). C-3310 is BLR-based, A320-rated, on-call 06:00–18:00Z, reachable in 45 min, DUTY-02 headroom 39.8h.
> - C-2210 is DEL-based, so RULE-BASE-07 requires paid positioning: ₹18,500 callout + ₹6,500 deadhead + ₹16,200 delay.
> - Exclusions from the same ranking: 8 on no A320 rating (RULE-QUAL-05), 8 on rest/overlap conflicts (RULE-REST-04), 2 on 60h/7d (RULE-DUTY-02: C-2087, C-2143), and reserve C-3305 whose on-call window 00:00–05:30Z does not cover the 06:00Z report.
> - Nothing committed yet — say the word and I'll apply an option.

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> **Joint plan — total ₹42,500, no delay, all 8 legs covered, nobody assigned twice:**
> - P-2205 (VT-DXA, C-3940 out): **C-3305** — reserve callout, ₹18,500, 0h delay, all legs
> - P-2212 (VT-DXB, C-1938 out): **C-1017** — day-off callout, ₹24,000, 0h delay, all legs
> 
> Alternates for either slot (all legal, 0h delay, all legs): C-1042 ₹24,000 · C-1526 ₹24,000 · C-2087 ₹24,000 · C-2143 ₹24,000 (RULE-REST-04 headroom only 0.2h on P-2205 / 0.8h on P-2212 — tight).
> 
> Reasoning:
> - Both A320 lines on 2026-09-18 are single-day pairings: P-2205 (DX401–DX404) and P-2212 (DX421–DX424); captains C-3940 and C-1938 respectively.
> - Only one reserve captain qualifies at those report times (01:30Z / 02:00Z): C-3305, BLR-based, A320-rated, on-call 00:00–05:30Z — so the second slot must go to the cheapest day-off callout, C-1017.
> - C-3310 excluded: reserve window 06:00–18:00Z doesn't cover the report times. C-5566 excluded on RULE-REST-04 (10.0h/10.5h rest after P-2293). C-1443 and the two sick captains excluded on overlapping duty. Six captains excluded on RULE-QUAL-05 (no A320 rating).
> - All seven rules (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07) pass for both assignments.
> - Nothing committed yet — say the word and I'll apply both covers.

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> The 90-minute delay puts P-2203 (VT-DXA, 2026-09-16) at 12.75h FDP against a 12.0h limit for 4 sectors — RULE-FDP-01 breach. The whole rostered crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089) can legally fly only the first 3 legs; DX404 needs re-crewing.
> 
> Two options:
> - **Rank 1 — re-crew DX404 with a reserve set** — legal, ₹75,000, no cancellation. Original crew operates DX401–DX403 delayed (3-leg FDP 11.0h vs 12.5h limit). Reserves: CPT C-3310, FO C-3311, SCC C-3677, CC C-1329 / C-4809 / C-5418; report 11:45Z, FDP 2.50h.
> - **Rank 2 — cancel DX404** — legal, ₹250,000, 162 passengers stranded.
> 
> Recommend rank 1.
> 
> Reasoning:
> - Delay simulation on VT-DXA 2026-09-16: report 01:30Z, release moves 12:45Z → 14:15Z; FDP 11.25h → 12.75h vs 12.0h limit (4 sectors) — RULE-FDP-01 breach, legal leg count 3, DX404 needs re-crew.
> - All six rostered crew fail only RULE-FDP-01; RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06, RULE-BASE-07 all pass for each.
> - Reserve set on the tail leg satisfies the callout window and RULE-REST-04 (12h); costs from the cost table.

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> C-5417's recurrent training expires 2026-09-17, so they are ineligible for P-2213 on 2026-09-19 (RULE-CERT-06). Recorded as unavailable from 2026-09-18; the Cabin Crew slot on P-2213 (VT-DXB, report 2026-09-19T02:00Z, DX421/422/423/424, 648 pax) is vacant. Ranked legal covers:
> 
> - Rank 1 — C-4809, reserve callout, ₹9,500, 0h delay, all legs
> - Rank 2 — C-1021, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 3 — C-1385, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 4 — C-1414, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 5 — C-1569, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 6 — C-1748, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 7 — C-1873, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 8 — C-1970, day-off callout, ₹12,500, 0h delay, all legs
> - Rank 9 — cancel all 4 legs, ₹1,000,000, 648 pax stranded (last resort)
> 
> Reasoning:
> - C-5417's certifications: recurrent_training valid to 2026-09-17, not valid on 2026-09-19; licence, medical and DG valid — RULE-CERT-06 fails only on training.
> - Scenario record: P-2213 on 2026-09-19 vacant, 4 legs, 648 passengers exposed; their 2026-09-16 pairing P-2210 is unaffected.
> - Cover ranking: 29 candidates, all seven rules checked per option; 21 excluded — RULE-QUAL-05 (no A320), RULE-REST-04 overlaps/short rest, or reserve windows 04:00–16:00Z not covering the 02:00Z report.
> - C-4809 is BLR-based, A320-rated, on-call 00:00–12:00Z, reachable in 45 min, RULE-DUTY-02 headroom 48.8h.
> 
> Say the word and I'll commit one and draft the callout.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> **BLR closed 08:00–14:00Z on 2026-09-17 — 13 flights hit, 6 pairings, 1,836 passengers affected. 10 of the 13 legs breach RULE-FDP-01 after the minimum delay; those tails need re-crewing or cancellation.**
> 
> Per pairing (minimum delay = reopen + 30 min turnaround):
> 
> - **P-2204** (3 legs, 486 seats) — worst case. DX402 arr 08:45Z +5.75h → FDP 17.0 vs 12.0; DX403 dep 09:30Z +5.0h → 16.25; DX404 arr 12:15Z +2.25h → 13.5. All three breach → re-crew the whole day from reserves or cancel.
> - **P-2211** (3 legs, 486 seats) — DX422 arr 08:45Z +5.75h → 17.0; DX423 dep 09:30Z +5.0h → 16.25; DX424 arr 12:45Z +1.75h → 13.0. All three breach → same treatment.
> - **P-2218** (2 legs, 324 seats) — DX433 dep 08:30Z +6.0h → 15.75 vs 12.0; DX434 arr 11:45Z +2.75h → 12.5. Both breach → re-crew both legs or cancel.
> - **P-2293** (2 legs, 324 seats) — DX413 arr 11:15Z +3.25h → 12.75 vs 12.5, breach; DX588 dep 12:15Z +2.25h → 11.75, crew stay legal. Cover DX413 only; DX588 runs delayed with the rostered crew.
> - **P-2225** (2 legs, 144 seats) — DX453 dep 08:00Z +6.5h → 14.75 vs 12.0, breach; DX454 arr 10:45Z +3.75h → 12.0, exactly at limit, legal. Re-crew DX453 only.
> - **P-2232** (1 leg, 72 seats) — DX462 arr 08:45Z +5.75h → 11.0 vs 13.0. No breach; delay only, no crew action.
> 
> Suggested sequencing: hold P-2232, P-2225 tail and P-2293's DX588 as delay-only; build reserve sets for P-2204 and P-2211 first (486 seats each, three breached legs each), then P-2218, then the single DX413 slot on P-2293.
> 
> Reasoning:
> - Station closure impact for BLR 08:00–14:00Z on 2026-09-17: 13 affected legs, 1,836 passengers, per-flight minimum delay and crew FDP after delay as listed.
> - Breach test is RULE-FDP-01 (13h base, less 0.5h per sector beyond the 2nd — hence the 12.0/12.5/13.0 limits shown per pairing).
> - Minimum delay per leg = reopen 14:00Z + 30 min turnaround − scheduled time at BLR.
> - Say the word and I'll rank reserve sets for the breached tails on any of these pairings.

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Callout drafted for C-3310 (D. Reddy, Captain) on P-2291 (VT-DXC), acknowledgement due by 2026-09-14T18:30Z.
> 
> **CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291**
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> 
> - **Day 1 (2026-09-15):** report 06:00Z at BLR crew room; DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z. Overnight at DEL — hotel arranged.
> - **Day 2 (2026-09-16):** report 04:00Z at DEL crew room; DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> 
> Acknowledgement request — deadline 2026-09-14T18:30Z (30 minutes): reply ACK P-2291.
> Contact for questions: Crew Control desk, BLR.
> 
> Reasoning:
> - Roster for P-2291: two duty days, report/release times, flights, DEL overnight with hotel arranged.
> - Crew record: C-3310 is a Captain, matching the slot.
> - Reason line defaults to crew unavailability — tell me if you want it worded differently.

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> Cheapest legal cover for C-4520 (FO, P-2235, VT-DXF, 2026-09-20): reserve callout C-3316 at ₹18,500, no delay, all legs.
> 
> Ranked options:
> - 1. C-3316 — reserve callout — ₹18,500 — 0h delay — all legs
> - 2. C-1313 — day-off callout — ₹24,000 — 0h delay — all legs
> - 3. C-1317 — day-off callout — ₹24,000 — 0h delay — all legs
> - 4. C-2085 — day-off callout — ₹24,000 — 0h delay — all legs
> - 5. C-3057 — day-off callout — ₹24,000 — 0h delay — all legs
> - 6. Cancel both legs — ₹500,000 — 144 passengers stranded (last resort)
> 
> Reasoning:
> - P-2235 on VT-DXF, 2026-09-20: DX461/DX462, BLR–BLR, report 04:00Z; FO slot is C-4520 (R. Sharma), 144 passengers exposed.
> - C-3316: BLR-based, ATR72-rated, on-call 03:00–15:00Z, reachable in 45 min; all seven rules pass (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07), DUTY-02 headroom 54.8h.
> - 26 FOs considered; 21 excluded on RULE-QUAL-05 (no ATR72 rating), C-3136 on RULE-REST-04 (overlaps P-2228).
> - Nothing recorded on the working scenario — this is a what-if only; say the word to declare C-4520 out and apply C-3316.

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Three per line, as the standing briefing for tomorrow (2026-09-15) already surfaces them:
> 
> - **Tightest 7-day duty headroom on the line** — the crew member closest to the RULE-DUTY-02 60h limit, plus certification validity (RULE-CERT-06). Tomorrow: VT-DXA is tightest at 27.83h (C-3988); all lines show certs valid.
> - **Highest disruption-risk score on the line** — flags who is most likely to drop out before report. Tomorrow: VT-DXC 0.78 (C-1042, Captain), VT-DXA 0.71 (C-3940), VT-DXB 0.69 (C-1938); VT-DXF lowest at 0.15.
> - **Eligible reserves at that line's report time** — cover depth if the line breaks, filtered by on-call window, rating and base (RULE-QUAL-05, RULE-BASE-07). Tomorrow: VT-DXC's 06:00Z report has 9 eligible; the 01:30–02:30Z lines (VT-DXA/B/D) have only 3 each — C-3305, C-4809, C-3312.
> 
> Reasoning:
> - Morning briefing for 2026-09-15, six aircraft lines with pairing and report time: P-2202 (01:30Z), P-2209 (02:00Z), P-2216 (02:30Z), P-2223 (03:00Z), P-2230 (04:00Z), P-2291 (06:00Z).
> - Headroom + certs answer "can the rostered crew legally fly it" (RULE-DUTY-02, RULE-CERT-06); risk answers "will they show"; reserve count answers "if not, what do I have" — the early-morning lines are the thin ones.
> - Risk scores are a provided input, not computed here.
