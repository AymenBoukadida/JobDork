import pytest


from app.cv_parser import parse_cv_text

from app.dork_engine import SearchParams, generate_dorks


def test_requires_title():
    with pytest.raises(ValueError, match="job title"):
        generate_dorks(SearchParams(title="", titles=[]))


def test_generates_dorks_with_title_only():

    result = generate_dorks(SearchParams(title="Software Engineer"))
    assert result["total"] > 20
    assert result["params"]["title"] == "Software Engineer"
    ids = {c["id"] for c in result["categories"]}
    assert "job_boards" in ids
    assert "ats" in ids


def test_location_and_skills_in_queries():

    result = generate_dorks(
        SearchParams(title="Data Analyst", location="Berlin", skills=["SQL", "Python"])
    )
    sample = result["categories"][0]["dorks"][0]["query"]
    assert "Data Analyst" in sample
    assert "Berlin" in sample


def test_google_url_encoded():

    result = generate_dorks(SearchParams(title="C++ Developer"))
    url = result["categories"][0]["dorks"][0]["google_url"]
    assert url.startswith("https://www.google.com/search?q=")


def test_ats_platform_filter_subset():

    result = generate_dorks(
        SearchParams(title="Engineer", ats_platforms=["greenhouse", "lever"])
    )
    ats = next(c for c in result["categories"] if c["id"] == "ats")
    labels = {d["label"] for d in ats["dorks"]}
    assert labels == {"Greenhouse", "Lever"}


def test_ats_platform_filter_none():

    result = generate_dorks(SearchParams(title="Engineer", ats_platforms=[]))
    ids = {c["id"] for c in result["categories"]}
    assert "ats" not in ids


def test_unknown_ats_platform():

    with pytest.raises(ValueError, match="Unknown ATS"):
        generate_dorks(SearchParams(title="Engineer", ats_platforms=["not-a-platform"]))


SAMPLE_CV = """

Jane Doe

Software Engineer

London, UK

jane@example.com



SUMMARY

Senior software engineer with 6 years of experience building APIs.



SKILLS

Python, FastAPI, PostgreSQL, AWS, Docker, React



EXPERIENCE

Senior Software Engineer | Acme Corp

"""


def test_parse_cv_extracts_fields():

    result = parse_cv_text(SAMPLE_CV)
    assert "Software Engineer" in result.title or result.title == "Software Engineer"
    assert any(s.lower() == "python" for s in result.skills)
    assert result.experience in ("senior", "mid level", "")
    assert "London" in result.location or result.location == "London, UK"


def test_parse_cv_does_not_use_name_as_title():
    cv = (
        "AYMEN BOUKADIDA\n"
        "Tunis, Tunisia\n"
        "aymen.boukadida@example.com\n"
        "+216 20 123 456\n"
        "Driven person with strong motivation.\n"
    )
    result = parse_cv_text(cv)
    assert result.title == ""


def test_parse_cv_uses_headline_after_name():
    cv = (
        "AYMEN BOUKADIDA\n"
        "Digital Marketing Specialist\n"
        "Tunis, Tunisia\n"
        "aymen.boukadida@example.com\n"
    )
    result = parse_cv_text(cv)
    assert result.title == "Digital Marketing Specialist"


def test_parse_cv_skips_section_headers_in_fallback():
    cv = "Jane Smith\n\nSUMMARY\n\nMotivated self-starter.\n\nSKILLS\n\nExcel, Word\n"
    result = parse_cv_text(cv)
    assert result.title == ""


def test_keyword_mode_or_in_skills():
    result = generate_dorks(
        SearchParams(title="Engineer", skills=["Python", "Go"], keyword_mode="or")
    )
    sample = result["categories"][0]["dorks"][0]["query"]
    assert "OR" in sample
    assert '"Python"' in sample


def test_sanitize_quotes_in_title():
    result = generate_dorks(SearchParams(title='Software "Engineer"'))
    q = result["categories"][0]["dorks"][0]["query"]
    assert q.count('"') % 2 == 0
