# Security

- Never commit `.env` or provider secrets.
- Versioned API endpoints require a server-to-server key.
- Key comparisons use constant-time comparison.
- Provider keys are never returned by API routes.
- The organization identifier is trusted only behind the authenticated WHAPPNUS backend boundary. Do not expose this service directly to browsers or end users.
- Production still requires distributed rate limiting, tenant-scoped quotas, request-size limits, secret rotation and security review.
