"""Tier-2 simulations reproduce the scenario and question answer keys (S1–S5, Q17–Q30)."""

import json
from datetime import date
from pathlib import Path

import pytest

from crew_ops_advisor.domain.timeutil import fmt_utc, parse_utc
from crew_ops_advisor.simulation import (
    SimulationError,
    assignment_check,
    cancellation,
    crew_removal,
    delay,
    earliest_report,
    near_limits,
    reserve_coverage,
    seats_at_risk,
    station_closure,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture(scope="module")
def scenarios():
    return {s["scenario_id"]: s for s in json.loads((DATA_DIR / "scenarios.json").read_text())}


# ---- sick calls (Q17, S1, S2) -------------------------------------------------


def test_q17_s2_flagship_sick_call(store):
    r = crew_removal(
        store, "C-1042", pairing_id="P-2291", reported_utc=parse_utc("2026-09-15T05:00:00Z")
    )
    d = r.to_dict()
    assert d["uncovered_now"] == ["DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15"]
    assert d["also_at_risk"] == ["DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16"]
    assert d["passengers_now"] == 486 and d["cover_must_take_full_pairing"]


def test_s1_atr_captain_sick_call_scopes_to_that_duty(store, scenarios):
    ev = scenarios["S1"]["event"]
    r = crew_removal(store, ev["crew_id"], reported_utc=parse_utc(ev["reported_utc"]))
    assert r.to_dict()["uncovered_now"] == scenarios["S1"]["answer_key"]["uncovered_flights"]
    assert not r.cover_must_take_full_pairing


def test_removal_after_release_has_no_effect(store):
    r = crew_removal(
        store, "C-1042", pairing_id="P-2291", reported_utc=parse_utc("2026-09-16T20:00:00Z")
    )
    assert r.days == () and "no rostered duties" in r.note


# ---- assignment legality (Q18, Q21, Q24, Q28, S2 exclusions) -------------------


def test_q18_c2087_dayoff_callout_breaches_duty(store):
    a = assignment_check(store, "C-2087", "P-2291", from_date=date(2026, 9, 15)).to_dict()
    assert a["callout_kind"] == "dayoff_callout" and a["cost_inr"] == 24000
    assert (
        not a["legal"] and len(a["issues"]) == 2 and all("RULE-DUTY-02" in i for i in a["issues"])
    )


def test_q21_c2210_deadhead_is_legal_with_three_hour_delay(store):
    a = assignment_check(store, "C-2210", "P-2291").to_dict()
    assert a["legal"] and a["available"] and a["callout_kind"] == "reserve_callout"
    assert a["deadhead"]["positioning_flight"] == "DX402"
    assert a["deadhead"]["first_departure_delay_hours"] == 3.0
    assert a["cost_inr"] == 41200 and a["cost_breakdown"] == {
        "callout": 18500,
        "deadhead_positioning": 6500,
        "delay": 16200,
    }
    assert a["consequence"] == (
        "Deadhead positioning on DX402 (arr 08:45Z) delays the first departure by ~3h; "
        "RULE-BASE-07 deadhead cost applies."
    )


def test_q24_c3305_full_pairing_breaches_day_two_and_window_misses_report(store):
    a = assignment_check(store, "C-3305", "P-2291").to_dict()
    assert a["issues"] == [
        "RULE-DUTY-02: would exceed 60h/7d by 8h15m on 2026-09-16 (total 68.25h)"
    ]
    assert (
        not a["available"]
        and "00:00-05:30Z does not cover required report 06:00Z" in a["availability_note"]
    )


def test_q28_c5837_downstream_rest_conflict(store):
    a = assignment_check(store, "C-5837", "P-2291").to_dict()
    assert a["issues"] == [
        "RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"
    ]


def test_s2_reserve_c3310_clean_and_rostered_recheck(store):
    a = assignment_check(store, "C-3310", "P-2291").to_dict()
    assert a["legal"] and a["feasible"] and a["cost_inr"] == 18500 and a["deadhead"] is None
    own = assignment_check(store, "C-1042", "P-2291").to_dict()
    assert own["callout_kind"] == "rostered" and own["legal"] and own["cost_inr"] is None


def test_assignment_past_pairing_end_is_an_error(store):
    with pytest.raises(SimulationError, match="no duty days"):
        assignment_check(store, "C-3310", "P-2291", from_date=date(2026, 9, 17))


# ---- station closure (Q19, Q29, S3) ---------------------------------------------


def test_s3_blr_closure_matches_per_flight_assessment(store, scenarios):
    key = scenarios["S3"]["answer_key"]
    impact = station_closure(
        store, "BLR", parse_utc("2026-09-17T08:00:00Z"), parse_utc("2026-09-17T14:00:00Z")
    )
    d = impact.to_dict()
    assert set(d["affected_flights"]) == set(key["affected_flights"])
    ours = {a["flight_id"]: a for a in d["per_flight"]}
    for expected in key["per_flight_assessment"]:
        mine = ours[expected["flight_id"]]
        assert mine["pairing_id"] == expected["pairing_id"]
        assert mine["min_delay_hours"] == expected["min_delay_hours"]
        assert mine["crew_fdp_after_delay"] == expected["crew_fdp_after_delay"]
        assert mine["fdp_limit"] == expected["fdp_limit"]
        assert mine["action"] == expected["action"]


def test_q29_hyd_closure(store):
    d = station_closure(
        store, "hyd", parse_utc("2026-09-19T05:00:00Z"), parse_utc("2026-09-19T09:00:00Z")
    ).to_dict()
    assert d["affected_flights"] == ["DX461-2026-09-19", "DX462-2026-09-19"]


# ---- delay (Q20, S4) --------------------------------------------------------------


def test_q20_s4_ninety_minute_delay_breaches_fdp_after_three_legs(store, scenarios):
    key = scenarios["S4"]["answer_key"]
    d = delay(store, date(2026, 9, 16), 1.5, aircraft="VT-DXA").to_dict()
    assert d["breach"] and d["fdp_after_delay"] == key["fdp_after_delay"] == 12.75
    assert d["fdp_limit"] == key["fdp_limit"] == 12.0
    assert d["legal_leg_count"] == 3 and d["legs_needing_recrew"] == ["DX404"]
    assert d["breach_detail"].startswith(
        "RULE-FDP-01: delayed duty runs 12.75h vs 12.0h limit (4 sectors)"
    )
    assert all(any("RULE-FDP-01" in i for i in c["issues"]) for c in d["crew_checks"])


def test_delay_by_flight_number_and_validation(store):
    d = delay(store, date(2026, 9, 16), 0.5, flight_no="DX401").to_dict()
    assert d["pairing_id"] == "P-2203" and not d["breach"] and d["legal_leg_count"] == 4
    with pytest.raises(SimulationError):
        delay(store, date(2026, 9, 16), -1, aircraft="VT-DXA")


# ---- cancellation, near limits, reserves, misc (Q23, Q25, Q26, Q27, Q30) -----------


def test_q25_cancellation_impact(store):
    d = cancellation(store, "DX404", date(2026, 9, 16)).to_dict()
    assert d["passengers_affected"] == 162 and d["direct_cancellation_cost_inr"] == 250000


def test_q26_crew_at_45_hours_including_planned_duty(store):
    rows = near_limits(store, date(2026, 9, 15))
    assert [(r.crew_id, r.duty_hours_7d) for r in rows] == [("C-2087", 51.83), ("C-3305", 50.0)]


def test_q27_reserve_coverage_for_atr_captain(store):
    rows = reserve_coverage(
        store,
        parse_utc("2026-09-16T03:00:00Z"),
        rank="Captain",
        aircraft_type="ATR72",
        station="BLR",
    )
    by_id = {r.crew_id: r for r in rows}
    assert [r.crew_id for r in rows if r.eligible] == ["C-3315"]
    assert by_id["C-3305"].reason == "RULE-QUAL-05: no ATR72 rating"
    assert (
        "reserve on-call window 06:00-18:00Z does not cover required report 03:00Z"
        in by_id["C-3310"].reason
    )


def test_q23_and_q30(store):
    assert (
        fmt_utc(earliest_report(store, parse_utc("2026-09-16T15:30:00Z"))) == "2026-09-17T03:30:00Z"
    )
    s = seats_at_risk(store)
    assert (
        s["most_seats_at_risk"] == "any A320 leg (162 seats)"
        and "ATR72 legs (72 seats)" in s["compared_with"]
    )


# ---- S5 certification lapse ------------------------------------------------------------


def test_s5_cert_lapse_flags_the_rostered_duty(store, scenarios):
    key = scenarios["S5"]["answer_key"]["illegal_assignment"]
    a = assignment_check(
        store, key["crew_id"], "P-2213", from_date=date.fromisoformat(key["date"])
    ).to_dict()
    assert not a["legal"] and a["issues"] == ["RULE-CERT-06: recurrent_training expired 2026-09-17"]
