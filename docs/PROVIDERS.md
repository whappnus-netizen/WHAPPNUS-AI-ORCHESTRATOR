# Providers

Configure provider credentials and model IDs through environment variables. Missing credentials mark a provider unavailable; no success is simulated.

Gemini exposes independent Flash and Advanced model IDs. OpenAI and Anthropic model IDs are configurable. The values in `.env.example` are defaults and must be checked against current provider availability before production.

The current adapter contract supports text only. Multimodal capabilities are deliberately not advertised as implemented.
