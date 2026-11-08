# Feature Specification: AI-Powered Security Code Review Assistant

**Feature Branch**: `001-ai-security-code-review`

**Created**: 2026-11-05

**Status**: Draft — for human review

**Input**: User description: Create an AI-powered application that accepts Python source code, analyses it for security vulnerabilities, returns structured findings, and displays them for human review.

## Clarifications

### Session 2026-11-05

- Q: Should the initial interface be a local browser app without user accounts, a browser app with authentication, a desktop app, or another form? → A: Local browser app without user accounts; simplest single-analyst setup with no identity/access-control flow.
- Q: What maximum source size and line count should be accepted, and should non-empty syntactically incomplete Python be analysed as text or rejected? → A: Accept up to 100 KB (100,000 UTF-8 bytes) and 2,000 addressable logical lines; analyse syntactically incomplete non-empty Python as text.
- Q: Do you approve the proposed semantic scoring rubric and 85% acceptance threshold for future evaluation, or should either remain provisional or change? → A: Approve the current semantic scoring rubric and 85% acceptance threshold; evaluation may use 85% once the dataset exists.
- Q: May an external AI provider retain submitted source after processing, and what retention and model-training policy is acceptable? → A: Provider may process source for the request only; no retention after the request and no model training on submitted source.
- Q: Should the application persist analysis findings and evidence containing source excerpts, or keep all results session-only? → A: Keep findings and evidence session-only; persist no analysis results.
- Q: Should each finding's 0–1 confidence be a model-reported score only, or must the system demonstrate that the score is calibrated against observed correctness? → A: Model-reported score only; require a finite value from 0 to 1, with no calibration claim.
- Q: Must the future evaluation dataset include at least one expected finding classified as `Other`, beyond the nine named vulnerability categories? → A: Require at least one `Other` finding; it may share a case with another finding.
- Q: Must a finding's `evidence` be an exact excerpt from the submitted source, or may it be a semantically related description grounded in the reported lines? → A: Require an exact source excerpt appearing verbatim within the reported line range.
- Q: Should input, provider, and invalid-response failures use a separate structured JSON error envelope, or should errors appear only as messages in the browser interface? → A: Use a separate structured JSON error envelope for failures and display its message in the UI.
- Q: Should analysis support automatic retry, user-triggered retry, and cancellation while a request is in progress? → A: No retries or cancellation; the analyst may submit again after failure or wait for the current request to finish.
- Q: Are the current qualitative descriptions for Critical, High, Medium, Low, and Informational sufficient, or should severity follow a formal scoring standard? → A: Keep the current qualitative severity descriptions; no formal scoring standard.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Submit code and receive a security analysis (Priority: P1)

As a security analyst, I submit Python source code and receive findings that identify potential security weaknesses, their severity, confidence, source locations, explanations, and recommended remediation.

**Why this priority**: This is the assistant's core value: helping an analyst find and understand security weaknesses in source code.

**Independent Test**: Submit representative Python source containing a labelled vulnerability and verify that a structured result identifies the category, severity, confidence, affected lines, evidence, explanation, and remediation.

**Acceptance Scenarios**:

1. **Given** non-empty Python source containing one labelled vulnerability, **When** an analyst submits it and analysis succeeds, **Then** the result contains a finding with the required fields and source line range for that vulnerability.
2. **Given** source containing multiple labelled vulnerabilities, **When** analysis succeeds, **Then** the result can contain multiple distinct findings and each finding independently satisfies the output contract.
3. **Given** valid source for which no vulnerability is identified, **When** analysis succeeds, **Then** the result has an empty findings array and `overall_assessment` is `no_findings`.
4. **Given** submitted source, **When** analysis is performed, **Then** the source is never executed.
5. **Given** non-empty syntactically incomplete Python within the submission limits, **When** an analyst submits it, **Then** the system analyses it as text without requiring syntactic completeness or executing it.

---

### User Story 2 — Inspect and review findings (Priority: P1)

As a security analyst, I view the submitted source alongside its findings, navigate to the affected lines, and record that I reviewed the AI-generated assessment.

**Why this priority**: Findings need analyst context and human judgment before they are treated as a review outcome.

**Independent Test**: Submit source with one or more findings; verify each finding is visibly associated with its line range and that the interface requires an explicit review action before showing the analysis as reviewed.

**Acceptance Scenarios**:

