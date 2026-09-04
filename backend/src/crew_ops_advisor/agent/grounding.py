"""Grounding check: every identifier, date and figure in an answer must come from evidence.

Evidence is the JSON of every tool result in the trace, plus the question itself
(a controller may quote a threshold) and the fixed constants of the rulebook.
The check is deliberately conservative about what it flags — counts and small
integers are allowed because the prompt lets the model count rows — so a
warning means "this figure did not come from a tool", which is exactly the
failure the brief calls worse than no answer.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

ID_RE = re.compile(r"\b(?:RULE-[A-Z]+-\d{2}|[CP]-\d{4}|DX\d{3}|VT-[A-Z]{3})\b")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?Z?)?")
NUMBER_RE = re.compile(r"(?<![\w.-])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+)(?![\w.]*\d)")
DURATION_RE = re.compile(r"\b\d+h\d{2}m\b")

# Small integers are counts/sectors/ordinals the model may legitimately derive by counting.
COUNT_CEILING = 100


@dataclass(frozen=True, slots=True)
class GroundingResult:
    checked: int
    unsupported: tuple[str, ...]
    ok: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "ok", not self.unsupported)

    def to_dict(self) -> dict[str, Any]:
        return {"checked": self.checked, "unsupported": list(self.unsupported), "ok": self.ok}


def evidence_corpus(
    question: str, tool_results: Iterable[dict[str, Any] | None], constants: Iterable[str] = ()
) -> str:
    parts = [question]
    for r in tool_results:
        if r:
            parts.append(json.dumps(r, default=str))
    parts.extend(constants)
    return _normalise("\n".join(parts))


def _normalise(text: str) -> str:
    return re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)


def _number_in(corpus: str, token: str) -> bool:
    """Numeric equality regardless of formatting: 50.00 == 50.0 == 50, 41,200 == 41200.0."""
    token = token.replace(",", "")
    try:
        value = float(token)
    except ValueError:
        return token in corpus
    if value.is_integer():
        core = rf"{int(value)}(?:\.0+)?"
    else:
        core = re.escape(token.rstrip("0")) + "0*"
    pattern = r"(?<![\d.])(?<!\d-)(?:" + core + r")(?!\d)(?!-\d)(?!\.\d)"
    return re.search(pattern, corpus) is not None


def check_grounding(answer_text: str, corpus: str) -> GroundingResult:
    """Facts in the answer that are not in the evidence corpus."""
    body = _normalise(answer_text)
    unsupported: list[str] = []
    checked = 0

    for m in ID_RE.finditer(body):
        checked += 1
        if m.group().upper() not in corpus.upper():
            unsupported.append(m.group())

    for m in DATE_RE.finditer(body):
        checked += 1
        if m.group() not in corpus:
            unsupported.append(m.group())

    for m in DURATION_RE.finditer(body):
        checked += 1
        if m.group() not in corpus:
            unsupported.append(m.group())

    # numbers: skip anything already inside an id/date/duration/time, and small counts
    scrubbed = ID_RE.sub(" ", body)
    scrubbed = DATE_RE.sub(" ", scrubbed)
    scrubbed = DURATION_RE.sub(" ", scrubbed)
    scrubbed = re.sub(r"\b\d{1,2}:\d{2}\b", " ", scrubbed)
    for m in NUMBER_RE.finditer(scrubbed):
        token = m.group().replace(",", "")
        try:
            value = float(token)
        except ValueError:
            continue
        if "." not in token and value < COUNT_CEILING:
            continue
        checked += 1
        if not _number_in(corpus, token):
            unsupported.append(m.group())

    return GroundingResult(checked=checked, unsupported=tuple(dict.fromkeys(unsupported)))


def rulebook_constants(ruleset) -> list[str]:
    """What the model may cite without a tool call: the rule ids and their parameters."""
    out: list[str] = []
    for rule in ruleset.rules.values():
        out.append(rule.rule_id)
        for v in rule.params.values():
            out.append(str(v))
    return out
