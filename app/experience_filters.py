from __future__ import annotations

from app.query_builder import google_quoted

NO_EXPERIENCE = "no_experience"
ENTRY_LEVEL = "entry level"

ZERO_EXP_POSITIVE = (
    '("no experience required" OR "no prior experience" OR "no experience necessary" '
    'OR "0 years" OR "fresh graduate" OR "recent graduate" OR "new graduate" OR trainee)'
)

ZERO_EXP_EXCLUDE_TOKENS = (
    '-"5 years"',
    '-"5+ years"',
    '-"4+ years"',
    '-"4 years"',
    '-"3+ years"',
    '-"3 years"',
    '-"minimum 3"',
    '-"minimum 5"',
    "-senior",
    '-"years of experience"',
)

ENTRY_LEVEL_EXCLUDE_TOKENS = (
    '-"5+ years"',
    '-"5 years"',
    '-"minimum 5"',
    "-senior",
)


def is_no_experience(experience: str) -> bool:
    normalized = experience.lower().replace("-", "_").replace(" ", "_")
    return normalized in ("no_experience", "zero", "0")


def is_entry_level(experience: str) -> bool:
    return experience.lower().strip() == ENTRY_LEVEL


def experience_clause(experience: str) -> str:
    if is_no_experience(experience):
        return ZERO_EXP_POSITIVE
    if experience:
        return google_quoted(experience)
    return ""


def zero_experience_exclude_tokens() -> list[str]:
    return list(ZERO_EXP_EXCLUDE_TOKENS)


def entry_level_exclude_tokens() -> list[str]:
    return list(ENTRY_LEVEL_EXCLUDE_TOKENS)


def experience_exclude_tokens(experience: str) -> list[str]:
    if is_no_experience(experience):
        return zero_experience_exclude_tokens()
    if is_entry_level(experience):
        return entry_level_exclude_tokens()
    return []
