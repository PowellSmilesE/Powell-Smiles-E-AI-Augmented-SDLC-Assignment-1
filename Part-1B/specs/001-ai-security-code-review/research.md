# Research: AI-Powered Security Code Review Assistant

**Date**: 2026-11-05
**Feature**: [spec.md](spec.md)

This research supports the technical plan. Framework/tool choices below are planning recommendations, not additional product requirements or provider approvals. No code, provider account, or evaluation dataset was created.

## Decisions

### Local web architecture

**Decision**: Use one Python web process that serves a static same-origin browser interface and a small JSON API. FastAPI is the proposed HTTP framework; deploy only on loopback. Use plain HTML/CSS/JavaScript to avoid a separate frontend build system.

**Rationale**: Matches the clarified local browser, single-analyst use. One origin avoids unnecessary cross-origin API configuration. Loopback binding and strict Host/Origin checks are needed because no account/authentication flow exists; “local” does not itself prevent cross-origin browser requests or local network exposure.

**Alternatives considered**: Desktop GUI (not the clarified interface); separately hosted frontend/backend (unneeded complexity and wider attack surface); Flask (also viable but offers fewer integrated request/response schema conveniences than FastAPI); SPA framework (unnecessary for a single form and result panel).

### Strict typed boundaries and schemas

**Decision**: Use strict validation models (Pydantic v2 is the proposed Python boundary library), with unknown fields forbidden. Publish JSON Schema contracts and keep semantic checks in explicit validators.

**Rationale**: Strict mode avoids silently coercing a model's wrong primitive type into a valid value. JSON Schema is useful for independent contract checks, but exact evidence-in-source and assessment consistency require application-level cross-field validation. The [`jsonschema` documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/) describes validator behavior and type checking.

**Alternatives considered**: Hand-written validation only (risk of duplicated/missed field rules); schema-only validation (cannot express every source-dependent invariant conveniently); permissive coercion (inconsistent with rejecting invalid AI output).

### Duplicate-key rejection

**Decision**: Parse provider JSON with a decoder hook that sees ordered key/value pairs for every JSON object and raises on a repeated key; also reject non-standard constants and trailing extra documents before schema validation.

**Rationale**: Standard decoder hooks expose each object’s ordered pairs; Python documents `object_pairs_hook` and `parse_constant` for this use ([Python `json` documentation](https://docs.python.org/3/library/json.html)). Rejection avoids differing interpretations of ambiguous output. Evaluation validation must independently implement the same contract without importing the application parser.

**Alternatives considered**: Accept first/last duplicate (parser-dependent and ambiguous); schema validation after ordinary dict decoding (duplicate evidence already lost); third-party parser (not needed unless performance/security review identifies a limitation).

### Provider is deliberately unselected

**Decision**: No AI provider/model is chosen. Provider selection is a blocking pre-transmission policy gate: require enforceable processing-only use, no post-request source retention, and no training on submitted source for the exact endpoint, account tier, features, and configuration.

**Rationale**: The approved privacy policy is stricter than a generic “not used for training” statement. Current official materials show provider-specific retention controls/conditions that must be evaluated for the actual configuration. OpenAI documents configurable data controls and endpoint-specific behavior ([OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)); Anthropic describes a standard API retention period and an approved Zero Data Retention arrangement ([Anthropic API data retention](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organizations-data)). The Gemini ZDR page could not be independently opened in this research session because it redirects to an inaccessible page; it is not treated as verified evidence. None of these sources establishes that an unselected account/configuration already satisfies this project’s no-retention rule. Confirm current terms and retain configuration/attestation evidence at the time of selection.

**Alternatives considered**: Select a popular hosted provider now (cannot guarantee the required retention policy without endpoint-specific proof); weaken retention policy (would contradict approved clarification); local model (may avoid external provider retention but introduces model hosting/runtime, hardware, model licensing and operational risks, and is not automatically approved as the intended AI service).

### Prompt injection and tool isolation

**Decision**: Treat source as untrusted content, delimit it, place it under a fixed analysis instruction, expose no tools/actions/secrets to the model, and validate output. Preserve residual model-influence risk in documentation and mandatory adversarial evaluation.

**Rationale**: OWASP describes prompt injection as malicious instructions in input that can override intended model behavior and notes that prompts alone cannot reliably distinguish instructions from data ([OWASP GenAI glossary](https://genai.owasp.org/glossary/prompt-injection/)). Therefore, prompt wording is defense-in-depth, not a formal guarantee. Least privilege, no tools, no secret context, strict output checks, and human review reduce consequences.

**Alternatives considered**: Rely solely on a delimiter/system prompt (not a reliable security boundary); allow agent tools (out of scope and expands impact); claim complete prevention (unsupported).

### Inert browser rendering

**Decision**: Render submitted source and all model-generated text using DOM text APIs; never interpret it as HTML/Markdown or turn model-provided links into navigation. Apply a restrictive CSP and test hostile content in a real browser.

**Rationale**: OWASP’s XSS guidance emphasizes context-appropriate handling and warns about unsafe DOM sinks. Text-only output removes the need to support HTML from untrusted data ([OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet)).

**Alternatives considered**: Markdown rendering (adds active link/HTML handling concerns); HTML sanitization while preserving markup (unneeded capability and sanitizer risk); direct `innerHTML` rendering (unsafe for untrusted content).

### Quality and test toolchain

**Decision**: pytest for automated tests; API and provider contracts tested without live provider calls; Playwright for browser behavior; Ruff for lint/format; Bandit for Python security patterns; dependency audit (pip-audit or equivalent) at verification.

**Rationale**: This keeps fast deterministic checks in the normal loop and browser-specific unsafe rendering checks at the UI boundary. Ruff supports lint and formatting from one CLI ([Ruff docs](https://docs.astral.sh/ruff/)); Bandit scans Python ASTs for common security issues ([Bandit docs](https://bandit.readthedocs.io/en/latest/)). Static analysis does not prove security and findings must be reviewed rather than suppressed reflexively.

**Alternatives considered**: Lint only (misses security-specific patterns); Bandit only (misses style/logic/contract behavior); live provider-dependent test suite (not reproducible and sends source outside controlled mocks); browser-only tests (insufficient unit/contract precision).

### Independent evaluator

**Decision**: Implement the future harness as a separate top-level package with separate schemas, decoder/validators and scoring code. It consumes application API outputs but does not import application validation helpers.

**Rationale**: Independence reduces the chance the implementation and its verifier share the same parsing/validation defect. The harness follows the specification’s exact one-to-one matching, IoU, reviewer and denominator rules and the approved 85% threshold, with mandatory gates outside the weighted score.

**Alternatives considered**: Reuse application validators (not independent); use model self-evaluation as final score (not reproducible human-labelled evaluation); store dataset alongside app fixtures (raises risk of accidental exposure/leakage into model requests).

## Decisions intentionally left pending

- AI provider/model/endpoint and proof for no post-request retention/no training.
- Final packaging/deployment details, beyond a local loopback application.
- Human-owned constitution ratification; the current constitution file is a template, not an approved policy.
- Dataset authoring and evaluation execution (future phase; no data created here).

## Source freshness

Policy pages and software documentation can change. Provider policy evidence must be rechecked against the actual selected endpoint and settings before any source is transmitted. This research records references consulted on 2026-11-05 and does not assert provider compliance or test outcomes.
