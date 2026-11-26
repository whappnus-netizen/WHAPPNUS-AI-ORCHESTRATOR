# Providers

Configure credentials and model identifiers through environment variables. Gemini exposes independent Flash and Advanced IDs. OpenAI and Anthropic model IDs are independently configurable. Provider selection is capability-aware: a provider is only considered when it supports every modality present in the request.

## Implemented input capabilities

- Text: Gemini, OpenAI and Anthropic.
- Images: all three adapters; JPEG, PNG, WebP and GIF, base64, maximum 5 MB per image.
- Audio: Gemini adapter; MPEG, WAV, OGG, MP4, WebM and FLAC, base64, maximum 15 MB per audio part.
- PDF documents: Gemini and Anthropic adapters; base64, maximum 10 MB per document.
- Payloads are translated into provider-native content blocks. Binary data is not written to logs.
- Schema validation and adapter payload translation are covered by automated tests. This is not yet a live paid-provider acceptance test; real API calls still require provider credentials.

## Not yet implemented

Video, remote URL fetching, audio output, speech generation and provider-native tool calling are not currently supported.

## Model configuration

Use `GEMINI_FLASH_MODEL`, `GEMINI_ADVANCED_MODEL`, `OPENAI_MODEL` and `ANTHROPIC_MODEL` to swap model IDs independently. `MODEL_LIMITS_JSON` can override input/output budgets per model using keys such as `gemini:gemini-2.5-flash`. `MODEL_PRICING_JSON` accepts explicitly maintained input/output rates per million tokens; no provider prices are hardcoded or guessed.
