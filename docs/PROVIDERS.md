# Providers

Configure credentials and model identifiers through environment variables. Gemini exposes independent Flash and Advanced IDs. OpenAI and Anthropic model IDs are independently configurable. The selected provider and model can be changed without changing the orchestration contract.

## Implemented capabilities

- Text input: all three adapters.
- Image input: all three adapters accept validated base64 image parts for JPEG, PNG, WebP and GIF, up to 5 MB per image.
- Provider SDKs receive native image content blocks; image bytes are never logged.
- The image contract is covered by adapter translation tests. Live paid-provider image calls still require credentials and must be acceptance-tested in the provider accounts.

## Not yet implemented

Audio, video, PDF/document extraction, URL fetching and provider-native tool calling are not currently advertised as supported. Do not send these payloads as if they were supported.

## Model configuration

Use `GEMINI_FLASH_MODEL`, `GEMINI_ADVANCED_MODEL`, `OPENAI_MODEL` and `ANTHROPIC_MODEL` to swap model IDs independently. `MODEL_LIMITS_JSON` can override input/output budgets per model using keys such as `gemini:gemini-2.5-flash`. `MODEL_PRICING_JSON` accepts explicitly maintained input/output rates per million tokens; no provider prices are hardcoded or guessed.
