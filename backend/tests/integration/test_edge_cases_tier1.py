"""Tier 1 (lookup) edge cases — the scenario list from PR #3 (T1-EC-1 … T1-EC-13), ported
onto the real API and the real dataset so every case executes.

Conventions: `registry.call(name, args)` returns a ToolOutcome (`ok`, `result`, `error`);
the `store` and `registry` fixtures come from tests/conftest.py. Crew ids are real ones.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, time

import pytest

from crew_ops_advisor.domain.models import ReserveEntry

UTC = UTC


def call(registry, name, **args):
    out = registry.call(name, args)
    assert out.ok, f"{name}: {out.error}"
    return out.result


def at(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=UTC)


# ---- T1-EC-1: an on-call window that wraps past midnight ---------------------------------


def test_t1_ec1_overnight_reserve_window_wraps_midnight():
    reserve = ReserveEntry(
        crew_id="C-TEST",
        base="BLR",
        dates=(date(2026, 9, 15),),
        oncall_start=time(22, 0, tzinfo=UTC),
        oncall_end=time(6, 0, tzinfo=UTC),
    )
    assert reserve.overnight
    assert reserve.covers(at(2026, 9, 15, 23, 30))  # evening of the reserve date
    assert reserve.covers(at(2026, 9, 16, 5, 0))  # early morning after it
    assert not reserve.covers(at(2026, 9, 16, 7, 0))  # after the window closed
    assert not reserve.covers(at(2026, 9, 15, 21, 0))  # before it opened
    assert not reserve.covers(at(2026, 9, 15, 5, 0))  # the morning *before* the reserve date


# ---- T1-EC-2: duty-clock history lists only days with hours ------------------------------


def test_t1_ec2_history_omits_zero_duty_days_and_says_so(registry):
    clock = call(registry, "get_duty_clock", crew_id="C-1042")
    history = clock["daily_history"]
    assert history and all(d["duty_hours"] > 0 or d["flight_hours"] > 0 for d in history)
    # the windows are explicit, so a missing date inside them is an off-day, not a gap
    assert clock["duty_window_7d"] == {"start": "2026-09-08", "end": "2026-09-14"}
    assert clock["flight_window_28d"] == {"start": "2026-08-18", "end": "2026-09-14"}


# ---- T1-EC-3: an unknown station is an empty result, not a crash -------------------------


def test_t1_ec3_unknown_station_yields_an_empty_listing(registry):
    r = call(registry, "list_flights", dep_station="INVALID_XYZ")
    assert r["count"] == 0 and r["flights"] == [] and r["total_seats"] == 0
    assert r["filters"]["dep_station"] == "INVALID_XYZ"


# ---- T1-EC-4: relative time words resolve deterministically ------------------------------


def test_t1_ec4_relative_time_words_are_resolved_against_the_snapshot(store):
    from crew_ops_advisor.agent.entities import EntityExtractor

    ex = EntityExtractor(store)
    e = ex.extract("Which flights depart DEL this afternoon?")
    assert "afternoon" in e.flags and e.dep_station == "DEL"
    e = ex.extract("Who is on reserve at BLR tomorrow?")
    assert "tomorrow" in e.flags and e.stations == ("BLR",)


# ---- T1-EC-5: nobody is rostered on two pairings the same day ----------------------------


def test_t1_ec5_no_crew_member_holds_two_pairings_on_one_day(store):
    seen = Counter()
    for pairing in store.pairings.list():
        for day in pairing.days:
            for member in pairing.crew:
                seen[(member.crew_id, day.date)] += 1
    assert not [k for k, n in seen.items() if n > 1]


# ---- T1-EC-6: certification validity is checked on the duty date, both ends --------------


def test_t1_ec6_certification_validity_checks_valid_from_and_valid_to(store):
    from crew_ops_advisor.domain.models import Certification

    cert = Certification("C-TEST", "licence", date(2026, 9, 10), date(2026, 9, 20))
    assert cert.valid_on(date(2026, 9, 10)) and cert.valid_on(date(2026, 9, 20))
    assert not cert.valid_on(date(2026, 9, 9)) and not cert.valid_on(date(2026, 9, 21))
    # and every crew member in the dataset carries the four certificate types
    for crew in store.crew.list():
        types = {c.cert_type for c in store.certifications.for_crew(crew.crew_id)}
        assert types >= {"licence", "medical_class1", "recurrent_training", "dangerous_goods"}


# ---- T1-EC-7: reachability is always present and plausible ------------------------------


def test_t1_ec7_reachability_is_reported_for_every_crew_member(store, registry):
    for crew in store.crew.list():
        assert 0 < crew.reachability_minutes <= 240
    r = call(registry, "get_crew", crew_id="C-1042")
    assert r["reachability_minutes"] == store.crew.get("C-1042").reachability_minutes


# ---- T1-EC-8: window boundaries are inclusive to the minute ------------------------------


def test_t1_ec8_reserve_window_boundaries_are_inclusive(store):
    reserve = store.reserves.get("C-3305")  # on call 00:00–05:30Z
    assert reserve.covers(at(2026, 9, 15, 5, 30))
    assert not reserve.covers(at(2026, 9, 15, 5, 31))
    assert reserve.covers(at(2026, 9, 15, 0, 0))
    assert not reserve.covers(at(2026, 9, 13, 3, 0))  # not a reserve date


# ---- T1-EC-9: near-limits thresholds behave as thresholds --------------------------------


def test_t1_ec9_near_limits_threshold_is_monotonic(registry):
    loose = call(registry, "crew_near_limits", date="2026-09-15", max_duty_headroom=15.0)
    tight = call(registry, "crew_near_limits", date="2026-09-15", max_duty_headroom=9.0)
    assert {c["crew_id"] for c in tight["crew"]} <= {c["crew_id"] for c in loose["crew"]}
    assert all(c["duty_headroom_7d"] <= 9.0 for c in tight["crew"])
    assert "C-2087" in {c["crew_id"] for c in tight["crew"]}


# ---- T1-EC-10: input validation is structured, never an exception ------------------------


@pytest.mark.parametrize(
    ("name", "args", "message"),
    [
        ("get_crew", {}, "missing required argument(s): crew_id"),
        ("get_crew", {"crew": "C-1042"}, "missing required argument(s): crew_id"),
        ("get_crew", {"crew_id": "C-1001"}, "unknown crew C-1001"),
        ("get_duty_clock", {"crew_id": "C-1042", "extra": 1}, "unknown argument(s): extra"),
        ("list_reserves", {"station": "BLR", "date": "15/09/2026"}, "date"),
    ],
)
def test_t1_ec10_query_tool_input_validation(registry, name, args, message):
    out = registry.call(name, args)
    assert not out.ok and message in out.error


# ---- T1-EC-11 / T1-EC-12: rolling windows are exactly 7 and 28 calendar days -------------


def test_t1_ec11_seven_day_window_is_seven_calendar_days_ending_today(registry):
    clock = call(registry, "get_duty_clock", crew_id="C-2087")
    start, end = clock["duty_window_7d"]["start"], clock["duty_window_7d"]["end"]
    assert (date.fromisoformat(end) - date.fromisoformat(start)).days == 6
    inside = [d for d in clock["daily_history"] if start <= d["date"] <= end]
    assert clock["duty_hours_7d"] == pytest.approx(sum(d["duty_hours"] for d in inside), abs=0.01)
    assert clock["duty_headroom_7d"] == pytest.approx(60 - clock["duty_hours_7d"], abs=0.01)


def test_t1_ec12_twenty_eight_day_window_is_twenty_eight_calendar_days(registry):
    clock = call(registry, "get_duty_clock", crew_id="C-2087")
    start, end = clock["flight_window_28d"]["start"], clock["flight_window_28d"]["end"]
    assert (date.fromisoformat(end) - date.fromisoformat(start)).days == 27
    inside = [d for d in clock["daily_history"] if start <= d["date"] <= end]
    assert clock["flight_hours_28d"] == pytest.approx(
        sum(d["flight_hours"] for d in inside), abs=0.01
    )


# ---- T1-EC-13: one certificate per type per crew member ----------------------------------


def test_t1_ec13_no_duplicate_certificate_types_per_crew_member(store, registry):
    for crew in store.crew.list():
        types = [c.cert_type for c in store.certifications.for_crew(crew.crew_id)]
        assert len(types) == len(set(types)), crew.crew_id
    r = call(registry, "get_certifications", crew_id="C-5417")
    assert len({c["cert_type"] for c in r["certifications"]}) == len(r["certifications"])
