from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from app.ats_platforms import list_ats_platforms
from app.cv_parser import MAX_CV_BYTES, parse_cv_file
from app.domain_presets import list_domain_presets
from app.dork_engine import SearchParams, generate_dorks
from app.time_filters import list_time_filters

MAX_BODY_BYTES = MAX_CV_BYTES + 1024 * 1024

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
        default="", max_length=200, description="Single job title (legacy)"
    )
    titles: list[str] = Field(
        default_factory=list, max_length=6, description="One or more job titles"
    )
    location: str = Field(
        default="", max_length=100, description="City, state, or country"
    )
    skills: list[str] = Field(default_factory=list, max_length=12)
    remote: bool = Field(default=False, description="Prefer remote-focused dorks")
    experience: str = Field(default="", max_length=30)
    exclude_terms: list[str] = Field(default_factory=list, max_length=15)
    company: str = Field(
        default="", max_length=100, description="Target a specific company"
    )
    company_domains: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Company career-site domains, e.g. ['stripe.com', 'plaid.com']",
    )
    ats_platforms: list[str] | None = Field(
        default=None,
        max_length=20,
        description="ATS platform ids to include; omit for all, empty list for none",
    )
    keyword_mode: str = Field(default="and", max_length=10)
    title_mode: str = Field(default="or", max_length=10)
    time_filter: str = Field(
        default="", max_length=10, description="24h, 7d, 30d, 90d, 180d"
    )
    preset_id: str = Field(default="", max_length=40)

    @model_validator(mode="after")
    def require_title(self) -> "DorkRequest":
        if not self.title and not self.titles:
            raise ValueError("At least one job title is required")
        return self


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


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
async def parse_cv(cv: UploadFile = File(..., description="PDF, DOCX, or TXT resume")):
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
