# Failure cases and honest limits

The brief asks for sample outputs including cases the system handles poorly, with analysis.
Everything below was observed on the real system during evaluation on 2026-09-04; each case
says what happened, why, what we changed, and what remains.

## 1. A correct derived figure triggered a grounding rewrite (design trade-off)

**Question.** "Can C-3310 cover just day 1 of P-2291 and hand day 2 to someone else?"
(Agent SDK provider.)

**What happened.** The model's first draft summed two callouts to "₹37,000 total". The
grounding check found `37000` in no tool result — only `18500` twice — and requested a
rewrite in the same session. The rewrite dropped the derived total and passed. Cost: one
extra model turn (~8 s of a 28.5 s answer).

**Analysis.** The check is deliberately conservative: it cannot tell a correct sum from a
hallucinated one, so it treats any figure not in evidence as unverified. That is the right
default for a desk where "fluent, confident and wrong" is worse than silence, but it taxes
legitimate arithmetic. The fix is in the tools, not the check: give the model a tool that
returns the total (e.g. `joint_cover_plan.total_cost_inr`), so the figure *is* evidence.

## 2. Partial cover of a multi-day pairing is under-modelled (limitation)

Same question. The tools evaluated "C-3310 on day 1" and "C-2210 on day 2" independently
and both are legal under the seven rules — so the answer said a split is legal. It did not
cost repatriating C-3310 from DEL after day 1 (the aircraft overnights there), nor check
his rest for whatever he flies next. `simulate_crew_removal` does flag that "the cover must
take the full remaining pairing", and the model did quote it, but the option ranker only
enumerates whole-remaining-pairing covers. **Status:** known gap; splits are reported as
legal-per-rules with the caveat, not as recommended plans.

## 3. The offline router answered a different question than the one asked (fixed, class remains)

"Book a hotel for C-1042" — the keyword router saw a crew id and returned C-1042's profile.
"Captain C-5837 (VT-DXA line, works 14/17/20 Sep) is proposed to cover P-2291" — it read
"20 Sep" from "14/17/20 Sep" as the cover start date and reported that P-2291 has no duty
on 20 Sep.

**Analysis.** Both are the closed-world failure mode of Option C from the architecture
review: regex entity extraction with no understanding. We added an out-of-scope guard
(weather, bookings, contact, HR → refuse) and only take a "from" date when the question
literally says "from …", and every offline answer is labelled as such. The class of error
cannot be eliminated in a keyword router — it is why the model provider is the primary
path and the router is demo insurance.

## 4. Where we disagree with the answer keys (deliberate)

- **S5 / Q34.** The key lists C-2840 and C-4588 as day-off covers for C-5417's Cabin Crew
  slot on P-2213, but both are *already rostered on P-2213* in another Cabin Crew slot;
  moving one just empties their own seat. We exclude a pairing's own crew. Our 41 options
  equal the key's 43 minus those two, in the same order.
- **S4 / Q33.** The key states the delayed 3-leg duty as "FDP 9.5h" while computing the
  4-leg duty with the report time fixed (12.75 h). With the report fixed, three legs run
  11.0 h. Both are under the 12.5 h limit, so the recommendation is identical; we keep the
  consistent computation and this is the one Tier-3 question our offline eval "misses".
- **Deadhead covers (Q21/S2).** We follow the dataset README: positioning on the earliest
  flight from base, report = arrival + 15 min, delay costed per duty hour. Legality is
  evaluated on the rostered duty times, as the key does. A production system would
  re-check rest for the shifted day-1 release against the day-2 report.

## 5. Automated grading understates the real model (measurement limit)

Tier-3 real-model runs graded 4/8 and 7/8 on consecutive runs with identical tool calls and
recommendations; every answer was correct on human review. The variance is presentation:
"DX402/403/404" instead of three flight numbers, "Acknowledge by…" instead of the rubric's
"acknowledgement request with deadline", a summary "all seven rules pass" instead of seven
ids. The grader (ADR-0011) checks recall of facts and now tolerates ids, aliases and
inflections, but we stopped short of an LLM judge on purpose. **Report both numbers**: the
automated recall and the reviewed outcome (`evals/reports/`).

## 6. Latency on Tier 3 (weakness)

Tier-1 answers take ~7 s p50 with the model and Tier-2 ~10 s; Tier-3 answers with three or
four tool calls take 14–42 s (p95 27 s), above the ≤ 8 s target and well inside the
"45 s is not a decision aid" bar — but not comfortable for a live shift. Tool time is
milliseconds; the time is the model turns and Claude Code's harness. Mitigations tried:
effort `low` saves ~1 s; the offline router answers in < 20 ms for every question family.
Not tried: streaming partial answers to the UI, capping tool result size for Tier 3.

## 7. Things the dataset let us skip (declared, not hidden)

- Certification `valid_from` dates are unreliable in the data (some lie in the future for
  crew whose rosters are certified legal); we enforce expiry only, as the organiser's
  validator does.
- Reserve on-call windows are treated as availability, not a rule: a reserve whose window
  misses the report is "not callable" rather than "illegal".
- Cabin-crew complements are assumed per aircraft type (A320: 1/1/1/3, ATR72: 1/1/1/1) from
  the roster; a real carrier's minimums vary by configuration.

## 8. Chained what-ifs rely on the conversation, not on state (design choice)

**What it does.** The assistant is read-only over crew data (ADR-0021): every simulation
computes a hypothetical from the roster as it stands and returns it. A what-if is stated in
the question — "if C-2210 is also out" becomes an excluded candidate in the ranking, "both
captains sick" becomes a joint-plan event list.

**Where it stops.** A chain across turns ("C-1042 is sick" … "now C-3310 is sick too")
depends on the model carrying the earlier condition into the next lookup's parameters. It
usually does, and the answer names the assumptions it used, but nothing pins the earlier
condition to the roster, so a later question that forgets it will be answered against the
unchanged roster. We chose this over a mutable scenario because the desk's systems of record
are where changes belong; the advisor advises.

**How we know.** `tests/integration/test_positioning.py` drives the what-if through
parameters; the earlier scenario-workspace tests were removed with the feature.

## 9. One SQLite connection shared across request threads (fixed)

**Symptom.** On page load the UI fires several requests at once; one in a while
`/api/watchlist` returned 500 with `fromisoformat: argument must be str` — a flight row read
with a NULL date that is not NULL in the database.

**Cause.** The datastore handed one `sqlite3` connection (`check_same_thread=False`) to every
API worker thread. SQLite's serialised mode protects the C library, not the Python-level
cursor and statement-cache state; two threads reading through the same connection can
interleave and one gets a half-reset row. It surfaced only when the watchlist added a
heavier query to the same instant as `/api/context` and `/api/chats`.

**Fix.** `connect()` now returns a per-thread connection object: each worker thread opens
its own connection lazily (the built database is read-only, so nothing needs coordinating);
the chat store, which writes, serialises every operation on a lock. A test fires 40
concurrent requests across five endpoints and asserts every one returns 200 — it fails on
the old code and passes on the fix.

## 10. Positioning knows our network, not the world (limitation)

Positioning cover (ADR-0020) finds crew elsewhere and itineraries on **our own** flights —
direct, one hub connection, or the evening before with a hotel. It does not consider partner
carriers, charters or ground transport, never delays a departure to wait for someone (by the
desk's own rule), and tries a duty extension only when the crew member's current duty ends at
the station. A held-out scenario at a spoke station with no inbound flight before the
departure will get "nobody can be flown in" plus the reasoned exclusions — which is the honest
answer on this dataset, not a proof that no option exists in the real world.
