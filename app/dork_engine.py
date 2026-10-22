from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote_plus

from app.ats_platforms import resolve_ats_platforms
from app.career_pages import (
    ATS_BOARD_SITES,
    CAREER_PATH_FILTER,
    HIRING_PHRASES,
    aggregator_exclude_clause,
    sanitize_company_domain,
)
from app.experience_filters import (
    experience_clause,
    experience_exclude_tokens,
    zero_experience_exclude_tokens,
    ZERO_EXP_POSITIVE,
)
from app.domain_presets import get_domain_preset
from app.query_builder import (
    assemble_query,
    combine_terms,
    google_quoted,
    intitle_clause,
    join_query_parts,
    normalize_exclude_list,
    query_length_warning,
    sanitize_term,
)
from app.time_filters import time_filter_clause

TUNISIA_LOCATION_HINTS = (
    "tunisia",
    "tunis",
    "sfax",
    "sousse",
    "bizerte",
    "nabeul",
    "gabes",
    "gabès",
    "ariana",
    "monastir",
    "kairouan",
)


@dataclass
class DorkQuery:
    category: str
    label: str
    query: str
    description: str
    platform_id: str = ""
    truncated: bool = False
    query_warning: str | None = None

    @property
    def google_url(self) -> str:
        return f"https://www.google.com/search?q={quote_plus(self.query)}"


@dataclass
class SearchParams:
    title: str = ""
    titles: list[str] | None = None
    location: str = ""
    skills: list[str] | None = None
    remote: bool = False
    experience: str = ""  # entry, mid, senior, lead, no_experience
    exclude_terms: list[str] | None = None
    company: str = ""
    company_domains: list[str] | None = None
    ats_platforms: list[str] | None = None
    keyword_mode: str = "and"  # and | or (skills)
    title_mode: str = "or"  # and | or (multiple job titles)
    time_filter: str = ""  # 24h, 7d, 30d, 90d, 180d
    preset_id: str = ""

    def __post_init__(self) -> None:
        raw_titles = list(self.titles or [])
        if self.title:
            raw_titles.insert(0, self.title)
        seen: set[str] = set()
        cleaned: list[str] = []
        for t in raw_titles:
            s = sanitize_term(t)
            key = s.lower()
            if s and key not in seen:
                seen.add(key)
                cleaned.append(s)
        self.titles = cleaned[:6]
        self.title = self.titles[0] if self.titles else ""

        self.location = sanitize_term(self.location)
        self.company = sanitize_term(self.company)
        cleaned_domains: list[str] = []
        seen_domains: set[str] = set()
        for raw in self.company_domains or []:
            domain = sanitize_company_domain(raw)
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                cleaned_domains.append(domain)
        self.company_domains = cleaned_domains[:5]
        self.experience = sanitize_term(self.experience)
        self.skills = [
            sanitize_term(s) for s in (self.skills or []) if sanitize_term(s)
        ]
        self.exclude_terms = [
            sanitize_term(t) for t in (self.exclude_terms or []) if sanitize_term(t)
        ]
        self.preset_id = sanitize_term(self.preset_id)
        if self.keyword_mode not in ("and", "or"):
            self.keyword_mode = "and"
        if self.title_mode not in ("and", "or"):
            self.title_mode = "or"
        self._apply_preset_defaults()

    def _apply_preset_defaults(self) -> None:
        if not self.preset_id:
            return
        try:
            preset = get_domain_preset(self.preset_id)
        except ValueError:
            return
        if not self.titles:
            self.titles = [sanitize_term(t) for t in preset.titles if sanitize_term(t)][
                :6
            ]
            self.title = self.titles[0] if self.titles else ""
        if not self.skills:
            self.skills = [sanitize_term(s) for s in preset.skills if sanitize_term(s)]
        if not self.exclude_terms:
            self.exclude_terms = [
                sanitize_term(t) for t in preset.exclude_terms if sanitize_term(t)
            ]

    def positive_text(self) -> str:
        return " ".join([*self.titles, self.company, *(self.skills or [])])