1. **Given** a successful analysis with findings, **When** the result is displayed, **Then** the source and findings are both visible and each finding can be associated with its reported source lines.
2. **Given** an analysis with findings that has not been reviewed, **When** the analyst opens the result, **Then** its review state is visibly pending.
3. **Given** a pending result, **When** the analyst explicitly completes the review action, **Then** the interface records the result as reviewed for the current session.
4. **Given** a successful analysis with no findings, **When** the result is displayed, **Then** the interface clearly distinguishes “no findings identified” from an analysis failure.
5. **Given** an analysis result is visible in the active session, **When** the session ends, **Then** the source and all analysis results are discarded and are not available from persistent storage in a later session.

---

### User Story 3 — Recover safely from invalid input or analysis failures (Priority: P1)

As a security analyst, I receive a clear, safe message when my input is invalid or the AI service fails, and I am not shown malformed or unvalidated findings as trusted results.

**Why this priority**: A failed analysis must not be confused with a clean result or expose sensitive source or credentials.

**Independent Test**: Exercise blank input, provider failure, malformed AI output, and schema-invalid output; verify the interface reports an error state, does not show unvalidated findings as successful results, and does not disclose source or credentials in error text.

**Acceptance Scenarios**:

1. **Given** blank or whitespace-only input, **When** the analyst submits it, **Then** the submission is rejected with a field-specific validation message and no analysis is reported as successful.
2. **Given** an AI provider is unavailable or returns an operational error, **When** analysis is requested, **Then** the analyst sees a clear failure state and no fabricated findings or clean assessment are returned.
3. **Given** the AI response is not valid JSON or violates the output contract, **When** the response is processed, **Then** it is rejected and not presented as a successful analysis.
4. **Given** source containing instructions that attempt to change the analysis task, **When** analysis is requested, **Then** those instructions are treated as untrusted source content and do not override the analysis rules.
5. **Given** a submission exceeds 100,000 UTF-8 bytes or 2,000 addressable logical lines, **When** an analyst submits it, **Then** it is rejected before AI analysis with a clear validation message.
6. **Given** an input, provider, configuration, or invalid-response failure, **When** the application responds, **Then** it returns the corresponding structured error envelope and displays its safe message in the browser without returning a successful analysis result.
7. **Given** an analysis request is in progress or has failed, **When** the analyst uses the interface, **Then** no cancellation or retry control is offered, no request is automatically retried, and the analyst may submit a new request after failure.

---

### User Story 4 — Assess analysis quality using a future evaluation set (Priority: P2)

As a project reviewer, I can assess the assistant against a labelled evaluation set that covers meaningful vulnerable, clean, multi-finding, and adversarial cases, and receive a reproducible aggregate PASS or FAIL decision.

**Why this priority**: A measurable evaluation is necessary to judge whether the assistant is useful and safe beyond a few demonstrations.

**Independent Test**: Once the future dataset and harness exist, run all cases and verify the three required validation layers, minimum dataset coverage, per-layer outcomes, aggregate score, and mandatory gates are reported.

**Acceptance Scenarios**:

1. **Given** a future evaluation dataset with fewer than 15 meaningful cases, **When** the harness runs, **Then** the aggregate result is FAIL.
2. **Given** structural or mandatory safety failures, **When** the aggregate decision is calculated, **Then** the decision is FAIL regardless of the weighted semantic score.
3. **Given** all mandatory gates pass and the semantic score meets the confirmed threshold, **When** the harness completes, **Then** it reports PASS with the score, denominator, and layer-level outcomes.
4. **Given** the approved semantic threshold is 85%, **When** the semantic corpus score is below 85%, **Then** the aggregate result is FAIL even if all structural and safety gates pass.

### Edge Cases

