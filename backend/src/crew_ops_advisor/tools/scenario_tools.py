"""Scenario workspace tools (ADR-0018 §3): the controller's working situation for one
conversation — sick calls declared, covers committed — so later questions are answered
against the roster as it now stands.

The model never mutates state directly: it calls these typed tools, deterministic code
validates (a cover is committed only after the full seven-rule check says it is legal) and
records the change on the conversation's Scenario. Only usable when the registry was built
on a ScenarioStore; on the plain Datastore they explain that no workspace is available.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from crew_ops_advisor.simulation import SimulationError
from crew_ops_advisor.simulation.engine import crew_removal
from crew_ops_advisor.simulation.options import rank_cover_options
from crew_ops_advisor.simulation.scenario import Cover, ScenarioStore
from crew_ops_advisor.tools.base import ToolError, ToolRegistry
from crew_ops_advisor.tools.query_tools import _date, _str_prop

TIER = 3


def _workspace(store: Any) -> ScenarioStore:
    if not isinstance(store, ScenarioStore):
        raise ToolError(
            "no scenario workspace in this context — declare and apply changes from a "
            "conversation on the desk"
        )
    return store


def _status(store: ScenarioStore) -> dict[str, Any]:
    scenario = store.scenario
    return {
        "empty": scenario.empty,
        "unavailable": [u.to_dict() for u in scenario.unavailable.values()],
        "covers": [c.to_dict() for c in scenario.covers],
        "vacancies": scenario.vacancies(store),  # the roster as it now stands, covers included
        "committed_cost_inr": scenario.committed_cost_inr,
        "summary": scenario.summary(),
    }


def register_scenario_tools(registry: ToolRegistry) -> None:
    @registry.tool(
        "declare_unavailable",
        "Record on the desk's working scenario that a crew member is unavailable from a date "
        "(sick call, no-show, lapsed certification) and return the impact: the pairing days "
        "now vacant, the flights and passengers exposed. Every later question in this "
        "conversation is answered with this person unavailable and their duties vacant until "
        "a cover is applied. Use when the controller reports the event, not when they only "
        "ask 'what if'.",
        {
            "type": "object",
            "properties": {
                "crew_id": _str_prop("Crew id, e.g. C-1042"),
                "from_date": _str_prop("First day unavailable, YYYY-MM-DD (default: tomorrow)"),
                "reason": _str_prop("sick | no-show | certification | other (default sick)"),
            },
            "required": ["crew_id"],
        },
        tier=TIER,
    )
    def declare_unavailable(
        store: Any, crew_id: str, from_date: str | None = None, reason: str = "sick"
    ) -> dict[str, Any]:
        ws = _workspace(store)
        crew_id = crew_id.upper()
        crew = ws.base.crew.get(crew_id)  # NotFoundError → clean tool error
        on = (
            _date(from_date, "from_date")
            if from_date
            else ws.snapshot_utc.date() + timedelta(days=1)
        )
        try:
            impact = crew_removal(ws, crew_id, from_date=on)
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
        entry = ws.scenario.declare_unavailable(crew_id, on, reason or "sick")
        return {
            "declared": {**entry.to_dict(), "name": crew.name, "rank": crew.rank},
            "impact": impact.to_dict(),
            "scenario": _status(ws),
            "note": (
                f"{crew_id} is now unavailable from {on.isoformat()} in this conversation; "
                "their pairing days are vacant until a cover is applied with apply_cover."
            ),
        }

    @registry.tool(
        "apply_cover",
        "Commit a cover on the desk's working scenario: `crew_id` takes over `replacing`'s "
        "slot on `pairing_id` from `from_date`. Runs the full seven-rule legality check and "
        "costs the callout first; an illegal or ineligible cover is refused with the verdict "
        "and nothing is recorded. Use only when the controller decides to apply, assign or go "
        "with an option — ranking options is recommend_cover / rank_cover_options.",
        {
            "type": "object",
            "properties": {
                "pairing_id": _str_prop("Pairing id, e.g. P-2291"),
                "crew_id": _str_prop("Who takes the duty, e.g. C-3310"),
                "replacing": _str_prop("Whose slot it is, e.g. C-1042"),
                "from_date": _str_prop("First day covered, YYYY-MM-DD (default: pairing start)"),
            },
            "required": ["pairing_id", "crew_id", "replacing"],
        },
        tier=TIER,
    )
    def apply_cover(
        store: Any, pairing_id: str, crew_id: str, replacing: str, from_date: str | None = None
    ) -> dict[str, Any]:
        ws = _workspace(store)
        pairing_id, crew_id, replacing = pairing_id.upper(), crew_id.upper(), replacing.upper()
        pairing = ws.base.pairings.get(pairing_id)
        on = _date(from_date, "from_date") if from_date else pairing.days[0].date
        members = ws.scenario.members_on(pairing, on)
        slot = next((m for m in members if m.crew_id == replacing), None)
        if slot is None:
            raise ToolError(
                f"{replacing} does not hold a slot on {pairing_id} on {on.isoformat()} "
                f"(crew that day: {', '.join(f'{m.crew_id} {m.role}' for m in members)})"
            )
        crew = ws.crew.get(crew_id)
        if crew.rank != slot.role:
            return {
                "applied": False,
                "reason": f"{crew_id} is a {crew.rank}; the slot needs a {slot.role}",
                "scenario": _status(ws),
            }
        if crew.status != "active":
            return {
                "applied": False,
                "reason": f"{crew_id} is {crew.status} and cannot be assigned",
                "scenario": _status(ws),
            }
        try:
            ranking = rank_cover_options(ws, pairing_id, slot.role, from_date=on)
        except SimulationError as exc:
            raise ToolError(str(exc)) from exc
        option = next((o for o in ranking.options if o.crew_id == crew_id and o.legal), None)
        if option is None:
            excluded = next((x for x in ranking.excluded if x.crew_id == crew_id), None)
            return {
                "applied": False,
                "reason": excluded.reason
                if excluded is not None
                else f"{crew_id} is not a legal cover for {pairing_id} from {on.isoformat()}",
                "legal_alternatives": [o.to_dict() for o in ranking.options[:3]],
                "scenario": _status(ws),
            }
        cover = Cover(
            pairing_id,
            on,
            slot.role,
            crew_id,
            replacing,
            kind=option.kind,
            cost_inr=option.cost_inr,
        )
        ws.scenario.apply_cover(cover)
        return {
            "applied": True,
            "cover": cover.to_dict(),
            "option": option.to_dict(),
            "scenario": _status(ws),
            "note": (
                f"{crew_id} now flies {pairing_id} as {slot.role} from {on.isoformat()}; "
                "the roster, reserve list and duty clocks in this conversation reflect it."
            ),
        }

    @registry.tool(
        "scenario_status",
        "The desk's working scenario for this conversation: crew declared unavailable, covers "
        "applied with their cost, pairing days still vacant, and the committed cost so far. "
        "Use for 'what have we changed', 'what is still uncovered', 'where are we'.",
        {"type": "object", "properties": {}},
        tier=TIER,
    )
    def scenario_status(store: Any) -> dict[str, Any]:
        return _status(_workspace(store))

    @registry.tool(
        "reset_scenario",
        "Clear the desk's working scenario for this conversation: everyone declared "
        "unavailable is available again and every applied cover is undone. Use only when the "
        "controller asks to start over or discard the scenario.",
        {"type": "object", "properties": {}},
        tier=TIER,
    )
    def reset_scenario(store: Any) -> dict[str, Any]:
        ws = _workspace(store)
        before = ws.scenario.summary()
        ws.scenario.reset()
        return {"reset": True, "discarded": before, "scenario": _status(ws)}
