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
