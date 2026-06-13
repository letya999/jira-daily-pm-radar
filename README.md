# Jira Daily PM Radar

[![CI](https://github.com/letya999/jira-daily-pm-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/letya999/jira-daily-pm-radar/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/jira-daily-pm-radar)](https://pypi.org/project/jira-daily-pm-radar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ежедневный PM-радар по Jira: что изменилось со вчера, где текущий спринт завис, что в backlog уже пахнет, что плохо оформлено и что проджекту надо сделать сегодня.

Проект сделан как демонстрационный **agent skill package**: внутри есть Python 3.12 CLI, async Jira client, MCP server, Open Skill-папка, HTML-отчет, security gates и mock-режим без реальной Jira.

## Что проверяет MVP

- изменения со вчера: новые, отмененные, sprint → backlog, backlog → sprint, priority/status/assignee/labels/epic changes
- current sprint: зависшие задачи, To Do после старта, долго в In Progress/Review/QA, blocked без движения, scope churn
- next sprint: задачи без description, AC, epic/parent, labels, tech/product, priority
- backlog smells: stale 60+ дней, high priority без движения, задачи без владельца, без epic, без labels, без описания
- possible unanswered comments: эвристика по `?`, mention и отсутствию движения после вопроса
- HTML + markdown summary + `signals.json` + `action-list.json` + `evidence.json`

## Быстрый старт

```bash
uv sync --all-extras
cp .env.example .env
uv run jira-radar doctor
uv run jira-radar daily --project DEMO --mock --out reports/
```

Открой отчет:

```bash
start reports/DEMO-latest/report.html  # Windows
open reports/DEMO-latest/report.html   # macOS
xdg-open reports/DEMO-latest/report.html # Linux
```

## Работа с реальной Jira

Заполни `.env`:

```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your_api_token
```

Запуск:

```bash
uv run jira-radar daily --project TWIN --board-id 123 --since yesterday --out reports/
```

Команды:

```bash
uv run jira-radar doctor
uv run jira-radar daily --project TWIN --board-id 123 --since yesterday --out reports/
uv run jira-radar sprint --project TWIN --board-id 123 --out reports/
uv run jira-radar backlog --project TWIN --board-id 123 --out reports/
uv run jira-radar issue TWIN-123 --out reports/
```

## Skill

Skill лежит здесь:

```text
skills/jira-daily-pm-radar/
  SKILL.md
  references/
  config/
  assets/
  scripts/
```

Главная идея: агент сначала читает `SKILL.md`, затем запускает CLI для batch-анализа, а MCP использует для drilldown по конкретным задачам.

## CLI + MCP модель

```text
Skill = навигатор для агента
CLI = стабильный batch-анализ и HTML
MCP = интерактивный drilldown в Jira
LLM = интерпретация и PM-ответ
```

## MCP server

Установка с MCP extra:

```bash
uv sync --extra mcp
```

Запуск stdio MCP:

```bash
uv run jira-radar-mcp
```

Инструменты MCP:

- `daily_report(project, board_id?, since?, out_dir?, mock?)`
- `sprint_report(project, board_id?, out_dir?, mock?)`
- `backlog_report(project, board_id?, out_dir?, mock?)`
- `issue_context(issue_key, out_dir?, mock?)`
- `search_issues(jql, max_results?)`

## Security gates

В проекте есть:

- `.gitignore` с запретом `.env`, токенов и локальных артефактов
- `.env.example` без секретов
- pre-commit:
  - ruff format/check
  - mypy
  - bandit
  - detect-secrets
  - custom secret/env scanner
- GitHub Actions CI:
  - ruff lint
  - mypy type check
  - pytest
  - bandit security scan

Установка pre-commit:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Разработка

```bash
uv sync --all-extras
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv run bandit -r src
uv run detect-secrets scan --baseline .secrets.baseline
uv run python scripts/check_no_secrets.py
```

## Ограничения MVP

- проект read-only и не меняет Jira
- не делает velocity/capacity forecast
- не авторасставляет labels/assignee
- possible unanswered comments — эвристика, не факт
- sprint membership лучше ловится через changelog + snapshot, но кастомные Jira-поля могут требовать настройки `fields.yaml`

## License

MIT
