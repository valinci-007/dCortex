"""dCortex Agentic Crew Ops Advisor.

Layering (see docs/architecture.md):
    domain      typed entities + time helpers (no I/O)
    data        SQLite loader + repositories (the only code that touches SQL)
    rules       the seven legality rules as pure functions -> RuleVerdict / LegalityEvidence
    simulation  Tier-2 engines composed from rules (P2)
    tools       typed tool registry exposed to the LLM (P1)
    agent       orchestrator, provider-agnostic LLM client, refusal policy (P1)
    explain     evidence -> reasoning trail rendering (P2)
    interface   local API + CLI (P1/P3)
"""

__version__ = "0.1.0"
