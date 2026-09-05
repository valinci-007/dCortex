"""Positioning cover (ADR-0020): when nobody at the station can legally take a duty, who
elsewhere can be flown in before the departure we are covering?

Deterministic, like every other simulation. For one role on one pairing from one date:

  1. Where is every qualified crew member at the required report time? Read from the
     roster — the end station of their last released duty, or the duty they are on — and
     the base only when the roster says nothing. A BLR captain overnighting in DEL is in DEL.
  2. Crew already at the station (including those landing there on their current trip) are
     "present": no positioning, the normal seven-rule check applies. A crew member whose
     current duty ends at the station shortly before the report may also *extend* that
     duty — the covered legs are added to the same flight duty period, no rest in between —
     and RULE-FDP-01 decides with the extra sectors counted.
  3. Everyone else needs an itinerary to the station on our own network: a direct flight,
     one connection through the hub (30 min minimum), or an earlier flight with a hotel
     overnight. The only hard constraint is the controller's: arrival plus a 15-minute
     buffer must be before the departure of the first flight we are covering. Arriving before
     the scheduled report is "on time"; between report and departure is a late report with
     no delay to the flight — shown, ranked after the on-time options, for the controller to
     decide. Nothing here delays a departure.
  4. Every option is checked against all seven rules with the crew member's full timeline
     and costed: callout + positioning legs × the deadhead rate + hotel if overnight.
     Positioning legs are not flying duty and do not shorten rest (consistent with the
     answer keys' deadhead treatment).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.models import Crew, DutyPeriod, Flight
from crew_ops_advisor.domain.timeutil import fmt_utc
from crew_ops_advisor.rules import CrewContext, evaluate_duties
from crew_ops_advisor.rules.verdicts import LegalityEvidence
from crew_ops_advisor.simulation import SimulationError
from crew_ops_advisor.simulation.costs import callout_cost
from crew_ops_advisor.simulation.engine import DEADHEAD_REPORT_AFTER_ARRIVAL

MIN_CONNECTION = timedelta(minutes=30)
ARRIVAL_BUFFER = DEADHEAD_REPORT_AFTER_ARRIVAL  # 15 min from touchdown to report
MAX_LOOKBACK = timedelta(days=2)  # how far back an "earlier flight + hotel" may start


# ---------------------------------------------------------------- where is everyone


@dataclass(frozen=True, slots=True)
class Position:
    crew_id: str
    station: str
    available_from: datetime | None  # release of the duty that put them there; None = base
    source: str  # "base" | "released" | "in duty"
    duty: DutyPeriod | None = None  # the duty they are on / just finished

    def to_dict(self) -> dict[str, Any]:
        return {
            "crew_id": self.crew_id,
            "station": self.station,
            "available_from": fmt_utc(self.available_from) if self.available_from else None,
            "source": self.source,
            "duty": self.duty.label() if self.duty else None,
        }


def crew_position(store: Datastore, crew_id: str, at: datetime) -> Position:
    """Where the roster puts a crew member at `at`, and from when they are free."""
    duties = store.pairings.duties_for_crew(crew_id)
    live = [d for d in duties if d.report_utc <= at < d.release_utc]
    if live:
        d = live[-1]
        return Position(crew_id, d.arr_station, d.release_utc, "in duty", d)
    before = [d for d in duties if d.release_utc <= at]
    if before:
        d = before[-1]
        return Position(crew_id, d.arr_station, d.release_utc, "released", d)
    return Position(crew_id, store.crew.get(crew_id).base, None, "base", None)


# ---------------------------------------------------------------- itineraries


@dataclass(frozen=True, slots=True)
class Itinerary:
    legs: tuple[Flight, ...]

    @property
    def departs(self) -> datetime:
        return self.legs[0].dep_utc

    @property
    def arrives(self) -> datetime:
        return self.legs[-1].arr_utc

    def to_dict(self) -> dict[str, Any]:
        return {
            "legs": [
                {
                    "flight_no": f.flight_no,
                    "flight_id": f.flight_id,
                    "from": f.dep_station,
                    "to": f.arr_station,
                    "dep_utc": fmt_utc(f.dep_utc),
                    "arr_utc": fmt_utc(f.arr_utc),
                }
                for f in self.legs
            ],
            "departs_utc": fmt_utc(self.departs),
            "arrives_utc": fmt_utc(self.arrives),
        }


def find_itineraries(
    store: Datastore,
    origin: str,
    destination: str,
    *,
    not_before: datetime,
    arrive_by: datetime,
) -> list[Itinerary]:
    """Every direct or one-stop itinerary on our network from `origin` to `destination`
    departing at or after `not_before` and landing at or before `arrive_by`."""
    if origin == destination:
        return []
    earliest = max(not_before, arrive_by - MAX_LOOKBACK)
    window = dict(dep_from=earliest, dep_to=arrive_by)
    out: list[Itinerary] = []
    for f in store.flights.list(dep_station=origin, arr_station=destination, **window):
        if f.arr_utc <= arrive_by:
            out.append(Itinerary((f,)))
    for first in store.flights.list(dep_station=origin, **window):
        if first.arr_station == destination:
            continue
        for second in store.flights.list(
            dep_station=first.arr_station,
            arr_station=destination,
            dep_from=first.arr_utc + MIN_CONNECTION,
            dep_to=arrive_by,
        ):
            if second.arr_utc <= arrive_by:
                out.append(Itinerary((first, second)))
    out.sort(key=lambda it: (it.arrives, len(it.legs)))
    return out


# ---------------------------------------------------------------- options


@dataclass(frozen=True, slots=True)
class PositioningOption:
    crew_id: str
    name: str
    rank_title: str
    base: str
    position: Position
    kind: str  # present | extension | positioning
    itinerary: Itinerary | None
    effective_report_utc: datetime
    on_time: bool
    hotel: bool
    legal: bool
    evidence: LegalityEvidence
    cost_breakdown: dict[str, float] = field(default_factory=dict)
    note: str = ""

    @property
    def cost_inr(self) -> float:
        return round(sum(self.cost_breakdown.values()), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "crew_id": self.crew_id,
            "name": self.name,
            "rank": self.rank_title,
            "base": self.base,
            "located_at": self.position.to_dict(),
            "kind": self.kind,
            "itinerary": self.itinerary.to_dict() if self.itinerary else None,
            "effective_report_utc": fmt_utc(self.effective_report_utc),
            "on_time": self.on_time,
            "hotel_overnight": self.hotel,
            "legal": self.legal,
            "rules_checked": list(self.evidence.rules_checked),
            "issues": list(self.evidence.issues),
            "cost_inr": self.cost_inr,
            "cost_breakdown": dict(self.cost_breakdown),
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class PositioningResult:
    pairing_id: str
    role: str
    from_date: date
    station: str
    scheduled_report_utc: datetime
    first_departure_utc: datetime
    options: tuple[PositioningOption, ...]
    excluded: tuple[dict[str, Any], ...]
    considered: int

    def to_dict(self) -> dict[str, Any]:
        on_time = [o for o in self.options if o.on_time]
        return {
            "pairing_id": self.pairing_id,
            "role": self.role,
            "from_date": self.from_date.isoformat(),
            "station": self.station,
            "scheduled_report_utc": fmt_utc(self.scheduled_report_utc),
            "first_departure_utc": fmt_utc(self.first_departure_utc),
            "constraint": (
                "arrival + 15 min before the first departure; on-time options (before the "
                "scheduled report) rank first, then late-report options that still avoid a "
                "delay — the controller decides"
            ),
            "candidates_considered": self.considered,
            "options": [{"rank": i + 1, **o.to_dict()} for i, o in enumerate(self.options)],
            "on_time_count": len(on_time),
            "excluded": list(self.excluded),
            "note": (
                "positions come from the roster (end station of the last released duty, or "
                "the duty in progress), base only when nothing is rostered; positioning legs "
                "are not flying duty and do not shorten rest"
            ),
        }


def positioning_cover(
    store: Datastore,
    pairing_id: str,
    role: str,
    *,
    from_date: date | None = None,
    exclude_crew: tuple[str, ...] = (),
    max_options: int | None = None,
) -> PositioningResult:
    pairing = store.pairings.get(pairing_id.upper())
    duties = store.pairings.duty_periods(pairing, from_date=from_date)
    if not duties:
        raise SimulationError(f"{pairing_id} has no duty days on or after {from_date}")
    if role not in {m.role for m in pairing.crew}:
        raise SimulationError(f"{pairing_id} has no {role} slot")
    first = duties[0]
    first_flight = store.flights.get(first.flight_ids[0])
    departure = first_flight.dep_utc
    station = first.dep_station
    slot_holders = {m.crew_id for m in pairing.crew if m.role == role}
    excluded_ids = set(exclude_crew) | slot_holders

    options: list[PositioningOption] = []
    excluded: list[dict[str, Any]] = []
    considered = 0
    for crew in store.crew.list(rank=role, status="active"):
        if crew.crew_id in excluded_ids:
            continue
        considered += 1
        if first.aircraft_type not in crew.ratings:
            excluded.append(
                {
                    "crew_id": crew.crew_id,
                    "reason": f"RULE-QUAL-05: no {first.aircraft_type} rating",
                }
            )
            continue
        pos = crew_position(store, crew.crew_id, first.report_utc)
        option = _assess(store, crew, pos, pairing.pairing_id, duties, first, departure)
        if isinstance(option, PositioningOption):
            options.append(option)
        else:
            excluded.append({"crew_id": crew.crew_id, "located_at": pos.station, "reason": option})

    options.sort(
        key=lambda o: (
            not o.legal,
            not o.on_time,
            o.cost_inr,
            o.effective_report_utc,
            o.crew_id,
        )
    )
    legal = [o for o in options if o.legal]
    for o in options:
        if not o.legal:
            excluded.append(
                {
                    "crew_id": o.crew_id,
                    "located_at": o.position.station,
                    "reason": "; ".join(o.evidence.issues) or "not legal",
                }
            )
    if max_options is not None:
        legal = legal[:max_options]
    return PositioningResult(
        pairing_id=pairing.pairing_id,
        role=role,
        from_date=first.date,
        station=station,
        scheduled_report_utc=first.report_utc,
        first_departure_utc=departure,
        options=tuple(legal),
        excluded=tuple(sorted(excluded, key=lambda e: e["crew_id"])),
        considered=considered,
    )


def _assess(
    store: Datastore,
    crew: Crew,
    pos: Position,
    pairing_id: str,
    duties: list[DutyPeriod],
    first: DutyPeriod,
    departure: datetime,
) -> PositioningOption | str:
    ctx = CrewContext.load(store, crew.crew_id)
    reserve = store.reserves.get(crew.crew_id)
    kind_of_callout = "reserve_callout" if reserve else "dayoff_callout"
    callout = callout_cost(store.costs, crew.rank, kind_of_callout)
    latest_arrival = departure - ARRIVAL_BUFFER

    def window_blocks(at: datetime) -> str | None:
        """A reserve can only be called out inside their on-call window."""
        if reserve is None or reserve.covers(at):
            return None
        return (
            f"reserve on-call window {reserve.oncall_start:%H:%M}-{reserve.oncall_end:%H:%M}Z "
            f"does not cover the callout at {at:%Y-%m-%dT%H:%M}Z"
        )

    # -- already at the station ---------------------------------------------------------
    if pos.station == first.dep_station:
        free_from = pos.available_from or first.report_utc
        if free_from > latest_arrival:
            return (
                f"at {pos.station} but not free until {free_from:%Y-%m-%dT%H:%M}Z, "
                "after the departure"
            )
        if blocked := window_blocks(max(first.report_utc, free_from)):
            return blocked
        evidence = evaluate_duties(ctx, store.ruleset, duties, callout=True)
        where = f"already at {first.dep_station}" + (
            f" ({pos.source} {pos.duty.label()})" if pos.duty else " (base)"
        )
        if evidence.legal or pos.duty is None:
            return PositioningOption(
                crew.crew_id,
                crew.name,
                crew.rank,
                crew.base,
                pos,
                "present",
                None,
                max(first.report_utc, free_from),
                free_from <= first.report_utc,
                False,
                evidence.legal,
                evidence,
                {"callout": callout},
                note=where,
            )
        # not legal as a fresh duty (typically RULE-REST-04 after landing here): try
        # continuing the duty they are on — the covered legs join the same FDP, no rest
        merged = _merge(pos.duty, first)
        extension = evaluate_duties(
            ctx,
            store.ruleset,
            [merged, *duties[1:]],
            replacing=[(pos.duty.pairing_id, pos.duty.date)] if pos.duty.pairing_id else (),
            callout=False,
        )
        chosen = extension if extension.legal else evidence
        return PositioningOption(
            crew.crew_id,
            crew.name,
            crew.rank,
            crew.base,
            pos,
            "extension" if extension.legal else "present",
            None,
            max(first.report_utc, free_from),
            free_from <= first.report_utc,
            False,
            chosen.legal,
            chosen,
            {"callout": callout},
            note=(
                f"lands at {first.dep_station} on {pos.duty.label()} at "
                f"{free_from:%H:%M}Z — continues on the same duty, {merged.sectors} sectors "
                f"in one FDP"
                if extension.legal
                else where
            ),
        )

    # -- elsewhere: fly them in ---------------------------------------------------------
    not_before = (pos.available_from or (first.report_utc - MAX_LOOKBACK)) + MIN_CONNECTION
    itineraries = find_itineraries(
        store, pos.station, first.dep_station, not_before=not_before, arrive_by=latest_arrival
    )
    if not itineraries:
        return (
            f"at {pos.station} ({pos.source}); no flight on our network reaches "
            f"{first.dep_station} before {latest_arrival:%Y-%m-%dT%H:%M}Z"
        )
    on_time = [it for it in itineraries if it.arrives + ARRIVAL_BUFFER <= first.report_utc]
    chosen = (
        max(on_time, key=lambda it: it.arrives)
        if on_time
        else min(itineraries, key=lambda it: it.arrives)
    )
    if blocked := window_blocks(chosen.departs):  # the callout happens when they must leave
        return blocked
    arrival_report = chosen.arrives + ARRIVAL_BUFFER
    effective_report = first.report_utc if on_time else arrival_report
    hotel = chosen.arrives.date() < first.date
    evidence = evaluate_duties(ctx, store.ruleset, duties, callout=True)
    breakdown = {
        "callout": callout,
        "positioning": store.costs.deadhead_positioning * len(chosen.legs),
    }
    if hotel:
        breakdown["hotel"] = store.costs.hotel_overnight
    legs = " → ".join(f"{f.flight_no} {f.dep_station}-{f.arr_station}" for f in chosen.legs)
    return PositioningOption(
        crew.crew_id,
        crew.name,
        crew.rank,
        crew.base,
        pos,
        "positioning",
        chosen,
        effective_report,
        bool(on_time),
        hotel,
        evidence.legal,
        evidence,
        breakdown,
        note=(
            f"from {pos.station} ({pos.source}) via {legs}, lands {chosen.arrives:%Y-%m-%dT%H:%M}Z"
            + (
                " — on time"
                if on_time
                else f" — reports late ({arrival_report:%H:%M}Z) but the departure is not delayed"
            )
            + (" · hotel overnight" if hotel else "")
        ),
    )


def _merge(current: DutyPeriod, covered: DutyPeriod) -> DutyPeriod:
    """The crew member's duty in progress plus the covered duty as one flight duty period."""
    return replace(
        covered,
        report_utc=current.report_utc,
        flight_ids=tuple(current.flight_ids) + tuple(covered.flight_ids),
        flight_hours=round(current.flight_hours + covered.flight_hours, 2),
        pairing_id=f"{current.label()}+{covered.label()}",
    )


__all__ = [
    "Itinerary",
    "Position",
    "PositioningOption",
    "PositioningResult",
    "crew_position",
    "find_itineraries",
    "positioning_cover",
]
