import re

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


def test_parse_cv_does_not_use_skills_as_location():
    cv = (
        "AYMEN BOUKADIDA\n"
        "Penetration Tester\n"
        "Tunis, Tunisia\n"
        "aymen@example.com\n"
        "SKILLS\n"
        "Metasploit, Burp Suite, Mimikatz, SSH, Nmap, Wireshark\n"
    )
    result = parse_cv_text(cv)
    assert result.location == "Tunis, Tunisia"


def test_parse_cv_location_rejects_non_country_uppercase():
    cv = "Jane Smith\nSoftware Engineer\nWindows, SSH\nAzure, AWS\nLondon, UK\n"
    result = parse_cv_text(cv)
    assert result.location == "London, UK"


def test_parse_cv_location_explicit_line_wins():
    cv = "Jane Smith\nSoftware Engineer\nLocation: Berlin, Germany\nLondon, UK\n"
    result = parse_cv_text(cv)
    assert result.location == "Berlin, Germany"


def test_parse_cv_canonicalizes_skill_names():
    cv = (
        "Jane Doe\n"
        "Data Engineer\n"
        "Skills\n"
        "Python, PostgreSQL, FastAPI, AWS, JavaScript, TypeScript\n"
    )
    result = parse_cv_text(cv)
    assert result.skills[:6] == [
        "Python",
        "PostgreSQL",
        "FastAPI",
        "AWS",
        "JavaScript",
        "TypeScript",
    ]


def test_parse_cv_orders_skills_by_first_mention():
    cv = "Jane Doe\nSoftware Engineer\nSkills\nFastAPI, Python, Docker\n"
    result = parse_cv_text(cv)
    assert result.skills[:3] == ["FastAPI", "Python", "Docker"]


def test_parse_cv_drops_work_mode_tokens_from_skills():
    cv = (
        "Jane Doe\n"
        "Backend Developer\n"
        "Skills\n"
        "Python, remote-friendly, hybrid, on-site, visa sponsorship, Docker\n"
    )
    result = parse_cv_text(cv)
    assert result.skills[:2] == ["Python", "Docker"]
    assert all(
        token not in {s.lower() for s in result.skills}
        for token in ("remote-friendly", "hybrid", "on-site", "visa sponsorship")
    )


def test_keyword_mode_or_in_skills():
    result = generate_dorks(
        SearchParams(title="Engineer", skills=["Python", "Go"], keyword_mode="or")
    )
    sample = result["categories"][0]["dorks"][0]["query"]
    assert "OR" in sample
    assert '"Python"' in sample


def test_modes_are_case_insensitive_and_invalid_values_fall_back():
    params = SearchParams(title="Engineer", keyword_mode="OR", title_mode="AND")
    assert params.keyword_mode == "or"
    assert params.title_mode == "and"

    params = SearchParams(title="Engineer", keyword_mode="xor", title_mode="nope")
    assert (params.keyword_mode, params.title_mode) == ("and", "or")


def test_skills_are_deduplicated_and_capped():
    params = SearchParams(
        title="Engineer",
        skills=["Python", " python ", "AWS", ""] + [f"skill{i}" for i in range(20)],
    )
    assert params.skills[:3] == ["Python", "AWS", "skill0"]
    assert len(params.skills) == 12


def test_exclude_terms_are_deduplicated():
    params = SearchParams(title="Engineer", exclude_terms=["intern", " Intern ", ""])
    assert params.exclude_terms == ["intern"]


def test_ats_ids_are_normalized_and_deduplicated():
    params = SearchParams(
        title="Engineer", ats_platforms=["Lever", "lever", " Greenhouse "]
    )
    result = generate_dorks(params)
    ats = next(c for c in result["categories"] if c["id"] == "ats")
    assert [d["label"] for d in ats["dorks"]] == ["Lever", "Greenhouse"]


def test_time_filter_is_normalized_or_ignored():
    assert SearchParams(title="Engineer", time_filter="30D").time_filter == "30d"
    assert SearchParams(title="Engineer", time_filter="1y").time_filter == ""


def test_sanitize_quotes_in_title():
    result = generate_dorks(SearchParams(title='Software "Engineer"'))
    q = result["categories"][0]["dorks"][0]["query"]
    assert q.count('"') % 2 == 0


def test_generated_queries_negate_excludes_and_keep_default_phrase():
    result = generate_dorks(
        SearchParams(
            title="Backend Developer",
            exclude_terms=["intern", "contract", "training course"],
        )
    )
    query = result["categories"][0]["dorks"][0]["query"]
    assert '-intitle:"how to become"' in query
    assert "-intern" in query
    assert "-contract" in query
    assert '-"training course"' in query
    assert " to become " not in query.replace('-intitle:"how to become"', "")


