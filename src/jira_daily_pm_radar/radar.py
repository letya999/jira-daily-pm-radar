from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from jira_daily_pm_radar.analyzer import RadarAnalyzer
from jira_daily_pm_radar.config import Settings, load_config
from jira_daily_pm_radar.jira_client import JiraClient, JiraConfigError
from jira_daily_pm_radar.mock_data import load_mock_payload
from jira_daily_pm_radar.models import Issue, ReportData, Scope
from jira_daily_pm_radar.normalizer import normalize_issue

_SINCE_MAP = {
    "yesterday": "-1d",
    "today": "-0d",
    "week": "-7d",
    "last week": "-7d",
    "month": "-30d",
    "last month": "-30d",
}


def _since_to_jql(since: str) -> str:
    normalized = since.strip().lower()
    if normalized in _SINCE_MAP:
        return _SINCE_MAP[normalized]
    # pass through Jira-native relative values like -2d, -14d
    if re.match(r"^-?\d+[dwhm]$", normalized):
        return normalized
    # pass through date strings like 2024-01-01
    if re.match(r"^\d{4}-\d{2}-\d{2}$", normalized):
        return f'"{since}"'
    return "-1d"


DEFAULT_FIELDS = [
    "summary",
    "description",
    "status",
    "resolution",
    "priority",
    "issuetype",
    "assignee",
    "reporter",
    "created",
    "updated",
    "labels",
    "components",
    "parent",
    "subtasks",
    "customfield_10014",
    "customfield_10016",
    "customfield_10019",
    "customfield_10020",
]


class RadarService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.config = load_config()

    async def doctor(self) -> dict[str, str | bool]:
        checks: dict[str, str | bool] = {
            "python_project": True,
            "jira_base_url_configured": bool(self.settings.jira_base_url),
            "jira_auth_configured": bool(
                self.settings.jira_bearer_token
                or (self.settings.jira_email and self.settings.jira_api_token)
            ),
        }
        if self.settings.jira_base_url and checks["jira_auth_configured"]:
            try:
                async with JiraClient(self.settings) as client:
                    await client._get("/rest/api/3/myself")
                checks["jira_connection"] = True
            except Exception as exc:  # pragma: no cover - depends on external Jira
                checks["jira_connection"] = f"failed: {exc.__class__.__name__}: {exc}"
        else:
            checks["jira_connection"] = "skipped: configure Jira env first"
        return checks

    async def daily(
        self,
        *,
        project: str,
        board_id: int | None,
        since: str,
        out_dir: Path,
        mock: bool = False,
    ) -> ReportData:
        payload = (
            load_mock_payload(project)
            if mock
            else await self._fetch_jira_payload(project, board_id, since)
        )
        current = self._normalize_many(payload["current_sprint"], Scope.CURRENT_SPRINT)
        next_sprint = self._normalize_many(payload["next_sprint"], Scope.NEXT_SPRINT)
        backlog = self._normalize_many(payload["backlog"], Scope.BACKLOG)
        updated = self._normalize_many(payload["updated_since"], Scope.UNKNOWN)
        analyzer = RadarAnalyzer(self.config, timezone=self.settings.jira_radar_timezone)
        report = analyzer.analyze(
            project=project,
            since=since,
            current_sprint=current,
            next_sprint=next_sprint,
            backlog=backlog,
            updated_since=updated,
        )
        self._save_snapshot(project, out_dir, current + next_sprint + backlog)
        return report

    async def sprint(
        self, *, project: str, board_id: int | None, out_dir: Path, mock: bool = False
    ) -> ReportData:
        return await self.daily(
            project=project, board_id=board_id, since="yesterday", out_dir=out_dir, mock=mock
        )

    async def backlog(
        self, *, project: str, board_id: int | None, out_dir: Path, mock: bool = False
    ) -> ReportData:
        return await self.daily(
            project=project, board_id=board_id, since="yesterday", out_dir=out_dir, mock=mock
        )

    async def issue_context(self, issue_key: str, *, mock: bool = False) -> Issue:
        if mock:
            payload = load_mock_payload(issue_key.split("-")[0])
            for issues in payload.values():
                for raw in issues:
                    if raw.get("key") == issue_key:
                        return normalize_issue(raw, fields_map=self.config.fields)
            return normalize_issue(payload["current_sprint"][0], fields_map=self.config.fields)
        async with JiraClient(self.settings) as client:
            raw = await client.get_issue(issue_key, expand="renderedFields")
            enriched = (await client.enrich_with_comments_and_changelog([raw]))[0]
            return normalize_issue(
                enriched, base_url=self.settings.jira_base_url, fields_map=self.config.fields
            )

    async def search_issues(self, jql: str, *, max_results: int = 20) -> list[Issue]:
        async with JiraClient(self.settings) as client:
            raw = await client.search_issues(jql, fields=DEFAULT_FIELDS, max_results=max_results)
            return self._normalize_many(raw, Scope.UNKNOWN)

    async def _fetch_jira_payload(
        self, project: str, board_id: int | None, since: str
    ) -> dict[str, list[dict]]:
        if not self.settings.jira_base_url:
            raise JiraConfigError("Jira is not configured. Use --mock or configure .env.")
        async with JiraClient(self.settings) as client:
            jql_current = f'project = "{project}" AND sprint in openSprints() AND statusCategory != Done ORDER BY Rank ASC'
            jql_next = f'project = "{project}" AND sprint in futureSprints() AND statusCategory != Done ORDER BY Rank ASC'
            jql_backlog = f'project = "{project}" AND sprint is EMPTY AND statusCategory != Done ORDER BY Rank ASC'
            # Jira JQL supports relative forms like -1d; we keep user value if it is already valid JQL-like.
            jql_since = _since_to_jql(since)
            jql_updated = f'project = "{project}" AND updated >= {jql_since} ORDER BY updated DESC'
            current, next_sprint, backlog, updated = await asyncio.gather(
                client.search_issues(jql_current, fields=DEFAULT_FIELDS, max_results=200),
                client.search_issues(jql_next, fields=DEFAULT_FIELDS, max_results=200),
                client.search_issues(jql_backlog, fields=DEFAULT_FIELDS, max_results=500),
                client.search_issues(jql_updated, fields=DEFAULT_FIELDS, max_results=200),
            )
            updated = await client.enrich_with_comments_and_changelog(updated)
            # Enrich suspicious scopes lightly as well. For MVP we enrich all returned scope issues; tune later.
            current = await client.enrich_with_comments_and_changelog(current)
            next_sprint = await client.enrich_with_comments_and_changelog(next_sprint)
            backlog = await client.enrich_with_comments_and_changelog(backlog[:200]) + backlog[200:]
            return {
                "current_sprint": current,
                "next_sprint": next_sprint,
                "backlog": backlog,
                "updated_since": updated,
            }

    def _normalize_many(self, raws: list[dict], scope: Scope) -> list[Issue]:
        return [
            normalize_issue(
                raw,
                scope=scope,
                base_url=self.settings.jira_base_url,
                fields_map=self.config.fields,
            )
            for raw in raws
        ]

    def _save_snapshot(self, project: str, out_dir: Path, issues: list[Issue]) -> None:
        snapshot_dir = out_dir / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        data = [issue.model_dump(mode="json") for issue in issues]
        (snapshot_dir / f"{project}-latest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
