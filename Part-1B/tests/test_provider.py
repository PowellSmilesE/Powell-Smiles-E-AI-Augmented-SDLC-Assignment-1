import json

import httpx
import pytest

from independent_review.provider import GroqProvider, ProviderError


def test_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="not configured"):
        GroqProvider().generate("system", "source")


def test_provider_success(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_token")

    def handler(request):
        assert request.url.host == "api.groq.com"
        assert request.headers["authorization"] == "Bearer test_token"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"analysis_summary": "No issues", "findings": []})
                        }
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert GroqProvider(client).generate("sys", "user")["findings"] == []


def test_provider_error_does_not_disclose_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "sensitive_secret_test_token")

    def handler(_):
        return httpx.Response(401, text="sensitive_secret_test_token")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError) as e:
            GroqProvider(client).generate("sys", "user")
    assert "sensitive_secret_test_token" not in str(e.value)


def test_retry_transient_502(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_token")
    monkeypatch.setattr("independent_review.provider.time.sleep", lambda _: None)
    calls = []

    def handler(_request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(502, text="gateway transient")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"analysis_summary": "No issues found", "findings": []}
                            )
                        }
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = GroqProvider(client).generate("instructions", "code")
    assert len(calls) == 2
    assert result["findings"] == []


def test_502_exhaustion_is_generic(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_token")
    monkeypatch.setattr("independent_review.provider.time.sleep", lambda _: None)

    def handler(_request):
        return httpx.Response(502, text="SECRET_SHOULD_NOT_ESCAPE")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError, match="temporarily unavailable") as error:
            GroqProvider(client).generate("instructions", "source")
    assert "SECRET_SHOULD_NOT_ESCAPE" not in str(error.value)
