FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN npx -y playwright install --with-deps chromium

RUN pip install uv

# Shared OpenRouter helpers (path dependency from researcher/pyproject.toml)
COPY agent_llm /app/agent_llm

WORKDIR /app/researcher
COPY researcher/pyproject.toml researcher/uv.lock ./

RUN uv sync --frozen --no-install-project

COPY researcher/*.py ./
COPY researcher/playwright-mcp.config.json ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
