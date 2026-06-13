from __future__ import annotations

from jira_daily_pm_radar.mock_data import load_mock_payload
from jira_daily_pm_radar.models import Scope
from jira_daily_pm_radar.normalizer import normalize_issue


def test_normalize_mock_issue() -> None:
    raw = load_mock_payload("DEMO")["current_sprint"][0]
    issue = normalize_issue(raw, scope=Scope.CURRENT_SPRINT)

    assert issue.key == "DEMO-101"
    assert issue.scope == Scope.CURRENT_SPRINT
    assert issue.priority == "High"
    assert issue.description_length > 0
