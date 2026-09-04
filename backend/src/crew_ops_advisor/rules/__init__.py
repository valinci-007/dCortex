"""Rules layer: the seven legality rules as pure functions, composed by the engine."""

from crew_ops_advisor.rules.engine import (
    CrewContext,
    daily_totals,
    evaluate_duties,
    evaluate_rostered,
)
from crew_ops_advisor.rules.verdicts import RULE_ORDER, LegalityEvidence, RuleVerdict, VerdictStatus

__all__ = [
    "RULE_ORDER",
    "CrewContext",
    "LegalityEvidence",
    "RuleVerdict",
    "VerdictStatus",
    "daily_totals",
    "evaluate_duties",
    "evaluate_rostered",
]
