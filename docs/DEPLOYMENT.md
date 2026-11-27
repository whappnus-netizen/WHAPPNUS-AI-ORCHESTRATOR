# Railway deployment

The production project runs the Orchestrator service and a private Redis service in the same Railway environment. The app uses Dockerfile builds and binds to Railway's dynamic `PORT`.

## Health and readiness

- `GET /health` is a liveness check: it confirms that the HTTP process is running.
- `GET /ready` is a readiness check: it requires at least one configured provider, working Redis for replay/rate-limit storage, and both server authentication secrets in production. It returns HTTP 503 while any required dependency is degraded.

Configure Railway's container healthcheck to use `/health`, not `/ready`, so a temporary upstream provider outage does not cause unnecessary container restarts.

## Required production variables

- `APP_ENV=production`
- `REDIS_URL=${{Redis.REDIS_URL}}` (Railway service reference; do not copy the Redis password into source control)
- `ORCHESTRATOR_API_KEY` (server-to-server secret)
- `TENANT_SIGNING_SECRET` (separate HMAC secret)
- At least one provider key: `GEMINI_API_KEY`, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

Optional variables configure provider model IDs, per-model token budgets, pricing, retries and tenant quotas. Set secrets in Railway Variables only; never commit them.

The app may start without provider credentials for diagnostics, but it is not ready to serve completions until authentication secrets, Redis and at least one provider credential are operational. The WHAPPNUS backend must implement the signed tenant headers documented in `INTEGRATION_WHAPPNUS.md` before chat routes can be used.
