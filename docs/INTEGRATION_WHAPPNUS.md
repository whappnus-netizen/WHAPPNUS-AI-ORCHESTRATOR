# WHAPPNUS integration

The WHAPPNUS backend remains responsible for authentication, organization membership, agent instructions, conversation history, knowledge, commercial credits and WhatsApp delivery.

Call `POST /v1/chat/completions` server-to-server with `X-Orchestrator-Key`. Never expose this key to a browser or WhatsApp client.

Example body:

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

The organization identifier is correlation/tenant context, not an authorization claim. The caller must validate tenant access before making the request.
