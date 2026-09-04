"""Each Tier-1 tool reproduces the relevant answer key when called directly (no model)."""

import json


def call(registry, name, **args):
    out = registry.call(name, args)
    assert out.ok, out.error
    json.dumps(out.result)  # must be JSON-serialisable for the model
    return out.result


def test_q01_reserves_at_blr_on_15_sep(registry):
    r = call(registry, "list_reserves", station="BLR", date="2026-09-15")
    by_id = {x["crew_id"]: x for x in r["reserves"]}
    assert r["count"] == 12 and "C-2210" not in by_id
    assert by_id["C-3310"]["oncall_window_utc"] == {"start": "06:00", "end": "18:00"}
    assert by_id["C-3310"]["rank"] == "Captain" and by_id["C-3310"]["reachability_minutes"] == 45


def test_q02_q13_duty_clock_headroom_and_flight_hours(registry):
    c = call(registry, "get_duty_clock", crew_id="C-1042")
    assert (c["duty_hours_7d"], c["duty_headroom_7d"], c["duty_limit_7d"]) == (20.93, 39.07, 60.0)
    assert c["duty_window_7d"] == {"start": "2026-09-08", "end": "2026-09-14"}
    c = call(registry, "get_duty_clock", crew_id="C-2087")
    assert c["flight_hours_28d"] == 23.5


def test_q03_q09_q10_flight_lists(registry):
    assert call(registry, "list_flights", date="2026-09-15", dep_station="DEL")[
        "flight_numbers"
    ] == ["DX402"]
    r = call(registry, "list_flights", date="2026-09-17", dep_station="BLR", arr_station="BOM")
    assert r["flight_numbers"] == ["DX412", "DX431"]
    assert call(registry, "list_flights", date="2026-09-16")["count"] == 21


def test_q04_expiring_certifications(registry):
    r = call(registry, "list_expiring_certifications", from_date="2026-09-15", within_days=30)
    assert r["count"] == 6 and r["window"]["end"] == "2026-10-15"
    assert [(x["crew_id"], x["cert_type"]) for x in r["expiring"]][:2] == [
        ("C-5417", "recurrent_training"),
        ("C-2087", "licence"),
    ]


def test_q05_flight_lookup(registry):
    f = call(registry, "get_flight", flight_no="dx412", date="2026-09-15")
    assert (f["aircraft"], f["aircraft_type"], f["seats"]) == ("VT-DXC", "A320", 162)
    assert f["pairing"]["pairing_id"] == "P-2291"


def test_q06_q07_crew_profiles(registry):
    c = call(registry, "get_crew", crew_id="C-3310")
    assert c["reserve"]["oncall_window_utc"] == {"start": "06:00", "end": "18:00"}
    assert c["reachability_minutes"] == 45 and c["pairings"] == []
    c = call(registry, "get_crew", crew_id="C-2210")
    assert (c["base"], c["ratings"]) == ("DEL", ["A320"])
    c = call(registry, "get_crew", crew_id="C-1042")
    assert (
        c["pairings"][0]["pairing_id"] == "P-2291"
        and c["disruption_risk"]["disruption_risk_score"] == 0.78
    )


def test_q08_pairing(registry):
    p = call(registry, "get_pairing", pairing_id="P-2291")
    assert [(m["crew_id"], m["role"]) for m in p["crew"]][:3] == [
        ("C-1042", "Captain"),
        ("C-1694", "First Officer"),
        ("C-3005", "Senior Cabin Crew"),
    ]
    assert [d["duty_hours"] for d in p["days"]] == [9.5, 10.75]


def test_q11_crew_list(registry):
    r = call(registry, "list_crew", base="DEL", rank="Captain")
    assert [c["crew_id"] for c in r["crew"]] == ["C-2210"]


def test_q12_schedule_stats(registry):
    s = call(registry, "schedule_stats")
    assert s["longest_block"] == {
        "block_hours": 2.75,
        "flight_numbers": ["DX401", "DX402", "DX588", "DX589"],
    }
    assert s["total_flights"] == 147 and s["flights_per_day"]["2026-09-16"] == 21


def test_q14_routes(registry):
    r = call(registry, "list_routes", dep_station="blr")
    assert r["destinations"] == ["BOM", "CCU", "COK", "DEL", "GOI", "HYD", "MAA"]


def test_q15_find_pairing_by_aircraft_and_date(registry):
    r = call(registry, "find_pairings", aircraft="VT-DXB", date="2026-09-16")
    assert r["count"] == 1
    scc = [m for m in r["pairings"][0]["crew"] if m["role"] == "Senior Cabin Crew"]
    assert [m["crew_id"] for m in scc] == ["C-3171"]


def test_q16_risk(registry):
    r = call(registry, "get_risk_signal", crew_id="C-1042")
    assert (
        r["disruption_risk_score"] == 0.78
        and r["drivers"][0] == "short-rest pattern over last 14 days"
    )


def test_snapshot_rules_costs(registry):
    s = call(registry, "get_snapshot")
    assert (s["today"], s["tomorrow"]) == ("2026-09-14", "2026-09-15")
    assert s["schedule_week"] == {"start": "2026-09-14", "end": "2026-09-20"}
    assert len(call(registry, "get_rules")["rules"]) == 7
    assert call(registry, "get_costs")["reserve_callout_pilot"] == 18500


def test_errors_are_structured(registry):
    assert "unknown crew" in registry.call("get_crew", {"crew_id": "C-9999"}).error
    assert "must be YYYY-MM-DD" in registry.call("list_flights", {"date": "15/09/2026"}).error
    assert (
        "no flight DX999"
        in registry.call("get_flight", {"flight_no": "DX999", "date": "2026-09-15"}).error
    )
    assert "unknown argument" in registry.call("list_crew", {"station": "BLR"}).error
