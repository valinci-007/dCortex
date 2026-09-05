"""Tier-3: ranked, rule-compliant resolution options with cost, legality and reasoning.

Heuristic ranking, not optimisation (the brief is explicit that this suffices):
enumerate every candidate of the needed rank, check them in the order a
controller would (rating, reserve window, then the full seven-rule evaluation),
cost the legal ones from costs.json, and sort by cost, then delay, then crew id.
Cancellation is always the last option so the trade-off is visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from itertools import product
from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.models import Crew, DutyPeriod, Pairing
from crew_ops_advisor.domain.timeutil import fmt_utc
from crew_ops_advisor.rules import RULE_ORDER, CrewContext, checks, evaluate_duties
from crew_ops_advisor.simulation.costs import (
    COMPLEMENTS,
    callout_cost,
    cancellation_cost,
    reserve_set_cost,
)
from crew_ops_advisor.simulation.engine import (
    TURNAROUND_MINUTES,
    SimulationError,
    crew_removal,
    plan_deadhead,
    reserve_coverage,
)
from crew_ops_advisor.simulation.engine import (
    delay as simulate_delay,
)
from crew_ops_advisor.simulation.models import DeadheadPlan


@dataclass(frozen=True, slots=True)
class Option:
    rank: int
    action: str
    crew_id: str | None
    kind: str  # reserve_callout | dayoff_callout | deadhead_callout | cancel | split_recrew
    legal: bool
    rules_checked: tuple[str, ...]
    cost_inr: float
    delay_hours: float
    reasoning: str
    coverage: str
    cost_breakdown: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, Any] | None = None
    margin: dict[str, Any] | None = None  # the tightest rule headroom this option leaves

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "action": self.action,
            "crew_id": self.crew_id,
            "kind": self.kind,
            "legal": self.legal,
            "rules_checked": list(self.rules_checked),
            "cost_inr": self.cost_inr,
            "delay_hours": self.delay_hours,
            "coverage": self.coverage,
            "reasoning": self.reasoning,
            "cost_breakdown": dict(self.cost_breakdown),
            "evidence": self.evidence,
            "margin": self.margin,
        }


@dataclass(frozen=True, slots=True)
class Excluded:
    crew_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"crew_id": self.crew_id, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class OptionsResult:
    pairing_id: str
    role: str
    from_date: date
    dates: tuple[date, ...]
    uncovered_flights: tuple[str, ...]
    passengers: int
    required_report_utc: datetime
    options: tuple[Option, ...]
    excluded: tuple[Excluded, ...]
    note: str = ""

    @property
    def expected_choice(self) -> Option | None:
        return self.options[0] if self.options else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pairing_id": self.pairing_id,
            "role": self.role,
            "from_date": self.from_date.isoformat(),
            "duty_dates": [d.isoformat() for d in self.dates],
            "uncovered_flights": list(self.uncovered_flights),
            "passengers_at_risk": self.passengers,
            "required_report_utc": fmt_utc(self.required_report_utc),
            "candidates_considered": len(self.options) + len(self.excluded) - 1,
            "options": [o.to_dict() for o in self.options],
            "expected_choice": self.expected_choice.to_dict() if self.expected_choice else None,
            "excluded_candidates": [e.to_dict() for e in self.excluded],
            "note": self.note,
        }


# ---------------------------------------------------------------- cover options


def rank_cover_options(
    store: Datastore,
    pairing_id: str,
    role: str,
    *,
    from_date: date | None = None,
    exclude_crew: tuple[str, ...] = (),
    max_options: int | None = None,
) -> OptionsResult:
    """Who can take the `role` slot of `pairing_id` from `from_date` (default: its first day)?"""
    pairing = store.pairings.get(pairing_id.upper())
    duties = store.pairings.duty_periods(pairing, from_date=from_date)
    if not duties:
        raise SimulationError(f"{pairing_id} has no duty days on or after {from_date}")
    if role not in {m.role for m in pairing.crew}:
        raise SimulationError(f"{pairing_id} has no {role} slot")
    first = duties[0]
    legs = [fid for d in duties for fid in d.flight_ids]
    passengers = sum(store.flights.get(f).seats for f in legs)
    current = {m.crew_id for m in pairing.crew}
    excluded_ids = set(exclude_crew) | current

    options: list[Option] = []
    excluded: list[Excluded] = []
    for crew in store.crew.list(rank=role, status="active"):
        if crew.crew_id in excluded_ids:
            continue
        verdict = _assess_candidate(store, crew, pairing, duties)
        if isinstance(verdict, Excluded):
            excluded.append(verdict)
        else:
            options.append(verdict)

    options.sort(key=lambda o: (o.cost_inr, o.delay_hours, o.crew_id or ""))
    if max_options is not None:
        options = options[:max_options]
    options.append(
        Option(
            rank=0,
            action=f"Cancel all {len(legs)} flights of the pairing",
            crew_id=None,
            kind="cancel",
            legal=True,
            rules_checked=(),
            cost_inr=cancellation_cost(store.costs, len(legs)),
            delay_hours=0.0,
            reasoning=(
                f"Last resort: {len(legs)} legs × {store.costs.cancellation_per_flight:.0f} INR; "
                f"{passengers} passengers stranded."
            ),
            coverage="none",
        )
    )
    ranked = tuple(replace(o, rank=i + 1) for i, o in enumerate(options))
    return OptionsResult(
        pairing_id=pairing.pairing_id,
        role=role,
        from_date=first.date,
        dates=tuple(d.date for d in duties),
        uncovered_flights=tuple(legs),
        passengers=passengers,
        required_report_utc=first.report_utc,
        options=ranked,
        excluded=tuple(sorted(excluded, key=lambda e: e.crew_id)),
        note=(
            "candidates = every active crew of the rank; checked rating → reserve window → all "
            "seven rules over their full timeline; ranked by cost, then delay, then crew id"
        ),
    )


# Headroom below which a legal option is flagged "tight" — the controller should know the
# cover works today but leaves little room for the next disruption.
TIGHT_HOURS = {"RULE-DUTY-02": 4.0, "RULE-FLT-03": 5.0, "RULE-REST-04": 1.0}


def tightest_margin(evidence) -> dict[str, Any] | None:
    """The rule with the least headroom among the verdicts that depend on the candidate —
    the rolling duty and block windows, and the rest before the first covered report. FDP
    and the rest between the pairing's own days are properties of the pairing, identical
    for every candidate, so they say nothing about which option is safer."""
    first = min(evidence.duty_dates) if evidence.duty_dates else None
    hours = [
        v
        for v in evidence.verdicts
        if v.margin is not None
        and v.passed
        and (
            v.rule_id in ("RULE-DUTY-02", "RULE-FLT-03")
            or (v.rule_id == "RULE-REST-04" and v.date == first)
        )
    ]
    if not hours:
        return None
    v = min(hours, key=lambda x: (x.margin / TIGHT_HOURS[x.rule_id], x.margin))
    tight = v.margin <= TIGHT_HOURS[v.rule_id]
    unit = "h"
    return {
        "rule": v.rule_id,
        "headroom_hours": round(v.margin, 2),
        "on": v.date.isoformat() if v.date else None,
        "label": "tight" if tight else "comfortable",
        "note": f"{v.rule_id} headroom {v.margin:.1f}{unit}"
        + (f" on {v.date.isoformat()}" if v.date else "")
        + (" — tight" if tight else ""),
    }


def _label(kind: str) -> str:
    return {"reserve_callout": "reserve callout", "dayoff_callout": "day-off callout"}.get(
        kind, kind
    )


def _assess_candidate(
    store: Datastore, crew: Crew, pairing: Pairing, duties: list[DutyPeriod]
) -> Option | Excluded:
    first = duties[0]
    actype = first.aircraft_type
    if actype not in crew.ratings:
        return Excluded(crew.crew_id, f"RULE-QUAL-05: no {actype} rating")

    deadhead: DeadheadPlan | None = None
    kind = "reserve_callout" if store.reserves.get(crew.crew_id) else "dayoff_callout"
    if crew.base != first.dep_station:
        deadhead = plan_deadhead(store, crew.base, first)
        if deadhead is None:
            return Excluded(
                crew.crew_id,
                f"RULE-BASE-07: based at {crew.base} with no positioning flight to "
                f"{first.dep_station} on {first.date.isoformat()}",
            )
    report = deadhead.new_report_utc if deadhead else first.report_utc

    reserve = store.reserves.get(crew.crew_id)
    if reserve is not None:
        if first.date not in reserve.dates:
            return Excluded(crew.crew_id, f"not on reserve on {first.date.isoformat()}")
        if not reserve.covers(report):
            return Excluded(
                crew.crew_id,
                f"reserve on-call window {reserve.oncall_start:%H:%M}-{reserve.oncall_end:%H:%M}Z "
                f"does not cover required report {report:%H:%M}Z",
            )

    ctx = CrewContext.load(store, crew.crew_id)
    evidence = evaluate_duties(ctx, store.ruleset, duties, callout=True)
    if not evidence.legal:
        return Excluded(crew.crew_id, "; ".join(evidence.issues))

    breakdown = {"callout": callout_cost(store.costs, crew.rank, kind)}
    delay_hours = 0.0
    action = f"Assign {crew.rank} {crew.crew_id} ({_label(kind)})"
    reasoning = (
        f"{crew.base}-based, {'/'.join(crew.ratings)}-rated, "
        + (
            f"on-call {reserve.oncall_start:%H:%M}-{reserve.oncall_end:%H:%M}Z, "
            if reserve
            else "not rostered on the cover days, "
        )
        + f"reachable in {crew.reachability_minutes} min; all seven rules pass."
    )
    if deadhead:
        base_kind = _label(kind)
        kind = "deadhead_callout"
        delay_hours = deadhead.delay_hours
        breakdown["deadhead_positioning"] = deadhead.positioning_cost_inr
        breakdown["delay"] = deadhead.delay_cost_inr
        action = (
            f"Assign {crew.rank} {crew.crew_id} ({base_kind} + deadhead from {crew.base} "
            f"(first departure delayed ~{delay_hours:.1f}h))"
        )
        reasoning = (
            f"Legal but incurs deadhead on {deadhead.flight_no} (arr {deadhead.arrives_utc:%H:%M}Z, "
            f"report {deadhead.new_report_utc:%H:%M}Z) and ~{delay_hours:.1f}h delay to "
            f"{first.flight_ids[0].split('-')[0]}."
        )
    return Option(
        rank=0,
        action=action,
        crew_id=crew.crew_id,
        kind=kind,
        legal=True,
        rules_checked=tuple(RULE_ORDER),
        cost_inr=round(sum(breakdown.values()), 2),
        delay_hours=delay_hours,
        reasoning=reasoning,
        coverage=f"all {len(duties)} duty day(s)" if len(duties) > 1 else "all legs",
        cost_breakdown=breakdown,
        evidence={"issues": [], "conditions": [v.detail for v in evidence.conditions]},
        margin=tightest_margin(evidence),
    )


def recommend_cover(
    store: Datastore,
    crew_id: str,
    *,
    pairing_id: str | None = None,
    from_date: date | None = None,
    reported_utc: datetime | None = None,
    max_options: int | None = None,
) -> tuple[dict[str, Any], OptionsResult]:
    """A crew member is out: find the duty they leave uncovered and rank the covers."""
    impact = crew_removal(
        store, crew_id, from_date=from_date, reported_utc=reported_utc, pairing_id=pairing_id
    )
    if not impact.days:
        raise SimulationError(f"{crew_id} has no rostered duty to cover in that period")
    day = impact.days[0]
    result = rank_cover_options(
        store,
        day.pairing_id,
        day.role,
        from_date=day.date,
        exclude_crew=(crew_id,),
        max_options=max_options,
    )
    return impact.to_dict(), result


# ---------------------------------------------------------------- joint plans


def joint_cover_plan(
    store: Datastore, events: list[dict[str, Any]], *, top_k: int = 6
) -> dict[str, Any]:
    """Several crew out at once: rank options per duty, then pick the cheapest combination
    that assigns no person twice. Equal-cost combinations are equally correct."""
    per_event: list[tuple[dict[str, Any], OptionsResult]] = []
    for ev in events:
        impact, result = recommend_cover(
            store,
            ev["crew_id"],
            pairing_id=ev.get("pairing_id"),
            reported_utc=ev.get("reported_utc"),
            from_date=ev.get("from_date"),
        )
        per_event.append((impact, result))

    shortlists = [
        [o for o in r.options if o.kind != "cancel"][:top_k] + [r.options[-1]] for _, r in per_event
    ]
    best: tuple[float, tuple[Option, ...]] | None = None
    for combo in product(*shortlists):
        ids = [o.crew_id for o in combo if o.crew_id]
        if len(ids) != len(set(ids)):
            continue
        total = sum(o.cost_inr for o in combo)
        if best is None or total < best[0]:
            best = (total, combo)
    assert best is not None
    total, combo = best
    return {
        "events": [
            {
                "crew_id": impact["crew_id"],
                "pairing_id": result.pairing_id,
                "role": result.role,
                "uncovered_flights": list(result.uncovered_flights),
                "options": [o.to_dict() for o in result.options[:top_k]],
                "excluded_candidates": [e.to_dict() for e in result.excluded],
            }
            for impact, result in per_event
        ],
        "plan": [
            {"pairing_id": r.pairing_id, "role": r.role, **o.to_dict()}
            for (_, r), o in zip(per_event, combo, strict=True)
        ],
        "total_cost_inr": round(total, 2),
        "note": "cheapest combination with no person assigned twice; equal-cost plans are equally valid",
    }


# ---------------------------------------------------------------- delay recovery


def resolve_delay_options(
    store: Datastore,
    on: date,
    delay_hours: float,
    *,
    aircraft: str | None = None,
    flight_no: str | None = None,
) -> dict[str, Any]:
    """After a delay: let the rostered crew fly the legal prefix and re-crew the tail from
    reserves, or cancel the tail — each costed and legality-checked."""
    impact = simulate_delay(store, on, delay_hours, aircraft=aircraft, flight_no=flight_no)
    d = impact.to_dict()
    if not impact.breach:
        return {
            **d,
            "options": [],
            "note": "no FDP breach: the rostered crew can complete the duty",
        }
    tail = list(impact.flights[impact.legal_leg_count :])
    head = list(impact.flights[: impact.legal_leg_count])
    tail_legs = store.flights.get_many(tail)
    actype = tail_legs[0].aircraft_type
    comp = COMPLEMENTS[actype]
    shift = timedelta(hours=delay_hours)
    tail_report = tail_legs[0].dep_utc + shift - timedelta(minutes=60)
    tail_release = tail_legs[-1].arr_utc + shift + timedelta(minutes=TURNAROUND_MINUTES)
    tail_fdp = round((tail_release - tail_report).total_seconds() / 3600, 2)

    # A full reserve complement for the tail: reserves based where the duty starts (they
    # position on the crew's own earlier legs), on call at the tail report time, rated.
    coverage_ok = True
    per_role: dict[str, list[str]] = {}
    for rank, needed in comp.items():
        rows = reserve_coverage(
            store,
            tail_report,
            rank=rank,
            aircraft_type=actype,
            station=impact.flights and store.flights.get(impact.flights[0]).dep_station,
        )
        eligible = [r.crew_id for r in rows if r.eligible]
        per_role[rank] = eligible[:needed]
        if len(eligible) < needed:
            coverage_ok = False

    head_fdp = 0.0
    if head:
        head_legs = store.flights.get_many(head)
        head_release = head_legs[-1].arr_utc + shift + timedelta(minutes=TURNAROUND_MINUTES)
        head_fdp = round((head_release - impact.original_report_utc).total_seconds() / 3600, 2)
    head_limit = checks.fdp_limit(len(head), store.ruleset) if head else 0.0

    options: list[dict[str, Any]] = []
    recrew_cost = reserve_set_cost(store.costs, actype)
    roles_label = "CPT, FO, SCC, " + f"{comp['Cabin Crew']} CC"
    options.append(
        {
            "rank": 1,
            "action": (
                f"Original crew operates {head[0].split('-')[0]}–{head[-1].split('-')[0]} (delayed); "
                f"full reserve set ({roles_label}) operates "
                + "/".join(f.split("-")[0] for f in tail)
            ),
            "legal": coverage_ok,
            "cost_inr": recrew_cost,
            "reasoning": (
                f"Delayed {len(head)}-leg duty FDP {head_fdp:.1f}h vs {head_limit:.1f}h limit — legal. "
                f"Reserve set covers the last sector{'s' if len(tail) > 1 else ''} (report "
                f"{tail_report:%H:%M}Z, FDP {tail_fdp:.2f}h; callout window and 12h rest satisfied)."
                + ("" if coverage_ok else " Not enough eligible reserves for every role.")
            ),
            "reserve_set": per_role,
            "cost_breakdown": {"reserve_callouts": recrew_cost},
        }
    )
    cancel_cost = cancellation_cost(store.costs, len(tail))
    options.append(
        {
            "rank": 2,
            "action": "Cancel " + ", ".join(f.split("-")[0] for f in tail),
            "legal": True,
            "cost_inr": cancel_cost,
            "reasoning": (
                f"Legal but ~{cancel_cost / recrew_cost:.1f}x more expensive than re-crewing; "
                f"{sum(f.seats for f in tail_legs)} passengers stranded."
            ),
            "cost_breakdown": {"cancellation": cancel_cost},
        }
    )
    options.sort(key=lambda o: (not o["legal"], o["cost_inr"]))
    for i, o in enumerate(options):
        o["rank"] = i + 1
    return {**d, "options": options, "expected_choice": options[0]}


# ---------------------------------------------------------------- notifications


def draft_notification(
    store: Datastore,
    crew_id: str,
    pairing_id: str,
    *,
    from_date: date | None = None,
    reason: str = "crew unavailability",
    ack_deadline_minutes: int = 30,
    contact: str = "Crew Control desk, BLR",
) -> dict[str, Any]:
    """A callout notification with every operational fact drawn from the roster."""
    crew = store.crew.get(crew_id)
    pairing = store.pairings.get(pairing_id.upper())
    duties = store.pairings.duty_periods(pairing, from_date=from_date)
    if not duties:
        raise SimulationError(f"{pairing_id} has no duty days on or after {from_date}")
    days = []
    for i, d in enumerate(duties):
        legs = store.flights.get_many(d.flight_ids)
        overnight = i < len(duties) - 1 and legs[-1].arr_station != first_station(duties)
        days.append(
            {
                "date": d.date.isoformat(),
                "report_utc": fmt_utc(d.report_utc),
                "report_place": f"{d.dep_station} crew room",
                "flights": [
                    f"{f.flight_no} {f.dep_station}-{f.arr_station} {f.dep_utc:%H:%M}Z-{f.arr_utc:%H:%M}Z"
                    for f in legs
                ],
                "release_utc": fmt_utc(d.release_utc),
                "overnight_at": legs[-1].arr_station if overnight else None,
                "hotel": "arranged" if overnight else None,
            }
        )
    deadline = store.snapshot_utc + timedelta(minutes=ack_deadline_minutes)
    lines = [
        f"CALLOUT — Crew ID {crew.crew_id} ({crew.name}, {crew.rank}) — Pairing ID {pairing.pairing_id}",
        f"You are assigned to pairing {pairing.pairing_id} ({pairing.aircraft}) due to {reason}.",
    ]
    for n, day in enumerate(days, start=1):
        lines.append(
            f"Day {n} ({day['date']}): report {day['report_utc'][11:16]}Z at {day['report_place']}; "
            f"flights {', '.join(day['flights'])}; release {day['release_utc'][11:16]}Z."
        )
        if day["overnight_at"]:
            lines.append(f"  Overnight at {day['overnight_at']} — hotel {day['hotel']}.")
    lines.append(
        f"Acknowledgement request — deadline {fmt_utc(deadline)} ({ack_deadline_minutes} minutes): "
        f"reply ACK {pairing.pairing_id}."
    )
    lines.append(f"Contact for questions: {contact}.")
    return {
        "crew_id": crew.crew_id,
        "crew_name": crew.name,
        "rank": crew.rank,
        "pairing_id": pairing.pairing_id,
        "aircraft": pairing.aircraft,
        "reason": reason,
        "days": days,
        "acknowledge_by_utc": fmt_utc(deadline),
        "contact": contact,
        "message": "\n".join(lines),
        "must_include": [
            "crew id and pairing id",
            "report time and place for each day",
            "flights per day",
            "overnight station and hotel where the pairing overnights",
            "acknowledgement request with deadline",
            "contact for questions",
        ],
    }


def first_station(duties: list[DutyPeriod]) -> str:
    return duties[0].dep_station


# ---------------------------------------------------------------- morning briefing


def morning_briefing(store: Datastore, on: date) -> dict[str, Any]:
    """Per aircraft line for a day: rostered crew's legality headroom, risk signals, and
    reserve availability by rating — the three things a desk should see first."""
    lines = []
    for reg, actype in store.flights.aircraft():
        pairing = store.pairings.for_aircraft_on(reg, on)
        if pairing is None:
            continue
        day = next(d for d in pairing.days if d.date == on)
        duty = store.pairings.duty_period(pairing, day)
        crew_rows = []
        for m in pairing.crew:
            ctx = CrewContext.load(store, m.crew_id)
            from crew_ops_advisor.rules import daily_totals

            duty_by_date, _ = daily_totals(ctx, ctx.rostered_duties)
            start = on - timedelta(days=int(store.ruleset.param(checks.DUTY, "window_days")) - 1)
            total7 = round(sum(v for d, v in duty_by_date.items() if start <= d <= on), 2)
            limit = float(store.ruleset.param(checks.DUTY, "max_duty_hours"))
            try:
                risk = store.risk.get(m.crew_id).disruption_risk_score
            except LookupError:
                risk = None
            certs_ok = all(c.valid_to >= on for c in store.certifications.for_crew(m.crew_id))
            crew_rows.append(
                {
                    "crew_id": m.crew_id,
                    "role": m.role,
                    "duty_hours_7d_through_today": total7,
                    "duty_headroom_7d": round(limit - total7, 2),
                    "certifications_valid": certs_ok,
                    "disruption_risk_score": risk,
                }
            )
        reserves = reserve_coverage(
            store, duty.report_utc, aircraft_type=actype, station=duty.dep_station
        )
        lines.append(
            {
                "aircraft": reg,
                "aircraft_type": actype,
                "pairing_id": pairing.pairing_id,
                "report_utc": fmt_utc(duty.report_utc),
                "flights": [f.split("-")[0] for f in duty.flight_ids],
                "tightest_duty_headroom_7d": min(c["duty_headroom_7d"] for c in crew_rows),
                "highest_risk": max((c["disruption_risk_score"] or 0) for c in crew_rows),
                "all_certs_valid": all(c["certifications_valid"] for c in crew_rows),
                "eligible_reserves_at_report": [r.crew_id for r in reserves if r.eligible],
                "crew": crew_rows,
            }
        )
    return {
        "date": on.isoformat(),
        "lines": lines,
        "surfaced": [
            "crew legality headroom (7d duty) for today's rostered crew",
            "reserve availability by on-call window and rating for the day",
            "risk signals for today's rostered crew (provided input)",
        ],
    }
