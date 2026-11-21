"""Freezes only personally approved labels; does not grant human review automatically."""

import argparse
import hashlib
import json
from datetime import datetime, timezone

from evaluation.harness import ROOT, read_cases

FILES = (
    "evaluation/dataset/cases.jsonl",
    "evaluation/dataset/reviews.jsonl",
    "evaluation/score.py",
    "evaluation/harness.py",
    "specs/001-independent-review/spec.md",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer", required=True, help="Actual person approving all 25 labels")
    args = parser.parse_args()
    cases = read_cases()
    reviews = [
        json.loads(x) for x in (ROOT / FILES[1]).read_text(encoding="utf8").splitlines() if x
    ]
    if len(cases) != 25 or len(reviews) != 25 or len({c["case_id"] for c in cases}) != 25:
        parser.error("Expected exactly 25 distinct case IDs and reviews")
    if any(
        x.get("review_state") != "Reviewed" or x.get("reviewer") != args.reviewer for x in reviews
    ):
        parser.error("Every case must first be individually marked Reviewed by the actual reviewer")
    if {x["case_id"] for x in cases} != {x["case_id"] for x in reviews}:
        parser.error("Missing review rows")
    manifest = {
        "reviewer": args.reviewer,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "count": 25,
        "hashes": {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in FILES},
    }
    output = ROOT / "evaluation/dataset/freeze-manifest.json"
    if output.exists():
        parser.error("Freeze exists. Never overwrite historical freeze; create a new version")
    output.write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print("Dataset frozen:", output)


if __name__ == "__main__":
    main()
