# Architecture

WHAPPNUS AI ORCHESTRATOR is a stateless service. WHAPPNUS remains the system of record for tenants, users, conversations, knowledge, billing and WhatsApp delivery.

The foundation separates API contracts, deterministic routing, provider adapters and security/observability. Credentials stay server-side.

Implemented foundation: FastAPI/OpenAPI, Gemini/OpenAI/Anthropic adapter boundaries, configurable model IDs, deterministic task tier selection, provider fallback order and server-to-server API key authentication.

Not yet implemented: distributed rate limiting, detailed provider error taxonomy, circuit breakers, token-aware context compaction, cost catalogue, metrics export and full multimodal payload contracts.
