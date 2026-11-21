"""Reconcile real gate evidence against an existing run without replaying Groq calls.

The referenced evidence must have been created and personally reviewed outside this script.
No gate is inferred as passing merely from an absent field or a successful unit test.
"""

import argparse
import hashlib
import json
from pathlib import Path

from evaluation.harness import GATES, ROOT, aggregate, read_cases, verify_freeze


def validate_gate_evidence(document: dict) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if set(document.get("gates", {})) != set(GATES):
        raise ValueError("Evidence must cover exactly all six gates")
    reviewer = document.get("reviewer", "")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Human reviewer name is required")
    for gate in GATES:
        item = document["gates"][gate]
        status = item.get("status")
        if status not in {"pass", "fail", "unscored"}:
            raise ValueError(f"Invalid status for {gate}")
        if status == "pass":
            path_value = item.get("evidence_path", "")
            digest = item.get("sha256", "")
            if not isinstance(path_value, str) or not isinstance(digest, str):
                raise ValueError("Evidence reference and sha256 are required")
            evidence = (ROOT / path_value).resolve()
            if not evidence.is_relative_to(ROOT.resolve()) or not evidence.is_file():
                raise ValueError("Evidence must be a local file in this project")
            if hashlib.sha256(evidence.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Evidence changed or hash incorrect for {gate}")
        statuses[gate] = status
    return statuses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="Existing live run ID")
    parser.add_argument("--gate-evidence", required=True, type=Path)
    args = parser.parse_args()
    verify_freeze()
    results = ROOT / "results"
    raw = results / f"live-{args.run}.jsonl"
    if not raw.is_file():
        parser.error(f"Live collection not found: {raw}")
    document = json.loads(args.gate_evidence.read_text(encoding="utf8"))
    gates = validate_gate_evidence(document)
    rows = [
        json.loads(line) for line in raw.read_text(encoding="utf8").splitlines() if line.strip()
    ]
    report = aggregate(rows, read_cases(), gates)
    out = results / f"final-{args.run}.json"
    if out.exists():
        parser.error("Final report already exists: cannot overwrite historical evidence")
    report["gate_evidence_file"] = str(args.gate_evidence.resolve())
    report["reviewer"] = document["reviewer"]
    out.write_text(json.dumps(report, indent=2), encoding="utf8")
    print("Aggregate:", report["aggregate"])
    print("Semantic:", report["semantic_pct"])
    print("Report:", out)


if __name__ == "__main__":
    main()
