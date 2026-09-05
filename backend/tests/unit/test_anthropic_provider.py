"""The Anthropic adapter builds the right request and reads the response (fake client)."""

from types import SimpleNamespace

import anthropic
import pytest

from crew_ops_advisor.agent.anthropic_provider import AnthropicProvider
from crew_ops_advisor.agent.types import LLMError, ToolResult


class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def _resp(content, stop_reason="end_turn"):
    return SimpleNamespace(
        content=content,
        stop_reason=stop_reason,
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=20,
            cache_read_input_tokens=80,
            cache_creation_input_tokens=0,
        ),
    )


def _block(**kw):
    return SimpleNamespace(**kw)


def provider_with(responses):
    p = AnthropicProvider(api_key="test-key", model="claude-opus-5", effort="low")
    fake = FakeMessages(responses)
    p._client = SimpleNamespace(beta=SimpleNamespace(messages=fake))
    return p, fake


def test_request_shape_and_tool_call_parsing():
    tool_use = _block(type="tool_use", id="toolu_1", name="get_crew", input={"crew_id": "C-1042"})
    p, fake = provider_with(
        [_resp([_block(type="text", text="Looking up."), tool_use], "tool_use")]
    )
    session = p.open_session(
        "SYSTEM", [{"name": "get_crew", "description": "d", "input_schema": {"type": "object"}}]
    )
    turn = session.send_user("Who is C-1042?")

    req = fake.requests[0]
    assert req["model"] == "claude-opus-5" and req["output_config"] == {"effort": "low"}
    assert req["system"][0]["text"] == "SYSTEM" and req["system"][0]["cache_control"] == {
        "type": "ephemeral"
    }
    assert req["tools"][0]["name"] == "get_crew"
    assert req["fallbacks"] == "default" and req["betas"] == ["server-side-fallback-2026-07-01"]
    assert req["messages"] == [{"role": "user", "content": "Who is C-1042?"}]

    assert turn.wants_tools and turn.tool_calls[0].name == "get_crew"
    assert turn.tool_calls[0].arguments == {"crew_id": "C-1042"} and turn.text == "Looking up."
    assert turn.usage["cache_read_input_tokens"] == 80 and turn.stop_reason == "tool_use"


def test_tool_results_are_batched_in_one_user_message_and_content_echoed_back():
    tool_use = _block(type="tool_use", id="toolu_1", name="get_crew", input={})
    first = _resp([_block(type="thinking", thinking=""), tool_use], "tool_use")
    p, fake = provider_with([first, _resp([_block(type="text", text="Done.")])])
    session = p.open_session("S", [])
    session.send_user("q")
    turn = session.send_tool_results(
        [ToolResult("toolu_1", '{"ok":true}'), ToolResult("toolu_2", "Error: x", is_error=True)]
    )

    msgs = fake.requests[1]["messages"]
    assert msgs[1] == {
        "role": "assistant",
        "content": first.content,
    }  # raw blocks, thinking included
    assert msgs[2]["role"] == "user" and [b["type"] for b in msgs[2]["content"]] == [
        "tool_result",
        "tool_result",
    ]
    assert (
        msgs[2]["content"][1]["is_error"] is True
        and msgs[2]["content"][0]["tool_use_id"] == "toolu_1"
    )
    assert turn.text == "Done." and not turn.wants_tools


def test_refusal_stop_reason_is_surfaced():
    p, _ = provider_with([_resp([], "refusal")])
    turn = p.open_session("S", []).send_user("q")
    assert turn.refused and turn.text == ""


def test_api_errors_become_llm_errors():
    err = anthropic.APIConnectionError(request=SimpleNamespace())
    p, _ = provider_with([err])
    with pytest.raises(LLMError, match="could not reach"):
        p.open_session("S", []).send_user("q")
