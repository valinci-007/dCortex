---
marp: true
theme: default
paginate: true
title: Crew Ops Advisor — dCortex hackathon
---

# Crew Ops Advisor
## AI-driven operational superintelligence for airline Crew Control

**Team:** Rajesh · Syed Maaz · (3rd) — dCortex hackathon, September 2026

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
          33 typed tools ─► rules engine (7 pure functions → evidence)
                         ─► simulations · option ranking · cost model
                         ─► SQLite built from the provided dataset
```

- Claude Code's built-in tools are **disabled**; our registry is exposed as an in-process
  MCP server. The model can call exactly our tools and nothing else.
- Every rule returns **evidence**: inputs, computed value, limit, margin, a human detail.
- A **grounding check** verifies every id, date and figure in the answer against tool
  evidence — one rewrite, then a visible warning.

---

# What it answers

**Tier 1 — lookups.** Reserves, duty clocks and headroom, flights, pairings, certifications,
risk signals, rules, costs.

**Tier 2 — consequences.** Sick call → uncrewed legs, at-risk legs, passengers. Substitution
→ all seven rules with the numbers. Station closure → every affected leg, minimum delay, crew
FDP after it. Delay → FDP after delay, legal prefix of legs. Crew near limits. Reserve
coverage for a callout time.

**Tier 3 — recommendations.** Ranked covers with cost, delay, coverage, reasoning and every
excluded candidate with its reason. Joint plans (nobody assigned twice, cheapest total).
Delay recovery. Callout notification drafts. Morning briefing.

---

# Results against the dataset's own answer keys

| | Automated recall | Human review | p50 latency |
|---|---|---|---|
| Tier 1 (16) | model **16/16** · offline 16/16 | all correct | 7.0 s · <5 ms |
| Tier 2 (14) | model **14/14** · offline 14/14 | all correct | 9.7 s · 1 ms |
| Tier 3 (8) | model 4–7/8 · offline 7/8 | all correct | 14 s · 6 ms |

- Scenarios S1, S2, S4, S6 reproduced **exactly** (options, costs, exclusions, reasons).
- The whole roster evaluates legal except the one flagged exception — parity with the
  organiser's validator.
- Estimated model cost per full Tier-1 eval: **$0.43**; ~3¢ per question with caching.

---

# Live demo

1. "Who's on reserve at BLR tomorrow?" — Tier 1, one tool, reasoning trail.
2. "If Captain C-2087 covers P-2291 from 15 Sep, does any rule breach?" — RULE-DUTY-02 by
   1h20m, with the window, the total, the margin.
3. "Captain C-1042 is out — what should I do?" — ranked covers: C-3310 ₹18,500 → day-off
   callouts ₹24,000 → deadhead ₹41,200 with 3 h delay → cancel ₹15,00,000; who was excluded
   and why.
4. "Draft the callout notification to C-3310." — every time and station from the roster.
5. "Will fog delay BLR tomorrow?" — **"I can't answer that reliably."**
6. Pull the network: the same question answered by the offline router, labelled.

---

# Where it is weak — and we say so

- **Tier-3 latency** 14–42 s with three or four tool calls: inside the 45 s bar, outside
  our 8 s target. Tool time is milliseconds; the cost is model turns.
- **Grounding is strict**: it flagged a *correct* derived sum (₹37,000) and forced a
  rewrite. We accept false positives over a fabricated figure.
- **Partial covers of multi-day pairings** are legality-checked but not costed for
  repatriation.
- **Two answer keys we deliberately don't match**: S5 lists a pairing's own crew as covers;
  Q33's 3-leg FDP contradicts its own 4-leg computation. Recorded, tested, explained.
- **The offline router is closed-world** — it answered "book a hotel for C-1042" with a
  profile until we added a guard. It is insurance, not the product.

---

# Engineering judgement

- Docs-first: three architectures, rubric matrix, 13 ADRs including what we skipped and why.
- Foundation up with exit gates: P0 rules engine → P1 tools + agent → P2 simulations →
  P3 UI + grounding → P4 ranking. No tier started before the previous gate was green.
- 178 tests pin the engine to the answer keys and the roster to the validator.
- Provider is a config switch: Agent SDK (default), Client SDK, offline. Automatic fallback.
- Eval harness grades recall of facts and writes every answer to a report — no LLM judge
  on a determinism claim.

---

# Production path

- **PII:** the model never needs names — tools return ids, the UI joins names from an
  authorised directory; redaction, audit logs (the trace already exists), residency.
- **Scale:** the model sees tool results, not the dataset; SQLite becomes the crew-tracking
  and roster systems behind the same repository interfaces; the core is stateless.
- **Latency:** stream partial answers; cap tool-result size on Tier 3; effort tuning.
- **Business impact:** minutes → seconds per disruption, every decision auditable, the
  cheapest legal option visible next to the ones that were excluded and why.

---

# Thank you

Repository: github.com/valinci-007/dCortex

`docs/architecture.md` · `docs/decisions.md` · `docs/failure-cases.md` · `evals/reports/`
