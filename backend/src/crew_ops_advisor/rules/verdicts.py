"""Verdict types: the structured evidence every rule check produces.

A RuleVerdict is deliberately more than a boolean — it carries the inputs, the
computed value, the limit and the margin so the explanation layer can render
reasoning a controller can check by hand, and so the grounding check can verify
that every number in an answer came from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

RULE_ORDER: tuple[str, ...] = (
    "RULE-FDP-01",
    "RULE-DUTY-02",
    "RULE-FLT-03",
    "RULE-REST-04",
    "RULE-QUAL-05",
    "RULE-CERT-06",
    "RULE-BASE-07",
)


class VerdictStatus(StrEnum):
    PASS = "pass"
    BREACH = "breach"
    CONDITIONAL = "conditional"  # legal only if a stated condition is met (e.g. deadhead)


@dataclass(frozen=True, slots=True)
class RuleVerdict:
    rule_id: str
    status: VerdictStatus
    detail: str
    date: date | None = None
    computed: float | None = None
    limit: float | None = None
    margin: float | None = None  # limit - computed; positive means headroom
    inputs: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status is not VerdictStatus.BREACH

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "status": self.status.value,
            "detail": self.detail,
            "date": self.date.isoformat() if self.date else None,
            "computed": self.computed,
            "limit": self.limit,
            "margin": self.margin,
            "inputs": dict(self.inputs),
        }


@dataclass(frozen=True, slots=True)
class LegalityEvidence:
    """All verdicts for one crew member against one proposed set of duties."""

    crew_id: str
    verdicts: tuple[RuleVerdict, ...]
    duty_dates: tuple[date, ...]

    @property
    def legal(self) -> bool:
        return all(v.passed for v in self.verdicts)

    @property
    def breaches(self) -> tuple[RuleVerdict, ...]:
        return tuple(v for v in self.verdicts if v.status is VerdictStatus.BREACH)

    @property
    def conditions(self) -> tuple[RuleVerdict, ...]:
        return tuple(v for v in self.verdicts if v.status is VerdictStatus.CONDITIONAL)

    @property
    def rules_checked(self) -> tuple[str, ...]:
        seen = {v.rule_id for v in self.verdicts}
        return tuple(r for r in RULE_ORDER if r in seen)

    @property
    def issues(self) -> tuple[str, ...]:
        """Breach details, in rule order then date order — the shape answer keys use."""
        ordered = sorted(
            self.breaches,
            key=lambda v: (RULE_ORDER.index(v.rule_id), v.date or date.min),
        )
        return tuple(v.detail for v in ordered)

    def by_rule(self, rule_id: str) -> tuple[RuleVerdict, ...]:
        return tuple(v for v in self.verdicts if v.rule_id == rule_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "crew_id": self.crew_id,
            "legal": self.legal,
            "duty_dates": [d.isoformat() for d in self.duty_dates],
            "rules_checked": list(self.rules_checked),
            "issues": list(self.issues),
            "conditions": [v.detail for v in self.conditions],
            "verdicts": [v.to_dict() for v in self.verdicts],
        }
