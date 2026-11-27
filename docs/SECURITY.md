# Security

- Never commit .env files or provider credentials.
- Versioned API endpoints require a constant-time-compared server-to-server API key.
- Chat/estimate/validate requests require a timestamped HMAC signature bound to organization ID and a one-time nonce.
- Signatures expire after five minutes; Redis rejects nonce reuse.
- Redis-backed atomic counters enforce organization-scoped quotas across replicas. Production refuses chat requests without the shared Redis store.
- WHAPPNUS must authenticate the caller and verify organization membership before signing each request.
- Provider errors are normalized; raw SDK messages, credentials and binary payloads are not logged.
- Prometheus metrics are aggregate and do not label requests with organization IDs.
- Provider credentials, API key and tenant signing secret must be managed and rotated through Railway secret variables.
- The API must not be exposed directly to browsers or end users.
- Live provider calls and multimodal acceptance tests remain mandatory before production traffic.
