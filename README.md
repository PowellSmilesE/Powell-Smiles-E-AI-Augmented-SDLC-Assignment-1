# AI-Augmented SDLC — Assignment 1

A software engineering assignment documenting AI-assisted development, implementation, testing, security validation, and evaluation through two **independent** Python projects.

- **Part-1A:** Security Alert Manager — a deterministic command-line application.
- **Part-1B:** AI Security Code Review Assistant — a FastAPI application that uses Groq for source-code security reviews.

> **Project distinction:** Part-1A does **not** use an LLM at runtime. Part-1B does, and explicitly requires consent before transferring submitted code to Groq.

## Contents

- [Project overview](#project-overview)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Part-1A: Setup and usage](#part-1a-setup-and-usage)
- [Part-1B: Setup and usage](#part-1b-setup-and-usage)
- [Verification and results](#verification-and-results)
- [Screenshots](#screenshots)
- [Security, privacy, and limitations](#security-privacy-and-limitations)

## Project overview

### Part-1A — Security Alert Manager

Part-1A implements a Python CLI for managing security alert records. The project includes specifications, implementation tasks, automated tests, and validation artifacts created as part of an AI-assisted software development workflow.

The application supports creating, listing, retrieving, searching, filtering, updating, changing the status of, and deleting alerts; it also generates summaries. Data is saved to a local JSON store, with input validation and documented error handling. There is no AI service, database server, or external API required at runtime.

**Documentation:** [Part-1A quickstart](Part-1A/specs/001-security-alert-management/quickstart.md) · [Human-review decision](Part-1A/artifacts/validation/human-decision.md)

### Part-1B — AI Security Code Review Assistant

Part-1B is a separate web-based Python security review assistant built with FastAPI and Groq. A user can submit Python source code and, after consenting to external transfer, request an AI-generated security review.

The application validates structured findings, source-line references, and evidence excerpts, and marks results as requiring human review. It includes a frozen 25-case security benchmark, scoring logic, security-gate evidence, and public sanitized data for score reconstruction.

**Documentation:** [Part-1B README](Part-1B/README.md) · [Final evaluation report](Part-1B/results/final-20261121T150550Z.json) · [Public evaluation evidence](Part-1B/evaluation/public_results/)

## Repository structure

```text
.
├── Part-1A/
│   ├── src/alert_manager/                # CLI application
│   ├── tests/                            # Automated tests
│   ├── specs/                            # Specifications and quickstart
│   ├── artifacts/validation/             # Test and review evidence
│   └── pyproject.toml
├── Part-1B/
│   ├── src/independent_review/           # FastAPI, model provider and review logic
│   ├── evaluation/dataset/               # Frozen benchmark and reviews
│   ├── evaluation/public_results/        # Sanitized, score-reconstruction evidence
│   ├── evidence/                          # Security-gate evidence
│   ├── results/                           # Published final evaluation report
│   ├── scripts/                           # Evidence verification tools
│   ├── tests/                             # Automated tests
│   ├── README.md
│   └── pyproject.toml
└── README.md
```

## Prerequisites

- **Python 3.11 or later** (the projects were verified with Python 3.11.9).
- **Git**, if cloning from GitHub.
- **Windows PowerShell** for the commands below. Commands use the virtual environment's Python directly, so activating the environment is unnecessary.
- Internet connectivity for initial dependency installation.
- A **Groq API key** only when performing live reviews in Part-1B. No key is needed for the automated tests or verification of public sanitized evidence.

Clone the repository:

```powershell
git clone https://github.com/PowellSmilesE/Powell-Smiles-E-AI-Augmented-SDLC-Assignment-1.git
cd Powell-Smiles-E-AI-Augmented-SDLC-Assignment-1
```

Set up each part separately; they have their own `pyproject.toml` and virtual environment.

## Part-1A: Setup and usage

### Install

From the repository root:

```powershell
cd Part-1A
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Run the alert manager

```powershell
# Display available commands and options
.\.venv\Scripts\python.exe -m alert_manager --help

# Create a sample alert in a local JSON store
.\.venv\Scripts\python.exe -m alert_manager --store alerts.json create `
  --title "Suspicious login" `
  --description "Repeated failed authentication attempts" `
  --source-ip 192.0.2.10 `
  --severity High

# View stored alerts
.\.venv\Scripts\python.exe -m alert_manager --store alerts.json list

# Display severity and status totals
.\.venv\Scripts\python.exe -m alert_manager --store alerts.json summary
```

For real or private alert data, use a user-restricted local store rather than a file in a shared directory. See the [Part-1A quickstart](Part-1A/specs/001-security-alert-management/quickstart.md) for the Windows ACL setup, additional commands, and validation procedures.

### Run Part-1A checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\bandit.exe -r src
```

Then return to the repository root:

```powershell
cd ..
```

## Part-1B: Setup and usage

### Install

From the repository root:

```powershell
cd Part-1B
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Configure Groq for live reviews

The web application uses the `GROQ_API_KEY` environment variable. For the current PowerShell session, enter the key securely:

```powershell
$secure = Read-Host "Groq API key" -AsSecureString
$env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', $secure).Password
Remove-Variable secure
```

`GROQ_MODEL` is optional; the configured default is `openai/gpt-oss-120b`. **Do not commit API keys or a populated `.env` file.** The included [`.env.example`](Part-1B/.env.example) documents the available variables; it is not automatically loaded by this application.

### Start the web application

```powershell
.\.venv\Scripts\python.exe -m uvicorn independent_review.api:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in your browser. Paste Python source code, select the external-transfer consent checkbox, and click **Analyze**. The response contains structured findings for human review. Do not submit credentials, confidential code, or other material you are not authorized to send to Groq.

Stop the server with **Ctrl+C**.

### Run Part-1B checks

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m bandit -r src

# Reconstruct the published 96% score without contacting Groq
.\.venv\Scripts\python.exe -m scripts.verify_public_evidence
```

For the live evaluation workflow, frozen dataset policy, and evidence finalization process, follow the [Part-1B README](Part-1B/README.md). The historical benchmark and final report should not be overwritten or re-labeled.

## Verification and results

The following results were recorded for the completed assignment and subsequently checked against the supplied repository evidence:

| Verification | Part-1A | Part-1B |
|---|---|---|
| Automated tests | 40 passed, 1 POSIX-only test skipped | 32 passed |
| Linting | Ruff passed | Ruff passed |
| Security checks | Bandit passed | Six scoped evidence gates passed |
| Additional evaluation | 8 CLI acceptance scenarios passed | 25/25 benchmark cases; **96.0%** semantic accuracy |
| Final review | Human decision: **ACCEPT** | Aggregate evaluation: **PASS** |

Part-1B's evaluation additionally recorded **100% recall on designated critical cases**, above its **90% overall semantic threshold** and at or above its **75% per-case minimum**.

**Evidence:** [Part-1A validation artifacts](Part-1A/artifacts/validation/) · [Part-1B final report](Part-1B/results/final-20261121T150550Z.json) · [Part-1B gate evidence](Part-1B/evidence/) · [Part-1B public score reconstruction](Part-1B/evaluation/public_results/)

The original live Groq responses are retained privately. The public sanitized results can reproduce the scoring metrics, but their narrative text is **not a verbatim model transcript**.

## Screenshots

Screenshots can be added later without changing the application or evaluation results. Create a `docs/screenshots/` folder at the repository root, then insert your own image files and uncomment the corresponding Markdown lines below.

### Part-1A — Alert Manager CLI

<!-- Add docs/screenshots/part-1a-create-alert.png and uncomment the line below. -->
<!-- ![Part-1A: Creating a security alert](docs/screenshots/part-1a-create-alert.png) -->

<!-- Add docs/screenshots/part-1a-summary.png and uncomment the line below. -->
<!-- ![Part-1A: Alert summary output](docs/screenshots/part-1a-summary.png) -->

### Part-1B — AI Security Review

<!-- Add docs/screenshots/part-1b-review-ui.png and uncomment the line below. -->
<!-- ![Part-1B: Web interface and review submission](docs/screenshots/part-1b-review-ui.png) -->

<!-- Add docs/screenshots/part-1b-review-result.png and uncomment the line below. -->
<!-- ![Part-1B: Structured findings requiring human review](docs/screenshots/part-1b-review-result.png) -->

<!-- Add docs/screenshots/part-1b-evaluation.png and uncomment the line below. -->
<!-- ![Part-1B: Published evaluation verification result](docs/screenshots/part-1b-evaluation.png) -->

**Screenshot guidance:** Use synthetic demonstration content and remove API keys, personal information, machine usernames, and private file paths before committing images.

## Security, privacy, and limitations

- **Part-1A** uses local plaintext JSON storage and is intended for single-user operation. Windows store privacy depends on suitable filesystem ACLs. POSIX file-permission behavior was not independently verified on a POSIX host.
- **Part-1B** sends submitted source to Groq only with explicit user consent. Its model output requires human review; its findings should not be treated as automatically approved security decisions.
- Part-1B's six security gates are **scoped tests**. The prompt-injection and no-persistence findings do not establish universal security, absence of external data retention, or production readiness.
- The sanitized public evaluation evidence reconstructs the reported numerical scores, not the original live interaction or full model narratives.

This repository documents the assignment implementation and its recorded evidence; it is not a production-security certification.