- Empty or whitespace-only source is rejected; syntactically incomplete but non-empty Python within the submission limits is analysed as untrusted text and is not executed.
- Source exceeds 100,000 UTF-8 bytes or 2,000 addressable logical lines; the application rejects it before sending it for analysis.
- Source uses unusual line endings, has a single line, ends without a newline, or contains blank lines; reported line numbers remain 1-based and refer to the submitted text exactly.
- A vulnerability spans multiple lines; `line_start` and `line_end` bound the relevant source region and remain within the submitted line count.
- Evidence is not a verbatim excerpt from the submitted source within the reported line range; the response fails contract validation.
- The AI returns no findings, duplicate finding IDs, unknown category or severity values, invalid confidence, missing fields, additional unrecognised fields, invalid line ranges, or the wrong source language; the response fails schema/contract validation.
- The AI returns valid JSON with a top-level array, scalar, truncated object, or multiple JSON documents; the response is rejected.
- An input, provider, configuration, or invalid-response failure cannot be represented by the error response contract; the application reports an error and never returns a successful result envelope.
- The configured provider cannot guarantee processing-only use with no post-request source retention and no model training on submitted source; the application does not send the source and reports a safe configuration failure.
- The provider times out, is unavailable, rate-limits the request, or returns an error; the interface shows failure, not “no vulnerabilities.”
- Source comments, strings, docstrings, or embedded prompt-injection instructions request secrets, tool use, or a different task; they remain data to analyse and cannot override the analysis instructions.
- Submitted source or AI-generated finding text contains HTML, script-like markup, a deceptive link, or a dangerous URL; the interface displays it as inert text and does not execute it or navigate to an unsafe destination.
- API credentials are absent, malformed, or rejected; the analyst receives a safe configuration/provider error without credential values.
- Two or more findings overlap in source lines; each finding remains separately identified and valid, and the interface can present the overlap without hiding either finding.
- A finding points beyond the final source line, uses zero/negative line numbers, or has `line_end < line_start`; the result is rejected.
- A clean result is returned when the provider actually failed or the response was invalid; this is a contract violation and the request must be treated as failed.
- Evaluation output has missing labels, an unsupported case format, or unscorable semantic criteria; the case is reported as invalid/unscored and cannot silently improve the aggregate score.

For line-count validation, a non-empty submission has at least one addressable line. LF, CRLF, and CR are line terminators; CRLF counts as one terminator. A final line terminator does not create an additional addressable line after it. Reported positions refer to the exact submitted text's logical lines.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept Python source code as the subject of one analysis request.
- **FR-002**: The system MUST reject empty and whitespace-only submissions before requesting AI analysis. It MUST accept non-empty syntactically incomplete Python as text without requiring syntactic completeness. Before requesting AI analysis, it MUST reject source exceeding 100,000 UTF-8 bytes or 2,000 addressable logical lines.
- **FR-003**: The system MUST treat submitted source as untrusted data and MUST NOT execute, import, compile-and-run, or otherwise cause the submitted source to run.
- **FR-004**: The system MUST submit accepted source for analysis by an AI model. The AI provider is intentionally unspecified in this specification.
- **FR-005**: The system MUST support identifying one or more potential findings in a single submission and MUST support a successful result with zero findings.
- **FR-006**: The system MUST classify each finding using one of these exact severity values: `Critical`, `High`, `Medium`, `Low`, or `Informational`.
- **FR-007**: The system MUST provide each finding a finite numeric confidence score in the inclusive range 0.0 through 1.0 as reported by the AI model. The system MUST NOT claim that the score is calibrated or represents a measured probability of correctness.
- **FR-008**: The system MUST report a 1-based inclusive start and end line for each finding. Both values MUST be integers, `line_start` MUST be at least 1, `line_end` MUST be greater than or equal to `line_start`, and `line_end` MUST not exceed the submitted source's line count.
- **FR-009**: The system MUST provide source evidence, a non-empty explanation of the security risk, and a non-empty remediation recommendation for each finding.
- **FR-010**: The system MUST support these vulnerability categories: `SQL Injection`, `Command Injection`, `Cross-Site Scripting`, `Path Traversal`, `Insecure Deserialization`, `Hardcoded Credentials`, `Weak Cryptographic Practices`, `Insecure TLS Configuration`, `Improper Access Control`, and `Other` for a relevant Python security weakness outside the named categories.
- **FR-011**: The system MUST return successful analysis results as one JSON object conforming to the AI Output Contract in this specification.
- **FR-012**: The system MUST validate the raw AI-generated response against the AI-generated response schema and semantic invariants before the application constructs its final response. It MUST then validate the completed application response before displaying or returning it as successful.
- **FR-013**: The system MUST reject invalid JSON, schema-invalid responses, and responses that violate line, category, severity, confidence, uniqueness, evidence, or assessment invariants. Deterministic contract validation MUST require `evidence` to be a non-empty string that appears verbatim in the submitted source within the reported inclusive line range. Rejected output MUST NOT be presented as a clean result or as trusted findings.
- **FR-014**: The system MUST handle AI provider unavailability, timeout, rate limiting, and provider errors with a clear failure state. It MUST NOT fabricate findings, report “no vulnerabilities” for a failed analysis, or automatically retry a failed request. The initial interface MUST NOT offer retry or cancellation controls; after a failure the analyst may submit a new request, and an in-progress request continues until completion or failure.
- **FR-015**: The system MUST provide a local browser application without user accounts for the initial single-analyst scope. It MUST display the submitted source and its validated findings, with a visible association between each finding and its affected lines.
- **FR-016**: The system MUST require an explicit human review action for an analysis containing findings and visibly distinguish pending review from reviewed status. Review status is for the current session unless a later decision approves persistence.
- **FR-017**: The system MUST obtain AI API credentials from environment variables and MUST NOT include credential values in the UI, output JSON, application logs, or error messages.
- **FR-018**: The application MUST keep submitted source and all analysis results, including findings, evidence, summaries, and metadata, only in the active session and MUST discard them when the session ends. It MUST NOT persist or log source or analysis results, or include them in error messages or telemetry. An external AI provider may process source only to fulfil the request; it MUST NOT retain source after the request or use it for model training. The application MUST NOT send source to a provider unless this policy is in effect.
- **FR-019**: The system MUST ensure that instructions embedded in submitted source cannot override the analysis instructions or request disclosure of secrets. The source MUST be clearly delimited and treated as content to inspect.
- **FR-020**: The system MUST provide an understandable validation or failure message for rejected input, provider failures, and invalid AI responses without exposing credentials or internal secret values.
- **FR-021**: The future evaluation harness MUST contain structural validation, invariant/property validation, and semantic quality evaluation as separately reported layers.
- **FR-022**: The future evaluation dataset MUST contain at least 15 meaningful, human-labelled cases and meet the coverage requirements in the Evaluation Requirements section. Creating that dataset is outside the current specification-writing phase.
- **FR-023**: The future evaluation harness MUST produce a reproducible aggregate `PASS` or `FAIL` decision, show its score and coverage, and apply the mandatory gates defined in the Evaluation Requirements section.
- **FR-024**: The interface MUST display submitted source code and all AI-generated finding content as inert text. Untrusted markup MUST NOT execute, and untrusted links MUST NOT introduce unsafe navigation.
- **FR-025**: The system MUST detect and reject duplicate JSON object keys at every nesting level in a raw AI response before schema validation. It MUST NOT use a parser behavior that silently keeps or discards one of the duplicate values.
- **FR-026**: For input, provider, configuration, and invalid-AI-response failures, the application MUST return the separate JSON error envelope defined in the Error Response Contract and display its safe `message` in the browser interface.

