"""Disclosure guard: answers never expose how the Advisor is built.

Three layers, applied to every answer whatever produced it:
  1. `humanise_sources` rewrites internal identifiers (tool names, dataset file names,
     "tool result") into the controller's vocabulary ("the reserve roster", "data result").
  2. `find_disclosures` detects vendor / model / SDK / framework terms and prompt-related
     phrases; the orchestrator asks the model for one rewrite when it finds any.
  3. `redact` is the last resort if a rewrite still leaks.

The trace (tool names, arguments, results) is the audit view and is left untouched; the UI
shows it under "reasoning trail", which a production deployment would restrict to
supervisors and auditors.
"""

from __future__ import annotations

import re

TOOL_SOURCES: dict[str, str] = {
    "get_snapshot": "the operational snapshot",
    "get_crew": "the crew roster",
    "list_crew": "the crew roster",
    "get_duty_clock": "the duty clock",
    "get_flight": "the flight schedule",
    "list_flights": "the flight schedule",
    "list_routes": "the route network",
    "schedule_stats": "the flight schedule",
    "get_pairing": "the pairing roster",
    "find_pairings": "the pairing roster",
    "list_reserves": "the reserve roster",
    "get_certifications": "the certification records",
    "list_expiring_certifications": "the certification records",
    "get_risk_signal": "the disruption-risk signals",
    "list_risk_signals": "the disruption-risk signals",
    "get_rules": "the rulebook",
    "get_costs": "the cost table",
    "simulate_crew_removal": "the sick-call impact assessment",
    "check_assignment_legality": "the legality check",
    "check_rostered_legality": "the legality check",
    "station_closure_impact": "the station-closure assessment",
    "simulate_delay": "the delay assessment",
    "cancellation_impact": "the cancellation assessment",
    "crew_near_limits": "the duty-limit watchlist",
    "reserve_coverage": "the reserve coverage check",
    "earliest_next_report": "the rest calculation",
    "seats_at_risk": "the flight schedule",
    "recommend_cover": "the cover-option ranking",
    "rank_cover_options": "the cover-option ranking",
    "joint_cover_plan": "the joint cover plan",
    "resolve_delay_options": "the delay-recovery options",
    "draft_callout_notification": "the callout draft",
    "morning_briefing": "the morning briefing",
    "watchlist": "the watchlist",
    "positioning_options": "the positioning options",
}

FILE_SOURCES: dict[str, str] = {
    "flights.json": "the flight schedule",
    "crew.json": "the crew roster",
    "rosters.json": "the pairing roster",
    "duty_clocks.json": "the duty clocks",
    "reserve_pool.json": "the reserve roster",
    "certifications.json": "the certification records",
    "rules.json": "the rulebook",
    "costs.json": "the cost table",
    "risk_signals.json": "the disruption-risk signals",
    "scenarios.json": "the scenario library",
    "questions.json": "the question set",
}

_TOOL_RE = re.compile(
    r"`?\b(" + "|".join(sorted(TOOL_SOURCES, key=len, reverse=True)) + r")\b`?(\([^)]*\))?"
)
_FILE_RE = re.compile(r"`?\b(" + "|".join(re.escape(f) for f in FILE_SOURCES) + r")\b`?")
_JARGON = (
    (re.compile(r"\btool result(s?)\b", re.I), r"data result\1"),
    (re.compile(r"\btool call(s?)\b", re.I), r"lookup\1"),
    (re.compile(r"\btool(?:s)? (?:returned|output)\b", re.I), "data returned"),
)

# Anything that names the machinery. Word-bounded and case-insensitive.
VENDOR_RE = re.compile(
    r"\b(anthropic|claude(?: code| agent)?|openai|gpt-?\d*|gemini|llama|mistral|"
    r"agent sdk|client sdk|sdk|mcp(?: server)?|langchain|llamaindex|fastapi|sqlite|python|react|"
    r"system prompt|my (?:instructions|prompt)|large language model|llm)\b",
    re.I,
)


def humanise_sources(text: str) -> str:
    """Replace internal identifiers with the controller's names for the same sources."""

    def tool(m: re.Match) -> str:
        source = TOOL_SOURCES[m.group(1)]
        args = m.group(2)
        if args and args.strip("()").strip():
            return f"{source} ({args.strip('()')})"
        return source

    out = _TOOL_RE.sub(tool, text)
    out = _FILE_RE.sub(lambda m: FILE_SOURCES[m.group(1)], out)
    for pattern, replacement in _JARGON:
        out = pattern.sub(replacement, out)
    return out


def find_disclosures(text: str) -> list[str]:
    """Vendor / model / framework terms still present after humanising."""
    return sorted({m.group(0) for m in VENDOR_RE.finditer(text)}, key=str.lower)


def redact(text: str) -> str:
    return VENDOR_RE.sub("[implementation detail withheld]", text)


IDENTITY_ANSWER = (
    "I'm the Crew Ops Advisor for dCortex Air Crew Control. I answer questions from the "
    "desk's operational data: rosters, pairings and reserves; duty clocks and legality against "
    "the seven rules (RULE-FDP-01 … RULE-BASE-07); the impact of sick calls, delays, station "
    "closures and cancellations; ranked cover options with costs; and callout drafts. Every "
    "figure I give comes from the desk's data, and I say so when I can't answer reliably."
)

IDENTITY_RE = re.compile(
    r"\b(who are you|what are you|who am i (?:talking|speaking) to|what can you do|"
    r"what do you do|your name|introduce yourself|what is this|are you (?:an? )?(?:ai|bot|human)|"
    r"which (?:model|ai|llm)|how (?:are|were) you (?:built|made|trained)|"
    r"what model|system prompt|your (?:instructions|prompt))\b",
    re.I,
)
