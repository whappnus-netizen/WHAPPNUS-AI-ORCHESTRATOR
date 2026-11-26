# Railway deployment

Deploy using the Dockerfile. Railway supplies `PORT`; the container binds to it. Set `ORCHESTRATOR_API_KEY` and the enabled provider credentials in Railway Variables.

No persistent volume or local model download is required. Health check: `/health`. `/ready` reports degraded when no provider credentials are configured.
