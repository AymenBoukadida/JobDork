from app.dork_engine import SearchParams, generate_dorks
from app.experience_filters import NO_EXPERIENCE, ZERO_EXP_POSITIVE
from app.query_builder import assemble_query, intitle_clause


def test_no_experience_option_in_queries():
    result = generate_dorks(
        SearchParams(title="Software Engineer", experience=NO_EXPERIENCE)
    )
    sample = result["categories"][0]["dorks"][0]["query"]
    assert "no experience required" in sample
    assert '-"5 years"' in sample
    assert '-"3+ years"' in sample
    assert "-senior" in sample
    assert '"entry level"' not in sample


def test_zero_experience_advanced_dork():
    result = generate_dorks(SearchParams(title="Developer", experience="senior"))
    advanced = next(c for c in result["categories"] if c["id"] == "advanced")
    zero = next(d for d in advanced["dorks"] if d["platform_id"] == "zero_experience")
    assert ZERO_EXP_POSITIVE in zero["query"]
    assert '-"5 years"' in zero["query"]
    assert '"senior"' not in zero["query"] or "-senior" in zero["query"]


def test_entry_level_adds_year_excludes():
    result = generate_dorks(SearchParams(title="Engineer", experience="entry level"))
    sample = result["categories"][0]["dorks"][0]["query"]
    assert '"entry level"' in sample
    assert '-"5 years"' in sample
    assert "-senior" in sample
    assert "no experience required" not in sample


def test_tunisia_hidden_without_location():
    result = generate_dorks(SearchParams(title="Engineer"))
    ids = {c["id"] for c in result["categories"]}
    assert "tunisia" not in ids


def test_tunisia_shown_with_location():
    result = generate_dorks(SearchParams(title="Engineer", location="Tunis"))
    ids = {c["id"] for c in result["categories"]}
    assert "tunisia" in ids


def test_exact_title_match_uses_intitle_not_broken_prefix():
    result = generate_dorks(
        SearchParams(titles=["Software Engineer", "Backend Developer"], title_mode="or")
    )
    advanced = next(c for c in result["categories"] if c["id"] == "advanced")
    exact = next(d for d in advanced["dorks"] if d["platform_id"] == "exact_title")
    assert (
        'intitle:"Software Engineer" OR intitle:"Backend Developer"' in exact["query"]
    )
    assert 'intitle:"Software Engineer" "Backend Developer"' not in exact["query"]


def test_recent_listings_groups_or_terms():
    result = generate_dorks(SearchParams(title="Engineer"))
    advanced = next(c for c in result["categories"] if c["id"] == "advanced")
    recent = next(d for d in advanced["dorks"] if d["platform_id"] == "recent")
    assert '"Engineer" ("posted" OR "posted on" OR "date posted")' in recent["query"]


def test_assemble_query_protects_excludes_and_site():
    core = '"Engineer" ' + " ".join(f'"skill{i}"' for i in range(30))
    protected = '-"5 years" site:indeed.com/jobs'
    result = assemble_query(core, protected, max_chars=250)
    assert "site:indeed.com/jobs" in result.query
    assert '-"5 years"' in result.query


def test_intitle_clause_single_title():
    assert intitle_clause(["Developer"], "or") == 'intitle:"Developer"'
