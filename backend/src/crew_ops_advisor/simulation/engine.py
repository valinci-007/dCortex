"""Tier-2 simulations: what breaks when a disruption hits, and whether a fix is legal.

Every function here is deterministic and returns a typed result whose to_dict()
is what the model sees. Legality always goes through the rules engine; nothing
here re-implements a rule.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.models import Crew, DutyPeriod, Flight, Pairing, ReserveEntry
from crew_ops_advisor.rules import CrewContext, checks, daily_totals, evaluate_duties
from crew_ops_advisor.simulation.costs import callout_cost, cancellation_cost, deadhead_costs
from crew_ops_advisor.simulation.models import (
    AssignmentCheck,
    CancellationImpact,
    ClosureImpact,
    CrewDelayCheck,
    CrewRemovalImpact,
    DeadheadPlan,
    DelayImpact,
    FlightAssessment,
    NearLimit,
    ReserveCandidate,
    UncoveredDay,
)

DEADHEAD_REPORT_AFTER_ARRIVAL = timedelta(minutes=15)
TURNAROUND_MINUTES = 30


class SimulationError(ValueError):
    """The simulation cannot be run for these inputs (user-facing message)."""


# ---------------------------------------------------------------- crew removal


def crew_removal(
    store: Datastore,
    crew_id: str,
    *,
    from_date: date | None = None,
    reported_utc: datetime | None = None,
    pairing_id: str | None = None,
    through_date: date | None = None,
) -> CrewRemovalImpact:
    """A crew member is unavailable from `from_date` (default: the reported day, else the
    snapshot day). Which rostered flights lose them, and what that exposes.

    Scope: the named pairing if given; otherwise the first affected pairing and all of its
    remaining days (a sick call covers that duty); `through_date` widens it to every
    pairing with days up to that date.
    """
    crew = store.crew.get(crew_id)
    start = from_date or (reported_utc.date() if reported_utc else store.snapshot_utc.date())
    pairings = store.pairings.for_crew(crew_id)
    if pairing_id:
        pairings = [p for p in pairings if p.pairing_id == pairing_id.upper()]
        if not pairings:
            raise SimulationError(f"{crew_id} is not rostered on {pairing_id}")
    affected_pairings: list[tuple[Pairing, list]] = []
    for pairing in sorted(pairings, key=lambda p: p.dates[0]):
        affected = [d for d in pairing.days if d.date >= start]
        if reported_utc is not None:
            affected = [d for d in affected if d.release_utc > reported_utc]
        if through_date is not None:
            affected = [d for d in affected if d.date <= through_date]
        if affected:
            affected_pairings.append((pairing, affected))
    if not pairing_id and through_date is None and affected_pairings:
        affected_pairings = affected_pairings[:1]  # the duty the sick call is for

    days: list[UncoveredDay] = []
    multi_day = False
    for pairing, affected in affected_pairings:
        multi_day = multi_day or len(affected) > 1
        for i, day in enumerate(affected):
            legs = store.flights.get_many(day.flight_ids)
            days.append(
                UncoveredDay(
                    date=day.date,
                    pairing_id=pairing.pairing_id,
                    role=pairing.role_of(crew_id) or crew.rank,
                    flight_ids=day.flight_ids,
                    passengers=sum(f.seats for f in legs),
                    immediate=(i == 0),
                    starts_at=legs[0].dep_station,
                    ends_at=legs[-1].arr_station,
                )
            )
    days.sort(key=lambda d: (d.date, d.pairing_id))
    note = ""
    if multi_day:
        note = (
            "a multi-day pairing: the aircraft overnights away from base, so the cover must take "
            "the full remaining pairing"
        )
    elif not days:
        note = f"{crew_id} has no rostered duties on or after {start.isoformat()}"
    return CrewRemovalImpact(
        crew_id=crew_id,
        crew_name=crew.name,
        rank=crew.rank,
        from_date=start,
        days=tuple(days),
        cover_must_take_full_pairing=multi_day,
        note=note,
    )


# ---------------------------------------------------------------- assignment legality


def plan_deadhead(
    store: Datastore, from_station: str, first_duty: DutyPeriod
) -> DeadheadPlan | None:
    """Earliest positioning flight from the crew's base to the duty's start station on the
    duty date; new report = arrival + 15 min; delay = how late the first departure becomes."""
    candidates = store.flights.list(
        on=first_duty.date, dep_station=from_station, arr_station=first_duty.dep_station
    )
    if not candidates:
        return None
    flight = min(candidates, key=lambda f: f.arr_utc)
    new_report = flight.arr_utc + DEADHEAD_REPORT_AFTER_ARRIVAL
    delay_hours = max(0.0, (new_report - first_duty.report_utc).total_seconds() / 3600)
    delay_hours = round(delay_hours * 4) / 4  # schedule granularity is 15 min
    positioning, delay_cost = deadhead_costs(store.costs, delay_hours)
    return DeadheadPlan(
        from_station=from_station,
        to_station=first_duty.dep_station,
        flight_id=flight.flight_id,
        flight_no=flight.flight_no,
        arrives_utc=flight.arr_utc,
        new_report_utc=new_report,
        scheduled_report_utc=first_duty.report_utc,
        delay_hours=delay_hours,
        positioning_cost_inr=positioning,
        delay_cost_inr=delay_cost,
    )


def callout_kind_for(store: Datastore, crew: Crew, pairing: Pairing) -> str:
    if crew.crew_id in pairing.crew_ids:
        return "rostered"
    return "reserve_callout" if store.reserves.get(crew.crew_id) else "dayoff_callout"


def reserve_window_covers(reserve: ReserveEntry, report_utc: datetime) -> bool:
    return reserve.covers(report_utc)


def assignment_check(
    store: Datastore,
    crew_id: str,
    pairing_id: str,
    *,
    from_date: date | None = None,
) -> AssignmentCheck:
    """Can `crew_id` operate `pairing_id` (from `from_date`, default: its first day)?

    Rostered crew are re-evaluated on their own duty; anyone else is a callout: reserve
    callout if they are in the reserve pool, day-off callout otherwise. Off-base callouts
    get a deadhead plan (RULE-BASE-07) and its cost and delay.
    """
    crew = store.crew.get(crew_id)
    pairing = store.pairings.get(pairing_id)
    duties = store.pairings.duty_periods(pairing, from_date=from_date)
    if not duties:
        operates = ", ".join(d.isoformat() for d in pairing.dates)
        raise SimulationError(
            f"{pairing_id} has no duty days on or after {from_date} (operates {operates})"
        )
    kind = callout_kind_for(store, crew, pairing)
    ctx = CrewContext.load(store, crew_id)
    if kind == "rostered":
        evidence = evaluate_duties(
            ctx, store.ruleset, duties, replacing=[(d.pairing_id, d.date) for d in duties]
        )
        return AssignmentCheck(
            crew_id,
            crew.name,
            crew.rank,
            pairing_id,
            duties[0].date,
            tuple(d.date for d in duties),
            kind,
            evidence,
            None,
            None,
        )

    evidence = evaluate_duties(ctx, store.ruleset, duties, callout=True)
    deadhead = None
    if crew.base != duties[0].dep_station:
        deadhead = plan_deadhead(store, crew.base, duties[0])
    breakdown = {"callout": callout_cost(store.costs, crew.rank, kind)}
    if deadhead:
        breakdown["deadhead_positioning"] = deadhead.positioning_cost_inr
        breakdown["delay"] = deadhead.delay_cost_inr
    role_ok, role_note = True, ""
    if crew.rank not in {m.role for m in pairing.crew}:
        role_ok, role_note = False, f"{crew.rank} has no matching role on {pairing_id}"
    report = deadhead.new_report_utc if deadhead else duties[0].report_utc
    available, availability_note = reserve_availability(store, crew_id, report)
    return AssignmentCheck(
        crew_id,
        crew.name,
        crew.rank,
        pairing_id,
        duties[0].date,
        tuple(d.date for d in duties),
        kind,
        evidence,
        deadhead,
        round(sum(breakdown.values()), 2),
        breakdown,
        role_ok,
        role_note,
        available,
        availability_note,
    )


def reserve_availability(store: Datastore, crew_id: str, report_utc: datetime) -> tuple[bool, str]:
    """Whether a reserve's on-call window covers the required report time (availability,
    not one of the seven rules)."""
    reserve = store.reserves.get(crew_id)
    if reserve is None:
        return True, "not a reserve (day-off callout)"
    if reserve.covers(report_utc):
        return True, (
            f"reserve on-call window {reserve.oncall_start:%H:%M}-{reserve.oncall_end:%H:%M}Z "
            f"covers required report {report_utc:%H:%M}Z"
        )
    return False, (
        f"reserve on-call window {reserve.oncall_start:%H:%M}-{reserve.oncall_end:%H:%M}Z "
        f"does not cover required report {report_utc:%H:%M}Z"
    )


# ---------------------------------------------------------------- station closure


def station_closure(
    store: Datastore,
    station: str,
    start_utc: datetime,
    end_utc: datetime,
    *,
    turnaround_minutes: int = TURNAROUND_MINUTES,
) -> ClosureImpact:
    """Flights departing or arriving `station` inside the window, each with the minimum
    delay to reopen + turnaround and what that does to the operating crew's FDP."""
    station = station.upper()
    if end_utc <= start_utc:
        raise SimulationError("closure window end must be after its start")
    reopen = end_utc + timedelta(minutes=turnaround_minutes)
    assessments: list[FlightAssessment] = []
    for flight in store.flights.list(on=start_utc.date()) + (
        store.flights.list(on=end_utc.date()) if end_utc.date() != start_utc.date() else []
    ):
        if flight.dep_station == station and start_utc <= flight.dep_utc <= end_utc:
            at, scheduled = "departure", flight.dep_utc
        elif flight.arr_station == station and start_utc <= flight.arr_utc <= end_utc:
            at, scheduled = "arrival", flight.arr_utc
        else:
            continue
        pairing = store.pairings.for_flight(flight.flight_id)
        if pairing is None:
            continue
        day = next(d for d in pairing.days if flight.flight_id in d.flight_ids)
        duty = store.pairings.duty_period(pairing, day)
        delay = round((reopen - scheduled).total_seconds() / 3600, 2)
        limit = checks.fdp_limit(duty.sectors, store.ruleset)
        after = round(duty.duty_hours + delay, 2)
        assessments.append(
            FlightAssessment(
                flight_id=flight.flight_id,
                flight_no=flight.flight_no,
                at_station=at,
                scheduled_utc=scheduled,
                pairing_id=pairing.pairing_id,
                min_delay_hours=delay,
                duty_hours=round(duty.duty_hours, 2),
                sectors=duty.sectors,
                fdp_after_delay=after,
                fdp_limit=limit,
                breach=after > limit + 1e-6,
                seats=flight.seats,
            )
        )
    assessments.sort(key=lambda a: (a.scheduled_utc, a.flight_no))
    return ClosureImpact(station, start_utc, end_utc, turnaround_minutes, tuple(assessments))


