"""Domain model: typed entities and UTC time helpers. No I/O, no LLM."""

from crew_ops_advisor.domain.models import (
    Certification,
    CostConfig,
    Crew,
    DailyDuty,
    DutyClock,
    DutyPeriod,
    FlaggedException,
    Flight,
    Pairing,
    PairingCrew,
    PairingDay,
    ReserveEntry,
    RiskSignal,
    RuleDef,
    Ruleset,
)

__all__ = [
    "Certification",
    "CostConfig",
    "Crew",
    "DailyDuty",
    "DutyClock",
    "DutyPeriod",
    "FlaggedException",
    "Flight",
    "Pairing",
    "PairingCrew",
    "PairingDay",
    "ReserveEntry",
    "RiskSignal",
    "RuleDef",
    "Ruleset",
]
