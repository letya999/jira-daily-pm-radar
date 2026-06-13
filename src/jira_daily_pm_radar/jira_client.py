from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

import httpx

from jira_daily_pm_radar.config import Settings


class JiraConfigError(RuntimeError):
    pass


class JiraClient:
    def __init__(self, settings: Settings, timeout: float = 30.0) -> None:
        if not settings.jira_base_url:
            raise JiraConfigError("JIRA_BASE_URL is not configured")
        self.settings = settings
        self.base_url = settings.jira_base_url.rstrip("/")
        headers = {"Accept": "application/json"}
        auth: tuple[str, str] | None = None
        if settings.jira_bearer_token:
            headers["Authorization"] = f"Bearer {settings.jira_bearer_token}"
        elif settings.jira_email and settings.jira_api_token:
            auth = (settings.jira_email, settings.jira_api_token)
        else:
            raise JiraConfigError(
                "Configure JIRA_EMAIL + JIRA_API_TOKEN or JIRA_BEARER_TOKEN in .env"
            )
        self.client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, auth=auth, timeout=timeout
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> JiraClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected Jira response for {url}")
        return data

    async def _post(self, url: str, json: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.post(url, json=json)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected Jira response for {url}")
        return data

    async def search_issues(
        self,
        jql: str,
        *,
        fields: Iterable[str] | None = None,
        max_results: int = 100,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        start_at = 0
        field_list = list(fields or [])
        while True:
            payload: dict[str, Any] = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": min(max_results, 100),
                "fields": field_list,
            }
            if expand:
                payload["expand"] = [expand]
            data = await self._post("/rest/api/3/search", json=payload)
            batch = data.get("issues", [])
            if not isinstance(batch, list):
                break
            issues.extend(batch)
            if len(issues) >= max_results:
                return issues[:max_results]
            total = int(data.get("total", len(issues)))
            start_at += len(batch)
            if not batch or start_at >= total:
                return issues
        return issues

    async def get_issue(self, issue_key: str, *, expand: str | None = None) -> dict[str, Any]:
        params = {"expand": expand} if expand else None
        return await self._get(f"/rest/api/3/issue/{issue_key}", params=params)

    async def get_comments(self, issue_key: str, max_results: int = 100) -> list[dict[str, Any]]:
        data = await self._get(
            f"/rest/api/3/issue/{issue_key}/comment",
            params={"maxResults": max_results, "orderBy": "created"},
        )
        comments = data.get("comments", [])
        return comments if isinstance(comments, list) else []

    async def get_changelog(self, issue_key: str, max_results: int = 100) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        start_at = 0
        while True:
            data = await self._get(
                f"/rest/api/3/issue/{issue_key}/changelog",
                params={"startAt": start_at, "maxResults": min(max_results, 100)},
            )
            batch = data.get("values", [])
            if not isinstance(batch, list):
                break
            values.extend(batch)
            total = int(data.get("total", len(values)))
            start_at += len(batch)
            if len(values) >= max_results or not batch or start_at >= total:
                return values[:max_results]
        return values

    async def enrich_with_comments_and_changelog(
        self, issues: list[dict[str, Any]], *, max_concurrency: int = 8
    ) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def enrich(issue: dict[str, Any]) -> dict[str, Any]:
            key = str(issue.get("key"))
            async with semaphore:
                results = await asyncio.gather(
                    self.get_comments(key), self.get_changelog(key), return_exceptions=True
                )
            comments_result, changelog_result = results
            issue = dict(issue)
            issue["_comments"] = comments_result if isinstance(comments_result, list) else []
            issue["_changelog"] = changelog_result if isinstance(changelog_result, list) else []
            return issue

        return await asyncio.gather(*(enrich(issue) for issue in issues))

    async def get_board_sprints(self, board_id: int, state: str) -> list[dict[str, Any]]:
        data = await self._get(f"/rest/agile/1.0/board/{board_id}/sprint", params={"state": state})
        values = data.get("values", [])
        return values if isinstance(values, list) else []
