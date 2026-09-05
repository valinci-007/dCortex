"""Tier 2 (consequence) edge cases — the scenario list from PR #3 (T2-EC-1 … T2-EC-13),
ported onto the real API and the real dataset so every case executes.

Where a scenario names a known limitation (partial multi-day covers, repatriation, overnight
station closures) the test asserts the honest current behaviour — a clean refusal or the
documented shape — and points at docs/failure-cases.md, rather than pretending.
"""

from __future__ import annotations

import copy

import pytest

RULES = [
    "RULE-FDP-01",
    "RULE-DUTY-02",
    "RULE-FLT-03",
    "RULE-REST-04",
    "RULE-QUAL-05",
    "RULE-CERT-06",
    "RULE-BASE-07",
]


def call(registry, name, **args):
    out = registry.call(name, args)
    assert out.ok, f"{name}: {out.error}"
    return out.result


# ---- T2-EC-1: a delay is checked against rest for the next duty, not just FDP ------------


def test_t2_ec1_delay_assessment_checks_rest_and_every_other_rule(registry):
    r = call(registry, "simulate_delay", aircraft="VT-DXA", date="2026-09-16", delay_hours=1.5)
    assert r["fdp_after_delay"] > r["fdp_before"] and r["rule"] == "RULE-FDP-01"
    for check in r["crew_checks"]:
        assert check["rules_checked"] == RULES  # all seven, RULE-REST-04 included
        rest = [v for v in check["verdicts"] if v["rule_id"] == "RULE-REST-04"]
        assert rest and all(v["computed"] is not None for v in rest)


# ---- T2-EC-2: a reserve in rest is not offered before the rest ends ----------------------


def test_t2_ec2_reserve_coverage_respects_rest_and_windows(registry):
    r = call(
        registry,
        "reserve_coverage",
        required_report_utc="2026-09-15T06:00:00Z",
        station="BLR",
        rank="Captain",
    )
    ids = set(r["eligible"])
    assert "C-3310" in ids  # on call 06:00–18:00Z, rested
    assert "C-3305" not in ids  # window 00:00–05:30Z does not cover a 06:00Z report
    excluded = {e["crew_id"]: e["reason"] for e in r["excluded"]}
    assert "C-3305" in excluded and "window" in excluded["C-3305"].lower()
    # every candidate carries its reason, eligible or not
    assert all(c["reason"] for c in r["candidates"])


# ---- T2-EC-3: a closure window that crosses midnight is refused, not mis-modelled --------


def test_t2_ec3_overnight_station_closure_is_refused_cleanly(registry):
    out = registry.call(
        "station_closure_impact",
        {"station": "BLR", "date": "2026-09-15", "start": "22:00", "end": "02:00"},
    )
    assert not out.ok and "end must be after its start" in out.error
    # the same closure expressed within one calendar day works
    r = call(
        registry,
        "station_closure_impact",
        station="BLR",
        date="2026-09-15",
        start="22:00",
        end="23:59",
    )
    assert "affected_flights" in r or "flights" in r


# ---- T2-EC-4 / T2-EC-5: partial covers of a multi-day pairing -----------------------------


def test_t2_ec4_cover_from_the_second_day_of_a_pairing_is_ranked(registry):
    r = call(
        registry, "rank_cover_options", pairing_id="P-2291", role="Captain", from_date="2026-09-16"
    )
    assert r["duty_dates"] == ["2026-09-16"] and r["options"]
    assert all(
        o["coverage"] in ("all legs", "all 1 duty day(s)") for o in r["options"] if o["crew_id"]
    )


@pytest.mark.xfail(
    strict=True,
    reason="repatriation of the relieved crew is not modelled — docs/failure-cases.md §2",
)
def test_t2_ec5_partial_cover_costs_the_relieved_crews_repatriation(registry):
    r = call(
        registry, "rank_cover_options", pairing_id="P-2291", role="Captain", from_date="2026-09-16"
    )
    best = r["options"][0]
    assert "repatriation" in best["cost_breakdown"]


# ---- T2-EC-6: a removal reaches every downstream pairing the crew member holds ----------


def test_t2_ec6_crew_removal_reaches_downstream_pairings(store, registry):
    crew_id = next(
        c.crew_id for c in store.crew.list() if len(store.pairings.for_crew(c.crew_id)) >= 2
    )
    held = sorted(p.pairing_id for p in store.pairings.for_crew(crew_id))
    # a plain sick call scopes to the duty it is for — the first affected pairing …
    first = call(registry, "simulate_crew_removal", crew_id=crew_id, from_date="2026-09-14")
    assert first["pairings_affected"] == held[:1]
    # … and `through_date` widens it to every downstream pairing the crew member holds
    whole = call(
        registry,
        "simulate_crew_removal",
        crew_id=crew_id,
        from_date="2026-09-14",
        through_date="2026-09-20",
    )
    assert sorted(whole["pairings_affected"]) == held
    assert whole["passengers_at_risk_total"] >= first["passengers_at_risk_total"]