def _finalize_query(core: str, protected: str) -> tuple[str, bool, str | None]:
    assembled = assemble_query(core, protected)
    warning = query_length_warning(len(assembled.query))
    if assembled.truncated:
        trunc_msg = "Query was trimmed to stay within Google's practical length limit."
        warning = f"{warning} {trunc_msg}".strip() if warning else trunc_msg
    return assembled.query, assembled.truncated, warning


def _title_only_clause(params: SearchParams) -> str:
    if not params.titles:
        return ""
    if len(params.titles) > 1:
        return combine_terms(params.titles, params.title_mode)
    return google_quoted(params.titles[0])


def _title_clause(params: SearchParams) -> str:
    parts = [_title_only_clause(params)]
    exp = experience_clause(params.experience)
    if exp:
        parts.append(exp)
    return join_query_parts(parts)


def _location_clause(params: SearchParams) -> str:
    if params.remote:
        return '("remote" OR "work from home" OR "WFH")'
    if params.location:
        return google_quoted(params.location)
    return ""


def _skills_clause(params: SearchParams) -> str:
    if not params.skills:
        return ""
    return combine_terms(params.skills[:4], params.keyword_mode)


def _user_exclude_terms(params: SearchParams) -> list[str]:
    return normalize_exclude_list(
        params.exclude_terms or [],
        title=params.positive_text(),
        skills=params.skills or [],
        company=params.company,
    )


def _exclude_clause(params: SearchParams) -> str:
    terms = _user_exclude_terms(params)
    seen = {t.lower() for t in terms}
    for token in experience_exclude_tokens(params.experience):
        key = token.lower()
        if key not in seen:
            seen.add(key)
            terms.append(token)
    return join_query_parts(terms)


def _include_tunisia_boards(params: SearchParams) -> bool:
    if params.preset_id == "tunisia":
        return True
    if not params.location:
        return False
    loc = params.location.lower()
    return any(hint in loc for hint in TUNISIA_LOCATION_HINTS)


def _core_terms(params: SearchParams) -> str:
    parts = [_title_clause(params)]
    loc = _location_clause(params)
    if loc:
        parts.append(loc)
    skills = _skills_clause(params)
    if skills:
        parts.append(skills)
    if params.company:
        parts.append(google_quoted(params.company))
    time_part = _time_clause(params)
    if time_part:
        parts.append(time_part)
    return join_query_parts(parts)


def _protected_suffix(params: SearchParams, site_filter: str = "") -> str:
    parts = [_exclude_clause(params)]
    if site_filter:
        parts.append(site_filter)
    return join_query_parts(parts)


def _time_clause(params: SearchParams) -> str:
    return time_filter_clause(params.time_filter)


def _make_dork(
    category: str,
    label: str,
    params: SearchParams,
    site_filter: str,
    description: str,
    *,
    platform_id: str = "",
) -> DorkQuery:
    core = _core_terms(params)
    protected = _protected_suffix(params, site_filter)
    query, truncated, warning = _finalize_query(core, protected)
    return DorkQuery(
        category=category,
        label=label,
        query=query,
        description=description,
        platform_id=platform_id,
        truncated=truncated,
        query_warning=warning,
    )


def _make_dork_parts(
    category: str,
    label: str,
    core: str,
    protected: str,
    description: str,
    *,
    platform_id: str = "",
) -> DorkQuery:
    query, truncated, warning = _finalize_query(core, protected)
    return DorkQuery(
        category=category,
        label=label,
        query=query,
        description=description,
        platform_id=platform_id,
        truncated=truncated,
        query_warning=warning,
    )


