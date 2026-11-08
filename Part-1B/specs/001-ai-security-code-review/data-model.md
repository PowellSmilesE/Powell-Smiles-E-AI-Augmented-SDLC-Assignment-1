# Data Model: AI-Powered Security Code Review Assistant

**Feature**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

All request, response, and review entities are transient. The application has no persistent store. JSON contracts are in [contracts/](contracts/).

## Analysis Request

| Field | Type | Origin | Validation |
|---|---|---|---|
| `source_code` | string | Browser request | After JSON decoding, required; non-empty after whitespace check; UTF-8 encoding <=100,000 bytes; <=2,000 addressable logical lines. Syntactic incompleteness is accepted. |

The source remains untrusted data, is never executed, and exists only in request/browser memory. Logical line terminators are LF, CRLF (one terminator), and CR; a trailing terminator does not add another addressable line. Keep the decoded source string unchanged for all later range and evidence checks; compare evidence with the exact source slice spanning the reported inclusive lines, retaining line terminators. Do not normalize line endings, whitespace, Unicode, or other source characters.

## AI-generated Response (untrusted until validated)

| Field | Type | Owner | Validation |
|---|---|---|---|
| `analysis_summary` | string | Model | Required non-empty. |
| `findings` | array[AI Finding] | Model | Required; empty allowed. |

### AI Finding

| Field | Type | Owner | Validation |
|---|---|---|---|
| `vulnerability_category` | string | Model | One of exact categories in FR-010; `Other` must denote a relevant Python weakness outside named categories. |
| `title` | string | Model | Non-empty. |
| `severity` | string | Model | `Critical`, `High`, `Medium`, `Low`, or `Informational`. |
| `confidence` | finite number | Model | Inclusive [0.0, 1.0], bool prohibited; model-reported only, not calibrated. |
| `line_start` | integer | Model | 1-based inclusive, >=1 and <= source line count. |
| `line_end` | integer | Model | 1-based inclusive, >= line_start and <= source line count; enforce `line_end >= line_start` and the source-line-count bound as cross-field invariants. |
| `evidence` | string | Model | Non-empty exact excerpt found verbatim within the reported inclusive source range, compared against unchanged decoded source text. |
| `explanation` | string | Model | Non-empty. |
| `remediation` | string | Model | Non-empty. |

The raw model JSON must have exactly one top-level object and no duplicate keys at any object depth. Unknown/missing fields, invalid primitive types, invalid constants, trailing data and semantic invariant failures reject the response. The model cannot supply application-owned fields.

## Final Application Analysis Result

| Field | Type | Owner | Validation |
|---|---|---|---|
| `schema_version` | string | Application | Exactly `1.0`. |
| `analysis_summary` | string | Model then application validation | Validated, non-empty and consistent with findings. |
| `findings` | array[Final Finding] | Model fields + application ID | May be empty; each finding meets the final finding contract. |
| `overall_assessment` | enum | Application-derived | Exactly `no_findings` when `findings` is empty; exactly `findings_present` when `findings` contains one or more findings. Enforce both directions as a cross-field invariant. |
| `metadata` | Metadata | Application | Must not include source or credentials. |

### Final Finding

Contains all AI Finding fields plus:

| Field | Type | Owner | Validation |
|---|---|---|---|
| `finding_id` | string | Application | Non-empty, unique within a result. Identifier format remains intentionally unspecified by the spec. |

### Metadata

| Field | Type | Owner | Validation |
|---|---|---|---|
| `analysis_id` | string | Application | Non-empty; generation policy unspecified. |
| `analysis_timestamp` | string | Application | RFC 3339 with explicit UTC offset; validate the final JSON Schema `date-time` format with an enabled `FormatChecker` and installed/registered date-time implementation (use `jsonschema[format]`), not annotation-only format handling. |
| `source_language` | string | Application | Exactly `python`. |
| `source_line_count` | integer | Application | >=1 addressable logical lines for accepted non-empty source. |
| `model_identifier` | string or null | Application/provider adapter | Provider-neutral identifier if available; never credentials. |
| `processing_time_ms` | integer | Application | >=0. |

The application validates the final object after adding its fields. A failed analysis is never represented by `findings: []` success.

## Error Response

Exactly `{error_code, message}`; distinct from success. `error_code` is `invalid_input`, `provider_failure`, `configuration_failure`, or `invalid_ai_response`; message is safe, non-empty and excludes source, credentials and internal secrets. HTTP status mapping remains documented by the HTTP contract as an implementation convention; the JSON contract is authoritative for payload semantics.

## Human Review State

Transient browser state associated with the currently displayed result:

| Field | Type | Values / lifecycle |
|---|---|---|
| `analysis_id` | string | Identifies the visible response only. |
| `review_status` | enum | `pending` initially for a result with findings; `reviewed` only after explicit analyst action. |

Not persisted, not part of the result JSON, and cleared on reload/close. A result with no findings is shown as no findings, not as an unreviewed security approval.

## Future Evaluation Case and Run

Contract shapes are described by `contracts/evaluation-case.schema.json`; no instances/data are included.

- **Case**: stable `case_id`, bounded source, and a list of expected findings (empty means expected clean). Expected findings have stable IDs, category, severity, inclusive source ranges and reviewer rubric annotations. Dataset-level metadata records coverage declarations and reviewer sign-off.
- **Run row**: exactly one outcome per declared case ID; structural, invariant/property and semantic statuses; component/case scores; errors/unscored reason; mandatory gate evidence references.
- **Run summary**: declared case count/denominator, coverage, threshold 85%, semantic mean, mandatory gate list, and exactly one aggregate PASS/FAIL.

Every declared ID is in the denominator. Failed/unscored cases score zero and force FAIL. The harness must be independent from application validators and preserve each case row.