# ---------------------------------------------------------------- delay


def _pairing_day_for(
    store: Datastore, on: date, *, aircraft: str | None, flight_no: str | None
) -> tuple[Pairing, DutyPeriod, Flight | None]:
    if flight_no:
        flight = store.flights.by_number(flight_no.upper(), on)
        if flight is None:
            raise SimulationError(f"no flight {flight_no} on {on.isoformat()}")
        pairing = store.pairings.for_flight(flight.flight_id)
    elif aircraft:
        flight = None
        pairing = store.pairings.for_aircraft_on(aircraft.upper(), on)
    else:
        raise SimulationError("give an aircraft registration or a flight number")
    if pairing is None:
        raise SimulationError(f"no pairing operates {aircraft or flight_no} on {on.isoformat()}")
    day = next(d for d in pairing.days if d.date == on)
    return pairing, store.pairings.duty_period(pairing, day), flight


def delay(
    store: Datastore,
    on: date,
    delay_hours: float,
    *,
    aircraft: str | None = None,
    flight_no: str | None = None,
) -> DelayImpact:
    """All remaining legs of the aircraft's duty that day shift by `delay_hours` (report
    time is unchanged: the crew is already on duty). FDP after delay is checked, every
    rostered crew member is re-evaluated, and the longest legal prefix of legs is found."""
    if delay_hours <= 0:
        raise SimulationError("delay_hours must be positive")
    pairing, duty, _ = _pairing_day_for(store, on, aircraft=aircraft, flight_no=flight_no)
    shift = timedelta(hours=delay_hours)
    delayed = replace(duty, release_utc=duty.release_utc + shift)
    limit = checks.fdp_limit(duty.sectors, store.ruleset)
    fdp_after = round(delayed.duty_hours, 2)

    legs = store.flights.get_many(duty.flight_ids)
    legal_count = 0
    for k in range(len(legs), 0, -1):
        release_k = legs[k - 1].arr_utc + timedelta(minutes=TURNAROUND_MINUTES) + shift
        fdp_k = (release_k - duty.report_utc).total_seconds() / 3600
        if fdp_k <= checks.fdp_limit(k, store.ruleset) + 1e-6:
            legal_count = k
            break

    crew_checks = []
    for member in pairing.crew:
        ctx = CrewContext.load(store, member.crew_id)
        ev = evaluate_duties(
            ctx, store.ruleset, [delayed], replacing=[(pairing.pairing_id, duty.date)]
        )
        crew_checks.append(CrewDelayCheck(member.crew_id, member.role, ev))

    return DelayImpact(
        aircraft=pairing.aircraft,
        date=on,
        pairing_id=pairing.pairing_id,
        delay_hours=delay_hours,
        first_flight=duty.flight_ids[0].split("-")[0],
        flights=duty.flight_ids,
        original_report_utc=duty.report_utc,
        original_release_utc=duty.release_utc,
        new_release_utc=delayed.release_utc,
        fdp_before=round(duty.duty_hours, 2),
        fdp_after=fdp_after,
        fdp_limit=limit,
        sectors=duty.sectors,
        crew_checks=tuple(crew_checks),
        legal_leg_count=legal_count,
    )


