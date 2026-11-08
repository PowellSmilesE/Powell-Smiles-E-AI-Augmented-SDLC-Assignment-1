# Feature Specification: Security Alert Management

**Feature Branch**: `001-security-alert-management`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: Python CLI for security analysts to record, search, track, and report security alerts with deterministic JSON-file persistence.

## Clarifications

### Session 2026-11-04

- Q: How should the system generate alert IDs, and what should it do if a generated ID already exists? → A: Generate UUID4 IDs and retry if an ID collision occurs.
- Q: Which status transitions should the system allow? → A: Any supported status may change directly to any other supported status, including backward changes.
- Q: What exact timestamp format should each alert use? → A: UTC RFC 3339 with whole-second precision and a trailing `Z` (for example, `2026-11-04T12:30:45Z`).
- Q: How should the CLI respond when the JSON store is missing, malformed, unreadable, or contains duplicate IDs? → A: Treat a missing file as an empty store; otherwise fail closed, report the problem, and preserve the file. Duplicate IDs make the store invalid.
- Q: What order should list, search, and filtered alert results use? → A: Stable ascending UUID order, with no other sort options.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record and review alerts (Priority: P1)

As a security analyst, I can create an alert and review the saved alert list or retrieve a specific alert so that investigation records are consistently available.

**Why this priority**: Reliable alert capture and retrieval are the foundation for tracking investigations.

**Independent Test**: Create one valid alert, list alerts, retrieve it by ID, and verify the returned fields match the saved record after restarting the CLI.

**Acceptance Scenarios**:

1. **Given** valid required alert details, **When** the analyst creates an alert, **Then** the system assigns a UUID4 ID and timestamp; if the ID already exists, it generates another UUID4 and retries, applies default status `New`, and confirms creation.
2. **Given** one or more stored alerts, **When** the analyst lists alerts, **Then** every alert is shown once in ascending UUID order.
3. **Given** an existing alert ID, **When** the analyst retrieves it, **Then** all its fields are displayed.
4. **Given** an unknown alert ID, **When** the analyst retrieves it, **Then** a clear not-found error is shown and stored data remains unchanged.

---

### User Story 2 - Find and update investigations (Priority: P2)

As a security analyst, I can search and filter alerts and update permitted details or investigation status so that I can find and maintain work consistently.

**Why this priority**: Analysts need to locate relevant records and keep investigation information current.

**Independent Test**: Create alerts with distinct text, severities, and statuses; search/filter them, edit allowed fields, and verify matching results and persisted changes.

**Acceptance Scenarios**:

1. **Given** alerts with different titles, descriptions, and source IPs, **When** the analyst searches a text term, **Then** all and only alerts containing the case-insensitive term in those fields are returned, ordered by ascending UUID.
2. **Given** alerts with different severities and statuses, **When** one or both filters are provided, **Then** only alerts matching every supplied filter are returned, ordered by ascending UUID.
3. **Given** an existing alert, **When** the analyst updates its title, description, source IP, or severity with valid values, **Then** those fields change and all other fields remain unchanged.
4. **Given** an existing alert, **When** the analyst changes its status through the status operation to an allowed status, **Then** the new status is persisted and displayed.
5. **Given** an invalid field, severity, status, or alert ID, **When** the analyst attempts an update, **Then** the system reports the validation error and leaves the record unchanged.

---

### User Story 3 - Close out and report alert workload (Priority: P3)

As a security analyst, I can delete an alert with deliberate confirmation and see summary counts so that records can be managed and workload can be reviewed.

**Why this priority**: Removal and summaries support cleanup and operational reporting after core capture and retrieval work.

**Independent Test**: Verify deletion cancellation preserves a record, confirmed deletion removes it, and summary counts match a known set of alerts.

**Acceptance Scenarios**:

1. **Given** an existing alert, **When** deletion is requested without confirmation, **Then** the system asks for confirmation and does not delete the record.
2. **Given** a pending deletion confirmation, **When** the analyst confirms, **Then** the record is deleted; when the analyst declines, the record remains.
3. **Given** alerts in known severity and status categories, **When** the analyst requests a summary, **Then** counts for every supported category, including zero-count categories, equal the stored records.
4. **Given** no alerts, **When** the analyst requests a summary, **Then** all category counts are zero.

