from typing import Any, Optional

from app.core.credentials import get_credential, has_credential, mask_credential
from app.core.database import connect
from .base import BaseModelAdapter
from .heuristic import HeuristicExtractor
from .providers import AnthropicAdapter, GeminiAdapter, OpenAIAdapter

SUPPORTED_PROVIDERS = ["openai", "anthropic", "gemini", "heuristic"]


def get_active_provider_name() -> str:
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE key='active_provider'").fetchone()
        if row and row["value"] in SUPPORTED_PROVIDERS:
            return row["value"]
    return "heuristic"


def set_active_provider_name(provider: str) -> str:
    clean = provider.strip().lower()
    if clean not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Provider must be one of {SUPPORTED_PROVIDERS}")
    with connect() as db:
        db.execute(
            "INSERT INTO settings(key, value) VALUES ('active_provider', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
            (clean,),
        )
    return clean


def get_model_settings() -> dict[str, Any]:
    active = get_active_provider_name()
    providers_status = {}
    for p in ["openai", "anthropic", "gemini"]:
        configured = has_credential(p)
        key = get_credential(p)
        providers_status[p] = {
            "configured": configured,
            "masked_key": mask_credential(key),
        }
    providers_status["heuristic"] = {
        "configured": True,
        "masked_key": "Local rules (offline)",
    }
    return {
        "active_provider": active,
        "providers": providers_status,
        "supported_providers": SUPPORTED_PROVIDERS,
    }


def get_active_adapter() -> BaseModelAdapter:
    active = get_active_provider_name()
    if active == "openai":
        return OpenAIAdapter(api_key=get_credential("openai"))
    if active == "anthropic":
        return AnthropicAdapter(api_key=get_credential("anthropic"))
    if active == "gemini":
        return GeminiAdapter(api_key=get_credential("gemini"))
    return HeuristicExtractor()


def extract_tasks_from_context(context_excerpts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adapter = get_active_adapter()
    return adapter.extract_tasks_and_urgency(context_excerpts)
