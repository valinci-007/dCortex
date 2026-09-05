"""Typed domain entities mirroring the dataset, plus the derived DutyPeriod.

All datetimes are aware UTC; all dates are calendar (UTC) dates. Entities are
frozen dataclasses so the rules engine can treat them as values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from crew_ops_advisor.domain.timeutil import hours_between


@dataclass(frozen=True, slots=True)
class Crew:
    crew_id: str
    name: str
    rank: str
    base: str
    ratings: tuple[str, ...]
    seniority: int
    reachability_minutes: int
    status: str  # active | leave | training

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_pilot(self) -> bool:
        return self.rank in ("Captain", "First Officer")


@dataclass(frozen=True, slots=True)
class Flight:
    flight_id: str
    flight_no: str
    date: date
    dep_station: str
    arr_station: str
    dep_utc: datetime
    arr_utc: datetime
    block_hours: float
    aircraft: str
    aircraft_type: str
    seats: int


@dataclass(frozen=True, slots=True)
class PairingDay:
    date: date
    flight_ids: tuple[str, ...]
    report_utc: datetime
    release_utc: datetime


@dataclass(frozen=True, slots=True)
class PairingCrew:
    crew_id: str
    role: str


@dataclass(frozen=True, slots=True)
class Pairing:
    pairing_id: str
    aircraft: str
    days: tuple[PairingDay, ...]
    crew: tuple[PairingCrew, ...]

    @property
    def dates(self) -> tuple[date, ...]:
        return tuple(d.date for d in self.days)

    @property
    def crew_ids(self) -> tuple[str, ...]:
        return tuple(m.crew_id for m in self.crew)

    def role_of(self, crew_id: str) -> str | None:
        for member in self.crew:
            if member.crew_id == crew_id:
                return member.role
        return None


@dataclass(frozen=True, slots=True)
class DailyDuty:
    date: date
    duty_hours: float
    flight_hours: float


@dataclass(frozen=True, slots=True)
class DutyClock:
    crew_id: str
    as_of_utc: datetime
    duty_hours_7d: float
    flight_hours_28d: float
    last_rest_ended: datetime  # earliest legal next report as of the snapshot
    daily_history: tuple[DailyDuty, ...]

    def history_by_date(self) -> dict[date, DailyDuty]:
        return {d.date: d for d in self.daily_history}


@dataclass(frozen=True, slots=True)
class ReserveEntry:
    crew_id: str
    base: str
    dates: tuple[date, ...]
    oncall_start: time
    oncall_end: time
    note: str = ""

    @property
    def overnight(self) -> bool:
        """An on-call window that wraps past midnight (22:00–06:00)."""
        return self.oncall_end < self.oncall_start

    def covers(self, at: datetime) -> bool:
        """True when `at` falls inside the on-call window on a reserve date. A window that
        wraps past midnight belongs to the date it starts on: 22:00–06:00 on the 15th covers
        23:30 on the 15th and 05:00 on the 16th."""
        t = at.timetz()
        if not self.overnight:
            return at.date() in self.dates and self.oncall_start <= t <= self.oncall_end
        if t >= self.oncall_start:
            return at.date() in self.dates
        if t <= self.oncall_end:
            return (at.date() - timedelta(days=1)) in self.dates
        return False


@dataclass(frozen=True, slots=True)
class Certification:
    crew_id: str
    cert_type: str
    valid_from: date
    valid_to: date

    def valid_on(self, on: date) -> bool:
        return self.valid_from <= on <= self.valid_to


@dataclass(frozen=True, slots=True)
class RiskSignal:
    crew_id: str
    as_of_utc: datetime
    disruption_risk_score: float
    drivers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CostConfig:
    currency: str
    reserve_callout_pilot: float
    reserve_callout_cabin: float
    dayoff_callout_pilot: float
    dayoff_callout_cabin: float
    deadhead_positioning: float
    delay_cost_per_duty_hour: float
    cancellation_per_flight: float
    hotel_overnight: float
    notes: str = ""


@dataclass(frozen=True, slots=True)
class FlaggedException:
    crew_id: str
    date: date
    rule: str
    note: str


@dataclass(frozen=True, slots=True)
class RuleDef:
    rule_id: str
    text: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Ruleset:
    time_convention: str
    definitions: dict[str, str]
    rules: dict[str, RuleDef]

    def __getitem__(self, rule_id: str) -> RuleDef:
        return self.rules[rule_id]

    def param(self, rule_id: str, name: str) -> Any:
        return self.rules[rule_id].params[name]


@dataclass(frozen=True, slots=True)
class DutyPeriod:
    """One duty day as the rules see it: report -> release, with its legs.

    Derived from a PairingDay plus its flights; also constructed directly by
    simulations (delays, substitutions) without a pairing.
    """

    date: date
    report_utc: datetime
    release_utc: datetime
    flight_ids: tuple[str, ...]
    flight_hours: float
    aircraft_type: str
    aircraft: str
    dep_station: str
    arr_station: str
    pairing_id: str | None = None

    @property
    def sectors(self) -> int:
        return len(self.flight_ids)

    @property
    def duty_hours(self) -> float:
        return hours_between(self.report_utc, self.release_utc)

    def label(self) -> str:
        return self.pairing_id or "/".join(self.flight_ids)