def test_preset_excludes_are_negated_and_preset_skills_default_to_or():
    params = SearchParams(preset_id="data")
    assert params.keyword_mode == "or"
    result = generate_dorks(params)
    query = result["categories"][0]["dorks"][0]["query"]
    assert "-bootcamp" in query
    assert '-"certificate program"' in query
    assert '("Python" OR "SQL"' in query
    assert " bootcamp " not in query
    assert " certificate program " not in query


def test_remote_with_location_keeps_location():
    result = generate_dorks(
        SearchParams(title="Technical Writer", location="Berlin", remote=True)
    )
    query = result["categories"][0]["dorks"][0]["query"]
    assert '("remote" OR "work from home" OR "WFH")' in query
    assert '"Berlin"' in query


def test_experience_is_normalized_and_invalid_values_are_dropped():
    assert SearchParams(title="X", experience="Senior").experience == "senior"
    assert SearchParams(title="X", experience="entry").experience == "entry level"
    assert SearchParams(title="X", experience="banana").experience == ""
    query = generate_dorks(
        SearchParams(title="Engineer", experience="banana")
    )["categories"][0]["dorks"][0]["query"]
    assert '"banana"' not in query


def test_preset_id_is_case_insensitive():
    params = SearchParams(preset_id="DATA")
    assert params.preset_id == "data"
    assert params.titles


def test_unknown_preset_raises_clear_error():
    with pytest.raises(ValueError, match="Unknown domain preset"):
        SearchParams(preset_id="not-a-preset")


def test_oversized_inputs_are_trimmed_with_warnings():
    titles = [f"Title {i}" for i in range(7)]
    skills = [f"Skill {i}" for i in range(13)]
    result = generate_dorks(
        SearchParams(titles=titles, skills=skills, title="A" * 200)
    )
    assert len(result["params"]["titles"]) == 6
    assert len(result["params"]["skills"]) == 12
    assert any("first 6 job titles" in w for w in result["warnings"])
    assert any("first 12 skills" in w for w in result["warnings"])
    assert any("shortened to 120" in w for w in result["warnings"])


def test_extreme_inputs_keep_queries_within_length_and_syntax_limits():
    def distinct(prefix: str, count: int) -> list[str]:
        return [f"{prefix}{i:02d}" + "x" * 110 for i in range(count)]

    result = generate_dorks(
        SearchParams(
            titles=distinct("Title ", 8),
            skills=distinct("Skill ", 14),
            exclude_terms=distinct("Exclude ", 16),
            location="L" * 120,
            company="C" * 120,
            remote=True,
            experience="senior",
            time_filter="30d",
            title_mode="or",
            keyword_mode="or",
            company_domains=[f"company{i}.com" for i in range(4)],
        )
    )
    assert result["warnings"]
    for category in result["categories"]:
        for dork in category["dorks"]:
            query = dork["query"]
            assert len(query) <= 1800, query
            assert query.count('"') % 2 == 0, query
            assert query.count("(") == query.count(")"), query
            assert not re.search(r"-(?:intitle|inurl|site|filetype):(\s|$)", query), query
            assert not re.search(
                r"(?:^|\s)(?:intitle|inurl|site|filetype):(\s|$)", query
            ), query
            assert not re.search(r"\(\s*OR\b|\bOR\s*\)|(^|\s)OR\s*$", query), query
    linkedin = next(
        dork
        for category in result["categories"]
        for dork in category["dorks"]
        if dork["label"] == "LinkedIn Jobs"
    )
    assert "site:linkedin.com/jobs/view" in linkedin["query"]


def _has_top_level_site_or(query: str) -> bool:
    depth = 0
    in_quotes = False
    for index, char in enumerate(query):
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(depth - 1, 0)
            elif depth == 0 and query.startswith(" OR site:", index):
                return True
    return False


def test_all_generated_site_or_filters_are_grouped():
    scenarios = [
        SearchParams(title="Backend Developer", exclude_terms=["intern"]),
        SearchParams(preset_id="data"),
        SearchParams(preset_id="cybersecurity"),
        SearchParams(title="Engineer", location="Tunis", remote=True),
        SearchParams(title="DevOps", ats_platforms=["greenhouse", "jobvite"]),
        SearchParams(title="Designer", company="Stripe", company_domains=["a.io", "b.io"]),
    ]
    for params in scenarios:
        result = generate_dorks(params)
        for category in result["categories"]:
            for dork in category["dorks"]:
                query = dork["query"]
                assert not _has_top_level_site_or(query), query
