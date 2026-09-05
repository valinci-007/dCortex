"""Cost model over costs.json: callouts, deadhead positioning, delay, cancellation."""

from __future__ import annotations

from crew_ops_advisor.domain.models import CostConfig, Crew

PILOT_RANKS = ("Captain", "First Officer")

# Required crew complement per aircraft type (from the dataset's roster rules).
COMPLEMENTS: dict[str, dict[str, int]] = {
    "A320": {"Captain": 1, "First Officer": 1, "Senior Cabin Crew": 1, "Cabin Crew": 3},
    "ATR72": {"Captain": 1, "First Officer": 1, "Senior Cabin Crew": 1, "Cabin Crew": 1},
}


def is_pilot(crew: Crew | str) -> bool:
    rank = crew if isinstance(crew, str) else crew.rank
    return rank in PILOT_RANKS


def callout_cost(costs: CostConfig, rank: str, kind: str) -> float:
    """kind: 'reserve_callout' | 'dayoff_callout'."""
    pilot = is_pilot(rank)
    if kind == "reserve_callout":
        return costs.reserve_callout_pilot if pilot else costs.reserve_callout_cabin
    if kind == "dayoff_callout":
        return costs.dayoff_callout_pilot if pilot else costs.dayoff_callout_cabin
    return 0.0


def deadhead_costs(costs: CostConfig, delay_hours: float) -> tuple[float, float]:
    """(positioning cost, delay cost) for a deadhead that delays the duty by delay_hours."""
    return costs.deadhead_positioning, round(costs.delay_cost_per_duty_hour * delay_hours, 2)


def cancellation_cost(costs: CostConfig, legs: int) -> float:
    return costs.cancellation_per_flight * legs


def reserve_set_cost(costs: CostConfig, aircraft_type: str) -> float:
    """Cost of calling out a full reserve complement for one aircraft type."""
    comp = COMPLEMENTS[aircraft_type]
    pilots = comp["Captain"] + comp["First Officer"]
    cabin = comp["Senior Cabin Crew"] + comp["Cabin Crew"]
    return pilots * costs.reserve_callout_pilot + cabin * costs.reserve_callout_cabin
