# HTTP and Browser Interface Contract (planned)

This design expresses the clarified requirements as a minimal same-origin interface. It is a contract proposal for implementation, not an implemented or tested API. JSON payload schemas are in the neighboring `*-schema.json` files.

## Routes

| Method and path | Purpose | Response |
|---|---|---|
| `GET /` | Serve local browser UI and static assets. | HTML/CSS/JS; no source or results embedded in server-rendered templates. |
| `POST /api/analyze` | Analyze one submission. | One final analysis JSON object on success; otherwise one error envelope. |

No retry, cancellation, persistence, authentication, accounts, batch endpoint, or CORS API is included.

## Analyze request

`Content-Type: application/json`; body conforms to [analysis-request.schema.json](analysis-request.schema.json).

```json
{"source_code":"print('example')\n"}
```

The request object has exactly one required string field `source_code`. Enforce an **independent maximum raw HTTP JSON entity size of 600,128 bytes** before JSON decoding. The six-times calculation accommodates worst-case JSON escaping of a source string whose decoded UTF-8 encoding is 100,000 bytes, with a small allowance for the compact JSON object structure. It does not bound arbitrary JSON whitespace: JSON permits arbitrary whitespace, so this raw entity cap may reject an otherwise valid source submission if its JSON representation contains excessive whitespace. The application's browser client MUST send compact JSON without unnecessary whitespace. After JSON decoding, reject empty/whitespace-only source, `source_code` UTF-8 encoding over **100,000 bytes**, or more than **2,000 addressable logical lines** before provider I/O. Accept syntactically incomplete but non-empty Python as text. The application must not execute it.

Measure the decoded source with its UTF-8 encoding after JSON parsing; do not use the raw JSON entity size as the source-byte count. Retain the decoded source string without normalization. Line counting recognizes LF, CRLF as one terminator, and CR; a final terminator does not add a line.

## Success response

HTTP success response is exactly one JSON object conforming to [analysis-result.schema.json](analysis-result.schema.json). It contains the app-enriched final result, not raw provider JSON. For every finding, enforce `line_end >= line_start` and `line_end <= metadata.source_line_count` using the submitted source's addressable logical line count. `overall_assessment` is exactly `no_findings` if and only if `findings` is empty; otherwise it is exactly `findings_present`. Validate `metadata.analysis_timestamp` using an enabled JSON Schema date-time `FormatChecker`. Success with no findings is distinguishable from every error response.

## Failure response

Failure response is exactly one JSON object conforming to [error-response.schema.json](error-response.schema.json). Proposed HTTP mapping for implementation review:

| `error_code` | Proposed HTTP status | Meaning |
|---|---:|---|
| `invalid_input` | 400 | Request is malformed, empty, or exceeds an input limit. |
| `configuration_failure` | 503 | Provider credentials/policy configuration is absent or fails the privacy gate; no source is transmitted. |
| `provider_failure` | 502 | Provider is unavailable, times out, rate-limits, or reports failure. |
| `invalid_ai_response` | 502 | Provider response is malformed, duplicate-keyed, schema-invalid, or violates source-dependent invariants. |

The proposed status mapping does not alter the spec's required error codes or payload. Messages are fixed/sanitized; raw exceptions and provider bodies are never returned. The UI displays only the envelope's safe `message` as text.

## Security and privacy behavior

- Serve and accept requests only on loopback. Reject unexpected Host/Origin values; disable CORS; require same-origin browser request. Apply CSRF defenses appropriate to cookie-free local operation and test them.
- Provider credentials are server-side environment variables and only enter the provider authentication channel. Never place them in UI assets, query strings, prompts, errors, logs or telemetry.
- Do not log request/response bodies, source, findings, evidence, raw provider response or credentials. Do not persist or cache analysis state. Disable service-worker/browser durable storage.
- Do not transmit source until endpoint-specific processing-only/no-retention/no-training evidence passes configuration review.
- Validate evidence by exact comparison against the unchanged decoded source slice covering the cited inclusive lines, retaining line terminators exactly as submitted. Do not normalize line endings, trim whitespace, or apply Unicode normalization before comparison.
- Use response headers including a restrictive Content Security Policy, `X-Content-Type-Options: nosniff`, and a restrictive referrer policy. No untrusted text is interpreted as markup or navigable link.

## Browser interaction

The user enters source and submits once. While pending, the interface shows progress and does not offer retry/cancel controls. On success, render source and validated findings as inert text and associate findings with their line ranges. A result containing findings starts visibly `pending`; only explicit review action changes it to `reviewed` in the current browser memory. Reload/close clears source, results and review state. A zero-finding success is displayed as “no findings identified,” distinct from failure.
