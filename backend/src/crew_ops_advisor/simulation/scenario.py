"""Scenario workspace (ADR-0018 §3): chained disruptions and "make the call".

A `Scenario` is the desk's working situation for one conversation: crew declared
unavailable from a date, and covers applied (who now flies which pairing role from which
day). `ScenarioStore` presents the roster *as it now stands* to every tool through the
same Datastore surface, so a question asked after a sick call and an applied callout is
answered against the updated roster — with the rules engine seeing the cover's new duties.

Semantics, deliberately simple:
  - Declaring a crew member unavailable does not delete anything: their status reads
    "unavailable" (so they are never proposed as a candidate) and every pairing day they
    held from that date is a *vacancy* until a cover is applied.
  - A cover replaces one named member in one pairing from a date; earlier days stay with
    the original member. `Pairing.crew` reads as the roster after all edits; per-day
    membership is exact through `duties_for_crew`.
  - A reserve who has been called out no longer appears on the reserve list for the days
    they now fly.
  - Nothing else changes: flights, clocks, certificates, costs and rules are untouched. With
    an empty scenario every call is a pass-through — the property the tests pin.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.domain.models import Crew, DutyPeriod, Pairing, PairingCrew, ReserveEntry

UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class Unavailability:
    crew_id: str
    from_date: date
    reason: str = "unavailable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "crew_id": self.crew_id,
            "from_date": self.from_date.isoformat(),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class Cover:
    pairing_id: str
    from_date: date
    role: str
    crew_id: str  # who now flies it
    replaces: str  # whose slot it is
    kind: str = "cover"
    cost_inr: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pairing_id": self.pairing_id,
            "from_date": self.from_date.isoformat(),
            "role": self.role,
            "crew_id": self.crew_id,
            "replaces": self.replaces,
            "kind": self.kind,
            "cost_inr": self.cost_inr,
        }


@dataclass
class Scenario:
    unavailable: dict[str, Unavailability] = field(default_factory=dict)
    covers: list[Cover] = field(default_factory=list)

    # ---- state ------------------------------------------------------------

    @property
    def empty(self) -> bool:
        return not self.unavailable and not self.covers

    def declare_unavailable(self, crew_id: str, from_date: date, reason: str) -> Unavailability:
        entry = Unavailability(crew_id, from_date, reason)
        self.unavailable[crew_id] = entry
        return entry

    def apply_cover(self, cover: Cover) -> None:
        # a newer cover for the same slot from the same date supersedes the older one
        self.covers = [
            c
            for c in self.covers
            if not (
                c.pairing_id == cover.pairing_id
                and c.replaces == cover.replaces
                and c.from_date == cover.from_date
            )
        ]
        self.covers.append(cover)

    def reset(self) -> None:
        self.unavailable.clear()
        self.covers.clear()

    @property
    def committed_cost_inr(self) -> float:
        return round(sum(c.cost_inr for c in self.covers), 2)

    # ---- membership -------------------------------------------------------

    def members_on(self, pairing: Pairing, on: date) -> tuple[PairingCrew, ...]:
        """Who flies `pairing` on `on` after the applied covers."""
        crew = list(pairing.crew)
        for cover in self.covers:
            if cover.pairing_id != pairing.pairing_id or on < cover.from_date:
                continue
            crew = [
                PairingCrew(cover.crew_id, m.role) if m.crew_id == cover.replaces else m
                for m in crew
            ]
        return tuple(crew)

    def vacancies(self, store: Datastore) -> list[dict[str, Any]]:
        """Pairing days still held by an unavailable crew member — nobody has taken them."""
        out = []
        for entry in self.unavailable.values():
            for pairing in store.pairings.for_crew(entry.crew_id):
                for day in pairing.days:
                    if day.date < entry.from_date:
                        continue
                    members = self.members_on(pairing, day.date)
                    if any(m.crew_id == entry.crew_id for m in members):
                        role = next(m.role for m in members if m.crew_id == entry.crew_id)
                        out.append(
                            {
                                "pairing_id": pairing.pairing_id,
                                "date": day.date.isoformat(),
                                "role": role,
                                "crew_id": entry.crew_id,
                                "flight_ids": list(day.flight_ids),
                                "aircraft": pairing.aircraft,
                            }
                        )
        out.sort(key=lambda v: (v["date"], v["pairing_id"], v["role"]))
        return out

    # ---- serialisation ----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "unavailable": [u.to_dict() for u in self.unavailable.values()],
            "covers": [c.to_dict() for c in self.covers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Scenario:
        scenario = cls()
        for u in (data or {}).get("unavailable", []):
            scenario.unavailable[u["crew_id"]] = Unavailability(
                u["crew_id"], date.fromisoformat(u["from_date"]), u.get("reason", "unavailable")
            )
        for c in (data or {}).get("covers", []):
            scenario.covers.append(
                Cover(
                    c["pairing_id"],
                    date.fromisoformat(c["from_date"]),
                    c["role"],
                    c["crew_id"],
                    c["replaces"],
                    c.get("kind", "cover"),
                    float(c.get("cost_inr", 0.0)),
                )
            )
        return scenario

    def summary(self) -> list[str]:
        """One line per edit, in the controller's words."""
        lines = [
            f"{u.crew_id} unavailable from {u.from_date.isoformat()} ({u.reason})"
            for u in self.unavailable.values()
        ]
        lines += [
            f"{c.crew_id} covers {c.pairing_id} as {c.role} from {c.from_date.isoformat()} "
            f"for {c.replaces}" + (f" (₹{c.cost_inr:,.0f})" if c.cost_inr else "")
            for c in self.covers
        ]
        return lines


