"""Domain objects -> plain JSON-ready dicts, as the model (and the offline composer) see them."""

from __future__ import annotations

from typing import Any

from crew_ops_advisor.domain.models import (
    Certification,
    Crew,
    DutyPeriod,
    Flight,
    Pairing,
    ReserveEntry,
    RiskSignal,
)
from crew_ops_advisor.domain.timeutil import fmt_utc


def crew_dict(c: Crew) -> dict[str, Any]:
    return {
        "crew_id": c.crew_id,
        "name": c.name,
        "rank": c.rank,
        "base": c.base,
        "ratings": list(c.ratings),
        "seniority": c.seniority,
        "reachability_minutes": c.reachability_minutes,
        "status": c.status,
    }


def flight_dict(f: Flight) -> dict[str, Any]:
    return {
        "flight_id": f.flight_id,
        "flight_no": f.flight_no,
        "date": f.date.isoformat(),
        "route": f"{f.dep_station}-{f.arr_station}",
        "dep_station": f.dep_station,
        "arr_station": f.arr_station,
        "dep_utc": fmt_utc(f.dep_utc),
        "arr_utc": fmt_utc(f.arr_utc),
        "block_hours": f.block_hours,
        "aircraft": f.aircraft,
        "aircraft_type": f.aircraft_type,
        "seats": f.seats,
    }


def duty_dict(d: DutyPeriod) -> dict[str, Any]:
    return {
        "date": d.date.isoformat(),
        "report_utc": fmt_utc(d.report_utc),
        "release_utc": fmt_utc(d.release_utc),
        "duty_hours": round(d.duty_hours, 2),
        "sectors": d.sectors,
        "flight_hours": d.flight_hours,
        "flights": list(d.flight_ids),
        "starts_at": d.dep_station,
        "ends_at": d.arr_station,
    }


def pairing_summary(p: Pairing) -> dict[str, Any]:
    return {
        "pairing_id": p.pairing_id,
        "aircraft": p.aircraft,
        "dates": [d.isoformat() for d in p.dates],
        "flights": [fid for day in p.days for fid in day.flight_ids],
        "crew": [{"crew_id": m.crew_id, "role": m.role} for m in p.crew],
    }


def reserve_dict(r: ReserveEntry, crew: Crew | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "crew_id": r.crew_id,
        "base": r.base,
        "oncall_window_utc": {
            "start": r.oncall_start.strftime("%H:%M"),
            "end": r.oncall_end.strftime("%H:%M"),
        },
        "reserve_dates": [d.isoformat() for d in r.dates],
    }
    if crew is not None:
        out.update(
            {
                "name": crew.name,
                "rank": crew.rank,
                "ratings": list(crew.ratings),
                "reachability_minutes": crew.reachability_minutes,
                "status": crew.status,
            }
        )
    return out


def cert_dict(c: Certification) -> dict[str, Any]:
    return {
        "crew_id": c.crew_id,
        "cert_type": c.cert_type,
        "valid_from": c.valid_from.isoformat(),
        "valid_to": c.valid_to.isoformat(),
    }


def risk_dict(r: RiskSignal) -> dict[str, Any]:
    return {
        "crew_id": r.crew_id,
        "as_of_utc": fmt_utc(r.as_of_utc),
        "disruption_risk_score": r.disruption_risk_score,
        "drivers": list(r.drivers),
    }
