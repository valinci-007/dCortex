"""Repositories hydrate the dataset's engineered facts exactly."""

from datetime import date

import pytest

from crew_ops_advisor.data import NotFoundError
from crew_ops_advisor.domain.timeutil import fmt_utc


def test_crew_c1042_is_the_flagship_captain(store):
    c = store.crew.get("C-1042")
    assert (c.name, c.rank, c.base, c.ratings, c.status) == (
        "A. Nair",
        "Captain",
        "BLR",
        ("A320",),
        "active",
    )
    assert c.reachability_minutes == 90


def test_unknown_ids_raise_not_found(store):
    with pytest.raises(NotFoundError):
        store.crew.get("C-9999")
    with pytest.raises(NotFoundError):
        store.pairings.get("P-0000")
    with pytest.raises(NotFoundError):
        store.flights.get("DX999-2026-09-15")


def test_crew_filters(store):
    del_captains = store.crew.list(base="DEL", rank="Captain")
    assert del_captains and all(c.base == "DEL" and c.rank == "Captain" for c in del_captains)
    atr_only = store.crew.get("C-2091")
    assert atr_only.ratings == ("ATR72",)
    assert "C-2091" not in {c.crew_id for c in store.crew.list(rating="A320")}


def test_pairing_p2291_two_days(store):
    p = store.pairings.get("P-2291")
    assert p.aircraft == "VT-DXC"
    assert p.dates == (date(2026, 9, 15), date(2026, 9, 16))
    assert p.days[0].flight_ids == ("DX412-2026-09-15", "DX413-2026-09-15", "DX588-2026-09-15")
    assert p.days[1].flight_ids == ("DX589-2026-09-16", "DX590-2026-09-16", "DX591-2026-09-16")
    assert p.role_of("C-1042") == "Captain"
    assert store.pairings.for_flight("DX412-2026-09-15").pairing_id == "P-2291"


def test_duty_periods_for_p2291(store):
    duties = store.pairings.duties_for_crew("C-1042")
    assert [d.pairing_id for d in duties] == ["P-2291", "P-2291"]
    assert [d.duty_hours for d in duties] == [9.5, 10.75]
    assert (
        duties[0].sectors == 3 and duties[0].dep_station == "BLR" and duties[0].arr_station == "DEL"
    )
    assert duties[1].dep_station == "DEL"  # the aircraft overnights at DEL


def test_flights_departing_del_on_15_sep(store):
    flights = store.flights.list(on=date(2026, 9, 15), dep_station="DEL")
    assert flights and all(f.dep_station == "DEL" and f.date == date(2026, 9, 15) for f in flights)
    assert [f.dep_utc for f in flights] == sorted(f.dep_utc for f in flights)
    assert store.flights.by_number("DX412", date(2026, 9, 15)).seats == 162


def test_reserves_at_blr_on_15_sep(store):
    entries = {r.crew_id: r for r in store.reserves.list(base="BLR", on=date(2026, 9, 15))}
    assert "C-3310" in entries and "C-2210" not in entries
    r = entries["C-3310"]
    assert (r.oncall_start.hour, r.oncall_end.hour) == (6, 18)
    assert r.covers(store.flights.get("DX412-2026-09-15").dep_utc)


def test_duty_clock_c1042(store):
    clock = store.duty_clocks.get("C-1042")
    assert clock.duty_hours_7d == 20.93 and clock.flight_hours_28d == 64.27
    assert len(clock.daily_history) == 28
    assert clock.daily_history[0].date == date(2026, 8, 18)
    assert clock.daily_history[-1].date == date(2026, 9, 14)
    assert fmt_utc(clock.last_rest_ended) == "2026-09-13T02:00:00Z"


def test_duty_hours_7d_recomputes_from_history_plus_roster_for_every_crew(store):
    """Validator parity: duty_hours_7d == history(8–14 Sep) + rostered duty on 14 Sep."""
    window = (date(2026, 9, 8), date(2026, 9, 14))
    for crew in store.crew.list():
        clock = store.duty_clocks.get(crew.crew_id)
        total = sum(h.duty_hours for h in clock.daily_history if window[0] <= h.date <= window[1])
        total += sum(
            d.duty_hours
            for d in store.pairings.duties_for_crew(crew.crew_id)
            if d.date <= window[1]
        )
        assert abs(round(total, 2) - clock.duty_hours_7d) <= 0.05, crew.crew_id


def test_certifications_and_expiry_query(store):
    certs = {c.cert_type: c for c in store.certifications.for_crew("C-5417")}
    assert set(certs) == {"licence", "medical_class1", "recurrent_training", "dangerous_goods"}
    assert certs["recurrent_training"].valid_to == date(2026, 9, 17)
    expiring = store.certifications.expiring_between(date(2026, 9, 15), date(2026, 10, 15))
    assert any(c.crew_id == "C-5417" and c.cert_type == "recurrent_training" for c in expiring)


def test_risk_signal_and_flagged_exception(store):
    risk = store.risk.get("C-1042")
    assert risk.disruption_risk_score == 0.78 and len(risk.drivers) == 2
    flagged = store.pairings.flagged_exceptions()
    assert [(f.crew_id, f.date, f.rule) for f in flagged] == [
        ("C-5417", date(2026, 9, 19), "RULE-CERT-06")
    ]
