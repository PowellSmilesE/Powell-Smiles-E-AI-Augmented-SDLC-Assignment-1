from evaluation.harness import GATES, aggregate, read_cases
from evaluation.score import score_case


def truth():
    return {
        "category": "sql_injection",
        "severity": "High",
        "start_line": 3,
        "end_line": 3,
        "remediation_terms": ["parameterized"],
    }


def prediction():
    return {
        "category": "sql_injection",
        "severity": "High",
        "start_line": 3,
        "end_line": 3,
        "explanation": "User input reaches SQL query execution without escaping.",
        "remediation": "Use parameterized SQL statements for every user supplied input.",
    }


def test_perfect_case():
    assert score_case({"findings": [truth()]}, {"findings": [prediction()]})["score"] == 1


def test_missing_finding_is_not_perfect():
    assert score_case({"findings": [truth()]}, {"findings": []})["score"] < 1


def test_extra_false_positive_is_penalized():
    out = score_case({"findings": []}, {"findings": [prediction()]})
    assert out["score"] < 1


def test_severity_mismatch_is_penalized():
    assert (
        score_case({"findings": [truth()]}, {"findings": [prediction() | {"severity": "Low"}]})[
            "score"
        ]
        < 1
    )


def test_case_count_and_gate_denominator():
    assert len(read_cases()) == 25
    assert len(GATES) == 6


def test_incomplete_run_never_passes():
    cases = read_cases()
    result = aggregate([], cases, {x: "pass" for x in GATES})
    assert result["aggregate"] == "FAIL"
    assert result["denominator"] == 25


def test_unscored_gate_never_passes():
    cases = read_cases()
    result = aggregate([], cases, {x: "pass" for x in GATES if x != "no_persistence"})
    assert result["gates"]["no_persistence"] == "unscored"


def test_critical_recall_fails_when_one_category_missing():
    second = truth() | {"category": "command_injection"}
    result = score_case({"findings": [truth(), second]}, {"findings": [prediction()]})
    assert result["critical_recall"] == 0.5


def test_duplicate_finding_is_penalized():
    result = score_case({"findings": [truth()]}, {"findings": [prediction(), prediction()]})
    assert result["components"]["finding_f1"] < 1