### Edge Cases

- Empty store: listing returns an empty result and summary returns zero for every category.
- Duplicate titles or identical alert contents: each created alert receives a distinct ID and remains independently retrievable.
- A missing persistence file is treated as an empty store. Malformed, unreadable, or structurally invalid JSON, including duplicate alert IDs or duplicate JSON object keys at any nesting level, causes a clear error; the CLI fails closed, preserves the file, and does not claim a write succeeded.
- Persistence write failure: the CLI reports failure and does not report the requested operation as successful.
- Missing, blank, excessively long, or wrong-format field values: validation fails before changing stored data.
- Invalid IP address, unsupported severity/status, unknown update field, and unknown alert ID: each produces a clear error without partial mutation.
- Search with no matches returns an empty result; combining text search and filters applies all criteria.
- Delete of a missing ID reports not found and leaves the store unchanged; cancellation is treated as a non-error outcome.
- Interrupted or repeated status updates preserve a valid, explicitly displayed status.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a command-line interface for security analysts to manage alerts.
- **FR-002**: The system MUST create an alert with a unique stable UUID4 ID, title, description, source IP address, severity, status, and timestamp. If the generated ID already exists in the store, it MUST generate another UUID4 and retry without overwriting an alert.
- **FR-003**: The system MUST default a new alert's status to `New` and assign its creation timestamp in UTC using RFC 3339 with whole-second precision and a trailing `Z` (for example, `2026-11-04T12:30:45Z`).
- **FR-004**: The system MUST list all alerts and retrieve a single alert by ID.
- **FR-005**: The system MUST support case-insensitive text search across title, description, and source IP, and filtering by severity, status, or both.
- **FR-006**: The system MUST update title, description, source IP, and severity; status MUST be changed through the dedicated status operation. ID and creation timestamp MUST NOT be editable.
- **FR-007**: The supported statuses MUST be `New`, `In Progress`, `Resolved`, and `Closed`. A status change MUST set exactly one supported status and report invalid values clearly. Every status may change directly to any other supported status, including backward changes; no transition is prohibited.
- **FR-008**: The system MUST delete an alert only after explicit confirmation; cancellation MUST preserve it. A request to delete an unknown ID MUST report not found.
- **FR-009**: The system MUST report counts by every supported severity and status, including categories with zero alerts. The supported severity values MUST be `Critical`, `High`, `Medium`, `Low`, and `Informational`, ordered from highest to lowest.
- **FR-010**: The system MUST persist alerts in a JSON file and reload them across CLI invocations without an external database. A missing file MUST be treated as an empty store; malformed, unreadable, or structurally invalid JSON, including duplicate alert IDs or duplicate object keys at any nesting level, MUST produce a clear error without modifying or replacing the file.
- **FR-011**: The system MUST validate input at command boundaries, reject invalid values without partial updates, and display actionable error messages.
- **FR-012**: The system MUST implement command handling, alert business rules, and JSON persistence in separate modules. The CLI calls business logic, and business logic does not perform file I/O.
- **FR-013**: The system MUST produce deterministic results for identical inputs and stored data, including ascending UUID order for list, search, and filtered results and stable summary output.
- **FR-014**: The system MUST NOT use AI or LLM functionality.
- **FR-015**: The CLI MUST distinguish successful operations from validation, not-found, and persistence failures; it MUST NOT claim success when an operation failed.

### Non-Functional Requirements

