"""The registry validates arguments and never lets a tool raise into the agent loop."""

from crew_ops_advisor.tools import ToolError, ToolRegistry, ToolSpec


def _registry():
    reg = ToolRegistry(store=None)

    def echo(store, name: str, times: int = 1) -> dict:
        if name == "boom":
            raise ToolError("boom is not allowed")
        return {"echo": name * times}

    reg.register(
        ToolSpec(
            "echo",
            "Echo a name",
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "times": {"type": "integer"},
                },
                "required": ["name"],
            },
            echo,
            tier=2,
        )
    )
    reg.register(
        ToolSpec(
            "noop", "No arguments", {"type": "object", "properties": {}}, lambda store: {"ok": True}
        )
    )
    return reg


def test_call_returns_result_and_json_content():
    out = _registry().call("echo", {"name": "ab", "times": 2})
    assert out.ok and out.result == {"echo": "abab"}
    assert out.content() == '{"echo":"abab"}'
    assert out.elapsed_ms >= 0


def test_missing_required_argument_is_an_error_not_an_exception():
    out = _registry().call("echo", {})
    assert not out.ok and "missing required argument(s): name" in out.error
    assert out.content().startswith("Error: ")


def test_unknown_argument_and_wrong_type_are_rejected():
    reg = _registry()
    assert "unknown argument(s): nope" in reg.call("echo", {"name": "x", "nope": 1}).error
    assert "must be integer" in reg.call("echo", {"name": "x", "times": "3"}).error
    assert "must be integer" in reg.call("echo", {"name": "x", "times": True}).error


def test_unknown_tool_and_tool_error_are_reported():
    reg = _registry()
    assert "unknown tool" in reg.call("nothing", {}).error
    assert reg.call("echo", {"name": "boom"}).error == "boom is not allowed"


def test_definitions_are_sorted_by_tier_then_name_and_filterable():
    reg = _registry()
    assert [d["name"] for d in reg.definitions()] == ["noop", "echo"]
    assert [d["name"] for d in reg.definitions(max_tier=1)] == ["noop"]
    assert set(reg.definitions()[0]) == {"name", "description", "input_schema"}
