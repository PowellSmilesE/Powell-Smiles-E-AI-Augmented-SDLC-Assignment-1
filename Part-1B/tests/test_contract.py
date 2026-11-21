from pydantic import ValidationError

from independent_review.contracts import ReviewResult
from independent_review.service import InvalidReview, review_source


class Stub:
    def __init__(self, data):
        self.data = data

    def generate(self, *args):
        return self.data


def finding(**changes):
    result = {
        "category": "sql_injection",
        "severity": "High",
        "start_line": 2,
        "end_line": 2,
        "evidence": "cursor.execute(query)",
        "explanation": "This executes an attacker-controlled SQL statement.",
        "remediation": "Use parameterized SQL queries with separate bind variables.",
    }
    return result | changes


def test_valid_source_evidence():
    output = {"analysis_summary": "A vulnerable SQL execution is present.", "findings": [finding()]}
    assert (
        review_source("query = input()\ncursor.execute(query)", Stub(output)).findings[0].start_line
        == 2
    )


def test_reject_fabricated_line():
    output = {
        "analysis_summary": "A vulnerable SQL execution is present.",
        "findings": [finding(end_line=50)],
    }
    try:
        review_source("query = input()\ncursor.execute(query)", Stub(output))
    except InvalidReview:
        pass
    else:
        raise AssertionError("Missing line range accepted")


def test_reject_evidence_not_present():
    output = {
        "analysis_summary": "A vulnerable SQL execution is present.",
        "findings": [finding(evidence="os.system('rm -rf')")],
    }
    try:
        review_source("query = input()\ncursor.execute(query)", Stub(output))
    except InvalidReview:
        pass
    else:
        raise AssertionError("Fabricated evidence accepted")


def test_strict_schema():
    try:
        ReviewResult.model_validate(
            {"analysis_summary": "hello", "findings": [finding(extra=True)]}
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Extra field accepted")
