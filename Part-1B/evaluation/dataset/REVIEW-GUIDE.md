# Human review of 25 new benchmark labels

Every case is new and is pending your independent review. Open `cases.jsonl` and verify:
1. Is the sample safe or genuinely vulnerable? Are all vulnerabilities identified?
2. Is the expected category justified from visible code? Avoid false positives.
3. Is expected severity justified using the written severity rubric?
4. Are `start_line` and `end_line` the narrowest defensible contiguous range?
5. Do remediation terms test an essential solution, without forcing one exact wording?
6. Are the 'critical-eval' multi-finding and direct-command cases correctly tagged?

Revise incorrect labels BEFORE you approve and freeze them. For every case only after your
own review, set `review_state` to `Reviewed` and set your real reviewer name. Do not mass
approve without looking at individual code; the freeze script checks recording, not judgment.

New project benchmark: no original Part 1B dataset, reports, prompts, or IDs copied.
