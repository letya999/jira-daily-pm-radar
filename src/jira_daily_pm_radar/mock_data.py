from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from typing import Any

from jira_daily_pm_radar.time_utils import now_tz


def _issue(
    key: str,
    summary: str,
    *,
    status: str,
    category: str,
    priority: str | None,
    issue_type: str = "Task",
    assignee: str | None = "Ivan Petrov",
    labels: list[str] | None = None,
    days_updated_ago: int = 0,
    scope_sprint: dict[str, Any] | None = None,
    description: str
    | None = "Normal description with Acceptance Criteria: user can complete the expected flow.",
    epic: str | None = "TWIN-EPIC-1",
    story_points: int | None = 3,
    comments: list[dict[str, Any]] | None = None,
    changelog: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    now = now_tz()
    updated = now - timedelta(days=days_updated_ago)
    fields: dict[str, Any] = {
        "summary": summary,
        "description": {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": description or ""}]}
            ],
        },
        "status": {"name": status, "statusCategory": {"name": category}},
        "resolution": None,
        "priority": {"name": priority} if priority else None,
        "issuetype": {"name": issue_type},
        "assignee": {"displayName": assignee} if assignee else None,
        "reporter": {"displayName": "Artem Letyushev"},
        "created": (now - timedelta(days=10 + days_updated_ago)).isoformat(),
        "updated": updated.isoformat(),
        "labels": labels or [],
        "components": [{"name": "backend"}],
        "customfield_10014": epic,
        "customfield_10016": story_points,
        "customfield_10020": [scope_sprint] if scope_sprint else None,
        "customfield_10019": f"0|i{key[-3:]}:",
        "subtasks": [],
    }
    return {
        "key": key,
        "fields": fields,
        "_comments": comments or [],
        "_changelog": changelog or [],
    }


def load_mock_payload(project: str = "DEMO") -> dict[str, list[dict[str, Any]]]:
    now = now_tz()
    active_sprint = {
        "id": 1001,
        "name": "Sprint 42",
        "state": "active",
        "startDate": (now - timedelta(days=5)).isoformat(),
        "endDate": (now + timedelta(days=5)).isoformat(),
    }
    future_sprint = {
        "id": 1002,
        "name": "Sprint 43",
        "state": "future",
        "startDate": (now + timedelta(days=6)).isoformat(),
        "endDate": (now + timedelta(days=16)).isoformat(),
    }

    current = [
        _issue(
            f"{project}-101",
            "High priority stuck in progress",
            status="In Progress",
            category="In Progress",
            priority="High",
            days_updated_ago=4,
            scope_sprint=active_sprint,
            labels=["product", "onboarding"],
        ),
        _issue(
            f"{project}-102",
            "QA task waiting too long",
            status="QA",
            category="In Progress",
            priority="Medium",
            days_updated_ago=3,
            scope_sprint=active_sprint,
            labels=["tech", "backend"],
        ),
        _issue(
            f"{project}-103",
            "Still todo after sprint start",
            status="To Do",
            category="To Do",
            priority="High",
            days_updated_ago=5,
            scope_sprint=active_sprint,
            labels=["product"],
            comments=[
                {
                    "author": {"displayName": "QA"},
                    "body": "Do we have requirements?",
                    "created": (now - timedelta(days=3)).isoformat(),
                    "updated": (now - timedelta(days=3)).isoformat(),
                }
            ],
        ),
    ]
    next_sprint = [
        _issue(
            f"{project}-201",
            "Next sprint issue without AC",
            status="To Do",
            category="To Do",
            priority="High",
            days_updated_ago=1,
            scope_sprint=future_sprint,
            labels=["product"],
            description="Make it better",
            epic=None,
        ),
        _issue(
            f"{project}-202",
            "Tech cleanup with missing labels",
            status="To Do",
            category="To Do",
            priority="Medium",
            days_updated_ago=1,
            scope_sprint=future_sprint,
            labels=[],
            description="",
            epic="TWIN-EPIC-2",
        ),
    ]
    backlog = [
        _issue(
            f"{project}-301",
            "Old stale backlog candidate",
            status="To Do",
            category="To Do",
            priority="Low",
            days_updated_ago=75,
            labels=[],
            description="",
            epic=None,
            assignee=None,
        ),
        _issue(
            f"{project}-302",
            "High priority stale backlog",
            status="To Do",
            category="To Do",
            priority="High",
            days_updated_ago=20,
            labels=["product"],
            epic="TWIN-EPIC-1",
        ),
        _issue(
            f"{project}-303",
            "Returned from sprint to backlog",
            status="To Do",
            category="To Do",
            priority="Medium",
            days_updated_ago=1,
            labels=["tech"],
            changelog=[
                {
                    "author": {"displayName": "PM"},
                    "created": (now - timedelta(hours=10)).isoformat(),
                    "items": [{"field": "Sprint", "fromString": "Sprint 42", "toString": None}],
                }
            ],
        ),
    ]
    updated = deepcopy(current[:2] + next_sprint[:1] + backlog[2:])
    updated.append(
        _issue(
            f"{project}-401",
            "New issue since yesterday",
            status="To Do",
            category="To Do",
            priority="Medium",
            days_updated_ago=0,
            labels=["product"],
            changelog=[
                {
                    "author": {"displayName": "PM"},
                    "created": (now - timedelta(hours=3)).isoformat(),
                    "items": [{"field": "created", "fromString": None, "toString": "created"}],
                }
            ],
        )
    )
    return {
        "current_sprint": current,
        "next_sprint": next_sprint,
        "backlog": backlog,
        "updated_since": updated,
    }