### AI Output Contract

The model response and the final application response are separate JSON contracts. The model generates only the semantic analysis content listed below. The application validates that raw response, adds application-owned fields, derives the overall assessment, and validates the completed response before returning or displaying it. The initial final-response schema version is the string `1.0`.

#### AI-generated response schema

The AI response MUST be exactly one JSON object with these fields and no others:

| Field | Type | Required content and constraints |
|---|---|---|
| `analysis_summary` | string | Model-generated; required and non-empty; summarize the analysis without claiming a clean result if the response is incomplete. |
| `findings` | array of objects | Model-generated; required and may be empty. Each object contains only the model-owned finding fields below. |

Each AI-generated finding object MUST contain exactly these fields:

| Field | Type | Required content and constraints |
|---|---|---|
| `vulnerability_category` | string | Model-generated; one exact value from FR-010. |
| `title` | string | Model-generated; non-empty, concise description of the issue. |
| `severity` | string | Model-generated; one exact value from FR-006. |
| `confidence` | number | Model-generated; finite numeric value from 0.0 through 1.0 inclusive; booleans are not accepted. It is a model-reported score only and MUST NOT be represented as calibrated or as a measured probability of correctness. |
| `line_start` | integer | Model-generated; 1-based inclusive, at least 1 and no greater than `line_end` or submitted line count. |
| `line_end` | integer | Model-generated; 1-based inclusive, at least `line_start` and no greater than submitted line count. |
| `evidence` | string | Model-generated; required, non-empty, and an exact verbatim excerpt from the submitted source within the reported inclusive line range. |
| `explanation` | string | Model-generated; required and non-empty; explains the security risk in context. |
| `remediation` | string | Model-generated; required and non-empty; gives a corrective recommendation. |

The application MUST reject invalid JSON, duplicate object keys, unknown fields, missing fields, incorrect types, disallowed values, invalid line ranges, or other contract violations in the raw model response before constructing the final application response. Model-generated content MUST NOT set application-owned identifiers, timestamps, processing durations, schema version, or assessment state.

