"""Eval harness: run questions.json through the Advisor and grade against the answer keys.

Grading is deliberately simple and honest: every atomic fact in the expected
answer (ids, codes, numbers, dates, strings) must appear in the answer text.
That is a *recall* check — it cannot catch extra, wrong facts — so reports say
"expected facts recalled", never "correct". Precision is reviewed by reading
the answers, which the report includes.
"""

from __future__ import annotations

import json
import re
import statistics
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from crew_ops_advisor.agent import Advisor, Answer
from crew_ops_advisor.data import Datastore, load_json

FLIGHT_ID_RE = re.compile(r"^(DX\d{3})-\d{4}-\d{2}-\d{2}$")

# Controllers' standard abbreviations count as the same fact.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "first officer": ("fo", "f/o"),
    "senior cabin crew": ("scc", "senior cc"),
    "cabin crew": ("cc",),
    "captain": ("capt", "cpt"),
}
_STOPWORDS = frozenset(
    {"the", "a", "an", "of", "over", "in", "on", "for", "to", "and", "this", "last"}
)

# Structured key strings ("RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)")
# are graded by their facts, in this priority order, not by their template wording.
FACT_RE = re.compile(
    r"RULE-[A-Z]+-\d{2}|[CP]-\d{4}|DX\d{3}|VT-[A-Z]{3}|\d{4}-\d{2}-\d{2}|\d+h\d{2}m|\d{1,2}:\d{2}"
    r"|\d+(?:\.\d+)?"
)
_MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    )
}
_TEXT_DATE_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b"
    r"|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class Question:
    question_id: str
    tier: int
    prompt: str
    expected: Any
    explanation: str = ""
    rules_ref: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Grade:
    passed: bool
    score: float
    found: tuple[str, ...]
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvalRow:
    question: Question
    answer: Answer
    grade: Grade

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question.question_id,
            "tier": self.question.tier,
            "prompt": self.question.prompt,
            "passed": self.grade.passed,
            "score": self.grade.score,
            "missing": list(self.grade.missing),
            "refused": self.answer.refused,
            "error": self.answer.error,
            "elapsed_ms": self.answer.elapsed_ms,
            "llm_calls": self.answer.llm_calls,
            "tool_calls": [s.name for s in self.answer.tool_calls],
            "cost_usd": self.answer.cost_usd,
            "mode": self.answer.mode,
            "answer": self.answer.text,
        }


@dataclass(slots=True)
class EvalReport:
    mode: str
    rows: list[EvalRow] = field(default_factory=list)
    started_utc: str = field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    @property
    def passed(self) -> int:
        return sum(1 for r in self.rows if r.grade.passed)

    @property
    def total(self) -> int:
        return len(self.rows)

    def latency(self) -> dict[str, float]:
        times = sorted(r.answer.elapsed_ms for r in self.rows) or [0.0]
        return {
            "p50_ms": round(statistics.median(times), 1),
            "p95_ms": round(times[min(len(times) - 1, int(round(0.95 * (len(times) - 1))))], 1),
            "max_ms": round(times[-1], 1),
        }

    def cost_usd(self) -> float | None:
        costs = [r.answer.cost_usd for r in self.rows if r.answer.cost_usd is not None]
        return round(sum(costs), 4) if costs else None

    def by_tier(self) -> dict[int, tuple[int, int]]:
        out: dict[int, list[int]] = {}
        for r in self.rows:
            t = out.setdefault(r.question.tier, [0, 0])
            t[0] += r.grade.passed
            t[1] += 1
        return {k: (v[0], v[1]) for k, v in sorted(out.items())}

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "started_utc": self.started_utc,
            "passed": self.passed,
            "total": self.total,
            "by_tier": {str(k): {"passed": p, "total": t} for k, (p, t) in self.by_tier().items()},
            "latency": self.latency(),
            "cost_usd": self.cost_usd(),
            "rows": [r.to_dict() for r in self.rows],
        }

    def summary(self) -> str:
        tiers = " · ".join(f"T{k} {p}/{t}" for k, (p, t) in self.by_tier().items())
        lat = self.latency()
        cost = self.cost_usd()
        return (
            f"{self.mode}: {self.passed}/{self.total} expected facts fully recalled ({tiers}) · "
            f"latency p50 {lat['p50_ms']:.0f} ms, p95 {lat['p95_ms']:.0f} ms"
            + (f" · est. cost ${cost:.2f}" if cost is not None else "")
        )


# ------------------------------------------------------------------ loading


def load_questions(
    store: Datastore, *, tiers: Iterable[int] = (1, 2, 3), ids: Iterable[str] | None = None
) -> list[Question]:
    wanted_tiers = set(tiers)
    wanted_ids = set(ids) if ids else None
    out = []
    for q in load_json(store.data_dir, "questions.json"):
        if q["tier"] not in wanted_tiers:
            continue
        if wanted_ids and q["question_id"] not in wanted_ids:
            continue
        out.append(
            Question(
                question_id=q["question_id"],
                tier=int(q["tier"]),
                prompt=q["prompt"],
                expected=q["expected_answer"],
                explanation=q.get("explanation", ""),
                rules_ref=tuple(q.get("rules_ref", [])),
            )
        )
    return out