# ---------------------------------------------------------------- overlay store


class ScenarioStore:
    """The Datastore as the tools see it under a scenario. Everything not listed here is
    delegated untouched; `base` is the raw store."""

    def __init__(self, base: Datastore, scenario: Scenario):
        self.base = base
        self.scenario = scenario
        self.crew = _CrewView(base.crew, scenario)
        self.pairings = _PairingView(base.pairings, scenario)
        self.reserves = _ReserveView(base.reserves, base.pairings, scenario)

    def __getattr__(self, name: str) -> Any:  # flights, duty_clocks, certifications, risk, …
        return getattr(self.base, name)


class _CrewView:
    def __init__(self, inner, scenario: Scenario):
        self._inner = inner
        self._scenario = scenario

    def _mark(self, crew: Crew) -> Crew:
        if crew.crew_id in self._scenario.unavailable:
            return dataclasses.replace(crew, status=UNAVAILABLE)
        return crew

    def get(self, crew_id: str) -> Crew:
        return self._mark(self._inner.get(crew_id))

    def exists(self, crew_id: str) -> bool:
        return self._inner.exists(crew_id)

    def search_name(self, fragment: str) -> list[Crew]:
        return [self._mark(c) for c in self._inner.search_name(fragment)]

    def list(self, *, base=None, rank=None, status=None, rating=None) -> list[Crew]:
        rows = [self._mark(c) for c in self._inner.list(base=base, rank=rank, rating=rating)]
        return [c for c in rows if status is None or c.status == status]


class _PairingView:
    def __init__(self, inner, scenario: Scenario):
        self._inner = inner
        self._scenario = scenario

    def _apply(self, pairing: Pairing) -> Pairing:
        if not self._scenario.covers:
            return pairing
        return dataclasses.replace(
            pairing, crew=self._scenario.members_on(pairing, pairing.days[-1].date)
        )

    def get(self, pairing_id: str) -> Pairing:
        return self._apply(self._inner.get(pairing_id))

    def list(self) -> list[Pairing]:
        return [self._apply(p) for p in self._inner.list()]

    def for_flight(self, flight_id: str) -> Pairing | None:
        p = self._inner.for_flight(flight_id)
        return self._apply(p) if p is not None else None

    def for_aircraft_on(self, aircraft: str, on: date) -> Pairing | None:
        p = self._inner.for_aircraft_on(aircraft, on)
        return self._apply(p) if p is not None else None

    def flagged_exceptions(self):
        return self._inner.flagged_exceptions()

    def duty_period(self, pairing: Pairing, day) -> DutyPeriod:
        return self._inner.duty_period(pairing, day)

    def duty_periods(self, pairing: Pairing, *, from_date: date | None = None) -> list[DutyPeriod]:
        return self._inner.duty_periods(pairing, from_date=from_date)

    def _flies(self, crew_id: str, pairing: Pairing, on: date) -> bool:
        return any(m.crew_id == crew_id for m in self._scenario.members_on(pairing, on))

    def for_crew(self, crew_id: str) -> list[Pairing]:
        if not self._scenario.covers:
            return self._inner.for_crew(crew_id)
        return [
            self._apply(p)
            for p in self._inner.list()
            if any(self._flies(crew_id, p, d.date) for d in p.days)
        ]

    def duties_for_crew(self, crew_id: str) -> list[DutyPeriod]:
        if not self._scenario.covers:
            return self._inner.duties_for_crew(crew_id)
        duties = [
            self._inner.duty_period(p, d)
            for p in self._inner.list()
            for d in p.days
            if self._flies(crew_id, p, d.date)
        ]
        duties.sort(key=lambda d: d.report_utc)
        return duties


class _ReserveView:
    def __init__(self, inner, pairings, scenario: Scenario):
        self._inner = inner
        self._pairings = pairings
        self._scenario = scenario

    def _called_out_on(self, crew_id: str, on: date) -> bool:
        for cover in self._scenario.covers:
            if cover.crew_id != crew_id or on < cover.from_date:
                continue
            pairing = self._pairings.get(cover.pairing_id)
            if any(d.date == on for d in pairing.days):
                return True
        return False

    def get(self, crew_id: str) -> ReserveEntry | None:
        return self._inner.get(crew_id)

    def list(self, *, base: str | None = None, on: date | None = None) -> list[ReserveEntry]:
        rows = self._inner.list(base=base, on=on)
        if on is None or not self._scenario.covers:
            return rows
        return [r for r in rows if not self._called_out_on(r.crew_id, on)]