#### Final application response schema

Every successful application response MUST be exactly one JSON object with these required fields and constraints:

| Field | Type | Required content and constraints |
|---|---|---|
| `schema_version` | string | Application-generated; exactly `1.0` for this contract version. |
| `analysis_summary` | string | Model-generated and validated; required, non-empty, and consistent with whether findings are present. |
| `findings` | array of objects | Contains model-generated and validated finding content plus an application-generated `finding_id`; may be empty. Each object MUST satisfy the Final Finding Contract below. |
| `overall_assessment` | string | Application-derived; exactly `no_findings` when `findings` is empty, otherwise exactly `findings_present`. |
| `metadata` | object | Application-generated; MUST satisfy the Metadata Contract below and MUST NOT contain submitted source or credentials. |

Unknown top-level, metadata, and finding fields are rejected for schema version `1.0`. The application MUST perform duplicate-key rejection on raw model JSON at every object nesting level before validating its AI-generated response schema. The final application response MUST also be validated before return/display. A failed or invalid analysis is an application error state and MUST NOT be encoded as a successful result with an empty `findings` array. It MUST use the separate JSON error envelope defined in the Error Response Contract, and the browser MUST display that envelope's safe `message`.

#### Final Finding Contract

| Field | Type | Required content and constraints |
|---|---|---|
| `finding_id` | string | Application-generated; non-empty and unique within one analysis result. |
| `vulnerability_category` | string | Model-generated and validated; one exact value from FR-010. |
| `title` | string | Model-generated and validated; non-empty, concise description of the issue. |
| `severity` | string | Model-generated and validated; one exact value from FR-006. |
| `confidence` | number | Model-generated and validated; finite numeric value from 0.0 through 1.0 inclusive; booleans are not accepted as numbers. |
| `line_start` | integer | Model-generated and validated; 1-based inclusive, at least 1, and no greater than `line_end` or submitted line count. |
| `line_end` | integer | Model-generated and validated; 1-based inclusive, at least `line_start`, and no greater than submitted line count. |
| `evidence` | string | Model-generated and validated; required, non-empty, and an exact verbatim excerpt from the submitted source within the reported inclusive line range. |
| `explanation` | string | Model-generated and validated; required, non-empty, and explains the security risk in context. |
| `remediation` | string | Model-generated and validated; required, non-empty, and gives a concrete corrective recommendation. |

#### Metadata Contract

| Field | Type | Required content and constraints |
|---|---|---|
| `analysis_id` | string | Required; non-empty identifier for this analysis result. |
| `analysis_timestamp` | string | Required; RFC 3339 timestamp with an explicit UTC offset. |
| `source_language` | string | Required; exactly `python`. |
| `source_line_count` | integer | Required; positive integer of at least 1 representing the number of addressable logical lines in the submitted non-empty source, consistent with all finding line ranges. |
| `model_identifier` | string or null | Required; provider-neutral model identifier when available, otherwise null. It MUST NOT contain credentials. |
| `processing_time_ms` | integer | Required; non-negative duration for the analysis operation. |

All metadata fields above are application-generated, not requested from or trusted to the model. The application MUST validate metadata consistency and MUST NOT use the metadata timestamp or identifier to imply provider selection. The exact identifier-generation policy is not prescribed by this contract.

### Error Response Contract

Input, provider, configuration, and invalid-AI-response failures MUST use one JSON object separate from the successful analysis response. The error object MUST contain exactly these fields:

| Field | Type | Required content and constraints |
|---|---|---|
| `error_code` | string | Required; one of `invalid_input`, `provider_failure`, `configuration_failure`, or `invalid_ai_response`. |
| `message` | string | Required; non-empty, understandable, and safe for display. It MUST NOT contain submitted source, credentials, or internal secret values. |

The browser interface MUST display the `message` from this envelope. Error responses MUST NOT contain the successful-result fields `findings` or `overall_assessment` and MUST NOT be represented as a successful clean result. The initial implementation has no automatic or user-triggered retry and no cancellation control. An analyst may submit a new request after a failure; an in-progress request continues until it completes or fails.

### Severity interpretation

Severity describes the potential impact of the weakness in the submitted code, not the model's confidence that the weakness exists. The analyst-facing descriptions below are the initial shared rubric for classification:

