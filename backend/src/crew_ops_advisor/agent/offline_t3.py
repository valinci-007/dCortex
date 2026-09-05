"""Tier-3 planning and composition for the offline router: recommendations, joint plans,
delay recovery, notifications, the morning briefing."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from crew_ops_advisor.agent.entities import Entities
from crew_ops_advisor.agent.offline_t2 import (
    Results,
    _err,
    _reasoning,
    _refused,
    compose_closure,
    delay_hours_from,
    reported_utc_from,
)
from crew_ops_advisor.agent.types import ToolCall
from crew_ops_advisor.data import Datastore

RECOMMEND_RE = re.compile(
    r"\b(what should|what do i do|recommend\w*|options?|resolve|resolution|cheapest|best way|"
    r"how (?:do|should) (?:i|we)|plan|handle)\b",
    re.I,
)


class T3Planner:
    def __init__(self, store: Datastore):
        self._store = store
        self._snapshot = store.snapshot_utc.date()

    def plan(self, text: str, e: Entities, call: Callable[..., ToolCall]):  # noqa: C901
        low = text.lower()
        has = lambda *words: any(re.search(rf"\b{w}\b", low) for w in words)  # noqa: E731

        # -- scenario workspace (ADR-0018 §3): explicit verbs only ------------------------
        if has("reset") and has("scenario", "workspace", "start over"):
            return "scenario_reset", (call("reset_scenario"),), compose_scenario_reset
        if has("scenario", "workspace") and has(
            "status", "changed", "committed", "vacant", "where are we"
        ):
            return "scenario_status", (call("scenario_status"),), compose_scenario_status
        if (
            has("record", "declare", "log")
            and e.crew_id
            and has("sick", "unavailable", "out", "no-show", "lapsed")
        ):
            args = {"crew_id": e.crew_id}
            if e.date:
                args["from_date"] = e.date.isoformat()
            args["reason"] = "certification" if has("lapsed", "certif\\w*") else "sick"
            return "scenario_declare", (call("declare_unavailable", **args),), compose_declare
        if has("apply", "assign", "commit") and len(e.crew_ids) >= 2 and e.pairing_ids:
            args = {
                "pairing_id": e.pairing_ids[0],
                "crew_id": e.crew_ids[0],
                "replacing": e.crew_ids[1],
            }
            if e.date:
                args["from_date"] = e.date.isoformat()
            return "scenario_apply", (call("apply_cover", **args),), compose_apply

        # -- notification drafting ----------------------------------------------------
        if (
            has("draft", "notif\\w*", "message", "notify", "callout message")
            and e.crew_id
            and e.pairing_ids
        ):
            args = {"crew_id": e.crew_id, "pairing_id": e.pairing_ids[0]}
            if e.date and re.search(r"\bfrom\s+\d", low):
                args["from_date"] = e.date.isoformat()
            return (
                "notification",
                (call("draft_callout_notification", **args),),
                compose_notification,
            )

        # -- morning briefing ------------------------------------------------------------
        if has("briefing", "brief"):
            on = e.date or (self._snapshot + timedelta(days=1))
            return "briefing", (call("morning_briefing", date=on.isoformat()),), compose_briefing

        if not RECOMMEND_RE.search(low):
            return None

        # -- closure recovery plan (per-flight assessment is the plan) --------------------
        if has("closed", "closes", "closure", "shut") and e.stations and e.time_window:
            on = e.date or self._snapshot
            return (
                "closure_plan",
                (
                    call(
                        "station_closure_impact",
                        station=e.stations[0],
                        date=on.isoformat(),
                        start=e.time_window[0],
                        end=e.time_window[1],
                    ),
                ),
                compose_closure,
            )

        # -- delay recovery ----------------------------------------------------------------
        if has("delay\\w*", "fdp breach") and (e.aircraft or e.flight_nos):
            hours = delay_hours_from(text)
            if hours:
                on = e.date or self._snapshot
                args: dict[str, Any] = {"date": on.isoformat(), "delay_hours": hours}
                if e.aircraft:
                    args["aircraft"] = e.aircraft[0]
                else:
                    args["flight_no"] = e.flight_nos[0]
                return (
                    "delay_options",
                    (call("resolve_delay_options", **args),),
                    compose_delay_options,
                )

        # -- several crew out at once -------------------------------------------------------
        if has("both", "two", "multiple", "simultaneous\\w*", "joint") and (
            len(e.crew_ids) >= 2 or len(e.aircraft) >= 2
        ):
            events = self._events(text, e)
            if len(events) >= 2:
                return "joint_plan", (call("joint_cover_plan", events=events),), compose_joint_plan

        # -- one crew member out: ranked cover -------------------------------------------------
        crew_id = e.crew_id or self._crew_from_aircraft(e)
        if crew_id:
            args = {"crew_id": crew_id}
            if e.pairing_ids:
                args["pairing_id"] = e.pairing_ids[0]
            when = reported_utc_from(text, e, self._snapshot)
            if when:
                args["reported_utc"] = when
            elif e.date:
                args["from_date"] = e.date.isoformat()
            return "recommend", (call("recommend_cover", **args),), compose_recommend
        return None

    # ---- lookups ------------------------------------------------------------------------

    def _crew_from_aircraft(self, e: Entities) -> str | None:
        """'the VT-DXF First Officer on 20 Sep' -> that crew member."""
        if not e.aircraft or not e.ranks:
            return None
        on = e.date or (self._snapshot + timedelta(days=1))
        pairing = self._store.pairings.for_aircraft_on(e.aircraft[0], on)
        if pairing is None:
            return None
        member = next((m for m in pairing.crew if m.role == e.ranks[0]), None)
        return member.crew_id if member else None

    def _events(self, text: str, e: Entities) -> list[dict[str, Any]]:
        when = reported_utc_from(text, e, self._snapshot)
        events: list[dict[str, Any]] = []
        if len(e.crew_ids) >= 2:
            for cid in e.crew_ids:
                ev: dict[str, Any] = {"crew_id": cid}
                if when:
                    ev["reported_utc"] = when
                events.append(ev)
            return events
        on = e.date or (self._snapshot + timedelta(days=1))
        role = e.ranks[0] if e.ranks else "Captain"
        for reg in e.aircraft:
            pairing = self._store.pairings.for_aircraft_on(reg, on)
            if pairing is None:
                continue
            member = next((m for m in pairing.crew if m.role == role), None)
            if member:
                ev = {"crew_id": member.crew_id, "pairing_id": pairing.pairing_id}
                if when:
                    ev["reported_utc"] = when
                events.append(ev)
        return events


# ----------------------------------------------------------------- composers


def _option_line(o: dict[str, Any]) -> str:
    legal = "legal" if o["legal"] else "NOT legal"
    delay = f", delay {o['delay_hours']:g}h" if o.get("delay_hours") else ""
    return f"{o['rank']}. {o['action']} — {o['cost_inr']:.0f} INR, {legal}{delay}. {o.get('reasoning', '')}".rstrip()


def compose_recommend(r: Results) -> str:
    if err := _err(r, "recommend_cover"):
        return _refused("recommend_cover", err)
    x = r["recommend_cover"]
    best = x["expected_choice"]
    legs = ", ".join(f.split("-")[0] for f in x["uncovered_flights"])
    head = (
        f"Recommended: {best['action']} — {best['cost_inr']:.0f} INR. {best['reasoning']} "
        f"This covers {x['pairing_id']} ({x['role']} slot, {', '.join(x['duty_dates'])}: {legs}; "
        f"{x['passengers_at_risk']} passengers at risk)."
    )
    ranked = "\n".join(_option_line(o) for o in x["options"])
    excluded = "\n".join(f"- {e['crew_id']}: {e['reason']}" for e in x["excluded_candidates"][:8])
    more = len(x["excluded_candidates"]) - 8
    rules = ", ".join(best["rules_checked"]) if best["rules_checked"] else "n/a"
    return (
        head
        + "\n\nRanked options:\n"
        + ranked
        + (
            "\n\nExcluded candidates:\n" + excluded + (f"\n- … and {more} more" if more > 0 else "")
            if excluded
            else ""
        )
        + "\n\n"
        + _reasoning(
            f"recommend_cover: {x['candidates_considered']} candidates of rank {x['role']} considered; "
            f"rules checked on the recommended option: {rules}",
            x["note"],
            "costs from costs.json: reserve/day-off callout, deadhead positioning + delay per duty hour, cancellation per leg",
        )
    )


def compose_joint_plan(r: Results) -> str:
    if err := _err(r, "joint_cover_plan"):
        return _refused("joint_cover_plan", err)
    x = r["joint_cover_plan"]
    lines = []
    for p in x["plan"]:
        rules = ", ".join(p["rules_checked"]) or "n/a"
        lines.append(
            f"- {p['pairing_id']} ({p['role']}): {p['action']} — {p['cost_inr']:.0f} INR, "
            f"{'legal' if p['legal'] else 'NOT legal'} (rules checked: {rules}). {p['reasoning']}"
        )
    per = []
    for ev in x["events"]:
        opts = "; ".join(
            f"{o['rank']}. {o['action']} ({o['cost_inr']:.0f})" for o in ev["options"][:4]
        )
        per.append(f"- {ev['pairing_id']} ({ev['crew_id']} out): {opts}")
    return (
        f"Optimal joint plan — total {x['total_cost_inr']:.0f} INR:\n"
        + "\n".join(lines)
        + "\n\nPer-duty ranked options:\n"
        + "\n".join(per)
        + "\n\n"
        + _reasoning(
            "joint_cover_plan: options ranked per duty, then the cheapest combination with no "
            "person assigned twice",
            x["note"],
        )
    )


def compose_delay_options(r: Results) -> str:
    if err := _err(r, "resolve_delay_options"):
        return _refused("resolve_delay_options", err)
    x = r["resolve_delay_options"]
    if not x.get("options"):
        return (
            f"No action needed: with a {x['delay_hours']:g}h delay the duty runs {x['fdp_after_delay']:.2f}h, "
            f"inside the {x['fdp_limit']:.1f}h RULE-FDP-01 limit.\n\n"
            + _reasoning("resolve_delay_options: no FDP breach")
        )
    lines = [
        f"{o['rank']}. {o['action']} — {o['cost_inr']:.0f} INR, {'legal' if o['legal'] else 'NOT legal'}. {o['reasoning']}"
        for o in x["options"]
    ]
    return (
        f"{x['breach_detail']}. Options:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            f"resolve_delay_options for {x['aircraft']} on {x['date']}: FDP {x['fdp_after_delay']:.2f}h vs {x['fdp_limit']:.1f}h limit after a {x['delay_hours']:g}h delay",
            "reserve set cost = full complement at reserve callout rates; cancellation per leg from costs.json",
        )
    )


def compose_notification(r: Results) -> str:
    if err := _err(r, "draft_callout_notification"):
        return _refused("draft_callout_notification", err)
    x = r["draft_callout_notification"]
    return (
        "Draft callout notification:\n\n"
        + x["message"]
        + "\n\nIncluded: crew id and pairing id; report time/place per day; flights per day; overnight and hotel; "
        "acknowledgement request with deadline; contact for questions."
        + "\n\n"
        + _reasoning(
            f"draft_callout_notification({x['crew_id']}, {x['pairing_id']}): every time and flight from rosters.json/flights.json"
        )
    )


def compose_briefing(r: Results) -> str:
    if err := _err(r, "morning_briefing"):
        return _refused("morning_briefing", err)
    x = r["morning_briefing"]
    lines = [
        f"- {ln['aircraft']} ({ln['aircraft_type']}, {ln['pairing_id']}, report {ln['report_utc'][11:16]}Z): tightest 7-day duty headroom "
        f"{ln['tightest_duty_headroom_7d']:.2f}h; highest risk {ln['highest_risk']:.2f}; certs {'all valid' if ln['all_certs_valid'] else 'NOT all valid'}; "
        f"eligible reserves at report: {', '.join(ln['eligible_reserves_at_report']) or 'none'}"
        for ln in x["lines"]
    ]
    return (
        f"Morning briefing for {x['date']} — surface three data points per aircraft line:\n"
        + "\n".join(f"{i}. {s}" for i, s in enumerate(x["surfaced"], start=1))
        + "\n\nToday's lines:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            "headroom from duty_clocks history + roster (RULE-DUTY-02); reserves from reserve_pool windows and ratings; risk from risk_signals.json",
            "why these three: legality headroom is what breaks first under a delay, reserve availability is what fixes it, and risk signals say where to look first",
        )
    )


# ---------------------------------------------------------------- scenario workspace


def compose_declare(r: Results) -> str:
    if err := _err(r, "declare_unavailable"):
        return _refused("declare_unavailable", err)
    d = r["declare_unavailable"]
    who, impact, sc = d["declared"], d["impact"], d["scenario"]
    vac = sc["vacancies"]
    lines = [
        f"Recorded: {who['crew_id']} ({who['name']}, {who['rank']}) unavailable from "
        f"{who['from_date']} ({who['reason']})."
    ]
    if impact.get("uncovered_now"):
        lines.append("Uncovered now: " + ", ".join(impact["uncovered_now"]) + ".")
    if vac:
        lines.append(
            "Vacant: "
            + "; ".join(f"{v['role']} on {v['pairing_id']} {v['date']}" for v in vac)
            + ". Ask for cover options, then apply one."
        )
    else:
        lines.append("No pairing days are vacant.")
    return (
        "\n".join(lines)
        + "\n\n"
        + _reasoning(
            "Sick-call impact assessment on the working scenario; the roster in this conversation "
            "now treats them as unavailable.",
            "Scenario: " + "; ".join(sc["summary"]),
        )
    )


def compose_apply(r: Results) -> str:
    if err := _err(r, "apply_cover"):
        return _refused("apply_cover", err)
    a = r["apply_cover"]
    sc = a["scenario"]
    if not a.get("applied"):
        alts = a.get("legal_alternatives") or []
        return (
            f"Not applied — {a.get('reason', 'not a legal cover')}."
            + (
                " Legal alternatives: "
                + ", ".join(f"{o['crew_id']} (₹{o['cost_inr']:,.0f})" for o in alts)
                + "."
                if alts
                else ""
            )
            + "\n\n"
            + _reasoning("Legality check on the working scenario refused the cover.")
        )
    c, o = a["cover"], a["option"]
    return (
        f"Committed: {c['crew_id']} covers {c['pairing_id']} as {c['role']} from {c['from_date']} "
        f"in place of {c['replaces']} — {o['kind'].replace('_', ' ')}, ₹{c['cost_inr']:,.0f}, "
        f"{o['coverage']}. Vacancies left: {len(sc['vacancies'])}. "
        f"Committed cost so far ₹{sc['committed_cost_inr']:,.0f}."
        + "\n\n"
        + _reasoning(
            "Cover applied after the full check: " + ", ".join(o["rules_checked"]) + ".",
            "Scenario: " + "; ".join(sc["summary"]),
        )
    )


def compose_scenario_status(r: Results) -> str:
    if err := _err(r, "scenario_status"):
        return _refused("scenario_status", err)
    sc = r["scenario_status"]
    if sc["empty"]:
        return "No changes in this conversation's scenario.\n\n" + _reasoning(
            "Scenario status: empty."
        )
    vac = sc["vacancies"]
    return (
        "Working scenario:\n"
        + "\n".join(f"- {line}" for line in sc["summary"])
        + (
            "\nStill vacant: "
            + "; ".join(f"{v['role']} on {v['pairing_id']} {v['date']}" for v in vac)
            if vac
            else "\nNothing vacant."
        )
        + f"\nCommitted cost so far ₹{sc['committed_cost_inr']:,.0f}."
        + "\n\n"
        + _reasoning("Scenario status from the desk's working scenario.")
    )


def compose_scenario_reset(r: Results) -> str:
    if err := _err(r, "reset_scenario"):
        return _refused("reset_scenario", err)
    d = r["reset_scenario"]
    return (
        "Scenario reset — everyone is available again and applied covers are undone."
        + (" Discarded: " + "; ".join(d["discarded"]) + "." if d["discarded"] else "")
        + "\n\n"
        + _reasoning("reset_scenario cleared the working scenario.")
    )
