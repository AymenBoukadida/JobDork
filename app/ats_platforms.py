from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AtsPlatform:
    id: str
    name: str
    site_filter: str
    description: str


ATS_PLATFORMS: tuple[AtsPlatform, ...] = (
    AtsPlatform(
        "greenhouse",
        "Greenhouse",
        "site:boards.greenhouse.io OR site:job-boards.greenhouse.io",
        "Greenhouse ATS",
    ),
    AtsPlatform(
        "lever",
        "Lever",
        "site:jobs.lever.co",
        "Lever ATS",
    ),
    AtsPlatform(
        "ashby",
        "Ashby",
        "site:jobs.ashbyhq.com",
        "Ashby ATS",
    ),
    AtsPlatform(
        "workday",
        "Workday",
        'inurl:myworkdayjobs.com "apply"',
        "Workday career portals",
    ),
    AtsPlatform(
        "smartrecruiters",
        "SmartRecruiters",
        "site:jobs.smartrecruiters.com",
        "SmartRecruiters ATS",
    ),
    AtsPlatform(
        "bamboohr",
        "BambooHR",
        "inurl:bamboohr.com/careers",
        "BambooHR career pages",
    ),
    AtsPlatform(
        "icims",
        "iCIMS",
        "inurl:icims.com/jobs",
        "iCIMS-hosted career sites",
    ),
    AtsPlatform(
        "jobvite",
        "Jobvite",
        "inurl:jobvite.com OR site:jobs.jobvite.com",
        "Jobvite ATS",
    ),
    AtsPlatform(
        "workable",
        "Workable",
        "site:apply.workable.com",
        "Workable-hosted job pages",
    ),
    AtsPlatform(
        "eightfold",
        "Eightfold",
        "site:jobs.eightfold.ai",
        "Eightfold AI career portals",
    ),
    AtsPlatform(
        "teamtailor",
        "Teamtailor",
        "site:teamtailor.com/jobs",
        "Teamtailor career sites (big in EU)",
    ),
    AtsPlatform(
        "recruitee",
        "Recruitee",
        "site:recruitee.com",
        "Recruitee-hosted job pages",
    ),
    AtsPlatform(
        "pinpoint",
        "Pinpoint",
        "site:pinpointhq.com",
        "Pinpoint-hosted job pages",
    ),
    AtsPlatform(
        "breezyhr",
        "Breezy HR",
        "site:breezy.hr",
        "Breezy HR-hosted job pages",
    ),
    AtsPlatform(
        "jazzhr",
        "JazzHR",
        "site:applytojob.com",
        "JazzHR-hosted job boards",
    ),
    AtsPlatform(
        "taleo",
        "Oracle Taleo",
        "inurl:tbe.taleo.net",
        "Oracle Taleo career portals (enterprise)",
    ),
    AtsPlatform(
        "ultipro",
        "UKG / UltiPro",
        "inurl:ultipro.com",
        "UKG (UltiPro) candidate portals",
    ),
)

ATS_BY_ID = {p.id: p for p in ATS_PLATFORMS}


def list_ats_platforms() -> list[dict[str, str]]:
    return [
        {"id": p.id, "name": p.name, "description": p.description}
        for p in ATS_PLATFORMS
    ]


def resolve_ats_platforms(selected_ids: list[str] | None) -> list[AtsPlatform]:
    if selected_ids is None:
        return list(ATS_PLATFORMS)
    unknown = [i for i in selected_ids if i not in ATS_BY_ID]
    if unknown:
        raise ValueError(f"Unknown ATS platform(s): {', '.join(unknown)}")
    return [ATS_BY_ID[i] for i in selected_ids]
