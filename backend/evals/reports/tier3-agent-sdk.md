# Eval report — agent-sdk

Run: 2026-09-04T12:34:45Z · **4/8** questions with all expected facts recalled · latency p50 14128 ms / p95 27330 ms / max 27330 ms · est. cost $0.97

Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.

| Q | Tier | Result | Missing | Tools | ms |
|---|---|---|---|---|---|
| Q31 | 3 | ❌ | Cancel all 6 flights of the pairing | recommend_cover, simulate_crew_removal | 14796 |
| Q32 | 3 | ✅ |  | find_pairings, find_pairings, joint_cover_plan | 16200 |
| Q33 | 3 | ❌ | Delayed 3-leg duty FDP 9.5h vs 12.5h limit — legal. Reserve set covers the last  | simulate_delay, resolve_delay_options | 13460 |
| Q34 | 3 | ✅ |  | get_crew, get_certifications, recommend_cover, simulate_crew_removal, get_pairing | 27330 |
| Q35 | 3 | ❌ | DX403, 3.25, DX423, 3.75, DX434, DX404, DX424 | station_closure_impact, list_reserves, get_costs | 24947 |
| Q36 | 3 | ❌ | acknowledgement request with deadline, contact for questions | draft_callout_notification | 10585 |
| Q37 | 3 | ✅ |  | find_pairings, recommend_cover | 12895 |
| Q38 | 3 | ✅ |  | morning_briefing | 13377 |

## Q31 — Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.

**Expected:** `[{"action": "Assign Captain C-3310 (reserve callout)", "crew_id": "C-3310", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Captain C-1526 (day-off callout)", "crew_id": "C-1526", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-`

**Answer:**

> **Recommended: Option 1 — call out reserve Captain C-3310 (₹18,500, no delay, covers both duty days).**
> 
> Impact: P-2291 loses its Captain for 6 legs (DX412/413/588 on 15 Sep, DX589/590/591 on 16 Sep), 972 pax exposed; aircraft overnights DEL, so cover must take the full remaining pairing. Report 15 Sep 06:00Z at BLR.
> 
> Ranked options:
> - **1. C-3310 — reserve callout — ₹18,500, 0h delay.** BLR-based, A320-rated, on-call 06:00–18:00Z, reachable 45 min; all 7 rules pass.
> - **2. C-1526 — day-off callout — ₹24,000, 0h delay.** BLR, A320, free both days, 90 min reachability.
> - **3. C-3983 — day-off callout — ₹24,000, 0h delay.** 45 min reachability.
> - **4. C-5566 — day-off callout — ₹24,000, 0h delay.** 60 min reachability.
> - **5. C-2210 — reserve + deadhead from DEL — ₹41,200 (18,500 callout + 6,500 positioning + 16,200 delay), ~3.0h delay** to DX412 (deadheads DX402 arr 08:45Z, report 09:00Z). RULE-BASE-07 condition applies.
> - **6. Cancel all 6 legs — ₹1,500,000, 972 pax stranded.** Last resort only.
> 
> Reasoning:
> - simulate_crew_removal (C-1042 / P-2291): 3 legs uncovered now, 3 more at risk 16 Sep, 972 pax, full-pairing cover required.
> - recommend_cover: 24 candidates screened; 5 legal covers + cancellation, ranked by cost then delay.
> - Notable exclusions: C-3305 (reserve window 00:00–05:30Z misses 06:00Z report), C-2087 and C-2143 (RULE-DUTY-02 60h/7d breach), several RULE-REST-04 downstream conflicts, six with no A320 rating (RULE-QUAL-05).
> - Rules checked on every option: RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07.
> 
> Want me to draft the callout message for C-3310?

## Q32 — Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.

**Expected:** `{"total_cost_inr": 42500, "assign_dxa": {"action": "Assign Captain C-3305 (reserve callout)", "crew_id": "C-3305", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}, "assign_dxb": {"action": "Assign Captain C-1017 (day-off callout)", "crew_id": "C-1017", "`

**Answer:**

