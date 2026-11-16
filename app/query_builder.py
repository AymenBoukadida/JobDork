from __future__ import annotations

import re
from dataclasses import dataclass

MAX_QUERY_CHARS = 1800
SOFT_WARN_CHARS = 1500


_OPERATOR_RE = re.compile(
    r"^(intitle|inurl|site|filetype|allintitle|allinurl):\s*(.*)$", re.IGNORECASE
)


def sanitize_term(value: str) -> str:
    if not value:
        return ""
    cleaned = value.replace('"', "")
    cleaned = re.sub(r"\s+", " ", cleaned.strip())
    return cleaned[:120]


def _quote_phrase(value: str) -> str:
    return f'"{value}"' if " " in value else value


def sanitize_operator_token(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    negated = raw.startswith("-")
    body = raw[1:].strip() if negated else raw
    if not body:
        return ""
    operator_match = _OPERATOR_RE.match(body)
    if operator_match:
        operator = operator_match.group(1).lower()
        operand = sanitize_term(operator_match.group(2))
        if not operand:
            return ""
        token = f"{operator}:{_quote_phrase(operand)}"
    else:
        term = sanitize_term(body)
        if not term:
            return ""
        token = _quote_phrase(term)
    return f"-{token}" if negated else token


def normalize_exclude_token(value: str) -> str:
    token = sanitize_operator_token(value)
    if not token:
        return ""
    return token if token.startswith("-") else f"-{token}"


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
        token = normalize_exclude_token(raw)
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


def group_top_level_or(clause: str) -> str:
    """Wrap a filter that joins alternatives so it stays one search operand."""
    clause = clause.strip()
    if " OR " not in clause:
        return clause
    depth = 0
    in_quotes = False
    index = 0
    while index < len(clause):
        char = clause[index]
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(depth - 1, 0)
            elif depth == 0 and clause.startswith(" OR ", index):
                return f"({clause})"
        index += 1
    return clause


def join_query_parts(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


@dataclass
class TrimResult:
    query: str
    truncated: bool
    original_length: int
    dropped: list[str]


MIN_CORE_CHARS = 80


def _split_top_level(text: str) -> list[str]:
    """Split on whitespace that sits outside quotes and parentheses."""
    parts: list[str] = []
    buffer: list[str] = []
    depth = 0
    in_quotes = False
    for char in text:
        if char == '"':
            in_quotes = not in_quotes
            buffer.append(char)
        elif not in_quotes and char == "(":
            depth += 1
            buffer.append(char)
        elif not in_quotes and char == ")":
            depth = max(depth - 1, 0)
            buffer.append(char)
        elif char.isspace() and not in_quotes and depth == 0:
            if buffer:
                parts.append("".join(buffer))
                buffer = []
        else:
            buffer.append(char)
    if buffer:
        parts.append("".join(buffer))
    return parts


def _split_alternatives(text: str) -> list[str]:
    """Split an OR group's body into alternatives, respecting nesting."""
    alternatives: list[str] = []
    depth = 0
    in_quotes = False
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(depth - 1, 0)
            elif depth == 0 and text.startswith(" OR ", index):
                alternatives.append(text[start:index].strip())
                index += 4
                start = index
                continue
        index += 1
    alternatives.append(text[start:].strip())
    return [part for part in alternatives if part]


def _is_group(token: str) -> bool:
    if not (token.startswith("(") and token.endswith(")")):
        return False
    depth = 0
    in_quotes = False
    for index, char in enumerate(token):
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(token) - 1:
                    return False
    return depth == 0


def _drop_unit(components: list[str], index: int) -> tuple[list[str], str]:
    """Drop one complete search unit, keeping operators attached to operands."""
    component = components[index]
    if _is_group(component):
        alternatives = _split_alternatives(component[1:-1].strip())
        if len(alternatives) > 1:
            rebuilt = f"({' OR '.join(alternatives[:-1])})"
            remaining = components[:index] + [rebuilt] + components[index + 1 :]
            return remaining, alternatives[-1]
    return components[:index] + components[index + 1 :], component


def trim_query(
    query: str,
    *,
    max_chars: int = MAX_QUERY_CHARS,
    preserve_negatives: bool = True,
) -> TrimResult:
    original = query
    if len(query) <= max_chars:
        return TrimResult(
            query=query, truncated=False, original_length=len(original), dropped=[]
        )

    dropped: list[str] = []
    working = query
    while len(working) > max_chars:
        components = _split_top_level(working)
        if not components:
            working = ""
            break
        index = len(components) - 1
        if preserve_negatives:
            positive = [
                position
                for position, component in enumerate(components)
                if not component.startswith("-")
            ]
            if positive:
                index = positive[-1]
        remaining, removed = _drop_unit(components, index)
        if not removed:
            break
        dropped.append(removed)
        updated = " ".join(remaining).strip()
        if updated == working:
            break
        working = updated

    if len(working) > max_chars:
        working = working[:max_chars].rstrip()
        dropped.append("(hard trim)")

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
    """Join core terms with protected filters, dropping whole units if needed.

    Protected filters are ordered by ascending priority: trimming drops the
    trailing (least important) ones before touching the leading scope filter.
    """
    core = core.strip()
    protected = protected.strip()
    original = join_query_parts([core, protected])
    if not protected:
        return trim_query(core, max_chars=max_chars)

    min_core = min(MIN_CORE_CHARS, max(max_chars // 2, 1))
    protected_budget = max(max_chars - min_core, 1)
    protected_trimmed = trim_query(
        protected, max_chars=protected_budget, preserve_negatives=False
    )
    core_budget = max(
        max_chars - len(protected_trimmed.query) - (1 if protected_trimmed.query else 0),
        min_core,
    )
    core_trimmed = trim_query(core, max_chars=core_budget)
    query = join_query_parts([core_trimmed.query, protected_trimmed.query])
    if len(query) > max_chars:
        query = trim_query(
            query, max_chars=max_chars, preserve_negatives=False
        ).query
    return TrimResult(
        query=query,
        truncated=core_trimmed.truncated or protected_trimmed.truncated,
        original_length=len(original),
        dropped=[*core_trimmed.dropped, *protected_trimmed.dropped],
    )


def query_length_warning(length: int) -> str | None:
    if length > MAX_QUERY_CHARS:
        return f"Query exceeds {MAX_QUERY_CHARS} characters and was trimmed."
    if length > SOFT_WARN_CHARS:
        return f"Query is long ({length} chars); Google may truncate or rank poorly."
    return None
