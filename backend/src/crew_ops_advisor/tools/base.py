"""Tool registry: the typed interface between the language model and the data.

A ToolSpec is a name, a description written for the model, a JSON schema for
its arguments, and a deterministic handler. The registry validates arguments
against the schema's `required`/`properties` before calling the handler and
turns every failure into a structured error the model can read — a tool never
raises into the agent loop.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from crew_ops_advisor.data import Datastore, NotFoundError

Handler = Callable[..., dict[str, Any]]


class ToolError(Exception):
    """A tool could not produce a result for these arguments (user-facing message)."""


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Handler
    tier: int = 1

    def definition(self) -> dict[str, Any]:
        """The provider-neutral tool definition (name/description/input_schema)."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass(frozen=True, slots=True)
class ToolOutcome:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    elapsed_ms: float

    @property
    def ok(self) -> bool:
        return self.error is None

    def content(self) -> str:
        """What the model sees: compact JSON of the result, or the error text."""
        if self.error is not None:
            return f"Error: {self.error}"
        return json.dumps(self.result, separators=(",", ":"), default=str)


@dataclass
class ToolRegistry:
    store: Datastore
    _specs: dict[str, ToolSpec] = field(default_factory=dict)

    def register(self, spec: ToolSpec) -> ToolSpec:
        if spec.name in self._specs:
            raise ValueError(f"duplicate tool {spec.name}")
        self._specs[spec.name] = spec
        return spec

    def tool(self, name: str, description: str, input_schema: dict[str, Any], *, tier: int = 1):
        """Decorator form of register(); the handler receives the Datastore first."""

        def decorate(fn: Handler) -> Handler:
            self.register(ToolSpec(name, description, input_schema, fn, tier))
            return fn

        return decorate

    def names(self) -> list[str]:
        return list(self._specs)

    def get(self, name: str) -> ToolSpec:
        return self._specs[name]

    def definitions(self, *, max_tier: int | None = None) -> list[dict[str, Any]]:
        """Stable, deterministic order — identical tool lists keep prompt caches warm."""
        specs = sorted(self._specs.values(), key=lambda s: (s.tier, s.name))
        return [s.definition() for s in specs if max_tier is None or s.tier <= max_tier]

    def call(self, name: str, arguments: Mapping[str, Any] | None = None) -> ToolOutcome:
        arguments = dict(arguments or {})
        started = time.perf_counter()
        spec = self._specs.get(name)
        if spec is None:
            return ToolOutcome(name, arguments, None, f"unknown tool '{name}'", _ms(started))
        problem = _validate(spec.input_schema, arguments)
        if problem:
            return ToolOutcome(name, arguments, None, problem, _ms(started))
        try:
            result = spec.handler(self.store, **arguments)
        except (ToolError, NotFoundError, ValueError) as exc:
            return ToolOutcome(name, arguments, None, str(exc), _ms(started))
        return ToolOutcome(name, arguments, result, None, _ms(started))


def _ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


_JSON_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _validate(schema: Mapping[str, Any], arguments: Mapping[str, Any]) -> str | None:
    props = schema.get("properties", {})
    missing = [k for k in schema.get("required", []) if k not in arguments]
    if missing:
        return f"missing required argument(s): {', '.join(missing)}"
    unknown = [k for k in arguments if k not in props]
    if unknown:
        return f"unknown argument(s): {', '.join(unknown)}; allowed: {', '.join(props)}"
    for key, value in arguments.items():
        if value is None:
            continue
        expected = props[key].get("type")
        py = _JSON_TYPES.get(expected)
        if py and not isinstance(value, py) or (expected == "integer" and isinstance(value, bool)):
            return f"argument '{key}' must be {expected}"
        choices = props[key].get("enum")
        if choices and value not in choices:
            return f"argument '{key}' must be one of {choices}"
    return None