def _job_board_dorks(params: SearchParams) -> list[DorkQuery]:
    boards = [
        (
            "LinkedIn Jobs",
            "site:linkedin.com/jobs/view",
            "Direct LinkedIn job postings",
            "linkedin",
        ),
        (
            "Indeed",
            "site:indeed.com/viewjob OR site:indeed.com/jobs",
            "Indeed listings",
            "indeed",
        ),
        (
            "Glassdoor",
            "site:glassdoor.com/job-listing OR site:glassdoor.com/Job",
            "Glassdoor postings",
            "glassdoor",
        ),
        (
            "ZipRecruiter",
            "site:ziprecruiter.com/jobs",
            "ZipRecruiter listings",
            "ziprecruiter",
        ),
        ("Monster", "site:monster.com/jobs", "Monster job board", "monster"),
        ("Dice (Tech)", "site:dice.com/job-detail", "Tech-focused Dice board", "dice"),
    ]
    return [
        _make_dork("job_boards", name, params, site, desc, platform_id=pid)
        for name, site, desc, pid in boards
    ]


def _tunisia_job_board_dorks(params: SearchParams) -> list[DorkQuery]:
    boards = [
        ("TanitJobs", "site:tanitjobs.com", "Leading Tunisian job board", "tanitjobs"),
        (
            "Option Carrière TN",
            "site:optioncarriere.tn",
            "Option Carrière Tunisia",
            "optioncarriere_tn",
        ),
        ("Keejob", "site:keejob.com", "Keejob (Tunisia & MENA)", "keejob"),
        (
            "Indeed Tunisia",
            "site:tn.indeed.com/viewjob OR site:tn.indeed.com/jobs",
            "Indeed Tunisia job pages",
            "indeed_tn",
        ),
        (
            "Tunisie Annonce",
            'site:tunisieannonce.com (emploi OR emplois OR "offre d\'emploi")',
            "Classified job ads on Tunisie Annonce",
            "tunisieannonce",
        ),
    ]
    return [
        _make_dork("tunisia", name, params, site, desc, platform_id=pid)
        for name, site, desc, pid in boards
    ]


def _ats_dorks(params: SearchParams) -> list[DorkQuery]:
    if params.ats_platforms is not None and not params.ats_platforms:
        return []
    platforms = resolve_ats_platforms(params.ats_platforms)
    return [
        _make_dork(
            "ats", p.name, params, p.site_filter, p.description, platform_id=p.id
        )
        for p in platforms
    ]


def _remote_dorks(params: SearchParams) -> list[DorkQuery]:
    remote_params = SearchParams(
        titles=params.titles,
        location=params.location,
        skills=params.skills,
        remote=True,
        experience=params.experience,
        exclude_terms=params.exclude_terms,
        company=params.company,
        ats_platforms=params.ats_platforms,
        keyword_mode=params.keyword_mode,
        title_mode=params.title_mode,
        time_filter=params.time_filter,
        preset_id=params.preset_id,
    )
    boards = [
        (
            "We Work Remotely",
            "site:weworkremotely.com",
            "Curated remote jobs",
            "weworkremotely",
        ),
        ("Remote OK", "site:remoteok.com", "Remote OK listings", "remoteok"),
        ("Remotive", "site:remotive.com/remote-jobs", "Remotive board", "remotive"),
        ("FlexJobs", "site:flexjobs.com/job", "FlexJobs (remote/hybrid)", "flexjobs"),
        ("Remote.co", "site:remote.co/remote-jobs", "Remote.co listings", "remote_co"),
        (
            "Working Nomads",
            "site:workingnomads.com/jobs",
            "Working Nomads",
            "workingnomads",
        ),
    ]
    return [
        _make_dork("remote", name, remote_params, site, desc, platform_id=pid)
        for name, site, desc, pid in boards
    ]


