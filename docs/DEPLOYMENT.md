# Railway deployment

The production project runs the orchestrator service and a private Redis service in the same Railway environment. The app uses Dockerfile builds and binds to Railway's dynamic `PORT`; `/health` is the container/Railway liveness endpoint.

Required production variables on the orchestrator service:
- `APP_ENV=production`
- `REDIS_URL=${{Redis.REDIS_URL}}` (Railway service reference; do not copy the Redis password into source control)
- `ORCHESTRATOR_API_KEY` (server-to-server secret)
- `TENANT_SIGNING_SECRET` (separate HMAC secret)
- At least one provider key: `GEMINI_API_KEY`, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

Optional variables configure provider model IDs, per-model token budgets, pricing, retries and tenant quotas. Set secrets in Railway Variables only; never commit them.

The app will start without provider credentials for diagnostics, but it is not ready to serve completions until authentication secrets and at least one provider credential are configured. The WHAPPNUS backend must implement the signed tenant headers documented in `INTEGRATION_WHAPPNUS.md` before chat routes can be used.
