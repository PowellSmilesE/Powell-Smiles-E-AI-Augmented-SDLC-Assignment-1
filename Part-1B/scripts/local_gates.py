"""Generate conservative preflight gate statuses, not a formal six-gate attestation."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from evaluation.harness import GATES, read_cases
from independent_review.api import app


def main() -> None:
    client = TestClient(app)
    denied = client.post(
        "/api/review", json={"source": "print(1)", "consent_external_transfer": False}
    )
    ui = client.get("/").text
    # Only outcomes proved by the local checks are reported as PASS.
    checks = {
        "source_not_executed": "unscored",  # source-flow/code-execution audit outstanding
        "prompt_injection_resistance": "unscored",  # needs live model evidence
        "human_review_state": "pass"
        if (
            denied.status_code == 400
            and app.openapi()["components"]["schemas"].get("ReviewEnvelope") is not None
        )
        else "fail",
        "denominator_preservation": "pass" if len(read_cases()) == 25 else "fail",
        "credential_non_disclosure": "unscored",  # full agreed scope requires further tests
        "no_persistence": "unscored",  # full browser / app scope requires further tests
    }
    assert set(checks) == set(GATES)
    assert "localStorage" not in ui and "sessionStorage" not in ui
    path = Path("results/local-gates.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "statuses": checks,
                "note": "Conservative local preflight, not the final six-gate evidence",
            },
            indent=2,
        ),
        encoding="utf8",
    )
    print(path, checks)


if __name__ == "__main__":
    main()
