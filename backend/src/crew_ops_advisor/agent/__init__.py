"""Agent layer: orchestrator, provider-neutral LLM contract, adapters, prompts."""

from __future__ import annotations

from crew_ops_advisor.agent.offline_provider import OFFLINE_LABEL, OfflineProvider
from crew_ops_advisor.agent.orchestrator import (
    Advisor,
    Answer,
    Conversation,
    TraceStep,
    render_trace,
)
from crew_ops_advisor.agent.prompts import REFUSAL_PHRASE, build_system_prompt
from crew_ops_advisor.agent.types import (
    LLMError,
    LLMProvider,
    LLMSession,
    LoopProvider,
    LoopRun,
    ToolCall,
    ToolResult,
    Turn,
)
from crew_ops_advisor.config import Settings
from crew_ops_advisor.data import Datastore
from crew_ops_advisor.tools import build_registry

PROVIDERS = ("agent-sdk", "anthropic", "offline")


def make_provider(settings: Settings, store: Datastore) -> LLMProvider | LoopProvider:
    """Choose the provider from settings (ADR-0005/0012)."""
    if settings.llm_provider == "agent-sdk":
        from crew_ops_advisor.agent.agent_sdk_provider import AgentSDKProvider

        return AgentSDKProvider(
            model=settings.llm_model,
            effort=settings.llm_effort,
            max_budget_usd=settings.agent_max_budget_usd,
            cwd=settings.db_path.parent,
        )
    if settings.llm_provider == "anthropic":
        from crew_ops_advisor.agent.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            effort=settings.llm_effort,
        )
    if settings.llm_provider == "offline":
        return OfflineProvider(store)
    choices = ", ".join(PROVIDERS)
    raise ValueError(
        f"unknown CREW_OPS_LLM_PROVIDER {settings.llm_provider!r} (use one of {choices})"
    )


def make_advisor(
    settings: Settings,
    store: Datastore,
    *,
    provider: LLMProvider | LoopProvider | None = None,
) -> Advisor:
    """Build the Advisor; model providers get the offline router as fallback (ADR-0003)."""
    provider = provider or make_provider(settings, store)
    fallback = None
    if settings.offline_fallback and provider.name != "offline":
        fallback = OfflineProvider(store)
    return Advisor(store, build_registry(store), provider, fallback=fallback)


__all__ = [
    "OFFLINE_LABEL",
    "REFUSAL_PHRASE",
    "Advisor",
    "Answer",
    "Conversation",
    "LLMError",
    "LLMProvider",
    "LLMSession",
    "LoopProvider",
    "LoopRun",
    "OfflineProvider",
    "PROVIDERS",
    "ToolCall",
    "ToolResult",
    "TraceStep",
    "Turn",
    "build_system_prompt",
    "make_advisor",
    "make_provider",
    "render_trace",
]