# ------------------------------------------------------------------ grading


def atoms(expected: Any) -> list[str]:
    """Leaf values of the expected answer, as strings to look for in the answer text."""
    out: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ("note", "notes", "rank"):  # rubric commentary / ordering, not facts
                    continue
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, bool):
            out.append("true" if v else "false")
        elif isinstance(v, int | float):
            if v == 0:  # "delay_hours: 0.0" is the absence of a fact, not a fact
                return
            out.append(_num(v))
        elif isinstance(v, str):
            m = FLIGHT_ID_RE.match(v)
            out.append(m[1] if m else v)

    walk(expected)
    return list(dict.fromkeys(a for a in out if a))


def _num(v: float) -> str:
    if isinstance(v, int) or float(v).is_integer():
        return str(int(v))
    return f"{v:g}"


def _number_present(text: str, token: str) -> bool:
    """Numbers must match as whole numbers (39.07 must not match inside 139.07 or 39.075)."""
    escaped = re.escape(token)
    variants = [escaped]
    if "." in token:
        variants.append(escaped + "0")  # 23.5 written as 23.50
    else:
        variants.append(escaped + r"\.0+")  # 21 written as 21.0
    # standalone: not glued to other digits, a decimal point, or a date-style hyphen+digit
    pattern = r"(?<![\d.])(?<!\d-)(?:" + "|".join(variants) + r")(?!\d)(?!-\d)(?!\.\d)"
    return re.search(pattern, text) is not None


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


_TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(?::(\d{2}))?Z?$")


def _timestamp_present(text: str, token: str) -> bool:
    """2026-09-17T03:30:00Z and 2026-09-17T03:30Z (how a controller writes it) are one fact."""
    m = _TIMESTAMP_RE.match(token)
    if not m:
        return token.lower() in text.lower()
    minute, seconds = m[1], m[2] or "00"
    forms = {f"{minute}:{seconds}Z", f"{minute}:{seconds}"}
    if seconds == "00":
        forms |= {f"{minute}Z", minute}
    return any(re.search(re.escape(f) + r"(?![\d:])", text) for f in forms)


def _squashed_present(text: str, token: str) -> bool:
    """Enumeration tokens (medical_class1, dangerous_goods) match their spoken form
    ("medical class 1", "dangerous goods")."""
    squash = lambda v: re.sub(r"[^a-z0-9]+", "", v.lower())  # noqa: E731
    return squash(token) in squash(text)


def normalise_text(text: str, *, year: int = 2026) -> str:
    """Answer text as the grader sees it: thousands separators removed (250,000 -> 250000) and
    textual dates ("17 Sep", "Sep 17") echoed in ISO form so date facts can be matched."""
    out = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    extra: list[str] = []
    for m in _TEXT_DATE_RE.finditer(out):
        day, mon = (m[1], m[2]) if m[1] else (m[4], m[3])
        try:
            extra.append(f"{year:04d}-{_MONTHS[mon[:3].lower()]:02d}-{int(day):02d}")
        except (KeyError, ValueError):
            continue
    return out + ("\n" + " ".join(extra) if extra else "")


ACTION_RE = re.compile(r"^Assign\s+(?P<rank>[A-Za-z ]+?)\s+(?P<crew>C-\d{4})\s+\((?P<kind>[^)]*)\)")
_KIND_WORDS = {
    "reserve callout": ("reserve",),
    "day-off callout": ("day-off", "dayoff", "day off"),
}


def _action_present(text: str, token: str) -> bool:
    """'Assign Captain C-3310 (reserve callout)' == the crew id plus the callout kind."""
    m = ACTION_RE.match(token)
    if not m:
        return False
    low = text.lower()
    if m["crew"].lower() not in low:
        return False
    kind = m["kind"].lower()
    for key, aliases in _KIND_WORDS.items():
        if kind.startswith(key):
            return any(a in low for a in aliases)
    if kind.startswith("deadhead") or "deadhead" in kind:
        return "deadhead" in low
    return True


def _rule_present(text: str, rule_id: str) -> bool:
    """RULE-DUTY-02 may be written DUTY-02 once the RULE- prefix is established, and a list of
    all seven rule ids is satisfied by 'all seven rules' / 'all 7 rules'."""
    low = text.lower()
    if rule_id.lower() in low or rule_id.lower().removeprefix("rule-") in low:
        return True
    return bool(re.search(r"\ball (?:seven|7) rules\b", low))


def _word_match(word: str, have: set[str]) -> bool:
    """Inflection-tolerant: 'tail' ~ 'tails', 'cancel' ~ 'cancelled', 'reserves' ~ 'reserve'."""
    if word in have:
        return True
    if len(word) < 4:
        return False
    return any((len(h) >= 4) and (h.startswith(word) or word.startswith(h)) for h in have)


def _is_structured(token: str) -> bool:
    facts = FACT_RE.findall(token)
    return bool(re.match(r"RULE-[A-Z]+-\d{2}", token)) or len(facts) >= 2


