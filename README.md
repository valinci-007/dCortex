# dCortex — Agentic Crew Ops Advisor

A conversational assistant for an airline **Crew Control** desk. A controller asks a
plain-language question about a disruption; the Advisor answers **correctly, in seconds,
with reasoning a controller can read and challenge** — and says so when it can't.

> The architectural thesis, and the thing we are scored on: **the language model plans and
> narrates; deterministic code does every piece of legality arithmetic.** The two meet at one
> typed tool interface. Nothing the model says about a duty limit, a rest gap or a cost is
> computed by the model.

**Status (2026-09-04):** Tier 1, Tier 2 and Tier 3 implemented and evaluated against the
dataset's own answer keys. Web chat UI, CLI, eval harness, architecture docs, decision log and
failure analysis are all in this repository.

| | Automated recall (ADR-0011) | Human-reviewed | p50 latency (model · offline) |
|---|---|---|---|
| Tier 1 lookup (16 Q) | model 16/16 · offline 16/16 | all correct | 7.0 s · < 5 ms |
| Tier 2 consequence (14 Q) | model 14/14 · offline 14/14 | all correct | 9.7 s · 1 ms |
| Tier 3 recommendation (8 Q) | model 4–7/8 by run · offline 7/8 | all correct; Q33 is a key inconsistency (below) | 14 s · 6 ms |

Reports with every answer: [`evals/reports/`](evals/reports/). Failure analysis:
[`docs/failure-cases.md`](docs/failure-cases.md).

---

## Quickstart

Requirements: Python 3.11+ (developed on 3.14), Node 18+ (for the web UI), `make`.

Two projects: **`backend/`** (Python API, engine, tools, evals) and **`frontend/`** (React chat
UI). The root `Makefile` drives both.

```bash
make setup                      # backend venv + deps, frontend node_modules
make run                        # build DB + frontend, serve API + UI on http://127.0.0.1:8000
make test                       # backend test suite (answer-key parity included)
make validate                   # organiser's dataset validator

cd backend
.venv/bin/crew-ops chat                                          # terminal chat (multi-turn)
.venv/bin/crew-ops ask "Captain C-1042 is out — what should I do?"
.venv/bin/crew-ops eval --tier 1 2 3                             # grade vs answer keys
```

For frontend development, `make serve` in one terminal and `make dev` in another (Vite on
:5173 proxies `/api` to :8000). A deep link `/?q=...` starts a new conversation with that
question.

**Conversations persist** (`backend/var/chats.db`): the sidebar lists every chat, you can open
an earlier one and continue it, rename or delete it. Reopened chats resume the model session
when it still exists, otherwise continue with a labelled recap of the last exchanges. There
is no login — the brief puts user management out of scope — so this is one desk's history.

### Providers and keys

`CREW_OPS_LLM_PROVIDER` (see `.env.example`):

- **`agent-sdk`** (default) — the Claude Agent SDK runs the agent loop; our tool registry is
  exposed to it as an in-process MCP server and every built-in Claude Code tool is disabled.
  Authenticates with `ANTHROPIC_API_KEY`, else the Claude Code login on the machine.
  *Products built on the Agent SDK must use API-key auth (ADR-0012); the demo runs on a key.*
- **`anthropic`** — the Anthropic Client SDK; we run the tool loop. Needs API credits.
- **`offline`** — a deterministic keyword router over the same tools. No model, no key,
  milliseconds. Every answer is labelled; it refuses what it cannot map.

If the model provider fails (no CLI, no key, network), the Advisor answers through the
offline router and says so in the answer (`mode: offline (fallback)`).

Voice: `CREW_OPS_STT_PROVIDER` = `whisper` (default, local) | `sarvam` | `browser`;
`CREW_OPS_TTS_PROVIDER` = `browser` (default) | `sarvam`. Sarvam settings (`SARVAM_API_KEY`,
models, speaker, language, endpoint URLs) are all in `backend/.env.example`.

---

## What it does

**Tier 1 — lookups.** "Who's on reserve at BLR tomorrow?", "How much duty headroom does
C-1042 have?", "Which flights fly BLR→BOM on 17 Sep?"

