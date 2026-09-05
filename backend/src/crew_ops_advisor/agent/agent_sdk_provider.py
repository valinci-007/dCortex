"""Claude Agent SDK adapter (ADR-0012): the SDK runs the agent loop, our tools stay ours.

The registry is exposed to the SDK as an in-process MCP server, so the model can
call exactly our typed, deterministic tools and nothing else: Claude Code's
built-in tools (Read/Bash/Write/WebSearch/…) are disabled, permissions are set to
deny anything not pre-approved, and no filesystem settings (CLAUDE.md, skills)
are loaded. Each tool handler records the trace entry itself, so the reasoning
trail has the same shape as with the turn-based providers.

Authentication is the SDK's: an `ANTHROPIC_API_KEY` in the environment, or the
Claude Code login already on the machine. Anthropic permits only API-key
authentication for products built on the Agent SDK (see ADR-0012).
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from crew_ops_advisor.agent.prompts import REFUSAL_PHRASE
from crew_ops_advisor.agent.types import EventSink, LLMError, LoopRun, TraceStep
from crew_ops_advisor.tools import ToolRegistry

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_EFFORT = "medium"
SERVER_NAME = "crew_ops"
MAX_TURNS = 8


def mcp_tool_name(tool: str) -> str:
    """How the SDK names an MCP tool: mcp__<server>__<tool>."""
    return f"mcp__{SERVER_NAME}__{tool}"


class AgentSDKProvider:
    name = "agent-sdk"
    owns_loop = True

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        effort: str = DEFAULT_EFFORT,
        max_turns: int = MAX_TURNS,
        max_budget_usd: float | None = None,
        cwd: str | Path | None = None,
        query: Callable[..., Any] | None = None,
    ):
        try:
            import claude_agent_sdk as sdk
        except ImportError as exc:  # pragma: no cover - depends on the optional extra
            raise LLMError(
                "the 'claude-agent-sdk' package is not installed (pip install -e '.[agent]')"
            ) from exc
        self._sdk = sdk
        self._query = query or sdk.query  # injectable for tests
        self.model = model
        self.effort = effort
        self.max_turns = max_turns
        self.max_budget_usd = max_budget_usd
        self.cwd = Path(cwd) if cwd else None

    # ---- public ------------------------------------------------------------

    def run(
        self,
        question: str,
        *,
        system: str,
        registry: ToolRegistry,
        resume: str | None = None,
        on_event: EventSink | None = None,
    ) -> LoopRun:
        return _run_sync(
            self.run_async(
                question, system=system, registry=registry, resume=resume, on_event=on_event
            )
        )

    async def run_async(
        self,
        question: str,
        *,
        system: str,
        registry: ToolRegistry,
        resume: str | None = None,
        on_event: EventSink | None = None,
    ) -> LoopRun:
        sdk = self._sdk
        trace: list[TraceStep] = []
        emit = on_event or (lambda event: None)
        tools = build_sdk_tools(registry, trace, sdk.tool, on_event=emit)
        server = sdk.create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=tools)
        options = sdk.ClaudeAgentOptions(
            system_prompt=system,
            include_partial_messages=on_event is not None,  # text deltas for the live UI
            tools=[],  # no built-in Claude Code tools: the registry is the only data access
            allowed_tools=[mcp_tool_name(n) for n in registry.names()],
            mcp_servers={SERVER_NAME: server},
            permission_mode="dontAsk",  # anything not pre-approved is denied, never prompted
            setting_sources=[],  # ignore CLAUDE.md / skills / hooks on this machine
            max_turns=self.max_turns,
            max_budget_usd=self.max_budget_usd,
            model=self.model,
            effort=self.effort,
            resume=resume,
            cwd=self.cwd,
        )

        texts: list[str] = []
        requested: list[str] = []
        result = None
        started = time.perf_counter()
        try:
            async for message in self._query(prompt=question, options=options):
                if isinstance(message, sdk.AssistantMessage):
                    for block in message.content:
                        if isinstance(block, sdk.TextBlock) and block.text.strip():
                            texts.append(block.text)
                        elif isinstance(block, sdk.ToolUseBlock):
                            requested.append(block.name)
                            emit(tool_call_event(block.name, block.input))
                elif isinstance(message, sdk.ResultMessage):
                    result = message
                elif on_event is not None and isinstance(message, sdk.StreamEvent):
                    delta = _text_delta(message.event)
                    if delta:
                        emit({"type": "text", "text": delta})
        except (sdk.CLINotFoundError, sdk.CLIConnectionError) as exc:
            raise LLMError(f"Claude Agent SDK cannot reach the Claude Code CLI: {exc}") from exc
        except sdk.ProcessError as exc:
            raise LLMError(f"Claude Agent SDK process failed: {_short(str(exc))}") from exc
        except sdk.CLIJSONDecodeError as exc:
            raise LLMError(
                f"Claude Agent SDK returned unreadable output: {_short(str(exc))}"
            ) from exc
        except sdk.ClaudeSDKError as exc:
            raise LLMError(f"Claude Agent SDK error: {_short(str(exc))}") from exc
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        if result is None:
            raise LLMError("Claude Agent SDK ended without a result message")

        api_ms = getattr(result, "duration_api_ms", None) or elapsed_ms
        trace.append(
            TraceStep(
                "llm",
                "agent-sdk",
                {"model": self.model, "effort": self.effort},
                float(api_ms),
                not result.is_error,
                f"{result.num_turns} turn(s), {len(requested)} tool request(s), "
                f"stop={result.subtype}",
            )
        )
        usage = _usage(result.usage)
        refused = False
        text = (result.result or "").strip() or "\n\n".join(t.strip() for t in texts).strip()
        if result.is_error:
            if "max_turns" in (result.subtype or ""):
                text = (
                    f"{REFUSAL_PHRASE}: the question needed more model turns than the "
                    f"{self.max_turns}-turn budget allows."
                )
                refused = True
            elif "budget" in (result.subtype or ""):
                text = f"{REFUSAL_PHRASE}: the per-question cost budget was exhausted."
                refused = True
            else:
                errors = "; ".join(result.errors or []) or result.subtype or "unknown error"
                raise LLMError(f"Claude Agent SDK error ({result.subtype}): {_short(errors)}")
        return LoopRun(
            text=text,
            trace=tuple(trace),
            usage=usage,
            refused=refused,
            session_id=result.session_id,
            cost_usd=result.total_cost_usd,
            stop_reason=result.subtype or "success",
        )


# ---- tools ---------------------------------------------------------------


def build_sdk_tools(
    registry: ToolRegistry,
    trace: list[TraceStep],
    tool_decorator,
    *,
    on_event: EventSink | None = None,
) -> list[Any]:
    """Wrap every registry tool as an SDK MCP tool whose handler calls the registry and
    records the trace entry. The registry's own validation and error mapping apply."""
    from crew_ops_advisor.agent.orchestrator import tool_done_event, tool_step

    tools = []
    for name in registry.names():
        spec = registry.get(name)

        async def handler(args: dict[str, Any], _name: str = name) -> dict[str, Any]:
            outcome = registry.call(_name, args or {})
            step = tool_step(_name, args or {}, outcome)
            trace.append(step)
            if on_event is not None:
                on_event(tool_done_event(step))
            reply: dict[str, Any] = {"content": [{"type": "text", "text": outcome.content()}]}
            if not outcome.ok:
                reply["is_error"] = True
            return reply

        tools.append(tool_decorator(spec.name, spec.description, spec.input_schema)(handler))
    return tools


