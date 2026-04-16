"""
Alex Researcher Service - Investment Advice Agent
"""

import os
from datetime import datetime, UTC
from typing import Optional

from dotenv import load_dotenv

# Load .env before any module that reads ALEX_API_* at import time
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import Agent, Runner
from agents.tracing import set_tracing_disabled
from alex_agent_llm import agent_trace, create_openrouter_model, is_openrouter_configured

# Import from our modules
from context import get_agent_instructions, DEFAULT_RESEARCH_PROMPT
from mcp_servers import create_playwright_mcp_server
from tools import ingest_financial_document

# OpenRouter: chat goes to OpenRouter; OpenAI trace export is irrelevant and spams
# "OPENAI_API_KEY is not set, skipping trace export". Disable Agents SDK tracing.
if is_openrouter_configured() or os.environ.get(
    "OPENAI_AGENTS_DISABLE_TRACING", ""
).lower() in ("1", "true", "yes"):
    set_tracing_disabled(True)

app = FastAPI(title="Alex Researcher Service")

# Browsing + MCP tool calls consume many turns; override with RESEARCH_MAX_TURNS if needed
_DEFAULT_RESEARCH_MAX_TURNS = 40


# Request model
class ResearchRequest(BaseModel):
    topic: Optional[str] = None  # Optional - if not provided, agent picks a topic


async def run_research_agent(topic: str = None) -> str:
    """Run the research agent to generate investment advice."""

    # Prepare the user query
    if topic:
        query = f"Research this investment topic: {topic}"
    else:
        query = DEFAULT_RESEARCH_PROMPT

    model = create_openrouter_model()

    max_turns = int(os.environ.get("RESEARCH_MAX_TURNS", str(_DEFAULT_RESEARCH_MAX_TURNS)))

    # Create and run the agent with MCP server (no SDK trace export with OpenRouter)
    with agent_trace("Researcher"):
        async with create_playwright_mcp_server(timeout_seconds=180) as playwright_mcp:
            agent = Agent(
                name="Alex Investment Researcher",
                instructions=get_agent_instructions(),
                model=model,
                tools=[ingest_financial_document],
                mcp_servers=[playwright_mcp],
            )

            result = await Runner.run(agent, input=query, max_turns=max_turns)

    return result.final_output


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Alex Researcher",
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.post("/research")
async def research(request: ResearchRequest) -> str:
    """
    Generate investment research and advice.

    The agent will:
    1. Browse current financial websites for data
    2. Analyze the information found
    3. Store the analysis in the knowledge base

    If no topic is provided, the agent will pick a trending topic.
    """
    try:
        response = await run_research_agent(request.topic)
        return response
    except Exception as e:
        print(f"Error in research endpoint: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/auto")
async def research_auto():
    """
    Automated research endpoint for scheduled runs.
    Picks a trending topic automatically and generates research.
    Used by EventBridge Scheduler for periodic research updates.
    """
    try:
        # Always use agent's choice for automated runs
        response = await run_research_agent(topic=None)
        return {
            "status": "success",
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Automated research completed",
            "preview": response[:200] + "..." if len(response) > 200 else response,
        }
    except Exception as e:
        print(f"Error in automated research: {e}")
        return {"status": "error", "timestamp": datetime.now(UTC).isoformat(), "error": str(e)}


@app.get("/health")
async def health():
    """Detailed health check."""
    # Debug container detection
    container_indicators = {
        "dockerenv": os.path.exists("/.dockerenv"),
        "containerenv": os.path.exists("/run/.containerenv"),
        "aws_execution_env": os.environ.get("AWS_EXECUTION_ENV", ""),
        "ecs_container_metadata": os.environ.get("ECS_CONTAINER_METADATA_URI", ""),
        "kubernetes_service": os.environ.get("KUBERNETES_SERVICE_HOST", ""),
    }

    return {
        "service": "Alex Researcher",
        "status": "healthy",
        "alex_api_configured": bool(os.getenv("ALEX_API_ENDPOINT") and os.getenv("ALEX_API_KEY")),
        "timestamp": datetime.now(UTC).isoformat(),
        "debug_container": container_indicators,
        "openrouter_model": os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    }


@app.get("/test-llm")
async def test_llm():
    """Sanity check OpenRouter connectivity (no browsing/tools)."""
    try:
        model = create_openrouter_model()
        agent = Agent(
            name="Test Agent",
            instructions="You are a helpful assistant. Be very brief.",
            model=model,
        )
        result = await Runner.run(agent, input="Say hello in 5 words or less", max_turns=1)
        return {
            "status": "success",
            "model": os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            "response": result.final_output,
        }
    except Exception as e:
        import traceback

        return {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