- **NFR-001**: Each CLI, business-logic, and persistence module boundary MUST expose an interface that unit or contract tests can exercise independently.
- **NFR-002**: For a store of up to 10,000 alerts, list, exact-ID retrieval, filtering, and summary operations MUST complete within 2 seconds on the supported development environment; the supported environment MUST be documented.
- **NFR-003**: The JSON file MUST remain valid JSON after each successful mutation. A missing file MUST represent an empty store; malformed, unreadable, or structurally invalid JSON, including duplicate object keys and duplicate alert IDs, MUST be reported and preserved without silent repair or replacement.
- **NFR-004**: Given the same alert data, searches, filters, and summaries MUST have stable output ordering and values across repeated runs.
- **NFR-005**: Error messages MUST identify the invalid input or failed operation without exposing unrelated sensitive information.
- **NFR-006**: On POSIX platforms, newly created and replaced store files and their temporary siblings MUST be readable and writable only by the current user (mode `0600`); acceptance verification MUST inspect the resulting permission bits. On Windows, the store and temporary siblings inherit the parent directory ACL; the documented setup MUST restrict that ACL to the current user, and acceptance verification MUST inspect the effective ACL. Encryption at rest is outside this scope.

### Key Entities *(include if data involved)*

- **Alert**: An independently managed security observation with unique ID, title, description, source IP, severity, status, and immutable creation timestamp in UTC RFC 3339 format with whole-second precision and a trailing `Z`.
- **Severity**: A documented finite classification used for alert triage and summary counts; supported values are `Critical`, `High`, `Medium`, `Low`, and `Informational`, ordered from highest to lowest.
- **Status**: One of `New`, `In Progress`, `Resolved`, or `Closed`, representing investigation progress.
- **Alert Summary**: Derived counts grouped by each supported severity and status; it does not modify alert records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance validation, analysts can create, list, and retrieve an alert with all required fields correct in 100% of valid test cases.
- **SC-002**: For a test dataset with 10,000 alerts, every list, exact-ID lookup, filter, and summary operation completes within 2 seconds on the documented supported environment.
- **SC-003**: Across valid and invalid input cases, 100% of rejected operations produce a clear error and leave persisted alerts unchanged.

  **Finite rejection matrix** (each case begins with a known persisted store; compare its exact bytes before and after, and assert an actionable error): blank title; blank description; title over 200 characters; description over 4,000 characters; invalid IP; unsupported severity; unsupported status; unknown update field; unknown alert ID for update/status/delete; invalid JSON root/alerts structure; duplicate alert IDs; duplicate JSON object keys; and simulated failed write. For invalid/unreadable stores, assert the persistence error and unchanged source bytes. Run mutation cases through both service/unit and CLI contract coverage where applicable.
- **SC-004**: After each successful create, update, status change, or delete, restarting the CLI yields exactly the persisted resulting alert set in 100% of persistence acceptance cases.
- **SC-005**: Search, severity/status filters, and category summaries return exactly the expected records/counts in 100% of the defined acceptance cases, including empty categories and no-match searches.
- **SC-006**: The final acceptance review has preserved evidence for unit tests, contract tests, linting, static security analysis, and an independent automated harness, followed by a recorded human ACCEPT or REJECT decision.

## Assumptions

- The application is operated locally by a security analyst; authentication and multi-user concurrency are outside this feature's scope.
- The JSON store is local single-user plaintext storage. Encryption at rest is outside the current scope; apply user-only file permissions where the platform supports them as specified by NFR-006.
- Alert IDs are generated by the system as UUID4 values, stable after creation, unique within the alert store, and not supplied by the analyst. A collision is handled by generating a new UUID4 and retrying; an existing record is never overwritten.
- Titles and descriptions are required non-empty text; title limit is 200 Unicode characters and description limit is 4,000 Unicode characters.
- Source IP accepts valid IPv4 or IPv6 textual addresses; hostnames and CIDR ranges are not accepted as source IP values.
- Search matches a case-insensitive substring in title, description, or source IP; search and supplied filters combine with logical AND. List, search, and filtered results are ordered by ascending UUID, with no other sort modes.
- Status may be changed directly from any supported status to any other supported status using the dedicated status operation, including backward changes; no transition graph is enforced.
- Delete confirmation is explicit for every request; there is no implicit bulk deletion.
- Severity uses the fixed values `Critical`, `High`, `Medium`, `Low`, and `Informational`, ordered from highest to lowest; summary counts include every value, even when its count is zero.
- JSON persistence is a single local file. Writes use a same-directory temporary file and replacement; concurrent writers and multi-process conflict handling are out of scope.
- No feature implementation is included in this specification phase.
