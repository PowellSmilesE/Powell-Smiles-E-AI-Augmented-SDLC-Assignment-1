---
description: "Implementation tasks for Security Alert Management"
---

# Tasks: Security Alert Management

**Input**: Design documents from `/specs/001-security-alert-management/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md)

**Organization**: Tasks are ordered by setup, shared foundation, then the specification's prioritized user stories. Tests are required by the specification and constitution; write each test task before its corresponding behavior implementation.

**Path scope**: All paths below are relative to `Part-1A/`.

## Phase 1: Setup

**Purpose**: Create the application/test skeleton and configure the minimal development environment.

- [x] T001 Create planned directories `src/alert_manager/`, `tests/unit/`, `tests/contract/`, `tests/fixtures/`, `validation/`, and `artifacts/validation/`; add package entry files `src/alert_manager/__init__.py` and `src/alert_manager/__main__.py` plus test package markers `tests/__init__.py`, `tests/unit/__init__.py`, and `tests/contract/__init__.py` (FR-012, NFR-001).
- [x] T002 [P] Configure `pyproject.toml` with `[build-system].requires = ["setuptools"]`, `build-backend = "setuptools.build_meta"`, and a named `[project]` table (name `security-alert-manager`) containing `requires-python = ">=3.11"`, `dependencies = []`, and `[project.optional-dependencies].dev = ["ruff", "bandit"]`; configure setuptools package discovery with `where = ["src"]`; verify `python -m pip install -e ".[dev]"` from a clean Part-1A virtual environment makes `python -m alert_manager` importable (FR-014, NFR-001).
- [x] T003 [P] Add `.venv/` and Python bytecode/cache patterns plus the root-anchored `/alerts.json` pattern to `Part-1A/.gitignore`; do not ignore nested test fixtures such as `tests/fixtures/alerts.json` or any validation reports (FR-010, constitution Security and Alert Handling).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared alert model, error boundaries, and validated JSON persistence required by all stories.

- [x] T004 [P] Write failing model tests in `tests/unit/test_models.py` for the exact data-model constraints: `Generated as UUID4; unique in the store; immutable. Retry generation on collision.`; `Non-empty after trimming; at most 200 Unicode characters.`; `Non-empty after trimming; at most 4,000 Unicode characters.`; `Must parse as IPv4 or IPv6; hostnames and CIDR ranges are invalid.`; severity `Critical`, `High`, `Medium`, `Low`, `Informational`; status `New`, `In Progress`, `Resolved`, `Closed`; and `UTC RFC 3339, whole seconds, trailing Z` (FR-002, FR-003, FR-007, FR-009, FR-011).
- [x] T005 Implement immutable alert data, canonical severity/status values, and field validation in `src/alert_manager/models.py`; satisfy every quoted field constraint in T004 (FR-002, FR-003, FR-007, FR-009, FR-011).
- [x] T006 Define controlled validation, not-found, and persistence exception types in `src/alert_manager/service.py` for consistent CLI handling (FR-011, FR-015, NFR-005).
- [x] T007 [P] Write failing storage contract tests in `tests/contract/test_storage_contract.py` for round trips, missing files, malformed/unreadable/oversized JSON, invalid schema, duplicate IDs, and preservation of original bytes after load/write failures; add `tests/fixtures/duplicate-json-keys.json` as raw JSON containing repeated `"title"` keys within one alert object and assert rejection without changing its exact bytes. Verify POSIX mode `0600` after creation/replacement, or verify on Windows that the inherited ACL grants access only to the current user (FR-010, FR-015, NFR-003, NFR-006).
- [x] T008 Implement JSON loading and strict whole-document validation in `src/alert_manager/storage.py`: use the `{"alerts": [...]}` shape, treat a missing file as empty, reject files over 256 MiB before parsing, reject duplicate object keys at every nesting level as well as duplicate alert IDs, and preserve invalid or unreadable files byte-for-byte without rewriting (FR-010, FR-011, NFR-003).
- [x] T009 Implement validated JSON serialization to a same-directory temporary file and replacement in `src/alert_manager/storage.py`; clean up failed temporary files when possible, preserve the prior target on failure, and report success only after replacement. On POSIX, set mode `0600` on temporary and final store files; verify permission bits after creation/replacement. On Windows, inherit a parent directory ACL restricted to the current user and verify the effective ACL (FR-010, FR-015, NFR-003, NFR-006).

**Checkpoint**: Shared model and storage contracts pass before story work starts.

---

## Phase 3: User Story 1 - Record and review alerts (Priority: P1) — MVP

**Goal**: Analysts can create alerts, list all records, retrieve by ID, and retain changes across CLI invocations.

**Independent Test**: Create one valid alert, list and retrieve it, restart the CLI using the same store, and verify all fields, UUID ordering, and persisted values.

### Tests for User Story 1

- [x] T010 [P] [US1] Write service unit tests in `tests/unit/test_service.py` for create/list/get, UUID4 collision retry, injected UTC clock formatting, default `New` status, stable ascending UUID order, and unknown-ID behavior (FR-002, FR-003, FR-004, FR-013).
- [x] T011 [P] [US1] Write CLI contract tests in `tests/contract/test_cli_contract.py` for create/list/get and restart persistence using a temporary `--store` path; assert exit codes 0 for success, 2 for usage error, 3 for invalid input, 4 for missing alert, and 5 for persistence failure (FR-001, FR-004, FR-010, FR-015).

### Implementation for User Story 1

- [x] T012 [US1] Implement create/list/get use cases in `src/alert_manager/service.py`, using injected UUID/time providers and validated storage (FR-002, FR-003, FR-004, FR-011, FR-013).
- [x] T013 [US1] Implement `create`, `list`, and `get <id>` in `src/alert_manager/cli.py` and `src/alert_manager/__main__.py`; apply exit codes 0 success, 2 usage error, 3 invalid input, 4 not found, and 5 persistence failure (FR-001, FR-004, FR-015).
- [x] T014 [US1] Verify the User Story 1 acceptance scenarios with `tests/unit/test_service.py` and `tests/contract/test_cli_contract.py`; fix any failing behavior in the corresponding `src/alert_manager/` module (FR-002, FR-003, FR-004, FR-010, SC-001, SC-004).

**Checkpoint**: User Story 1 is an independently usable MVP.

---

## Phase 4: User Story 2 - Find and update investigations (Priority: P2)

**Goal**: Analysts can search/filter alerts and update permitted fields or set any supported status directly.

**Independent Test**: Seed alerts spanning distinct text, severities, and statuses; verify exact search/filter results and ordering, then update allowed fields/status and confirm persistence while ID and timestamp remain unchanged.

### Tests for User Story 2

- [x] T015 [P] [US2] Add service unit tests in `tests/unit/test_service.py` for case-insensitive substring search combined with optional severity and/or status filters (AND across all supplied criteria), ascending UUID output, permitted updates, immutable ID/timestamp, direct transitions between all statuses, and the SC-003 rejection matrix: blank title/description, title >200, description >4,000, invalid IP/severity/status, unknown update field, and unknown update/status/delete IDs. For every rejected mutation assert an actionable error and byte-for-byte unchanged persisted data (FR-005, FR-006, FR-007, FR-011, FR-013, SC-003, SC-005).
- [x] T016 [P] [US2] Add CLI contract tests in `tests/contract/test_cli_contract.py` for `search <text> [--severity <value>] [--status <value>]`, each optional filter alone and both together, AND matching, no-match output, and ascending UUID order; verify exit codes 0/2/3/4/5; exercise applicable SC-003 invalid-input cases and assert meaningful errors plus unchanged store bytes; then launch fresh CLI processes after update and status changes to verify persisted values and unchanged alert ID/creation timestamp (FR-005, FR-006, FR-007, FR-015, SC-003, SC-004, SC-005).

### Implementation for User Story 2

- [x] T017 [US2] Implement case-insensitive search with optional severity/status filters, AND-combine every supplied criterion, sort by ascending UUID, and implement permitted field updates/direct status assignment in `src/alert_manager/service.py` (FR-005, FR-006, FR-007, FR-013).
- [x] T018 [US2] Implement `search <text> [--severity <value>] [--status <value>]`, standalone `filter`, `update`, and `status` commands in `src/alert_manager/cli.py`; map exit codes to 0/2/3/4/5 as specified in `contracts/cli.md` (FR-005, FR-006, FR-007, FR-011, FR-015).

**Checkpoint**: Search and changes are deterministic, validated, and persisted.

---

## Phase 5: User Story 3 - Close out and report alert workload (Priority: P3)

**Goal**: Analysts can confirm individual deletions and view severity/status summary counts, including zero-count categories.

**Independent Test**: Verify a declined deletion preserves the alert, a confirmed deletion removes it after restart, missing IDs report not-found, and summary counts match a known store.

### Tests for User Story 3

- [x] T019 [P] [US3] Add service unit tests in `tests/unit/test_service.py` for confirmed/cancelled deletion, missing-ID deletion, and complete severity/status counts including zeroes (FR-008, FR-009).
- [x] T020 [P] [US3] Add CLI contract tests in `tests/contract/test_cli_contract.py` for interactive/non-interactive confirmation and cancellation; after confirmed deletion, launch a fresh CLI process and assert the alert is absent; after cancellation, launch a fresh CLI process and assert it remains; verify missing-ID code 4, persistence-failure code 5, success/cancellation code 0, and summary rendering. Exercise remaining SC-003 invalid store structures, duplicate IDs, duplicate JSON keys and simulated failed writes; each rejected mutation must produce a meaningful error and leave persisted data byte-for-byte unchanged (FR-008, FR-009, FR-015, SC-003, SC-004, SC-005).

### Implementation for User Story 3

- [x] T021 [US3] Implement single-record delete and complete category summary calculations in `src/alert_manager/service.py` (FR-008, FR-009).
- [x] T022 [US3] Implement `delete` confirmation and `summary` in `src/alert_manager/cli.py`; require affirmative confirmation for every deletion and use exit codes 0/2/3/4/5 as specified in `contracts/cli.md` (FR-008, FR-009, FR-015).

**Checkpoint**: All three user stories are independently verifiable.

---

## Phase 6: Polish, Validation, and Acceptance Evidence

**Purpose**: Validate cross-cutting requirements, preserve evidence, and obtain the required human decision.

- [x] T023 Add the independent subprocess-based acceptance harness in `validation/acceptance_harness.py`; drive only the published CLI contract and persisted JSON, without importing application modules (SC-006, NFR-004).
- [x] T024 Run unit and contract suites with `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` and summarize command, environment, pass/fail counts, failures, and the unittest `Ran N tests` total in `artifacts/validation/test-report.md`; fail the validation gate if N is zero (SC-006).
- [x] T025 Run `.\.venv\Scripts\ruff.exe check src tests` and preserve complete output and disposition of findings in `artifacts/validation/ruff-report.txt` (SC-006).
- [x] T026 Run `.\.venv\Scripts\bandit.exe -r src` and preserve complete output and disposition of findings in `artifacts/validation/bandit-report.txt` (SC-006).
- [x] T027 Run `.\.venv\Scripts\python.exe validation\acceptance_harness.py` against a fresh temporary store and preserve scenarios, results, and failures in `artifacts/validation/harness-report.md` (SC-006).
- [x] T028 Validate list, ID lookup, filter, and summary performance with 10,000 alerts on the documented development environment; require each operation to complete within 2 seconds and record environment, timings, and outcomes in `artifacts/validation/performance-report.md` (NFR-002, SC-002).
- [x] T029 Review CLI/storage errors and logs for unrelated sensitive data exposure, verify no AI/LLM functionality or dependency is present, and verify the local single-user/plaintext assumption, encryption-at-rest scope exclusion, POSIX mode `0600` and Windows current-user-only ACL; record the review and any remediation in `artifacts/validation/security-review.md` (FR-014, NFR-005, NFR-006, constitution Security and Alert Handling).
- [x] T030 Update `specs/001-security-alert-management/quickstart.md` with verified final commands and outcomes; keep failed or unavailable checks clearly reported (SC-006).
- [x] T031 Record the final human `ACCEPT` or `REJECT` decision and links to validation evidence in `artifacts/validation/human-decision.md` (SC-006, constitution Development and Acceptance Workflow).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T002 and T003 may run in parallel after T001 creates the project root files/directories.
- **Foundational (Phase 2)**: Depends on setup; model and storage contracts block all user stories. T004 precedes T005; T007 precedes T008 and T009; storage load precedes save.
- **User Stories (Phases 3–5)**: Depend on the foundation. Implement in priority order because the stories extend shared `service.py` and `cli.py` files.
- **Polish (Phase 6)**: Depends on all three stories. T023 precedes T027; test/quality/performance evidence tasks require the complete implementation.

### User Story Dependencies

- **US1 (P1)**: First deliverable and MVP; depends on setup and foundation only.
- **US2 (P2)**: Depends on the shared alert/store foundation and is scheduled after US1 because it extends the same service and CLI modules. Its tests can use seeded records.
- **US3 (P3)**: Depends on the shared alert/store foundation and is scheduled after US2 to avoid conflicting edits to the service/CLI modules. Its tests can use seeded records.

### Parallel Opportunities

- T002 and T003 touch separate files and can run in parallel after T001.
- Within each user story, the service unit-test task and CLI contract-test task touch separate files and can be authored in parallel before that story's implementation.
- In the polish phase, T025 and T026 can run in parallel after implementation; T024, T027, and T028 use separate evidence files and can run in parallel after their prerequisites.

## Parallel Examples

### User Story 1

```text
Task: T010 — write service unit tests in tests/unit/test_service.py
Task: T011 — write CLI contract tests in tests/contract/test_cli_contract.py
```

### User Story 2

```text
Task: T015 — add service unit tests in tests/unit/test_service.py
Task: T016 — add CLI contract tests in tests/contract/test_cli_contract.py
```

### User Story 3

```text
Task: T019 — add service unit tests in tests/unit/test_service.py
Task: T020 — add CLI contract tests in tests/contract/test_cli_contract.py
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete US1 and validate create/list/get plus persistence independently.
3. Stop for review at the US1 checkpoint; this is the minimum useful deliverable.
4. Add US2, then US3, running each story's tests before integrating it.
5. Complete quality gates, independent harness validation, evidence preservation, and final human decision.

## Notes

- Every checkbox line uses sequential task IDs; `[P]` is used only for tasks that touch separate files and have no dependency on unfinished work.
- `[US1]`, `[US2]`, and `[US3]` map to the corresponding stories in `spec.md`.
- Requirement and success-criterion IDs are included in task descriptions for traceability.
- **SC-004 verification map**: T011/T014 verify create persistence; T016 verifies update and status change in fresh CLI processes and checks ID/timestamp immutability; T020 verifies confirmed deletion and cancellation in fresh processes.
- **SC-003 verification map**: T015 covers service mutation rejection cases; T007/T008 cover invalid store structure, duplicate IDs, duplicate object keys and byte preservation; T016/T020 cover CLI errors and failed writes. Every rejected mutation asserts an actionable error and unchanged persisted bytes.
- Tasks T001–T031 are checked complete; the human decision recorded in `artifacts/validation/human-decision.md` is `ACCEPT`.
- **Execution-order deviation**: The shared `service.py` implementation included US2/US3 operations before T015/T019 tests were authored. Those tests were subsequently added and executed successfully; no requirements were changed or omitted.
