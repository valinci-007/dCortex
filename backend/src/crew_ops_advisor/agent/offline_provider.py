"""Offline provider: a deterministic keyword router that speaks the LLM contract.

It exists so the whole pipeline — tools, orchestrator, CLI, evals — runs and
demos with no API key and no network (ADR-0005), and as the live-demo fallback
if the venue's model is unavailable. It plans tool calls from extracted
entities and composes answers from the tool results with templates. It never
computes anything the tools did not return.

Its answers are labelled so nobody mistakes them for model output.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from crew_ops_advisor.agent.disclosure import IDENTITY_ANSWER, IDENTITY_RE
from crew_ops_advisor.agent.entities import Entities, EntityExtractor
from crew_ops_advisor.agent.offline_t2 import T2Planner
from crew_ops_advisor.agent.offline_t3 import T3Planner
from crew_ops_advisor.agent.prompts import REFUSAL_PHRASE
from crew_ops_advisor.agent.types import ToolCall, ToolResult, Turn
from crew_ops_advisor.data import Datastore

OFFLINE_LABEL = "(offline mode — answered by the desk's rule-based router)"

# Requests the desk tool cannot serve at all: weather/forecasting, bookings, personal contact,
# HR. A crew id in such a question must not turn it into a profile lookup.
OUT_OF_SCOPE_RE = re.compile(
    r"\b(weather|fog|storm|forecast|book(?:ing)?|hotel room|taxi|email|phone|call (?:him|her|them)|"
    r"salary|pay(?:roll)?|leave request|holiday)\b",
    re.I,
)

SIMULATION_RE = re.compile(
    r"\b(sick|unwell|illness|cancel\w*|delay\w*|closed|closure|shut|divert\w*|reassign\w*|"
    r"move|moving|swap\w*|substitut\w*|replace\w*|cover(?:s|ed|ing)?|breach\w*|legal(?:ly|ity)?|"
    r"illegal|uncrewed|impact|what should|recommend\w*|options?|resolve|deadhead|draft|notify|"
    r"notification|if (?:i|we)|can [a-z0-9-]+ (?:legally|cover|operate))\b"
)

Results = dict[str, Any]  # tool name -> parsed result dict, or {"error": str}
Composer = Callable[[Results], str]


@dataclass(frozen=True, slots=True)
class Plan:
    intent: str
    calls: tuple[ToolCall, ...]
    compose: Composer


class OfflineProvider:
    name = "offline"

    def __init__(self, store: Datastore):
        self._router = OfflineRouter(store)

    def open_session(self, system: str, tools: Sequence[dict[str, Any]]) -> OfflineSession:
        return OfflineSession(self._router, {t["name"] for t in tools})


class OfflineSession:
    def __init__(self, router: OfflineRouter, tool_names: set[str]):
        self._router = router
        self._tool_names = tool_names
        self._plan: Plan | None = None
        self._ids: dict[str, str] = {}

    def send_user(self, text: str) -> Turn:
        plan = self._router.route(text)
        if plan is None or any(c.name not in self._tool_names for c in plan.calls):
            self._plan = None
            return Turn(text=self._router.refusal(text), refused=True, stop_reason="refusal")
        if not plan.calls:  # answered without data (identity / capabilities)
            self._plan = None
            return Turn(text=f"{plan.compose({})}\n\n{OFFLINE_LABEL}", stop_reason="end_turn")
        self._plan = plan
        self._ids = {c.id: c.name for c in plan.calls}
        return Turn(text="", tool_calls=plan.calls, stop_reason="tool_use")

    def send_tool_results(self, results: Sequence[ToolResult]) -> Turn:
        if self._plan is None:
            return Turn(text=self._router.refusal(""), refused=True, stop_reason="refusal")
        parsed: Results = {}
        for r in results:
            name = self._ids.get(r.call_id, r.call_id)
            if r.is_error:
                parsed[name] = {"error": r.content.removeprefix("Error: ")}
            else:
                try:
                    parsed[name] = json.loads(r.content)
                except json.JSONDecodeError:
                    parsed[name] = {"error": "unreadable tool result"}
        text = self._plan.compose(parsed)
        self._plan = None
        return Turn(text=f"{text}\n\n{OFFLINE_LABEL}", stop_reason="end_turn")


# ------------------------------------------------------------------ routing


class OfflineRouter:
    def __init__(self, store: Datastore):
        self._store = store
        self._ex = EntityExtractor(store)
        self._snapshot = store.snapshot_utc.date()
        self._t2 = T2Planner(store)
        self._t3 = T3Planner(store)

    def refusal(self, text: str) -> str:
        if OUT_OF_SCOPE_RE.search(text.lower()):
            return (
                f"{REFUSAL_PHRASE}: that is outside this dataset (no weather, bookings, contact "
                "or HR data). I can answer roster, duty-clock, legality, disruption and cover "
                f"questions.\n\n{OFFLINE_LABEL}"
            )
        if SIMULATION_RE.search(text.lower()):
            return (
                f"{REFUSAL_PHRASE} in offline mode: I could not map this consequence question onto "
                "a simulation. Name the crew id, pairing or flight, the date, and the event (sick "
                "call with its time, a closure window like 08:00–14:00Z, a delay in minutes, a "
                "cancellation, or a cover such as 'can C-2210 cover P-2291'). Recommendations "
                "('what should I do') need the ranking tools."
                f"\n\n{OFFLINE_LABEL}"
            )
        return (
            f"{REFUSAL_PHRASE} in offline mode. I can look up crew, duty clocks, flights, "
            "pairings, reserves, certifications, risk signals, rules and costs by id, station "
            "or date — try naming a crew id (C-1042), pairing (P-2291), flight (DX412), "
            "aircraft (VT-DXC), station (BLR) or date (2026-09-15).\n\n"
            f"{OFFLINE_LABEL}"
        )

    def route(self, text: str) -> Plan | None:  # noqa: C901 - one branch per intent family
        e = self._ex.extract(text)
        low = text.lower()
        has = lambda *words: any(re.search(rf"\b{w}\b", low) for w in words)  # noqa: E731
        n = _Counter()

        if IDENTITY_RE.search(low):
            return Plan("identity", (), lambda r: IDENTITY_ANSWER)
        if OUT_OF_SCOPE_RE.search(low):
            return None

        # Consequence questions go to the Tier-2 planner first (its patterns are specific);
        # a disruption question it cannot map is refused rather than answered as an easier
        # lookup about the same crew (a confident wrong answer).
        planned = self._t3.plan(text, e, n.call) or self._t2.plan(text, e, n.call)
        if planned is not None:
            intent, calls, compose = planned
            return Plan(intent, tuple(calls), compose)
        if SIMULATION_RE.search(low):
            return None

        # -- pairing by id -----------------------------------------------------
        if e.pairing_ids and not e.crew_ids:
            pid = e.pairing_ids[0]
            return Plan(
                "pairing", (n.call("get_pairing", pairing_id=pid),), lambda r: compose_pairing(r, e)
            )

        # -- flight by number + date --------------------------------------------
        if e.flight_nos and e.date and not has("cancel", "cancelled", "delay", "delayed"):
            fno = e.flight_nos[0]
            return Plan(
                "flight",
                (n.call("get_flight", flight_no=fno, date=e.date.isoformat()),),
                lambda r: compose_flight(r, e),
            )

        # -- certifications ----------------------------------------------------
        if has(
            "certif\\w*",
            "certs?",
            "licen[cs]e",
            "medical",
            "recurrent",
            "dangerous goods",
            "expir\\w*",
            "laps\\w*",
        ):
            if e.crew_id:
                on = e.date.isoformat() if e.date else None
                args = {"crew_id": e.crew_id, **({"on_date": on} if on else {})}
                return Plan(
                    "crew_certs",
                    (n.call("get_certifications", **args),),
                    lambda r: compose_crew_certs(r, e),
                )
            start = e.date or (self._snapshot + timedelta(days=1))
            days = e.within_days or 30
            return Plan(
                "expiring_certs",
                (
                    n.call(
                        "list_expiring_certifications",
                        from_date=start.isoformat(),
                        within_days=days,
                    ),
                ),
                lambda r: compose_expiring(r, e),
            )

        # -- risk --------------------------------------------------------------
        if has("risk", "risky", "fatigue"):
            if e.crew_id:
                return Plan(
                    "risk",
                    (n.call("get_risk_signal", crew_id=e.crew_id),),
                    lambda r: compose_risk(r, e),
                )
            return Plan(
                "risk_list",
                (n.call("list_risk_signals", limit=10),),
                lambda r: compose_risk_list(r, e),
            )

        # -- duty clock / hours ---------------------------------------------------
        if e.crew_id and has(
            "duty", "hours?", "headroom", "accru\\w*", "block", "rest", "report", "clock", "limit"
        ):
            cid = e.crew_id
            return Plan(
                "duty_clock",
                (n.call("get_crew", crew_id=cid), n.call("get_duty_clock", crew_id=cid)),
                lambda r: compose_duty_clock(r, e),
            )

        # -- reserves at a station / on a date -----------------------------------
        if has("reserves?", "standby", "on[- ]call") and not e.crew_ids:
            args: dict[str, Any] = {}
            if e.stations:
                args["station"] = e.stations[0]
            if e.date:
                args["date"] = e.date.isoformat()
            return Plan(
                "reserves", (n.call("list_reserves", **args),), lambda r: compose_reserves(r, e)
            )

        # -- crew profile ---------------------------------------------------------
        if e.crew_id:
            return Plan(
                "crew", (n.call("get_crew", crew_id=e.crew_id),), lambda r: compose_crew(r, e)
            )

        # -- pairing by aircraft/date ---------------------------------------------
        if e.aircraft and (e.date or has("pairing", "crew", "operat\\w*", "who")):
            args = {"aircraft": e.aircraft[0]}
            if e.date:
                args["date"] = e.date.isoformat()
            if has("flights?", "legs?", "rotation", "schedule") and not has(
                "crew", "who", "pairing"
            ):
                return Plan(
                    "aircraft_flights",
                    (n.call("list_flights", **args),),
                    lambda r: compose_flights(r, e),
                )
            return Plan(
                "aircraft_pairing",
                (n.call("find_pairings", **args),),
                lambda r: compose_find_pairings(r, e),
            )

        # -- schedule-wide stats ----------------------------------------------------
        if (
            has(
                "longest",
                "shortest",
                "block time",
                "busiest",
                "fleet",
                "how many aircraft",
                "total flights",
            )
            and not e.date
        ):
            return Plan("stats", (n.call("schedule_stats"),), lambda r: compose_stats(r, e))

        # -- routes -------------------------------------------------------------------
        if (
            has("nonstop", "non-stop", "destinations?", "serve[sd]?", "routes?", "where .* fly")
            and e.stations
            and not e.date
        ):
            return Plan(
                "routes",
                (n.call("list_routes", dep_station=e.stations[0]),),
                lambda r: compose_routes(r, e),
            )

        # -- crew lists by rank/base -----------------------------------------------------
        if e.ranks and (e.stations or has("based", "base")) and not e.date and not has("flights?"):
            args = {"rank": e.ranks[0]}
            if e.stations:
                args["base"] = e.stations[0]
            return Plan(
                "crew_list", (n.call("list_crew", **args),), lambda r: compose_crew_list(r, e)
            )

        # -- flights ---------------------------------------------------------------------
        if has(
            "flights?", "departures?", "arrivals?", "legs?", "sectors?", "depart\\w*", "arriv\\w*"
        ) and (e.date or e.stations):
            args = {}
            if e.date:
                args["date"] = e.date.isoformat()
            if e.dep_station:
                args["dep_station"] = e.dep_station
            if e.arr_station:
                args["arr_station"] = e.arr_station
            window = _time_window(e)
            if window:
                on = e.date or self._snapshot
                args["date"] = on.isoformat()
                args["dep_from_utc"] = f"{on.isoformat()}T{window[0]}:00Z"
                args["dep_to_utc"] = f"{on.isoformat()}T{window[1]}:00Z"
            return Plan(
                "flights", (n.call("list_flights", **args),), lambda r: compose_flights(r, e)
            )

        # -- rulebook / costs / snapshot ------------------------------------------------------
        if e.rule_ids or has("rules?", "rulebook", "fdp", "legal limit", "regulation\\w*"):
            return Plan("rules", (n.call("get_rules"),), lambda r: compose_rules(r, e))
        if has("costs?", "rates?", "inr", "price", "expensive", "cheap\\w*"):
            return Plan("costs", (n.call("get_costs"),), lambda r: compose_costs(r, e))
        if has("today", "snapshot", "what day", "which week", "now", "stations?", "network"):
            return Plan("snapshot", (n.call("get_snapshot"),), lambda r: compose_snapshot(r, e))
        return None


class _Counter:
    def __init__(self):
        self.i = 0

    def call(self, name: str, **arguments: Any) -> ToolCall:
        self.i += 1
        return ToolCall(id=f"offline-{self.i}", name=name, arguments=arguments)


def _time_window(e: Entities) -> tuple[str, str] | None:
    if e.time_window:
        return e.time_window
    if "morning" in e.flags:
        return ("00:00", "12:00")
    if "afternoon" in e.flags:
        return ("12:00", "18:00")
    if "evening" in e.flags or "tonight" in e.flags:
        return ("18:00", "23:59")
    return None


# ------------------------------------------------------------------ composers


def _err(r: Results, name: str) -> str | None:
    res = r.get(name)
    if res is None:
        return f"{name} returned nothing"
    if "error" in res and len(res) == 1:
        return res["error"]
    return None


def _reasoning(*lines: str) -> str:
    return "Reasoning:\n" + "\n".join(f"- {line}" for line in lines if line)


def _fmt_window(w: dict[str, str]) -> str:
    return f"{w['start']}–{w['end']}Z"


def compose_pairing(r: Results, e: Entities) -> str:
    if err := _err(r, "get_pairing"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_pairing failed")
    p = r["get_pairing"]
    crew_lines = [f"- {m['crew_id']} — {m['role']} ({m['name']})" for m in p["crew"]]
    day_lines = [
        f"- {d['date']}: {', '.join(f.split('-')[0] for f in d['flights'])} "
        f"({d['starts_at']}→{d['ends_at']}), report {d['report_utc'][11:16]}Z, "
        f"release {d['release_utc'][11:16]}Z, {d['duty_hours']:.2f}h duty, {d['sectors']} sectors"
        for d in p["days"]
    ]
    return (
        f"Pairing {p['pairing_id']} operates {p['aircraft']} over {len(p['days'])} day(s) with "
        f"{len(p['crew'])} crew:\n"
        + "\n".join(crew_lines)
        + "\n\nDuty days:\n"
        + "\n".join(day_lines)
        + "\n\n"
        + _reasoning(
            f"get_pairing({p['pairing_id']}) from rosters — crew roles and duty days as rostered"
        )
    )


def compose_flight(r: Results, e: Entities) -> str:
    if err := _err(r, "get_flight"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_flight failed")
    f = r["get_flight"]
    pairing = f.get("pairing")
    crew = ""
    if pairing:
        crew = f" Operated under pairing {pairing['pairing_id']} ({len(pairing['crew'])} crew)."
    return (
        f"{f['flight_no']} on {f['date']} is operated by {f['aircraft']} ({f['aircraft_type']}, "
        f"{f['seats']} seats), {f['dep_station']}→{f['arr_station']} departing "
        f"{f['dep_utc'][11:16]}Z and arriving {f['arr_utc'][11:16]}Z, block {f['block_hours']}h.{crew}"
        + "\n\n"
        + _reasoning(f"get_flight({f['flight_no']}, {f['date']}) from flights.json")
    )


def compose_crew_certs(r: Results, e: Entities) -> str:
    if err := _err(r, "get_certifications"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_certifications failed")
    c = r["get_certifications"]
    lines = [
        f"- {x['cert_type']}: valid to {x['valid_to']}"
        + ("" if x["valid_on_date"] else " — EXPIRED on the checked date")
        for x in c["certifications"]
    ]
    state = "all valid" if c["all_valid"] else "NOT all valid"
    return (
        f"{c['crew_id']} certifications checked on {c['checked_on']}: {state}.\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            f"get_certifications({c['crew_id']}) — RULE-CERT-06 requires validity on the duty date"
        )
    )


def compose_expiring(r: Results, e: Entities) -> str:
    if err := _err(r, "list_expiring_certifications"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("list_expiring_certifications failed")
    c = r["list_expiring_certifications"]
    w = c["window"]
    if not c["expiring"]:
        return f"No certifications expire between {w['start']} and {w['end']}.\n\n" + _reasoning(
            "list_expiring_certifications returned 0 rows"
        )
    lines = [
        f"- {x['crew_id']} ({x['rank']}): {x['cert_type']} expires {x['valid_to']}"
        for x in c["expiring"]
    ]
    return (
        f"{c['count']} certification(s) expire within {w['days']} days of {w['start']} (to {w['end']}):\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            f"list_expiring_certifications({w['start']}, {w['days']} days) over certifications.json; RULE-CERT-06 applies from the expiry date"
        )
    )


def compose_risk(r: Results, e: Entities) -> str:
    if err := _err(r, "get_risk_signal"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_risk_signal failed")
    s = r["get_risk_signal"]
    drivers = "; ".join(s["drivers"]) or "no drivers listed"
    return (
        f"{s['crew_id']} has a disruption-risk score of {s['disruption_risk_score']} (as of {s['as_of_utc']}). "
        f"Drivers: {drivers}."
        + "\n\n"
        + _reasoning(
            "get_risk_signal — pre-computed signal from risk_signals.json (provided input, not computed here)"
        )
    )


def compose_risk_list(r: Results, e: Entities) -> str:
    if err := _err(r, "list_risk_signals"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("list_risk_signals failed")
    s = r["list_risk_signals"]
    lines = [
        f"- {x['crew_id']} ({x['rank']}): {x['disruption_risk_score']} — {'; '.join(x['drivers'])}"
        for x in s["signals"]
    ]
    return (
        "Highest disruption-risk crew:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning("list_risk_signals sorted by score, from risk_signals.json")
    )


def compose_duty_clock(r: Results, e: Entities) -> str:
    if err := _err(r, "get_duty_clock"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_duty_clock failed")
    c = r["get_duty_clock"]
    crew = r.get("get_crew") or {}
    who = f"{c['crew_id']}" + (
        f" ({crew['name']}, {crew['rank']}, base {crew['base']})" if "name" in crew else ""
    )
    return (
        f"{who} has accrued {c['duty_hours_7d']:.2f}h of duty in the 7 calendar days ending "
        f"{c['duty_window_7d']['end']} (window {c['duty_window_7d']['start']} → {c['duty_window_7d']['end']}), "
        f"leaving {c['duty_headroom_7d']:.2f}h headroom under RULE-DUTY-02 (limit {c['duty_limit_7d']:.0f}h). "
        f"Block hours in the 28 days ending {c['flight_window_28d']['end']}: {c['flight_hours_28d']:.2f}h, "
        f"headroom {c['flight_headroom_28d']:.2f}h under RULE-FLT-03 (limit {c['flight_limit_28d']:.0f}h). "
        f"Earliest next report under RULE-REST-04: {c['earliest_next_report_utc']}."
        + "\n\n"
        + _reasoning(
            f"get_duty_clock({c['crew_id']}) — sums from duty_clocks.json daily_history as of {c['as_of_utc']}",
            "headroom = limit − accrued (computed by the tool, not estimated)",
        )
    )


def compose_reserves(r: Results, e: Entities) -> str:
    if err := _err(r, "list_reserves"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("list_reserves failed")
    res = r["list_reserves"]
    f = res["filters"]
    where = f" at {f['station']}" if f.get("station") else ""
    when = f" on {f['date']}" if f.get("date") else ""
    if not res["reserves"]:
        return f"No reserves{where}{when}.\n\n" + _reasoning("list_reserves returned 0 rows")
    lines = [
        f"- {x['crew_id']} — {x['rank']} ({x['name']}), on call {_fmt_window(x['oncall_window_utc'])}, "
        f"reachable in {x['reachability_minutes']} min, ratings {'/'.join(x['ratings'])}"
        for x in res["reserves"]
    ]
    return (
        f"{res['count']} crew on reserve{where}{when}:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(
            f"list_reserves({f.get('station') or 'all'}, {f.get('date') or 'any date'}) from reserve_pool.json joined to crew.json",
            "a reserve may be called out only if the required report time falls inside their on-call window (RULE-BASE-07 for base)",
        )
    )


def compose_crew(r: Results, e: Entities) -> str:
    if err := _err(r, "get_crew"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_crew failed")
    c = r["get_crew"]
    parts = [
        f"{c['crew_id']} is {c['name']}, {c['rank']} based at {c['base']}, rated {'/'.join(c['ratings'])}, "
        f"seniority {c['seniority']}, reachable in {c['reachability_minutes']} minutes, status {c['status']}."
    ]
    if c.get("reserve"):
        parts.append(
            f"Reserve on-call window {_fmt_window(c['reserve']['oncall_window_utc'])} on {len(c['reserve']['reserve_dates'])} days this week."
        )
    else:
        parts.append("Not in the reserve pool.")
    if c.get("pairings"):
        parts.append(
            "Rostered on "
            + ", ".join(
                f"{p['pairing_id']} as {p['role']} ({'/'.join(p['dates'])})" for p in c["pairings"]
            )
            + "."
        )
    else:
        parts.append("No rostered pairings this week.")
    if c.get("disruption_risk"):
        parts.append(f"Disruption-risk score {c['disruption_risk']['disruption_risk_score']}.")
    return (
        " ".join(parts)
        + "\n\n"
        + _reasoning(
            f"get_crew({c['crew_id']}) from crew.json, reserve_pool.json, rosters.json, risk_signals.json"
        )
    )


def compose_find_pairings(r: Results, e: Entities) -> str:
    if err := _err(r, "find_pairings"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("find_pairings failed")
    res = r["find_pairings"]
    f = res["filters"]
    label = " ".join(
        x for x in (f.get("aircraft"), f"on {f['date']}" if f.get("date") else "") if x
    )
    if not res["pairings"]:
        return f"No pairing found for {label}.\n\n" + _reasoning("find_pairings returned 0 rows")
    out: list[str] = []
    for p in res["pairings"]:
        wanted = [m for m in p["crew"] if m["role"] in e.ranks] if e.ranks else p["crew"]
        if e.ranks and wanted:
            out.append(
                f"On {p['pairing_id']} ({p['aircraft']}, {'/'.join(p['dates'])}) the {e.ranks[0]} is "
                + ", ".join(f"{m['crew_id']} ({m['name']})" for m in wanted)
                + "."
            )
        else:
            out.append(
                f"{p['pairing_id']} ({p['aircraft']}, {'/'.join(p['dates'])}) crew: "
                + ", ".join(f"{m['crew_id']} {m['role']}" for m in p["crew"])
                + "."
            )
    return "\n".join(out) + "\n\n" + _reasoning(f"find_pairings({label}) from rosters.json")


def compose_stats(r: Results, e: Entities) -> str:
    if err := _err(r, "schedule_stats"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("schedule_stats failed")
    s = r["schedule_stats"]
    lb, sb = s["longest_block"], s["shortest_block"]
    return (
        f"The longest block time in the schedule is {lb['block_hours']}h, flown by "
        f"{', '.join(lb['flight_numbers'])}. The shortest is {sb['block_hours']}h ({', '.join(sb['flight_numbers'])}). "
        f"The week has {s['total_flights']} flights across {len(s['stations'])} stations with {len(s['fleet'])} aircraft."
        + "\n\n"
        + _reasoning(
            "schedule_stats — max/min of block_hours over flights.json (computed by the tool)"
        )
    )


def compose_routes(r: Results, e: Entities) -> str:
    if err := _err(r, "list_routes"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("list_routes failed")
    s = r["list_routes"]
    per = ", ".join(f"{k} ({v})" for k, v in s["flights_per_destination"].items())
    return (
        f"From {s['dep_station']} the network serves {len(s['destinations'])} stations nonstop: "
        f"{', '.join(s['destinations'])}. Flights per destination this week: {per}."
        + "\n\n"
        + _reasoning(
            f"list_routes({s['dep_station']}) — distinct arr_station where dep_station={s['dep_station']} in flights.json"
        )
    )


def compose_crew_list(r: Results, e: Entities) -> str:
    if err := _err(r, "list_crew"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("list_crew failed")
    s = r["list_crew"]
    f = s["filters"]
    label = " ".join(
        x for x in (f.get("rank"), f"based at {f['base']}" if f.get("base") else "") if x
    )
    if not s["crew"]:
        return f"No {label} found.\n\n" + _reasoning("list_crew returned 0 rows")
    lines = [
        f"- {c['crew_id']} ({c['name']}), ratings {'/'.join(c['ratings'])}, status {c['status']}"
        for c in s["crew"]
    ]
    return (
        f"{s['count']} {label}:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(f"list_crew({label}) from crew.json")
    )


def compose_flights(r: Results, e: Entities) -> str:
    if err := _err(r, "list_flights"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("list_flights failed")
    s = r["list_flights"]
    f = s["filters"]
    bits = []
    if f.get("dep_station") and f.get("arr_station"):
        bits.append(f"{f['dep_station']}→{f['arr_station']}")
    elif f.get("dep_station"):
        bits.append(f"departing {f['dep_station']}")
    elif f.get("arr_station"):
        bits.append(f"arriving {f['arr_station']}")
    if f.get("aircraft"):
        bits.append(f"on {f['aircraft']}")
    if f.get("date"):
        bits.append(f"on {f['date']}")
    if f.get("dep_from_utc"):
        bits.append(f"departing {f['dep_from_utc'][11:16]}–{f['dep_to_utc'][11:16]}Z")
    label = " ".join(bits) or "in the schedule"
    if not s["flights"]:
        return f"No flights {label}.\n\n" + _reasoning(f"list_flights({label}) returned 0 rows")
    lines = [
        f"- {x['flight_no']} {x['dep_station']}→{x['arr_station']} dep {x['dep_utc'][11:16]}Z arr {x['arr_utc'][11:16]}Z, "
        f"{x['aircraft']} ({x['seats']} seats)"
        for x in s["flights"]
    ]
    return (
        f"{s['count']} flight(s) {label}: {', '.join(s['flight_numbers'])}.\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning(f"list_flights({label}) filtered flights.json; all times UTC")
    )


def compose_rules(r: Results, e: Entities) -> str:
    if err := _err(r, "get_rules"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_rules failed")
    s = r["get_rules"]
    rules = s["rules"]
    if e.rule_ids:
        rules = [x for x in rules if x["rule_id"] in e.rule_ids] or rules
    lines = [
        f"- {x['rule_id']}: {x['text']}" + (f" (params: {x['params']})" if x.get("params") else "")
        for x in rules
    ]
    return (
        "Legality rules:\n"
        + "\n".join(lines)
        + "\n\n"
        + _reasoning("get_rules from rules.json (machine-readable ruleset)")
    )


def compose_costs(r: Results, e: Entities) -> str:
    if err := _err(r, "get_costs"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_costs failed")
    c = r["get_costs"]
    return (
        f"Cost rates ({c['currency']}): reserve callout pilot {c['reserve_callout_pilot']:,.0f} / cabin {c['reserve_callout_cabin']:,.0f}; "
        f"day-off callout pilot {c['dayoff_callout_pilot']:,.0f} / cabin {c['dayoff_callout_cabin']:,.0f}; "
        f"deadhead positioning {c['deadhead_positioning']:,.0f}; delay {c['delay_cost_per_duty_hour']:,.0f} per duty hour; "
        f"cancellation {c['cancellation_per_flight']:,.0f} per flight; hotel overnight {c['hotel_overnight']:,.0f}."
        + "\n\n"
        + _reasoning("get_costs from costs.json")
    )


def compose_snapshot(r: Results, e: Entities) -> str:
    if err := _err(r, "get_snapshot"):
        return f"{REFUSAL_PHRASE}: {err}.\n\n" + _reasoning("get_snapshot failed")
    s = r["get_snapshot"]
    return (
        f"Snapshot is {s['snapshot_utc']} (today {s['today']}, tomorrow {s['tomorrow']}); schedule week "
        f"{s['schedule_week']['start']} to {s['schedule_week']['end']}; hub {s['hub']}; stations {', '.join(s['stations'])}; "
        f"fleet {', '.join(a['aircraft'] + ' (' + a['aircraft_type'] + ')' for a in s['fleet'])}."
        + "\n\n"
        + _reasoning("get_snapshot from duty_clocks.json as_of_utc and flights.json")
    )


def snapshot_date(store: Datastore) -> date:
    return store.snapshot_utc.date()