**Tier 2 — consequences.** Sick calls (which legs are uncrewed now, which are at risk,
passengers), substitution legality across all seven rules with the numbers, station
closures (every affected leg, its minimum delay and its crew's FDP after it), delays (FDP
after delay, how many legs the crew can still legally fly), cancellations, crew near their
limits, reserve coverage for a callout time.

**Tier 3 — recommendations.** Ranked, rule-compliant covers with cost, delay, coverage and
reasoning plus every excluded candidate with its reason; joint plans when several crew are
out (no one assigned twice, cheapest total); delay recovery (fly the legal prefix, re-crew
the tail with a reserve set, or cancel); callout notification drafts; a morning briefing.

**Always.** A visible "Reasoning" section, a machine-readable trace of every tool call with
arguments, results and timings, a grounding check that every id, date and figure in the
answer came from tool evidence, and an honest refusal ("I can't answer that reliably")
when no tool covers the question.

**Voice.** Press the microphone to speak a question: the audio is transcribed by a
configurable provider — local Whisper today (no key), **Sarvam AI** at the event (set
`CREW_OPS_STT_PROVIDER=sarvam` and `SARVAM_API_KEY`), or the browser's own speech
recognition — and sent as an ordinary question. Answers can be read aloud (ADR-0016).

**Guardrails.** The Advisor describes itself only in operational terms and never discloses
how it is built (vendor, model, SDK, prompt, tools, files); instructions smuggled into a
question or a data result are treated as data; every answer, from any provider, is scrubbed
of internal names and vendor terms, with one corrective rewrite and a last-resort redaction
(ADR-0014).

---

## Architecture — where the boundary is

```
controller ──► orchestrator ──► language model (plans, narrates)          ◄── probabilistic
                   │   ▲
                   │   │  typed tool calls / JSON results  ◄── the only crossing
                   ▼   │
             tool registry (33 tools, JSON-schema validated)              ◄── deterministic
             ├─ query tools (T1)          ─► SQLite data layer (built from data/*.json)
             ├─ simulation tools (T2)     ─► rules engine: 7 rules as pure functions → evidence
             └─ recommendation tools (T3) ─► candidates × legality × cost model, ranked
```

