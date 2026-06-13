from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from jira_daily_pm_radar.analyzer import distribution
from jira_daily_pm_radar.models import ReportData, Scope, Signal
from jira_daily_pm_radar.time_utils import safe_filename_datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "skills" / "jira-daily-pm-radar" / "assets"


def model_dump_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [model_dump_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: model_dump_jsonable(item) for key, item in value.items()}
    return value


def signals_by_scope(signals: list[Signal], scope: Scope) -> list[Signal]:
    return [signal for signal in signals if signal.scope == scope]


def render_summary(report: ReportData) -> str:
    top = report.signals[:12]
    lines = [
        f"# Daily PM Radar: {report.project}",
        "",
        f"Generated: {report.generated_at.isoformat()}",
        f"Signals: critical={report.critical_count}, warning={report.warning_count}, info={report.info_count}",
        "",
        "## Главное",
    ]
    if not top:
        lines.append("- Сильных сигналов не найдено")
    for signal in top:
        issue = f" `{signal.issue_key}`" if signal.issue_key else ""
        lines.append(f"- [{signal.severity}] {signal.title}{issue}: {signal.reason}")
    lines.extend(["", "## Что сделать сегодня"])
    if not report.actions:
        lines.append("- Ничего срочного")
    for index, action in enumerate(report.actions, start=1):
        keys = ", ".join(action.issue_keys)
        suffix = f" ({keys})" if keys else ""
        lines.append(f"{index}. {action.priority}: {action.title}{suffix}")
    lines.extend(["", "## Ограничения"])
    for limitation in report.limitations:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def write_report(report: ReportData, out_dir: Path) -> Path:
    date_part = safe_filename_datetime(report.generated_at)
    run_dir = out_dir / f"{report.project}-{date_part}"
    latest_dir = out_dir / f"{report.project}-latest"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("daily-report-template.html")
    html = template.render(
        report=report,
        current_signals=signals_by_scope(report.signals, Scope.CURRENT_SPRINT),
        next_signals=signals_by_scope(report.signals, Scope.NEXT_SPRINT),
        backlog_signals=signals_by_scope(report.signals, Scope.BACKLOG),
        unknown_signals=signals_by_scope(report.signals, Scope.UNKNOWN),
        dist_issue_type={
            "current_sprint": distribution(report.current_sprint, "issue_type"),
            "next_sprint": distribution(report.next_sprint, "issue_type"),
            "backlog": distribution(report.backlog, "issue_type"),
        },
        dist_priority={
            "current_sprint": distribution(report.current_sprint, "priority"),
            "next_sprint": distribution(report.next_sprint, "priority"),
            "backlog": distribution(report.backlog, "priority"),
        },
    )
    summary = render_summary(report)
    files = {
        "report.html": html,
        "summary.md": summary,
        "signals.json": json.dumps(
            model_dump_jsonable(report.signals), ensure_ascii=False, indent=2
        ),
        "action-list.json": json.dumps(
            model_dump_jsonable(report.actions), ensure_ascii=False, indent=2
        ),
        "evidence.json": json.dumps(model_dump_jsonable(report), ensure_ascii=False, indent=2),
    }
    for name, content in files.items():
        (run_dir / name).write_text(content, encoding="utf-8")

    latest_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (latest_dir / name).write_text(content, encoding="utf-8")
    return run_dir / "report.html"
