# WHAPPNUS integration

WHAPPNUS remains the system of record for users, organization membership, agents, conversation history, knowledge, credits, CRM and WhatsApp delivery. This service only performs provider orchestration.

Every versioned API request must include:
- `X-Orchestrator-Key`: server-to-server API key; never expose it in browsers.
- `X-Tenant-Timestamp`: Unix timestamp in seconds.
- `X-Tenant-Nonce`: a cryptographically random one-time value of 16–128 characters.
- `X-Tenant-Signature`: lowercase hex HMAC-SHA256 of `{organization_id}:{timestamp}:{nonce}`, using the shared `TENANT_SIGNING_SECRET`.

The orchestrator rejects signatures older than five minutes, rejects reused nonces through Redis, and applies an atomic Redis-backed fixed-window quota per organization. The WHAPPNUS backend must authenticate the user and verify organization membership before signing a request.

Example request body:

```json
{
  "request_id": "req-123",
  "organization_id": "org-456",
  "conversation_id": "conv-789",
  "task_type": "customer_support",
  "system_instructions": "Responde em português de Angola.",
  "messages": [{"role": "user", "content": "Quais são os vossos horários?"}],
  "max_tokens": 500,
  "temperature": 0.3
}
```


## Routing and time budget

The default Gemini tier is `gemini-3.8-flash`; requests classified as complex use `gemini-3.1-pro-preview` unless the backend explicitly selects another configured model. The overall request deadline defaults to 22 seconds (`TOTAL_REQUEST_TIMEOUT_SECONDS`), even though the per-provider attempt timeout defaults to 45 seconds. This keeps provider retries and fallback inside the WHAPPNUS backend's 25-second request budget and the Netlify worker's 28-second callback budget. The Orchestrator returns a retryable deadline error when the total budget expires; the backend may then place the generation on its durable queue.

Keep the API key and tenant signing secret in backend secret storage only. Never send either secret to a browser, WhatsApp client or customer.
