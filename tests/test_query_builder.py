import pytest

from app.query_builder import (
    assemble_query,
    combine_terms,
    google_quoted,
    normalize_exclude_list,
    sanitize_term,
    trim_query,
)


def test_sanitize_strips_stray_quotes():
    assert sanitize_term('senior "engineer"') == "senior engineer"
    assert google_quoted('foo"bar') == '"foobar"'


def test_combine_terms_or_mode():
    clause = combine_terms(["Python", "Go"], "or")
    assert clause == '("Python" OR "Go")'


def test_combine_terms_and_mode():
    clause = combine_terms(["Python", "Go"], "and")
    assert clause == '"Python" "Go"'


def test_exclude_skips_double_negative_on_title_word():
    terms = normalize_exclude_list(
        ["engineer"],
        title="Software Engineer",
        skills=[],
        company="",
    )
    assert "-engineer" not in " ".join(terms).lower()


def test_trim_query_when_too_long():
    long_query = '"Software Engineer" ' + " ".join(f'"skill{i}"' for i in range(40))
    result = trim_query(long_query, max_chars=200)
    assert len(result.query) <= 200
    assert result.truncated


def test_trim_query_preserves_minus_quoted_excludes():
    query = '"Engineer" ' + " ".join(f'"skill{i}"' for i in range(20)) + ' -"5 years"'
    result = trim_query(query, max_chars=120)
    assert '-"5 years"' in result.query


def test_assemble_query_keeps_site_filter():
    core = '"Engineer" ' + " ".join(f'"skill{i}"' for i in range(25))
    protected = '-"5 years" site:linkedin.com/jobs/view'
    result = assemble_query(core, protected, max_chars=180)
    assert "site:linkedin.com/jobs/view" in result.query
    assert '-"5 years"' in result.query
