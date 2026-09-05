---
marp: true
theme: default
paginate: true
title: Crew Ops Advisor — dCortex hackathon
---

<!--
Running order — built for a 10-minute slot: ~3 min slides, ~5 min demo, ~2 min Q&A.
  1  Cold open (no slide, 30 s) — say the 5 a.m. scenario out loud, then the arithmetic line.
  2  Slides 2–5 (90 s) — problem, the architectural question, the boundary, what it answers.
  3  DEMO (5 min) — switch to the app. Slide 6 is the running order; see docs/demo.md.
  4  Slides 7–10 (90 s) — results, trust, weaknesses, production path.
  5  Slide 11 only if asked about process.
If the slot is 5 minutes: keep 2, 4, 6 (demo beats 1–3 only), 9, 10. Drop 3, 5, 7, 11.
-->

# Crew Ops Advisor
## AI-driven operational superintelligence for airline Crew Control

**Team:** Rajesh Tippana · Syed Maaz · Uma Shankar — dCortex hackathon, September 2026

> The best submission will be the one a real crew controller would want beside them at
> 6 a.m. on a bad day — because it is fast, because it is right, and because when it isn't
> sure, it says so.

---

# The problem

- A captain calls in sick at 5 a.m. Which flights break? Who can legally take them? What
  does it cost? Who else breaks tomorrow because of the fix?
- Today that reasoning lives in one senior controller's head, across six screens and a
  rulebook. It is slow to learn, impossible to scale, and worst under pressure.
- **Legality is exact arithmetic.** An LLM that approximates a duty-hour sum is fluent,
  confident and wrong — operationally worse than no answer.

---

# The central question is architectural

*What should the language model do, what should deterministic code do, and how do you
compose them?*

We wrote three candidates down, scored them against the rubric, and chose:

| | Tool agent (A) | NL→SQL (B) | Intent router (C) |
|---|---|---|---|
| AI Utilization 20% | strong | blurry | "decorated lookup" |
| Correctness | tools own all math | silent wrong SQL | strong but closed-world |
| Held-out questions | generalises | partial | refuses the unanticipated |

**Chosen: A, hardened with C's refusal discipline + offline router and B's reasoning trace.**

---

# Where the boundary is

```
controller ─► orchestrator ─► Claude (Agent SDK) — plans, narrates, never computes
                   │  ▲   typed tool calls / JSON evidence — the only crossing
                   ▼  │
          35 typed tools ─► rules engine (7 pure functions → evidence)
                         ─► simulations · option ranking · cost model
                         ─► SQLite built from the provided dataset
```

- Claude Code's built-in tools are **disabled**; our registry is exposed as an in-process
  MCP server. The model can call exactly our tools and nothing else.
- Every rule returns **evidence**: inputs, computed value, limit, margin, a human detail.
- A **grounding check** verifies every id, date and figure in the answer against tool
  evidence — one rewrite, then a visible warning.

---

# What it answers — 35 typed tools

**Tier 1 — lookups (17 tools).** Reserves, duty clocks and headroom, flights, routes,
pairings, certifications, risk signals, rules, costs.

**Tier 2 — consequences (10 tools).** Sick call → uncrewed legs, at-risk legs, passengers.
Substitution → all seven rules with the numbers. Station closure → every affected leg,
minimum delay, crew FDP after it. Delay → FDP after delay, legal prefix of legs. Crew near
limits. Reserve coverage for a callout time.

**Tier 3 — recommendations (8 tools).** Ranked covers with cost, delay,
coverage, reasoning, the tightest rule headroom each leaves, and every excluded candidate
with its reason. Joint plans (nobody assigned twice, cheapest total). Delay recovery.
Callout drafts. Morning briefing and a proactive watchlist. **Positioning cover**: when
nobody local can take a duty on time, who elsewhere — per the roster — can be flown in
before the departure, any itinerary, seven rules, costed. Read-only throughout: what-ifs are
questions; the controller decides and acts in the desk's own systems.

---

# Live demo

1. **"If Captain C-2087 covers P-2291 from 15 Sep, does any rule breach?"**
   RULE-DUTY-02 by 1h20m — the window, the total, the margin. *None of it computed by the model.*
2. **"C-1042 called in sick from tomorrow — record it. What should I do?"**
   Ranked: C-3310 ₹18,500 → day-off callouts ₹24,000 → deadhead ₹41,200 + 3 h delay →
   cancel ₹15,00,000. Plus who was **excluded and why**. Watch the steps stream as they run.
3. **"Captain C-2210 in DEL is also out — who covers P-2291's DEL day on 16 Sep?"**
   No legal on-time cover at DEL: the ranking escalates to positioning — DX588 the evening
   before with a hotel, ₹29,200, on time, cheaper than the delayed deadhead.
