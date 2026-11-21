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
cd "C:\path\to\Part-1B-Fresh"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src evaluation scripts tests
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m scripts.local_gates
```

Review `evaluation/dataset/cases.jsonl` and `evaluation/dataset/reviews.jsonl` yourself. All 25
review statuses intentionally start as Pending. Make any legitimate corrections *before*
freezing, then set each review status to `Reviewed` with your real reviewer name.

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

## Git — begin immediately

```powershell
git status
git add .
git commit -m 'Initial independent Part 1B spec, implementation, tests and draft dataset'
git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO.git
git push -u origin main
```

The provided ZIP already contains an **initialized but uncommitted** Git repository. If the hidden `.git` directory does not survive extraction, first run `git init -b main`. Create an empty repo on GitHub and replace the URL. Do not claim the first commit
represents separate historical development stages; commit subsequent actual reviews, fixes,
and evaluations as they happen. **Do not push your API key, private code samples or raw live
provider responses**. Verify `.gitignore` before `git add`.

## Honest current status

Local engineering tests are verifiable; **no live Groq scoring has been performed** in this
new project. Six mandatory gates are not yet completely proven; in particular live prompt-
injection and broader scoped privacy audit are pending. The benchmark labels require your
independent review. Do not call the project ACCEPT before these items are verified.
