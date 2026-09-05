# Edge-case analysis (PR #3)

Analysis notes and scenario lists contributed in PR #3. The two test files the PR added
(`backend/tests/integration/test_edge_cases_tier{1,2}.py`) were written against an API that
does not exist in this repository (`load_database`, `registry.get_tool(...).execute(...)`,
tool names such as `analyze_delay`) and failed at import, which stopped the whole suite from
collecting. They have been rewritten in place against the real API and dataset, keeping the
scenario ids (T1-EC-1 … T2-EC-13) and intent:

- 29 of the 30 ported cases pass; T2-EC-5 (repatriation of a relieved crew member) is marked
  `xfail(strict=True)` because that cost is genuinely not modelled — see
  `docs/failure-cases.md` §2.
- T1-EC-1 found a real defect: an on-call window that wraps past midnight (22:00–06:00) was
  evaluated as `start <= t <= end` and could never match. Fixed in
  `domain/models.py` (`ReserveEntry.covers`); the dataset has no such window, a held-out
  scenario might.
- T2-EC-3 (overnight station closure) and T2-EC-6 (downstream pairings) assert the engine's
  documented behaviour: a closure window must sit within one calendar day (clean refusal),
  and a plain sick call scopes to the duty it is for unless `through_date` widens it.

The scores and "production-ready" verdicts in these notes are the author's assessment at
the time of writing, not measured results; the measured results live in
`backend/evals/reports/`.