4. **"Will fog delay BLR tomorrow?"** → **"I can't answer that reliably."**

*Held in reserve:* the watchlist on the home screen (a training lapse two days before a
rostered duty), the PII audit console (names never reach the model), the offline router
answering the same chain with the network pulled, voice input, persistent chats.

---

# Results against the dataset's own answer keys

| | Model (Agent SDK) | Offline router | p50 latency |
|---|---|---|---|
| Tier 1 (16 Q) | **16/16** | 16/16 | 6.8 s · < 1 ms |
| Tier 2 (14 Q) | **14/14** | 14/14 | 9.7 s · 1 ms |
| Tier 3 (8 Q) | **7/8** automated · **8/8 on human review** | 7/8 | 13 s · 6 ms |

- Offline router, all 38 questions, re-run today: **37/38** — the one miss is the answer
  key we disagree with (Q33, below).
- Latest full three-tier run (`tier123-agent-sdk-v6`): **16/16 · 14/14 · 7/8**, **zero
  correction turns**, every answer verified on the first pass, p50 8.4 s / p95 15.0 s. It
  started the day at 3/8 on Tier 3 with four correction turns: rotations written
  "DX402/403/404", ₹2,50,000 read as "50000", the controller's own "00:30Z on 18 Sep" not
  recognised — all fixed in our checks, not by tuning the model. We report every run.
- Scenarios S1, S2, S4, S6 reproduced **exactly** (options, costs, exclusions, reasons).
- The whole roster evaluates legal except the one flagged exception — parity with the
  organiser's validator.
- ~3¢ per Tier-1 question with caching; **$0.43** for the whole Tier-1 eval.

---

# Trust is built in, not asserted

- **Refusal is a feature.** No tool covers weather, bookings, HR — it declines and names the
  nearest supported question. A wrong answer at a crew desk is worse than no answer.
- **Grounding check.** Every id, date and figure in the answer must appear in tool evidence.
  One rewrite, then a visible "unverified figures" badge.
- **PII minimisation** (`CREW_OPS_PII_MODE=minimal`). The model never sees a crew name — ids
  only; the browser joins names from a local directory. Medical dates are health data.
- **Audit console.** Every system prompt, every question as typed *and as sent*, every tool
  result **before and after** the scrub, printed to the server console. Verifiable live.
- Model sandboxed to our 35 tools · fully local · speech on-device · chats deletable.
- **Confidence on every answer** — verified · verified after correction · unverified ·
  declined — and the tightest rule headroom on every ranked option.

---

# Where it is weak — and we say so

- **Tier-3 latency** 12–30 s with three or four tool calls. Tool time is milliseconds; the
  cost is model turns. Mitigated, not solved: we now **stream** each tool step in the
  controller's words and the answer as it is written, so the wait is legible rather than blank.
- **Grounding is strict**: it flagged a *correct* derived sum (₹37,000) and forced a
  rewrite. We accept false positives over a fabricated figure.
- **Partial covers of multi-day pairings** are legality-checked but not costed for
  repatriation.
- **Two answer keys we deliberately don't match**: S5 lists a pairing's own crew as covers;
  Q33's 3-leg FDP contradicts its own 4-leg computation. Recorded, tested, explained.
- **The offline router is closed-world** — it answered "book a hotel for C-1042" with a
  profile until we added a guard. It is insurance, not the product.

---

# Production path

- **Scale:** the model sees tool results, not the dataset; SQLite becomes the crew-tracking
  and roster systems behind the same repository interfaces; the core is stateless.
- **Latency:** streaming shipped; next is capping Tier-3 evidence sent to the model and effort
  tuning per tier.
- **Scenario depth:** delays and station closures as persistent state; per-line undo;
  repatriation costed.
- **Production adds:** role-based access, retention policy, redaction at rest.
- **Business impact:** minutes → seconds per disruption, every decision auditable, the
  cheapest legal option visible next to the ones that were excluded and why.

---

# How we worked

- Docs-first: three architectures, a rubric matrix, **21 ADRs** including what we skipped
  and why.
- Foundation up with exit gates: P0 rules engine → P1 tools + agent → P2 simulations →
  P3 UI + grounding → P4 ranking. No tier started before the previous gate was green.
- **264 tests** pin the engine to the answer keys and the roster to the organiser's validator.
- Provider is a config switch: Agent SDK (default), Client SDK, offline. Automatic fallback.
- Eval harness grades recall of facts and writes every answer to a report — no LLM judge
  on a determinism claim.

---

# Thank you

Repository: github.com/valinci-007/dCortex

`docs/architecture.md` · `docs/decisions.md` · `docs/failure-cases.md` · `evals/reports/`
