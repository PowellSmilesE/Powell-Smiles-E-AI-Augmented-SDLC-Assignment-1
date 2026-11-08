# Planned Development and Validation Quickstart

This is a future implementation guide, not evidence that an application exists or has been tested. The commands below describe the planned setup after implementation and before choosing a compliant provider. Start in the parent repository root, `Powell-Smiles-E-AI-Augmented-SDLC-Assignment-1`; the first command changes into its `Part-1B` directory, where the remaining commands run.

## Prerequisites

- Python 3.12 or newer and Git.
- A virtual environment.
- No provider key is needed for local/unit/contract tests. Do not submit real source to a provider until the endpoint is selected and its enforceable no-retention/no-training policy is verified.
- The evaluation dataset is not part of this plan and must be created/reviewed in its later approved phase.

## Install development dependencies (planned)

```powershell
cd Powell-Smiles-E-AI-Augmented-SDLC-Assignment-1/Part-1B
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The implementation must define a reproducible `pyproject.toml` and lock/constraints strategy before these commands are treated as executable documentation. Do not store credentials in source files or shell history.

## Local test and quality commands (planned)

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m bandit -r src
python -m pip_audit
```

Expected behavior after implementation: deterministic tests run without external provider credentials; provider calls are mocked; static checks exit nonzero when configured findings exist. A test report must include the collected and executed test counts. These commands have not been run as part of planning.

## Run the local UI (planned)

```powershell
python -m security_code_review --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/`. The application binds to loopback only. Provider settings are loaded from environment variables in the future implementation; source submission must remain disabled until compliant endpoint policy evidence is configured. The UI must not offer retry or cancellation. Reload/close clears displayed source, findings and review state.

## Manual contract scenarios (planned)

1. Submit blank text and confirm a structured `invalid_input` error, with no provider call.
2. Submit incomplete but non-empty Python and confirm it is treated as text, never executed.
3. Exercise 100,000-byte / 100,001-byte and 2,000-line / 2,001-line boundaries.
4. Mock valid AI output with empty findings and confirm `overall_assessment=no_findings`; mock one finding and verify exact evidence/source-line bounds and application-generated fields.
5. Mock malformed JSON, nested duplicate keys, unknown fields, invalid types, provider failure, and invalid evidence; confirm safe structured errors and no false clean result.
6. Without policy evidence, verify no request is sent to any provider and a `configuration_failure` is returned.
7. In browser tests, submit source/finding strings containing markup, script payloads and dangerous URLs; verify inert display and no navigation.
8. Confirm findings begin `pending`, change to `reviewed` only after the explicit action, and disappear after reload.
9. Run the future independent evaluation harness only after its reviewed dataset exists; require at least 15 cases, complete coverage, all gates passing and semantic score >=85% for aggregate PASS. Failed/unscored cases remain in denominator and force FAIL.

See [HTTP API contract](contracts/http-api.md), [data model](data-model.md), and [evaluation requirements in the spec](spec.md#evaluation-requirements). No tests or live provider calls were performed for this guide.