def _fact_present(text: str, fact: str) -> bool:
    if re.fullmatch(r"-?\d+(?:\.\d+)?", fact):
        return _number_present(text, fact)
    if re.fullmatch(r"RULE-[A-Z]+-\d{2}", fact):
        return _rule_present(text, fact)
    if re.fullmatch(r"\d{1,2}:\d{2}", fact):
        return fact in text
    if _TIMESTAMP_RE.match(fact):
        return _timestamp_present(text, fact)
    return fact.lower() in text.lower()


def _present(text: str, token: str) -> bool:
    if re.fullmatch(r"-?\d+(?:\.\d+)?", token):
        return _number_present(text, token)
    low_token, low_text = token.lower(), text.lower()
    if low_token in ("true", "false"):
        # legality flags are checked by their words, not by json literals
        return True
    if low_token in low_text:
        return True
    if _TIMESTAMP_RE.match(token):
        return _timestamp_present(text, token)
    if "_" in token and re.fullmatch(r"[a-z0-9_]+", low_token):
        return _squashed_present(text, token)
    if re.fullmatch(r"RULE-[A-Z]+-\d{2}", token):
        return _rule_present(text, token)
    for alias in SYNONYMS.get(low_token, ()):
        if re.search(rf"\b{re.escape(alias)}\b", low_text):
            return True
    if ACTION_RE.match(token):
        return _action_present(text, token)
    # structured key strings: every fact (rule id, crew/pairing/flight id, date, duration,
    # time, number) must appear; the template wording around them need not
    if _is_structured(token):
        facts = list(dict.fromkeys(FACT_RE.findall(token)))
        return all(_fact_present(text, f) for f in facts)
    # multi-word prose (risk drivers, action sentences): content words must appear — all of
    # them for short phrases, at least 70% for long template sentences that get paraphrased
    content = [w for w in _words(token) if w not in _STOPWORDS]
    if len(content) >= 3:
        have = set(_words(text))
        hits = sum(1 for w in content if _word_match(w, have))
        needed = len(content) if len(content) <= 5 else int(0.7 * len(content) + 0.999)
        return hits >= needed
    return False


def grade(answer_text: str, expected: Any) -> Grade:
    wanted = atoms(expected)
    if not wanted:
        return Grade(passed=True, score=1.0, found=(), missing=())
    answer_text = normalise_text(answer_text)
    found = tuple(a for a in wanted if _present(answer_text, a))
    missing = tuple(a for a in wanted if a not in found)
    return Grade(
        passed=not missing, score=round(len(found) / len(wanted), 3), found=found, missing=missing
    )


# ------------------------------------------------------------------ running


def run_evals(
    advisor: Advisor, questions: Sequence[Question], *, fresh_conversation: bool = True
) -> EvalReport:
    report = EvalReport(mode=advisor.provider.name)
    conversation = None if fresh_conversation else advisor.new_conversation()
    for q in questions:
        answer = advisor.ask(q.prompt, conversation)
        report.rows.append(EvalRow(q, answer, grade(answer.text, q.expected)))
    return report


def write_report(
    report: EvalReport, directory: Path, *, stem: str | None = None
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    stem = stem or f"{report.mode}-{time.strftime('%Y%m%d-%H%M%S')}"
    json_path = directory / f"{stem}.json"
    md_path = directory / f"{stem}.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2))
    md_path.write_text(render_markdown(report))
    return json_path, md_path


def render_markdown(report: EvalReport) -> str:
    lat = report.latency()
    lines = [
        f"# Eval report — {report.mode}",
        "",
        f"Run: {report.started_utc} · **{report.passed}/{report.total}** questions with all expected facts recalled · "
        f"latency p50 {lat['p50_ms']:.0f} ms / p95 {lat['p95_ms']:.0f} ms / max {lat['max_ms']:.0f} ms"
        + (f" · est. cost ${report.cost_usd():.2f}" if report.cost_usd() is not None else ""),
        "",
        "Grading is recall of the answer key's atomic facts; extra or wrong facts are not detected automatically — read the answers.",
        "",
        "| Q | Tier | Result | Missing | Tools | ms |",
        "|---|---|---|---|---|---|",
    ]
    for r in report.rows:
        mark = "✅" if r.grade.passed else ("🚫 refused" if r.answer.refused else "❌")
        missing = ", ".join(r.grade.missing)[:80]
        tools = ", ".join(s.name for s in r.answer.tool_calls)
        lines.append(
            f"| {r.question.question_id} | {r.question.tier} | {mark} | {missing} | {tools} | {r.answer.elapsed_ms:.0f} |"
        )
    lines.append("")
    for r in report.rows:
        lines += [
            f"## {r.question.question_id} — {r.question.prompt}",
            "",
            "**Expected:** `" + json.dumps(r.question.expected)[:400] + "`",
            "",
            "**Answer:**",
            "",
            *(f"> {ln}" for ln in r.answer.text.splitlines()),
            "",
        ]
    return "\n".join(lines)
