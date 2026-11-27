# Providers

Configure credentials and model identifiers through environment variables. Gemini exposes independently configurable Flash and Advanced IDs. OpenAI and Anthropic model IDs are independently configurable. Provider selection is capability-aware: a provider is considered only when it supports every modality present in the request.

The default Gemini model for new installations is the stable `gemini-3.8-flash`. Gemini 2.5 models remain configurable for projects that retain access, but Google limits new-project access to those models.

## Implemented input capabilities

- Text: Gemini, OpenAI and Anthropic.
- Images: all three adapters; JPEG, PNG, WebP and GIF, base64, maximum 5 MB per image.
- Audio: Gemini adapter; MPEG, WAV, OGG, MP4, WebM and FLAC, base64, maximum 15 MB per audio part.
- PDF documents: Gemini and Anthropic adapters; base64, maximum 10 MB per document.
- Payloads are translated into provider-native content blocks. Binary data is not written to logs.
- Schema validation and adapter payload translation are covered by automated tests. This is not a live paid-provider acceptance test; real API calls still require provider credentials.

## Provider error and fallback policy

- Rate limits and transient network/server errors are retryable with bounded backoff.
- Model-not-found and provider-specific request errors are not retried against the same provider, but may fall through to another configured provider.
- Explicitly requested models that are not in the selected provider's advertised allowlist fail clearly with `MODEL_NOT_CONFIGURED`; they are not silently redirected.
- Safe provider status, error type/code and request IDs are retained for diagnostics. API keys, request bodies and media payloads are not logged.

## Not yet implemented

Video, remote URL fetching, audio output, speech generation and provider-native tool calling are not currently supported.

## Model configuration

Use `GEMINI_FLASH_MODEL`, `GEMINI_ADVANCED_MODEL`, `OPENAI_MODEL` and `ANTHROPIC_MODEL` to swap model IDs independently. `MODEL_LIMITS_JSON` can override input/output budgets per model using keys such as `gemini:gemini-3.8-flash`. `MODEL_PRICING_JSON` accepts explicitly maintained input/output rates per million tokens; no provider prices are hardcoded or guessed.
