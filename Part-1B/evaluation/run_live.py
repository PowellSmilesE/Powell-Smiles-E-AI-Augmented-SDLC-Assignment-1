"""A full, honest 25-request Groq collection, never silently discards failed cases."""

import argparse
import json
import os
import time
from datetime import datetime, timezone

from evaluation.harness import ROOT, aggregate, read_cases, verify_freeze
from independent_review.provider import GroqProvider, ProviderError
from independent_review.service import InvalidReview, review_source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay-seconds", type=float, default=5)
    args = parser.parse_args()
    verify_freeze()
    if not os.getenv("GROQ_API_KEY"):
        parser.error("GROQ_API_KEY is not set")
    cases = read_cases()
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = ROOT / "results"
    output_dir.mkdir(exist_ok=True)
    rows = []
    provider = GroqProvider()
    for ix, case in enumerate(cases):
        if ix:
            time.sleep(max(0, args.delay_seconds))
        try:
            result = review_source(case["source"], provider)
            row = {"case_id": case["case_id"], "output": result.model_dump(mode="json")}
            print(f"{case['case_id']}: received structurally valid response")
        except (ProviderError, InvalidReview) as exc:
            row = {"case_id": case["case_id"], "error": type(exc).__name__}
            print(f"{case['case_id']}: {type(exc).__name__}")
        rows.append(row)
        # Raw generated findings contain code snippets: treat as confidential evidence.
        (output_dir / f"live-{run}.jsonl").write_text(
            "\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf8"
        )
    # No fabricated live prompt-injection verdict. Six gates must be independently
    # verified and attested before final PASS, not inferred from collection.
    gates_path = output_dir / f"gates-{run}.json"
    gates = json.loads(gates_path.read_text(encoding="utf8")) if gates_path.exists() else {}
    report = aggregate(rows, cases, gates)
    (output_dir / f"live-{run}.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print("Run:", run)
    print("Semantic:", report["semantic_pct"], "%, complete:", report["semantic_complete"])
    print("Aggregate:", report["aggregate"])
    print("Report:", output_dir / f"live-{run}.json")
    return 0 if report["aggregate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
