"""Tier-2 planning and composition for the offline router.

Consequence questions map onto the simulation tools; the composers turn the tool
results into the same shape of answer the model would give — verdict first,
numbers from the tool, then "Reasoning:" lines quoting the evidence.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from crew_ops_advisor.agent.entities import Entities
from crew_ops_advisor.agent.prompts import REFUSAL_PHRASE
from crew_ops_advisor.agent.types import ToolCall
from crew_ops_advisor.data import Datastore

Results = dict[str, Any]

TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\s*(?:z|utc)\b", re.I)
DELAY_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:-\s*)?(minutes?|mins?|min|hours?|hrs?|h)\b(?:\s+(?:delay|late))?", re.I
)
HOURS_THRESHOLD_RE = re.compile(
    r"\b(\d{1,3}(?:\.\d+)?)\s*(?:or more|\+|plus)?\s*(?:duty\s+)?hours?\b", re.I
)


def _reasoning(*lines: str) -> str:
    return "Reasoning:\n" + "\n".join(f"- {line}" for line in lines if line)


def _err(r: Results, name: str) -> str | None:
    res = r.get(name)
    if res is None:
        return f"{name} returned nothing"
    if "error" in res and len(res) == 1:
        return res["error"]
    return None


def _refused(name: str, err: str) -> str:
    return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning(f"{name} failed")


def reported_utc_from(text: str, e: Entities, snapshot: date) -> str | None:
    m = TIME_RE.search(text)
    if not m:
        return None
    on = e.date or snapshot
    return f"{on.isoformat()}T{int(m[1]):02d}:{m[2]}:00Z"


def delay_hours_from(text: str) -> float | None:
    m = DELAY_RE.search(text)
    if not m:
        return None
    value, unit = float(m[1]), m[2].lower()
    return round(value / 60, 4) if unit.startswith("m") else value


# ----------------------------------------------------------------- planning


class T2Planner:
    """Given a question and its entities, decide which simulation tool answers it."""

    def __init__(self, store: Datastore):
        self._store = store
        self._snapshot = store.snapshot_utc.date()

    def plan(self, text: str, e: Entities, call: Callable[..., ToolCall]):  # noqa: C901
        low = text.lower()
        has = lambda *words: any(re.search(rf"\b{w}\b", low) for w in words)  # noqa: E731

        # Recommendation questions need the ranking tools (Tier 3); never answer them with an
        # impact-only simulation as if that were the advice.
        if has(
            "what should",
            "recommend\\w*",
            "best option",
            "options?",
            "what do i do",
            "resolve",
            "recovery plan",
        ):
            return None

        # -- released at … earliest report -----------------------------------------
        if has("released", "release") and has("earliest", "report", "next duty"):
            when = reported_utc_from(text, e, self._snapshot)
            if when:
                return (
                    "earliest_report",
                    (call("earliest_next_report", release_utc=when),),
                    compose_earliest_report,
                )

        # -- station closure ---------------------------------------------------------
        if has("closed", "closure", "shut") and e.stations and e.time_window:
            on = e.date or self._snapshot
            return (
                "closure",
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

        # -- cancellation ------------------------------------------------------------
        if has("cancel\\w*") and e.flight_nos:
            on = e.date or self._next_operating_date(e.flight_nos[0])
            return (
                "cancellation",
                (call("cancellation_impact", flight_no=e.flight_nos[0], date=on.isoformat()),),
                compose_cancellation,
            )

        # -- delay -------------------------------------------------------------------
        if (
            has("delay\\w*", "late")
            and (e.aircraft or e.flight_nos)
            and not has("closed", "closure")
        ):
            hours = delay_hours_from(text)
            if hours:
                on = e.date or self._snapshot
                args: dict[str, Any] = {"date": on.isoformat(), "delay_hours": hours}
                if e.aircraft:
                    args["aircraft"] = e.aircraft[0]
                elif e.flight_nos:
                    args["flight_no"] = e.flight_nos[0]
                return "delay", (call("simulate_delay", **args),), compose_delay

        # -- reserve coverage for a callout ------------------------------------------
        if (
            has("reserve\\w*")
            and has("cover\\w*", "window\\w*", "qualified", "eligible")
            and (e.aircraft or e.pairing_ids)
            and not e.crew_ids
        ):
            duty = self._duty_for(e)
            if duty:
                args = {
                    "required_report_utc": duty["report_utc"],
                    "aircraft_type": duty["aircraft_type"],
                    "station": duty["dep_station"],
                }
                if e.ranks:
                    args["rank"] = e.ranks[0]
                return (
                    "reserve_coverage",
                    (
                        call("get_pairing", pairing_id=duty["pairing_id"]),
                        call("reserve_coverage", **args),
                    ),
                    lambda r: compose_reserve_coverage(r, duty),
                )

        # -- sick / unavailable ------------------------------------------------------
        if e.crew_id and has(
            "sick", "unwell", "ill", "illness", "no[- ]show", "unavailable", "out", "removed"
        ):
            if not has("cover\\w*", "assign\\w*", "move", "onto", "legal\\w*"):
                args = {"crew_id": e.crew_id}
                if e.pairing_ids:
                    args["pairing_id"] = e.pairing_ids[0]
                when = reported_utc_from(text, e, self._snapshot)
                if when:
                    args["reported_utc"] = when
                elif e.date:
                    args["from_date"] = e.date.isoformat()
                return (
                    "crew_removal",
                    (call("simulate_crew_removal", **args),),
                    compose_crew_removal,
                )

        # -- own rostered duty legality ----------------------------------------------
        if (
            e.crew_id
            and has("rostered", "their duty", "own duty", "operate")
            and has("legal\\w*")
            and not e.pairing_ids
        ):
            args = {"crew_id": e.crew_id}
            if e.date:
                args["date"] = e.date.isoformat()
            return (
                "rostered_legality",
                (call("check_rostered_legality", **args),),
                compose_rostered_legality,
            )

        # -- assignment / cover legality ---------------------------------------------
        if (
            e.crew_id
            and (e.pairing_ids or e.flight_nos)
            and has(
                "cover\\w*",
                "assign\\w*",
                "move",
                "moving",
                "onto",
                "legal\\w*",
                "breach\\w*",
                "swap\\w*",
                "replace\\w*",
                "substitut\\w*",
                "position\\w*",
            )
        ):
            pairing_id = e.pairing_ids[0] if e.pairing_ids else self._pairing_for_flight(e)
            if pairing_id:
                args = {"crew_id": e.crew_id, "pairing_id": pairing_id}
                explicit_from = re.search(
                    r"\bfrom\s+(?:the\s+)?(\d|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                    low,
                )
                if (
                    e.date
                    and explicit_from
                    and not has("full pairing", "both days", "whole pairing")
                ):
                    args["from_date"] = e.date.isoformat()
                return (
                    "assignment",
                    (call("check_assignment_legality", **args),),
                    compose_assignment,
                )

        # -- crew near limits ----------------------------------------------------------
        if (
            has(
                "duty hours",
                "duty limit\\w*",
                "approach\\w*",
                "near\\w* (?:the )?limit\\w*",
                "close to (?:the )?limit\\w*",
            )
            and not e.crew_ids
        ):
            on = e.date or (self._snapshot + timedelta(days=1))
            args = {"date": on.isoformat()}
            m = HOURS_THRESHOLD_RE.search(text)
            if m and has("or more", "at least", "\\+", "over", "more than"):
                args["min_duty_hours"] = float(m[1])
            elif has("approach\\w*", "near\\w*", "close to"):
                args["max_duty_headroom"] = 10.0
            return "near_limits", (call("crew_near_limits", **args),), compose_near_limits

        # -- most seats at risk ---------------------------------------------------------
        if has("seats") and has("risk", "most", "largest", "biggest"):
            return "seats_at_risk", (call("seats_at_risk"),), compose_seats_at_risk

        return None

    # ---- lookups the planner needs ----------------------------------------------------

    def _next_operating_date(self, flight_no: str) -> date:
        for f in self._store.flights.list():
            if f.flight_no == flight_no and f.date > self._snapshot:
                return f.date
        return self._snapshot + timedelta(days=1)

    def _pairing_for_flight(self, e: Entities) -> str | None:
        fno = e.flight_nos[0]
        on = e.date or self._next_operating_date(fno)
        flight = self._store.flights.by_number(fno, on)
        if flight is None:
            return None
        pairing = self._store.pairings.for_flight(flight.flight_id)
        return pairing.pairing_id if pairing else None

    def _duty_for(self, e: Entities) -> dict[str, Any] | None:
        """Report time / aircraft type / start station of the duty named by aircraft+date or pairing."""
        on = e.date or (self._snapshot + timedelta(days=1))
        pairing = None
        if e.pairing_ids:
            try:
                pairing = self._store.pairings.get(e.pairing_ids[0])
            except LookupError:
                return None
        elif e.aircraft:
            pairing = self._store.pairings.for_aircraft_on(e.aircraft[0], on)
        if pairing is None:
            return None
        day = next((d for d in pairing.days if d.date == on), pairing.days[0])
        duty = self._store.pairings.duty_period(pairing, day)
        return {
            "pairing_id": pairing.pairing_id,
            "aircraft": pairing.aircraft,
            "aircraft_type": duty.aircraft_type,
            "dep_station": duty.dep_station,
            "report_utc": duty.report_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "date": day.date.isoformat(),
        }


# ----------------------------------------------------------------- composers


def compose_earliest_report(r: Results) -> str:
    if err := _err(r, "earliest_next_report"):
        return _refused("earliest_next_report", err)
    x = r["earliest_next_report"]
    return (
        f"Earliest next report is {x['earliest_report_utc']} — release {x['release_utc']} plus the "
        f"{x['min_rest_hours']:.0f}h minimum rest."
        + "\n\n"
        + _reasoning(
            f"RULE-REST-04: report ≥ release + {x['min_rest_hours']:.0f}h (computed by earliest_next_report)"
        )
    )


def compose_closure(r: Results) -> str:
    if err := _err(r, "station_closure_impact"):
        return _refused("station_closure_impact", err)
    c = r["station_closure_impact"]
    if not c["per_flight"]:
        return (
            f"No flights depart or arrive {c['station']} between {c['window']['start'][11:16]}Z and {c['window']['end'][11:16]}Z.\n\n"
            + _reasoning("station_closure_impact returned 0 flights")
        )
    lines = [
        f"- {a['flight_no']} ({a['at_station']} {a['scheduled_utc'][11:16]}Z, {a['pairing_id']}): min delay "
        f"{a['min_delay_hours']:g}h → FDP {a['crew_fdp_after_delay']:.2f}h vs {a['fdp_limit']:.1f}h limit — {a['action']}"
        for a in c["per_flight"]
    ]
    return (
        f"{c['count']} flights are affected at {c['station']} ({c['window']['start'][11:16]}–{c['window']['end'][11:16]}Z): "
        f"{', '.join(c['affected_flight_numbers'])}; {c['passengers_affected']} seats exposed; "
        f"{len(c['fdp_breaches'])} of them push their crew past RULE-FDP-01 ({', '.join(c['fdp_breaches']) or 'none'}).\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            "station_closure_impact: any flight departing or arriving the station inside the window is affected",
            c["note"],
        )
    )


def compose_cancellation(r: Results) -> str:
    if err := _err(r, "cancellation_impact"):
        return _refused("cancellation_impact", err)
    x = r["cancellation_impact"]
    return (
        f"Cancelling {x['flight_no']} on {x['date']} ({x['route']}) affects {x['passengers_affected']} passengers "
        f"and costs {x['direct_cancellation_cost_inr']:.0f} INR in direct cancellation cost"
        + (
            f"; it releases the {len(x['crew_released'])} crew of {x['pairing_id']} from that leg."
            if x.get("pairing_id")
            else "."
        )
        + "\n\n"
        + _reasoning(
            "cancellation_impact: seats from flights.json; cancellation_per_flight from costs.json"
        )
    )


def compose_delay(r: Results) -> str:
    if err := _err(r, "simulate_delay"):
        return _refused("simulate_delay", err)
    d = r["simulate_delay"]
    verdict = (
        f"Yes — a {d['delay_hours']:g}h delay pushes the {d['sectors']}-sector duty to {d['fdp_after_delay']:.2f}h "
        f"against a {d['fdp_limit']:.1f}h RULE-FDP-01 limit, so the rostered crew cannot legally complete all "
        f"{d['sectors']} legs. They can legally complete the first {d['legal_leg_count']}; "
        f"{', '.join(d['legs_needing_recrew'])} need{'s' if len(d['legs_needing_recrew']) == 1 else ''} a reserve crew or cancellation."
        if d["breach"]
        else f"No — with a {d['delay_hours']:g}h delay the duty runs {d['fdp_after_delay']:.2f}h, inside the "
        f"{d['fdp_limit']:.1f}h RULE-FDP-01 limit for {d['sectors']} sectors."
    )
    other = [c for c in d["crew_checks"] if any(i for i in c["issues"] if "RULE-FDP-01" not in i)]
    extra = ""
    if other:
        extra = " Other breaches: " + "; ".join(
            f"{c['crew_id']}: {'; '.join(c['issues'])}" for c in other
        )
    return (
        verdict
        + extra
        + "\n\n"
        + _reasoning(
            f"simulate_delay for {d['aircraft']} on {d['date']} ({d['pairing_id']}): report {d['original_report_utc'][11:16]}Z unchanged, "
            f"release {d['original_release_utc'][11:16]}Z → {d['new_release_utc'][11:16]}Z",
            f"FDP before {d['fdp_before']:.2f}h, after {d['fdp_after_delay']:.2f}h, limit {d['fdp_limit']:.1f}h (13h − 0.5h per sector beyond the 2nd)",
            "all rostered crew re-evaluated against the seven rules with the delayed duty",
        )
    )


def compose_reserve_coverage(r: Results, duty: dict[str, Any]) -> str:
    if err := _err(r, "reserve_coverage"):
        return _refused("reserve_coverage", err)
    x = r["reserve_coverage"]
    eligible = [c for c in x["candidates"] if c["eligible"]]
    excluded = [c for c in x["candidates"] if not c["eligible"]]
    lines = [
        f"- {c['crew_id']} ({c['name']}): window {c['oncall_window_utc']['start']}-{c['oncall_window_utc']['end']}Z, rated {'/'.join(c['ratings'])}, reachable in {c['reachability_minutes']} min"
        for c in eligible
    ]
    ex_lines = [f"- {c['crew_id']}: {c['reason']}" for c in excluded]
    head = (
        f"{len(eligible)} reserve {x['filters'].get('rank') or 'crew'}(s) can take {duty['pairing_id']} ({duty['aircraft']}, "
        f"{duty['aircraft_type']}) reporting {x['required_report_utc'][11:16]}Z on {duty['date']}: "
        f"{', '.join(x['eligible']) or 'none'}."
    )
    return (
        head
        + ("\n" + "\n".join(lines) if lines else "")
        + ("\nExcluded:\n" + "\n".join(ex_lines) if ex_lines else "")
        + "\n\n"
        + _reasoning(
            "reserve_coverage: callout must fall inside the on-call window; RULE-QUAL-05 rating and RULE-BASE-07 base checked",
            f"required report time is the pairing's rostered report {x['required_report_utc']}",
        )
    )


def compose_crew_removal(r: Results) -> str:
    if err := _err(r, "simulate_crew_removal"):
        return _refused("simulate_crew_removal", err)
    x = r["simulate_crew_removal"]
    if not x["days"]:
        return (
            f"{x['crew_id']} has no rostered duty in that period, so no flight loses crew.\n\n"
            + _reasoning(x["note"])
        )
    now = ", ".join(f.split("-")[0] for f in x["uncovered_now"])
    later = ", ".join(f.split("-")[0] for f in x["also_at_risk"])
    first = x["days"][0]
    text = (
        f"Immediately uncrewed: {now} on {first['date']} ({x['pairings_affected'][0]}, {x['rank']} slot) — "
        f"{x['passengers_now']} passengers."
    )
    if later:
        text += (
            f" Also at risk: {later} on {x['days'][-1]['date']} — the same pairing continues, "
            f"so the cover must take the full remaining pairing ({x['passengers_at_risk_total']} passengers in total)."
        )
    return (
        text
        + "\n\n"
        + _reasoning(
            f"simulate_crew_removal({x['crew_id']}) from rosters.json: {x['crew_name']} is rostered as {x['rank']} on {', '.join(x['pairings_affected'])}",
            "passengers = seats of the uncovered legs (flights.json)",
            x["note"],
        )
    )


def compose_rostered_legality(r: Results) -> str:
    if err := _err(r, "check_rostered_legality"):
        return _refused("check_rostered_legality", err)
    x = r["check_rostered_legality"]
    parts = []
    for p in x["pairings"]:
        parts.append(p["summary"] + "\n" + "\n".join(f"  {ln}" for ln in p["explanation"]))
    return (
        "\n".join(parts)
        + "\n\n"
        + _reasoning(
            "check_rostered_legality: all seven rules evaluated over the crew member's full timeline"
        )
    )


def compose_assignment(r: Results) -> str:
    if err := _err(r, "check_assignment_legality"):
        return _refused("check_assignment_legality", err)
    x = r["check_assignment_legality"]
    text = x["summary"]
    if x.get("deadhead"):
        text += " " + x["consequence"]
        text += f" Cost {x['cost_inr']:.0f} INR ({', '.join(f'{k} {v:.0f}' for k, v in x['cost_breakdown'].items())})."
    elif x.get("cost_inr") is not None:
        text += f" Callout cost {x['cost_inr']:.0f} INR ({x['callout_kind'].replace('_', ' ')})."
    if not x.get("available", True):
        text += f" Availability: {x['availability_note']}."
    lines = list(x["explanation"])
    return (
        text
        + "\n"
        + "\n".join(f"  {ln}" for ln in lines)
        + "\n\n"
        + _reasoning(
            f"check_assignment_legality({x['crew_id']} → {x['pairing_id']}): seven rules over the crew member's full timeline "
            f"(28-day history + rostered week + the proposed duty days {', '.join(x['duty_dates'])})",
            "deadhead: earliest positioning flight from base, report = arrival + 15 min, delay costed per duty hour"
            if x.get("deadhead")
            else "",
        )
    )


def compose_near_limits(r: Results) -> str:
    if err := _err(r, "crew_near_limits"):
        return _refused("crew_near_limits", err)
    x = r["crew_near_limits"]
    crit = x["criteria"]
    label = (
        f"{crit['min_duty_hours']:g} or more duty hours in the 7 days ending {x['date']}"
        if crit.get("min_duty_hours") is not None
        else f"{crit.get('max_duty_headroom') or crit.get('max_flight_headroom')}h or less headroom as of {x['date']}"
    )
    if not x["crew"]:
        return f"No crew have {label}.\n\n" + _reasoning("crew_near_limits returned 0 rows")
    lines = [
        f"- {c['crew_id']} ({c['name']}, {c['rank']}): {c['duty_hours_7d']:.2f}h duty / 7d (headroom {c['duty_headroom_7d']:.2f}h), "
        f"{c['flight_hours_28d']:.2f}h block / 28d, planned {c['planned_duty_hours_on_date']:.2f}h that day"
        for c in x["crew"]
    ]
    return (
        f"{x['count']} crew have {label}:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            "crew_near_limits: rolling calendar-day windows over duty_clocks.json history plus rostered duties (RULE-DUTY-02 60h/7d, RULE-FLT-03 100h/28d)"
        )
    )


def compose_seats_at_risk(r: Results) -> str:
    if err := _err(r, "seats_at_risk"):
        return _refused("seats_at_risk", err)
    x = r["seats_at_risk"]
    return (
        f"{x['most_seats_at_risk'].capitalize()} — versus {x['compared_with']}. {x['reason'].capitalize()}; "
        f"direct cancellation cost is {x['cancellation_cost_per_leg_inr']:.0f} INR per leg regardless of type."
        + "\n\n"
        + _reasoning(
            "seats_at_risk: seats per aircraft type from flights.json; cancellation_per_flight from costs.json"
        )
    )
