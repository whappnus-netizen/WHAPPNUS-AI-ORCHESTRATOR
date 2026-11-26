# WHAPPNUS AI ORCHESTRATOR

Independent multi-provider AI orchestration service for WHAPPNUS. It has no Ollama, local model runtime or dependency on the legacy router.

## Runtime architecture

- Python 3.12, FastAPI and Pydantic Settings.
- Independent Gemini, OpenAI and Anthropic adapters using official SDKs.
- Provider/model IDs, fallback order, per-model token limits and prices are environment-configurable.
- Redis-backed organization rate limits; process-local limiting is development-only.
- Timestamped HMAC tenant signatures plus a server-to-server API key.
- Provider-specific error normalization, bounded retries, Retry-After handling and per-process circuit breakers.
- Prometheus-compatible aggregate metrics.
- Docker and Railway deployment support.

## API

- `GET /health`: public liveness.
- `GET /ready`: readiness summary.
- `GET /v1/providers` and `GET /v1/providers/health`.
- `GET /v1/metrics`: authenticated aggregate Prometheus metrics.
- `POST /v1/chat/completions`, `/estimate`, `/validate`.

All `/v1/*` routes require `X-Orchestrator-Key`. Tenant-scoped routes additionally require `X-Tenant-Timestamp` and `X-Tenant-Signature`. See `docs/INTEGRATION_WHAPPNUS.md`.

## Configuration

See `.env.example`. Production requires `ORCHESTRATOR_API_KEY`, `TENANT_SIGNING_SECRET`, `REDIS_URL`, and at least one provider key. Provider prices are never guessed: `MODEL_PRICING_JSON` is empty by default and only estimates costs for explicitly configured rates. Per-model budgets use `MODEL_LIMITS_JSON`.

## Validation status

This branch is under active hardening. CI tests and Docker build are being expanded. Provider calls against real paid APIs and live multimodal payloads require valid credentials and separate acceptance tests. Text-only adapter behavior must not be mistaken for image/audio/PDF support.
