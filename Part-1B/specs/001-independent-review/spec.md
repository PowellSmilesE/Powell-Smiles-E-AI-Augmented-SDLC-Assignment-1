# Approved specification — independent security review

**Project identity:** New Part 1B project, completely independent of prior implementation.
**Acceptance baseline:** 90% average semantic threshold, declared before any live model run.
**Scope:** Python source review only; never execute source; user explicitly consents to
external transfer. Model findings are advisory, pending human verification.

## Functional requirements
- FR-001: Accept a bounded Python snippet, or reject invalid input.
- FR-002: Require positive opt-in before forwarding source to Groq.
- FR-003: Preserve separation of trusted system policy and untrusted code-as-data.
- FR-004: Produce a strict JSON object with summary and typed findings.
- FR-005: Findings carry grounded source-line ranges and exact source evidence.
- FR-006: Explain risks and actionable remediation without asserting unobserved facts.
- FR-007: Keep findings marked pending human review; no auto-promotion to accepted.
- FR-008: Use bounded, explicit retries for transient provider failures; report unavailable if unresolved.
- FR-009: No local application storage or execution of submitted source; no exposed secret-bearing logs.
- FR-010: Evaluation report includes 25-case denominator and honest missing/unscored cases.

## Verification policy (frozen when dataset is personally approved)
- SC-001: >=25 genuinely distinct cases; exactly 25 in canonical benchmark.
- SC-002: Mean semantic score >=90%; all cases >=75% individually.
- SC-003: Structural valid outputs and deterministic source evidence invariants 25/25 PASS.
- SC-004: All expected finding categories recalled for each designated critical-eval case.
- SC-005: Six scoped security gates PASS with real evidence (source_not_executed,
  prompt_injection_resistance, human_review_state, denominator_preservation,
  credential_non_disclosure, no_persistence). Scope limited to application and tested browser;
  no claims about third-party retention or all host telemetry.
- SC-006: Final human ACCEPT/REJECT and known risks documented by the student.

**Important:** The benchmark and scorer must be reviewed, committed, and hash-frozen before
final live evaluation. A FAIL must not be converted into PASS by editing the benchmark,
weakening assertions, or marking incomplete evidence as verified.
