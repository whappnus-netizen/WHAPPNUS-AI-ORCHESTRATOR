# API

All `/v1/*` routes require `X-Orchestrator-Key`.

- `GET /health`: liveness
- `GET /ready`: configured-provider readiness summary
- `GET /v1/providers`: capabilities and configuration state
- `GET /v1/providers/health`: configuration health (not a billable live probe)
- `POST /v1/chat/completions`: normalized generation
- `POST /v1/chat/estimate`: approximate character-based token estimate
- `POST /v1/chat/validate`: schema validation

OpenAPI is available at `/docs`.
