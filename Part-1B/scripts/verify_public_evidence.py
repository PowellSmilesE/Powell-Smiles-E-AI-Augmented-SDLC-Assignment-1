"""Verify the public sanitized score-reconstruction package (no Groq calls)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evaluation.harness import aggregate, read_cases, verify_freeze

RUN = "20261121T150550Z"
ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "evaluation" / "public_results"
ROWS = PUBLIC / f"sanitized-live-{RUN}.jsonl"
MANIFEST = PUBLIC / f"sanitized-live-{RUN}.manifest.json"
FINAL = ROOT / "results" / f"final-{RUN}.json"


def main() -> None:
    verify_freeze()
    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    if manifest["kind"] != "sanitized_score_reconstruction_not_raw_provider_transcript":
        raise SystemExit("Wrong evidence kind")
    if hashlib.sha256(ROWS.read_bytes()).hexdigest() != manifest["sanitized_sha256"]:
        raise SystemExit("Sanitized rows do not match manifest hash")
    rows = [json.loads(line) for line in ROWS.read_text(encoding="utf8").splitlines() if line.strip()]
    final = json.loads(FINAL.read_text(encoding="utf8"))
    result = aggregate(rows, read_cases(), final["gates"])
    if len(rows) != manifest["case_count"] or len(rows) != 25:
        raise SystemExit("Case count mismatch")
    for key in ("aggregate", "semantic_pct", "semantic_complete", "denominator", "critical_recall", "gates", "threshold_pct", "per_case_min_pct", "critical_case_recall_min_pct"):
        if result[key] != final[key]:
            raise SystemExit(f"Final metric mismatch: {key}")
    for actual, expected in zip(result["cases"], final["cases"]):
        for key, expected_value in expected.items():
            observed = actual.get(key)
            if key == "score" and isinstance(expected_value, (int, float)):
                if observed is None or abs(observed - expected_value) > 1e-12:
                    raise SystemExit(f"Score mismatch: {actual['case_id']}")
            elif observed != expected_value:
                raise SystemExit(f"Case mismatch: {actual['case_id']} / {key}")
    if result["aggregate"] != "PASS" or result["semantic_pct"] != 96.0:
        raise SystemExit("Expected result not reproduced")
    print("PASS: 25/25 public sanitized rows validated")
    print("PASS: independent structure, source-evidence and benchmark scoring")
    print("PASS: 96.0% semantic accuracy; aggregate PASS")
    print("LIMITATION: narratives are placeholders, not verbatim Groq responses")


if __name__ == "__main__":
    main()
