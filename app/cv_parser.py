from __future__ import annotations

import io
import re
from dataclasses import dataclass

KNOWN_SKILLS: frozenset[str] = frozenset(
    {
        "python",
        "javascript",
        "typescript",
        "java",
        "c#",
        "c++",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "react",
        "vue",
        "angular",
        "next.js",
        "node.js",
        "django",
        "flask",
        "fastapi",
        "spring",
        "express",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "ci/cd",
        "git",
        "linux",
        "agile",
        "scrum",
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "spark",
        "kafka",
        "graphql",
        "rest",
        "api",
        "microservices",
        "figma",
        "salesforce",
        "tableau",
        "power bi",
        "excel",
        "project management",
        "product management",
    }
)

TITLE_PATTERNS = re.compile(
    r"\b("
    r"software engineer(?:ing)?|full[\s-]?stack developer|backend developer|"
    r"frontend developer|front[\s-]?end developer|data (?:scientist|analyst|engineer)|"
    r"devops engineer|site reliability engineer|sre|platform engineer|"
    r"cloud engineer|security engineer|qa engineer|test engineer|"
    r"mobile developer|ios developer|android developer|"
    r"product manager|project manager|business analyst|"
    r"ux designer|ui designer|designer|"
    r"technical lead|engineering manager|architect"
    r")\b",
    re.IGNORECASE,
)

EXPERIENCE_LEVEL_MAP = (
    (re.compile(r"\b(principal|staff|distinguished|lead|head of)\b", re.I), "lead"),
    (re.compile(r"\b(senior|sr\.?)\b", re.I), "senior"),
    (
        re.compile(
            r"\b(no experience|without experience|0 years|zero years|fresh grad)\b",
            re.I,
        ),
        "no_experience",
    ),
    (
        re.compile(r"\b(junior|jr\.?|entry[\s-]?level|graduate|intern)\b", re.I),
        "entry level",
    ),
    (re.compile(r"\b(mid[\s-]?level|intermediate)\b", re.I), "mid level"),
)

SKILLS_SECTION = re.compile(
    r"(?:^|\n)\s*(?:technical\s+)?skills?\s*(?:&|and)?\s*(?:competenc(?:ies|e))?\s*:?\s*\n",
    re.IGNORECASE,
)

MAX_CV_BYTES = 5 * 1024 * 1024


@dataclass
class CvParseResult:
    title: str
    location: str
    skills: list[str]
    experience: str
    suggested_remote: bool
    raw_text_preview: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "location": self.location,
            "skills": self.skills,
            "experience": self.experience,
            "suggested_remote": self.suggested_remote,
            "raw_text_preview": self.raw_text_preview,
        }


def extract_text_from_cv(filename: str, content: bytes) -> str:
    if len(content) > MAX_CV_BYTES:
        raise ValueError("CV file is too large (max 5 MB)")

    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _text_from_pdf(content)
    if lower.endswith(".docx"):
        return _text_from_docx(content)
    if lower.endswith((".txt", ".md")):
        return _text_from_plain(content)
    raise ValueError("Unsupported format. Use PDF, DOCX, or TXT.")


def parse_cv_text(text: str) -> CvParseResult:
    normalized = _normalize_text(text)
    title = _extract_title(normalized)
    location = _extract_location(normalized)
    skills = _extract_skills(normalized)
    experience = _extract_experience_level(normalized, title)
    remote = bool(
        re.search(r"\b(remote|work from home|wfh|distributed)\b", normalized, re.I)
    )

    preview = normalized[:800] + ("…" if len(normalized) > 800 else "")

    return CvParseResult(
        title=title,
        location=location,
        skills=skills,
        experience=experience,
        suggested_remote=remote,
        raw_text_preview=preview,
    )


def parse_cv_file(filename: str, content: bytes) -> CvParseResult:
    text = extract_text_from_cv(filename, content)
    if not text.strip():
        raise ValueError("Could not extract text from this file")
    return parse_cv_text(text)


def _text_from_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _text_from_docx(content: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _text_from_plain(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file")


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_title(text: str) -> str:
    head = text[:2500]
    match = TITLE_PATTERNS.search(head)
    if match:
        return _title_case(match.group(1))

    for line in text.split("\n")[:12]:
        line = line.strip()
        if not line or len(line) > 80:
            continue
        if "@" in line or re.search(r"\d{3}[-.\s]?\d", line):
            continue
        if line.lower() in {"curriculum vitae", "resume", "cv"}:
            continue
        if len(line.split()) <= 6:
            return line
    return ""


def _title_case(role: str) -> str:
    small = {"of", "and", "or", "the", "in", "for"}
    words = role.split()
    result = []
    for i, w in enumerate(words):
        lw = w.lower()
        if i > 0 and lw in small:
            result.append(lw)
        else:
            result.append(lw.capitalize() if lw != "sre" else "SRE")
    return " ".join(result)


def _extract_location(text: str) -> str:
    loc_line = re.search(
        r"(?:^|\n)\s*(?:location|based in|address)\s*:?\s*([^\n]+)",
        text,
        re.I,
    )
    if loc_line:
        loc = loc_line.group(1).strip()
        if len(loc) < 60:
            return loc

    city_country = re.search(
        r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s*(?:UK|USA|US|United Kingdom|United States|[A-Z]{2,}))\b",
        text[:2000],
    )
    if city_country:
        return city_country.group(1)
    return ""


def _extract_skills(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    section = SKILLS_SECTION.search(text)
    skill_blob = text[section.end() : section.end() + 1200] if section else text

    lower_blob = skill_blob.lower()
    for skill in sorted(KNOWN_SKILLS, key=len, reverse=True):
        pattern = re.escape(skill).replace(r"\ ", r"[\s-]?")
        if re.search(rf"\b{pattern}\b", lower_blob, re.I):
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                display = (
                    skill.upper()
                    if skill in {"aws", "gcp", "sql", "api", "ci/cd", "sre"}
                    else skill.title()
                )
                if skill == "c++":
                    display = "C++"
                elif skill == "node.js":
                    display = "Node.js"
                elif skill == "next.js":
                    display = "Next.js"
                found.append(display)

    if section:
        block = skill_blob.split("\n\n")[0]
        for part in re.split(r"[,|•·\n/;]", block):
            token = part.strip()
            if 2 <= len(token) <= 40 and not token.isdigit():
                key = token.lower()
                if key not in seen and len(found) < 12:
                    seen.add(key)
                    found.append(token)

    return found[:10]


def _extract_experience_level(text: str, title: str) -> str:
    combined = f"{title}\n{text[:3000]}"
    for pattern, level in EXPERIENCE_LEVEL_MAP:
        if pattern.search(combined):
            return level
    years = re.search(
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience", combined, re.I
    )
    if years:
        n = int(years.group(1))
        if n >= 8:
            return "senior"
        if n >= 4:
            return "mid level"
        if n == 0:
            return "no_experience"
        if n >= 1:
            return "entry level"
    return ""