# ---- helpers -------------------------------------------------------------


def tool_call_event(sdk_tool_name: str, arguments: Any) -> dict[str, Any]:
    from crew_ops_advisor.agent.orchestrator import tool_call_event as _event

    prefix = f"mcp__{SERVER_NAME}__"
    name = sdk_tool_name[len(prefix) :] if sdk_tool_name.startswith(prefix) else sdk_tool_name
    return _event(name, arguments if isinstance(arguments, dict) else {})


def _text_delta(event: dict[str, Any]) -> str:
    """The text of a raw API stream event, if it carries any."""
    if event.get("type") != "content_block_delta":
        return ""
    delta = event.get("delta") or {}
    return delta.get("text", "") if delta.get("type") == "text_delta" else ""


def _usage(raw: Any) -> dict[str, int]:
    if not raw:
        return {}
    if not isinstance(raw, dict):
        raw = {
            k: getattr(raw, k, None)
            for k in (
                "input_tokens",
                "output_tokens",
                "cache_read_input_tokens",
                "cache_creation_input_tokens",
            )
        }
    out: dict[str, int] = {}
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    ):
        value = raw.get(key)
        if isinstance(value, int | float):
            out[key] = int(value)
    return out


def _short(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _run_sync(coro):
    """Run a coroutine from sync code, even when an event loop is already running
    (e.g. inside an async web server): then use a worker thread with its own loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def describe_options(options: Any) -> str:
    """Debug helper: the options as JSON-ish text (used by tests and --json traces)."""
    keys = (
        "tools",
        "allowed_tools",
        "permission_mode",
        "setting_sources",
        "max_turns",
        "model",
        "effort",
        "resume",
    )
    return json.dumps({k: getattr(options, k, None) for k in keys}, default=str)
