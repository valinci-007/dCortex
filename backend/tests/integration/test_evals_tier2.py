"""P2 exit gate: every Tier-2 question end to end through the agent loop, offline provider."""

from crew_ops_advisor.evals import load_questions, run_evals


def test_all_tier2_questions_pass_offline(offline_advisor, store):
    questions = load_questions(store, tiers=[2])
    assert len(questions) == 14
    report = run_evals(offline_advisor, questions)
    failed = [(r.question.question_id, r.grade.missing) for r in report.rows if not r.grade.passed]
    assert failed == []
    assert all(not r.answer.refused and r.answer.error is None for r in report.rows)
    assert {s.name for r in report.rows for s in r.answer.tool_calls} >= {
        "simulate_crew_removal",
        "check_assignment_legality",
        "station_closure_impact",
        "simulate_delay",
        "cancellation_impact",
        "crew_near_limits",
        "reserve_coverage",
        "earliest_next_report",
        "check_rostered_legality",
        "seats_at_risk",
    }
