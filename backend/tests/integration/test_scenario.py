"""Scenario workspace (ADR-0018 §3): chained disruptions against an overlay of the roster."""

from __future__ import annotations

from datetime import date

import pytest

from crew_ops_advisor.simulation.scenario import Scenario, ScenarioStore
from crew_ops_advisor.tools import build_registry

D15 = date(2026, 9, 15)


@pytest.fixture
def workspace(store):
    ws = ScenarioStore(store, Scenario())
    reg = build_registry(ws)

    def call(name, **kw):
        out = reg.call(name, kw)
        assert out.ok, f"{name}: {out.error}"
        return out.result

    return ws, call


def test_empty_scenario_is_a_pass_through(store):
    ws = ScenarioStore(store, Scenario())
    assert ws.pairings.get("P-2291") == store.pairings.get("P-2291")
    assert ws.pairings.for_crew("C-1042") == store.pairings.for_crew("C-1042")
    assert ws.pairings.duties_for_crew("C-1042") == store.pairings.duties_for_crew("C-1042")
    assert ws.crew.get("C-1042") == store.crew.get("C-1042")
    assert [c.crew_id for c in ws.crew.list(status="active")] == [
        c.crew_id for c in store.crew.list(status="active")
    ]
    assert ws.reserves.list(base="BLR", on=D15) == store.reserves.list(base="BLR", on=D15)
    assert ws.snapshot_utc == store.snapshot_utc and ws.costs == store.costs


def test_declare_then_cover_then_the_cover_goes_sick(workspace, store):
    ws, call = workspace
    declared = call("declare_unavailable", crew_id="C-1042", from_date="2026-09-15")
    assert declared["impact"]["uncovered_now"][:3] == [
        "DX412-2026-09-15",
        "DX413-2026-09-15",
        "DX588-2026-09-15",
    ]
    assert [(v["pairing_id"], v["date"]) for v in declared["scenario"]["vacancies"]] == [
        ("P-2291", "2026-09-15"),
        ("P-2291", "2026-09-16"),
    ]
    assert ws.crew.get("C-1042").status == "unavailable"
    assert "C-1042" not in {c.crew_id for c in ws.crew.list(status="active")}

    # the answer key's substitution: C-2087 would breach RULE-DUTY-02 — refused, nothing recorded
    refused = call("apply_cover", pairing_id="P-2291", crew_id="C-2087", replacing="C-1042")
    assert refused["applied"] is False and "RULE-DUTY-02" in refused["reason"]
    assert ws.scenario.covers == []

    applied = call("apply_cover", pairing_id="P-2291", crew_id="C-3310", replacing="C-1042")
    assert applied["applied"] is True and applied["cover"]["cost_inr"] == 18500.0
    assert applied["scenario"]["vacancies"] == []
    # the roster as it now stands
    assert ("C-3310", "Captain") in [(m.crew_id, m.role) for m in ws.pairings.get("P-2291").crew]
    assert "C-1042" not in ws.pairings.get("P-2291").crew_ids
    assert {d.date for d in ws.pairings.duties_for_crew("C-3310")} >= {D15, date(2026, 9, 16)}
    assert all(d.date < D15 for d in ws.pairings.duties_for_crew("C-1042"))
    assert "C-3310" not in {r.crew_id for r in ws.reserves.list(base="BLR", on=D15)}
    assert "C-3310" in {r.crew_id for r in store.reserves.list(base="BLR", on=D15)}
    # asking the impact again finds nothing uncovered
    assert (
        call("simulate_crew_removal", crew_id="C-1042", from_date="2026-09-15")["uncovered_now"]
        == []
    )

    # chained: the cover himself calls in sick — the vacancy reappears, neither is offered
    again = call("declare_unavailable", crew_id="C-3310", from_date="2026-09-15")
    assert [(v["pairing_id"], v["role"]) for v in again["scenario"]["vacancies"]] == [
        ("P-2291", "Captain"),
        ("P-2291", "Captain"),
    ]
    options = call("recommend_cover", crew_id="C-3310", from_date="2026-09-15")["options"]
    assert options and not any(o["crew_id"] in ("C-1042", "C-3310") for o in options)

    status = call("scenario_status")
    assert status["committed_cost_inr"] == 18500.0 and len(status["summary"]) == 3
    watch = call("watchlist", date="2026-09-15")
    assert [u["pairing_id"] for u in watch["uncovered_flights"]] == ["P-2291", "P-2291"]

    assert call("reset_scenario")["scenario"]["empty"] is True
    assert ws.pairings.get("P-2291") == store.pairings.get("P-2291")


