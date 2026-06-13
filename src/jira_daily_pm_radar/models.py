from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Scope(StrEnum):
    CURRENT_SPRINT = "current_sprint"
    NEXT_SPRINT = "next_sprint"
    BACKLOG = "backlog"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SprintInfo(BaseModel):
    id: int | None = None
    name: str | None = None
    state: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class Comment(BaseModel):
    author: str | None = None
    body: str
    created: datetime | None = None
    updated: datetime | None = None


class ChangeItem(BaseModel):
    field: str
    from_value: str | None = None
    to_value: str | None = None


class ChangeLogEntry(BaseModel):
    author: str | None = None
    created: datetime
    items: list[ChangeItem]


class Issue(BaseModel):
    key: str
    summary: str = ""
    description: str | None = None
    status: str | None = None
    status_category: str | None = None
    resolution: str | None = None
    priority: str | None = None
    issue_type: str | None = None
    assignee: str | None = None
    reporter: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    sprint: SprintInfo | None = None
    scope: Scope = Scope.UNKNOWN
    rank: str | None = None
    epic: str | None = None
    parent: str | None = None
    story_points: float | None = None
    subtasks: list[str] = Field(default_factory=list)
    url: str | None = None
    comments: list[Comment] = Field(default_factory=list)
    changelog: list[ChangeLogEntry] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def description_length(self) -> int:
        return len((self.description or "").strip())

    @property
    def lower_labels(self) -> set[str]:
        return {label.lower() for label in self.labels}

    @property
    def is_done(self) -> bool:
        return (self.status_category or "").lower() == "done"

    @property
    def is_high_priority(self) -> bool:
        return (self.priority or "").lower() in {"highest", "high", "critical", "blocker"}


class Signal(BaseModel):
    id: str
    severity: Severity
    scope: Scope
    issue_key: str | None = None
    title: str
    reason: str
    recommended_action: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ActionItem(BaseModel):
    priority: Literal["P1", "P2", "P3"]
    title: str
    issue_keys: list[str] = Field(default_factory=list)
    reason: str


class ReportData(BaseModel):
    project: str
    generated_at: datetime
    since: str
    signals: list[Signal]
    actions: list[ActionItem]
    current_sprint: list[Issue]
    next_sprint: list[Issue]
    backlog: list[Issue]
    limitations: list[str] = Field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for signal in self.signals if signal.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for signal in self.signals if signal.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for signal in self.signals if signal.severity == Severity.INFO)
