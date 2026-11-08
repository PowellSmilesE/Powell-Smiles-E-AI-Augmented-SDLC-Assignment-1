# Research: Security Alert Management

## Decisions

### Runtime and module structure

- **Decision**: Target Python 3.11+ and use only the standard library at runtime. Keep CLI,
  business rules, and persistence in distinct modules under `src/alert_manager`.
- **Rationale**: Python is an explicit constraint. Standard-library argument parsing, UUID, UTC
  datetime, IP-address validation, JSON, and filesystem primitives cover the requirements without
  adding deployment or dependency-management burden.
- **Alternatives considered**: A CLI framework and a persistence framework. Both add dependencies
  and abstractions unnecessary for a small local assignment.

### Editable installation for the `src/` layout

- **Decision**: Configure setuptools in `pyproject.toml` as a build-time backend using
  `[build-system].requires = ["setuptools"]` and `build-backend = "setuptools.build_meta"`; define a
  `[project]` table with `name = "security-alert-manager"`, a Python requirement, and empty runtime
  dependencies, discover the application package from `src/`, and provide optional `dev`
  dependencies for Ruff and Bandit.
  Use a local virtual environment and `python -m pip install -e ".[dev]"` in PowerShell.
- **Rationale**: An editable install makes `python -m alert_manager` work without changing
  `PYTHONPATH`, activating a shell script, or relying on a global package installation. Setuptools
  remains a build-time dependency; the application has no runtime dependencies.
- **Alternatives considered**: Setting `PYTHONPATH=src` for every command. That requires maintaining
  shell environment state and is easier to omit from subprocess or later commands.

### Testing and quality tools

- **Decision**: Use `unittest` for unit and contract tests, Ruff for linting, and Bandit for static
  security analysis. Keep Ruff and Bandit as development tools, not runtime dependencies.
- **Rationale**: `unittest` is included with Python and can exercise both direct module contracts and
  subprocess CLI behavior. Ruff and Bandit provide separate lint and security gates requested by
  the constitution.
- **Alternatives considered**: `pytest` as a test-runner dependency and a larger collection of
  overlapping linters. Neither is necessary for the expected scope.

### JSON schema and safe writes

- **Decision**: Store a top-level object containing an `alerts` array. Validate the complete file
  before use, rejecting duplicate object keys at every nesting level and duplicate alert IDs. Write
  to a temporary file in the target directory and replace the original only after successful
  serialization and flush. Apply POSIX mode `0600` to temporary and final store files.
- **Rationale**: A small explicit envelope allows future schema metadata; full validation catches
  malformed records and duplicate UUIDs. Same-directory replacement avoids exposing a partially written target on supported filesystems/platforms; atomicity is not an unconditional cross-platform guarantee. Limit JSON input to 256 MiB before parsing.
- **Alternatives considered**: A bare array, direct overwrite, automatic repair, or backup rotation.
  A bare array offers no obvious place for schema metadata; direct overwrite can truncate data;
  repair/reset violates fail-closed behavior; backups add complexity outside current scope.

### Local storage threat assumption

- **Decision**: Treat the JSON file as local single-user plaintext storage. Encryption at rest is
  outside the current scope. POSIX uses user-only read/write mode `0600`; Windows inherits a parent
  directory ACL restricted to the current user, and acceptance verifies the effective ACL.
- **Rationale**: The feature has no authentication or multi-user support; limiting local file
  permissions where supported is a proportionate safeguard without adding key management.

### Identity, time, and deterministic tests

- **Decision**: Use UUID4 and an injected UTC clock, formatted as RFC 3339 with whole-second
  precision and trailing `Z`. Inject ID and clock providers into business logic for deterministic
  tests; retry UUID4 generation if the ID is already present.
- **Rationale**: UUIDs avoid sequential identifiers, and UTC strings are unambiguous. Dependency
  injection keeps time and randomness from making business tests flaky while preserving production
  behavior.
- **Alternatives considered**: Sequential or timestamp-derived IDs, local-time timestamps, and
  hard-coded real-time calls in business logic. These complicate uniqueness, portability, or tests.

### Concurrency and durability boundary

- **Decision**: Support a single local writer at a time. Use same-directory replacement for writes (atomic where supported); do not
  implement locking, multi-process conflict resolution, or a backup/restore workflow.
- **Rationale**: The spec scopes the application to a local analyst and excludes multi-user
  concurrency. Same-directory replacement handles the relevant partial-write risk on supported platforms without a database.
- **Alternatives considered**: File locks, transaction journals, database migration, and automatic
  recovery. They are disproportionate to the assignment and change the storage model.

## Resolved Context

There are no unresolved technical choices that block the plan. The specification fixes CLI scope,
fields, severity/status values, ID behavior, timestamp format, invalid-store policy, deletion
confirmation, filters, and sort order. The implementation plan selects concrete module boundaries,
JSON write strategy, and development checks consistent with those requirements.


## Primary References

- Python 3.11 standard library: [argparse](https://docs.python.org/3.11/library/argparse.html), [ipaddress](https://docs.python.org/3.11/library/ipaddress.html), [uuid](https://docs.python.org/3.11/library/uuid.html), [datetime](https://docs.python.org/3.11/library/datetime.html), [unittest](https://docs.python.org/3.11/library/unittest.html), [tempfile](https://docs.python.org/3.11/library/tempfile.html), [os.replace](https://docs.python.org/3.11/library/os.html#os.replace), and [json](https://docs.python.org/3.11/library/json.html).
- Quality checks: [Ruff linter](https://docs.astral.sh/ruff/linter/) and [Bandit CLI](https://bandit.readthedocs.io/en/latest/man/bandit.html).
