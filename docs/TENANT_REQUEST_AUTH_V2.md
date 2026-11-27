# Tenant request authentication v2

## Contract

The caller serializes the JSON body once, computes SHA-256 over the exact UTF-8 bytes, and signs:

POST:/v1/chat/completions:{organization_id}:{timestamp}:{nonce}:{body_sha256}

The body digest is sent in X-Tenant-Body-SHA256. The Orchestrator recomputes the digest from the raw HTTP request body and compares it before verifying the HMAC, consuming the nonce or calling a provider. The HMAC binds the organization, HTTP method, endpoint path, timestamp, nonce and body hash.

## Compatibility rollout

TENANT_BODY_SIGNATURE_REQUIRED defaults to false so existing v1 callers remain compatible during a staged rollout.

- A request with X-Tenant-Body-SHA256 must match the exact raw body and use the v2 HMAC.
- A request without the body hash is accepted only while the enforcement flag is false.
- An incorrect or malformed body hash is always rejected.
- The same verification applies to /v1/chat/completions, /v1/chat/estimate and /v1/chat/validate.

Deploy in this order:

1. Deploy the Orchestrator with TENANT_BODY_SIGNATURE_REQUIRED=false.
2. Deploy the backend v2 caller.
3. Run the live smoke tests and verify that all callers send X-Tenant-Body-SHA256.
4. Set TENANT_BODY_SIGNATURE_REQUIRED=true in Railway and redeploy.
5. Remove legacy v1 callers and scripts.

Never enable enforcement before every caller has moved to v2.
