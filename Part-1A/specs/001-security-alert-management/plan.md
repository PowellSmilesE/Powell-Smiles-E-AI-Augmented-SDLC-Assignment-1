# Implementation Plan: Security Alert Management

**Branch**: `001-security-alert-management` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-security-alert-management/spec.md`

## Summary

Deliver a local Python command-line tool for analysts to create, list, retrieve, search, filter,
update, change status, delete, and summarize security alerts. Keep the implementation to three
clear layers: CLI argument and output handling, alert business rules, and JSON-file persistence.
Use Python's standard library for runtime behavior, validate before mutation, and write JSON through
a temporary sibling file followed by same-directory replacement. Replacement is atomic on supported filesystems/platforms; a failed replacement must preserve the prior target.

## Technical Context

**Language/Version**: Python 3.11 or newer (standard library `enum`, `dataclasses`, `uuid`, `datetime`, `argparse`, and `ipaddress`).

**Primary Dependencies**: None at runtime. Configure `[build-system].requires = ["setuptools"]` and `build-backend = "setuptools.build_meta"`; define `[project]` with `name = "security-alert-manager"`, `requires-python = ">=3.11"`, and `dependencies = []`. Keep setuptools build-time only. Development checks: use `unittest`, Ruff, and Bandit as documented development tools.

**Storage**: One UTF-8 JSON file at `alerts.json` in the current working directory by default, overridable with `--store PATH`; it has a top-level `alerts` array. Missing file means an empty store. Invalid or unreadable contents are reported and preserved.

**Testing**: Python `unittest` for unit tests and CLI/storage contract tests; an independent acceptance harness validates the published CLI contract.

**Target Platform**: Local Windows, macOS, or Linux environment with Python 3.11+; one analyst process at a time.

**Project Type**: Single Python CLI application.

**Performance Goals**: For up to 10,000 alerts, list, ID lookup, filtering, and summary complete within 2 seconds on the documented development environment.

**Constraints**: No external database, AI/LLM, network service, or runtime package dependency. UUIDs and current time are generated at creation; tests inject controllable ID and clock providers. No concurrent writers or multi-user coordination. Reject JSON files larger than 256 MiB before parsing. Limit title to 200 Unicode characters and description to 4,000 Unicode characters.

**Scale/Scope**: One local JSON file and up to 10,000 alert records for the acceptance performance target; no authentication, bulk delete, import/export, or multi-user support.

## Constitution Check

- **Specification first**: PASS. The implementation is driven by the clarified feature spec and its acceptance scenarios.
- **Modular Python**: PASS. Three focused modules separate CLI, business rules, and persistence.
- **Determinism and validation**: PASS. Validate at CLI/service boundaries; inject UUID/time providers; use canonical severity/status values and UUID sorting.
- **Unit and contract tests**: PASS. Unit tests cover domain rules; contract tests exercise storage and CLI behavior, including failure cases.
- **Lint and static security**: PASS. Ruff and Bandit are planned quality gates; findings must be fixed or explicitly reviewed.
- **Independent validation and evidence**: PASS. Keep harness output and quality-gate results as review evidence; report failures accurately.
- **Human decision**: PASS. Release acceptance requires a recorded human ACCEPT or REJECT decision.

## Project Structure

### Documentation (this feature)

```text
specs/001-security-alert-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
├── checklists/
│   └── requirements.md
└── spec.md
```

### Source Code (Part-1A application root, to be created during implementation)

```text
src/alert_manager/
├── __init__.py
├── __main__.py       # `python -m alert_manager` entry point
├── cli.py            # Arguments, prompts, rendering, exit codes
├── models.py         # Alert and finite severity/status values
├── service.py        # Validation, CRUD, search/filter, transitions, summaries
└── storage.py        # JSON load, schema validation, atomic save

tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_service.py
└── contract/
    ├── __init__.py
    ├── test_storage_contract.py
    └── test_cli_contract.py
└── fixtures/
    └── duplicate-json-keys.json  # raw invalid JSON fixture

