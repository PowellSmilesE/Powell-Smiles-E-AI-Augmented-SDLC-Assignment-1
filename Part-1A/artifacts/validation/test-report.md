# Unit and Contract Test Report

- **Command**: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- **Environment**: Windows 10 build 26200; Python 3.11.9
- **Result**: `Ran 41 tests`; 40 passed, 0 failed, 1 skipped.
- **Skip**: POSIX permission-bit verification is not available on Windows. The Windows inherited-ACL test ran and passed.
- **Exit code**: 0
- **Raw output**: [test-report-output.txt](test-report-output.txt)

The first full run had one failed search-filter assertion: the standalone filter correctly returned two
matching records, while the assertion expected one. The fixture assertion was corrected and the full
suite then passed. The initial run is preserved in [test-report-initial-full-run.txt](test-report-initial-full-run.txt).
Earlier red-phase outputs are also retained as `T004-initial-test-output.txt`,
`T007-initial-test-output.txt`, and `T010-T011-initial-test-output.txt`. The deletion-cancellation
prompt parsing failure and its repair are documented in
`T020-delete-cancel-test-failure-before-repair.txt`.
