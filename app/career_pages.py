from __future__ import annotations

import re

AGGREGATOR_DOMAINS: tuple[str, ...] = (
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "monster.com",
    "dice.com",
    "careerbuilder.com",
    "simplyhired.com",
    "jooble.org",
    "adzuna.com",
    "talent.com",
    "neuvoo.com",
)

CAREER_PATH_FILTER = (
    "(inurl:careers OR inurl:jobs OR inurl:join-us OR inurl:work-with-us)"
)

HIRING_PHRASES = (
    '("we are hiring" OR "we\'re hiring" OR "now hiring" OR "join our team")'
)

ATS_BOARD_SITES = (
    "site:boards.greenhouse.io",
    "site:job-boards.greenhouse.io",
    "site:jobs.lever.co",
    "site:jobs.ashbyhq.com",
    "site:jobs.smartrecruiters.com",
    "site:apply.workable.com",
)

_DOMAIN_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"
)


def aggregator_exclude_clause(domains: tuple[str, ...] = AGGREGATOR_DOMAINS) -> str:
    return " ".join(f"-site:{d}" for d in domains)


def sanitize_company_domain(raw: str) -> str:
    if not raw:
        return ""
    value = raw.strip().lower()
    value = re.sub(r"^[a-z]+://", "", value)
    value = value.split("/", 1)[0]
    value = value.split("?", 1)[0].split("#", 1)[0]
    if value.startswith("www."):
        value = value[4:]
    if "@" in value:
        value = value.rsplit("@", 1)[1]
    value = value.strip(".")
    if len(value) > 100 or not _DOMAIN_RE.match(value):
        return ""
    return value
