import pytest

from app.ats_platforms import ATS_PLATFORMS, resolve_ats_platforms
from app.career_pages import aggregator_exclude_clause, sanitize_company_domain
from app.dork_engine import SearchParams, generate_dorks


def _company_dorks(params: SearchParams) -> list[dict]:
    result = generate_dorks(params)
    return next(c["dorks"] for c in result["categories"] if c["id"] == "company")


def test_all_ats_platforms_resolve():
    ids = [p.id for p in ATS_PLATFORMS]
    assert len(ids) == len(set(ids)), "ATS ids must be unique"
    resolved = resolve_ats_platforms(None)
    assert len(resolved) >= 17
    new_ids = {
        "workable",
        "eightfold",
        "teamtailor",
        "recruitee",
        "pinpoint",
        "breezyhr",
        "jazzhr",
        "taleo",
        "ultipro",
    }
    assert new_ids <= set(ids)


def test_career_pages_dork_excludes_job_boards():
    dorks = _company_dorks(SearchParams(title="Software Engineer"))
    careers = next(d for d in dorks if d["platform_id"] == "careers_pages")
    query = careers["query"]
    assert "inurl:careers" in query
    assert "-site:linkedin.com" in query
    assert "-site:indeed.com" in query
    assert aggregator_exclude_clause().split()  # clause is non-empty


def test_hiring_announcements_dork_present():
    dorks = _company_dorks(SearchParams(title="Software Engineer"))
    hiring = next(d for d in dorks if d["platform_id"] == "hiring_announcements")
    assert "we're hiring" in hiring["query"]
    assert "-site:glassdoor.com" in hiring["query"]


def test_company_name_gets_own_site_and_ats_lookup_dorks():
    dorks = _company_dorks(SearchParams(title="Software Engineer", company="Stripe"))
    own_site = next(d for d in dorks if d["platform_id"] == "company_site")
    assert '"Stripe"' in own_site["query"]
    assert "inurl:careers" in own_site["query"]
    assert "-site:linkedin.com" in own_site["query"]
    ats_lookup = next(d for d in dorks if d["platform_id"] == "company_ats")
    assert "site:jobs.lever.co" in ats_lookup["query"]
    assert "site:boards.greenhouse.io" in ats_lookup["query"]
    assert '"Stripe"' in ats_lookup["query"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("stripe.com", "stripe.com"),
        ("https://www.instadeep.com/careers", "instadeep.com"),
        ("  WWW.PhotoRoom.COM/jobs  ", "photoroom.com"),
        ("http://sub.domain.co.uk/path?q=1", "sub.domain.co.uk"),
        ("not a domain", ""),
        ("", ""),
        ("justtext", ""),
        ("user@jobscout.io", "jobscout.io"),
    ],
)
def test_sanitize_company_domain(raw, expected):
    assert sanitize_company_domain(raw) == expected


def test_company_domains_generate_targeted_dorks():
    params = SearchParams(
        title="Backend Developer",
        company_domains=[
            "https://www.instadeep.com/careers",
            "photoroom.com",
            "bad domain",
        ],
    )
    assert params.company_domains == ["instadeep.com", "photoroom.com"]
    dorks = _company_dorks(params)
    labels = {d["platform_id"]: d["query"] for d in dorks}
    assert "site:instadeep.com" in labels["domain_instadeep_com"]
    assert "site:photoroom.com" in labels["domain_photoroom_com"]
    combined = labels["domain_all"]
    assert "(site:instadeep.com OR site:photoroom.com)" in combined


def test_single_company_domain_has_no_combined_dork():
    dorks = _company_dorks(SearchParams(title="Dev", company_domains=["stripe.com"]))
    assert not any(d["platform_id"] == "domain_all" for d in dorks)


def test_company_domains_echoed_in_params():
    result = generate_dorks(
        SearchParams(title="Dev", company_domains=["https://a.io/x", "b.com"])
    )
    assert result["params"]["company_domains"] == ["a.io", "b.com"]


def test_career_queries_stay_within_length_limit():
    params = SearchParams(
        titles=[
            "Software Engineer",
            "Backend Developer",
            "Full Stack Developer",
            "DevOps Engineer",
            "Platform Engineer",
            "Cloud Engineer",
        ],
        location="Tunis",
        skills=["Python", "Docker", "AWS", "PostgreSQL"],
        company="Instadeep",
        company_domains=["instadeep.com", "photoroom.com"],
        time_filter="7d",
    )
    result = generate_dorks(params)
    for category in result["categories"]:
        for dork in category["dorks"]:
            assert len(dork["query"]) <= 1800, f"{dork['label']} too long"