def _company_direct_dorks(params: SearchParams) -> list[DorkQuery]:
    board_excludes = aggregator_exclude_clause()
    dorks: list[DorkQuery] = []

    if params.company_domains:
        for domain in params.company_domains:
            dorks.append(
                _make_dork(
                    "company",
                    f"{domain} careers",
                    params,
                    f"site:{domain} (inurl:careers OR inurl:jobs OR inurl:job)",
                    f"Job listings on {domain} only",
                    platform_id=f"domain_{domain.replace('.', '_')}",
                )
            )
        if len(params.company_domains) > 1:
            site_group = (
                "(" + " OR ".join(f"site:{d}" for d in params.company_domains) + ")"
            )
            dorks.append(
                _make_dork(
                    "company",
                    "All target company sites",
                    params,
                    site_group,
                    "One query across every company domain you listed",
                    platform_id="domain_all",
                )
            )

    if params.company:
        dorks.append(
            _make_dork(
                "company",
                f"{params.company} on its own site",
                params,
                join_query_parts([CAREER_PATH_FILTER, board_excludes]),
                f"{params.company} postings on its own site, with job boards excluded",
                platform_id="company_site",
            )
        )
        ats_sites = " OR ".join(ATS_BOARD_SITES)
        dorks.append(
            _make_dork(
                "company",
                f"{params.company} on its ATS board",
                params,
                f"({ats_sites})",
                f"Find {params.company}'s hosted ATS board, where jobs land first",
                platform_id="company_ats",
            )
        )

    dorks.extend(
        [
            _make_dork(
                "company",
                "Career pages only (no job boards)",
                params,
                join_query_parts([CAREER_PATH_FILTER, '"apply"', board_excludes]),
                "Employer career-site postings with aggregator boards subtracted",
                platform_id="careers_pages",
            ),
            _make_dork(
                "company",
                "Hiring announcements",
                params,
                join_query_parts([HIRING_PHRASES, board_excludes]),
                '"We\'re hiring" pages on company sites, not boards',
                platform_id="hiring_announcements",
            ),
            _make_dork(
                "company",
                "Job Postings (PDF)",
                params,
                "filetype:pdf (intitle:job OR intitle:position OR intitle:opening)",
                "Job descriptions shared as PDFs",
                platform_id="pdf_jobs",
            ),
            _make_dork(
                "company",
                "Startup Jobs",
                params,
                "site:wellfound.com/jobs OR site:angel.co/jobs",
                "Wellfound / AngelList startups",
                platform_id="wellfound",
            ),
        ]
    )
    return dorks


def _tech_dorks(params: SearchParams) -> list[DorkQuery]:
    sources = [
        (
            "Authentic Jobs",
            "site:authenticjobs.com",
            "Authentic Jobs tech/creative board",
            "authenticjobs",
        ),
        (
            "GitHub Hiring Posts",
            'site:github.com ("we are hiring" OR "we\'re hiring" OR "now hiring")',
            "GitHub repos with explicit hiring posts",
            "github",
        ),
        (
            "Hacker News Who's Hiring",
            'site:news.ycombinator.com "Who is hiring"',
            "HN monthly hiring threads",
            "hn",
        ),
        (
            "Arc.dev",
            "site:arc.dev/remote-jobs OR site:arc.dev/jobs",
            "Arc.dev developer job listings",
            "arcdev",
        ),
    ]
    return [
        _make_dork("tech", name, params, site, desc, platform_id=pid)
        for name, site, desc, pid in sources
    ]


def _advanced_dorks(params: SearchParams) -> list[DorkQuery]:
    title = _title_clause(params)
    title_only = _title_only_clause(params)
    intitle = intitle_clause(params.titles, params.title_mode)
    loc = _location_clause(params)
    time_part = _time_clause(params)
    exclude = _exclude_clause(params)
    tail_core = join_query_parts([loc, time_part])
    tail = join_query_parts([tail_core, exclude])
    user_excludes = _user_exclude_terms(params)
    zero_exp_protected = join_query_parts(
        [
            join_query_parts(user_excludes),
            join_query_parts(zero_experience_exclude_tokens()),
        ]
    )

    specs = [
        (
            "Zero Experience (0 yrs)",
            join_query_parts([title_only, ZERO_EXP_POSITIVE, tail_core]),
            zero_exp_protected,
            "Roles that explicitly require no prior experience; excludes common year minimums",
            "zero_experience",
        ),
        (
            "Exact Title Match",
            join_query_parts([intitle, "(apply OR hiring OR opening)", tail_core]),
            exclude,
            "Pages with your title in the page title",
            "exact_title",
        ),
        (
            "Recent Listings",
            join_query_parts(
                [title, '("posted" OR "posted on" OR "date posted")', tail_core]
            ),
            exclude,
            "Pages mentioning posting dates",
            "recent",
        ),
        (
            "Salary Mentioned",
            join_query_parts(
                [title, '(salary OR compensation OR "pay range")', tail_core]
            ),
            exclude,
            "Listings that mention compensation",
            "salary",
        ),
        (
            "No Recruiter Spam",
            join_query_parts([title, tail_core]),
            join_query_parts([exclude, "-recruiter -staffing -agency"]),
            "Exclude recruiter/staffing agency posts",
            "no_recruiter",
        ),
    ]

    dorks = [
        _make_dork_parts("advanced", name, core, protected, desc, platform_id=pid)
        for name, core, protected, desc, pid in specs
    ]

    if params.skills:
        skill = google_quoted(params.skills[0])
        dorks.append(
            _make_dork_parts(
                "advanced",
                f"Skill + Title ({params.skills[0]})",
                join_query_parts(
                    [title, skill, '(hiring OR "we are looking")', tail_core]
                ),
                exclude,
                "Combine primary skill with job title",
                platform_id="skill_title",
            )
        )

    return dorks


