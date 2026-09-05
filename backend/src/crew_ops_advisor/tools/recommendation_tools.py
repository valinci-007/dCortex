"""Tier-3 recommendation tools: ranked options, joint plans, delay recovery, notifications,
and the morning briefing. Deterministic ranking over the rules engine and cost table."""

from __future__ import annotations

from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.timeutil import parse_utc
from crew_ops_advisor.simulation import SimulationError
from crew_ops_advisor.simulation.options import (
    draft_notification,
    joint_cover_plan,
    morning_briefing,
    rank_cover_options,
    recommend_cover,
    resolve_delay_options,
)
from crew_ops_advisor.tools.base import ToolError, ToolRegistry
from crew_ops_advisor.tools.query_tools import RANKS, _date, _str_prop, _utc

TIER = 3


def register_recommendation_tools(registry: ToolRegistry) -> None:
    @registry.tool(
        "recommend_cover",
        "A crew member is out (sick, lapsed certification, removed): the ranked, rule-compliant "
        "options to cover the duty they leave uncovered — reserve callouts, day-off callouts, "
        "deadhead covers from other bases, and cancellation as last resort — each with legality, "
        "rules checked, cost in INR, delay, coverage and reasoning, plus every excluded candidate "
        "with the reason. Use for 'what should I do', 'cheapest legal cover', 'resolve'.",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("The crew member who is out, e.g. C-1042"),
                "pairing_id": _str_prop("The pairing concerned, if named (optional)"),
                "from_date": _str_prop("First day unavailable YYYY-MM-DD (optional)"),
                "reported_utc": _str_prop(
                    "When it was reported, e.g. 2026-09-15T05:00:00Z (optional)"
                ),
                "also_unavailable": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "What-if: other crew ids also out (sick, unavailable) in this scenario, "
                        'e.g. ["C-2210"] — excluded as candidates by the engine'
                    ),
                },
                "max_options": {
                    "type": "integer",
                    "description": "Cap on ranked options returned (default 8)",
                },
            },
            "required": ["crew_id"],
        },
        tier=TIER,
    )
    def recommend_cover_tool(
        store: Datastore,
        crew_id: str,
        pairing_id: str | None = None,
        from_date: str | None = None,
        reported_utc: str | None = None,
        also_unavailable: list[str] | None = None,
        max_options: int = 8,
    ) -> dict[str, Any]:
        try:
            impact, result = recommend_cover(
                store,
                crew_id.upper(),
                pairing_id=pairing_id,
                from_date=_date(from_date, "from_date"),
                reported_utc=_utc(reported_utc, "reported_utc"),
                exclude_crew=tuple(c.upper() for c in (also_unavailable or [])),
                max_options=max(1, int(max_options)),
            )
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
        return {"impact": impact, **result.to_dict()}

    @registry.tool(
        "rank_cover_options",
        "Ranked options to fill one role on a pairing (e.g. the Captain slot of P-2291 from "
        "15 Sep) without naming who is out. Same output as recommend_cover.",
        {
            "type": "object",
            "properties": {
                "pairing_id": _str_prop("Pairing id"),
                "role": _str_prop("Role to fill", enum=list(RANKS)),
                "from_date": _str_prop("First duty day YYYY-MM-DD (default: pairing start)"),
                "also_unavailable": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "What-if: other crew ids also out (sick, unavailable) in this scenario, "
                        'e.g. ["C-2210"] — excluded as candidates by the engine'
                    ),
                },
                "max_options": {
                    "type": "integer",
                    "description": "Cap on ranked options (default 8)",
                },
            },
            "required": ["pairing_id", "role"],
        },
        tier=TIER,
    )
    def rank_cover_options_tool(
        store: Datastore,
        pairing_id: str,
        role: str,
        from_date: str | None = None,
        also_unavailable: list[str] | None = None,
        max_options: int = 8,
    ) -> dict[str, Any]:
        try:
            return rank_cover_options(
                store,
                pairing_id,
                role,
                from_date=_date(from_date, "from_date"),
                exclude_crew=tuple(c.upper() for c in (also_unavailable or [])),
                max_options=max(1, int(max_options)),
            ).to_dict()
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc

    @registry.tool(
        "joint_cover_plan",
        "Several crew out at once (e.g. two captains sick the same morning): the cheapest "
        "combination of legal covers with no person assigned twice, plus each duty's ranked "
        "options. events is a list of {crew_id, pairing_id?, reported_utc?}.",
        {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "description": "One entry per crew member who is out",
                    "items": {
                        "type": "object",
                        "properties": {
                            "crew_id": {"type": "string"},
                            "pairing_id": {"type": "string"},
                            "reported_utc": {"type": "string"},
                            "from_date": {"type": "string"},
                        },
                        "required": ["crew_id"],
                    },
                }
            },
            "required": ["events"],
        },
        tier=TIER,
    )
    def joint_cover_plan_tool(store: Datastore, events: list[dict[str, Any]]) -> dict[str, Any]:
        if not events:
            raise ToolError("events must list at least one crew member")
        parsed = []
        for ev in events:
            if not isinstance(ev, dict) or not ev.get("crew_id"):
                raise ToolError("each event needs a crew_id")
            parsed.append(
                {
                    "crew_id": ev["crew_id"].upper(),
                    "pairing_id": ev.get("pairing_id"),
                    "reported_utc": parse_utc(ev["reported_utc"])
                    if ev.get("reported_utc")
                    else None,
                    "from_date": _date(ev.get("from_date"), "from_date"),
                }
            )
        try:
            return joint_cover_plan(store, parsed)
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc

    @registry.tool(
        "resolve_delay_options",
        "After a delay breaches the crew's FDP: the ranked ways out — the rostered crew flies "
        "the legal prefix of legs and a full reserve set takes the tail, or the tail is "
        "cancelled — each with legality, cost and reasoning.",
        {
            "type": "object",
            "properties": {
                "date": _str_prop("Date YYYY-MM-DD"),
                "delay_hours": {"type": "number", "description": "Delay in hours"},
                "aircraft": _str_prop("Aircraft registration, e.g. VT-DXA"),
                "flight_no": _str_prop("Or the delayed flight number"),
            },
            "required": ["date", "delay_hours"],
        },
        tier=TIER,
    )
    def resolve_delay_options_tool(
        store: Datastore,
        date: str,
        delay_hours: float,
        aircraft: str | None = None,
        flight_no: str | None = None,
    ) -> dict[str, Any]:
        try:
            return resolve_delay_options(
                store, _date(date), float(delay_hours), aircraft=aircraft, flight_no=flight_no
            )
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc

    @registry.tool(
        "draft_callout_notification",
        "Draft the callout message to a crew member covering a pairing, with every operational "
        "fact from the roster: report time/place per day, flights, release, overnight station "
        "and hotel, acknowledgement deadline, contact.",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("Crew member being called out"),
                "pairing_id": _str_prop("Pairing they will cover"),
                "from_date": _str_prop("First duty day YYYY-MM-DD (default: pairing start)"),
                "reason": _str_prop("Reason shown in the message (default: crew unavailability)"),
            },
            "required": ["crew_id", "pairing_id"],
        },
        tier=TIER,
    )
    def draft_callout_notification_tool(
        store: Datastore,
        crew_id: str,
        pairing_id: str,
        from_date: str | None = None,
        reason: str = "crew unavailability",
    ) -> dict[str, Any]:
        try:
            return draft_notification(
                store,
                crew_id.upper(),
                pairing_id,
                from_date=_date(from_date, "from_date"),
                reason=reason,
            )
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc

    @registry.tool(
        "morning_briefing",
        "Standing morning briefing for a date, per aircraft line: today's pairing and report, "
        "each rostered crew member's 7-day duty headroom and certification status, their "
        "disruption-risk score, and which reserves are eligible at the report time.",
        {
            "type": "object",
            "properties": {"date": _str_prop("Date YYYY-MM-DD")},
            "required": ["date"],
        },
        tier=TIER,
    )
    def morning_briefing_tool(store: Datastore, date: str) -> dict[str, Any]:
        return morning_briefing(store, _date(date))

    @registry.tool(
        "watchlist",
        "Proactive watchlist for a date (default tomorrow): crew within a margin of the 7-day "
        "duty limit (RULE-DUTY-02) or the 28-day block limit (RULE-FLT-03) once that day's "
        "rostered duty counts, certifications lapsing within a few days flagged when the crew "
        "member is rostered after the expiry (RULE-CERT-06), and the highest disruption-risk crew. "
        "Use for 'anything I should "
        "worry about tomorrow?', 'who is close to a limit?', 'what needs attention?'.",
        {
            "type": "object",
            "properties": {
                "date": _str_prop("Date YYYY-MM-DD; default tomorrow"),
                "duty_headroom_hours": {
                    "type": "number",
                    "description": "Crew with at most this much 7-day duty headroom (default 10)",
                },
                "certification_days": {
                    "type": "integer",
                    "description": "Certifications expiring within this many days (default 7)",
                },
            },
        },
        tier=TIER,
    )
    def watchlist_tool(
        store: Datastore,
        date: str | None = None,
        duty_headroom_hours: float | None = None,
        certification_days: int | None = None,
    ) -> dict[str, Any]:
        from datetime import timedelta

        from crew_ops_advisor.simulation.watchlist import build_watchlist

        on = _date(date) if date else store.snapshot_utc.date() + timedelta(days=1)
        kwargs: dict[str, Any] = {}
        if duty_headroom_hours is not None:
            kwargs["duty_margin_h"] = float(duty_headroom_hours)
        if certification_days is not None:
            kwargs["cert_days"] = int(certification_days)
        return build_watchlist(store, on, **kwargs)

    @registry.tool(
        "positioning_options",
        "When nobody at the station can legally take a duty: who elsewhere can be flown in "
        "before the departure we are covering? Reads where every qualified crew member is at "
        "report time from the roster (including those landing at the station on their current "
        "trip), finds itineraries on our network — direct, one connection via the hub, or an "
        "earlier flight with a hotel overnight — that land before the departure, checks all "
        "seven rules (a crew member landing there may also continue on the same duty), and "
        "costs callout + positioning + hotel. On-time options (before the scheduled report) "
        "rank first, then late-report options that avoid a delay. Use for 'can we fly someone "
        "in', 'anyone at another airport', 'who is arriving at BLR who could take it'. "
        "rank_cover_options attaches this automatically as `escalation` when it finds no "
        "legal cover at the station.",
        {
            "type": "object",
            "properties": {
                "pairing_id": _str_prop("Pairing id, e.g. P-2291"),
                "role": _str_prop("Captain | First Officer | Senior Cabin Crew | Cabin Crew"),
                "from_date": _str_prop("First day to cover, YYYY-MM-DD (default: pairing start)"),
                "also_unavailable": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "What-if: other crew ids also out (sick, unavailable) in this scenario, "
                        'e.g. ["C-2210"] — excluded as candidates by the engine'
                    ),
                },
                "max_options": {"type": "integer", "description": "Cap on options returned"},
            },
            "required": ["pairing_id", "role"],
        },
        tier=TIER,
    )
    def positioning_options_tool(
        store: Datastore,
        pairing_id: str,
        role: str,
        from_date: str | None = None,
        also_unavailable: list[str] | None = None,
        max_options: int | None = None,
    ) -> dict[str, Any]:
        from crew_ops_advisor.simulation.positioning import positioning_cover

        if role not in RANKS:
            raise ToolError(f"unknown role {role!r} (use one of {', '.join(RANKS)})")
        try:
            return positioning_cover(
                store,
                pairing_id,
                role,
                from_date=_date(from_date, "from_date") if from_date else None,
                exclude_crew=tuple(c.upper() for c in (also_unavailable or [])),
                max_options=max_options,
            ).to_dict()
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
