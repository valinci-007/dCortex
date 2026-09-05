"""Result types for Tier-2 simulations. Plain frozen dataclasses with to_dict() so the
tool layer can hand them to the model unchanged and the offline composer can template them."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from crew_ops_advisor.domain.timeutil import fmt_utc
from crew_ops_advisor.rules import LegalityEvidence


@dataclass(frozen=True, slots=True)
class UncoveredDay:
    date: date
    pairing_id: str
    role: str
    flight_ids: tuple[str, ...]
    passengers: int
    immediate: bool  # first affected day (the rest are "also at risk")
    starts_at: str
    ends_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "pairing_id": self.pairing_id,
            "role": self.role,
            "flights": list(self.flight_ids),
            "flight_numbers": [f.split("-")[0] for f in self.flight_ids],
            "passengers": self.passengers,
            "immediate": self.immediate,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
        }


@dataclass(frozen=True, slots=True)
class CrewRemovalImpact:
    crew_id: str
    crew_name: str
    rank: str
    from_date: date
    days: tuple[UncoveredDay, ...]
    cover_must_take_full_pairing: bool
    note: str = ""

    @property
    def immediate_flights(self) -> tuple[str, ...]:
        return tuple(f for d in self.days if d.immediate for f in d.flight_ids)

    @property
    def at_risk_flights(self) -> tuple[str, ...]:
        return tuple(f for d in self.days if not d.immediate for f in d.flight_ids)

    def to_dict(self) -> dict[str, Any]:
        immediate = [d for d in self.days if d.immediate]
        return {
            "crew_id": self.crew_id,
            "crew_name": self.crew_name,
            "rank": self.rank,
            "from_date": self.from_date.isoformat(),
            "pairings_affected": sorted({d.pairing_id for d in self.days}),
            "uncovered_now": list(self.immediate_flights),
            "also_at_risk": list(self.at_risk_flights),
            "passengers_now": sum(d.passengers for d in immediate),
            "passengers_at_risk_total": sum(d.passengers for d in self.days),
            "cover_must_take_full_pairing": self.cover_must_take_full_pairing,
            "days": [d.to_dict() for d in self.days],
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class FlightAssessment:
    flight_id: str
    flight_no: str
    at_station: str  # "departure" | "arrival"
    scheduled_utc: datetime
    pairing_id: str
    min_delay_hours: float
    duty_hours: float
    sectors: int
    fdp_after_delay: float
    fdp_limit: float
    breach: bool
    seats: int

    @property
    def action(self) -> str:
        if self.breach:
            return "delay exceeds crew FDP — re-crew tail legs from reserves or cancel"
        return "delay (crew legal)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "flight_id": self.flight_id,
            "flight_no": self.flight_no,
            "at_station": self.at_station,
            "scheduled_utc": fmt_utc(self.scheduled_utc),
            "pairing_id": self.pairing_id,
            "min_delay_hours": self.min_delay_hours,
            "crew_fdp_after_delay": self.fdp_after_delay,
            "fdp_limit": self.fdp_limit,
            "breach": self.breach,
            "rule": "RULE-FDP-01",
            "action": self.action,
            "seats": self.seats,
        }


@dataclass(frozen=True, slots=True)
class ClosureImpact:
    station: str
    start_utc: datetime
    end_utc: datetime
    turnaround_minutes: int
    assessments: tuple[FlightAssessment, ...]

    def to_dict(self) -> dict[str, Any]:
        pairings: dict[str, list[str]] = {}
        for a in self.assessments:
            pairings.setdefault(a.pairing_id, []).append(a.flight_no)
        return {
            "station": self.station,
            "window": {"start": fmt_utc(self.start_utc), "end": fmt_utc(self.end_utc)},
            "turnaround_minutes": self.turnaround_minutes,
            "count": len(self.assessments),
            "affected_flights": [a.flight_id for a in self.assessments],
            "affected_flight_numbers": [a.flight_no for a in self.assessments],
            "passengers_affected": sum(a.seats for a in self.assessments),
            "pairings_affected": pairings,
            "fdp_breaches": [a.flight_no for a in self.assessments if a.breach],
            "per_flight": [a.to_dict() for a in self.assessments],
            "note": (
                f"minimum delay = reopen time + {self.turnaround_minutes} min turnaround − "
                "scheduled time at the station; FDP after delay = rostered duty length + that delay"
            ),
        }


@dataclass(frozen=True, slots=True)
class CrewDelayCheck:
    crew_id: str
    role: str
    evidence: LegalityEvidence

    def to_dict(self) -> dict[str, Any]:
        return {"crew_id": self.crew_id, "role": self.role, **self.evidence.to_dict()}


@dataclass(frozen=True, slots=True)
class DelayImpact:
    aircraft: str
    date: date
    pairing_id: str
    delay_hours: float
    first_flight: str
    flights: tuple[str, ...]
    original_report_utc: datetime
    original_release_utc: datetime
    new_release_utc: datetime
    fdp_before: float
    fdp_after: float
    fdp_limit: float
    sectors: int
    crew_checks: tuple[CrewDelayCheck, ...]
    legal_leg_count: int  # how many legs the rostered crew can still legally complete

    @property
    def breach(self) -> bool:
        return self.fdp_after > self.fdp_limit + 1e-6

    def to_dict(self) -> dict[str, Any]:
        return {
            "aircraft": self.aircraft,
            "date": self.date.isoformat(),
            "pairing_id": self.pairing_id,
            "delay_hours": self.delay_hours,
            "first_flight": self.first_flight,
            "flights": list(self.flights),
            "original_report_utc": fmt_utc(self.original_report_utc),
            "original_release_utc": fmt_utc(self.original_release_utc),
            "new_release_utc": fmt_utc(self.new_release_utc),
            "fdp_before": self.fdp_before,
            "fdp_after_delay": self.fdp_after,
            "fdp_limit": self.fdp_limit,
            "sectors": self.sectors,
            "breach": self.breach,
            "rule": "RULE-FDP-01",
            "breach_detail": (
                f"RULE-FDP-01: delayed duty runs {self.fdp_after:.2f}h vs {self.fdp_limit:.1f}h "
                f"limit ({self.sectors} sectors) — the rostered crew cannot legally complete "
                f"{self.flights[-1].split('-')[0]}"
                if self.breach
                else None
            ),
            "legal_leg_count": self.legal_leg_count,
            "legs_needing_recrew": [f.split("-")[0] for f in self.flights[self.legal_leg_count :]]
            if self.breach
            else [],
            "crew_checks": [c.to_dict() for c in self.crew_checks],
        }


@dataclass(frozen=True, slots=True)
class CancellationImpact:
    flight_id: str
    flight_no: str
    date: date
    seats: int
    cost_inr: float
    pairing_id: str | None
    crew_ids: tuple[str, ...]
    route: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "flight_id": self.flight_id,
            "flight_no": self.flight_no,
            "date": self.date.isoformat(),
            "route": self.route,
            "passengers_affected": self.seats,
            "direct_cancellation_cost_inr": self.cost_inr,
            "pairing_id": self.pairing_id,
            "crew_released": list(self.crew_ids),
        }


@dataclass(frozen=True, slots=True)
class NearLimit:
    crew_id: str
    name: str
    rank: str
    duty_hours_7d: float
    duty_headroom: float
    flight_hours_28d: float
    flight_headroom: float
    planned_today: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "crew_id": self.crew_id,
            "name": self.name,
            "rank": self.rank,
            "duty_hours_7d": self.duty_hours_7d,
            "duty_headroom_7d": self.duty_headroom,
            "flight_hours_28d": self.flight_hours_28d,
            "flight_headroom_28d": self.flight_headroom,
            "planned_duty_hours_on_date": self.planned_today,
        }


@dataclass(frozen=True, slots=True)
class ReserveCandidate:
    crew_id: str
    name: str
    rank: str
    base: str
    ratings: tuple[str, ...]
    window: tuple[str, str]
    reachability_minutes: int
    eligible: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "crew_id": self.crew_id,
            "name": self.name,
            "rank": self.rank,
            "base": self.base,
            "ratings": list(self.ratings),
            "oncall_window_utc": {"start": self.window[0], "end": self.window[1]},
            "reachability_minutes": self.reachability_minutes,
            "eligible": self.eligible,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class DeadheadPlan:
    from_station: str
    to_station: str
    flight_id: str
    flight_no: str
    arrives_utc: datetime
    new_report_utc: datetime
    scheduled_report_utc: datetime
    delay_hours: float
    positioning_cost_inr: float
    delay_cost_inr: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_station": self.from_station,
            "to_station": self.to_station,
            "positioning_flight": self.flight_no,
            "positioning_flight_id": self.flight_id,
            "arrives_utc": fmt_utc(self.arrives_utc),
            "new_report_utc": fmt_utc(self.new_report_utc),
            "scheduled_report_utc": fmt_utc(self.scheduled_report_utc),
            "first_departure_delay_hours": self.delay_hours,
            "positioning_cost_inr": self.positioning_cost_inr,
            "delay_cost_inr": self.delay_cost_inr,
        }


@dataclass(frozen=True, slots=True)
class AssignmentCheck:
    crew_id: str
    crew_name: str
    rank: str
    pairing_id: str
    from_date: date
    dates: tuple[date, ...]
    callout_kind: str  # "rostered" | "reserve_callout" | "dayoff_callout"
    evidence: LegalityEvidence
    deadhead: DeadheadPlan | None
    cost_inr: float | None
    cost_breakdown: dict[str, float] = field(default_factory=dict)
    role_matches: bool = True
    role_note: str = ""
    available: bool = True  # reserve on-call window covers the required report time
    availability_note: str = ""

    @property
    def legal(self) -> bool:
        return self.evidence.legal and self.role_matches

    @property
    def feasible(self) -> bool:
        """Legal under the seven rules and actually callable (reserve window covers report)."""
        return self.legal and self.available

    def to_dict(self) -> dict[str, Any]:
        ev = self.evidence.to_dict()
        issues = list(ev["issues"])
        if not self.role_matches and self.role_note:
            issues.insert(0, self.role_note)
        consequence = None
        if self.deadhead:
            consequence = (
                f"Deadhead positioning on {self.deadhead.flight_no} (arr "
                f"{self.deadhead.arrives_utc:%H:%M}Z) delays the first departure by "
                f"~{self.deadhead.delay_hours:g}h; RULE-BASE-07 deadhead cost applies."
            )
        return {
            "crew_id": self.crew_id,
            "crew_name": self.crew_name,
            "rank": self.rank,
            "pairing_id": self.pairing_id,
            "from_date": self.from_date.isoformat(),
            "duty_dates": [d.isoformat() for d in self.dates],
            "callout_kind": self.callout_kind,
            "legal": self.legal,
            "available": self.available,
            "availability_note": self.availability_note,
            "feasible": self.feasible,
            "issues": issues,
            "conditions": ev["conditions"],
            "rules_checked": ev["rules_checked"],
            "verdicts": ev["verdicts"],
            "deadhead": self.deadhead.to_dict() if self.deadhead else None,
            "consequence": consequence,
            "cost_inr": self.cost_inr,
            "cost_breakdown": dict(self.cost_breakdown),
        }