pyproject.toml        # Package/build metadata, src discovery, optional development tools, and Ruff configuration
```

**Structure Decision**: Use one small package under `src/alert_manager` with a separate `tests`
tree. This matches the required CLI/business/storage boundaries without adding a framework,
repository abstraction, database, or extra application layers. The paths above describe planned
future implementation; this plan creates documentation only.

## Module Responsibilities

- `cli.py`: Parse commands/options, obtain explicit delete confirmation, call the service, render
  stable user-facing output, and map validation/not-found/storage errors to stderr and exit codes.
- `models.py`: Define immutable alert data, canonical severity/status values, and shared field rules.
- `service.py`: Orchestrate use cases; validate inputs; generate/retry UUID4 values; obtain UTC time
  through an injected provider; implement search, AND filters, UUID sorting, updates, deletion, and
  category counts. It does not read or write files directly.
- `storage.py`: Resolve the selected store path; load and strictly validate JSON, rejecting duplicate
  object keys at any nesting level, duplicate IDs, and oversized documents; save through a
  same-directory temporary file and replacement; on POSIX apply mode `0600` to temporary and final
  store files; on Windows inherit the parent directory ACL (restricted by setup and verified during
  acceptance); map filesystem/JSON failures to storage errors without exposing raw contents.

### Storage Security Assumption

The store is local, single-user, and plaintext. Encryption at rest is outside the current scope.
On POSIX systems, store and temporary files use user-only read/write permissions (`0600`), verified
by inspecting permission bits. On Windows, store and temporary files inherit the parent directory
ACL; the operator must use a directory whose ACL grants access only to the current user, and
acceptance verification inspects that effective ACL. No separate ACL is authored by the application.

### Test Responsibilities

- Unit tests exercise model validation and service rules with in-memory/fake storage plus fixed ID
  and clock providers.
- Storage contract tests use temporary directories to verify valid round trips, missing files,
  malformed/oversized documents, duplicate IDs and duplicate object keys (using the raw fixture),
  preservation after simulated write failures, and platform-specific user-only permission
  verification (POSIX mode `0600` or the Windows inherited ACL).
- CLI contract tests invoke the module entry point in a subprocess with an isolated `--store` path;
  assert stdout, stderr, exit statuses, prompt/confirmation behavior, and persisted records.
- An independent harness drives the documented CLI contract and preserves its report as acceptance
  evidence. Unit tests authored with the implementation do not replace this check.
## Design Decisions

- `Alert` is an immutable-at-identity record. Updates create a changed copy while retaining the
  UUID and original timestamp; status is changed only through the status operation.
- UUID generation and time acquisition are injected into the service. Production defaults use
  UUID4 and the current UTC clock; deterministic tests supply fixed providers.
- The JSON document has schema `{"alerts": [...]}`. Loading validates every record, enum value,
  IP address, timestamp, and UUID uniqueness before exposing any records.
- A missing JSON file is an empty store. Invalid JSON, invalid schema, duplicate JSON object keys
  at any nesting level, duplicate alert IDs, and read errors are explicit storage errors; they fail
  closed and never trigger automatic reset, rewrite, or overwrite.
- Save by serializing the full validated store to a temporary file in the same directory, flushing
  and closing it, then replacing the target with `os.replace` on the same filesystem. If any step fails, report failure,
  clean up the temporary file when possible, and preserve the prior target. Replacement is atomic on supported filesystems/platforms, not an unconditional cross-platform guarantee. This is for a single writer, not a multi-process locking or backup system.
- Normalize filter values against documented enums. Search is a case-insensitive substring over
  title, description, and source IP; combined criteria use AND; results sort by ascending UUID.
- Delete requires explicit analyst confirmation. Provide an interactive confirmation and an
  explicit affirmative option for non-interactive use; missing IDs remain not-found errors.
- Use controlled application errors for validation, not-found, and storage failures. The CLI prints
  concise actionable messages to stderr and returns distinct non-zero exit codes for failures.

## Constitution Re-check

The design remains within the constitution: it is spec-led, modular, deterministic under injected
UUID/time dependencies, validated at boundaries, covered by unit and contract tests, checked with
linting and static security analysis, and reviewed with preserved independent-harness evidence.
No constitution exception or complexity-tracking entry is needed.
