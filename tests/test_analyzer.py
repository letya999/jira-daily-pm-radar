from __future__ import annotations

from jira_daily_pm_radar.analyzer import RadarAnalyzer
from jira_daily_pm_radar.config import load_config
from jira_daily_pm_radar.mock_data import load_mock_payload
from jira_daily_pm_radar.models import Scope
from jira_daily_pm_radar.normalizer import normalize_issue


def test_mock_analyzer_produces_signals() -> None:
    config = load_config()
    payload = load_mock_payload("DEMO")
    current = [
        normalize_issue(raw, scope=Scope.CURRENT_SPRINT, fields_map=config.fields)
        for raw in payload["current_sprint"]
    ]
    next_sprint = [
        normalize_issue(raw, scope=Scope.NEXT_SPRINT, fields_map=config.fields)
        for raw in payload["next_sprint"]
    ]
    backlog = [
        normalize_issue(raw, scope=Scope.BACKLOG, fields_map=config.fields)
        for raw in payload["backlog"]
    ]
    updated = [normalize_issue(raw, fields_map=config.fields) for raw in payload["updated_since"]]

    report = RadarAnalyzer(config).analyze(
        project="DEMO",
        since="yesterday",
        current_sprint=current,
        next_sprint=next_sprint,
        backlog=backlog,
        updated_since=updated,
    )

    ids = {signal.id for signal in report.signals}
    assert "stuck_in_status" in ids
    assert "missing_description" in ids
    assert "stale_backlog_60_days" in ids
    assert report.actions
