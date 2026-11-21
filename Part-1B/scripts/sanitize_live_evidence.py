"""Produce score-equivalent, explicitly transformed public evaluation rows.

Run from Part-1B with `python scripts/sanitize_live_evidence.py`.
No Groq calls, no changes to original files. This is a *score reconstruction*
artifact and not the verbatim model transcript.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evaluation.harness import GATES, aggregate, check_invariants, read_cases, verify_freeze
from evaluation.score import score_case
from independent_review.contracts import ReviewResult

RUN = "20261121T150550Z"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / f"live-{RUN}.jsonl"
FINAL = ROOT / "results" / f"final-{RUN}.json"
PUBLIC = ROOT / "evaluation" / "public_results"
OUT = PUBLIC / f"sanitized-live-{RUN}.jsonl"
MANIFEST = PUBLIC / f"sanitized-live-{RUN}.manifest.json"

PLACEHOLDER_EXPLANATION = (
    "Sanitized explanatory placeholder used exclusively for reproducible benchmark scoring."
)
PLACEHOLDER_REMEDIATION = (
    "Sanitized corrective placeholder used exclusively for scoring comparison."
)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    verify_freeze()
    if not RAW.is_file():
        raise SystemExit(f"Missing private original raw run: {RAW}")
    if not FINAL.is_file():
        raise SystemExit(f"Missing immutable final report: {FINAL}")
    if OUT.exists() or MANIFEST.exists():
        raise SystemExit("Public evidence already exists; refusing to overwrite")

    cases = read_cases()
    final = json.loads(FINAL.read_text(encoding="utf8"))
    originals = [json.loads(line) for line in RAW.read_text(encoding="utf8").splitlines() if line.strip()]
    if len(originals) != len(cases) or len(originals) != 25:
        raise SystemExit("Unexpected run denominator")
    by_id = {case["case_id"]: case for case in cases}
    if len(by_id) != 25 or {r["case_id"] for r in originals} != set(by_id):
        raise SystemExit("Case IDs mismatch or duplicates")

    sanitized = []
    for row in originals:
        if set(row) != {"case_id", "output"}:
            raise SystemExit(f"Original row not output-only: {row.get('case_id')}")
        case = by_id[row["case_id"]]
        original_output = ReviewResult.model_validate(row["output"])
        if not check_invariants(original_output, case["source"]):
            raise SystemExit(f"Original invariants failed: {row['case_id']}")
        src = original_output.model_dump(mode="json")
        new_findings = []
        for finding in src["findings"]:
            options = [
                truth for truth in case["findings"] if truth["category"] == finding["category"]
            ]
            # For this frozen benchmark, each category appears at most once per case.
            if len(options) > 1:
                raise SystemExit("Ambiguous category; manual redaction needed")
            replacement = dict(finding)
            replacement["explanation"] = PLACEHOLDER_EXPLANATION
            replacement["remediation"] = PLACEHOLDER_REMEDIATION
            if options:
                terms = options[0]["remediation_terms"]
                original_remediation_ok = (
                    len(finding["explanation"].strip()) >= 25
                    and len(finding["remediation"].strip()) >= 25
                    and any(term in finding["remediation"].lower() for term in terms)
                )
                if any(term in PLACEHOLDER_REMEDIATION.lower() for term in terms):
                    raise SystemExit("Placeholder accidentally matches a scoring rubric term")
                if original_remediation_ok:
                    replacement["remediation"] += " " + terms[0]
            new_findings.append(replacement)
        sanitized_output = {
            "analysis_summary": "Sanitized review summary for independent score reconstruction.",
            "findings": new_findings,
        }
        sanitized_model = ReviewResult.model_validate(sanitized_output)
        if not check_invariants(sanitized_model, case["source"]):
            raise SystemExit(f"Sanitized invariants failed: {row['case_id']}")
        original_score = score_case(case, src)
        sanitized_score = score_case(case, sanitized_model.model_dump(mode="json"))
        if original_score != sanitized_score:
            raise SystemExit(f"Scoring changed for {row['case_id']}: {original_score} != {sanitized_score}")
        sanitized.append({"case_id": row["case_id"], "output": sanitized_output})

    gates = final["gates"]
    if set(gates) != set(GATES):
        raise SystemExit("Final gate set differs from code")
    result = aggregate(sanitized, cases, gates)
    for field in ("aggregate", "semantic_pct", "semantic_complete", "denominator", "critical_recall", "gates", "threshold_pct", "per_case_min_pct", "critical_case_recall_min_pct"):
        if result[field] != final[field]:
            raise SystemExit(f"Final report mismatch: {field}")
    for actual_case, recorded_case in zip(result["cases"], final["cases"]):
        for key, value in recorded_case.items():
            observed = actual_case.get(key)
            # Historical finalizer serialized two 0.75 scores as 0.7500000000000001.
            if key == "score" and isinstance(value, (int, float)):
                if observed is None or abs(observed - value) > 1e-12:
                    raise SystemExit(f"Case score mismatch: {recorded_case['case_id']}")
            elif observed != value:
                raise SystemExit(f"Case mismatch: {recorded_case['case_id']} / {key}")
    if result["aggregate"] != "PASS" or result["semantic_pct"] != 96.0:
        raise SystemExit("Unexpected final score")

    content = ("\n".join(json.dumps(row, ensure_ascii=False) for row in sanitized) + "\n").encode("utf8")
    PUBLIC.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(content)
    manifest = {
        "kind": "sanitized_score_reconstruction_not_raw_provider_transcript",
        "run": RUN,
        "case_count": len(sanitized),
        "source_data": "public frozen synthetic benchmark; source-backed finding evidence retained",
        "removed_or_replaced_fields": ["analysis_summary", "findings[].explanation", "findings[].remediation"],
        "preserved_fields": ["case_id", "findings[].category", "findings[].severity", "findings[].start_line", "findings[].end_line", "findings[].evidence"],
        "remediation_note": "Synthetic placeholders preserve only whether rubric terms were present; they are not model advice.",
        "original_raw_sha256": digest(RAW.read_bytes()),
        "sanitized_sha256": digest(content),
        "matches_final_report": True,
        "semantic_pct": result["semantic_pct"],
        "aggregate": result["aggregate"],
        "limitation": "Validates benchmark scores, structure, and source evidence; does not independently verify the original narrative text or gate test execution.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    print(f"PASS: {len(sanitized)} sanitized cases; semantic={result['semantic_pct']}%; aggregate={result['aggregate']}")
    print(f"Public rows: {OUT.relative_to(ROOT)}")
    print(f"Manifest: {MANIFEST.relative_to(ROOT)}")
    print("No raw provider narrative is copied. Review outputs before publishing.")


if __name__ == "__main__":
    main()