def test_apply_cover_validates_the_slot_and_the_rank(workspace):
    ws, call = workspace
    reg = build_registry(ws)
    bad = reg.call(
        "apply_cover", {"pairing_id": "P-2291", "crew_id": "C-3310", "replacing": "C-9999"}
    )
    assert not bad.ok and "does not hold a slot" in bad.error
    wrong_rank = call("apply_cover", pairing_id="P-2291", crew_id="C-3311", replacing="C-1042")
    assert wrong_rank["applied"] is False and "needs a Captain" in wrong_rank["reason"]


def test_scenario_tools_need_a_workspace(registry):
    out = registry.call("scenario_status", {})
    assert not out.ok and "no scenario workspace" in out.error


def test_scenario_round_trips_through_json(store):
    s = Scenario()
    s.declare_unavailable("C-1042", D15, "sick")
    from crew_ops_advisor.simulation.scenario import Cover

    s.apply_cover(Cover("P-2291", D15, "Captain", "C-3310", "C-1042", "reserve_callout", 18500.0))
    again = Scenario.from_dict(s.to_dict())
    assert again.to_dict() == s.to_dict() and again.summary() == s.summary()
    assert Scenario.from_dict(None).empty


def test_offline_router_drives_the_scenario_with_explicit_verbs(store, registry):
    from crew_ops_advisor.agent import Advisor, OfflineProvider

    advisor = Advisor(store, registry, OfflineProvider(store))
    conv = advisor.new_conversation()
    first = advisor.ask("Record that C-1042 is sick from 2026-09-15.", conv).text
    assert "Recorded: C-1042" in first and "Vacant: Captain on P-2291 2026-09-15" in first
    applied = advisor.ask("Apply C-3310 to P-2291 replacing C-1042.", conv).text
    assert "Committed: C-3310 covers P-2291" in applied and "₹18,500" in applied
    reserves = advisor.ask("Who is on reserve at BLR on 2026-09-15?", conv).text
    assert "11 crew on reserve" in reserves and "C-3310" not in reserves
    refused = advisor.ask("Apply C-2087 to P-2291 replacing C-3310.", conv).text
    assert refused.startswith("Not applied") and "RULE-DUTY-02" in refused
    status = advisor.ask("What is the scenario status?", conv).text
    assert "Committed cost so far ₹18,500" in status
    assert "Scenario reset" in advisor.ask("Reset the scenario.", conv).text
    assert conv.scenario.empty


def test_options_carry_the_tightest_candidate_specific_margin(registry):
    r = registry.call("recommend_cover", {"crew_id": "C-1042", "from_date": "2026-09-15"}).result
    by_id = {o["crew_id"]: o for o in r["options"] if o["crew_id"]}
    # rolling windows differ by candidate; the pairing's own inter-day rest (0.5 h) must not
    # be reported for everyone
    assert by_id["C-3310"]["margin"]["rule"] == "RULE-DUTY-02"
    assert by_id["C-3310"]["margin"]["headroom_hours"] > 30
    assert by_id["C-2210"]["margin"] == {
        "rule": "RULE-REST-04",
        "headroom_hours": 4.0,
        "on": "2026-09-15",
        "label": "comfortable",
        "note": "RULE-REST-04 headroom 4.0h on 2026-09-15",
    }
    assert all(o["margin"]["headroom_hours"] != 0.5 for o in r["options"] if o["margin"])
    assert next(o for o in r["options"] if o["kind"] == "cancel")["margin"] is None
