#!/usr/bin/env python3
"""Run the Financial Planner orchestrator for one job (local dev when SQS/Lambda is not used)."""

import asyncio
import sys

from lambda_handler import run_orchestrator


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run run_planner_job.py <job_id>", file=sys.stderr)
        sys.exit(1)
    job_id = sys.argv[1].strip()
    asyncio.run(run_orchestrator(job_id))


if __name__ == "__main__":
    main()