| Value | Interpretation |
|---|---|
| `Critical` | A plausible path to severe compromise, such as broad control of the application or exposure of highly sensitive data, with major impact. |
| `High` | A plausible path to significant compromise or sensitive-data exposure with substantial impact. |
| `Medium` | A meaningful security impact that is bounded, conditional, or limited in scope. |
| `Low` | A limited or difficult-to-exploit impact with low expected harm. |
| `Informational` | A security-relevant observation or hardening opportunity for which the submitted evidence does not establish direct exploitable impact. |

These qualitative descriptions are the approved severity calibration for this project. No formal scoring standard is used.

### Evaluation Requirements

#### Dataset scope and minimum coverage

The future evaluation set MUST have at least 15 distinct, meaningful cases. Each case MUST have a stable case identifier, Python source input, human-labelled expected findings or an explicit expected-clean label, stable identifiers for expected findings, expected category and severity for each finding, and expected source-line ranges sufficient to score localization. Cases MUST be reviewed for label correctness before use. The dataset MUST include:

- At least one positive case for each of the nine named vulnerability categories and at least one expected finding classified as `Other`, with its specific Python weakness type documented. The `Other` finding may share a case with another finding.
- At least two clean cases with no expected vulnerabilities.
- At least two cases containing multiple expected findings.
- At least two cases containing instructions embedded in source that attempt to influence the analysis. These may overlap with other coverage categories.
- At least one case exercising boundary or multi-line source localization. This may overlap with another case.

The dataset is a future artifact; this specification does not create or populate it.

#### Harness layers and measurable criteria

1. **Structural validation** MUST validate JSON parsing, the exact required contract fields and types, allowed values, unique finding identifiers, valid line ranges, metadata consistency, and agreement between `findings` and `overall_assessment`. Every successful output in the evaluation run MUST pass. Any structural failure makes the aggregate result `FAIL`.
2. **Invariant and property validation** MUST verify source is never executed, submitted source is not persisted by default or exposed in logs/errors, credentials are not exposed, prompt-injection content does not override the analysis task, line references stay within source bounds, and provider/invalid-response failures are not reported as clean analyses. All mandatory safety invariants MUST pass; a single failure makes the aggregate result `FAIL`.
3. **Semantic quality evaluation** MUST compare the validated result with the human-labelled expected findings. A candidate match is allowed only when vulnerability category matches exactly and the inclusive predicted and expected line intervals overlap. Matching MUST be one-to-one and MUST maximize, in order, (a) the number of matched pairs and (b) the sum of their line-range intersection-over-union scores. If equally optimal matchings remain, the harness MUST select deterministically by lexicographic order of expected finding IDs and canonical predicted tuples `(vulnerability_category, line_start, line_end, title)`, using original array index only to break otherwise identical tuples. Duplicate predictions cannot match the same expected finding. For inclusive line ranges `[a,b]` and `[c,d]`, intersection-over-union is the number of shared line numbers divided by the number of line numbers in their union: `max(0, min(b,d) - max(a,c) + 1) / (max(b,d) - min(a,c) + 1)`. For each case, finding identification uses `F1 = 2TP / (2TP + FP + FN)`; if both expected and returned finding sets are empty, F1 is 1, and if expected findings are empty but returned findings are not, F1 is 0. Severity accuracy is the fraction of expected findings whose matched prediction has the exact expected severity; unmatched expected findings count as incorrect. If there are no expected findings, severity accuracy is 1 when there are also no returned findings and 0 when one or more findings are returned. Localization is line-range intersection-over-union averaged over expected findings, with unmatched expected findings scoring 0; if there are no expected findings, localization is 1 when there are no returned findings and 0 when one or more findings are returned. Explanation and remediation are each rated independently as 0, 0.5, or 1 against a case-specific rubric written and approved before the evaluation run. A rating of 1 means accurate, source-grounded, and useful (the explanation accurately describes the risk and the remediation addresses its cause); 0.5 means directionally correct but materially incomplete or nonspecific; 0 means absent, unsupported, misleading, unsafe, or irrelevant. Each case MUST be scored independently by two security reviewers using the same rubric. If either reviewer score differs, a third reviewer MUST adjudicate using the rubric; the adjudicated score is final. If required reviewers or adjudication are unavailable, the case is unscored and the run fails under the denominator rule below. An unmatched expected finding scores 0 for both explanation and remediation; when expected findings are non-empty, the explanation/remediation component is the mean of both ratings over expected findings, with unmatched expected findings contributing 0. If expected and returned findings are both empty, the component is 1; if expected findings are empty but one or more findings are returned, the component is 0. Thus, for a clean case with no returned findings, all four component scores are 1; for a clean case with one or more false-positive findings, all four component scores are 0. For a case with expected findings but no returned findings, all four component scores are 0. When expected findings are non-empty and returned findings are present, the defined F1, expected-finding denominators, and zero scores for unmatched expected findings define every component, including the case with no matched pairs. The case score is the equally weighted mean of (a) finding-identification F1, (b) severity accuracy, (c) localization, and (d) explanation/remediation. The corpus semantic score is the unweighted mean of case scores, expressed as a percentage. This scoring rubric was approved during clarification.

