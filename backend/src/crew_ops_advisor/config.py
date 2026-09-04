"""Runtime settings, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    db_path: Path
    chats_db_path: Path
    llm_provider: str  # "agent-sdk" | "anthropic" | "offline"
    anthropic_api_key: str | None
    llm_model: str
    llm_effort: str  # low | medium | high | xhigh | max
    offline_fallback: bool  # answer via the offline router if the model provider fails
    agent_max_budget_usd: float | None  # per-question cost cap for the Agent SDK (API-key billing)
    # voice (ADR-0016)
    stt_provider: str  # whisper | sarvam | browser
    tts_provider: str  # browser | sarvam
    whisper_model: str
    sarvam_api_key: str | None
    sarvam_stt_model: str
    sarvam_tts_model: str
    sarvam_tts_speaker: str
    sarvam_language: str
    sarvam_stt_url: str
    sarvam_tts_url: str

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        data_dir = Path(env.get("CREW_OPS_DATA_DIR", _REPO_ROOT / "data"))
        db_path = Path(env.get("CREW_OPS_DB_PATH", _REPO_ROOT / "var" / "crew_ops.db"))
        chats = Path(env.get("CREW_OPS_CHATS_DB_PATH", _REPO_ROOT / "var" / "chats.db"))
        return cls(
            data_dir=data_dir if data_dir.is_absolute() else _REPO_ROOT / data_dir,
            db_path=db_path if db_path.is_absolute() else _REPO_ROOT / db_path,
            chats_db_path=chats if chats.is_absolute() else _REPO_ROOT / chats,
            llm_provider=env.get("CREW_OPS_LLM_PROVIDER", "agent-sdk"),
            anthropic_api_key=env.get("ANTHROPIC_API_KEY") or None,
            llm_model=env.get("CREW_OPS_LLM_MODEL", "claude-opus-5"),
            llm_effort=env.get("CREW_OPS_LLM_EFFORT", "medium"),
            offline_fallback=env.get("CREW_OPS_OFFLINE_FALLBACK", "1") not in ("0", "false", "no"),
            agent_max_budget_usd=_optional_float(env.get("CREW_OPS_AGENT_MAX_BUDGET_USD", "0.50")),
            stt_provider=env.get("CREW_OPS_STT_PROVIDER", "whisper"),
            tts_provider=env.get("CREW_OPS_TTS_PROVIDER", "browser"),
            whisper_model=env.get("CREW_OPS_WHISPER_MODEL", "base"),
            sarvam_api_key=env.get("SARVAM_API_KEY") or None,
            sarvam_stt_model=env.get("SARVAM_STT_MODEL", "saarika:v2.5"),
            sarvam_tts_model=env.get("SARVAM_TTS_MODEL", "bulbul:v2"),
            sarvam_tts_speaker=env.get("SARVAM_TTS_SPEAKER", "anushka"),
            sarvam_language=env.get("SARVAM_LANGUAGE", "en-IN"),
            sarvam_stt_url=env.get("SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text"),
            sarvam_tts_url=env.get("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech"),
        )


def _optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "" or value.strip().lower() in ("none", "off"):
        return None
    return float(value)


DATASET_FILES = (
    "flights.json",
    "crew.json",
    "rosters.json",
    "duty_clocks.json",
    "reserve_pool.json",
    "certifications.json",
    "rules.json",
    "costs.json",
    "risk_signals.json",
    "scenarios.json",
    "questions.json",
)
