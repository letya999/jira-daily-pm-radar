from __future__ import annotations

from pathlib import Path

from jira_daily_pm_radar.analyzer import RadarAnalyzer
from jira_daily_pm_radar.config import load_config
from jira_daily_pm_radar.mock_data import load_mock_payload
from jira_daily_pm_radar.models import Scope
from jira_daily_pm_radar.normalizer import normalize_issue
from jira_daily_pm_radar.report import write_report


def test_write_report(tmp_path: Path) -> None:
    config = load_config()
    payload = load_mock_payload("DEMO")
    report = RadarAnalyzer(config).analyze(
        project="DEMO",
        since="yesterday",
        current_sprint=[
            normalize_issue(raw, scope=Scope.CURRENT_SPRINT, fields_map=config.fields)
            for raw in payload["current_sprint"]
        ],
        next_sprint=[
            normalize_issue(raw, scope=Scope.NEXT_SPRINT, fields_map=config.fields)
            for raw in payload["next_sprint"]
        ],
        backlog=[
            normalize_issue(raw, scope=Scope.BACKLOG, fields_map=config.fields)
            for raw in payload["backlog"]
        ],
        updated_since=[
            normalize_issue(raw, fields_map=config.fields) for raw in payload["updated_since"]
        ],
    )

    html = write_report(report, tmp_path)

    assert html.exists()
    assert (html.parent / "summary.md").exists()
    assert (html.parent / "signals.json").exists()