# ---- T2-EC-7: the legality verdict for a delay carries every rule with numbers -----------


def test_t2_ec7_delay_verdicts_carry_computed_limit_and_margin(registry):
    r = call(registry, "simulate_delay", aircraft="VT-DXA", date="2026-09-16", delay_hours=1.5)
    for check in r["crew_checks"]:
        fdp = [v for v in check["verdicts"] if v["rule_id"] == "RULE-FDP-01"]
        assert fdp and all(
            v["limit"] is not None
            and v["margin"] == pytest.approx(v["limit"] - v["computed"], abs=0.01)
            for v in fdp
        )


# ---- T2-EC-8: a cancellation reports the passengers and the crew it releases -------------


def test_t2_ec8_cancellation_impact_reports_passengers_and_released_crew(registry):
    r = call(registry, "cancellation_impact", flight_no="DX412", date="2026-09-15")
    assert r["passengers_affected"] == 162 and r["direct_cancellation_cost_inr"] > 0
    assert r["pairing_id"] == "P-2291" and "C-1042" in r["crew_released"]


# ---- T2-EC-9: an exhausted reserve pool is an empty eligible list with reasons ----------


def test_t2_ec9_reserve_pool_exhaustion_lists_every_exclusion(registry):
    r = call(
        registry,
        "reserve_coverage",
        required_report_utc="2026-09-15T20:00:00Z",
        station="BLR",
        rank="Captain",
    )
    assert r["eligible"] == []
    assert r["excluded"] and all(e["reason"] for e in r["excluded"])


# ---- T2-EC-10: evidence objects have the same shape everywhere ---------------------------


def test_t2_ec10_legality_evidence_objects_are_uniform(registry):
    r = call(
        registry,
        "check_assignment_legality",
        crew_id="C-2087",
        pairing_id="P-2291",
        from_date="2026-09-15",
    )
    assert r["legal"] is False and r["rules_checked"] == RULES
    for v in r["verdicts"]:
        assert set(v) >= {
            "rule_id",
            "status",
            "detail",
            "date",
            "computed",
            "limit",
            "margin",
            "inputs",
        }
        assert v["rule_id"] in RULES and v["status"] in ("pass", "breach", "conditional")
    breach = next(
        v for v in r["verdicts"] if v["rule_id"] == "RULE-DUTY-02" and v["status"] == "breach"
    )
    assert breach["computed"] > breach["limit"] and breach["margin"] < 0


# ---- T2-EC-11: simulation tools agree with each other ------------------------------------


def test_t2_ec11_removal_and_recommendation_agree_on_the_uncovered_flights(registry):
    removal = call(registry, "simulate_crew_removal", crew_id="C-1042", from_date="2026-09-15")
    cover = call(registry, "recommend_cover", crew_id="C-1042", from_date="2026-09-15")
    assert set(removal["uncovered_now"]) <= set(cover["uncovered_flights"])
    assert cover["passengers_at_risk"] == removal["passengers_at_risk_total"]


# ---- T2-EC-12: simulations never mutate the roster or the clocks -------------------------


def test_t2_ec12_simulations_do_not_mutate_the_datastore(registry):
    before = copy.deepcopy(call(registry, "get_duty_clock", crew_id="C-3310"))
    pairing_before = copy.deepcopy(call(registry, "get_pairing", pairing_id="P-2291"))
    call(registry, "simulate_crew_removal", crew_id="C-1042", from_date="2026-09-15")
    call(registry, "recommend_cover", crew_id="C-1042", from_date="2026-09-15")
    call(
        registry,
        "check_assignment_legality",
        crew_id="C-3310",
        pairing_id="P-2291",
        from_date="2026-09-15",
    )
    assert call(registry, "get_duty_clock", crew_id="C-3310") == before
    assert call(registry, "get_pairing", pairing_id="P-2291") == pairing_before


# ---- T2-EC-13: the grounding check refuses facts that no tool returned -------------------


def test_t2_ec13_grounding_flags_figures_absent_from_the_evidence():
    from crew_ops_advisor.agent.grounding import check_grounding

    corpus = '{"crew_id": "C-1042", "duty_hours_7d": 48.5, "cost_inr": 18500}'
    assert check_grounding("C-1042 has 48.5h; the callout costs 18500 INR.", corpus).ok
    bad = check_grounding("C-9999 has 52.0h; the callout costs 41200 INR.", corpus)
    assert not bad.ok and {"C-9999", "52.0", "41200"} <= set(bad.unsupported)
