"""Anthropic adapter for the provider-neutral LLM contract.

The session keeps the raw transcript (assistant content blocks are echoed back
unchanged, which is what the API requires for thinking and tool-use blocks) and
translates each response into a Turn for the orchestrator.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

from crew_ops_advisor.agent.types import LLMError, ToolCall, ToolResult, Turn

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_EFFORT = "medium"
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        effort: str = DEFAULT_EFFORT,
        max_tokens: int = 8192,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - depends on the optional extra
            raise LLMError(
                "the 'anthropic' package is not installed (pip install -e '.[llm]')"
            ) from exc
        self._anthropic = anthropic
        kwargs: dict[str, Any] = {"timeout": timeout, "max_retries": max_retries}
        if api_key:
            kwargs["api_key"] = api_key
        self._client = anthropic.Anthropic(**kwargs)
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens

    def open_session(self, system: str, tools: Sequence[dict[str, Any]]) -> AnthropicSession:
        return AnthropicSession(self, system, list(tools))


class AnthropicSession:
    def __init__(self, provider: AnthropicProvider, system: str, tools: list[dict[str, Any]]):
        self._p = provider
        # cache_control on the system block: the tools + system prefix is identical for every
        # question in a session, so every request after the first reads it from cache.
        self._system = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        self._tools = tools
        self._messages: list[dict[str, Any]] = []

    def seed(self, prior: Sequence[tuple[str, str]]) -> None:
        """Replay stored (question, answer) pairs as plain text so a reopened chat has context."""
        for question, answer in prior:
            self._messages.append({"role": "user", "content": question})
            self._messages.append({"role": "assistant", "content": answer})

    def send_user(self, text: str) -> Turn:
        self._messages.append({"role": "user", "content": text})
        return self._create()

    def send_tool_results(self, results: Sequence[ToolResult]) -> Turn:
        blocks = [
            {
                "type": "tool_result",
                "tool_use_id": r.call_id,
                "content": r.content,
                "is_error": r.is_error,
            }
            for r in results
        ]
        self._messages.append({"role": "user", "content": blocks})
        return self._create()

    def _create(self) -> Turn:
        a = self._p._anthropic
        started = time.perf_counter()
        try:
            response = self._p._client.beta.messages.create(
                model=self._p.model,
                max_tokens=self._p.max_tokens,
                system=self._system,
                tools=self._tools,
                messages=list(self._messages),
                output_config={"effort": self._p.effort},
                betas=[_FALLBACK_BETA],
                fallbacks="default",
            )
        except a.AuthenticationError as exc:
            raise LLMError("Anthropic authentication failed — check ANTHROPIC_API_KEY") from exc
        except a.RateLimitError as exc:
            raise LLMError("Anthropic rate limit hit; retry shortly") from exc
        except a.APIStatusError as exc:
            raise LLMError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
        except a.APIConnectionError as exc:
            raise LLMError("could not reach the Anthropic API (network)") from exc
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        # Echo the full content back (thinking + tool_use blocks included) on the next request.
        self._messages.append({"role": "assistant", "content": response.content})

        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, arguments=dict(block.input)))

        usage = response.usage
        return Turn(
            text="\n".join(p for p in text_parts if p).strip(),
            tool_calls=tuple(calls),
            stop_reason=response.stop_reason or "end_turn",
            refused=response.stop_reason == "refusal",
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0)
                or 0,
            },
            latency_ms=latency_ms,
        )
