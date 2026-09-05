"""PII minimisation at the tool boundary (README → Security and PII; ADR-0017).

`CREW_OPS_PII_MODE=minimal` removes direct identifiers before anything leaves this machine
for the model provider:

  - crew names are dropped from tool results (every record that carries a `crew_id`) and
    replaced by the crew id wherever they appear inside free text — tool results and the
    controller's own question alike;
  - crew ids are pseudonyms: the model reasons over `C-1042`, and the UI joins the name back
    from the local directory (`/api/directory`) for the controller.

Licence and medical dates, reachability and risk scores stay, because the desk's questions
are about them; in minimal mode they are tied to a pseudonym, not to a person. The scrub
happens in one place — the registry wrapper the model-facing providers are given — so the
trace, the grounding check and the stored conversation all see the same scrubbed data. The
offline router is local code and keeps the raw registry: nothing it touches leaves the machine.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from crew_ops_advisor.agent import audit
from crew_ops_advisor.data import Datastore
from crew_ops_advisor.tools import ToolRegistry
from crew_ops_advisor.tools.base import ToolOutcome

MODES = ("full", "minimal")
NAME_KEYS = frozenset({"name", "crew_name"})
WITHHELD = "[crew member]"  # a name shared by more than one crew member cannot be resolved


class PiiGuard:
    def __init__(self, store: Datastore, mode: str = "full"):
        if mode not in MODES:
            raise ValueError(f"unknown CREW_OPS_PII_MODE {mode!r} (use one of {', '.join(MODES)})")
        self.mode = mode
        self.directory: dict[str, str] = {c.crew_id: c.name for c in store.crew.list()}
        counts = Counter(self.directory.values())
        self._id_for_name: dict[str, str] = {
            name: crew_id for crew_id, name in self.directory.items() if counts[name] == 1
        }
        names = sorted(set(self.directory.values()), key=len, reverse=True)
        self._name_re = (
            re.compile(r"(?<![\w.])(?:" + "|".join(re.escape(n) for n in names) + r")(?![\w])")
            if names
            else None
        )

    @property
    def active(self) -> bool:
        return self.mode == "minimal"

    # ---- scrubbing --------------------------------------------------------

    def scrub_text(self, text: str) -> tuple[str, int]:
        """Known crew names → crew ids (or a withheld marker when the name is ambiguous)."""
        if not self.active or not text or self._name_re is None:
            return text, 0
        count = 0

        def swap(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return self._id_for_name.get(match.group(), WITHHELD)

        return self._name_re.sub(swap, text), count

    def scrub_result(self, value: Any) -> tuple[Any, int]:
        """Drop name fields from crew records and pseudonymise names inside strings."""
        if not self.active:
            return value, 0
        removed = 0

        def walk(node: Any) -> Any:
            nonlocal removed
            if isinstance(node, dict):
                out = {}
                is_crew = "crew_id" in node
                for key, item in node.items():
                    if is_crew and key in NAME_KEYS and isinstance(item, str):
                        removed += 1
                        continue
                    out[key] = walk(item)
                return out
            if isinstance(node, list | tuple):
                return [walk(item) for item in node]
            if isinstance(node, str):
                text, n = self.scrub_text(node)
                removed += n
                return text
            return node

        return walk(value), removed

    # ---- registry wrapper -------------------------------------------------

    def wrap(self, registry: ToolRegistry) -> ScrubbedRegistry:
        return ScrubbedRegistry(registry, self)


class ScrubbedRegistry:
    """The registry as the model-facing providers see it: same tools, results scrubbed
    according to the guard's mode, every result written to the audit console."""

    def __init__(self, inner: ToolRegistry, guard: PiiGuard):
        self._inner = inner
        self._guard = guard

    @property
    def store(self):
        return self._inner.store

    def names(self) -> list[str]:
        return self._inner.names()

    def get(self, name: str):
        return self._inner.get(name)

    def definitions(self, *, max_tier: int | None = None) -> list[dict[str, Any]]:
        return self._inner.definitions(max_tier=max_tier)

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> ToolOutcome:
        outcome = self._inner.call(name, arguments)
        if not outcome.ok or outcome.result is None:
            audit.tool_result(
                name,
                dict(arguments or {}),
                before=None,
                after=None,
                removed=0,
                pii_mode=self._guard.mode,
                error=outcome.error or "empty result",
            )
            return outcome
        scrubbed, removed = self._guard.scrub_result(outcome.result)
        audit.tool_result(
            name,
            dict(arguments or {}),
            before=outcome.result,
            after=scrubbed,
            removed=removed,
            pii_mode=self._guard.mode,
        )
        if removed == 0:
            return outcome
        return ToolOutcome(outcome.name, outcome.arguments, scrubbed, None, outcome.elapsed_ms)
