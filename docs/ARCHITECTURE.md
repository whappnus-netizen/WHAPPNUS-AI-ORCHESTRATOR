# Architecture

WHAPPNUS AI ORCHESTRATOR is a stateless, independent generation service. WHAPPNUS remains the system of record for users, tenants, conversations, agents, knowledge, CRM, billing and WhatsApp delivery.

The service has independent provider adapters for Gemini, OpenAI and Anthropic; deterministic task classification; capability-aware model routing; bounded retries; Retry-After handling; fallback; and per-process circuit breakers. Model identifiers, model budgets, fallback order and explicit pricing rates are environment-configurable.

Redis provides atomic organization-scoped rate limits and one-time HMAC nonce storage shared across app replicas. Provider metrics are exported in Prometheus format without organization labels. The Railway project contains separate app and Redis services.

Supported request modalities currently include text for all providers, images for all three, audio for Gemini, and PDF documents for Gemini/Anthropic. Unsupported modality/provider combinations are excluded by routing.

No Ollama, local inference runtime, local model download or dependency on the legacy router is part of this service.
