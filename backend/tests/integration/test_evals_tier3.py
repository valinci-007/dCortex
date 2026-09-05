"""P4 exit gate: Tier-3 questions end to end through the agent loop, offline provider.

Q33 is expected to miss: its answer key states the delayed 3-leg duty as 9.5 h while the same
key computes the 4-leg duty with the report time fixed (12.75 h); with the report fixed the
3-leg duty is 11.0 h. We keep the consistent computation (docs/failure-cases.md).
"""

from crew_ops_advisor.evals import load_questions, run_evals

KNOWN_KEY_INCONSISTENCY = {"Q33"}


def test_tier3_questions_pass_offline_except_documented_key_inconsistency(offline_advisor, store):
    questions = load_questions(store, tiers=[3])
    assert len(questions) == 8
    report = run_evals(offline_advisor, questions)
    failed = {r.question.question_id for r in report.rows if not r.grade.passed}
    assert failed == KNOWN_KEY_INCONSISTENCY, [
        (r.question.question_id, r.grade.missing) for r in report.rows if not r.grade.passed
    ]
    assert all(not r.answer.refused and r.answer.error is None for r in report.rows)
    tools = {s.name for r in report.rows for s in r.answer.tool_calls}
    assert tools >= {
        "recommend_cover",
        "joint_cover_plan",
        "resolve_delay_options",
        "draft_callout_notification",
        "morning_briefing",
        "station_closure_impact",
    }


def test_out_of_scope_questions_are_still_refused(offline_advisor):
    for q in (
        "Will fog delay BLR tomorrow?",
        "What's the weather at DEL?",
        "Book a hotel for C-1042",
    ):
        a = offline_advisor.ask(q)
        assert a.refused, q
