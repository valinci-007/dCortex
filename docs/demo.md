# Demo script (≈ 6 minutes)

Dry-run on 2026-09-04 with the Agent SDK provider; timings are from that run. Start the
server before the session (`make serve` from the repo root) and open http://127.0.0.1:8000.
Keep a terminal with `cd backend && .venv/bin/crew-ops chat --provider offline` ready for the fallback beat.

| # | Say | Type / click | What to point at | Time |
|---|---|---|---|---|
| 1 | "A controller asks in plain language; the model plans tool calls, deterministic code computes." | `Who's on reserve at BLR tomorrow?` | 12 reserves, windows in UTC; open the **reasoning trail**: one tool call `list_reserves(station=BLR, date=2026-09-15)`, 0.3 ms; green **grounded · N facts** badge | ~7 s |
| 2 | "Legality is exact arithmetic — none of it is done by the model." | `If Captain C-2087 covers P-2291 from 15 Sep, does any rule breach?` | RULE-DUTY-02 by **1h20m** on 15 Sep (61.33 h vs 60 h) and 1h05m on 16 Sep; the seven verdicts with margins; open the tool result JSON | ~10 s |
| 3 | "Consequence, not just lookup." | `Captain C-1042 calls in sick at 05:00Z on 15 Sep for P-2291 — which flights are uncrewed?` | DX412/413/588 now, 486 pax; DX589/590/591 at risk; "cover must take the full pairing" | ~9 s |
| 4 | "Now the recommendation — ranked, costed, with who was excluded and why." | `Captain C-1042 is out — what should I do?` | C-3310 reserve ₹18,500 → three day-off callouts ₹24,000 → C-2210 deadhead ₹41,200 + 3 h delay → cancel ₹15,00,000; excluded: C-2087 (DUTY-02), C-3305 (window), C-3315 (rating), C-5837 (rest) | ~15–30 s |
| 5 | "It drafts the callout from the roster — every time and station is a fact." | `Draft the callout notification to C-3310 for covering P-2291.` | Day 1 report 06:00Z BLR, overnight DEL hotel, day 2 report 04:00Z DEL, ack deadline, contact | ~10 s |
| 6 | "When it isn't sure, it says so." | `Will fog delay BLR tomorrow?` | "I can't answer that reliably" — no tool covers forecasts; nearest supported question | ~5 s |
| 7 | "And if the model is gone —" (switch to the offline terminal) | `Which crew have 45 or more duty hours in the 7 days ending 2026-09-15?` | Same tools, labelled "offline mode", C-2087 51.83 h and C-3305 50.0 h, in 1 ms | instant |

Fallback beat alternative: stop the network and re-ask question 1 in the web UI — the answer
comes back with the amber "Model provider failed … answered by the offline router" notice.

## If something goes wrong

- **Model slow (> 30 s):** say "Tier-3 questions run 15–40 s — our known weakness — the
  tools took milliseconds; the time is model turns" and show the trace timings.
- **Grounding warning appears:** it is a feature — read the flagged figure; usually a derived
  sum. Say why we prefer a false positive to a fabricated figure.
- **Provider error:** the answer will already have fallen back to offline mode; continue.
- **Nothing works:** `cd backend && .venv/bin/crew-ops ask "…" --provider offline` in the terminal.

## Questions judges may ask, and the short answer

- *Why not put the data in the prompt?* Works for lookups, fails at legality: exact
  arithmetic against a rulebook. The model here never sees the dataset, only tool results.
- *What generalises to held-out scenarios?* The tools, not intents: any new phrasing is a
  new plan over the same 33 tools; the offline router is the closed-world contrast.
- *What's wrong with it?* `docs/failure-cases.md` — latency on Tier 3, strict grounding,
  partial covers, two answer keys we disagree with.
- *Cost?* ~3¢ per Tier-1 question with prompt caching; $0.43 for the whole Tier-1 eval.
