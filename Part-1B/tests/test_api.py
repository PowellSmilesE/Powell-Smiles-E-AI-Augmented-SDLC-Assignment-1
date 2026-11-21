from fastapi.testclient import TestClient

from independent_review.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_requires_consent():
    r = client.post(
        "/api/review", json={"source": "print('hello')", "consent_external_transfer": False}
    )
    assert r.status_code == 400


def test_bad_request_does_not_echo_secret():
    secret = "private_candidate_key_9f17"
    r = client.post("/api/review", json={"source": secret, "consent_external_transfer": False})
    assert secret not in r.text


def test_ui_no_storage():
    body = client.get("/").text
    assert "localStorage" not in body and "sessionStorage" not in body
    assert "consent_external_transfer" in body


def test_oversized_source_is_not_echoed():
    secret = "private_sentinel_45" + "x" * 25000
    r = client.post("/api/review", json={"source": secret, "consent_external_transfer": True})
    assert r.status_code == 422
    assert "private_sentinel_45" not in r.text
    assert r.headers["cache-control"] == "no-store"


def test_get_no_cache():
    r = client.get("/")
    assert r.headers["cache-control"] == "no-store"


def test_review_envelope_requires_human_review():
    from independent_review.contracts import ReviewEnvelope, ReviewResult

    result = ReviewResult(
        analysis_summary="No confirmed security vulnerabilities found.",
        findings=[],
    )

    envelope = ReviewEnvelope(model_output=result)

    assert envelope.review_required is True
    assert envelope.model_dump()["review_required"] is True


def test_api_requires_human_review(monkeypatch):
    from independent_review import api
    from independent_review.contracts import ReviewResult

    def fake_review(_source):
        return ReviewResult(
            analysis_summary="No confirmed security vulnerabilities found.",
            findings=[],
        )

    monkeypatch.setattr(api, "review_source", fake_review)

    response = client.post(
        "/api/review",
        json={
            "source": "x = 1",
            "consent_external_transfer": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["review_required"] is True


def test_provider_error_does_not_disclose_secret(monkeypatch):
    from independent_review import api
    from independent_review.provider import ProviderError

    secret = "SYNTHETIC_PRIVATE_KEY_7319"

    def failing_review(_source):
        raise ProviderError(f"Provider failed: {secret}")

    monkeypatch.setattr(api, "review_source", failing_review)

    response = client.post(
        "/api/review",
        json={
            "source": "print('test')",
            "consent_external_transfer": True,
        },
    )

    assert response.status_code == 503
    assert secret not in response.text
    assert response.json()["detail"] == "Review provider unavailable"


def test_invalid_review_does_not_disclose_source(monkeypatch):
    from independent_review import api
    from independent_review.service import InvalidReview

    secret = "SYNTHETIC_SOURCE_SECRET_8421"

    def failing_review(_source):
        raise InvalidReview(f"Invalid evidence containing {secret}")

    monkeypatch.setattr(api, "review_source", failing_review)

    response = client.post(
        "/api/review",
        json={
            "source": secret,
            "consent_external_transfer": True,
        },
    )

    assert response.status_code == 422
    assert secret not in response.text
    assert response.json()["detail"] == "Unable to validate review result"
