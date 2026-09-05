"""P1 exit gate: every Tier-1 question, end to end through the agent loop, offline provider."""

from crew_ops_advisor.evals import load_questions, run_evals


def test_all_tier1_questions_pass_offline(offline_advisor, store):
    questions = load_questions(store, tiers=[1])
    assert len(questions) == 16
    report = run_evals(offline_advisor, questions)
    failed = [(r.question.question_id, r.grade.missing) for r in report.rows if not r.grade.passed]
    assert failed == []
    assert report.passed == report.total == 16
    assert all(not r.answer.refused and r.answer.error is None for r in report.rows)
    assert report.latency()["p50_ms"] < 8000
