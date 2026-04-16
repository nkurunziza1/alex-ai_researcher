# GitHub Actions (standalone Alex repository)

When **`alex/` is the Git repository root**, workflows live under **`.github/workflows/`**.

| Workflow | When | Purpose |
|----------|------|--------|
| **`deploy.yml`** | Manual (`workflow_dispatch`) | **Single deploy:** Part 6 agent Lambdas (OpenRouter) → Part 7 API Lambda + Next static export + S3 + CloudFront (`scripts/deploy.py`). Optional input: package agent zips with Docker first. |
| **`destroy.yml`** | Manual | `scripts/destroy.sh` after confirmation (twin-style). |

There is **no** per-PR CI workflow here by design; run tests locally (`uv`, `npm`) before deploying.

**Secrets:** `AWS_ROLE_ARN`, `ALEX_AWS_REGION`, `OPENROUTER_API_KEY`, Aurora / vector / Polygon / Clerk keys — same as guides.

## Parent monorepo

If Alex lives under e.g. `production/projects/alex`, use **`/<parent>/.github/workflows/alex-deploy.yml`** (paths prefixed with `projects/alex/`).
