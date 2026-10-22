from __future__ import annotations

import re
from dataclasses import dataclass

MAX_QUERY_CHARS = 1800
SOFT_WARN_CHARS = 1500


def sanitize_term(value: str) -> str:
    if not value:
        return ""
    cleaned = value.replace('"', "").replace("'", "")
    cleaned = re.sub(r"\s+", " ", cleaned.strip())
    return cleaned[:120]


def sanitize_operator_token(value: str) -> str:
    raw = value.strip()
    has_minus = raw.startswith("-")
    body = raw[1:] if has_minus else raw
    body = sanitize_term(body)
    if not body:
        return ""
    return f"-{body}" if has_minus else body


def google_quoted(term: str) -> str:
    term = sanitize_term(term)
    if not term:
        return ""
    return f'"{term}"'


def combine_terms(terms: list[str], mode: str) -> str:
    cleaned = [sanitize_term(t) for t in terms if sanitize_term(t)]
    if not cleaned:
        return ""
    if mode == "or" and len(cleaned) > 1:
        inner = " OR ".join(google_quoted(t) for t in cleaned)
        return f"({inner})"
    return " ".join(google_quoted(t) for t in cleaned)


def intitle_clause(titles: list[str], title_mode: str) -> str:
    cleaned = [sanitize_term(t) for t in titles if sanitize_term(t)]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return f"intitle:{google_quoted(cleaned[0])}"
    if title_mode == "or":
        inner = " OR ".join(f"intitle:{google_quoted(t)}" for t in cleaned)
        return f"({inner})"
    return " ".join(f"intitle:{google_quoted(t)}" for t in cleaned)


def normalize_exclude_list(
    exclude_terms: list[str],
    *,
    title: str,
    skills: list[str],
    company: str,
) -> list[str]:
    positive_blob = " ".join([title, company, *skills]).lower()
    positive_tokens = set(re.findall(r"[a-z0-9+#]+", positive_blob))

    defaults = ["-intitle:reviews", '-intitle:"how to become"']
    seen: set[str] = set()
    result: list[str] = []

    for raw in defaults + exclude_terms:
        token = sanitize_operator_token(raw)
        if not token:
            continue
        neg_body = token.lstrip("-").lower()
        neg_words = set(re.findall(r"[a-z0-9+#]+", neg_body))
        if neg_words and neg_words <= positive_tokens:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(token)
    return result


def join_query_parts(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


@dataclass
class TrimResult:
    query: str
    truncated: bool
    original_length: int
    dropped: list[str]


def trim_query(query: str, *, max_chars: int = MAX_QUERY_CHARS) -> TrimResult:
    original = query
    if len(query) <= max_chars:
        return TrimResult(
            query=query, truncated=False, original_length=len(original), dropped=[]
        )

    dropped: list[str] = []
    working = query
    quoted_pattern = re.compile(r'(?<!-)\s*"[^"]+"')

    while len(working) > max_chars:
        matches = list(quoted_pattern.finditer(working))
        if not matches:
            working = working[:max_chars].rstrip()
            dropped.append("(hard trim)")
            break
        last = matches[-1]
        dropped.append(last.group().strip())
        working = (working[: last.start()] + working[last.end() :]).strip()
        working = re.sub(r"\s+", " ", working)

    return TrimResult(
        query=working,
        truncated=True,
        original_length=len(original),
        dropped=dropped,
    )


def assemble_query(
    core: str,
    protected: str,
    *,
    max_chars: int = MAX_QUERY_CHARS,
) -> TrimResult:
    core = core.strip()
    protected = protected.strip()
    original = join_query_parts([core, protected])
    if not protected:
        return trim_query(core, max_chars=max_chars)

    reserve = len(protected) + (1 if core else 0)
    max_core = max(max_chars - reserve, 80)
    trimmed = trim_query(core, max_chars=max_core)
    query = join_query_parts([trimmed.query, protected])
    return TrimResult(
        query=query,
        truncated=trimmed.truncated,
        original_length=len(original),
        dropped=trimmed.dropped,
    )


def query_length_warning(length: int) -> str | None:
    if length > MAX_QUERY_CHARS:
        return f"Query exceeds {MAX_QUERY_CHARS} characters and was trimmed."
    if length > SOFT_WARN_CHARS:
        return f"Query is long ({length} chars); Google may truncate or rank poorly."
    return None
