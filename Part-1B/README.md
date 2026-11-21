# Independent AI Security Code Review — Part 1B (fresh project)

This is a newly authored, self-contained Part 1B implementation. Its files and benchmark are
not imported or inherited from any earlier assignment project. The original work should be
kept separate and unchanged, and must not be described as the baseline for this project.

## Acceptance policy — approved before final evaluation

- 25 independently reviewed, diverse Python security-review cases; all labels reviewed by you.
- **90%** mean semantic score, **75%** minimum per-case score.
- 100% strict response schemas and source-evidence invariants on all 25 cases.
- 100% finding recall on designated `critical-eval` cases.
- All six **scoped** mandatory gates must have actual, attributable PASS evidence.
- A missing response, unreviewed case, false claim, or unscored gate cannot be accepted.
- These are quality and application-scoped guarantees, not guarantees about Groq's internal
  retention, your entire OS, or production readiness.

## Windows PowerShell quickstart

```powershell
cd "C:\path\to\Powell-Smiles-E-AI-Augmented-SDLC-Assignment-1\Part-1B"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src evaluation scripts tests
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m scripts.local_gates
```

The 25 benchmark cases have completed human review and were frozen before the
final live evaluation. All 25 review records have status `Reviewed`.

The reviewed benchmark and freeze manifest are preserved in the repository.
Do not modify the frozen dataset or review labels after final evaluation.
For a new evaluation, establish a separate reviewed and frozen benchmark
rather than altering the historical evaluation evidence.

```powershell
.\.venv\Scripts\python.exe -m scripts.freeze --reviewer 'YOUR ACTUAL NAME'
$secure = Read-Host 'Groq API key' -AsSecureString
$env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', $secure).Password
Remove-Variable secure
.\.venv\Scripts\python.exe -m evaluation.run_live --delay-seconds 60
```

The live runner honestly returns FAIL until every required gate has independently
validated PASS. After live evaluation, consult `evidence/GATE-REVIEW-INSTRUCTIONS.md`
and use `python -m evaluation.finalize` to attach real gate evidence to the preserved run
without making another 25 requests. Review actual live model behavior, save the raw observations locally,
and independently attest the gated scope without fabricating evidence. Do not edit scores,
labels or evidence to force acceptance. Keep private code and keys out of Git.

To start the application:

```powershell
.\.venv\Scripts\python.exe -m uvicorn independent_review.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 . User code is transferred to Groq **only** with explicit consent.


## Final verified status — 21 November 2026

The independent Part-1B implementation has completed live Groq evaluation and final validation.

| Validation | Result |
|---|---|
| Aggregate evaluation | PASS |
| Semantic accuracy | 96.0% |
| Required semantic threshold | 90% |
| Frozen benchmark cases | 25/25 |
| Minimum per-case score | 75% |
| Critical vulnerability recall | 100% |
| Security gates | 6/6 PASS |
| Automated tests | 32 passed |
| Ruff | All checks passed |

The 25 benchmark labels were reviewed and frozen before the final evaluation.

**Final evaluation run:** `20261121T150550Z`

**Final report:** `results/final-20261121T150550Z.json`

**Security evidence:** `evidence/my-gate-review.json` and `evidence/gates/`

The six security gates cover source non-execution, prompt-injection resistance, human review, denominator preservation, credential non-disclosure, and no persistence.

These results apply to the documented tests and scope. Prompt-injection resistance is not universal, and external provider data retention is outside the application's verification scope.

### Evaluation evidence and reproducibility

The final PASS report and six security-gate evidence records are committed
to GitHub.

The raw live evaluation responses are intentionally excluded from GitHub
because they may contain source-code snippets and provider-generated content
that should not be published.

The raw results remain in the private local evaluation workspace.

**Reproducibility limitation:** The GitHub repository preserves the final
evaluation report and integrity-verified gate evidence, but it does not contain
all raw responses needed to independently recalculate the 96.0% semantic score.

The original evaluation was verified against locally retained raw responses.
Do not regenerate, fabricate, or publish sensitive responses solely to make
the repository self-contained.

The final evaluation covers the documented benchmark and security-gate scope;
it does not establish universal security or production readiness.

## Public Evaluation Reproducibility

The original live Groq responses are retained privately and are not
published in this repository.

A sanitized score-reconstruction dataset is available under
`evaluation/public_results/`.

The sanitized dataset contains all 25 evaluated cases and retains the
structured findings needed to reproduce the reported benchmark metrics.

To verify:

    python -m scripts.verify_public_evidence

Expected result:
- 25/25 cases verified
- Semantic accuracy: 96.0%
- Aggregate: PASS

The sanitized outputs are transformed evidence, not verbatim Groq
responses. Model-generated explanations and remediation narratives
have been replaced with scoring-preserving placeholders.

This allows independent score reconstruction but does not independently
authenticate the original model narratives or reproduce the live
provider interaction.