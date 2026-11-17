from __future__ import annotations

import re

from app.query_builder import google_quoted

NO_EXPERIENCE = "no_experience"
ENTRY_LEVEL = "entry level"
MID_LEVEL = "mid level"
SENIOR = "senior"
LEAD = "lead"

ZERO_EXP_POSITIVE = (
    '("no experience required" OR "no prior experience" OR "no experience necessary" '
    'OR "0 years" OR "fresh graduate" OR "recent graduate" OR "new graduate" OR trainee)'
)

TUNISIA_ENTRY_POSITIVE = (
    '("entry level" OR junior OR débutant OR "jeune diplômé" OR "0-2 ans" '
    "OR SIVP OR PFE)"
)

TUNISIA_ZERO_EXP_POSITIVE = (
    '("jeune diplômé" OR débutant OR "0-2 ans" OR "sans expérience" '
    'OR SIVP OR PFE OR "no experience required")'
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

_EXPERIENCE_ALIASES = {
    "": "",
    "no_experience": NO_EXPERIENCE,
    "no experience": NO_EXPERIENCE,
    "none": NO_EXPERIENCE,
    "zero": NO_EXPERIENCE,
    "0": NO_EXPERIENCE,
    "entry": ENTRY_LEVEL,
    "entry level": ENTRY_LEVEL,
    "entry-level": ENTRY_LEVEL,
    "junior": ENTRY_LEVEL,
    "jr": ENTRY_LEVEL,
    "mid": MID_LEVEL,
    "mid level": MID_LEVEL,
    "mid-level": MID_LEVEL,
    "intermediate": MID_LEVEL,
    "senior": SENIOR,
    "sr": SENIOR,
    "lead": LEAD,
    "staff": LEAD,
    "principal": LEAD,
}

_EXPERIENCE_CLAUSES = {
    ENTRY_LEVEL: '"entry level"',
    MID_LEVEL: '("mid level" OR "mid-level" OR "intermediate")',
    SENIOR: '("senior" OR "sr" OR "experienced")',
    LEAD: '("lead" OR "staff" OR "principal")',
}


def normalize_experience(value: str) -> str:
    key = re.sub(r"\s+", " ", (value or "").strip().lower())
    return _EXPERIENCE_ALIASES.get(key, "")


def is_no_experience(experience: str) -> bool:
    return normalize_experience(experience) == NO_EXPERIENCE


def is_entry_level(experience: str) -> bool:
    return normalize_experience(experience) == ENTRY_LEVEL


def experience_clause(experience: str, *, tunisia: bool = False) -> str:
    normalized = normalize_experience(experience)
    if is_no_experience(normalized):
        if tunisia:
            return TUNISIA_ZERO_EXP_POSITIVE
        return ZERO_EXP_POSITIVE
    if normalized:
        if tunisia and is_entry_level(normalized):
            return TUNISIA_ENTRY_POSITIVE
        return _EXPERIENCE_CLAUSES.get(normalized, google_quoted(normalized))
    return ""


def zero_experience_exclude_tokens() -> list[str]:
    return list(ZERO_EXP_EXCLUDE_TOKENS)


def entry_level_exclude_tokens() -> list[str]:
    return list(ENTRY_LEVEL_EXCLUDE_TOKENS)


def experience_exclude_tokens(experience: str) -> list[str]:
    normalized = normalize_experience(experience)
    if is_no_experience(normalized):
        return zero_experience_exclude_tokens()
    if is_entry_level(normalized):
        return entry_level_exclude_tokens()
    return []
