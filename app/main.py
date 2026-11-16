import json
from collections import defaultdict, deque
from pathlib import Path
from time import monotonic

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.ats_platforms import list_ats_platforms
from app.cv_parser import MAX_CV_BYTES, parse_cv_file
from app.domain_presets import list_domain_presets
from app.dork_engine import SearchParams, generate_dorks
from app.time_filters import list_time_filters

MAX_BODY_BYTES = MAX_CV_BYTES + 1024 * 1024
CV_RATE_LIMIT = 20
CV_RATE_WINDOW_SECONDS = 60.0
_cv_requests: dict[str, deque[float]] = defaultdict(deque)


def _cv_rate_limited(client_key: str) -> bool:
    now = monotonic()
    hits = _cv_requests[client_key]
    while hits and now - hits[0] >= CV_RATE_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= CV_RATE_LIMIT:
        return True
    hits.append(now)
    return False

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'self'"
    ),
}

app = FastAPI(
    title="JobScout Dorks",
    description="Google dork engine for job searching",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def guard_request(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


class DorkRequest(BaseModel):
    title: str = Field(
        default="", max_length=500, description="Single job title (legacy)"
    )
    titles: list[str] = Field(
        default_factory=list, max_length=100, description="One or more job titles"
    )
    location: str = Field(
        default="", max_length=500, description="City, state, or country"
    )
    skills: list[str] = Field(default_factory=list, max_length=100)
    remote: bool = Field(default=False, description="Prefer remote-focused dorks")
    experience: str = Field(default="", max_length=100)
    exclude_terms: list[str] = Field(default_factory=list, max_length=100)
    company: str = Field(
        default="", max_length=500, description="Target a specific company"
    )
    company_domains: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Company career-site domains, e.g. ['stripe.com', 'plaid.com']",
    )
    ats_platforms: list[str] | None = Field(
        default=None,
        max_length=100,
        description="ATS platform ids to include; omit for all, empty list for none",
    )
    keyword_mode: str = Field(default="and", max_length=30)
    title_mode: str = Field(default="or", max_length=30)
    time_filter: str = Field(
        default="", max_length=30, description="24h, 7d, 30d, 90d, 180d"
    )
    preset_id: str = Field(default="", max_length=100)


@app.get("/")
async def index() -> HTMLResponse:
    # Presets ship with the page so the grid paints in its final position.
    template = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    presets = json.dumps(list_domain_presets(), separators=(",", ":")).replace(
        "</", "<\\/"
    )
    bootstrap = (
        '<script type="application/json" id="preset-bootstrap">'
        f"{presets}</script>"
    )
    html = template.replace("<!--PRESET_BOOTSTRAP-->", bootstrap)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/privacy")
async def privacy() -> FileResponse:
    return FileResponse(STATIC_DIR / "privacy.html")


@app.get("/api/ats-platforms")
async def get_ats_platforms():
    return {"platforms": list_ats_platforms()}


@app.get("/api/presets")
async def get_presets():
    return {"presets": list_domain_presets()}


@app.get("/api/time-filters")
async def get_time_filters():
    return {"filters": list_time_filters()}


@app.post("/api/cv/parse")
async def parse_cv(
    request: Request,
    cv: UploadFile = File(..., description="PDF, DOCX, or TXT resume"),
):
    client_key = request.client.host if request.client else "unknown"
    if _cv_rate_limited(client_key):
        raise HTTPException(
            status_code=429,
            detail="Too many CV uploads. Try again in a minute.",
        )
    if not cv.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await cv.read(MAX_CV_BYTES + 1)
    if len(content) > MAX_CV_BYTES:
        raise HTTPException(status_code=413, detail="CV file is too large (max 5 MB)")
    try:
        result = parse_cv_file(cv.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()


@app.post("/api/dorks")
async def create_dorks(body: DorkRequest):
    try:
        params = SearchParams(
            title=body.title,
            titles=body.titles,
            location=body.location,
            skills=body.skills,
            remote=body.remote,
            experience=body.experience,
            exclude_terms=body.exclude_terms,
            company=body.company,
            company_domains=body.company_domains,
            ats_platforms=body.ats_platforms,
            keyword_mode=body.keyword_mode,
            title_mode=body.title_mode,
            time_filter=body.time_filter,
            preset_id=body.preset_id,
        )
        return generate_dorks(params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/health")
async def health():
    return {"status": "ok"}
