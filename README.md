# WHAPPNUS AI ORCHESTRATOR

Independent multi-provider orchestration service for WHAPPNUS. No Ollama, local model runtime or dependency on the legacy router.

## Stack and modules

- Python 3.12, FastAPI, Pydantic Settings.
- Official Gemini, OpenAI and Anthropic SDK adapters.
- Configurable provider/model IDs, per-model token budgets and fallback order.
- Capability-aware text/image/audio/PDF routing: images across all three providers, audio on Gemini, PDF on Gemini and Anthropic.
- Redis-backed organization quotas and one-time HMAC nonce protection.
- Provider-specific error normalization, bounded retries, Retry-After, fallback and circuit breakers.
- Configurable cost estimates; prices are never guessed.
- Prometheus metrics, Docker and Railway deployment support.

## API

- `GET /health`, `GET /ready`.
- `GET /v1/providers`, `GET /v1/providers/health`, `GET /v1/metrics`.
- `POST /v1/chat/completions`, `/estimate`, `/validate`.

All versioned routes require `X-Orchestrator-Key`. Tenant-scoped routes also require timestamp, nonce and HMAC signature headers. See `docs/INTEGRATION_WHAPPNUS.md`.

## Production gate

The code and Docker image are being validated in CI. The service is not approved for customer traffic until Railway secrets are configured, WHAPPNUS implements the signed tenant contract, and live smoke tests are run against the selected provider accounts. SDK payload tests are not the same as paid live-provider acceptance tests.
