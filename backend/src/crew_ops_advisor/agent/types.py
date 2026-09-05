"""Provider-neutral contract between the orchestrator and any language model.

The orchestrator only ever sees Turns: text plus zero or more tool calls. How a
provider represents its transcript (content blocks, thinking, ids) stays inside
the provider's session object, so swapping providers is a config change.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    content: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class Turn:
    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    stop_reason: str = "end_turn"
    refused: bool = False  # the provider itself declined (offline router: nothing matched)
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


class LLMError(RuntimeError):
    """The provider could not produce a turn (network, auth, quota, malformed reply)."""


class LLMSession(Protocol):
    """One conversation with one provider. Providers own their transcript."""

    def send_user(self, text: str) -> Turn: ...

    def send_tool_results(self, results: Sequence[ToolResult]) -> Turn: ...


class LLMProvider(Protocol):
    """A provider whose loop *we* run — it answers turn by turn (Anthropic adapter, offline)."""

    name: str

    def open_session(self, system: str, tools: Sequence[dict[str, Any]]) -> LLMSession: ...


@dataclass(frozen=True, slots=True)
class TraceStep:
    """One step of the reasoning trail: a model call or a tool call."""

    kind: str  # "llm" | "tool"
    name: str
    arguments: dict[str, Any]
    elapsed_ms: float
    ok: bool
    summary: str
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "arguments": self.arguments,
            "elapsed_ms": self.elapsed_ms,
            "ok": self.ok,
            "summary": self.summary,
            "result": self.result,
        }


@dataclass(frozen=True, slots=True)
class LoopRun:
    """What a loop-owning provider hands back for one question."""

    text: str
    trace: tuple[TraceStep, ...]
    usage: dict[str, int] = field(default_factory=dict)
    refused: bool = False
    session_id: str | None = None
    cost_usd: float | None = None
    stop_reason: str = "end_turn"


# Progress events pushed to the UI while an answer is being produced (ADR-0018 §1):
#   {"type": "tool_call", "name", "label", "arguments"}      a lookup or simulation starts
#   {"type": "tool_done", "name", "label", "ok", "elapsed_ms", "summary"}
#   {"type": "text", "text"}                                  a chunk of the answer as written
#   {"type": "phase", "text"}                                 e.g. "verifying the answer"
EventSink = Callable[[dict[str, Any]], None]


class LoopProvider(Protocol):
    """A provider that runs the agent loop itself (the Claude Agent SDK) and calls our tools
    through the registry. `owns_loop` is how the orchestrator tells the two shapes apart."""

    name: str
    owns_loop: bool

    def run(
        self,
        question: str,
        *,
        system: str,
        registry: Any,
        resume: str | None = None,
        on_event: EventSink | None = None,
    ) -> LoopRun: ...
