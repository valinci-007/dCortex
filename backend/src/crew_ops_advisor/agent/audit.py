"""Console audit trail: exactly what leaves this machine for the model, and what the PII
guard changed on the way.

Printed to stderr so a reviewer watching the server console sees, per question:
  - the system prompt and the user message handed to the model provider (the prompt in full
    the first time it is sent, then its fingerprint — it never changes within a run);
  - every tool result BEFORE and AFTER PII minimisation, with a count of what was removed;
  - the model's reply.

CREW_OPS_AUDIT_LOG=0 silences it; CREW_OPS_AUDIT_LOG=full prints every tool result in full
and the system prompt on every question instead of the first 1,500 characters / once.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from typing import Any

LOGGER_NAME = "crew_ops.audit"
SNIPPET = 1500
RULE = "─" * 78

_seen_prompts: set[str] = set()


def setting() -> str:
    return os.environ.get("CREW_OPS_AUDIT_LOG", "1").strip().lower()


def enabled() -> bool:
    return setting() not in ("0", "false", "no", "off")


def full() -> bool:
    return setting() == "full"


def logger() -> logging.Logger:
    log = logging.getLogger(LOGGER_NAME)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
        log.propagate = False
    log.setLevel(logging.INFO if enabled() else logging.CRITICAL)
    return log


def reset() -> None:
    """Forget which prompts were printed (tests)."""
    _seen_prompts.clear()


# ---- events ---------------------------------------------------------------


def model_input(
    provider: str,
    system: str,
    message: str,
    *,
    as_typed: str | None = None,
    pii_mode: str = "full",
    session_id: str | None = None,
) -> None:
    if not enabled():
        return
    log = logger()
    digest = hashlib.sha256(system.encode()).hexdigest()[:12]
    head = f"MODEL INPUT → {provider}"
    if session_id:
        head += f" · resuming session {session_id[:8]}…"
    head += f" · PII mode: {pii_mode}"
    log.info("\n[audit] %s\n[audit] %s", RULE, head)
    if digest not in _seen_prompts or full():
        _seen_prompts.add(digest)
        log.info(
            "[audit] SYSTEM PROMPT (%s chars, sha256 %s):\n%s", f"{len(system):,}", digest, system
        )
    else:
        log.info(
            "[audit] SYSTEM PROMPT: unchanged — sha256 %s, %s chars (printed in full above)",
            digest,
            f"{len(system):,}",
        )
    if as_typed is not None and as_typed != message:
        log.info("[audit] USER MESSAGE as typed:\n%s", as_typed)
        log.info("[audit] USER MESSAGE → model (names replaced by crew ids):\n%s", message)
    else:
        log.info("[audit] USER MESSAGE → model:\n%s", message)


def tool_result(
    name: str,
    arguments: dict[str, Any],
    *,
    before: Any,
    after: Any,
    removed: int,
    pii_mode: str,
    error: str | None = None,
) -> None:
    if not enabled():
        return
    log = logger()
    args = json.dumps(arguments, separators=(",", ":"), default=str)
    if error is not None:
        log.info("[audit] TOOL %s %s → error → model: %s", name, args, error)
        return
    if pii_mode == "minimal":
        log.info(
            "[audit] TOOL %s %s — BEFORE PII scrub (never leaves this machine):\n%s",
            name,
            args,
            _json(before),
        )
        log.info(
            "[audit] TOOL %s — AFTER PII scrub → model (%s removed):\n%s",
            name,
            _plural(removed),
            _json(after),
        )
    else:
        log.info(
            "[audit] TOOL %s %s → model (PII mode full — sent as is):\n%s", name, args, _json(after)
        )


def model_output(provider: str, text: str, *, elapsed_ms: float | None = None) -> None:
    if not enabled():
        return
    took = f" · {elapsed_ms / 1000:.1f}s" if elapsed_ms else ""
    logger().info("[audit] MODEL OUTPUT ← %s%s:\n%s\n[audit] %s", provider, took, text, RULE)


# ---- helpers --------------------------------------------------------------


def _json(value: Any) -> str:
    text = json.dumps(value, separators=(",", ":"), default=str, ensure_ascii=False)
    if full() or len(text) <= SNIPPET:
        return text
    more = len(text) - SNIPPET
    return f"{text[:SNIPPET]}… [{more:,} more chars; CREW_OPS_AUDIT_LOG=full prints all]"


def _plural(n: int) -> str:
    return f"{n} identifier{'s' if n != 1 else ''}"