# ---------------------------------------------------------------- cancellation


def cancellation(store: Datastore, flight_no: str, on: date) -> CancellationImpact:
    flight = store.flights.by_number(flight_no.upper(), on)
    if flight is None:
        raise SimulationError(f"no flight {flight_no} on {on.isoformat()}")
    pairing = store.pairings.for_flight(flight.flight_id)
    return CancellationImpact(
        flight_id=flight.flight_id,
        flight_no=flight.flight_no,
        date=on,
        seats=flight.seats,
        cost_inr=cancellation_cost(store.costs, 1),
        pairing_id=pairing.pairing_id if pairing else None,
        crew_ids=pairing.crew_ids if pairing else (),
        route=f"{flight.dep_station}-{flight.arr_station}",
    )


# ---------------------------------------------------------------- near limits


def near_limits(
    store: Datastore,
    on: date,
    *,
    min_duty_hours: float | None = None,
    max_duty_headroom: float | None = None,
    max_flight_headroom: float | None = None,
) -> list[NearLimit]:
    """Crew whose rolling windows ending on `on` (history + rostered duties through that
    day) meet a threshold. Defaults to duty hours >= 45 in the 7-day window."""
    if min_duty_hours is None and max_duty_headroom is None and max_flight_headroom is None:
        min_duty_hours = 45.0
    duty_limit = float(store.ruleset.param(checks.DUTY, "max_duty_hours"))
    flight_limit = float(store.ruleset.param(checks.FLT, "max_flight_hours"))
    duty_days = int(store.ruleset.param(checks.DUTY, "window_days"))
    flight_days = int(store.ruleset.param(checks.FLT, "window_days"))
    out: list[NearLimit] = []
    for crew in store.crew.list(status="active"):
        ctx = CrewContext.load(store, crew.crew_id)
        duty_by_date, flight_by_date = daily_totals(ctx, ctx.rostered_duties)
        d_start, f_start = on - timedelta(days=duty_days - 1), on - timedelta(days=flight_days - 1)
        duty7 = round(sum(v for d, v in duty_by_date.items() if d_start <= d <= on), 2)
        flight28 = round(sum(v for d, v in flight_by_date.items() if f_start <= d <= on), 2)
        planned = round(sum(d.duty_hours for d in ctx.rostered_duties if d.date == on), 2)
        hit = (
            (min_duty_hours is not None and duty7 >= min_duty_hours)
            or (max_duty_headroom is not None and duty_limit - duty7 <= max_duty_headroom)
            or (max_flight_headroom is not None and flight_limit - flight28 <= max_flight_headroom)
        )
        if hit:
            out.append(
                NearLimit(
                    crew.crew_id,
                    crew.name,
                    crew.rank,
                    duty7,
                    round(duty_limit - duty7, 2),
                    flight28,
                    round(flight_limit - flight28, 2),
                    planned,
                )
            )
    out.sort(key=lambda n: (-n.duty_hours_7d, n.crew_id))
    return out


