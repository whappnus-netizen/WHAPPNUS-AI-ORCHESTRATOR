# WHAPPNUS provider routing policy

## Current operating mode

The Orchestrator uses Gemini 3.1 Flash Lite (gemini-3.1-flash-lite) as the primary generation model for both normal customer support and complex tasks.

This primary model is controlled by GEMINI_PRIMARY_MODEL. It intentionally does not consume the legacy GEMINI_FLASH_MODEL environment variable, which may contain an obsolete or temporarily unavailable model ID.

Gemini Pro remains prepared but disabled by default:

- GEMINI_ADVANCED_MODEL=gemini-3.1-pro-preview
- GEMINI_ADVANCED_ENABLED=false

When advanced routing is disabled, both classifier-selected advanced tasks and explicit legacy Pro model pins are routed to the primary Flash Lite model. When advanced routing is enabled, complex tasks may use the configured advanced model.

## Fallback policy

Fallback is opt-in, not inferred from the presence of provider credentials.

- ENABLE_FALLBACK=true allows the Orchestrator to use the explicit provider allowlist.
- FALLBACK_PROVIDER_ORDER is an ordered, comma-separated allowlist, for example openai,anthropic.
- The default allowlist is empty. Do not add a provider until its credentials, quota/billing, model access and generation path have been verified.
- The requested provider is always tried first. Only allowlisted fallback providers are considered afterwards.

This prevents configured-but-unfunded providers from receiving traffic automatically.

## Retry policy

- Transient provider failures retain the bounded general retry policy (MAX_RETRIES).
- HTTP 429 rate-limit errors use the smaller MAX_RATE_LIMIT_RETRIES budget (default: one retry).
- Explicit quota exhaustion, zero Free Tier quota, insufficient provider credits and hard billing quota errors are classified as PROVIDER_QUOTA_EXHAUSTED and are not retried.
- A quota/billing failure may fall back only to an explicitly allowlisted provider.
- The global Orchestrator deadline remains authoritative; retries never extend it.

## Future activation

After validating Gemini Pro access and/or a secondary provider:

1. Confirm successful direct API generation with the exact production project and key.
2. Set GEMINI_ADVANCED_ENABLED=true only when Pro quota/billing is operational.
3. Add secondary providers to FALLBACK_PROVIDER_ORDER only after a real generation test succeeds.
4. Run the simple, complex, multimodal, fallback and tenant-isolation regression suites.
5. Roll out through a controlled deployment and verify the live /v1/providers model list.

## Required regression checks

- Simple and complex tasks use Flash Lite while advanced mode is disabled.
- Complex tasks use Pro only when advanced mode is explicitly enabled.
- Legacy Flash and Pro agent pins are normalized safely.
- No provider is attempted as fallback unless it appears in the explicit allowlist.
- Zero quota and insufficient credits do not trigger retries.
- Standard 429 rate limits have a bounded retry budget.


## Tenant request integrity

The Orchestrator supports HMAC v2, which signs method, path, organization ID, timestamp, nonce and SHA-256 of the exact raw request body. The body hash is verified before nonce consumption and provider invocation. Legacy v1 remains temporarily accepted while TENANT_BODY_SIGNATURE_REQUIRED=false; set the flag to true only after all backend callers have moved to v2. See docs/TENANT_REQUEST_AUTH_V2.md.
