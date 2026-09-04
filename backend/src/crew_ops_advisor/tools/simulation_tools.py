"""Tier-2 simulation tools: consequence and legality questions. Deterministic; every
legality answer comes from the rules engine and carries its evidence and a rendered
explanation the model can quote."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.timeutil import fmt_utc, parse_utc
from crew_ops_advisor.explain import explain_evidence_dict
from crew_ops_advisor.explain.render import legality_sentence
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
from crew_ops_advisor.tools.base import ToolError, ToolRegistry
from crew_ops_advisor.tools.query_tools import RANKS, _date, _str_prop, _utc

TIER = 2


def _window(on: str, start: str, end: str) -> tuple[datetime, datetime]:
    day = _date(on)
    try:
        s = parse_utc(f"{day.isoformat()}T{start}:00Z")
        e = parse_utc(f"{day.isoformat()}T{end}:00Z")
    except ValueError as exc:
        raise ToolError("start/end must be HH:MM (UTC)") from exc
    return s, e


def register_simulation_tools(registry: ToolRegistry) -> None:
    @registry.tool(
        "simulate_crew_removal",
        "A crew member becomes unavailable (sick, no-show, removed). Which rostered flights "
        "lose them right now, which later legs of the same pairing are also at risk, how many "
        "passengers are exposed, and whether the cover must take the whole remaining pairing. "
        "Give the pairing if the controller named one; give reported_utc for a sick call time.",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("Crew id, e.g. C-1042"),
                "pairing_id": _str_prop("Pairing the sick call is for, e.g. P-2291 (optional)"),
                "from_date": _str_prop("First day unavailable, YYYY-MM-DD (optional)"),
                "reported_utc": _str_prop(
                    "When the call came in, e.g. 2026-09-15T05:00:00Z (optional)"
                ),
                "through_date": _str_prop(
                    "Last day unavailable, YYYY-MM-DD, to include later pairings (optional)"
                ),
            },
            "required": ["crew_id"],
        },
        tier=TIER,
    )
    def simulate_crew_removal(
        store: Datastore,
        crew_id: str,
        pairing_id: str | None = None,
        from_date: str | None = None,
        reported_utc: str | None = None,
        through_date: str | None = None,
    ) -> dict[str, Any]:
        try:
            impact = crew_removal(
                store,
                crew_id.upper(),
                from_date=_date(from_date, "from_date"),
                reported_utc=_utc(reported_utc, "reported_utc"),
                pairing_id=pairing_id,
                through_date=_date(through_date, "through_date"),
            )
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
        out = impact.to_dict()
        out["rules"] = ["RULE-QUAL-05"]
        return out

    @registry.tool(
        "check_assignment_legality",
        "Can a crew member operate a pairing (cover it, be moved onto it, or — if already "
        "rostered — still legally fly it)? Evaluates all seven rules over their full timeline, "
        "reports every breach with the numbers, whether a reserve's on-call window covers the "
        "report time, the deadhead positioning plan and delay if they are based elsewhere "
        "(RULE-BASE-07), and the callout cost. Use for 'does anyone breach a limit', 'is it "
        "legal', 'can X cover Y'.",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("Crew id, e.g. C-2087"),
                "pairing_id": _str_prop("Pairing id, e.g. P-2291"),
                "from_date": _str_prop(
                    "First duty day to cover, YYYY-MM-DD (default: the pairing's first day)"
                ),
            },
            "required": ["crew_id", "pairing_id"],
        },
        tier=TIER,
    )
    def check_assignment_legality(
        store: Datastore, crew_id: str, pairing_id: str, from_date: str | None = None
    ) -> dict[str, Any]:
        try:
            check = assignment_check(
                store, crew_id.upper(), pairing_id.upper(), from_date=_date(from_date, "from_date")
            )
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
        out = check.to_dict()
        subject = (
            f"{check.crew_id} covering {check.pairing_id}"
            if check.callout_kind != "rostered"
            else f"{check.crew_id}'s rostered duty on {check.pairing_id}"
        )
        out["summary"] = legality_sentence(out, subject)
        out["explanation"] = explain_evidence_dict(out)
        return out

    @registry.tool(
        "check_rostered_legality",
        "Re-check a crew member's own rostered pairing (or one day of it) against all seven "
        "rules as of now — e.g. after a certification lapse. Reports breaches with details.",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("Crew id"),
                "pairing_id": _str_prop("Pairing id (optional if a date is given)"),
                "date": _str_prop("One duty date YYYY-MM-DD (optional)"),
            },
            "required": ["crew_id"],
        },
        tier=TIER,
    )
    def check_rostered_legality(
        store: Datastore, crew_id: str, pairing_id: str | None = None, date: str | None = None
    ) -> dict[str, Any]:
        on = _date(date)
        pairings = store.pairings.for_crew(crew_id.upper())
        if pairing_id:
            pairings = [p for p in pairings if p.pairing_id == pairing_id.upper()]
        if on is not None:
            pairings = [p for p in pairings if on in p.dates]
        if not pairings:
            raise ToolError(f"{crew_id} has no rostered pairing matching those filters")
        results = []
        for p in pairings:
            try:
                check = assignment_check(store, crew_id.upper(), p.pairing_id, from_date=on)
            except SimulationError as exc:
                raise ToolError(str(exc)) from exc
            d = check.to_dict()
            if on is not None:
                d["duty_dates"] = [on.isoformat()]
            d["summary"] = legality_sentence(
                d, f"{check.crew_id}'s rostered duty on {p.pairing_id}"
            )
            d["explanation"] = explain_evidence_dict(d)
            results.append(d)
        return {"crew_id": crew_id.upper(), "count": len(results), "pairings": results}

    @registry.tool(
        "station_closure_impact",
        "A station is closed to departures and arrivals for a window on a date. Lists every "
        "affected flight with the minimum delay to reopen (+30 min turnaround), the operating "
        "crew's FDP after that delay vs the RULE-FDP-01 limit, and whether tail legs need "
        "re-crewing or cancellation. Times are UTC HH:MM.",
        {
            "type": "object",
            "properties": {
                "station": _str_prop("Station code, e.g. BLR"),
                "date": _str_prop("Date YYYY-MM-DD"),
                "start": _str_prop("Closure start, HH:MM UTC"),
                "end": _str_prop("Closure end, HH:MM UTC"),
            },
            "required": ["station", "date", "start", "end"],
        },
        tier=TIER,
    )
    def station_closure_impact(
        store: Datastore, station: str, date: str, start: str, end: str
    ) -> dict[str, Any]:
        s, e = _window(date, start, end)
        try:
            return station_closure(store, station, s, e).to_dict()
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc

    @registry.tool(
        "simulate_delay",
        "An aircraft's remaining legs on a date are delayed by N hours (technical delay before "
        "a flight). Reports the duty's FDP after the delay vs the RULE-FDP-01 limit, every "
        "rostered crew member's full legality check, how many legs they can still legally "
        "complete, and which tail legs need re-crewing.",
        {
            "type": "object",
            "properties": {
                "date": _str_prop("Date YYYY-MM-DD"),
                "delay_hours": {
                    "type": "number",
                    "description": "Delay in hours, e.g. 1.5 for 90 minutes",
                },
                "aircraft": _str_prop("Aircraft registration, e.g. VT-DXA"),
                "flight_no": _str_prop("Or the delayed flight number, e.g. DX401"),
            },
            "required": ["date", "delay_hours"],
        },
        tier=TIER,
    )
    def simulate_delay(
        store: Datastore,
        date: str,
        delay_hours: float,
        aircraft: str | None = None,
        flight_no: str | None = None,
    ) -> dict[str, Any]:
        try:
            impact = delay(
                store, _date(date), float(delay_hours), aircraft=aircraft, flight_no=flight_no
            )
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
        out = impact.to_dict()
        for c in out["crew_checks"]:
            c["explanation"] = explain_evidence_dict(c)
        return out

    @registry.tool(
        "cancellation_impact",
        "If a flight leg is cancelled: passengers affected (seats), the direct cancellation "
        "cost from the cost table, and the pairing/crew released.",
        {
            "type": "object",
            "properties": {
                "flight_no": _str_prop("Flight number, e.g. DX404"),
                "date": _str_prop("Date YYYY-MM-DD"),
            },
            "required": ["flight_no", "date"],
        },
        tier=TIER,
    )
    def cancellation_impact(store: Datastore, flight_no: str, date: str) -> dict[str, Any]:
        try:
            return cancellation(store, flight_no, _date(date)).to_dict()
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc

    @registry.tool(
        "crew_near_limits",
        "Crew approaching their rolling limits as of a date, counting history plus rostered "
        "duty through that date: duty hours in the 7-day window (RULE-DUTY-02, 60h) and "
        "block hours in the 28-day window (RULE-FLT-03, 100h). Default: 45h or more duty. "
        "Use for proactive alerts and 'who has 45+ hours' questions.",
        {
            "type": "object",
            "properties": {
                "date": _str_prop("Window end date YYYY-MM-DD"),
                "min_duty_hours": {
                    "type": "number",
                    "description": "Report crew at or above this 7-day duty total (default 45)",
                },
                "max_duty_headroom": {
                    "type": "number",
                    "description": "Or crew with this much or less 7-day duty headroom",
                },
                "max_flight_headroom": {
                    "type": "number",
                    "description": "Or crew with this much or less 28-day block headroom",
                },
            },
            "required": ["date"],
        },
        tier=TIER,
    )
    def crew_near_limits(
        store: Datastore,
        date: str,
        min_duty_hours: float | None = None,
        max_duty_headroom: float | None = None,
        max_flight_headroom: float | None = None,
    ) -> dict[str, Any]:
        rows = near_limits(
            store,
            _date(date),
            min_duty_hours=min_duty_hours,
            max_duty_headroom=max_duty_headroom,
            max_flight_headroom=max_flight_headroom,
        )
        return {
            "date": date,
            "criteria": {
                "min_duty_hours": 45.0
                if (
                    min_duty_hours is None
                    and max_duty_headroom is None
                    and max_flight_headroom is None
                )
                else min_duty_hours,
                "max_duty_headroom": max_duty_headroom,
                "max_flight_headroom": max_flight_headroom,
            },
            "count": len(rows),
            "crew": [r.to_dict() for r in rows],
            "rules": ["RULE-DUTY-02", "RULE-FLT-03"],
        }

    @registry.tool(
        "reserve_coverage",
        "Which reserves could be called out for a duty that must report at a given UTC time: "
        "on reserve that day, on-call window covers the report time, and (if given) matching "
        "rank, aircraft rating (RULE-QUAL-05) and base (RULE-BASE-07). Returns eligible and "
        "excluded reserves with the reason for each.",
        {
            "type": "object",
            "properties": {
                "required_report_utc": _str_prop("Report time, e.g. 2026-09-16T03:00:00Z"),
                "rank": _str_prop("Rank needed", enum=list(RANKS)),
                "aircraft_type": _str_prop("Aircraft type rating needed, e.g. ATR72"),
                "station": _str_prop("Station the duty starts at, e.g. BLR"),
            },
            "required": ["required_report_utc"],
        },
        tier=TIER,
    )
    def reserve_coverage_tool(
        store: Datastore,
        required_report_utc: str,
        rank: str | None = None,
        aircraft_type: str | None = None,
        station: str | None = None,
    ) -> dict[str, Any]:
        at = _utc(required_report_utc, "required_report_utc")
        rows = reserve_coverage(store, at, rank=rank, aircraft_type=aircraft_type, station=station)
        return {
            "required_report_utc": fmt_utc(at),
            "filters": {"rank": rank, "aircraft_type": aircraft_type, "station": station},
            "eligible": [r.crew_id for r in rows if r.eligible],
            "excluded": [
                {"crew_id": r.crew_id, "reason": r.reason} for r in rows if not r.eligible
            ],
            "candidates": [r.to_dict() for r in rows],
            "rules": ["RULE-QUAL-05", "RULE-BASE-07"],
        }

    @registry.tool(
        "earliest_next_report",
        "RULE-REST-04: the earliest a crew member may report after being released at a UTC "
        "time (release + minimum rest).",
        {
            "type": "object",
            "properties": {"release_utc": _str_prop("Release time, e.g. 2026-09-16T15:30:00Z")},
            "required": ["release_utc"],
        },
        tier=TIER,
    )
    def earliest_next_report(store: Datastore, release_utc: str) -> dict[str, Any]:
        release = _utc(release_utc, "release_utc")
        assert release is not None
        report = earliest_report(store, release)
        return {
            "release_utc": fmt_utc(release),
            "earliest_report_utc": fmt_utc(report),
            "min_rest_hours": store.ruleset.param("RULE-REST-04", "min_rest_hours"),
            "rule": "RULE-REST-04",
        }

    @registry.tool(
        "seats_at_risk",
        "Which single flight leg has the most seats at risk if cancelled, by aircraft type, "
        "with the cancellation cost per leg.",
        {"type": "object", "properties": {}},
        tier=TIER,
    )
    def seats_at_risk_tool(store: Datastore) -> dict[str, Any]:
        return seats_at_risk(store)