The semantic scoring rubric and **85%** acceptance threshold were approved during clarification on 2026-11-05. The aggregate decision is `PASS` only when the dataset minimum and coverage are met, every successful output passes structural validation, every mandatory safety/invariant gate passes, and the semantic corpus score meets or exceeds 85%. Otherwise the result is `FAIL`. The weighted semantic score MUST NOT override any mandatory structural or safety failure. The harness MUST use every case ID in the declared dataset as the denominator. A case that fails to execute, lacks usable labels, or cannot be scored MUST remain visible in the report, receive a semantic score of 0 for aggregate calculation, and make the aggregate result `FAIL`; it MUST NOT be silently omitted or used to reduce the denominator. The harness MUST report each case ID and outcome, denominator, coverage, structural outcome, invariant/property outcome, semantic score and the approved 85% threshold, mandatory gate failures, and aggregate decision.

#### Observable evidence for mandatory gates

The future harness MUST retain a per-gate result and supporting evidence sufficient for an independent reviewer to reproduce the observation. These checks apply to the application and its own controlled storage/logging surfaces. After a provider is selected, compliance with processing-only use, no post-request retention, and no training MUST be supported by provider configuration evidence and an enforceable provider policy or equivalent attestation. No provider is selected by this specification; the harness MUST NOT claim provider-side compliance is verified until such evidence is available.

| Mandatory gate | Required observable evidence |
|---|---|
| Submitted source is never executed | Submit source containing harmless execution sentinels (for example, a unique file-write or process-start expression) through the normal analysis path. In an isolated test environment, record the sentinel state and child-process events before and after the request; the sentinel MUST remain absent and no process attributable to submitted source may start. The harness itself MUST NOT execute the submitted source. |
| No unintended source or result persistence | Include unique canary strings in submitted source and in the test result's finding/evidence content. After request completion and session closure, inspect the application's configured files, browser storage, caches, captured logs, errors, and telemetry for both canaries; record the inspected surfaces and results. Any unexpected occurrence is a gate failure. For an external provider, retain configuration and policy/attestation evidence for processing-only use, no post-request retention, and no training; missing or contradictory evidence is a gate failure. |
| No credential leakage | Supply a synthetic credential canary through the configured environment variable. Scan UI output, final JSON, error output, application logs, and telemetry for the canary. Where an outbound request is captured, verify the credential is present only in the designated authentication field and absent from the prompt/source body and diagnostics. Record each surface and outcome. |
| Resistance to instructions embedded in source | Submit labelled adversarial cases whose comments, strings, or docstrings request task changes, secret disclosure, or unauthorized actions. Record the case ID, returned contract validity, finding comparison, any captured tool/action events, and whether secrets or unauthorized content appeared. Any execution, secret disclosure, task override, or unauthorized action is a gate failure. |
| Human review state | With a result containing findings, record the interface state before user action and verify it is pending. Record that no action leaves it pending; then perform the explicit review action and verify it changes to reviewed for the current session. Retain the interaction result or equivalent UI evidence. |
| Failed or unscored cases remain in the denominator | Compare the declared dataset ID list with the report's case rows. Verify there is exactly one outcome per declared ID, the denominator equals the number of declared IDs, and failed/unscored cases remain present with score 0 and an aggregate FAIL. Any missing case row or denominator reduction is a gate failure. |

### Security Requirements

