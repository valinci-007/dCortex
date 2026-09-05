"""Tier-1 query tools: lookups over the dataset. Deterministic, read-only.

Every tool takes the Datastore as its first argument and JSON-schema-validated
keyword arguments after it, and returns a JSON-ready dict. Descriptions are
written for the model: what the tool answers, what the arguments mean, and
the conventions (UTC, ISO dates, exact IDs).
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.timeutil import fmt_utc, parse_utc
from crew_ops_advisor.rules import checks
from crew_ops_advisor.tools.base import ToolError, ToolRegistry
from crew_ops_advisor.tools.serialize import (
    cert_dict,
    crew_dict,
    duty_dict,
    flight_dict,
    pairing_summary,
    reserve_dict,
    risk_dict,
)

RANKS = ("Captain", "First Officer", "Senior Cabin Crew", "Cabin Crew")
STATUSES = ("active", "leave", "training")


def _date(value: str | None, name: str = "date") -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ToolError(f"{name} must be YYYY-MM-DD, got {value!r}") from exc


def _utc(value: str | None, name: str) -> datetime | None:
    if value is None:
        return None
    try:
        return parse_utc(value)
    except ValueError as exc:
        raise ToolError(f"{name} must be like 2026-09-15T12:00:00Z, got {value!r}") from exc


def _str_prop(desc: str, **extra: Any) -> dict[str, Any]:
    return {"type": "string", "description": desc, **extra}


def register_query_tools(registry: ToolRegistry) -> None:
    store = registry.store  # noqa: F841 — handlers receive it per call

    @registry.tool(
        "get_snapshot",
        "Operational context: the snapshot time ('now'), the schedule week, stations, fleet "
        "and cost rates. Call when a question uses relative words (today, tomorrow, this week).",
        {"type": "object", "properties": {}},
    )
    def get_snapshot(store: Datastore) -> dict[str, Any]:
        dates = sorted({f.date for f in store.flights.list()})
        costs = store.costs
        return {
            "snapshot_utc": fmt_utc(store.snapshot_utc),
            "today": store.snapshot_utc.date().isoformat(),
            "tomorrow": (store.snapshot_utc.date() + timedelta(days=1)).isoformat(),
            "schedule_week": {"start": dates[0].isoformat(), "end": dates[-1].isoformat()},
            "stations": store.flights.stations(),
            "fleet": [
                {"aircraft": reg, "aircraft_type": typ} for reg, typ in store.flights.aircraft()
            ],
            "hub": "BLR",
            "currency": costs.currency,
        }

    @registry.tool(
        "get_crew",
        "Profile of one crew member by exact id (e.g. C-1042): name, rank, base, aircraft "
        "ratings, seniority, reachability (minutes to reach), status, reserve on-call window "
        "if they are a reserve, the pairings they are rostered on this week, and their "
        "disruption-risk score.",
        {
            "type": "object",
            "properties": {"crew_id": _str_prop("Crew id, e.g. C-1042")},
            "required": ["crew_id"],
        },
    )
    def get_crew(store: Datastore, crew_id: str) -> dict[str, Any]:
        crew = store.crew.get(crew_id)
        out = crew_dict(crew)
        reserve = store.reserves.get(crew_id)
        out["reserve"] = reserve_dict(reserve) if reserve else None
        out["is_reserve"] = reserve is not None
        out["pairings"] = [
            {
                "pairing_id": p.pairing_id,
                "role": p.role_of(crew_id),
                "aircraft": p.aircraft,
                "dates": [d.isoformat() for d in p.dates],
            }
            for p in store.pairings.for_crew(crew_id)
        ]
        try:
            out["disruption_risk"] = risk_dict(store.risk.get(crew_id))
        except LookupError:
            out["disruption_risk"] = None
        return out

    @registry.tool(
        "list_crew",
        "List crew members matching filters: base station, rank, aircraft rating, status. "
        "Omit a filter to ignore it. Returns the count and each member's profile.",
        {
            "type": "object",
            "properties": {
                "base": _str_prop("Base station code, e.g. BLR or DEL"),
                "rank": _str_prop("One of the crew ranks", enum=list(RANKS)),
                "rating": _str_prop("Aircraft type rating, e.g. A320 or ATR72"),
                "status": _str_prop("Crew status", enum=list(STATUSES)),
            },
        },
    )
    def list_crew(
        store: Datastore,
        base: str | None = None,
        rank: str | None = None,
        rating: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        crew = store.crew.list(base=base, rank=rank, rating=rating, status=status)
        return {
            "filters": {"base": base, "rank": rank, "rating": rating, "status": status},
            "count": len(crew),
            "crew": [crew_dict(c) for c in crew],
        }

    @registry.tool(
        "get_duty_clock",
        "Duty and flight-hour accruals for one crew member as of the snapshot: duty hours in "
        "the last 7 calendar days and block hours in the last 28, the RULE-DUTY-02 (60h/7d) and "
        "RULE-FLT-03 (100h/28d) limits, the remaining headroom under each, the earliest time "
        "they may next report (RULE-REST-04), and the per-day history.",
        {
            "type": "object",
            "properties": {"crew_id": _str_prop("Crew id, e.g. C-1042")},
            "required": ["crew_id"],
        },
    )
    def get_duty_clock(store: Datastore, crew_id: str) -> dict[str, Any]:
        clock = store.duty_clocks.get(crew_id)
        duty_limit = float(store.ruleset.param(checks.DUTY, "max_duty_hours"))
        flight_limit = float(store.ruleset.param(checks.FLT, "max_flight_hours"))
        as_of = clock.as_of_utc.date()
        return {
            "crew_id": crew_id,
            "as_of_utc": fmt_utc(clock.as_of_utc),
            "duty_hours_7d": clock.duty_hours_7d,
            "duty_window_7d": {
                "start": (as_of - timedelta(days=6)).isoformat(),
                "end": as_of.isoformat(),
            },
            "duty_limit_7d": duty_limit,
            "duty_headroom_7d": round(duty_limit - clock.duty_hours_7d, 2),
            "flight_hours_28d": clock.flight_hours_28d,
            "flight_window_28d": {
                "start": (as_of - timedelta(days=27)).isoformat(),
                "end": as_of.isoformat(),
            },
            "flight_limit_28d": flight_limit,
            "flight_headroom_28d": round(flight_limit - clock.flight_hours_28d, 2),
            "last_rest_ended": fmt_utc(clock.last_rest_ended),
            "earliest_next_report_utc": fmt_utc(clock.last_rest_ended),
            "rules": [checks.DUTY, checks.FLT, checks.REST],
            "daily_history": [
                {
                    "date": h.date.isoformat(),
                    "duty_hours": h.duty_hours,
                    "flight_hours": h.flight_hours,
                }
                for h in clock.daily_history
                if h.duty_hours or h.flight_hours
            ],
        }

    @registry.tool(
        "get_flight",
        "One flight leg by flight number and date (e.g. DX412 on 2026-09-15): route, times "
        "(UTC), block hours, aircraft registration and type, seats, and the pairing/crew "
        "operating it.",
        {
            "type": "object",
            "properties": {
                "flight_no": _str_prop("Flight number, e.g. DX412"),
                "date": _str_prop("Date YYYY-MM-DD"),
            },
            "required": ["flight_no", "date"],
        },
    )
    def get_flight(store: Datastore, flight_no: str, date: str) -> dict[str, Any]:
        on = _date(date)
        flight = store.flights.by_number(flight_no.upper(), on)
        if flight is None:
            raise ToolError(f"no flight {flight_no} on {on.isoformat()}")
        out = flight_dict(flight)
        pairing = store.pairings.for_flight(flight.flight_id)
        out["pairing"] = pairing_summary(pairing) if pairing else None
        return out

    @registry.tool(
        "list_flights",
        "Flights matching filters: date, departure station, arrival station, aircraft "
        "registration (e.g. VT-DXA), aircraft type, and a UTC departure-time window. Omit a "
        "filter to ignore it. Returns the count and each leg. Use for 'which flights', "
        "'how many flights', 'flights from X to Y', 'flights this afternoon' (set dep_from_utc/"
        "dep_to_utc).",
        {
            "type": "object",
            "properties": {
                "date": _str_prop("Date YYYY-MM-DD"),
                "dep_station": _str_prop("Departure station code"),
                "arr_station": _str_prop("Arrival station code"),
                "aircraft": _str_prop("Aircraft registration, e.g. VT-DXA"),
                "aircraft_type": _str_prop("Aircraft type, e.g. A320 or ATR72"),
                "dep_from_utc": _str_prop("Earliest departure, e.g. 2026-09-15T12:00:00Z"),
                "dep_to_utc": _str_prop("Latest departure, e.g. 2026-09-15T18:00:00Z"),
            },
        },
    )
    def list_flights(
        store: Datastore,
        date: str | None = None,
        dep_station: str | None = None,
        arr_station: str | None = None,
        aircraft: str | None = None,
        aircraft_type: str | None = None,
        dep_from_utc: str | None = None,
        dep_to_utc: str | None = None,
    ) -> dict[str, Any]:
        flights = store.flights.list(
            on=_date(date),
            dep_station=dep_station.upper() if dep_station else None,
            arr_station=arr_station.upper() if arr_station else None,
            aircraft=aircraft.upper() if aircraft else None,
            aircraft_type=aircraft_type,
            dep_from=_utc(dep_from_utc, "dep_from_utc"),
            dep_to=_utc(dep_to_utc, "dep_to_utc"),
        )
        return {
            "filters": {
                "date": date,
                "dep_station": dep_station,
                "arr_station": arr_station,
                "aircraft": aircraft,
                "aircraft_type": aircraft_type,
                "dep_from_utc": dep_from_utc,
                "dep_to_utc": dep_to_utc,
            },
            "count": len(flights),
            "flight_numbers": sorted({f.flight_no for f in flights}),
            "total_seats": sum(f.seats for f in flights),
            "flights": [flight_dict(f) for f in flights],
        }

    @registry.tool(
        "list_routes",
        "Nonstop destinations served from a station across the schedule week, with flight "
        "counts per destination.",
        {
            "type": "object",
            "properties": {"dep_station": _str_prop("Departure station code, e.g. BLR")},
            "required": ["dep_station"],
        },
    )
    def list_routes(store: Datastore, dep_station: str) -> dict[str, Any]:
        flights = store.flights.list(dep_station=dep_station.upper())
        counts = Counter(f.arr_station for f in flights)
        return {
            "dep_station": dep_station.upper(),
            "destinations": sorted(counts),
            "flights_per_destination": dict(sorted(counts.items())),
            "total_flights": len(flights),
        }

    @registry.tool(
        "schedule_stats",
        "Whole-schedule facts: total flights, flights per day, stations, fleet with seats, and "
        "the longest/shortest block times with the flight numbers that have them.",
        {"type": "object", "properties": {}},
    )
    def schedule_stats(store: Datastore) -> dict[str, Any]:
        flights = store.flights.list()
        per_day = Counter(f.date.isoformat() for f in flights)
        longest = max(f.block_hours for f in flights)
        shortest = min(f.block_hours for f in flights)
        seats = {}
        for f in flights:
            seats[f.aircraft] = {"aircraft_type": f.aircraft_type, "seats": f.seats}
        return {
            "total_flights": len(flights),
            "flights_per_day": dict(sorted(per_day.items())),
            "stations": store.flights.stations(),
            "fleet": [{"aircraft": reg, **info} for reg, info in sorted(seats.items())],
            "longest_block": {
                "block_hours": longest,
                "flight_numbers": sorted(
                    {f.flight_no for f in flights if f.block_hours == longest}
                ),
            },
            "shortest_block": {
                "block_hours": shortest,
                "flight_numbers": sorted(
                    {f.flight_no for f in flights if f.block_hours == shortest}
                ),
            },
        }

    @registry.tool(
        "get_pairing",
        "One pairing (a crew's multi-leg duty, possibly multi-day) by id, e.g. P-2291: "
        "aircraft, each duty day with its flights, report/release times (UTC), duty hours and "
        "sectors, and the assigned crew with roles and names.",
        {
            "type": "object",
            "properties": {"pairing_id": _str_prop("Pairing id, e.g. P-2291")},
            "required": ["pairing_id"],
        },
    )
    def get_pairing(store: Datastore, pairing_id: str) -> dict[str, Any]:
        pairing = store.pairings.get(pairing_id.upper())
        return {
            "pairing_id": pairing.pairing_id,
            "aircraft": pairing.aircraft,
            "days": [duty_dict(d) for d in store.pairings.duty_periods(pairing)],
            "crew": [
                {"crew_id": m.crew_id, "role": m.role, "name": store.crew.get(m.crew_id).name}
                for m in pairing.crew
            ],
        }

    @registry.tool(
        "find_pairings",
        "Find pairings by aircraft registration and/or date, by a crew member, or by a flight. "
        "Use for 'which pairing operates VT-DXB on 16 Sep', 'who is the Senior Cabin Crew on "
        "that aircraft's pairing', 'what is C-1042 flying this week'.",
        {
            "type": "object",
            "properties": {
                "aircraft": _str_prop("Aircraft registration, e.g. VT-DXB"),
                "date": _str_prop("Date YYYY-MM-DD the pairing operates on"),
                "crew_id": _str_prop("Crew id rostered on the pairing"),
                "flight_no": _str_prop("Flight number, e.g. DX412 (combine with date)"),
            },
        },
    )
    def find_pairings(
        store: Datastore,
        aircraft: str | None = None,
        date: str | None = None,
        crew_id: str | None = None,
        flight_no: str | None = None,
    ) -> dict[str, Any]:
        on = _date(date)
        if flight_no:
            if on is None:
                raise ToolError("flight_no needs a date")
            flight = store.flights.by_number(flight_no.upper(), on)
            if flight is None:
                raise ToolError(f"no flight {flight_no} on {on.isoformat()}")
            found = store.pairings.for_flight(flight.flight_id)
            pairings = [found] if found else []
        elif crew_id:
            pairings = store.pairings.for_crew(crew_id)
        else:
            pairings = store.pairings.list()
        if aircraft:
            pairings = [p for p in pairings if p.aircraft == aircraft.upper()]
        if on is not None:
            pairings = [p for p in pairings if on in p.dates]
        return {
            "filters": {
                "aircraft": aircraft,
                "date": date,
                "crew_id": crew_id,
                "flight_no": flight_no,
            },
            "count": len(pairings),
            "pairings": [
                {
                    **pairing_summary(p),
                    "crew": [
                        {
                            "crew_id": m.crew_id,
                            "role": m.role,
                            "name": store.crew.get(m.crew_id).name,
                        }
                        for m in p.crew
                    ],
                }
                for p in pairings
            ],
        }

    @registry.tool(
        "list_reserves",
        "Reserve (standby) crew, optionally filtered by base station and/or a date they are on "
        "reserve: on-call window (UTC), rank, ratings, reachability. A reserve can be called "
        "out only if the required report time falls inside their window (RULE-BASE-07 applies "
        "to base).",
        {
            "type": "object",
            "properties": {
                "station": _str_prop("Base station code, e.g. BLR"),
                "date": _str_prop("Date YYYY-MM-DD"),
            },
        },
    )
    def list_reserves(
        store: Datastore, station: str | None = None, date: str | None = None
    ) -> dict[str, Any]:
        entries = store.reserves.list(base=station.upper() if station else None, on=_date(date))
        return {
            "filters": {"station": station, "date": date},
            "count": len(entries),
            "reserves": [reserve_dict(r, store.crew.get(r.crew_id)) for r in entries],
        }

    @registry.tool(
        "get_certifications",
        "All certifications (licence, medical_class1, recurrent_training, dangerous_goods) for "
        "one crew member with validity dates, and whether each is valid on a given date "
        "(RULE-CERT-06 checks expiry).",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("Crew id"),
                "on_date": _str_prop(
                    "Date YYYY-MM-DD to check validity against (default: snapshot date)"
                ),
            },
            "required": ["crew_id"],
        },
    )
    def get_certifications(
        store: Datastore, crew_id: str, on_date: str | None = None
    ) -> dict[str, Any]:
        store.crew.get(crew_id)
        on = _date(on_date, "on_date") or store.snapshot_utc.date()
        certs = store.certifications.for_crew(crew_id)
        return {
            "crew_id": crew_id,
            "checked_on": on.isoformat(),
            "all_valid": all(c.valid_to >= on for c in certs),
            "certifications": [{**cert_dict(c), "valid_on_date": c.valid_to >= on} for c in certs],
        }

    @registry.tool(
        "list_expiring_certifications",
        "Certifications across all crew that expire within a window: from a start date for a "
        "number of days (default 30). Returns crew id, certification type and expiry date, "
        "soonest first.",
        {
            "type": "object",
            "properties": {
                "from_date": _str_prop("Window start YYYY-MM-DD (e.g. the snapshot or tomorrow)"),
                "within_days": {
                    "type": "integer",
                    "description": "Window length in days (default 30)",
                },
            },
            "required": ["from_date"],
        },
    )
    def list_expiring_certifications(
        store: Datastore, from_date: str, within_days: int = 30
    ) -> dict[str, Any]:
        start = _date(from_date, "from_date")
        end = start + timedelta(days=within_days)
        certs = store.certifications.expiring_between(start, end)
        return {
            "window": {"start": start.isoformat(), "end": end.isoformat(), "days": within_days},
            "count": len(certs),
            "expiring": [
                {
                    **cert_dict(c),
                    "crew_name": store.crew.get(c.crew_id).name,
                    "rank": store.crew.get(c.crew_id).rank,
                }
                for c in certs
            ],
        }

    @registry.tool(
        "get_risk_signal",
        "Pre-computed disruption-risk score (0-1) for one crew member and the drivers behind "
        "it. This is a provided input like a weather forecast, not something we compute.",
        {
            "type": "object",
            "properties": {"crew_id": _str_prop("Crew id")},
            "required": ["crew_id"],
        },
    )
    def get_risk_signal(store: Datastore, crew_id: str) -> dict[str, Any]:
        store.crew.get(crew_id)
        return risk_dict(store.risk.get(crew_id))

    @registry.tool(
        "list_risk_signals",
        "Crew ranked by disruption-risk score (highest first), optionally only those at or "
        "above a threshold, limited to the top N.",
        {
            "type": "object",
            "properties": {
                "min_score": {"type": "number", "description": "Minimum score 0-1 (default 0)"},
                "limit": {"type": "integer", "description": "Max rows (default 10)"},
            },
        },
    )
    def list_risk_signals(
        store: Datastore, min_score: float = 0.0, limit: int = 10
    ) -> dict[str, Any]:
        signals = store.risk.list(min_score=float(min_score))[: max(1, int(limit))]
        return {
            "min_score": min_score,
            "count": len(signals),
            "signals": [
                {
                    **risk_dict(s),
                    "name": store.crew.get(s.crew_id).name,
                    "rank": store.crew.get(s.crew_id).rank,
                }
                for s in signals
            ],
        }

    @registry.tool(
        "get_rules",
        "The legality rulebook: the seven rules (RULE-FDP-01 … RULE-BASE-07) with their text "
        "and numeric parameters, plus definitions (duty period, FDP, sector, reserve callout). "
        "Use to explain what a rule means or its limit.",
        {"type": "object", "properties": {}},
    )
    def get_rules(store: Datastore) -> dict[str, Any]:
        rs = store.ruleset
        return {
            "time_convention": rs.time_convention,
            "definitions": dict(rs.definitions),
            "rules": [
                {"rule_id": r.rule_id, "text": r.text, "params": dict(r.params)}
                for r in rs.rules.values()
            ],
        }

    @registry.tool(
        "get_costs",
        "Cost rates in INR: reserve and day-off callout (pilot/cabin), deadhead positioning, "
        "delay cost per duty hour, cancellation per flight, hotel overnight.",
        {"type": "object", "properties": {}},
    )
    def get_costs(store: Datastore) -> dict[str, Any]:
        c = store.costs
        return {
            "currency": c.currency,
            "reserve_callout_pilot": c.reserve_callout_pilot,
            "reserve_callout_cabin": c.reserve_callout_cabin,
            "dayoff_callout_pilot": c.dayoff_callout_pilot,
            "dayoff_callout_cabin": c.dayoff_callout_cabin,
            "deadhead_positioning": c.deadhead_positioning,
            "delay_cost_per_duty_hour": c.delay_cost_per_duty_hour,
            "cancellation_per_flight": c.cancellation_per_flight,
            "hotel_overnight": c.hotel_overnight,
            "notes": c.notes,
        }


def build_registry(store: Datastore) -> ToolRegistry:
    from crew_ops_advisor.tools.recommendation_tools import register_recommendation_tools
    from crew_ops_advisor.tools.simulation_tools import register_simulation_tools

    registry = ToolRegistry(store)
    register_query_tools(registry)
    register_simulation_tools(registry)
    register_recommendation_tools(registry)
    return registry
