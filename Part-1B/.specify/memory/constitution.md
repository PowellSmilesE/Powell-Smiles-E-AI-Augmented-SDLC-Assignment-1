# AI-Powered Security Code Review Assistant Constitution

**Status: Approved by human project owner.** This approval records the project owner's decision only and does not imply approval by BITS Pilani, the instructor, or any organization.

## Core Principles

### I. Security-First Engineering

Security requirements shape architecture, implementation, and verification from the start. Prefer least privilege, narrow interfaces, safe defaults, explicit threat assumptions, and defense in depth. Security-sensitive changes require focused tests and review. A security gate failure cannot be offset by a usability or aggregate quality score.

### II. Privacy by Default

Collect and transmit only data needed for the requested analysis. Submitted source, findings, evidence, and review state remain transient and must not be persisted, logged, cached, or sent to telemetry. Source may be transmitted to an AI provider only after the exact service configuration has enforceable evidence of request-only processing, no post-request retention, and no training on submitted source. If that condition cannot be established, fail closed without transmitting source.

### III. Never Execute Submitted Source

Submitted Python is data for review, never program input to an execution environment. The application, tests, and evaluation harness must not execute, import, compile-and-run, or otherwise cause submitted source to run. Test execution sentinels only through the application's analysis path; do not execute the sentinel source to test it.

### IV. Treat External Content as Untrusted

Submitted source and all AI-generated content are untrusted. Embedded instructions cannot grant authority, change system instructions, reveal secrets, or trigger tools/actions. Render source and findings as inert text; do not interpret markup or unsafe links. Prompt wording is defense in depth, not proof that model influence is impossible.

### V. Modular, Maintainable Architecture

Keep interface, application orchestration, provider integration, validation, and evaluation responsibilities clearly separated. Use small, typed, documented interfaces and avoid unnecessary services, frameworks, persistence, and abstractions. Provider-specific details must not leak across the provider boundary. Complexity must be justified by a stated requirement or security need.

### VI. Strict Contracts and Invariants

Validate request bounds before provider I/O. Reject duplicate JSON object keys at every nesting level before schema validation. Validate strict types, exact fields, enums, ranges, evidence grounding, uniqueness, metadata, and cross-field invariants for both AI-generated and application-generated responses. Invalid AI output is a failure, never a clean result; errors use the separate safe error contract.

### VII. Independent Testing and Evaluation

Test units and public contracts independently. The evaluation harness must implement its own structural and invariant validators rather than importing application validation logic. Verify security and privacy properties with observable evidence, including no source execution, no unintended persistence, no credential leakage, prompt-injection resistance, safe rendering, explicit human review, and denominator preservation.

### VIII. Reproducible Evaluation and Honest Evidence

Evaluation must be reproducible from versioned rules, declared case IDs, reviewer procedures, and preserved outcomes. Keep failed and unscored cases visible in the denominator. Structural or mandatory safety failures force an overall FAIL regardless of semantic score. Report commands and results accurately; never claim checks or provider policies were verified without evidence. Preserve genuine failures and subsequent repairs rather than rewriting history.

### IX. Human Review and Decision Authority

AI findings are potential issues requiring analyst judgment. A result with findings remains visibly pending until the analyst takes an explicit review action. The assistant and evaluation harness do not make the final human security decision on the analyst's behalf.

### X. Documentation and Traceability

Keep specification, architecture, contracts, tests, evaluation rules, and evidence aligned. Trace each requirement to design responsibilities and verification. Document assumptions, limitations, unresolved risks, and deviations. When a clarification changes behavior, update affected artifacts consistently without silently changing approved decisions.

## Security and Quality Constraints

- Bind the initial browser application to loopback only and apply same-origin, Host/Origin, and browser-rendering protections appropriate to a local unauthenticated application.
- Keep provider credentials in environment configuration; never return, render, log, or include them in source prompts or diagnostics.
- Do not add durable source/result storage, retries, cancellation, accounts, or provider-specific behavior unless a future approved specification changes scope.
- Run unit, contract, browser, static analysis, and independent evaluation checks as planned. A tool's clean result is evidence for its specific checks only, not a general security guarantee.
- Keep the approved semantic evaluation threshold at 85%; mandatory structural and safety gates remain non-overridable.

## Development Workflow

1. Clarify requirements and record decisions before planning behavior that depends on them.
2. Maintain this approved constitution with the human project owner; record amendments and review decisions without claiming instructor or organizational approval.
3. Plan and trace requirements before implementation. Resolve document conflicts before implementation begins.
4. Implement behind the documented module boundaries with tests for contracts and security invariants.
5. Run the independent harness and quality checks; retain actual output, failures, repairs, and platform limitations.
6. Present evidence and limitations for human review. Only the human reviewer records the final ACCEPT/REJECT decision.

## Governance

This constitution has been approved by the human project owner and remains subordinate to explicit human-approved assignment requirements. Amendments must retain the approval status, record the change and rationale, and update affected specification, plan, contract, and verification artifacts. No agent or automated check may claim approval by BITS Pilani, the instructor, or any organization.

### Approval Record

- **Decision**: APPROVED
- **Approver**: Human project owner
- **Approval date**: 2026-11-05

**Version**: 0.1 (approved) | **Ratified**: 2026-11-05 by human project owner | **Last Amended**: 2026-11-05
