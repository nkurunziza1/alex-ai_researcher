"""OpenRouter model factory and tracing helpers for the OpenAI Agents SDK."""

from __future__ import annotations

import os
from contextlib import nullcontext


def is_openrouter_configured() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())


def create_openrouter_model():
    """
    Build an OpenAI-compatible chat model pointed at OpenRouter.

    Environment:
      OPENROUTER_API_KEY (required)
      OPENROUTER_BASE_URL (optional, default https://openrouter.ai/api/v1)
      OPENROUTER_MODEL (optional, default openai/gpt-4o-mini)

    Also disables OpenAI-hosted trace export when using OpenRouter (otherwise the
    SDK posts spans to api.openai.com and a stale/wrong OPENAI_API_KEY causes 401).
    """
    from openai import AsyncOpenAI
    from agents import OpenAIChatCompletionsModel
    from agents.tracing import set_tracing_disabled

    if is_openrouter_configured() or os.getenv(
        "OPENAI_AGENTS_DISABLE_TRACING", ""
    ).lower() in ("1", "true", "yes"):
        set_tracing_disabled(True)

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required. Add it to your environment or .env file."
        )
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


def agent_trace(name: str):
    """
    Context manager for Agents SDK tracing.

    OpenRouter does not support the SDK's OpenAI-hosted tracing export, so tracing
    is skipped whenever OpenRouter is configured. Tracing is only enabled when
    OPENAI_API_KEY is set and OpenRouter is not in use.
    """
    if is_openrouter_configured():
        return nullcontext()
    try:
        from agents import trace
    except ImportError:
        return nullcontext()
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return nullcontext()
    return trace(name)
