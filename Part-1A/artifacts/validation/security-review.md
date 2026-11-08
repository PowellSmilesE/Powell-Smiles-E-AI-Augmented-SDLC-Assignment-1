# Security Review

- The JSON store is local, single-user, and plaintext. Encryption at rest is outside scope.
- On Windows, the application creates a same-directory temporary file and replaces the target, so file
  access inherits the parent directory ACL. The recommended `.alert-store` directory was created with
  inheritance disabled and a FullControl rule for the current user only. `Get-Acl` and `icacls` showed
  only `Smiles\CodexSandboxOffline`; the Windows storage contract test verified the generated file
  inherits that one-entry ACL.
- The POSIX mode `0600` test is skipped on Windows. The implementation sets mode `0600` for POSIX
  temporary files before replacement; platform-specific verification remains available on POSIX.
- Storage errors are generic and do not print file contents. Unit/contract fixtures and reports use
  synthetic alert data; no production alert data was used.
- Source and project dependency metadata were reviewed for AI/LLM calls and dependencies; none are
  present. Bandit completed with no issues identified.
- Ruff completed with no findings. Unit/contract suite: 41 ran, 40 passed, 0 failed, 1 POSIX-only
  permission-bit check skipped; the Windows ACL test passed.

Evidence: [bandit-report.txt](bandit-report.txt), [ruff-report.txt](ruff-report.txt),
[test-report.md](test-report.md), [harness-report.md](harness-report.md), and
[performance-report.md](performance-report.md).
