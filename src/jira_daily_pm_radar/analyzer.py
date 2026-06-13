from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from jira_daily_pm_radar.config import ConfigBundle
from jira_daily_pm_radar.models import (
    ActionItem,
    ChangeLogEntry,
    Issue,
    ReportData,
    Scope,
    Severity,
    Signal,
)
from jira_daily_pm_radar.time_utils import days_between, now_tz

CANCELLED_WORDS = {"cancelled", "canceled", "rejected", "won't do", "wont do", "duplicate"}


class RadarAnalyzer:
    def __init__(self, config: ConfigBundle, *, timezone: str = "Asia/Almaty") -> None:
        self.config = config
        self.timezone = timezone
        self.now = now_tz(timezone)

    def analyze(
        self,
        *,
        project: str,
        since: str,
        current_sprint: list[Issue],
        next_sprint: list[Issue],
        backlog: list[Issue],
        updated_since: list[Issue],
    ) -> ReportData:
        signals: list[Signal] = []
        signals.extend(self._changes_since_yesterday(updated_since))
        signals.extend(self._current_sprint_signals(current_sprint))
        signals.extend(self._next_sprint_signals(next_sprint))
        signals.extend(self._backlog_signals(backlog))
        signals.extend(self._formatting_signals(current_sprint + next_sprint + backlog))
        signals.extend(self._possible_unanswered_comments(current_sprint + next_sprint + backlog))
        actions = self._actions_from_signals(signals)
        limitations = [
            "Possible unanswered comments are heuristic signals, not proof.",
            "Rank/priority order depends on Jira board ordering and available Rank field.",
            "Returned-from-sprint detection is best with changelog plus daily snapshots.",
        ]
        return ReportData(
            project=project,
            generated_at=self.now,
            since=since,
            signals=signals,
            actions=actions,
            current_sprint=current_sprint,
            next_sprint=next_sprint,
            backlog=backlog,
            limitations=limitations,
        )

    def _signal(
        self,
        signal_id: str,
        severity: Severity,
        scope: Scope,
        title: str,
        reason: str,
        action: str,
        issue: Issue | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Signal:
        return Signal(
            id=signal_id,
            severity=severity,
            scope=scope,
            issue_key=issue.key if issue else None,
            title=title,
            reason=reason,
            recommended_action=action,
            evidence=evidence or {},
        )

    def _last_change_for_field(self, issue: Issue, field_names: set[str]) -> ChangeLogEntry | None:
        for entry in sorted(issue.changelog, key=lambda item: item.created, reverse=True):
            if any(item.field.lower() in field_names for item in entry.items):
                return entry
        return None

    def _days_in_status(self, issue: Issue) -> int | None:
        entry = self._last_change_for_field(issue, {"status"})
        if entry:
            return days_between(entry.created, self.now)
        return days_between(issue.updated, self.now)

    def _changes_since_yesterday(self, issues: list[Issue]) -> list[Signal]:
        signals: list[Signal] = []
        for issue in issues:
            for entry in issue.changelog:
                for item in entry.items:
                    field = item.field.lower()
                    if field == "created":
                        signals.append(
                            self._signal(
                                "new_issue",
                                Severity.INFO,
                                issue.scope,
                                f"New issue {issue.key}",
                                "Issue appeared in Jira changes since selected period.",
                                "Triage the new issue and decide whether it belongs to sprint, next sprint, or backlog.",
                                issue,
                                {"created_at": entry.created.isoformat(), "summary": issue.summary},
                            )
                        )
                    if (
                        field in {"resolution", "status"}
                        and (item.to_value or "").lower() in CANCELLED_WORDS
                    ):
                        signals.append(
                            self._signal(
                                "cancelled_issue",
                                Severity.INFO,
                                issue.scope,
                                f"Issue {issue.key} was cancelled/rejected/duplicated",
                                f"{item.field} changed to {item.to_value}.",
                                "Check whether dependent tasks or sprint scope should be updated.",
                                issue,
                                {
                                    "field": item.field,
                                    "to": item.to_value,
                                    "at": entry.created.isoformat(),
                                },
                            )
                        )
                    if field == "sprint":
                        from_sprint = bool(item.from_value)
                        to_sprint = bool(item.to_value)
                        if from_sprint and not to_sprint:
                            signals.append(
                                self._signal(
                                    "sprint_to_backlog",
                                    Severity.WARNING,
                                    Scope.BACKLOG,
                                    f"Issue {issue.key} returned from sprint to backlog",
                                    "Sprint field was removed in changelog.",
                                    "Ask why it returned and whether scope/priority changed.",
                                    issue,
                                    {
                                        "from": item.from_value,
                                        "to": item.to_value,
                                        "at": entry.created.isoformat(),
                                    },
                                )
                            )
                        elif not from_sprint and to_sprint:
                            signals.append(
                                self._signal(
                                    "backlog_to_sprint",
                                    Severity.INFO,
                                    issue.scope,
                                    f"Issue {issue.key} moved from backlog to sprint",
                                    "Sprint field was added in changelog.",
                                    "Check if the issue is ready and properly described.",
                                    issue,
                                    {
                                        "from": item.from_value,
                                        "to": item.to_value,
                                        "at": entry.created.isoformat(),
                                    },
                                )
                            )
                    if field in {"priority", "assignee", "labels", "epic link", "parent"}:
                        signals.append(
                            self._signal(
                                f"{field.replace(' ', '_')}_changed",
                                Severity.INFO,
                                issue.scope,
                                f"{issue.key}: {item.field} changed",
                                f"{item.field} changed from {item.from_value} to {item.to_value}.",
                                "Review whether the change affects PM priorities or grooming actions.",
                                issue,
                                {
                                    "field": item.field,
                                    "from": item.from_value,
                                    "to": item.to_value,
                                    "at": entry.created.isoformat(),
                                },
                            )
                        )
        return signals

    def _current_sprint_signals(self, issues: list[Issue]) -> list[Signal]:
        signals: list[Signal] = []
        for issue in issues:
            if issue.is_done:
                continue
            days_status = self._days_in_status(issue)
            threshold = self.config.status_thresholds.max_days_in_status(issue.status or "")
            if days_status is not None and days_status > threshold:
                signals.append(
                    self._signal(
                        "stuck_in_status",
                        Severity.WARNING if not issue.is_high_priority else Severity.CRITICAL,
                        Scope.CURRENT_SPRINT,
                        f"{issue.key} may be stuck in {issue.status}",
                        f"Issue stayed in status for {days_status} days, threshold is {threshold}.",
                        "Ask current owner for real state and move/update the issue if needed.",
                        issue,
                        {
                            "status": issue.status,
                            "days_in_status": days_status,
                            "threshold": threshold,
                            "assignee": issue.assignee,
                        },
                    )
                )
            if (
                (issue.status or "").lower() in {"to do", "todo", "open"}
                and issue.sprint
                and issue.sprint.start_date
            ):
                days_after_start = days_between(issue.sprint.start_date, self.now)
                if (
                    days_after_start is not None
                    and days_after_start
                    > self.config.status_thresholds.todo_after_sprint_started_days
                ):
                    signals.append(
                        self._signal(
                            "todo_after_sprint_started",
                            Severity.WARNING,
                            Scope.CURRENT_SPRINT,
                            f"{issue.key} is still To Do after sprint start",
                            f"Sprint started {days_after_start} days ago.",
                            "Check if this item is really planned for the sprint.",
                            issue,
                            {
                                "days_after_sprint_start": days_after_start,
                                "sprint": issue.sprint.name,
                            },
                        )
                    )
            if issue.is_high_priority:
                days_updated = days_between(issue.updated, self.now)
                if (
                    days_updated is not None
                    and days_updated
                    > self.config.status_thresholds.high_priority_stale_activity_days
                ):
                    signals.append(
                        self._signal(
                            "high_priority_no_recent_activity",
                            Severity.CRITICAL,
                            Scope.CURRENT_SPRINT,
                            f"High priority {issue.key} has no recent activity",
                            f"Updated {days_updated} days ago.",
                            "Raise on daily and clarify blocker/next action.",
                            issue,
                            {"updated_days_ago": days_updated, "priority": issue.priority},
                        )
                    )
        return signals

    def _next_sprint_signals(self, issues: list[Issue]) -> list[Signal]:
        signals = self._readiness_signals(issues, Scope.NEXT_SPRINT)
        signals.extend(self._priority_order_signals(issues, Scope.NEXT_SPRINT))
        return signals

    def _backlog_signals(self, issues: list[Issue]) -> list[Signal]:
        signals: list[Signal] = []
        for issue in issues:
            days_updated = days_between(issue.updated, self.now)
            if days_updated is not None and days_updated >= self.config.rules.stale_backlog_days:
                signals.append(
                    self._signal(
                        "stale_backlog_60_days",
                        Severity.WARNING,
                        Scope.BACKLOG,
                        f"{issue.key} is stale in backlog",
                        f"Issue was not updated for {days_updated} days.",
                        "Close, park, reprioritize, or refresh the issue.",
                        issue,
                        {"updated_days_ago": days_updated},
                    )
                )
            if (
                issue.is_high_priority
                and days_updated is not None
                and days_updated >= self.config.rules.high_priority_stale_days
            ):
                signals.append(
                    self._signal(
                        "high_priority_stale_backlog",
                        Severity.CRITICAL,
                        Scope.BACKLOG,
                        f"High priority {issue.key} is stale in backlog",
                        f"High priority issue was not updated for {days_updated} days.",
                        "Review priority or move to active planning.",
                        issue,
                        {"updated_days_ago": days_updated, "priority": issue.priority},
                    )
                )
        signals.extend(self._readiness_signals(issues, Scope.BACKLOG))
        return signals

    def _formatting_signals(self, issues: list[Issue]) -> list[Signal]:
        # Current sprint also deserves formatting checks, but with lower noise.
        return self._readiness_signals(
            [issue for issue in issues if issue.scope == Scope.CURRENT_SPRINT], Scope.CURRENT_SPRINT
        )

    def _readiness_signals(self, issues: list[Issue], scope: Scope) -> list[Signal]:
        signals: list[Signal] = []
        for issue in issues:
            if issue.description_length == 0:
                signals.append(
                    self._signal(
                        "missing_description",
                        Severity.WARNING,
                        scope,
                        f"{issue.key} has no description",
                        "Description is empty.",
                        "Add problem, expected result, and acceptance criteria.",
                        issue,
                        {"description_length": issue.description_length},
                    )
                )
            elif issue.description_length < self.config.rules.min_description_length:
                signals.append(
                    self._signal(
                        "weak_description",
                        Severity.INFO,
                        scope,
                        f"{issue.key} has weak description",
                        f"Description length is {issue.description_length}, minimum is {self.config.rules.min_description_length}.",
                        "Clarify problem, scope, and expected result.",
                        issue,
                        {"description_length": issue.description_length},
                    )
                )
            text = (issue.description or "").lower()
            if issue.description_length > 0 and not any(
                marker in text for marker in self.config.rules.acceptance_criteria_markers
            ):
                signals.append(
                    self._signal(
                        "missing_acceptance_criteria",
                        Severity.WARNING,
                        scope,
                        f"{issue.key} has no visible acceptance criteria",
                        "No configured acceptance criteria markers found in description.",
                        "Add acceptance criteria or expected result before planning.",
                        issue,
                        {"markers": self.config.rules.acceptance_criteria_markers},
                    )
                )
            issue_type = (issue.issue_type or "").lower()
            if issue_type in self.config.rules.required_epic_issue_types and not (
                issue.epic or issue.parent
            ):
                signals.append(
                    self._signal(
                        "missing_epic_or_parent",
                        Severity.WARNING,
                        scope,
                        f"{issue.key} has no epic/parent",
                        f"Issue type {issue.issue_type} requires epic/parent by configuration.",
                        "Attach to epic/parent or explicitly mark as standalone.",
                        issue,
                        {"issue_type": issue.issue_type},
                    )
                )
            if not issue.labels:
                signals.append(
                    self._signal(
                        "missing_labels",
                        Severity.INFO,
                        scope,
                        f"{issue.key} has no labels",
                        "Labels list is empty.",
                        "Add domain/work type labels if they are used in the team.",
                        issue,
                    )
                )
            required = self.config.rules.required_work_type_labels
            if required and not issue.lower_labels.intersection(required):
                signals.append(
                    self._signal(
                        "missing_tech_product_classification",
                        Severity.INFO,
                        scope,
                        f"{issue.key} has no tech/product classification",
                        f"None of required labels found: {sorted(required)}.",
                        "Add tech/product classification or update label policy.",
                        issue,
                        {"labels": issue.labels, "required_any": sorted(required)},
                    )
                )
        return signals

    def _priority_order_signals(self, issues: list[Issue], scope: Scope) -> list[Signal]:
        order = self.config.rules.raw.get("priority", {}).get("order", {})
        if not order or len(issues) < 2:
            return []
        signals: list[Signal] = []
        last_score = -1
        for index, issue in enumerate(issues):
            score = int(order.get(issue.priority, order.get("null", 99)))
            if index > 0 and score < last_score:
                signals.append(
                    self._signal(
                        "priority_order_conflict",
                        Severity.WARNING,
                        scope,
                        f"{issue.key} may be ranked below lower-priority work",
                        "Board order does not follow configured priority order.",
                        "Review rank/order before planning.",
                        issue,
                        {
                            "priority": issue.priority,
                            "priority_score": score,
                            "position": index + 1,
                        },
                    )
                )
            last_score = max(last_score, score)
        return signals

    def _possible_unanswered_comments(self, issues: list[Issue]) -> list[Signal]:
        signals: list[Signal] = []
        threshold = self.config.rules.possible_unanswered_comment_days
        for issue in issues:
            if not issue.comments:
                continue
            last_comment = max(issue.comments, key=lambda comment: comment.created or datetime.min)
            body = last_comment.body or ""
            has_question = "?" in body or "@" in body
            age = days_between(last_comment.created, self.now)
            updated_after_comment = bool(
                issue.updated and last_comment.created and issue.updated > last_comment.created
            )
            if has_question and age is not None and age >= threshold and not updated_after_comment:
                signals.append(
                    self._signal(
                        "possible_unanswered_comment",
                        Severity.WARNING,
                        issue.scope,
                        f"{issue.key} may have an unanswered question",
                        f"Last comment looks like a question/mention and is {age} days old.",
                        "Check comment thread and close the question or update the issue.",
                        issue,
                        {
                            "comment_age_days": age,
                            "last_comment": body[:240],
                            "author": last_comment.author,
                        },
                    )
                )
        return signals

    def _actions_from_signals(self, signals: list[Signal]) -> list[ActionItem]:
        grouped: dict[str, list[Signal]] = {}
        for signal in signals:
            grouped.setdefault(signal.id, []).append(signal)
        priority_map = {
            "high_priority_no_recent_activity": "P1",
            "high_priority_stale_backlog": "P1",
            "stuck_in_status": "P1",
            "sprint_to_backlog": "P1",
            "missing_description": "P2",
            "missing_acceptance_criteria": "P2",
            "missing_epic_or_parent": "P2",
            "stale_backlog_60_days": "P2",
            "possible_unanswered_comment": "P2",
        }
        actions: list[ActionItem] = []
        for signal_id, items in sorted(
            grouped.items(), key=lambda pair: len(pair[1]), reverse=True
        ):
            top = items[:8]
            issue_keys = [item.issue_key for item in top if item.issue_key]
            first = top[0]
            priority = priority_map.get(signal_id, "P3")
            actions.append(
                ActionItem(
                    priority=priority,  # type: ignore[arg-type]
                    title=first.recommended_action,
                    issue_keys=issue_keys,
                    reason=f"{len(items)} signal(s): {first.title}",
                )
            )
        return actions[:12]


def distribution(issues: list[Issue], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for issue in issues:
        value = getattr(issue, field, None) or "<empty>"
        counter[str(value)] += 1
    return dict(counter.most_common())