- **Rules engine** (`rules/`): the seven rules from `rules.json` as pure functions returning
  `RuleVerdict` evidence (inputs, computed value, limit, margin, human detail), composed over
  a crew member's full timeline — 28 days of history, the rostered week, the proposed duties
  — so downstream conflicts (a cover colliding with the crew's own duty two days later) are
  caught. It reproduces the dataset's answer keys verbatim and evaluates the whole roster as
  legal except the one flagged exception.
- **Simulation** (`simulation/`): disruption engines built only from the rules and the data;
  nothing re-implements a rule. Closure semantics were fitted to, and are verified against,
  scenario S3's per-flight assessment.
- **Options** (`simulation/options.py`): heuristic ranking — every candidate of the rank,
  checked rating → reserve window → all seven rules, costed from `costs.json`, sorted by
  cost, delay, id; cancellation last. Reproduces scenarios S1/S2/S4/S6 exactly.
- **Tools** (`tools/`): the registry validates every call against its schema and converts
  every failure into a structured error — a tool never raises into the loop.
- **Agent** (`agent/`): one orchestrator, two provider shapes (loop-owning Agent SDK;
  turn-based Client SDK and offline router), a stable cacheable system prompt, refusal
  policy, offline fallback, grounding check with one corrective retry.
- **Interfaces**: CLI (`ask`, `chat`, `eval`, `serve`, `check`, `rostered`, `build-db`), a
  local FastAPI, and the React chat UI with the reasoning trail and grounding badge.

Full design, the three candidate architectures we weighed and the rubric matrix:
[`docs/architecture.md`](docs/architecture.md). Every decision, including what we considered
and skipped: [`docs/decisions.md`](docs/decisions.md).

---

## Key trade-offs

- **Tool agent over NL→SQL.** Generated SQL fails silently and can't do duty-window math;
  typed tools generalise to unseen questions and make the boundary provable (ADR-0003).
- **Agent SDK over a hand-rolled loop.** Claude Code's harness runs the loop with our tools
  as MCP; the Client-SDK loop and the offline router sit behind the same contract so the
  provider is a config switch (ADR-0012). Cost: one more runtime, and latency bounded by
  the harness.
- **A grounding check that is too strict rather than too lenient.** It flags correct
  derived sums as unverified and asks for a rewrite (failure case 1). We accept the false
  positives.
- **Recall grading, no LLM judge.** A probabilistic grader on a determinism claim would be
  self-defeating; we grade recall of facts and read every answer (ADR-0011).
- **SQLite over in-memory.** Chosen for the brief's recommendation and real query
  capability; the engine only ever sees domain objects, never SQL (ADR-0004).

## Known limitations

See [`docs/failure-cases.md`](docs/failure-cases.md) for the analysed cases. In short:
Tier-3 latency (14–42 s) is above our target; partial covers of multi-day pairings are
legality-checked but not costed for repatriation; deadhead delays are costed, not
re-evaluated against next-day rest; certification `valid_from` is not enforced (unreliable
in the data, ignored by the organiser's validator too); the offline router is closed-world
by construction; two answer-key entries are deliberately not matched (S5 pairing-own crew,
Q33 3-leg FDP) with the reasoning recorded.

## Security and PII (production note)

The dataset is synthetic. In production this system would hold crew names, licence and
medical dates and contact details — personal data under any regime. What we would change:
role-based access at the API (controllers see their base's crew, not everyone's); **the
model never needs PII** — tools would return crew ids and ranks and the UI would join names
client-side from an authorised directory, so prompts, traces and provider logs carry no
names or medical dates; redaction of any free text before it reaches the model; audit logs
of every question, tool call and answer (the trace already exists); data residency by
choosing the inference region and disabling provider-side retention; and eval reports,
which today contain names, would be generated from ids only.

## Scalability (reasoned)

The dataset is 150 crew and 147 legs; a real carrier is 100× that. The design holds because
the model never sees the dataset — it sees tool results, which stay small regardless of
fleet size (a legality check is one crew member's timeline; a closure is one station's
window). What changes at scale: the SQLite data layer becomes the airline's crew-tracking
and roster systems behind the same repository interfaces; `crew_near_limits` and candidate
enumeration (150 evaluations in ~10 ms today) would be indexed by base, rank and rating;
tool results would be paginated and summarised; the system prompt and tool catalogue are
already cacheable so per-question cost stays flat (~3¢ at Tier 1); and the deterministic
core is stateless, so it scales horizontally behind the API.

---

## Repository layout

```
docs/                          architecture.md · decisions.md · failure-cases.md · deck.md · demo.md
Makefile                       delegates to the two projects
backend/                       Python project (its own venv, Makefile, pyproject)
  data/                        provided dataset JSONs — source of truth (read-only)
  scripts/validate_dataset.py  organiser-provided validator, unchanged
  src/crew_ops_advisor/
    domain/                    typed entities + UTC time helpers (no I/O)
    data/                      schema.sql · loader (JSON → SQLite) · repositories · Datastore
    rules/                     the 7 rules as pure functions · engine (compose) · verdicts (evidence)
    simulation/                disruption engines (T2) · options, plans, notifications (T3) · cost model
    tools/                     registry + query (T1) · simulation (T2) · recommendation (T3) tools
    agent/                     orchestrator · provider contract · Agent SDK · Client SDK · offline router · grounding · disclosure guard
    chats/                     persistent conversations (SQLite)
    voice/                     speech-to-text / text-to-speech providers (whisper · sarvam · browser)
    explain/                   evidence → reasoning lines
    evals/                     harness: run questions.json, grade, write reports
    interface/                 cli.py (ask/chat/eval/serve/check/rostered/build-db) · api.py (FastAPI)
  tests/unit · tests/integration · tests/fixtures (voice clip)
  evals/reports/               committed eval reports
  var/                         derived artifacts (dataset SQLite, chats), git-ignored
frontend/                      React (Vite) chat UI — conversations sidebar, reasoning trail, samples drawer
```

## Team workflow

Branch per person/feature (`<your-name>/<feature>`), `make test` and `make lint` green, PR
to `main`. Decisions go in `docs/decisions.md` — including what was skipped and why.

Team: Rajesh (@valinci-007) · @SyedMaaz786
