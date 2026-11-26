# API

## Public
- `GET /health`: process liveness.
- `GET /ready`: configured-provider readiness summary.

## Authenticated
All `/v1/*` routes require `X-Orchestrator-Key`.
Tenant-scoped routes (`/v1/chat/*`) additionally require:
- `X-Tenant-Timestamp`: Unix timestamp seconds.
- `X-Tenant-Nonce`: cryptographically random, single-use value.
- `X-Tenant-Signature`: HMAC-SHA256 over `organization_id:timestamp:nonce`.

## Routes
- `GET /v1/providers`: configured models and capabilities.
- `GET /v1/providers/health`: credential/configuration status (not a billable provider probe).
- `GET /v1/metrics`: aggregate Prometheus metrics.
- `POST /v1/chat/completions`: normalized generation with provider fallback.
- `POST /v1/chat/estimate`: rough token and optional configured-price estimate. Accepts `preferred_provider` and `preferred_model`.
- `POST /v1/chat/validate`: request contract validation.

## Multimodal content parts

A message's `content` can be a string or an array of typed parts. Supported types are `text`, `image`, `audio` and `document`. Binary parts carry base64 data and a MIME type. Routing is capability-aware: audio goes to Gemini; PDF documents go to Gemini or Anthropic; images can go to all three providers. Unsupported modality/provider combinations are excluded before generation.

Provider-specific tokenization remains authoritative. Estimates use coarse modality budgets and must not be used for billing settlement.
