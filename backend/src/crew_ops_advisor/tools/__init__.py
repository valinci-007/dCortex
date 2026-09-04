"""Tool layer: the typed registry the model calls into. Tools are the only way the
language side touches data or arithmetic."""

from crew_ops_advisor.tools.base import ToolError, ToolOutcome, ToolRegistry, ToolSpec
from crew_ops_advisor.tools.query_tools import build_registry, register_query_tools
from crew_ops_advisor.tools.recommendation_tools import register_recommendation_tools
from crew_ops_advisor.tools.simulation_tools import register_simulation_tools

__all__ = [
    "ToolError",
    "ToolOutcome",
    "ToolRegistry",
    "ToolSpec",
    "build_registry",
    "register_query_tools",
    "register_recommendation_tools",
    "register_simulation_tools",
]
