"""Stateless API; raw code is neither executed nor persisted by this application."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from .contracts import ReviewEnvelope, ReviewRequest
from .provider import ProviderError
from .service import InvalidReview, review_source

app = FastAPI(title="Independent AI Security Review", docs_url=None, redoc_url=None)


@app.middleware("http")
async def no_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(RequestValidationError)
async def safe_validation_error(_request: Request, _error: RequestValidationError):
    # Default FastAPI validation details can contain the submitted source.
    return JSONResponse(status_code=422, content={"detail": "Invalid review request"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/review", response_model=ReviewEnvelope)
def review(request: ReviewRequest) -> ReviewEnvelope:
    if not request.consent_external_transfer:
        raise HTTPException(status_code=400, detail="External transfer consent required")
    try:
        output = review_source(request.source)
    except ProviderError:
        raise HTTPException(status_code=503, detail="Review provider unavailable") from None
    except InvalidReview:
        raise HTTPException(status_code=422, detail="Unable to validate review result") from None
    return ReviewEnvelope(review_required=True, model_output=output)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    # Presentation only; user/provider data is inserted using textContent.
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>AI Security Code Reviewer</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #090f1d; color: #e8eefb; min-height: 100vh; }
    .page { max-width: 1330px; margin: 0 auto; padding: 36px 24px 64px; }
    .topbar { display:flex; gap:16px; justify-content:space-between; align-items:center; padding-bottom:26px; border-bottom:1px solid #26334e; }
    .brand { display:flex; align-items:center; gap:14px; }
    .mark { width:48px; height:48px; border-radius:14px; display:grid; place-items:center; background:#182b52; color:#91b5ff; font-size:26px; border:1px solid #304b80; }
    h1 { margin:0 0 5px; font-size:22px; letter-spacing:-.4px; }
    .subtitle { color:#9cadc7; margin:0; font-size:13px; }
    .pill { border:1px solid #40536d; border-radius:999px; padding:8px 12px; color:#c7d6ed; font-size:12px; white-space:nowrap; }
    .intro { margin:26px 0; display:flex; flex-wrap:wrap; justify-content:space-between; gap:14px; align-items:center; }
    .intro h2 { font-size:20px; margin:0 0 6px; }
    .intro p { color:#9cadc7; margin:0; max-width:730px; line-height:1.6; font-size:14px; }
    .offline { display:flex; align-items:center; gap:8px; color:#afc6e9; font-size:12px; }
    .dot { width:8px; height:8px; border-radius:50%; background:#6a9fff; }
    .columns { display:grid; grid-template-columns:minmax(0,1.1fr) minmax(0,1fr); gap:20px; align-items:start; }
    .panel { border:1px solid #293a57; background:#121d32; border-radius:16px; box-shadow:0 14px 38px rgba(0,0,0,.16); overflow:hidden; }
    .panel-head { display:flex; justify-content:space-between; gap:12px; align-items:center; padding:19px 20px; border-bottom:1px solid #293a57; }
    .panel-title { font-weight:700; font-size:15px; }
    .panel-note { font-size:12px; color:#9cadc7; }
    .panel-body { padding:20px; }
    .editor { display:block; width:100%; min-height:375px; resize:vertical; border:1px solid #304363; border-radius:12px; padding:18px; background:#0a1426; color:#dbe8ff; outline:none; font:13px/1.65 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace; tab-size:4; }
    .editor:focus { border-color:#6898ff; box-shadow:0 0 0 3px rgba(87,141,255,.13); }
    .editor::placeholder { color:#7186a8; }
    .editor-meta { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-top:10px; font-size:12px; color:#94a9c6; }
    .text-btn { background:none; border:0; cursor:pointer; color:#90b8ff; padding:0; font:inherit; text-decoration:underline; text-underline-offset:3px; }
    .notice { margin-top:19px; background:#19263e; border:1px solid #3a4e6f; border-radius:12px; padding:13px 14px; color:#c9d7ed; font-size:13px; line-height:1.55; }
    .consent { display:flex; gap:11px; align-items:flex-start; margin:20px 0 16px; font-size:13px; color:#e0e9fa; line-height:1.5; cursor:pointer; }
    .consent input { margin:3px 0 0; accent-color:#5d91ff; width:17px; height:17px; flex-shrink:0; }
    button.primary { padding:13px 20px; width:100%; background:#3579f6; color:white; border:1px solid #5990fd; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; transition:background .15s; }
    button.primary:hover:not(:disabled) { background:#4c8aff; }
    button.primary:disabled { cursor:not-allowed; opacity:.52; }
    .status { color:#acbfdc; font-size:13px; padding:12px 0 0; min-height:34px; }
    .status.error { color:#ffb9b9; }
    .empty { display:grid; justify-items:center; text-align:center; align-content:center; min-height:320px; gap:12px; padding:28px 18px; }
    .empty-icon { font-size:34px; background:#1c2c48; width:72px; height:72px; border-radius:18px; display:grid; place-items:center; color:#9abaff; }
    .empty strong { font-size:17px; }
    .empty p { margin:0; color:#99abc8; max-width:350px; line-height:1.7; font-size:13px; }
    .review-banner { background:#2c2516; border:1px solid #655332; border-radius:10px; padding:11px 13px; color:#f5d792; font-size:12px; margin-bottom:16px; }
    .summary { color:#d5e0f3; font-size:14px; line-height:1.6; white-space:pre-wrap; margin:0 0 18px; }
    .results-heading { display:flex; align-items:center; justify-content:space-between; margin:0 0 12px; font-size:14px; gap:8px; }
    .count { color:#9eafcb; font-size:12px; }
    .finding { background:#0c1729; border:1px solid #354663; border-radius:12px; padding:16px; margin:12px 0; overflow-wrap:anywhere; }
    .finding-top { display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; }
    .finding h3 { font-size:14px; margin:0; text-transform:capitalize; }
    .severity { font-size:11px; border:1px solid; border-radius:999px; padding:4px 9px; font-weight:700; }
    .severity-critical { color:#ffb0bb; background:#46212c; border-color:#854151; }
    .severity-high { color:#ffd0a6; background:#4a2a20; border-color:#80513d; }
    .severity-medium { color:#ffe0a0; background:#423717; border-color:#75622a; }
    .severity-low { color:#9ddae5; background:#153b47; border-color:#336575; }
    .lines { color:#97b4de; margin:8px 0 13px; font-size:12px; }
    .field-label { color:#9fb2d0; font-size:12px; font-weight:700; margin:13px 0 6px; }
    .detail { color:#d3e1f4; font-size:13px; line-height:1.6; white-space:pre-wrap; margin:0; }
    .evidence { padding:11px 12px; background:#070e1b; border:1px solid #273652; border-radius:8px; color:#bcd4ff; white-space:pre-wrap; overflow-wrap:anywhere; font:12px/1.6 ui-monospace,Consolas,monospace; }
    .success { padding:13px; border:1px solid #2e655b; border-radius:10px; background:#15352d; color:#a8e7cc; font-size:13px; line-height:1.6; }
    .footer { color:#798caa; margin-top:24px; font-size:12px; line-height:1.6; }
    [hidden] { display:none !important; }
    @media (max-width:880px) { .columns { grid-template-columns:1fr; } .editor { min-height:260px; } }
    @media (max-width:550px) { .page { padding:18px 13px 40px; } .panel-body {padding:14px;} .panel-head { padding:16px 14px; } .pill {white-space:normal; text-align:center;} .brand {align-items:flex-start;} h1 {font-size:19px;} }
    @media (prefers-reduced-motion:reduce) { button.primary {transition:none;} }
  </style>
</head>
<body>
<main class="page">
  <header class="topbar">
    <div class="brand">
      <div class="mark" aria-hidden="true">⛨</div>
      <div><h1>AI Security Code Reviewer</h1><p class="subtitle">Part-1B · Python source-code security analysis</p></div>
    </div>
    <div class="pill">Human review required</div>
  </header>
  <div class="intro">
    <div><h2>Review source code for security risks</h2><p>Analyze a Python snippet for potential vulnerabilities, source-line evidence and remediation guidance. Findings are advisory and must be checked by a human.</p></div>
    <div class="offline"><span class="dot" aria-hidden="true"></span>Groq-powered analysis</div>
  </div>
  <div class="columns">
    <section class="panel" aria-labelledby="source-title">
      <div class="panel-head"><span class="panel-title" id="source-title">Python source code</span><span class="panel-note">Maximum 25,000 characters</span></div>
      <div class="panel-body">
        <label for="source" class="panel-note" style="display:block;margin-bottom:10px">Paste code below or load a synthetic example.</label>
        <textarea class="editor" id="source" rows="16" spellcheck="false" aria-label="Python source" placeholder="def example(user_input):&#10;    # Paste Python code to review here&#10;    pass"></textarea>
        <div class="editor-meta"><button type="button" class="text-btn" id="demo">Load sample vulnerable code</button><span id="chars">0 / 25,000 characters</span></div>
        <div class="notice">🔒 Source is sent to Groq only after you consent and click Analyze. Do not submit passwords, private code, API keys or other secrets.</div>
        <label class="consent"><input type="checkbox" id="consent"><span>I consent to sending this source code to Groq for analysis.</span></label>
        <button type="button" class="primary" id="send" disabled>Analyze Code</button>
        <div class="status" id="status" role="status" aria-live="polite"></div>
      </div>
    </section>
    <section class="panel" aria-labelledby="findings-title">
      <div class="panel-head"><span class="panel-title" id="findings-title">Security findings</span><span class="panel-note">Evidence-based review</span></div>
      <div class="panel-body">
        <div id="empty" class="empty"><div class="empty-icon" aria-hidden="true">◇</div><strong>No review submitted yet</strong><p>Your structured findings, severity levels, affected lines and remediation guidance will appear here.</p></div>
        <div id="review" hidden>
          <div class="review-banner" id="human-warning">AI-generated findings require independent human verification before any action.</div>
          <p id="summary" class="summary"></p>
          <div class="results-heading"><strong>Findings</strong><span class="count" id="finding-count"></span></div>
          <div id="findings"></div>
        </div>
      </div>
    </section>
  </div>
  <p class="footer">Assignment 1 · Independent AI Security Review · No automatic acceptance or code execution. Submitted source is processed as text.</p>
</main>
<script>
'use strict';
const sourceInput = document.getElementById('source');
const consentInput = document.getElementById('consent');
const btn = document.getElementById('send');
const status = document.getElementById('status');
const results = document.getElementById('review');
const empty = document.getElementById('empty');
const findingsContainer = document.getElementById('findings');
const maxChars = 25000;
let busy = false;

const example = `import subprocess

def ping_host(host):
    return subprocess.run('ping ' + host, shell=True)
`;

function resetResults() {
  results.hidden = true;
  empty.hidden = false;
  findingsContainer.replaceChildren();
}
function updateControls() {
  const length = sourceInput.value.length;
  document.getElementById('chars').textContent = `${length.toLocaleString()} / ${maxChars.toLocaleString()} characters`;
  btn.disabled = busy || !consentInput.checked || !sourceInput.value.trim() || length > maxChars;
}
function addText(tag, className, value, parent) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  el.textContent = String(value ?? '');
  parent.appendChild(el);
  return el;
}
function renderReview(envelope) {
  if (!envelope || envelope.review_required !== true || !envelope.model_output || !Array.isArray(envelope.model_output.findings)) {
    throw new Error('Unexpected review format');
  }
  const data = envelope.model_output;
  findingsContainer.replaceChildren();
  document.getElementById('summary').textContent = data.analysis_summary;
  document.getElementById('finding-count').textContent = `${data.findings.length} reported`;
  document.getElementById('human-warning').textContent = 'Human review required — verify all AI-generated findings before acting.';
  if (data.findings.length === 0) {
    addText('div', 'success', 'No confirmed findings were returned for this snippet. This does not guarantee the code is secure.', findingsContainer);
  }
  for (const finding of data.findings) {
    const card = document.createElement('article');
    card.className = 'finding';
    const top = document.createElement('div');
    top.className = 'finding-top';
    const title = String(finding.category || 'Security finding').replace(/_/g, ' ');
    addText('h3', '', title, top);
    const severity = String(finding.severity || 'Unknown');
    const allowed = ['Critical', 'High', 'Medium', 'Low'];
    const severityClass = allowed.includes(severity) ? `severity-${severity.toLowerCase()}` : '';
    addText('span', `severity ${severityClass}`, severity, top);
    card.appendChild(top);
    addText('p', 'lines', `Affected lines: ${finding.start_line}–${finding.end_line}`, card);
    addText('p', 'field-label', 'Source evidence', card);
    addText('pre', 'evidence', finding.evidence, card);
    addText('p', 'field-label', 'Explanation', card);
    addText('p', 'detail', finding.explanation, card);
    addText('p', 'field-label', 'Suggested remediation', card);
    addText('p', 'detail', finding.remediation, card);
    findingsContainer.appendChild(card);
  }
  empty.hidden = true;
  results.hidden = false;
}
sourceInput.addEventListener('input', () => {resetResults(); updateControls();});
consentInput.addEventListener('change', updateControls);
document.getElementById('demo').addEventListener('click', () => {
  sourceInput.value = example;
  consentInput.checked = false;
  status.textContent = 'Synthetic example loaded. Consent is still required.';
  status.classList.remove('error');
  resetResults();
  updateControls();
});
btn.addEventListener('click', async () => {
  if (busy || !consentInput.checked || !sourceInput.value.trim() || sourceInput.value.length > maxChars) return;
  const source = sourceInput.value;
  const consent_external_transfer = consentInput.checked;
  busy = true; updateControls(); resetResults();
  status.classList.remove('error');
  status.textContent = 'Analyzing source code…';
  try {
    const response = await fetch('/api/review', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store'},
      cache: 'no-store',
      body: JSON.stringify({source, consent_external_transfer})
    });
    if (!response.ok) {
      status.textContent = 'Review unavailable or request invalid. Check consent, code length and provider configuration.';
      status.classList.add('error');
      return;
    }
    const envelope = await response.json();
    if (sourceInput.value !== source) {
      status.textContent = 'Source changed during review. Please analyze the updated code again.';
      return;
    }
    renderReview(envelope);
    status.textContent = 'Review completed. Human verification required.';
  } catch (_) {
    status.textContent = 'Review unavailable. Please try again.';
    status.classList.add('error');
  } finally {
    busy = false;
    updateControls();
  }
});
updateControls();
</script>
</body>
</html>
"""
