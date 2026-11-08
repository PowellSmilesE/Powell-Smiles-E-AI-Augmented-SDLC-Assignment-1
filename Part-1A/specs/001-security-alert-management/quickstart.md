# Quickstart: Security Alert Management Validation

This guide describes the implemented validation workflow and the verified results from the Part-1A
workspace.

## Prerequisites

- Python 3.11 or newer and Windows PowerShell.
- Run commands from the Part-1A application root.
- Network access is needed once to install the build backend and development tools into the virtual environment.

## Install for the `src/` layout

The package is installed in editable mode from `pyproject.toml`. This registers `src/alert_manager`
with the virtual environment, so the venv's Python can run `python -m alert_manager` without a
`PYTHONPATH` setting or PowerShell activation.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run all later commands from the same Part-1A directory using the virtual environment's executables.
The commands use explicit paths so they work in PowerShell without changing its execution policy.

## Configure a user-only local store on Windows

The store is plaintext. Keep it in a directory whose ACL grants access only to the current user;
the JSON file and its temporary sibling inherit that ACL. Run once from the Part-1A root:

```powershell
$storeDirectory = Join-Path (Get-Location) ".alert-store"
New-Item -ItemType Directory -Force -Path $storeDirectory | Out-Null
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls.exe $storeDirectory /inheritance:r /grant:r "$currentUser`:(OI)(CI)F"
if ($LASTEXITCODE -ne 0) { throw "Could not restrict the alert-store ACL" }
Get-Acl -LiteralPath $storeDirectory | Format-List Owner,AccessToString
```

Use `--store "$storeDirectory\alerts.json"` for commands that read or modify alerts. The project
`.gitignore` excludes this private runtime directory.

## Validation commands

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m alert_manager --help
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\bandit.exe -r src
```

Verified on Windows 10 build 26200 with Python 3.11.9: editable installation completed; the test
suite ran 41 tests with 40 passing and one POSIX-only permission-bit test skipped; the Windows ACL
inheritance test passed. Ruff reported no findings, and Bandit reported no issues. Full output is
preserved in `artifacts/validation/test-report-output.txt`, `ruff-report.txt`, and
`bandit-report.txt`. The initial test failure and repair evidence is retained in the neighboring
`*-initial-*` and `*-failure-before-repair.txt` files.

## End-to-end acceptance scenarios

1. Create an alert with a valid IPv4 source and `High` severity. Confirm a UUID4 ID, UTC timestamp
   ending in `Z`, and `New` status are displayed.
2. Create records covering each severity and status, then list and filter them. Verify exact matches
   and ascending UUID ordering. Run `search <text> --severity High --status New` and verify only
   records matching all three criteria are returned, in ascending UUID order; also test each optional
   flag alone.
3. Update permitted fields and change status directly between any supported values. In a fresh CLI
   process, confirm the changes persisted and the ID and creation timestamp remain unchanged.
4. Attempt invalid severity, invalid status, malformed IP, unknown update field, and unknown ID.
   Also attempt blank title and description, title longer than 200 characters, and description
   longer than 4,000 characters. For every rejected mutation, confirm a meaningful error and compare
   persisted store bytes before and after; they must be identical.
5. Decline a deletion, restart the CLI, and verify the alert remains. Confirm another deletion, restart
   the CLI, and verify that alert is absent.
6. Verify summary counts include all categories, including zero values.
7. Load a missing file and verify an empty store. Then validate malformed JSON, unreadable file,
   invalid root/alerts structure, duplicate IDs, duplicate JSON object keys (using the raw fixture
   `tests/fixtures/duplicate-json-keys.json`), and files larger than 256 MiB each fail closed and
   preserve the original bytes. Each rejected mutation reports a meaningful error and leaves store
   bytes unchanged.
8. Simulate a failed write and confirm a meaningful error, byte-identical prior store, and no
   success message. On POSIX, verify created/replaced store files have mode `0600`; on Windows,
   inspect `Get-Acl -LiteralPath "$storeDirectory\alerts.json" | Format-List Owner,AccessToString`
   and verify the inherited ACL grants access only to the current user. The accepted threat model is
   local single-user plaintext storage; encryption at rest is outside scope.
9. Run the independent acceptance harness against the CLI contract and preserve its report in
   `artifacts/validation/harness-report.md`. It passed 8 scenarios with 0 failures. The 10,000-alert
   performance check passed with list 1.0384s, ID lookup 0.7415s, filter 0.7268s, and summary
   0.6850s; see `artifacts/validation/performance-report.md`. Complete command output is retained in
   the corresponding `.txt` files.

The final human ACCEPT/REJECT decision remains for the reviewer to record after reviewing the
preserved evidence.

See [the CLI contract](contracts/cli.md) and [the data model](data-model.md) for canonical values
and behavior.
