# WHAPPNUS AI ORCHESTRATOR

Independent multi-provider AI orchestration service for the WHAPPNUS SaaS platform.

## Current status

Foundation branch: `feat/orchestrator-foundation`.

This is an active build, not a production-ready release. The initial commit establishes the FastAPI application, request/response contracts, Gemini/OpenAI/Anthropic adapter boundaries, deterministic routing, basic fallback, server-to-server API-key authentication, Docker/Railway configuration and initial tests.

## Stack

- Python 3.12
- FastAPI + Pydantic Settings
- Official Google GenAI, OpenAI and Anthropic SDKs
- Pytest and Ruff
- Docker; Railway-compatible dynamic `PORT`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# Set ORCHESTRATOR_API_KEY and at least one provider API key in .env
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`.

## Routes

- `GET /health` (public liveness)
- `GET /ready` (provider readiness summary)
- `GET /v1/providers`
- `GET /v1/providers/health`
- `POST /v1/chat/completions`
- `POST /v1/chat/estimate`
- `POST /v1/chat/validate`

All `/v1/*` routes require `X-Orchestrator-Key`.

## Configuration

See `.env.example`. Provider credentials are optional at startup. Providers without credentials are reported as unavailable; no simulated completions are returned. Model identifiers are environment-configurable.

## Important production gaps

The current foundation is not yet approved for production. Distributed rate limiting, tenant-scoped quotas, circuit breakers, precise provider error classification, bounded retries/backoff, token-aware context management, cost accounting, structured tracing/metrics, multimodal content contracts and comprehensive security tests remain future implementation work. The initial adapters are text-only and must not be treated as proof of vision/audio/PDF support.

## Architecture and integration

See `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/PROVIDERS.md`, `docs/SECURITY.md`, `docs/DEPLOYMENT.md` and `docs/INTEGRATION_WHAPPNUS.md`.
