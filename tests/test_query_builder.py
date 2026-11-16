import re

import pytest

from app.query_builder import (
    assemble_query,
    combine_terms,
    google_quoted,
    group_top_level_or,
    normalize_exclude_list,
    sanitize_term,
    trim_query,
)


def test_sanitize_strips_stray_quotes_but_keeps_apostrophes():
    assert sanitize_term('senior "engineer"') == "senior engineer"
    assert google_quoted('foo"bar') == '"foobar"'
    assert sanitize_term("O'Reilly") == "O'Reilly"


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


def test_exclude_terms_are_always_negative_and_keep_phrases():
    terms = normalize_exclude_list(
        ["intern", "training course", "-site:example.com", "intitle:reviews"],
        title="Engineer",
        skills=[],
        company="",
    )
    assert terms == [
        "-intitle:reviews",
        '-intitle:"how to become"',
        "-intern",
        '-"training course"',
        "-site:example.com",
    ]


def test_exclude_terms_preserve_default_quoted_phrase():
    terms = normalize_exclude_list(
        [], title="Engineer", skills=[], company=""
    )
    assert '-intitle:"how to become"' in terms
    assert "-intitle:how to become" not in terms


def test_group_top_level_or_wraps_only_bare_alternatives():
    assert group_top_level_or("site:a.com OR site:b.com") == (
        "(site:a.com OR site:b.com)"
    )
    assert group_top_level_or("(site:a.com OR site:b.com)") == (
        "(site:a.com OR site:b.com)"
    )
    assert group_top_level_or('site:a.com (jobs OR careers)') == (
        'site:a.com (jobs OR careers)'
    )


def test_trim_query_when_too_long():
    long_query = '"Software Engineer" ' + " ".join(f'"skill{i}"' for i in range(40))
    result = trim_query(long_query, max_chars=200)
    assert len(result.query) <= 200
    assert result.truncated


def test_trim_query_preserves_minus_quoted_excludes():
    query = '"Engineer" ' + " ".join(f'"skill{i}"' for i in range(20)) + ' -"5 years"'
    result = trim_query(query, max_chars=120)
    assert '-"5 years"' in result.query


def test_trim_query_removes_whole_operators_not_just_operands():
    query = " ".join(f'intitle:"job title {i}"' for i in range(30))
    result = trim_query(query, max_chars=200)
    assert len(result.query) <= 200
    assert not re.search(r"intitle:(\s|$)", result.query)
    assert result.query.count('"') % 2 == 0


def test_trim_query_drops_group_alternatives_without_leaving_dangling_or():
    query = '(intitle:"alpha" OR intitle:"bravo" OR intitle:"charlie")'
    result = trim_query(query, max_chars=30)
    assert len(result.query) <= 30
    assert result.query.count("(") == result.query.count(")")
    assert not re.search(r"(^|\s)OR(\s|$)", result.query)
    assert not re.search(r"intitle:(\s|$)", result.query)


def test_assemble_query_caps_total_length_with_oversized_protected_filters():
    core = '"Engineer" ' + " ".join(f'"skill{i}"' for i in range(6))
    protected = "site:linkedin.com/jobs/view " + " ".join(
        f'-"exclude phrase {i}"' for i in range(25)
    )
    result = assemble_query(core, protected, max_chars=180)
    assert len(result.query) <= 180
    assert result.truncated
    assert "site:linkedin.com/jobs/view" in result.query
    assert result.query.count('"') % 2 == 0
    assert not re.search(r'-(?:intitle|inurl|site|filetype):(\s|$)', result.query)


def test_assemble_query_keeps_site_filter():
    core = '"Engineer" ' + " ".join(f'"skill{i}"' for i in range(25))
    protected = '-"5 years" site:linkedin.com/jobs/view'
    result = assemble_query(core, protected, max_chars=180)
    assert "site:linkedin.com/jobs/view" in result.query
    assert '-"5 years"' in result.query
