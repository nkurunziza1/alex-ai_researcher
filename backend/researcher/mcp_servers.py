"""
MCP server configurations for the Alex Researcher
"""
import glob
import os
from pathlib import Path

from agents.mcp import MCPServerStdio


def create_playwright_mcp_server(timeout_seconds=60):
    """Create a Playwright MCP server instance for web browsing.
    
    Args:
        timeout_seconds: Client session timeout in seconds (default: 60)
        
    Returns:
        MCPServerStdio instance configured for Playwright
    """
    # Base arguments (Docker/App Runner: see playwright-mcp.config.json for launchOptions)
    args = [
        "@playwright/mcp@latest",
        "--headless",
        "--isolated",
        "--no-sandbox",
        "--ignore-https-errors",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    ]
    _config = Path(__file__).resolve().parent / "playwright-mcp.config.json"
    if _config.exists():
        args.extend(["--config", str(_config)])
    
    # Add executable path in Docker / App Runner (Linux container)
    if os.path.exists("/.dockerenv") or os.environ.get("AWS_EXECUTION_ENV") or os.path.exists(
        "/run/.containerenv"
    ):
        # Find the installed Chrome executable dynamically
        chrome_paths = glob.glob("/root/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")
        if chrome_paths:
            # Use the first (should be only one) Chrome installation found
            chrome_path = chrome_paths[0]
            print(f"DEBUG: Found Chrome at: {chrome_path}")
            args.extend(["--executable-path", chrome_path])
        else:
            # Fallback to a known path if glob doesn't find it
            print("DEBUG: Chrome not found via glob, using fallback path")
            args.extend(["--executable-path", "/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"])
    
    params = {
        "command": "npx",
        "args": args
    }
    
    return MCPServerStdio(params=params, client_session_timeout_seconds=timeout_seconds)