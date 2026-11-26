# Security

- Never commit .env files or provider credentials.
- Versioned API endpoints require a constant-time-compared server-to-server API key.
- Chat/estimate/validate requests require a timestamped HMAC signature bound to the organization ID.
- HMAC signatures expire after five minutes; WHAPPNUS must authorize membership before signing.
- Organization rate limits use atomic Redis counters shared across replicas. Production refuses to run chat requests without Redis.
- Provider errors are normalized and do not expose raw SDK messages or secrets.
- Metrics are aggregate and do not label requests with organization IDs.
- Provider credentials and tenant signing secrets must be rotated through Railway secret variables.
- The API must not be exposed directly to browsers or end users.