# ---------------------------------------------------------------- reserve coverage


def reserve_coverage(
    store: Datastore,
    required_report_utc: datetime,
    *,
    rank: str | None = None,
    aircraft_type: str | None = None,
    station: str | None = None,
) -> list[ReserveCandidate]:
    """Which reserves could be called out for a duty reporting at `required_report_utc`:
    on reserve that day, window covers the report time, rank/rating/base as required."""
    out: list[ReserveCandidate] = []
    for reserve in store.reserves.list(on=required_report_utc.date()):
        crew = store.crew.get(reserve.crew_id)
        if rank and crew.rank != rank:
            continue
        window = (reserve.oncall_start.strftime("%H:%M"), reserve.oncall_end.strftime("%H:%M"))
        reasons: list[str] = []
        if aircraft_type and aircraft_type not in crew.ratings:
            reasons.append(f"RULE-QUAL-05: no {aircraft_type} rating")
        if not reserve.covers(required_report_utc):
            reasons.append(
                f"reserve on-call window {window[0]}-{window[1]}Z does not cover required "
                f"report {required_report_utc:%H:%M}Z"
            )
        if station and reserve.base != station.upper():
            reasons.append(
                f"RULE-BASE-07: based at {reserve.base}, duty starts at {station.upper()} "
                "(deadhead positioning required)"
            )
        eligible = not reasons
        out.append(
            ReserveCandidate(
                crew.crew_id,
                crew.name,
                crew.rank,
                reserve.base,
                crew.ratings,
                window,
                crew.reachability_minutes,
                eligible,
                "; ".join(reasons)
                if reasons
                else f"window {window[0]}-{window[1]}Z covers {required_report_utc:%H:%M}Z"
                + (f"; rated {aircraft_type}" if aircraft_type else ""),
            )
        )
    out.sort(key=lambda c: (not c.eligible, c.reachability_minutes, c.crew_id))
    return out


# ---------------------------------------------------------------- misc


def earliest_report(store: Datastore, release_utc: datetime) -> datetime:
    return checks.earliest_next_report(release_utc, store.ruleset)


def seats_at_risk(store: Datastore) -> dict:
    """Which single leg has the most seats at risk if cancelled: the answer is by type."""
    flights = store.flights.list()
    by_type: dict[str, dict] = {}
    for f in flights:
        t = by_type.setdefault(
            f.aircraft_type, {"seats": f.seats, "legs": 0, "example": f.flight_no}
        )
        t["legs"] += 1
        t["seats"] = max(t["seats"], f.seats)
    ranked = sorted(by_type.items(), key=lambda kv: -kv[1]["seats"])
    top_type, top = ranked[0]
    others = ", ".join(f"{k} legs ({v['seats']} seats)" for k, v in ranked[1:])
    return {
        "most_seats_at_risk": f"any {top_type} leg ({top['seats']} seats)",
        "compared_with": others,
        "by_aircraft_type": {k: v for k, v in ranked},
        "cancellation_cost_per_leg_inr": store.costs.cancellation_per_flight,
        "reason": (
            "seats are fixed by aircraft type; every leg of the larger type carries the same "
            "exposure"
        ),
    }
