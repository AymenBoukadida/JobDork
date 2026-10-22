from datetime import date, timedelta

from app.dork_engine import SearchParams, generate_dorks
from app.time_filters import time_filter_clause


def test_multiple_titles_or_mode():
    result = generate_dorks(
        SearchParams(titles=["Software Engineer", "Backend Developer"], title_mode="or")
    )
    sample = result["categories"][0]["dorks"][0]["query"]
    assert "OR" in sample
    assert "Software Engineer" in sample
    assert "Backend Developer" in sample


def test_time_filter_in_query():
    result = generate_dorks(SearchParams(title="Engineer", time_filter="30d"))
    sample = result["categories"][0]["dorks"][0]["query"]
    expected = time_filter_clause("30d")
    assert expected in sample
    assert expected.startswith("after:")


def test_domain_preset_adds_niche_category():
    result = generate_dorks(
        SearchParams(title="Security Engineer", preset_id="cybersecurity")
    )
    ids = {c["id"] for c in result["categories"]}
    assert "domain" in ids
    domain = next(c for c in result["categories"] if c["id"] == "domain")
    assert len(domain["dorks"]) >= 1


def test_sysadmin_preset():
    result = generate_dorks(
        SearchParams(title="Systems Administrator", preset_id="sysadmin")
    )
    ids = {c["id"] for c in result["categories"]}
    assert "domain" in ids
    domain = next(c for c in result["categories"] if c["id"] == "domain")
    assert any(
        "Sysadmin" in d["label"] or "Linux" in d["label"] for d in domain["dorks"]
    )


def test_tunisia_job_board_category():
    result = generate_dorks(SearchParams(title="Développeur", location="Tunis"))
    tunisia = next(c for c in result["categories"] if c["id"] == "tunisia")
    labels = {d["label"] for d in tunisia["dorks"]}
    assert "TanitJobs" in labels
    assert "Option Carrière TN" in labels
    sample = tunisia["dorks"][0]["query"]
    assert "tanitjobs.com" in sample
    assert "Tunis" in sample


def test_list_presets_includes_sysadmin():
    from app.domain_presets import list_domain_presets

    ids = {p["id"] for p in list_domain_presets()}
    assert "sysadmin" in ids
    assert "it_support" in ids
    assert "it_general" in ids
    assert "tunisia" in ids