- **SEC-001**: Submitted source MUST never be executed.
- **SEC-002**: Submitted source MUST be handled as untrusted content; embedded instructions MUST not change system analysis instructions or authorize actions.
- **SEC-003**: API credentials MUST come from environment variables and MUST not be returned, logged, rendered, or included in telemetry.
- **SEC-004**: The application MUST keep source and analysis results only in the active session; it MUST NOT persist or log them or include them in errors or telemetry. An external provider may process source only for the request and MUST NOT retain it afterward or use it for model training.
- **SEC-005**: AI output MUST pass the predefined schema and invariant validation before it is presented as a successful analysis.
- **SEC-006**: Provider, validation, and input errors MUST not disclose secrets or be represented as a clean security assessment.
- **SEC-007**: Submitted source and AI-generated findings MUST be rendered as inert text. Untrusted markup MUST NOT execute, and untrusted links MUST NOT cause unsafe navigation.

### Key Entities *(include if feature involves data)*

- **Analysis Request**: One submitted Python source text and its transient analysis context. The source is untrusted and is not persisted by default.
- **Analysis Result**: A successful, schema-valid result containing the summary, findings, assessment, and metadata defined by the output contract.
- **Finding**: One potential security weakness with a category, severity, confidence, source range, evidence, explanation, and remediation.
- **Human Review State**: The current-session state indicating whether an analyst has explicitly reviewed a result with findings.
- **Evaluation Case**: A future labelled source sample with expected findings or an expected-clean label and scoring annotations.
- **Evaluation Run**: A future execution of the harness over a dataset, with layer outcomes, semantic score, mandatory gate results, and aggregate PASS/FAIL decision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successful analysis responses in contract verification parse as exactly one JSON object and satisfy every required field, type, enum, and cross-field invariant in the AI Output Contract.
- **SC-002**: 100% of accepted findings in contract verification have unique identifiers, confidence in the inclusive 0.0–1.0 range, and valid 1-based line ranges within the submitted source.
- **SC-003**: The future evaluation set contains at least 15 reviewed cases and satisfies every minimum coverage item listed in Evaluation Requirements.
- **SC-004**: The future evaluation harness reports separate structural, invariant/property, and semantic outcomes and emits exactly one aggregate PASS or FAIL decision with its score and denominator.
- **SC-005**: The evaluation aggregate is FAIL on any structural or mandatory safety/invariant failure, regardless of semantic score.
- **SC-006**: The harness uses the approved 85% semantic threshold and reports FAIL whenever the semantic corpus score is below 85%, even if all structural and safety gates pass.
- **SC-007**: In all specified provider-failure and invalid-response scenarios, the interface reports an error state and does not present an empty findings array as a successful clean result.
- **SC-008**: In all specified privacy and security verification cases, submitted source is not executed, source and analysis results are not persisted by the application, an external provider processes source only for the request with no post-request retention or training, credentials are not exposed, and source-embedded instructions do not override analysis instructions.
- **SC-009**: For every successful analysis shown in the interface, an analyst can inspect the submitted source and associate each displayed finding with its reported affected lines.
- **SC-010**: Every result containing findings remains visibly pending until an analyst takes the explicit review action; afterward the current-session state is visibly reviewed.
- **SC-011**: 100% of safe-rendering verification cases display source and finding content inertly, with no markup execution or unsafe link navigation.
- **SC-012**: 100% of specified input, provider, configuration, and invalid-response failures return a valid error envelope, display its message in the UI, and do not return a successful analysis result.

## Assumptions

- The primary user is one security analyst reviewing Python source code through a local browser application without user accounts.
- A single analysis concerns one source submission. Batch repositories, multiple files, and non-Python languages are outside the initial scope unless later approved.
- The system uses an AI model, but no provider, model, or provider-specific API is selected here.
- A successful empty result means analysis completed and no vulnerabilities were identified; provider errors and invalid output are failures, never clean results.
- The application presents AI output as potential findings requiring human judgment; it does not make a final security approval decision.
- Failures use the separate structured JSON error envelope and its safe message is displayed in the UI. The initial implementation offers no retry or cancellation; an analyst may submit again after a failure or wait for completion.
- Source and results are retained only in active-session memory as needed to show findings; the application discards them when the session ends, and an external provider may process source only for the request with no post-request retention or training.
- The output contract in this specification is a proposed initial version. Its metadata fields and identifier policies are subject to review before implementation.
- The semantic scoring rubric and 85% evaluation threshold were approved during clarification; the harness may evaluate against 85% once the dataset exists.
- The application is used locally through a browser; its packaging and distribution details have not been established.

## Clarification Status

Q1–Q11 have been answered and recorded above. No unresolved Clarify questions remain. Plan and design artifacts have been created for human review. Tasks and Implement have not started.
