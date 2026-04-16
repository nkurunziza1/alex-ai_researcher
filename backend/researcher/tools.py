"""
Tools for the Alex Researcher agent
"""
import logging
import os
from typing import Dict, Any
from datetime import datetime, UTC
import httpx
from agents import function_tool
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Read at call time so .env / App Runner env is always current (not captured at import)


def _ingest(document: Dict[str, Any]) -> Dict[str, Any]:
    """Internal function to make the actual API call."""
    endpoint = os.getenv("ALEX_API_ENDPOINT")
    api_key = os.getenv("ALEX_API_KEY")
    if not endpoint or not api_key:
        raise RuntimeError("ALEX_API_ENDPOINT or ALEX_API_KEY is missing")

    # SageMaker cold start + embedding can exceed 30s
    timeout = float(os.getenv("ALEX_INGEST_TIMEOUT_SECONDS", "120"))

    with httpx.Client() as client:
        response = client.post(
            endpoint,
            json=document,
            headers={"x-api-key": api_key},
            timeout=timeout,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = (response.text or "")[:500]
            logger.error(
                "Ingest HTTP %s %s: %s",
                response.status_code,
                endpoint,
                body,
            )
            raise RuntimeError(
                f"Ingest failed HTTP {response.status_code}: {body or response.reason_phrase}"
            ) from e
        return response.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def ingest_with_retries(document: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest with retry logic for SageMaker cold starts."""
    return _ingest(document)


@function_tool
def ingest_financial_document(topic: str, analysis: str) -> Dict[str, Any]:
    """
    Ingest a financial document into the Alex knowledge base.
    
    Args:
        topic: The topic or subject of the analysis (e.g., "AAPL Stock Analysis", "Retirement Planning Guide")
        analysis: Detailed analysis or advice with specific data and insights
    
    Returns:
        Dictionary with success status and document ID
    """
    if not os.getenv("ALEX_API_ENDPOINT") or not os.getenv("ALEX_API_KEY"):
        return {
            "success": False,
            "error": "Alex API not configured. Set ALEX_API_ENDPOINT and ALEX_API_KEY (Guide 3 ingest API).",
        }
    
    document = {
        "text": analysis,
        "metadata": {
            "topic": topic,
            "timestamp": datetime.now(UTC).isoformat()
        }
    }
    
    try:
        result = ingest_with_retries(document)
        return {
            "success": True,
            "document_id": result.get("document_id"),  # Changed from documentId
            "message": f"Successfully ingested analysis for {topic}"
        }
    except Exception as e:
        logger.exception("ingest_financial_document failed for topic=%s", topic)
        return {
            "success": False,
            "error": str(e),
        }