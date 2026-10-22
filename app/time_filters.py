from __future__ import annotations

from datetime import date, timedelta

TIME_FILTERS: dict[str, int] = {
    "24h": 1,
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "180d": 180,
}


def time_filter_clause(filter_key: str) -> str:
    days = TIME_FILTERS.get(filter_key or "")
    if not days:
        return ""
    after = date.today() - timedelta(days=days)
    return f"after:{after.isoformat()}"


def list_time_filters() -> list[dict[str, str]]:
    labels = {
        "24h": "Past 24 hours",
        "7d": "Past week",
        "30d": "Past month",
        "90d": "Past 3 months",
        "180d": "Past 6 months",
    }
    return [{"id": k, "label": labels[k]} for k in TIME_FILTERS]
