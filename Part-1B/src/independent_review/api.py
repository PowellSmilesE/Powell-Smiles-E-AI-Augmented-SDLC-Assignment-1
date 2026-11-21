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
    # Self-contained UI: no localStorage, cookies or analytics dependencies.
    return """<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Independent Code Review</title></head><body>
<h1>AI security code review</h1><p>Source is sent to Groq. Do not submit private code or real secrets.</p>
<textarea id='source' rows='16' cols='85' aria-label='Python source'></textarea>
<p><label><input type='checkbox' id='consent'>I consent to sending the code to Groq</label></p>
<button id='send'>Analyze</button><pre id='result' aria-live='polite'></pre>
<script>
const btn=document.getElementById('send');
btn.addEventListener('click',async()=>{
 const source=document.getElementById('source').value;
 const consent_external_transfer=document.getElementById('consent').checked;
 const output=document.getElementById('result');output.textContent='Reviewing...';
 try {const response=await fetch('/api/review',{method:'POST',
 headers:{'Content-Type':'application/json','Cache-Control':'no-store'},
 body:JSON.stringify({source,consent_external_transfer})});
 const result=await response.json();output.textContent=JSON.stringify(result,null,2);
 }catch(_){output.textContent='Review unavailable';}
});</script></body></html>"""
