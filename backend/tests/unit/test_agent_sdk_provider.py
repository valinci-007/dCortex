"""The Agent SDK adapter: tool exposure, option lockdown, result parsing, error mapping.

`query` is injected, so nothing here talks to the Claude Code CLI.
"""

import asyncio
import json

import claude_agent_sdk as sdk
import pytest

from crew_ops_advisor.agent.agent_sdk_provider import (
    SERVER_NAME,
    AgentSDKProvider,
    build_sdk_tools,
    mcp_tool_name,
)
from crew_ops_advisor.agent.types import LLMError


def _result(**kw):
    base = dict(
        subtype="success",
        duration_ms=1200,
        duration_api_ms=900,
        is_error=False,
        num_turns=2,
        session_id="sess-1",
        total_cost_usd=0.05,
        usage={"input_tokens": 500, "output_tokens": 80},
        result="C-2210 is based at DEL.",
    )
    base.update(kw)
    return sdk.ResultMessage(**base)


def _assistant(*blocks):
    return sdk.AssistantMessage(content=list(blocks), model="claude-opus-5")


def fake_query(messages, *, record: list | None = None, raise_exc: Exception | None = None):
    async def query(*, prompt, options):
        if record is not None:
            record.append((prompt, options))
        if raise_exc is not None:
            raise raise_exc
        for m in messages:
            yield m

    return query


# ---- tool exposure ----------------------------------------------------------


def test_registry_tools_become_sdk_tools_with_raw_schemas_and_traced_handlers(registry):
    trace: list = []
    tools = build_sdk_tools(registry, trace, sdk.tool)
    by_name = {t.name: t for t in tools}
    assert set(by_name) == set(registry.names())
    assert by_name["get_crew"].input_schema == registry.get("get_crew").input_schema

    reply = asyncio.run(by_name["get_crew"].handler({"crew_id": "C-2210"}))
    payload = json.loads(reply["content"][0]["text"])
    assert payload["base"] == "DEL" and "is_error" not in reply
    assert trace[-1].kind == "tool" and trace[-1].name == "get_crew" and trace[-1].ok

    bad = asyncio.run(by_name["get_crew"].handler({"crew_id": "C-0000"}))
    assert bad["is_error"] is True and "unknown crew" in bad["content"][0]["text"]
    assert not trace[-1].ok


# ---- run() ------------------------------------------------------------------


def test_run_locks_down_options_and_parses_result(registry):
    record: list = []
    messages = [
        _assistant(
            sdk.ToolUseBlock(id="t1", name=mcp_tool_name("get_crew"), input={"crew_id": "C-2210"})
        ),
        _assistant(sdk.TextBlock(text="C-2210 is based at DEL.")),
        _result(),
    ]
    provider = AgentSDKProvider(
        model="claude-opus-5", effort="low", query=fake_query(messages, record=record)
    )
    run = provider.run(
        "Where is C-2210 based?", system="SYSTEM", registry=registry, resume="prev-sess"
    )

    prompt, options = record[0]
    assert prompt == "Where is C-2210 based?"
    assert options.system_prompt == "SYSTEM"
    assert options.tools == []  # no built-in Claude Code tools
    assert options.permission_mode == "dontAsk" and options.setting_sources == []
    assert options.allowed_tools == [mcp_tool_name(n) for n in registry.names()]
    assert SERVER_NAME in options.mcp_servers
    assert (options.model, options.effort, options.resume) == ("claude-opus-5", "low", "prev-sess")

    assert run.text == "C-2210 is based at DEL." and not run.refused
    assert run.session_id == "sess-1" and run.cost_usd == 0.05
    assert run.usage == {"input_tokens": 500, "output_tokens": 80}
    llm = [s for s in run.trace if s.kind == "llm"][0]
    assert llm.name == "agent-sdk" and "1 tool request(s)" in llm.summary and llm.elapsed_ms == 900


def test_text_blocks_are_used_when_result_text_is_empty(registry):
    messages = [_assistant(sdk.TextBlock(text="Final answer here.")), _result(result=None)]
    provider = AgentSDKProvider(query=fake_query(messages))
    assert provider.run("q", system="S", registry=registry).text == "Final answer here."


def test_max_turns_becomes_a_refusal_not_an_error(registry):
    messages = [_result(is_error=True, subtype="error_max_turns", result=None)]
    provider = AgentSDKProvider(query=fake_query(messages))
    run = provider.run("q", system="S", registry=registry)
    assert run.refused and "turn budget" in run.text or "turns" in run.text


def test_other_sdk_errors_and_cli_failures_become_llm_errors(registry):
    provider = AgentSDKProvider(
        query=fake_query(
            [_result(is_error=True, subtype="error_during_execution", errors=["boom"], result=None)]
        )
    )
    with pytest.raises(LLMError, match="boom"):
        provider.run("q", system="S", registry=registry)

    provider = AgentSDKProvider(
        query=fake_query([], raise_exc=sdk.CLINotFoundError("no claude binary"))
    )
    with pytest.raises(LLMError, match="Claude Code CLI"):
        provider.run("q", system="S", registry=registry)

    provider = AgentSDKProvider(query=fake_query([]))  # ends without a ResultMessage
    with pytest.raises(LLMError, match="without a result"):
        provider.run("q", system="S", registry=registry)
