"""Diagnose one frozen case without saving generated source or responses."""

import argparse

from pydantic import ValidationError

from evaluation.harness import read_cases, verify_freeze
from evaluation.score import score_case
from independent_review.contracts import ReviewResult
from independent_review.prompt import SYSTEM_PROMPT, make_user_prompt
from independent_review.provider import GroqProvider, ProviderError
from independent_review.service import InvalidReview, validate_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()

    verify_freeze()

    matches = [case for case in read_cases() if case["case_id"] == args.case_id]

    if len(matches) != 1:
        parser.error("Case ID not found or not unique")

    case = matches[0]
    source = case["source"]

    try:
        raw = GroqProvider().generate(
            SYSTEM_PROMPT,
            make_user_prompt(source),
        )
    except ProviderError:
        print("RESULT: PROVIDER_ERROR")
        return 1

    try:
        result = ReviewResult.model_validate(raw)
    except ValidationError as exc:
        print("RESULT: SCHEMA_INVALID")

        for error in exc.errors(include_input=False):
            print("Field:", ".".join(map(str, error["loc"])))
            print("Error type:", error["type"])

        return 1

    lines = source.splitlines()

    for index, finding in enumerate(result.findings):
        if finding.end_line < finding.start_line or finding.end_line > len(lines):
            print(f"RESULT: INVALID_LINE_RANGE, finding={index}")
            return 1

        span = "\n".join(lines[finding.start_line - 1 : finding.end_line])

        if finding.evidence.strip() not in span:
            print(f"RESULT: EVIDENCE_MISMATCH, finding={index}")
            return 1

    try:
        validate_evidence(result, source)
    except InvalidReview:
        print("RESULT: EVIDENCE_VALIDATION_FAILED")
        return 1

    # Score the response against the unchanged frozen case.
    score = score_case(
        case,
        result.model_dump(mode="json"),
    )

    semantic_pct = round(score["score"] * 100, 2)

    print("RESULT: VALID")
    print("Number of findings:", len(result.findings))
    print("Categories:", [finding.category.value for finding in result.findings])
    print("Semantic score:", semantic_pct, "%")
    print("Scoring components:")

    for component, value in score["components"].items():
        print(f"  {component}: {value * 100:.2f}%")

    print("Expected findings:", score["expected"])
    print("Detected findings:", score["found"])
    print("Predicted findings:", score["predicted"])
    print("Critical recall:", round(score["critical_recall"] * 100, 2), "%")

    # This is diagnostic-only and does not replace an official full run.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
