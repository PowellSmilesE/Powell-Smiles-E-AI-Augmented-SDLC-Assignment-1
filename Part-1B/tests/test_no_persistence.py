"""Check application-owned persistence behavior using a stubbed review service."""

from fastapi.testclient import TestClient

from independent_review import api
from independent_review.contracts import ReviewResult


def test_review_api_does_not_persist_source(monkeypatch, tmp_path):
    marker = "SYNTHETIC_PERSISTENCE_MARKER_59271"

    def fake_review(_source):
        return ReviewResult(
            analysis_summary="No confirmed security vulnerabilities found.",
            findings=[],
        )

    monkeypatch.setattr(api, "review_source", fake_review)
    monkeypatch.chdir(tmp_path)

    client = TestClient(api.app)

    response = client.post(
        "/api/review",
        json={
            "source": marker,
            "consent_external_transfer": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"

    # Check application-created files in the isolated working directory.
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert marker not in path.read_text(encoding="utf-8", errors="ignore"), (
                f"Source marker persisted in {path}"
            )


def test_ui_does_not_expose_browser_storage_calls():
    client = TestClient(api.app)
    html = client.get("/").text

    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "indexedDB" not in html
    assert "document.cookie" not in html
    assert client.get("/").headers["cache-control"] == "no-store"
