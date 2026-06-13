from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    jira_base_url: str | None = Field(default=None, alias="JIRA_BASE_URL")
    jira_email: str | None = Field(default=None, alias="JIRA_EMAIL")
    jira_api_token: str | None = Field(default=None, alias="JIRA_API_TOKEN")
    jira_bearer_token: str | None = Field(default=None, alias="JIRA_BEARER_TOKEN")
    jira_default_project: str | None = Field(default=None, alias="JIRA_DEFAULT_PROJECT")
    jira_default_board_id: int | None = Field(default=None, alias="JIRA_DEFAULT_BOARD_ID")
    jira_radar_timezone: str = Field(default="Asia/Almaty", alias="JIRA_RADAR_TIMEZONE")
    jira_radar_output_dir: str = Field(default="reports", alias="JIRA_RADAR_OUTPUT_DIR")


class RadarRules(BaseModel):
    raw: dict[str, Any]

    @property
    def stale_backlog_days(self) -> int:
        return int(self.raw.get("stale", {}).get("backlog_days", 60))

    @property
    def high_priority_stale_days(self) -> int:
        return int(self.raw.get("stale", {}).get("high_priority_days", 14))

    @property
    def min_description_length(self) -> int:
        return int(self.raw.get("description", {}).get("min_length", 50))

    @property
    def acceptance_criteria_markers(self) -> list[str]:
        markers = self.raw.get("description", {}).get("acceptance_criteria_markers", [])
        return [str(marker).lower() for marker in markers]

    @property
    def possible_unanswered_comment_days(self) -> int:
        return int(self.raw.get("comments", {}).get("possible_unanswered_question_days", 2))

    @property
    def required_work_type_labels(self) -> set[str]:
        groups = self.raw.get("labels", {}).get("required_any_groups", {})
        labels = groups.get("work_type", [])
        return {str(label).lower() for label in labels}

    @property
    def required_epic_issue_types(self) -> set[str]:
        values = self.raw.get("epic", {}).get("required_for_issue_types", [])
        return {str(value).lower() for value in values}

    @property
    def max_story_points_without_subtasks(self) -> int:
        return int(self.raw.get("decomposition", {}).get("max_story_points_without_subtasks", 8))


class StatusThresholds(BaseModel):
    raw: dict[str, Any]

    def max_days_in_status(self, status: str, default: int = 3) -> int:
        mapping = self.raw.get("current_sprint", {}).get("max_days_in_status", {})
        return int(mapping.get(status, default))

    @property
    def todo_after_sprint_started_days(self) -> int:
        return int(self.raw.get("current_sprint", {}).get("todo_after_sprint_started_days", 2))

    @property
    def default_stale_activity_days(self) -> int:
        return int(
            self.raw.get("current_sprint", {}).get("stale_activity_days", {}).get("default", 3)
        )

    @property
    def high_priority_stale_activity_days(self) -> int:
        return int(
            self.raw.get("current_sprint", {})
            .get("stale_activity_days", {})
            .get("high_priority", 2)
        )


class ConfigBundle(BaseModel):
    rules: RadarRules
    status_thresholds: StatusThresholds
    fields: dict[str, Any]
    labels: dict[str, Any]
    statuses: dict[str, Any]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_config(config_dir: Path | None = None) -> ConfigBundle:
    directory = config_dir or DEFAULT_CONFIG_DIR
    rules = load_yaml(directory / "rules.yaml")
    thresholds = load_yaml(directory / "status_thresholds.yaml")
    return ConfigBundle(
        rules=RadarRules(raw=rules),
        status_thresholds=StatusThresholds(raw=thresholds),
        fields=load_yaml(directory / "fields.yaml"),
        labels=load_yaml(directory / "labels.yaml"),
        statuses=load_yaml(directory / "statuses.yaml"),
    )
