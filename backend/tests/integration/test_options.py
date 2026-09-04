"""Tier-3 ranking reproduces the scenario answer keys (S1, S2, S4, S5, S6) and Q36/Q37."""

import json
from datetime import date
from pathlib import Path

import pytest

from crew_ops_advisor.domain.timeutil import parse_utc
from crew_ops_advisor.simulation import (
    SimulationError,
    draft_notification,
    joint_cover_plan,
    morning_briefing,
    rank_cover_options,
    recommend_cover,
    resolve_delay_options,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture(scope="module")
def scenarios():
    return {s["scenario_id"]: s for s in json.loads((DATA_DIR / "scenarios.json").read_text())}


def _key_options(scenario):
    return [
        (o["action"], o["cost_inr"], o["delay_hours"]) for o in scenario["answer_key"]["options"]
    ]


def test_s2_flagship_options_and_exclusions_match_exactly(store, scenarios):
    r = rank_cover_options(
        store, "P-2291", "Captain", from_date=date(2026, 9, 15), exclude_crew=("C-1042",)
    )
    assert [(o.action, o.cost_inr, o.delay_hours) for o in r.options] == _key_options(
        scenarios["S2"]
    )
    key_excluded = {
        e["crew_id"]: e["reason"] for e in scenarios["S2"]["answer_key"]["excluded_candidates"]
    }
    ours = {e.crew_id: e.reason for e in r.excluded}
    assert set(ours) == set(key_excluded)
    for cid in ("C-2087", "C-3305", "C-3315", "C-5837"):
        assert ours[cid] == key_excluded[cid]
    assert r.expected_choice.crew_id == "C-3310" and r.passengers == 972
    assert r.options[0].rules_checked == tuple(
        scenarios["S2"]["answer_key"]["options"][0]["rules_checked"]
    )


def test_s1_atr_captain_options_match(store, scenarios):
    r = rank_cover_options(
        store, "P-2224", "Captain", from_date=date(2026, 9, 16), exclude_crew=("C-3231",)
    )
    assert [(o.action, o.cost_inr, o.delay_hours) for o in r.options] == _key_options(
        scenarios["S1"]
    )


def test_s5_cabin_crew_options_match_except_the_pairings_own_crew(store, scenarios):
    """The key lists C-2840 and C-4588 as day-off covers, but both are already rostered on
    P-2213 in another Cabin Crew slot; moving them just empties their own slot. We exclude a
    pairing's own crew deliberately (documented in docs/failure-cases.md)."""
    r = rank_cover_options(
        store, "P-2213", "Cabin Crew", from_date=date(2026, 9, 19), exclude_crew=("C-5417",)
    )
    key = [
        o for o in _key_options(scenarios["S5"]) if "C-2840" not in o[0] and "C-4588" not in o[0]
    ]
    assert [(o.action, o.cost_inr, o.delay_hours) for o in r.options] == key
    assert r.options[0].crew_id == "C-4809" and r.options[0].cost_inr == 9500


def test_s4_delay_recovery_options(store, scenarios):
    d = resolve_delay_options(store, date(2026, 9, 16), 1.5, aircraft="VT-DXA")
    key = scenarios["S4"]["answer_key"]["options"]
    assert [(o["action"], o["legal"], o["cost_inr"]) for o in d["options"]] == [
        (o["action"], o["legal"], o["cost_inr"]) for o in key
    ]
    assert d["options"][0]["reserve_set"]["First Officer"] == ["C-3311"]  # BLR-based, not DEL
    assert (
        "3.3x" in d["options"][1]["reasoning"] and "162 passengers" in d["options"][1]["reasoning"]
    )


def test_s6_q32_joint_plan(store, scenarios):
    events = [
        {
            "crew_id": e["crew_id"],
            "pairing_id": e["pairing_id"],
            "reported_utc": parse_utc(e["reported_utc"]),
        }
        for e in scenarios["S6"]["event"]["events"]
    ]
    plan = joint_cover_plan(store, events)
    assert plan["total_cost_inr"] == 42500
    assert {(p["pairing_id"], p["crew_id"]) for p in plan["plan"]} == {
        ("P-2205", "C-3305"),
        ("P-2212", "C-1017"),
    }
    ids = [p["crew_id"] for p in plan["plan"]]
    assert len(ids) == len(set(ids))


def test_q37_recommend_cover_resolves_the_sick_first_officer(store):
    pairing = store.pairings.for_aircraft_on("VT-DXF", date(2026, 9, 20))
    fo = next(m.crew_id for m in pairing.crew if m.role == "First Officer")
    impact, r = recommend_cover(store, fo, reported_utc=parse_utc("2026-09-20T03:30:00Z"))
    assert (
        r.role == "First Officer"
        and r.options[0].action == "Assign First Officer C-3316 (reserve callout)"
    )
    assert r.options[0].cost_inr == 18500 and impact["pairings_affected"] == [pairing.pairing_id]


def test_q36_notification_carries_every_operational_fact(store):
    n = draft_notification(store, "C-3310", "P-2291")
    msg = n["message"]
    for must in (
        "C-3310",
        "P-2291",
        "06:00Z",
        "BLR crew room",
        "DX412",
        "DX413",
        "DX588",
        "Overnight at DEL",
        "hotel arranged",
        "DX589",
        "DX590",
        "DX591",
        "04:00Z at DEL crew room",
        "Acknowledgement request",
        "Contact for questions",
    ):
        assert must in msg, must
    assert n["days"][0]["overnight_at"] == "DEL" and n["days"][1]["overnight_at"] is None


def test_q38_morning_briefing_lines(store):
    b = morning_briefing(store, date(2026, 9, 15))
    assert {ln["aircraft"] for ln in b["lines"]} == {
        "VT-DXA",
        "VT-DXB",
        "VT-DXC",
        "VT-DXD",
        "VT-DXE",
        "VT-DXF",
    }
    line = next(ln for ln in b["lines"] if ln["aircraft"] == "VT-DXC")
    assert line["pairing_id"] == "P-2291" and "C-3310" in line["eligible_reserves_at_report"]
    assert len(b["surfaced"]) == 3


def test_errors(store):
    with pytest.raises(SimulationError):
        rank_cover_options(store, "P-2291", "Captain", from_date=date(2026, 9, 17))
    with pytest.raises(SimulationError):
        recommend_cover(store, "C-3310")  # a reserve with no rostered duty
