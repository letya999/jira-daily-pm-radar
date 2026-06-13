from __future__ import annotations

import asyncio
import json
from collections.abc import Coroutine
from pathlib import Path
from typing import Annotated, Any, TypeVar

import typer
from rich.console import Console
from rich.table import Table

from jira_daily_pm_radar.config import Settings
from jira_daily_pm_radar.radar import RadarService
from jira_daily_pm_radar.report import render_summary, write_report

app = typer.Typer(help="Daily PM Radar for Jira")
console = Console()
T = TypeVar("T")


def run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


@app.command()
def doctor() -> None:
    """Check local config and Jira connectivity."""
    service = RadarService(Settings())
    checks = run(service.doctor())
    table = Table(title="Jira Radar Doctor")
    table.add_column("Check")
    table.add_column("Result")
    for key, value in checks.items():
        table.add_row(key, str(value))
    console.print(table)


@app.command()
def daily(
    project: Annotated[str, typer.Option("--project", "-p")],
    board_id: Annotated[int | None, typer.Option("--board-id", "-b")] = None,
    since: Annotated[str, typer.Option("--since", "-s")] = "yesterday",
    out: Annotated[Path, typer.Option("--out", "-o")] = Path("reports"),
    mock: Annotated[bool, typer.Option("--mock")] = False,
) -> None:
    """Generate daily PM radar report."""
    service = RadarService(Settings())
    report = run(
        service.daily(project=project, board_id=board_id, since=since, out_dir=out, mock=mock)
    )
    html_path = write_report(report, out)
    console.print(render_summary(report), markup=False)
    console.print(f"[green]HTML report:[/] {html_path}")


@app.command()
def sprint(
    project: Annotated[str, typer.Option("--project", "-p")],
    board_id: Annotated[int | None, typer.Option("--board-id", "-b")] = None,
    out: Annotated[Path, typer.Option("--out", "-o")] = Path("reports"),
    mock: Annotated[bool, typer.Option("--mock")] = False,
) -> None:
    """Generate current sprint radar. MVP uses the daily report and focuses on sprint signals."""
    service = RadarService(Settings())
    report = run(service.sprint(project=project, board_id=board_id, out_dir=out, mock=mock))
    html_path = write_report(report, out)
    console.print(render_summary(report), markup=False)
    console.print(f"[green]HTML report:[/] {html_path}")


@app.command()
def backlog(
    project: Annotated[str, typer.Option("--project", "-p")],
    board_id: Annotated[int | None, typer.Option("--board-id", "-b")] = None,
    out: Annotated[Path, typer.Option("--out", "-o")] = Path("reports"),
    mock: Annotated[bool, typer.Option("--mock")] = False,
) -> None:
    """Generate backlog grooming radar. MVP uses the daily report and focuses on backlog signals."""
    service = RadarService(Settings())
    report = run(service.backlog(project=project, board_id=board_id, out_dir=out, mock=mock))
    html_path = write_report(report, out)
    console.print(render_summary(report), markup=False)
    console.print(f"[green]HTML report:[/] {html_path}")


@app.command(name="issue")
def issue_cmd(
    issue_key: Annotated[str, typer.Argument(help="Jira issue key, e.g. TWIN-123")],
    mock: Annotated[bool, typer.Option("--mock")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect one issue context."""
    service = RadarService(Settings())
    issue = run(service.issue_context(issue_key, mock=mock))
    if json_output:
        console.print(json.dumps(issue.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return
    table = Table(title=f"Issue {issue.key}")
    table.add_column("Field")
    table.add_column("Value")
    for key, value in [
        ("Summary", issue.summary),
        ("Status", issue.status),
        ("Priority", issue.priority),
        ("Assignee", issue.assignee),
        ("Epic/Parent", issue.epic or issue.parent),
        ("Labels", ", ".join(issue.labels)),
        ("Updated", issue.updated.isoformat() if issue.updated else ""),
        ("Comments", str(len(issue.comments))),
        ("Changelog entries", str(len(issue.changelog))),
    ]:
        table.add_row(key, str(value or ""))
    console.print(table)


@app.command(name="search")
def search_cmd(
    jql: Annotated[str, typer.Argument(help="JQL query")],
    max_results: Annotated[int, typer.Option("--max-results", "-n")] = 20,
) -> None:
    """Run safe JQL search and print normalized issues."""
    service = RadarService(Settings())
    issues = run(service.search_issues(jql, max_results=max_results))
    for issue in issues:
        console.print(f"{issue.key}: {issue.summary} [{issue.status} / {issue.priority}]")


if __name__ == "__main__":
    app()
