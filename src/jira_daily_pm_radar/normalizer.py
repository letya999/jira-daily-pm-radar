from __future__ import annotations

import re
from typing import Any

from jira_daily_pm_radar.models import ChangeItem, ChangeLogEntry, Comment, Issue, Scope, SprintInfo
from jira_daily_pm_radar.time_utils import parse_datetime

ADF_TEXT_RE = re.compile(r"'text': '([^']+)'")


def adf_to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "text" and isinstance(node.get("text"), str):
                    parts.append(node["text"])
                for child in node.get("content", []) or []:
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(value)
        return "\n".join(parts).strip() or None
    return str(value)


def get_name(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return (
            str(
                value.get("displayName")
                or value.get("name")
                or value.get("value")
                or value.get("key")
                or ""
            )
            or None
        )
    return str(value)


def normalize_sprint(value: Any) -> SprintInfo | None:
    if value is None:
        return None
    sprint_data: dict[str, Any] | None = None
    if isinstance(value, list) and value:
        last = value[-1]
        if isinstance(last, dict):
            sprint_data = last
    elif isinstance(value, dict):
        sprint_data = value
    if not sprint_data:
        return None
    return SprintInfo(
        id=sprint_data.get("id"),
        name=sprint_data.get("name"),
        state=sprint_data.get("state"),
        start_date=parse_datetime(sprint_data.get("startDate")),
        end_date=parse_datetime(sprint_data.get("endDate")),
    )


def normalize_comments(raw_comments: list[dict[str, Any]]) -> list[Comment]:
    comments: list[Comment] = []
    for raw in raw_comments:
        comments.append(
            Comment(
                author=get_name(raw.get("author")),
                body=adf_to_text(raw.get("body")) or "",
                created=parse_datetime(raw.get("created")),
                updated=parse_datetime(raw.get("updated")),
            )
        )
    return comments


def normalize_changelog(raw_changelog: list[dict[str, Any]]) -> list[ChangeLogEntry]:
    entries: list[ChangeLogEntry] = []
    for raw in raw_changelog:
        created = parse_datetime(raw.get("created"))
        if created is None:
            continue
        items: list[ChangeItem] = []
        for item in raw.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            items.append(
                ChangeItem(
                    field=str(item.get("field") or item.get("fieldId") or "unknown"),
                    from_value=item.get("fromString"),
                    to_value=item.get("toString"),
                )
            )
        entries.append(
            ChangeLogEntry(author=get_name(raw.get("author")), created=created, items=items)
        )
    return entries


def normalize_issue(
    raw: dict[str, Any],
    *,
    scope: Scope = Scope.UNKNOWN,
    base_url: str | None = None,
    fields_map: dict[str, Any] | None = None,
) -> Issue:
    fields_map = fields_map or {}
    fields = raw.get("fields", {}) if isinstance(raw.get("fields", {}), dict) else {}
    key = str(raw.get("key") or fields.get("key") or "UNKNOWN")
    priority = fields.get("priority")
    status = fields.get("status")
    status_category = status.get("statusCategory") if isinstance(status, dict) else None
    issue_type = fields.get("issuetype")
    parent = fields.get("parent")

    epic_field = fields_map.get("optional_fields", {}).get("epic_link", "customfield_10014")
    story_points_field = fields_map.get("optional_fields", {}).get(
        "story_points", "customfield_10016"
    )
    sprint_field = fields_map.get("optional_fields", {}).get("sprint", "customfield_10020")
    rank_field = fields_map.get("optional_fields", {}).get("rank", "customfield_10019")

    labels = fields.get("labels") or []
    components = [
        component.get("name")
        for component in fields.get("components", [])
        if isinstance(component, dict)
    ]
    subtasks = [
        subtask.get("key") for subtask in fields.get("subtasks", []) if isinstance(subtask, dict)
    ]

    story_points_raw = fields.get(story_points_field)
    try:
        story_points = float(story_points_raw) if story_points_raw is not None else None
    except (TypeError, ValueError):
        story_points = None

    return Issue(
        key=key,
        summary=str(fields.get("summary") or raw.get("summary") or ""),
        description=adf_to_text(fields.get("description")),
        status=get_name(status),
        status_category=get_name(status_category),
        resolution=get_name(fields.get("resolution")),
        priority=get_name(priority),
        issue_type=get_name(issue_type),
        assignee=get_name(fields.get("assignee")),
        reporter=get_name(fields.get("reporter")),
        created=parse_datetime(fields.get("created")),
        updated=parse_datetime(fields.get("updated")),
        labels=[str(label) for label in labels if label],
        components=[str(component) for component in components if component],
        sprint=normalize_sprint(fields.get(sprint_field)),
        scope=scope,
        rank=str(fields.get(rank_field)) if fields.get(rank_field) is not None else None,
        epic=str(fields.get(epic_field)) if fields.get(epic_field) else None,
        parent=str(parent.get("key")) if isinstance(parent, dict) else None,
        story_points=story_points,
        subtasks=[str(subtask) for subtask in subtasks if subtask],
        url=f"{base_url.rstrip('/')}/browse/{key}" if base_url else None,
        comments=normalize_comments(
            raw.get("_comments", []) if isinstance(raw.get("_comments"), list) else []
        ),
        changelog=normalize_changelog(
            raw.get("_changelog", []) if isinstance(raw.get("_changelog"), list) else []
        ),
        raw=raw,
    )
