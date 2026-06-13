from __future__ import annotations

from pathlib import Path
from typing import Any

from jira_daily_pm_radar.config import Settings
from jira_daily_pm_radar.radar import RadarService
from jira_daily_pm_radar.report import render_summary, write_report


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        raise SystemExit("Install MCP extra first: uv sync --extra mcp") from exc

    mcp = FastMCP("jira-daily-pm-radar")

    @mcp.tool()
    async def daily_report(
        project: str,
        board_id: int | None = None,
        since: str = "yesterday",
        out_dir: str = "reports",
        mock: bool = False,
    ) -> dict[str, Any]:
        """Generate daily PM Jira radar report and return summary + report path."""
        service = RadarService(Settings())
        report = await service.daily(
            project=project,
            board_id=board_id,
            since=since,
            out_dir=Path(out_dir),
            mock=mock,
        )
        html = write_report(report, Path(out_dir))
        return {
            "summary": render_summary(report),
            "report_path": str(html),
            "signals": [signal.model_dump(mode="json") for signal in report.signals],
            "actions": [action.model_dump(mode="json") for action in report.actions],
        }

    @mcp.tool()
    async def sprint_report(
        project: str,
        board_id: int | None = None,
        out_dir: str = "reports",
        mock: bool = False,
    ) -> dict[str, Any]:
        """Generate current sprint PM radar report."""
        service = RadarService(Settings())
        report = await service.sprint(
            project=project, board_id=board_id, out_dir=Path(out_dir), mock=mock
        )
        html = write_report(report, Path(out_dir))
        return {"summary": render_summary(report), "report_path": str(html)}

    @mcp.tool()
    async def backlog_report(
        project: str,
        board_id: int | None = None,
        out_dir: str = "reports",
        mock: bool = False,
    ) -> dict[str, Any]:
        """Generate backlog grooming radar report."""
        service = RadarService(Settings())
        report = await service.backlog(
            project=project, board_id=board_id, out_dir=Path(out_dir), mock=mock
        )
        html = write_report(report, Path(out_dir))
        return {"summary": render_summary(report), "report_path": str(html)}

    @mcp.tool()
    async def issue_context(issue_key: str, mock: bool = False) -> dict[str, Any]:
        """Inspect one Jira issue with comments and changelog when available."""
        service = RadarService(Settings())
        issue = await service.issue_context(issue_key, mock=mock)
        return issue.model_dump(mode="json")

    @mcp.tool()
    async def search_issues(jql: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Run JQL search and return normalized issues."""
        service = RadarService(Settings())
        issues = await service.search_issues(jql, max_results=max_results)
        return [issue.model_dump(mode="json") for issue in issues]

    mcp.run()


if __name__ == "__main__":
    main()
