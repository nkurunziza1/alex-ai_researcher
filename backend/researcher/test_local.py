#!/usr/bin/env python3
"""
Run the researcher agent in-process (no HTTP). Uses the same stack as server.py.

Prerequisites:
  - projects/alex/.env with OPENROUTER_API_KEY (and optional OPENROUTER_MODEL)
  - Playwright browsers: npx playwright install chromium (or rely on first run)

Usage:
  cd backend/researcher
  uv run test_local.py
  uv run test_local.py "Your topic here"
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

from agents import Agent, Runner
from agents.tracing import set_tracing_disabled
from alex_agent_llm import create_openrouter_model, is_openrouter_configured

from context import get_agent_instructions, DEFAULT_RESEARCH_PROMPT
from mcp_servers import create_playwright_mcp_server
from tools import ingest_financial_document

if is_openrouter_configured() or os.environ.get(
    "OPENAI_AGENTS_DISABLE_TRACING", ""
).lower() in ("1", "true", "yes"):
    set_tracing_disabled(True)

_DEFAULT_RESEARCH_MAX_TURNS = 40


async def test_local(topic: str | None = None):
    """Run one research pass like /research."""
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        print("❌ Set OPENROUTER_API_KEY in projects/alex/.env (or export it).")
        sys.exit(1)

    query = (
        f"Research this investment topic: {topic}"
        if topic
        else DEFAULT_RESEARCH_PROMPT
    )
    max_turns = int(os.environ.get("RESEARCH_MAX_TURNS", str(_DEFAULT_RESEARCH_MAX_TURNS)))
    model = create_openrouter_model()

    print("Testing researcher (OpenRouter + Playwright MCP + ingest tool)...")
    print("=" * 60)

    async with create_playwright_mcp_server(timeout_seconds=60) as playwright_mcp:
        agent = Agent(
            name="Alex Investment Researcher",
            instructions=get_agent_instructions(),
            model=model,
            tools=[ingest_financial_document],
            mcp_servers=[playwright_mcp],
        )
        result = await Runner.run(agent, input=query, max_turns=max_turns)

    print("\nRESULT:")
    print("=" * 60)
    print(result.final_output)
    print("=" * 60)
    print("\n✅ Local run finished.")


if __name__ == "__main__":
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_local(topic_arg))
