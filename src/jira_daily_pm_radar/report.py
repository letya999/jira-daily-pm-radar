from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from jira_daily_pm_radar.analyzer import distribution
from jira_daily_pm_radar.models import ReportData, Scope, Signal
from jira_daily_pm_radar.time_utils import safe_filename_datetime

TEMPLATES_DIR = Path(__file__).resolve().parent / "assets"


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


def _top_keys(signals: list[Signal], limit: int = 8) -> tuple[list[str], int]:
    keys = [s.issue_key for s in signals if s.issue_key]
    shown = keys[:limit]
    rest = len(keys) - len(shown)
    return shown, rest


def _keys_line(signals: list[Signal], limit: int = 8) -> str:
    shown, rest = _top_keys(signals, limit)
    if not shown:
        return ""
    line = ", ".join(shown)
    if rest:
        line += f" (и ещё {rest})"
    return line


def render_summary(report: ReportData) -> str:
    date_str = report.generated_at.strftime("%d.%m.%Y %H:%M")
    lines: list[str] = [
        f"# PM Радар: {report.project} — {date_str}",
        f"Signals: critical={report.critical_count}, warning={report.warning_count}, info={report.info_count}",
        "",
    ]

    # ── Текущий спринт ──────────────────────────────────────────────────────
    lines.append("## Текущий спринт")
    sprint_sigs = [s for s in report.signals if s.scope == Scope.CURRENT_SPRINT]
    stuck = [s for s in sprint_sigs if s.id in {"stuck_in_status", "todo_after_sprint_started"}]
    no_activity = [s for s in sprint_sigs if s.id == "high_priority_no_recent_activity"]
    bad_desc = [s for s in sprint_sigs if s.id in {"missing_description", "weak_description", "missing_acceptance_criteria"}]

    if stuck:
        lines.append(f"Зависшие задачи ({len(stuck)}): {_keys_line(stuck)}")
        for s in stuck[:5]:
            days = s.evidence.get("days_in_status") or s.evidence.get("days_after_sprint_start", "?")
            lines.append(f"  - {s.issue_key}: {s.evidence.get('status', '')} уже {days} дн.")
    if no_activity:
        lines.append(f"Высокий приоритет без активности ({len(no_activity)}): {_keys_line(no_activity)}")
    if bad_desc:
        lines.append(f"Плохо описанные задачи в спринте ({len(bad_desc)}): {_keys_line(bad_desc)}")
    if not sprint_sigs:
        lines.append("— Текущий спринт чист")
    lines.append("")

    # ── Следующий спринт ────────────────────────────────────────────────────
    lines.append("## Следующий спринт")
    next_sigs = [s for s in report.signals if s.scope == Scope.NEXT_SPRINT]
    not_ready = [s for s in next_sigs if s.id in {
        "missing_description", "weak_description", "missing_acceptance_criteria",
        "missing_epic_or_parent", "missing_labels",
    }]
    priority_conflict = [s for s in next_sigs if s.id == "priority_order_conflict"]

    if not_ready:
        lines.append(f"Не готово к планированию ({len(not_ready)}): {_keys_line(not_ready)}")
    if priority_conflict:
        keys = _keys_line(priority_conflict)
        lines.append(f"Конфликт приоритетов в ранге ({len(priority_conflict)}): {keys}")
    if not next_sigs:
        lines.append("— Следующий спринт чист")
    lines.append("")

    # ── Бэклог ──────────────────────────────────────────────────────────────
    lines.append("## Бэклог")
    backlog_sigs = [s for s in report.signals if s.scope == Scope.BACKLOG]
    stale = [s for s in backlog_sigs if s.id == "stale_backlog_60_days"]
    stale_hp = [s for s in backlog_sigs if s.id == "high_priority_stale_backlog"]
    backlog_no_desc = [s for s in backlog_sigs if s.id in {
        "missing_description", "weak_description", "missing_acceptance_criteria",
    }]

    if stale_hp:
        lines.append(f"КРИТИЧНО — высокоприоритетные задачи давно без движения ({len(stale_hp)}): {_keys_line(stale_hp)}")
    if stale:
        shown, rest = _top_keys(stale, 5)
        line = f"Протухло (60+ дней без обновлений): {len(stale)} задач"
        if shown:
            line += f" — например {', '.join(shown)}"
        if rest:
            line += f" и ещё {rest}"
        lines.append(line)
    if backlog_no_desc:
        lines.append(f"Без описания/критериев ({len(backlog_no_desc)}): {_keys_line(backlog_no_desc)}")
    if not backlog_sigs:
        lines.append("— Бэклог без сильных запахов")
    lines.append("")

    # ── Что изменилось ──────────────────────────────────────────────────────
    lines.append(f"## Что изменилось с {report.since}")
    change_sigs = [s for s in report.signals if s.scope == Scope.UNKNOWN]
    new_issues = [s for s in change_sigs if s.id == "new_issue"]
    to_backlog = [s for s in change_sigs if s.id == "sprint_to_backlog"]
    to_sprint = [s for s in change_sigs if s.id == "backlog_to_sprint"]
    cancelled = [s for s in change_sigs if s.id == "cancelled_issue"]
    field_changes = [s for s in change_sigs if s.id not in {
        "new_issue", "sprint_to_backlog", "backlog_to_sprint", "cancelled_issue",
    }]

    if new_issues:
        lines.append(f"Новые задачи ({len(new_issues)}):")
        for s in new_issues[:5]:
            summary = s.evidence.get("summary", "")
            lines.append(f"  - {s.issue_key}: {summary[:80]}")
        if len(new_issues) > 5:
            lines.append(f"  ... и ещё {len(new_issues) - 5}")
    if to_backlog:
        lines.append(f"Вернулись из спринта в бэклог ({len(to_backlog)}): {_keys_line(to_backlog)}")
    if to_sprint:
        lines.append(f"Переехали в спринт из бэклога ({len(to_sprint)}): {_keys_line(to_sprint)}")
    if cancelled:
        lines.append(f"Отменены/закрыты ({len(cancelled)}): {_keys_line(cancelled)}")
    if field_changes:
        lines.append(f"Изменения приоритета/ответственного/меток ({len(field_changes)}): {_keys_line(field_changes)}")
    if not change_sigs:
        lines.append("— Изменений не зафиксировано")
    lines.append("")

    # ── Возможно не отвечены ─────────────────────────────────────────────────
    unanswered = [s for s in report.signals if s.id == "possible_unanswered_comment"]
    if unanswered:
        lines.append("## Возможно не отвечены")
        for s in unanswered[:6]:
            age = s.evidence.get("comment_age_days", "?")
            excerpt = str(s.evidence.get("last_comment", ""))[:100].replace("\n", " ")
            lines.append(f"  - {s.issue_key}: комментарий {age} дн. назад — «{excerpt}»")
        if len(unanswered) > 6:
            lines.append(f"  ... и ещё {len(unanswered) - 6}")
        lines.append("")

    # ── Что сделать сегодня ──────────────────────────────────────────────────
    lines.append("## Что сделать сегодня")
    if not report.actions:
        lines.append("— Ничего срочного")
    for index, action in enumerate(report.actions, start=1):
        keys = ", ".join(action.issue_keys)
        suffix = f" ({keys})" if keys else ""
        lines.append(f"{index}. {action.priority}: {action.title}{suffix}")
    lines.append("")

    # ── Ограничения ──────────────────────────────────────────────────────────
    lines.append("## Ограничения")
    for limitation in report.limitations:
        lines.append(f"- {limitation}")
    lines.append("")

    # ── HTML-отчет (placeholder, заменяется caller'ом) ──────────────────────
    lines.append("HTML-отчет: {html_report_path}")

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