> Optimal joint plan — total ₹42,500, no delay, all 8 legs covered, nobody assigned twice:
> 
> - **P-2205 / VT-DXA** (DX401–DX404, Capt C-3940 out): call out reserve **C-3305** — ₹18,500, report 01:30Z, on-call 00:00–05:30Z, reachable 45 min.
> - **P-2212 / VT-DXB** (DX421–DX424, Capt C-1938 out): day-off callout **C-1017** — ₹24,000, report 02:00Z, reachable 75 min.
> 
> Fallbacks for the P-2212 slot at the same ₹24,000: C-1042, C-1526, C-2087, C-2143 (all BLR, A320, legal).
> 
> Reasoning:
> - find_pairings: VT-DXA → P-2205 (Capt C-3940), VT-DXB → P-2212 (Capt C-1938), both 4 legs on 2026-09-18.
> - joint_cover_plan with both sick events at 00:30Z returned the cheapest no-double-assignment combination: C-3305 is the only eligible reserve (C-3310's window 06:00–18:00Z misses both report times), so the second slot must take the cheapest day-off callout.
> - All seven rules pass for both assignments (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07).
> - Excluded: C-1443 and C-5566 on RULE-REST-04; six captains on RULE-QUAL-05 (no A320 rating).

## Q33 — After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?

**Expected:** `[{"rank": 1, "action": "Original crew operates DX401\u2013DX403 (delayed); full reserve set (CPT, FO, SCC, 3 CC) operates DX404", "legal": true, "cost_inr": 75000, "reasoning": "Delayed 3-leg duty FDP 9.5h vs 12.5h limit \u2014 legal. Reserve set covers the last sector (callout window and 12h-rest all satisfied)."}, {"rank": 2, "action": "Cancel DX404", "legal": true, "cost_inr": 250000, "reasonin`

**Answer:**

> **Recommended: split the duty on P-2203 — rostered crew flies DX401–DX403 delayed, a full reserve set operates DX404. Cost ₹75,000.**
> 
> - Breach: delayed duty runs 12.75h FDP vs 12.0h limit (4 sectors) — RULE-FDP-01, margin −0.75h. Release slips 12:45Z → 14:15Z.
> - Only DX404 needs re-crewing; rostered crew are legal for the first 3 legs (11.0h vs 12.5h limit).
> - Reserve set (report 11:45Z, FDP 2.50h): CPT C-3310, FO C-3311, SCC C-3677, CC C-1329 / C-4809 / C-5418.
> - Fallback: cancel DX404 — legal but ₹250,000 and 162 pax stranded (~3.3x costlier).
> 
> Reasoning:
> - simulate_delay VT-DXA 2026-09-16 +1.5h: pairing P-2203, fdp_after_delay 12.75 vs limit 12.0, legal_leg_count 3, legs_needing_recrew [DX404].
> - All six rostered crew (C-3187, C-5375, C-3211, C-2876, C-1542, C-5089) breach only RULE-FDP-01; RULE-DUTY-02, RULE-FLT-03, RULE-REST-04, RULE-QUAL-05, RULE-CERT-06 all pass.
> - resolve_delay_options ranked reserve re-crew of DX404 first (₹75,000) over cancellation (₹250,000).

## Q34 — C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.

**Expected:** `[{"action": "Assign Cabin Crew C-4809 (reserve callout)", "crew_id": "C-4809", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 9500, "delay_hours": 0.0, "rank": 1}, {"action": "Assign Cabin Crew C-1021 (day-off callout)", "crew_id": "C-1021", "legal": true, "rules_checked": ["RULE-FDP-01", "`

**Answer:**

> **Call out reserve C-4809 (Cabin Crew) to cover C-5417's Cabin Crew slot on P-2213, 2026-09-19 — ₹9,500, 0 delay, all legs covered.** C-5417's recurrent_training is valid_to 2026-09-17, so it is invalid on 2026-09-19 (RULE-CERT-06). Their 2026-09-16 pairing P-2210 is not in scope of this resolution.
> 
> - Uncovered without cover: DX421, DX422, DX423, DX424 on 2026-09-19 — 648 passengers
> - Best option: C-4809, reserve callout, ₹9,500, legal on all seven rules
> - Backups (day-off callout, ₹12,500 each): C-1021, C-1385, C-1414, C-1569, C-1748, C-1873, C-1970
> - Last resort: cancel all 4 legs — ₹1,000,000
> 
> Reasoning:
> - get_certifications C-5417 on 2026-09-19: all_valid false; recurrent_training valid_to 2026-09-17 → RULE-CERT-06 breach.
> - get_pairing P-2213: 2026-09-19, VT-DXB, report 2026-09-19T02:00:00Z, release 13:15:00Z, 11.25 duty hours, 4 sectors, BLR–BLR; C-5417 listed as Cabin Crew.
> - simulate_crew_removal: 4 flights uncovered, 648 passengers, cover_must_take_full_pairing false, rule RULE-QUAL-05 flagged.
> - recommend_cover: 29 candidates; rank 1 C-4809 reserve callout ₹9,500 (on-call 00:00–12:00Z, reachable 45 min); exclusions cite RULE-QUAL-05, RULE-REST-04 and reserve on-call windows 04:00–16:00Z not covering the required report.

## Q35 — BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.

**Expected:** `[{"flight_id": "DX402-2026-09-17", "pairing_id": "P-2204", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew tail legs from reserves or cancel"}, {"flight_id": "DX422-2026-09-17", "pairing_id": "P-2211", "min_delay_hours": 5.75, "crew_fdp_after_delay": 17.0, "fdp_limit": 12.0, "action": "delay exceeds crew FDP \u2014 re-crew `

**Answer:**

> **BLR closed 08:00–14:00Z, 17 Sep — 13 legs, 6 pairings, 1,836 seats exposed. 10 of the 13 legs breach RULE-FDP-01 after minimum delay; those tails need re-crewing from BLR reserves or cancellation.**
> 
> Per pairing:
> - **P-2204** (DX402/403/404) — delays 5.75/5.0/2.25h, FDP 17.0 / 16.25 / 13.5 vs 12.0 limit. All three legs breach. Worst line: re-crew the whole post-reopen tail with a fresh A320 set.
> - **P-2211** (DX422/423/424) — delays 5.75/5.0/1.75h, FDP 17.0 / 16.25 / 13.0 vs 12.0. All three breach; same treatment.
> - **P-2218** (DX433/434) — delays 6.0/2.75h, FDP 15.75 / 12.5 vs 12.0. Both breach; re-crew.
> - **P-2225** (DX453/454, ATR) — DX453 breaches (FDP 14.75 vs 12.0); DX454 at 12.0 = limit, legal. Re-crew DX453 onward with ATR-rated reserves.
> - **P-2293** (DX413/588) — DX413 breaches marginally (12.75 vs 12.5); DX588 legal at 11.75. Only the DX413 leg needs a fresh crew.
> - **P-2232** (DX462) — no breach (11.0 vs 13.0). Delay only, rostered crew continues.
> 
> Cover pool at BLR on 17 Sep — 12 reserves, but on-call windows bind for post-14:00Z reports:
> - A320 pilots: C-3310 (Capt) and C-3311 (FO) to 18:00Z — the only pilot pair covering reports after 15:00Z. C-3312 (FO) ends 12:00, C-3305 (Capt) ends 05:30.
> - ATR pilots: C-3315 (Capt) / C-3316 (FO), window to 15:00Z — tight for P-2225's DX453 (min delay 6.5h).
> - Cabin: C-2111, C-3677 (SCC), C-1329, C-2248, C-5418 (CC) to 16:00Z; C-4809 to 12:00Z.
> 
> Implication: one A320 pilot pair on reserve cannot re-crew three breached A320 lines (P-2204, P-2211, P-2218). Expect day-off callouts (₹24,000/pilot, ₹12,500/cabin) or cancellation (₹250,000/leg) on the lowest-value tails — the ATR legs DX453/454 (72 seats each) are the cheapest to drop versus 162-seat A320 legs.
> 
> Reasoning:
> - station_closure_impact BLR 08:00–14:00Z 2026-09-17: 13 flights, 6 pairings, 1,836 pax, 10 FDP breaches; min delay = reopen +30 min turnaround.
> - RULE-FDP-01 limits vary by sector count (12.0 / 12.5 / 13.0 in this set).
> - list_reserves BLR 2026-09-17 returned 12 reserves with on-call windows; RULE-BASE-07 satisfied (all BLR-based), RULE-QUAL-05 splits A320 vs ATR72 pilots.
> - get_costs for callout/cancellation/delay rates.
> - Not yet run: per-crew legality (RULE-DUTY-02 / REST-04) on the reserves — say the word and I'll run check_assignment_legality per pairing to firm up the assignments.

## Q36 — Draft the callout notification to C-3310 for covering P-2291.

**Expected:** `{"must_include": ["crew_id and pairing_id", "report time/place: 06:00Z 15 Sep, BLR crew room", "flights day 1: DX412/DX413/DX588; overnight DEL (hotel arranged)", "flights day 2: DX589/DX590/DX591, report 04:00Z at DEL", "acknowledgement request with deadline", "contact for questions"]}`

**Answer:**

> Callout drafted for C-3310 (D. Reddy, Captain) on P-2291 (VT-DXC), 2-day pairing, ack by 2026-09-14T18:30:00Z.
> 
> **CALLOUT — Crew ID C-3310 (D. Reddy, Captain) — Pairing ID P-2291**
> You are assigned to pairing P-2291 (VT-DXC) due to crew unavailability.
> - **Day 1 (2026-09-15):** report 06:00Z at BLR crew room; DX412 BLR-BOM 07:00Z-08:45Z, DX413 BOM-BLR 09:30Z-11:15Z, DX588 BLR-DEL 12:15Z-15:00Z; release 15:30Z. Overnight at DEL — hotel arranged.
> - **Day 2 (2026-09-16):** report 04:00Z at DEL crew room; DX589 DEL-BLR 05:00Z-07:45Z, DX590 BLR-CCU 08:30Z-11:00Z, DX591 CCU-BLR 11:45Z-14:15Z; release 14:45Z.
> - **Acknowledge by 2026-09-14T18:30:00Z (30 min): reply ACK P-2291.**
> - Contact: Crew Control desk, BLR.
> 
> Reasoning:
> - draft_callout_notification for C-3310 on P-2291 returned both duty days with report/release times, flights, DEL overnight with hotel arranged, ack deadline and contact.
> - Legality of this assignment not re-checked here — run check_assignment_legality (RULE-FDP-01, RULE-REST-04, RULE-QUAL-05) before releasing if not already done.

## Q37 — What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?

**Expected:** `{"action": "Assign First Officer C-3316 (reserve callout)", "crew_id": "C-3316", "legal": true, "rules_checked": ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03", "RULE-REST-04", "RULE-QUAL-05", "RULE-CERT-06", "RULE-BASE-07"], "cost_inr": 18500, "delay_hours": 0.0, "rank": 1}`

**Answer:**

> Call out reserve FO **C-3316** — ₹18,500, legal, zero delay, covers both legs.
> 
> - Pairing P-2235 (VT-DXF, 20 Sep), FO C-4520 (R. Sharma) out; report 04:00Z, DX461/DX462, 144 pax.
> - C-3316: BLR-based, ATR72-rated, on-call 03:00–15:00Z, reachable in 45 min.
> - Next best: day-off callouts C-1313 / C-1317 / C-2085 / C-3057 at ₹24,000 each. Cancellation of both legs would cost ₹500,000.
> 
> Reasoning:
> - find_pairings VT-DXF on 2026-09-20 → single pairing P-2235 with FO C-4520.
> - recommend_cover (C-4520, P-2235, reported 03:30Z) → 26 candidates, 6 options; rank 1 = reserve callout C-3316, all seven rules pass (RULE-FDP-01, DUTY-02, FLT-03, REST-04, QUAL-05, CERT-06, BASE-07).
> - 21 candidates excluded mainly on RULE-QUAL-05 (no ATR72 rating); C-3136 excluded on RULE-REST-04.

## Q38 — If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?

**Expected:** `{"suggested": ["crew legality headroom (7d duty) for today's rostered crew", "reserve availability by window and rating for the day", "risk_signals for today's rostered crew (provided input)"], "note": "Open-ended; judged on operational reasoning, not exact match."}`

**Answer:**

> Three per line, exactly what `morning_briefing` surfaces:
> 
> - **Tightest 7-day duty headroom on the line** (plus cert validity flag) — tells you which line is closest to a RULE-DUTY-02 (60h/7d) / RULE-CERT-06 stop before any disruption. E.g. VT-DXA is tightest at 27.83h (C-3988); VT-DXF loosest at 34.90h.
> - **Highest disruption-risk score among the rostered crew** — the provided signal for who is most likely to go sick/no-show. VT-DXC 0.78 (C-1042), VT-DXA 0.71 (C-3940), VT-DXB 0.69 (C-1938).
> - **Eligible reserves at that line's report time** — cover depth if the risk lands, already filtered for on-call window, rating (RULE-QUAL-05) and base (RULE-BASE-07). Thin at the early reports: VT-DXA/B/D report 01:30–02:30Z with only 3 eligible each; VT-DXC at 06:00Z has 9.
> 
> Read together they give risk × exposure × cover: a line with tight headroom, a high-risk crew member and only three eligible reserves (VT-DXA) is the one to pre-plan.
> 
> Reasoning:
> - `morning_briefing` for 2026-09-15 returned 6 aircraft lines with pairing, report time, per-crew 7d duty hours/headroom, cert validity, risk scores and eligible reserves at report.
> - Its own `surfaced` list names the same three: legality headroom, reserve availability by window/rating, risk signals.
> - Rules in play: RULE-DUTY-02, RULE-CERT-06, RULE-QUAL-05, RULE-BASE-07.
