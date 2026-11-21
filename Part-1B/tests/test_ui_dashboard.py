"""Presentation-only regression tests for the security review dashboard."""

from fastapi.testclient import TestClient

from independent_review.api import app

client = TestClient(app)


def test_dashboard_contains_editor_and_results_sections():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    html = response.text
    assert 'id="source"' in html
    assert 'id="consent"' in html
    assert 'id="send"' in html
    assert 'id="findings"' in html
    assert "Human review required" in html
    assert "@media (max-width:880px)" in html


def test_dashboard_preserves_consent_before_request():
    html = client.get("/").text
    assert "const consent_external_transfer = consentInput.checked" in html
    assert "!consentInput.checked" in html
    assert "body: JSON.stringify({source, consent_external_transfer})" in html
    assert "fetch('/api/review'" in html


def test_dashboard_does_not_write_browser_storage_or_render_untrusted_html():
    html = client.get("/").text
    for forbidden in ("localStorage", "sessionStorage", "indexedDB", "document.cookie", "innerHTML", "eval("):
        assert forbidden not in html
    assert "el.textContent = String(value ?? '')" in html
    assert "findingsContainer.replaceChildren()" in html


def test_dashboard_example_does_not_enable_consent():
    html = client.get("/").text
    assert "consentInput.checked = false" in html
    assert "shell=True" in html
    assert "sourceInput.value !== source" in html
