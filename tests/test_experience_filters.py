from app.dork_engine import SearchParams, generate_dorks
from app.experience_filters import NO_EXPERIENCE, ZERO_EXP_POSITIVE
from app.query_builder import assemble_query, intitle_clause


def _queries(params: SearchParams) -> list[str]:
    result = generate_dorks(params)
    return [d["query"] for c in result["categories"] for d in c["dorks"]]


def _tunisia_dorks(params: SearchParams) -> list[dict]:
    result = generate_dorks(params)
    return next(c for c in result["categories"] if c["id"] == "tunisia")["dorks"]


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


def test_tunisia_entry_uses_french_terms_and_keeps_entry_channels():
    queries = _queries(
        SearchParams(
            titles=["Développeur"], preset_id="tunisia", experience="entry level"
        )
    )
    assert any("junior" in q and "débutant" in q for q in queries)
    assert any('"jeune diplômé"' in q for q in queries)
    assert all("-PFE" not in q for q in queries)
    assert all("-stage" not in q for q in queries)
    assert all("-formation" not in q for q in queries)


def test_tunisia_entry_adds_stage_pfe_sivp_dork():
    dorks = _tunisia_dorks(
        SearchParams(
            titles=["Développeur"], preset_id="tunisia", experience="entry level"
        )
    )
    entry = next(d for d in dorks if d["platform_id"] == "tunisia_entry")
    assert "PFE" in entry["query"]
    assert "SIVP" in entry["query"]
    assert "stage" in entry["query"]
    assert "site:tanitjobs.com" in entry["query"]
    assert "site:keejob.com" in entry["query"]


def test_tunisia_entry_dork_only_for_entry_levels():
    default_dorks = _tunisia_dorks(
        SearchParams(titles=["Développeur"], preset_id="tunisia")
    )
    assert all(d["platform_id"] != "tunisia_entry" for d in default_dorks)

    senior_dorks = _tunisia_dorks(
        SearchParams(titles=["Développeur"], preset_id="tunisia", experience="senior")
    )
    assert all(d["platform_id"] != "tunisia_entry" for d in senior_dorks)


def test_tunisia_zero_experience_uses_local_terms():
    queries = _queries(
        SearchParams(
            titles=["Développeur"], preset_id="tunisia", experience=NO_EXPERIENCE
        )
    )
    assert any(
        '"jeune diplômé"' in q and '"sans expérience"' in q for q in queries
    )
    assert all("-PFE" not in q for q in queries)


def test_tunisia_location_hint_uses_local_entry_terms():
    queries = _queries(
        SearchParams(titles=["Développeur"], location="Tunis", experience="junior")
    )
    assert any("junior" in q and "débutant" in q for q in queries)


def test_tunisia_preset_keeps_training_titles_out_without_hiding_jobs():
    dorks = _tunisia_dorks(SearchParams(titles=["Développeur"], preset_id="tunisia"))
    sample = next(d for d in dorks if d["platform_id"] == "tanitjobs")
    assert "-intitle:formation" in sample["query"]
    assert "-PFE" not in sample["query"]
    assert "-stage" not in sample["query"]

