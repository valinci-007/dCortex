# Demo script

Built for a **5-minute live demo** inside a 10-minute slot. Beats 1–3 are the whole thesis and
must be shown; beats 4–7 are held in reserve for a longer slot or for judges' questions.

## Before you present

```bash
make run                      # builds the DB + frontend, serves API and UI on :8000
```

- Open **http://127.0.0.1:8000**. If port 8000 is taken:
  `cd backend && .venv/bin/crew-ops serve --port 8010` and use that URL everywhere below.
- Start the server with PII mode on so beat 5 is available without a restart:
  `CREW_OPS_PII_MODE=minimal make serve` — the header then shows a green **PII: minimal** badge.
- Keep the **server console visible on a second screen or window**. It is the audit trail, and
  it is the proof for beat 5.
- Keep a spare terminal ready with `cd backend && .venv/bin/crew-ops chat --provider offline`
  for the fallback beat.
- Do one full dry-run on the presenting machine and note the real latencies. Numbers below are
  from the 2026-09-04 dry-run with the Agent SDK provider.

---

## The core — always show these three

| # | Say | Type | What to point at | Time |
|---|---|---|---|---|
| 1 | "Legality is exact arithmetic — and none of it is done by the model." | `If Captain C-2087 covers P-2291 from 15 Sep, does any rule breach?` | RULE-DUTY-02 breached by **1h20m** on 15 Sep (61.33 h vs 60 h) and 1h05m on 16 Sep. Seven verdicts, each with its margin. Open the **reasoning trail** and the tool-result JSON: the model asked, the rules engine computed. | ~10 s |
| 2 | "Now the recommendation — ranked, costed, and it tells you who was ruled out." | `Captain C-1042 is out — what should I do?` | Steps **stream as they run** in the controller's own words ("ranking cover options for P-2291"), then the answer writes itself. C-3310 reserve ₹18,500 → three day-off callouts ₹24,000 → C-2210 deadhead ₹41,200 + 3 h delay → cancel ₹15,00,000. Excluded: C-2087 (DUTY-02), C-3305 (window), C-3315 (rating), C-5837 (rest). | ~15–30 s |
| 3 | "And when it isn't sure, it says so." | `Will fog delay BLR tomorrow?` | **"I can't answer that reliably"** — no tool covers forecasts; it names the nearest supported question. The brief says a refusal beats a wrong answer; this is that, by construction. | ~5 s |

**End the demo on beat 3.** The refusal is the strongest note, not the weakest.

---

## Held in reserve — for a longer slot or for questions

| # | Say | Type / do | What to point at | Time |
|---|---|---|---|---|
| 4 | "Consequence, not just lookup." | `Captain C-1042 calls in sick at 05:00Z on 15 Sep for P-2291 — which flights are uncrewed?` | DX412/413/588 uncrewed now, 486 pax; DX589/590/591 at risk tomorrow; "the cover must take the full remaining pairing" | ~9 s |
| 5 | "Crew data is health data. Watch what the model actually receives." | Point at the **server console** during any question | The audit trail: system prompt, the question **as typed** and **as sent**, every tool result **before and after** the scrub. Names are gone; the model sees `C-1042`. The browser joins the name back. This is the PII claim, verifiable live. | ~20 s |
| 6 | "It drafts the callout from the roster — every time and station is a fact." | `Draft the callout notification to C-3310 for covering P-2291.` | Day 1 report 06:00Z BLR, overnight DEL hotel, day 2 report 04:00Z DEL, acknowledgement deadline, contact | ~10 s |
| 7 | "And if the model is gone —" (switch to the offline terminal, or pull the network) | `Which crew have 45 or more duty hours in the 7 days ending 2026-09-15?` | Same tools, labelled **"offline mode"**: C-2087 51.83 h and C-3305 50.0 h, in 1 ms. In the browser the answer comes back with the amber "Model provider failed … answered by the offline router" notice. | instant |
| 8 | "A controller can talk to it, and the conversation persists." | Mic button; then reopen a chat from the sidebar | Speech transcribed on-device (Whisper) into the composer; earlier chats resume with their context | ~15 s |

---

## If something goes wrong

- **Model slow (> 30 s):** you now have something to show — point at the streaming steps:
  "each of those is a deterministic tool call finishing in milliseconds; the time is model
  turns, and it is our known weakness on Tier 3."
- **Grounding warning appears:** it is a feature — read the flagged figure aloud; it is usually
  a correct derived sum. Say why we prefer a false positive to a fabricated figure
  (`docs/failure-cases.md` case 1).
- **Provider error:** the answer will already have fallen back to the offline router with an
  amber notice. Carry on — that *is* beat 7, arriving early.
- **Nothing works:** `cd backend && .venv/bin/crew-ops ask "…" --provider offline` in the terminal.

## Questions judges may ask, and the short answer

- *Why not put the data in the prompt?* Works for lookups, fails at legality: exact arithmetic
  against a rulebook. The model here never sees the dataset, only tool results.
- *What generalises to held-out scenarios?* The tools, not intents: any new phrasing is a new
  plan over the same 38 tools. The offline router is the closed-world contrast — and it is
  labelled as such whenever it answers.
- *How do you know the model isn't doing the maths?* The audit console shows every tool result
  going in and the answer coming out; the grounding check rejects any figure that is not in the
  evidence.
- *What's wrong with it?* `docs/failure-cases.md` — Tier-3 latency, strict grounding, partial
  covers of multi-day pairings, and two answer keys we deliberately disagree with.
- *Where's the PII?* Beat 5. `CREW_OPS_PII_MODE=minimal`, names never leave the machine.
- *Cost?* ~3¢ per Tier-1 question with prompt caching; $0.43 for the whole Tier-1 eval.
- *What's next?* ADR-0018: a deterministic proactive watchlist, a scenario workspace for chained
  disruptions, graded confidence per answer and per option.
