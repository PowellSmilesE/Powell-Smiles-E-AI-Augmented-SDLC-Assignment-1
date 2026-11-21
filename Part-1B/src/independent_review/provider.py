"""Minimal Groq transport. No raw request/response telemetry or on-disk caches."""

import os
import time
from typing import Any

import httpx


class ProviderError(Exception):
    """Generic provider failure; never includes user source or credentials."""


class GroqProvider:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def generate(self, system: str, user: str) -> dict[str, Any]:
        token = os.getenv("GROQ_API_KEY", "")
        if not token:
            raise ProviderError("Provider not configured")
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        if not model or len(model) > 100:
            raise ProviderError("Invalid model configuration")
        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        # At most three attempts, retries only transient transport/HTTP failures.
        # Caller-owned injected clients are not closed here.
        owned = self._client is None
        client = self._client or httpx.Client(timeout=60, follow_redirects=False, verify=True)
        try:
            for attempt in range(3):
                try:
                    response = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    if response.status_code in (429, 500, 502, 503, 504):
                        if attempt < 2:
                            time.sleep(2**attempt)
                            continue
                        raise ProviderError("Provider temporarily unavailable")
                    if response.status_code != 200:
                        raise ProviderError("Provider rejected request")
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    import json

                    return json.loads(content)
                except (httpx.TimeoutException, httpx.TransportError):
                    if attempt == 2:
                        raise ProviderError("Provider transport unavailable") from None
                    time.sleep(2**attempt)
                except (ValueError, KeyError, IndexError, TypeError):
                    raise ProviderError("Provider returned invalid JSON") from None
            raise ProviderError("Provider unavailable")
        finally:
            if owned:
                client.close()
