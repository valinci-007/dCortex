"""Positioning cover (ADR-0020): nobody at the station can take a duty on time — who
elsewhere can be flown in before the departure, per the roster and our own network?"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from crew_ops_advisor.domain.models import DutyPeriod
from crew_ops_advisor.rules import CrewContext, evaluate_duties
from crew_ops_advisor.simulation.positioning import (
    crew_position,
    find_itineraries,
    positioning_cover,
)
from crew_ops_advisor.tools import build_registry


def at(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=UTC)


def test_position_comes_from_the_roster_not_the_base(store):
    # C-1042 (BLR-based) flies P-2291 on 15 Sep and overnights in DEL
    on_duty = crew_position(store, "C-1042", at(2026, 9, 15, 10, 0))
    assert (on_duty.station, on_duty.source) == ("DEL", "in duty")
    assert on_duty.available_from == at(2026, 9, 15, 15, 30)
    overnight = crew_position(store, "C-1042", at(2026, 9, 16, 3, 0))  # before day 2 reports
    assert (overnight.station, overnight.source) == ("DEL", "released")
    fresh = crew_position(store, "C-3310", at(2026, 9, 15, 6, 0))  # a reserve with no duties
    assert (fresh.station, fresh.source, fresh.available_from) == ("BLR", "base", None)


def test_itineraries_direct_one_stop_and_the_evening_before(store):
    direct = find_itineraries(
        store, "BLR", "DEL", not_before=at(2026, 9, 14, 18, 0), arrive_by=at(2026, 9, 16, 4, 45)
    )
    assert direct and all(len(it.legs) == 1 for it in direct)
    assert any(
        it.legs[0].flight_no == "DX588" and it.arrives.date() == date(2026, 9, 15) for it in direct
    )
    assert all(it.arrives <= at(2026, 9, 16, 4, 45) for it in direct)
    # DEL only flies to BLR, so DEL → BOM must connect through the hub
    hop = find_itineraries(
        store, "DEL", "BOM", not_before=at(2026, 9, 14, 18, 0), arrive_by=at(2026, 9, 16, 23, 0)
    )
    assert hop and all(len(it.legs) == 2 and it.legs[0].arr_station == "BLR" for it in hop)
    assert all(it.legs[1].dep_utc - it.legs[0].arr_utc >= timedelta(minutes=30) for it in hop)
    assert (
        find_itineraries(
            store, "BLR", "BLR", not_before=at(2026, 9, 14, 18, 0), arrive_by=at(2026, 9, 16, 4, 45)
        )
        == []
    )


def test_positioning_for_the_del_day_of_p2291(store):
    r = positioning_cover(store, "P-2291", "Captain", from_date=date(2026, 9, 16)).to_dict()
    assert r["station"] == "DEL" and r["scheduled_report_utc"] == "2026-09-16T04:00:00Z"
    by_id = {o["crew_id"]: o for o in r["options"]}
    # the DEL-based captain is simply there
    assert by_id["C-2210"]["kind"] == "present" and by_id["C-2210"]["cost_inr"] == 18500
    # BLR captains take the evening flight and a hotel — on time for the 04:00Z report
    flown = by_id["C-3310"]
    assert flown["kind"] == "positioning" and flown["on_time"] and flown["hotel_overnight"]
    assert flown["itinerary"]["legs"][0]["flight_no"] == "DX588"
    assert flown["effective_report_utc"] == "2026-09-16T04:00:00Z"
    assert flown["cost_breakdown"] == {"callout": 18500.0, "positioning": 6500.0, "hotel": 4200.0}
    assert all(o["legal"] for o in r["options"]) and r["on_time_count"] == len(r["options"])
    # a reserve whose window does not cover the callout moment is excluded, with the reason
    excluded = {e["crew_id"]: e["reason"] for e in r["excluded"]}
    assert "C-3305" in excluded and "on-call window" in excluded["C-3305"]
    assert "C-1042" not in by_id  # the slot holder is never a candidate


def test_ranking_escalates_when_no_option_keeps_the_departure_on_time(store):
    from crew_ops_advisor.simulation.options import rank_cover_options

    # day 1 of P-2291 has on-time local cover (C-3310): no escalation, keys unchanged
    day1 = rank_cover_options(store, "P-2291", "Captain", from_date=date(2026, 9, 15))
    assert day1.has_on_time_cover and day1.escalation is None
    assert [o.crew_id for o in day1.options[:2]] == ["C-3310", "C-1526"]

    # a what-if from the question: the only DEL captain is also out → every local option
    # now delays the departure, so the ranking escalates to positioning
    day2 = rank_cover_options(
        store, "P-2291", "Captain", from_date=date(2026, 9, 16), exclude_crew=("C-2210",)
    )
    assert not day2.has_on_time_cover and day2.escalation is not None
    assert "delay the first departure" in day2.escalation["reason"]
    options = day2.escalation["positioning"]["options"]
    assert (
        options
        and options[0]["on_time"]
        and options[0]["cost_inr"]
        < min(o.cost_inr for o in day2.options if o.legal and o.kind == "deadhead_callout")
    )
    assert "C-2210" not in {o["crew_id"] for o in options}


def test_an_arriving_crew_member_may_continue_on_the_same_duty(store):
    """Landing at the station with too little rest for a fresh duty, but legal if the covered
    legs join the same flight duty period."""
    from crew_ops_advisor.simulation.positioning import _merge

    ctx = CrewContext.load(store, "C-3310")  # no rostered duties: a clean timeline
    current = DutyPeriod(
        date=date(2026, 9, 15),
        report_utc=at(2026, 9, 15, 3, 0),
        release_utc=at(2026, 9, 15, 8, 0),
        flight_ids=("DX900-2026-09-15", "DX901-2026-09-15"),
        flight_hours=3.5,
        aircraft_type="A320",
        aircraft="VT-DXA",
        dep_station="BLR",
        arr_station="BLR",
        pairing_id="P-TEST",
    )
    covered = DutyPeriod(
        date=date(2026, 9, 15),
        report_utc=at(2026, 9, 15, 8, 30),
        release_utc=at(2026, 9, 15, 13, 0),
        flight_ids=("DX902-2026-09-15", "DX903-2026-09-15", "DX904-2026-09-15"),
        flight_hours=3.75,
        aircraft_type="A320",
        aircraft="VT-DXB",
        dep_station="BLR",
        arr_station="BLR",
        pairing_id="P-COVER",
    )
    ctx = replace(ctx, rostered_duties=(current,))
    fresh = evaluate_duties(ctx, store.ruleset, [covered], replacing=(), callout=True)
    assert not fresh.legal and any("RULE-REST-04" in i for i in fresh.issues)
    merged = _merge(current, covered)
    assert merged.report_utc == at(2026, 9, 15, 3, 0) and merged.sectors == 5
    extended = evaluate_duties(
        ctx, store.ruleset, [merged], replacing=[("P-TEST", date(2026, 9, 15))]
    )
    assert extended.legal  # 10 h FDP against a 13 − 1.5 = 11.5 h limit for five sectors
    fdp = next(v for v in extended.verdicts if v.rule_id == "RULE-FDP-01")
    assert fdp.computed == 10.0 and fdp.limit == 11.5


def test_positioning_tool_and_offline_router(store, registry):
    out = registry.call(
        "positioning_options",
        {"pairing_id": "P-2291", "role": "Captain", "from_date": "2026-09-16"},
    )
    assert out.ok and out.result["options"][0]["crew_id"] == "C-2210"
    bad = registry.call("positioning_options", {"pairing_id": "P-2291", "role": "Pilot"})
    assert not bad.ok and "unknown role" in bad.error

    from crew_ops_advisor.agent import Advisor, OfflineProvider

    advisor = Advisor(store, build_registry(store), OfflineProvider(store))
    text = advisor.ask("Can we fly a Captain in for P-2291 from 2026-09-16?").text
    assert "legal option(s)" in text and "DX588" in text and "hotel overnight" in text


def test_a_what_if_is_a_parameter_not_model_side_editing(registry):
    """'C-2210 is also out' reaches the engine as also_unavailable, so the ranking itself
    escalates — the model never has to drop a candidate by hand."""
    out = registry.call(
        "rank_cover_options",
        {
            "pairing_id": "P-2291",
            "role": "Captain",
            "from_date": "2026-09-16",
            "also_unavailable": ["c-2210"],
        },
    )
    assert out.ok
    r = out.result
    assert r["headline"].startswith("NO LEGAL ON-TIME COVER AT THE STATION")
    assert "C-2210" not in {o["crew_id"] for o in r["options"]}
    assert r["escalation"]["positioning"]["options"][0]["crew_id"] == "C-3310"
    plain = registry.call(
        "rank_cover_options", {"pairing_id": "P-2291", "role": "Captain", "from_date": "2026-09-16"}
    ).result
    assert "headline" not in plain and plain["options"][0]["crew_id"] == "C-2210"
    rc = registry.call(
        "recommend_cover",
        {"crew_id": "C-1042", "from_date": "2026-09-16", "also_unavailable": ["C-2210"]},
    )
    assert rc.ok and rc.result["headline"].startswith("NO LEGAL ON-TIME COVER")