def _domain_niche_dorks(params: SearchParams) -> list[DorkQuery]:
    if not params.preset_id:
        return []
    preset = get_domain_preset(params.preset_id)
    return [
        _make_dork(
            "domain",
            board.name,
            params,
            board.site_filter,
            board.description,
            platform_id=f"{params.preset_id}_{board.name.lower().replace(' ', '_')}",
        )
        for board in preset.niche_boards
    ]


CATEGORY_META = {
    "job_boards": {"label": "Job Boards", "icon": "📋"},
    "tunisia": {"label": "Tunisia Job Boards", "icon": "🇹🇳"},
    "ats": {"label": "ATS Platforms", "icon": "🏢"},
    "remote": {"label": "Remote Boards", "icon": "🌍"},
    "company": {"label": "Company Direct", "icon": "🎯"},
    "tech": {"label": "Tech & Dev", "icon": "💻"},
    "domain": {"label": "Domain Niche", "icon": "🧩"},
    "advanced": {"label": "Advanced", "icon": "🔍"},
}


def generate_dorks(params: SearchParams) -> dict:
    if not params.titles:
        raise ValueError("At least one job title is required")

    all_dorks = (
        _job_board_dorks(params)
        + (_tunisia_job_board_dorks(params) if _include_tunisia_boards(params) else [])
        + _ats_dorks(params)
        + _remote_dorks(params)
        + _company_direct_dorks(params)
        + _tech_dorks(params)
        + _domain_niche_dorks(params)
        + _advanced_dorks(params)
    )
    warnings = [d.query_warning for d in all_dorks if d.query_warning]
    warnings = list(dict.fromkeys(warnings))

    grouped: dict[str, list[dict]] = {}
    for dork in all_dorks:
        grouped.setdefault(dork.category, []).append(
            {
                "label": dork.label,
                "query": dork.query,
                "description": dork.description,
                "google_url": dork.google_url,
                "platform_id": dork.platform_id,
                "truncated": dork.truncated,
                "query_warning": dork.query_warning,
            }
        )

    categories = [
        {
            "id": cat_id,
            "label": CATEGORY_META[cat_id]["label"],
            "icon": CATEGORY_META[cat_id]["icon"],
            "dorks": grouped.get(cat_id, []),
        }
        for cat_id in CATEGORY_META
        if cat_id in grouped
    ]

    return {
        "params": {
            "title": params.title,
            "titles": params.titles,
            "location": params.location,
            "skills": params.skills,
            "remote": params.remote,
            "experience": params.experience,
            "company": params.company,
            "company_domains": params.company_domains,
            "ats_platforms": params.ats_platforms,
            "keyword_mode": params.keyword_mode,
            "title_mode": params.title_mode,
            "time_filter": params.time_filter,
            "preset_id": params.preset_id,
            "exclude_terms": params.exclude_terms,
        },
        "total": len(all_dorks),
        "warnings": warnings,
        "categories": categories,
    }
