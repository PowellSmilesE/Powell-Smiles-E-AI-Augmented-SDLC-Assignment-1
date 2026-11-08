# Tasks: AI-Powered Security Code Review Assistant

**Input**: Approved design documents in `specs/001-ai-security-code-review/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Approval**: Plan approved by human project owner on 2026-11-05. Task generation is authorized; implementation still requires its own authorization.

**Task format**: `- [ ] Tnnn [P?] [USn?] Action and exact file path(s)`

**Tests**: Included because the specification explicitly requires unit, contract, browser and evaluation verification. Tests are listed before the implementation they verify. No tests have been run by task generation.

## Phase 1: Setup

**Purpose**: Establish the planned Python package and reproducible development workflow.

- [ ] T001 Define the `security-code-review` package metadata, Python 3.12+ requirement, runtime dependencies, development extras, and pinned dependency/constraints workflow in `pyproject.toml` and `requirements-dev.lock`.
- [ ] T002 Create the package entry points and test package directories in `src/security_code_review/__init__.py`, `src/security_code_review/__main__.py`, `tests/unit/__init__.py`, `tests/contract/__init__.py`, `tests/integration/__init__.py`, `tests/browser/README.md`, and `tests/evaluation/README.md`.
- [ ] T003 Configure pytest, Ruff, Bandit and coverage defaults in `pyproject.toml` and `.bandit`.
- [ ] T004 Configure a test-only settings fixture and safe temporary directories in `tests/conftest.py`; ensure fixtures do not log or persist submitted source/results.

## Phase 2: Foundational Components

**Purpose**: Build shared security, request, schema and error boundaries before user-story work.

- [ ] T005 [P] Write unit tests for environment loading, missing credentials and secret redaction in `tests/unit/test_config.py` before implementation (FR-017, SEC-003).
- [ ] T006 [P] Write tests before implementation for incremental raw-body counting (accept at 600,128 bytes, reject above it without fully buffering or JSON decoding), decoded source byte/line limits, line-ending cases, exact source preservation and safe errors in `tests/unit/test_body_limit.py`, `tests/unit/test_input_validation.py`, and `tests/unit/test_errors.py` (FR-002, FR-020, FR-026).
- [ ] T007 [P] Write unit tests for nested duplicate keys, malformed/trailing JSON and invalid constants in `tests/unit/test_json_decoder.py` before implementation (FR-012–FR-013, FR-025).
- [ ] T008 [P] Write unit tests for source ranges, exact evidence, final assessment, IDs, metadata and enabled date-time format checking in `tests/unit/test_response_validation.py` before implementation (FR-006–FR-013).
- [ ] T009 [P] Write provider-policy tests proving default-disabled behavior and no source transmission without approved evidence in `tests/unit/test_provider_policy.py` before implementation (FR-018).
- [ ] T010 Implement typed environment settings and secret redaction in `src/security_code_review/config.py`; credentials must only be read from environment variables and never exposed to the browser or logs (FR-017, SEC-003).
- [ ] T011 Implement the FastAPI application factory, loopback defaults, Host/Origin checks, same-origin policy and security headers in `src/security_code_review/api/app.py` and `src/security_code_review/security/headers.py` (FR-015, FR-024, SEC-007).
- [ ] T012 Define strict request, AI-generated response, final response and error models with unknown fields forbidden in `src/security_code_review/schemas/ai_response.py`, `src/security_code_review/schemas/analysis_result.py`, and `src/security_code_review/schemas/errors.py` (FR-011–FR-013, FR-026, SEC-005).
- [ ] T013 Implement post-JSON-decode request validation in `src/security_code_review/validation/input.py`: reject empty/whitespace-only input, decoded `source_code` UTF-8 size >100,000 bytes, or >2,000 addressable logical lines; accept incomplete Python as text; preserve the decoded source unchanged. Count LF, CRLF-as-one and CR terminators, with no extra addressable line after a final terminator (FR-001–FR-003, FR-008).
- [ ] T014 Enforce the 600,128-byte raw JSON entity limit incrementally while receiving the request body in `src/security_code_review/api/routes.py`; count actual received bytes and stop/reject as soon as the limit is exceeded, before unbounded buffering or JSON decoding. `Content-Length` may support early rejection but must not be the sole enforcement mechanism. Preserve the separate post-decode limits of 100,000 UTF-8 source bytes and 2,000 addressable logical lines (FR-002).
- [ ] T015 Implement duplicate-key rejecting JSON parsing at every nesting level, exactly-one-document parsing and rejection of non-standard numeric constants in `src/security_code_review/validation/json_decoder.py` (FR-025).
- [ ] T016 Implement source-dependent finding validation in `src/security_code_review/validation/model_output.py`: require `line_end >= line_start`, line bounds within submitted logical line count, exact evidence matching the unchanged source slice including submitted line terminators, and all specified category/severity/confidence/string rules (FR-006–FR-010, FR-013).
- [ ] T017 Implement final response construction and cross-field validation in `src/security_code_review/validation/analysis_result.py`: unique app-generated finding IDs, metadata, `source_line_count`, and `overall_assessment == no_findings` iff findings are empty (FR-011–FR-013).
- [ ] T018 Validate `metadata.analysis_timestamp` with JSON Schema `format: date-time`, an enabled `FormatChecker`, and the installed/registered date-time checker dependency in `src/security_code_review/validation/analysis_result.py` (FR-012).
- [ ] T019 Implement fixed safe error mapping to the four specified error codes and envelope in `src/security_code_review/api/errors.py`; never include source, provider bodies, credentials or internal secrets (FR-020, FR-026, SEC-006).
- [ ] T020 Implement the provider protocol and a fail-closed policy gate in `src/security_code_review/providers/protocol.py` and `src/security_code_review/providers/policy.py`; provider calls remain disabled unless endpoint-specific processing-only, no-retention and no-training evidence has human approval (FR-004, FR-018).
- [ ] T021 Record the selected provider or the decision to keep live transmission disabled, with endpoint/tier/configuration evidence and human owner approval, in `docs/provider-policy-decision.md`; do not select a provider or transmit source without that approval (FR-018).
- [ ] T022 Implement source/result-free structured logging and disable request-body capture, telemetry and application/browser persistence in `src/security_code_review/security/logging.py` and `src/security_code_review/api/app.py` (FR-018, SEC-003–SEC-004).
- [ ] T023 Verify the shared foundation keeps provider transmission disabled by default and that all request, error and log boundaries exclude source/results/secrets in `tests/integration/test_foundation_security.py` (FR-018, SEC-003–SEC-006).

**Foundation checkpoint**: Shared validators and API boundaries reject invalid input/output; no live provider request can occur until T021 is approved.

## Phase 3: User Story 1 — Submit code and receive a security analysis (P1, MVP)

**Goal**: Submit one accepted Python source string and receive zero or more contract-valid findings, without ever executing the source.

**Independent test**: With a mocked provider, submit bounded source through `POST /api/analyze`; verify a successful empty result and one/multiple findings conform to the final contract, exact evidence and source-line bounds. Confirm submitted source was not executed. Live provider tests remain blocked until T021 is approved.

- [ ] T024 [P] [US1] Write provider-protocol contract tests for one request, response handling and no implicit retries in `tests/contract/test_provider_protocol.py` (FR-004, FR-014).
- [ ] T025 [P] [US1] Write API success contract tests for empty, single-finding and multiple-finding outputs in `tests/contract/test_analysis_success.py`; validate the AI-response and final-result schemas directly for required fields, additional-property rejection, types, enums and applicable assessment/range constraints (FR-005–FR-013).
- [ ] T026 [P] [US1] Write analysis service tests for successful empty and populated model responses in `tests/unit/test_analyzer.py` (FR-004–FR-005).
- [ ] T027 [US1] Implement a provider-neutral prompt template that delimits source as untrusted content and grants no tools/actions in `src/security_code_review/security/prompt.py` (FR-003–FR-004, FR-019, SEC-001–SEC-002).
- [ ] T028 [US1] Implement the provider-neutral HTTP adapter behind the approved policy gate in `src/security_code_review/providers/adapter.py`; use credentials only in the authentication channel and never in prompt/body diagnostics (FR-004, FR-017–FR-018, SEC-003).
- [ ] T029 [US1] Implement the analysis orchestration service for input validation, one provider call, raw response validation, application fields and final response validation in `src/security_code_review/services/analyzer.py` (FR-001–FR-013).
- [ ] T030 [US1] Implement `POST /api/analyze` request and success handling in `src/security_code_review/api/routes.py` using the approved request and final-response contracts (FR-001, FR-004–FR-013).
- [ ] T031 [US1] Implement application-owned analysis/finding identifiers, timestamp, duration, model identifier and logical line metadata in `src/security_code_review/services/analyzer.py` (FR-011–FR-012).
- [ ] T032 [US1] Add integration tests for valid source, incomplete source, empty findings and multiple findings through the API in `tests/integration/test_analysis_flow.py` (FR-001–FR-013).
- [ ] T033 [US1] Add a non-execution sentinel test through the normal analysis request path in `tests/integration/test_source_not_executed.py`; assert no sentinel effect and no child process attributable to submitted code (FR-003, SEC-001).
- [ ] T034 [US1] Directly validate all four application JSON contracts—`specs/001-ai-security-code-review/contracts/analysis-request.schema.json`, `specs/001-ai-security-code-review/contracts/ai-response.schema.json`, `specs/001-ai-security-code-review/contracts/analysis-result.schema.json`, and `specs/001-ai-security-code-review/contracts/error-response.schema.json`—in `tests/contract/test_json_schemas.py`; cover required fields, additional-property rejection, types, enums, the findings/overall-assessment conditional, and enabled date-time format checking. Keep source-dependent range/evidence invariants in T016. Do not use application validators as the schema test oracle (FR-011–FR-013, FR-026, SC-001–SC-002, SC-012).

**Checkpoint**: The MVP analysis flow passes mocked-provider tests and cannot send source when provider policy is unapproved.

## Phase 4: User Story 2 — Inspect and review findings (P1)

**Goal**: Display source and findings together as inert text and retain explicit review state only in the current browser memory.

**Independent test**: Load a mocked successful result with findings; verify line association, inert display, pending state, explicit transition to reviewed, and loss of state after reload.

- [ ] T035 [P] [US2] Write browser tests for line navigation/association, pending/reviewed transition and reload clearing in `tests/browser/test_review_flow.py` (FR-015–FR-016, SC-009–SC-010).
- [ ] T036 [P] [US2] Write browser security tests using markup, script-like content, deceptive links and dangerous URL strings in `tests/browser/test_inert_rendering.py` (FR-024, SEC-007, SC-011).
- [ ] T037 [US2] Implement the source submission and result layout in `src/security_code_review/web/index.html` and `src/security_code_review/web/styles.css` (FR-015).
- [ ] T038 [US2] Implement compact JSON request serialization, source display and finding-to-line association using inert DOM text APIs in `src/security_code_review/web/app.js` (FR-015, FR-024, SEC-007).
- [ ] T039 [US2] Implement visible pending/reviewed status and explicit review action in browser memory only in `src/security_code_review/web/app.js` (FR-016, FR-018).
- [ ] T040 [US2] Implement the zero-finding success view distinct from failure in `src/security_code_review/web/app.js` (FR-005, SC-007).
- [ ] T041 [US2] Verify restrictive CSP and browser security headers for the rendered UI in `tests/browser/test_security_headers.py` and `src/security_code_review/security/headers.py` (FR-024, SEC-007).

**Checkpoint**: Findings are legible and associated with source lines; untrusted markup remains inert, and review state is session-only.

## Phase 5: User Story 3 — Recover safely from invalid input or analysis failures (P1)

**Goal**: Reject invalid submissions and handle provider/configuration/model failures through safe structured errors; do not report failure as a clean scan.

**Independent test**: Exercise invalid/oversize source, provider timeout/rate-limit/failure, malformed/duplicate-key/schema-invalid output, absent policy approval, and adversarial source. Verify exact error envelopes, no retries/cancel UI, no false clean result, and no secret/source leakage.

- [ ] T042 [P] [US3] Write API contract tests for the error envelope schema, required fields, additional-property rejection, field types, allowed error codes, HTTP mapping and successful/error response separation in `tests/contract/test_error_responses.py` (FR-020, FR-026, SC-012).
- [ ] T043 [P] [US3] Write provider failure tests for timeout, rate limit, unavailability and one-call/no-retry behavior in `tests/unit/test_provider_failures.py` (FR-014, SC-007).
- [ ] T044 [P] [US3] Write ASGI request-body contract tests in `tests/contract/test_request_limits.py` for a body within 600,128 bytes, a body exceeding the limit, missing `Content-Length`, deliberately under/over-reported `Content-Length`, and chunked/streamed receipt where supported by the ASGI test setup; verify actual received chunks are counted, reading stops once the cap is crossed, the JSON decoder is not called for oversized bodies, and no oversized body is accepted even when the header is absent or inaccurate. Reject inconsistent lengths safely before JSON decoding. Also verify the `analysis-request.schema.json` required field, type and additional-property rules, plus blank input, >100,000 decoded UTF-8 source bytes, and >2,000 logical lines as separate rejection conditions (FR-002).
- [ ] T045 [P] [US3] Write secret-canary tests for UI, responses, errors, logs and telemetry in `tests/integration/test_secret_non_disclosure.py` (FR-017–FR-018, SEC-003–SEC-004).
- [ ] T046 [P] [US3] Verify the application's browser request serialization is compact and boundary behavior for excessive JSON whitespace is documented in `tests/contract/test_compact_request.py` and `specs/001-ai-security-code-review/contracts/http-api.md` (FR-002).
- [ ] T047 [US3] Map input, provider, configuration and invalid-response failures to their safe structured error envelope and status codes in `src/security_code_review/api/errors.py` and `src/security_code_review/api/routes.py` (FR-014, FR-020, FR-026, SEC-006).
- [ ] T048 [US3] Ensure provider exceptions and raw AI payloads are sanitized and never logged or exposed in `src/security_code_review/services/analyzer.py` and `src/security_code_review/security/logging.py` (FR-017–FR-020, SEC-003–SEC-006).
- [ ] T049 [US3] Add adversarial prompt-injection examples to synthetic test fixtures and verify no tools/actions/secrets are exposed in `tests/integration/test_prompt_injection_boundary.py` (FR-019, SEC-002).
- [ ] T050 [US3] Verify failed or invalid AI responses never produce empty-findings success in `tests/integration/test_failure_not_clean_result.py` (FR-013–FR-014, SEC-005–SEC-006, SC-007).
- [ ] T051 [US3] Verify source/result canaries are absent from application files, browser durable storage, caches, logs, errors and telemetry after session closure in `tests/integration/test_no_persistence.py` (FR-018, SEC-004).
- [ ] T052 [US3] Verify interface offers no retry/cancellation control and performs no automatic retry in `tests/browser/test_no_retry_cancel.py` (FR-014).

**Checkpoint**: Invalid and failed requests are safe, distinguishable from successful clean results, and do not leak content or secrets.

## Phase 6: User Story 4 — Assess analysis quality using the future evaluation set (P2)

**Goal**: Independently validate structural correctness, mandatory invariants and semantic quality and report reproducible PASS/FAIL using the approved 85% threshold.

**Independent test**: Run the evaluator against synthetic fixtures and, after dataset creation/review, the complete declared dataset. Verify every case appears in the denominator; structural/safety/unscored failures force FAIL; PASS requires coverage and semantic score >=85%.

- [ ] T053 [P] [US4] Write structural validator tests for exact fields/types/enums, duplicate keys, line ranges, metadata and assessment consistency in `tests/evaluation/test_structural.py`; these tests and the evaluator must use evaluator-owned schemas/checks and must not import application validation functions (FR-021, SC-001–SC-002).
- [ ] T054 [P] [US4] Write semantic matching/scoring tests for one-to-one matching, exact category, line overlap/IoU, tie-breaks, clean cases and false positives in `tests/evaluation/test_semantic.py` (FR-021, SC-004, SC-006).
- [ ] T055 [P] [US4] Write aggregate tests for the 85% threshold, mandatory gate precedence, denominator preservation and failed/unscored cases in `tests/evaluation/test_aggregation.py` (FR-023, SC-003–SC-006).
- [ ] T056 [US4] Define only the evaluator-owned result and error schemas needed to validate evaluation outputs in `evaluation/schemas/analysis_result.schema.json` and `evaluation/schemas/error_response.schema.json`; do not add an evaluator request schema because request-schema validation is not required by the approved evaluation specification (FR-021, FR-023).
- [ ] T057 [US4] Implement independent duplicate-aware JSON decoding and structural validation in `evaluation/harness/structural.py` (FR-021, SC-001–SC-002).
- [ ] T058 [US4] Enable JSON Schema `FormatChecker` and the `jsonschema[format]` date-time implementation in the evaluator's final result validation in `evaluation/harness/structural.py` (SC-001, SC-004).
- [ ] T059 [US4] Implement independent line-range, evidence, non-execution, privacy, credential, prompt-injection and human-review invariant checks in `evaluation/harness/invariants.py` (FR-021, FR-023, SC-005, SC-008–SC-011).
- [ ] T060 [US4] Implement deterministic one-to-one finding matching and inclusive line IoU tie-break behavior in `evaluation/harness/semantic.py` (FR-021, SC-004, SC-006).
- [ ] T061 [US4] Implement all four semantic components, two-reviewer scoring and third-reviewer disagreement adjudication in `evaluation/harness/semantic.py` (FR-021, SC-004, SC-006).
- [ ] T062 [US4] Implement aggregate denominator, coverage, mandatory gate precedence and approved 85% PASS/FAIL calculation in `evaluation/harness/aggregation.py` (FR-022–FR-023, SC-003–SC-006).
- [ ] T063 [US4] Implement a report with one row per declared case, layer outcomes, scores, denominator, gate evidence and aggregate decision in `evaluation/harness/report.py` (FR-021, FR-023, SC-004–SC-006).
- [ ] T064 [US4] Implement the evaluation command entry point and deterministic input/report paths in `evaluation/harness/cli.py` (FR-021–FR-023).
- [ ] T065 [US4] Create a reviewed dataset of at least 15 meaningful cases with all required category, `Other`, clean, multi-finding, injection and line-boundary coverage in `evaluation/dataset/cases.jsonl` (FR-022, SC-003).
- [ ] T066 [US4] Record stable expected finding IDs, labels, line ranges, case-specific rubrics, reviewer scores and adjudications in `evaluation/dataset/labels.jsonl` and `evaluation/dataset/review-record.md` (FR-022–FR-023).
- [ ] T067 [US4] Verify every dataset case is in the report denominator and failed/unscored cases remain visible with score zero and aggregate FAIL in `tests/evaluation/test_denominator_and_gates.py` (FR-023, SC-004–SC-005).
- [ ] T068 [US4] Capture per-gate evidence for source non-execution, no persistence, credential non-disclosure, prompt-injection resistance, human review and denominator preservation in `evaluation/evidence/README.md` (FR-023, SC-005, SC-008–SC-011).

**Checkpoint**: The evaluator is independent of application validators; dataset creation and any evaluation run remain future work until these tasks are authorized and the dataset is reviewed.

## Phase 7: Polish and Cross-Cutting Verification

**Purpose**: Verify quality gates, documentation and evidence across the completed stories.

- [ ] T069 Run unit, contract, integration, browser and evaluation tests; preserve commands, actual outcomes, failure evidence and repairs in `artifacts/validation/test-report.md` (all FR/SEC/SC requirements).
- [ ] T070 Run Ruff lint and format checks and resolve or justify findings in `pyproject.toml` and `artifacts/validation/quality-report.md` (plan quality gate).
- [ ] T071 Run Bandit and dependency audit; record findings, versions and dispositions in `artifacts/validation/security-report.md` (SEC-001–SEC-007).
- [ ] T072 Validate quickstart commands from the documented parent repository root and record actual results or blockers in `artifacts/validation/quickstart-report.md` (SC-001–SC-012).
- [ ] T073 Review requirement-to-task-to-evidence traceability and update the mapping in `specs/001-ai-security-code-review/traceability.md` (FR-001–FR-026, SEC-001–SEC-007, SC-001–SC-012).
- [ ] T074 Prepare the final human review package and record the human ACCEPT/REJECT decision only in `artifacts/validation/human-decision.md`; do not infer or make the decision in code or evaluation output (Constitution governance).

## Requirement-to-Task Traceability

| Requirements | Task coverage |
|---|---|
| FR-001–FR-003, FR-008–FR-010; SEC-001–SEC-002 | T006, T013, T016, T027, T033, T049, T059 |
| FR-004–FR-007, FR-011–FR-013; SEC-005 | T008, T012, T015–T018, T024–T034, T053, T056–T061 |
| FR-014, FR-020, FR-026; SEC-006 | T019, T042–T043, T047–T050, T052 |
| FR-015–FR-016, FR-024; SEC-007 | T011, T035–T041, T059 |
| FR-017–FR-019; SEC-003–SEC-004 | T005, T009–T010, T020–T023, T028, T045, T048–T051, T059, T068 |
| FR-021–FR-023; SC-003–SC-006 | T053–T068 |
| SC-001–SC-002, SC-007–SC-012 | T008, T025, T032–T034, T042–T046, T050–T051, T053–T059, T063, T067–T074 |

## Dependencies & Execution Order

### Phase dependencies

- Phase 1 has no dependencies.
- Phase 2 depends on Phase 1 and blocks all user stories.
- US1, US2 and US3 are P1. US1 establishes the analysis/result contract; US2 and US3 integrate with its API. Tests for separate files can be prepared in parallel, but end-to-end story acceptance depends on the shared API foundation.
- US4 can develop against synthetic fixtures after the contracts exist, but final evaluation depends on the application, reviewed dataset and human/provider policy evidence.
- Phase 7 depends on the selected implementation scope being complete. Human ACCEPT/REJECT remains an external decision.

### Provider privacy gate

T021 requires human project-owner selection/approval and enforceable endpoint-specific evidence. Until it is complete, use only mocked providers; keep live source transmission disabled. If no provider meets the approved no-retention/no-training policy, do not weaken the policy or enable transmission.

### Parallel opportunities

- Complete T001, then T002. After T002, T003 and T004 can proceed in parallel on separate configuration/test files.
- Foundation tests T005–T009 can be prepared in parallel because they target separate test files; implementation follows in the listed order.
- US1 test files T024–T026 can be prepared in parallel; implementation tasks follow the validators and provider protocol.
- US2 browser tests T035–T036 can be prepared in parallel; UI structure, rendering and review state remain sequential where they share `app.js`.
- US3 tests T042–T045 can be prepared in parallel; failure mapping and sanitization tasks depend on the shared API/service.
- US4 test files T053–T055 can be prepared in parallel. Structural, semantic and aggregation modules can then be developed independently, with the CLI/reporting integration after them.
- Do not parallelize changes to the same shared files (`pyproject.toml`, `routes.py`, `app.js`, or the aggregate report pipeline) without explicit coordination.

### Per-story parallel execution examples

- **US1**: Prepare T024, T025 and T026 in parallel; after those contracts are agreed, implement and integrate the shared analyzer/API in task order. Live-provider work still depends on T021.
- **US2**: Prepare T035 and T036 in parallel. Then implement T037, followed by T038–T040; run T041 with the header/UI verification work.
- **US3**: Prepare T042–T046 in parallel because each test targets a separate file. Implement T047 then T048 where they touch shared error/logging boundaries; execute independent verification tasks T049–T052 after those changes.
- **US4**: Prepare T053–T055 in parallel. Then implement structural/date-time validation (T057–T058), independent invariants (T059) and matching (T060) on separate modules; continue with scoring, aggregation, reporting and CLI in listed order. Dataset authoring/review (T065–T066) is a separate human-reviewed activity.

## Implementation Strategy

### MVP

Complete Setup and Foundation, then US1 with a mocked provider and a verified fail-closed live-provider policy. Validate the output contract, boundary handling and non-execution before proceeding. This MVP can demonstrate analysis orchestration without transmitting real source until T021 is approved.

### Incremental delivery

1. Setup and Foundation: package, schemas, validators, safe errors and disabled provider gate.
2. US1: successful mocked analysis and validated JSON output.
3. US2: local interface, inert findings and human review state.
4. US3: safe input/provider/model failure behavior and privacy/security evidence.
5. US4: independent harness, then separately authorized dataset creation/review and evaluation.
6. Polish: static checks, quickstart verification, preserved reports and human decision.

## Notes

- All implementation tasks remain unchecked. This file creates no application code, tests, provider selection, dataset or evaluation result.
- `[P]` means the task uses different files and has no dependency on unfinished work; `[USn]` maps to the corresponding story in `spec.md`.
- Keep task execution in listed ID order except explicitly parallel tasks with independent files.
- Tests must be implemented and executed as specified when implementation is authorized; this generation phase did not execute tests.
