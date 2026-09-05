"""Render LegalityEvidence (or its dict form) into short, checkable reasoning lines.

Breaches are always spelled out with their numbers; passing rules are summarised
one line per rule with the tightest margin, so a controller sees both what
failed and how much headroom the rest had.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from crew_ops_advisor.rules import RULE_ORDER, LegalityEvidence, RuleVerdict, VerdictStatus

_MARK = {"pass": "✓", "breach": "✗", "conditional": "~"}


def verdict_line(v: RuleVerdict | Mapping[str, Any]) -> str:
    if isinstance(v, RuleVerdict):
        status, rule_id, detail = v.status.value, v.rule_id, v.detail
    else:
        status, rule_id, detail = v["status"], v["rule_id"], v["detail"]
    detail = detail.removeprefix(f"{rule_id}: ")
    return f"{_MARK[status]} {rule_id}: {detail}"


def explain_evidence(evidence: LegalityEvidence, *, compact: bool = True) -> list[str]:
    """Lines for a human. compact=True folds passing verdicts to one line per rule."""
    return explain_evidence_dict(evidence.to_dict(), compact=compact)


def explain_evidence_dict(ev: Mapping[str, Any], *, compact: bool = True) -> list[str]:
    verdicts = list(ev.get("verdicts", []))
    lines: list[str] = []
    for rule_id in RULE_ORDER:
        mine = [v for v in verdicts if v["rule_id"] == rule_id]
        if not mine:
            continue
        failing = [v for v in mine if v["status"] == VerdictStatus.BREACH.value]
        conditional = [v for v in mine if v["status"] == VerdictStatus.CONDITIONAL.value]
        if failing:
            lines.extend(verdict_line(v) for v in failing)
        elif conditional:
            lines.extend(verdict_line(v) for v in conditional)
        elif not compact or len(mine) == 1:
            lines.extend(verdict_line(v) for v in mine)
        else:
            tightest = min(
                (v for v in mine if v.get("margin") is not None),
                key=lambda v: v["margin"],
                default=mine[0],
            )
            lines.append(verdict_line(tightest) + f" [{len(mine)} checks, tightest shown]")
    return lines


def legality_sentence(ev: Mapping[str, Any], subject: str) -> str:
    """One sentence verdict: 'C-2087 cannot legally cover P-2291: …' or the positive form."""
    if ev.get("legal"):
        cond = ev.get("conditions") or []
        if cond:
            return f"{subject} is legal subject to: " + "; ".join(cond) + "."
        return f"{subject} is legal under all seven rules."
    issues = ev.get("issues") or []
    return f"{subject} is not legal: " + "; ".join(issues) + "."
