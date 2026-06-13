# Jira Daily PM Radar

[![CI](https://github.com/letya999/jira-daily-pm-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/letya999/jira-daily-pm-radar/actions/workflows/ci.yml)
[![Status: local-only](https://img.shields.io/badge/Status-local--only-blue)](https://github.com/letya999/jira-daily-pm-radar)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ежедневный PM-радар по Jira: что изменилось со вчера, где текущий спринт завис, что в backlog уже пахнет, что плохо оформлено и что проджекту надо сделать сегодня.

Проект сделан как демонстрационный **agent skill package**: внутри есть Python 3.12 CLI, async Jira client, MCP server, Open Skill-папка, HTML-отчет, security gates и mock-режим без реальной Jira.

## Быстрый старт (без клонирования)

Если у вас установлен [uv](https://astral.sh/uv/), вы можете запустить радар мгновенно через `uvx`:

```bash
# Запуск с mock-данными (не нужна реальная Jira)
uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git \
  jira-radar daily --project DEMO --mock --out reports/
```

## Установка скилла

### Шаг 1: Регистрация в Skills CLI

Используйте [Skills CLI](https://skills.sh) для мгновенной регистрации навыка во всех AI-агентах (Claude Code, Gemini CLI, Cursor и др.):

```bash
npx skills add -g letya999/jira-daily-pm-radar
```

После этого агент будет знать, как запускать радар через `uvx`. Никакого клонирования и настройки venv вручную не требуется.

### Шаг 2: Настройка MCP клиента

Добавьте следующую конфигурацию в ваш MCP-клиент (например, `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "jira-daily-pm-radar": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/letya999/jira-daily-pm-radar.git[mcp]",
        "jira-radar-mcp"
      ],
      "env": {
        "JIRA_BASE_URL": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "you@example.com",
        "JIRA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

## Работа с реальной Jira (через CLI)

```bash
export JIRA_BASE_URL=https://your-domain.atlassian.net
export JIRA_EMAIL=you@example.com
export JIRA_API_TOKEN=your_api_token

uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git \
  jira-radar daily --project TWIN --board-id 123 --since yesterday --out reports/
```

Команды `uvx`:
- `... jira-radar doctor` - проверка связи
- `... jira-radar daily` - ежедневный отчет
- `... jira-radar sprint` - статус спринта
- `... jira-radar backlog` - аудит бэклога

## Разработка

Для локальной разработки склонируйте репозиторий и используйте `uv sync`:

```bash
git clone https://github.com/letya999/jira-daily-pm-radar.git
cd jira-daily-pm-radar
uv sync --all-extras
```

### Настройка (local-only)
**Linux / macOS:** `bash scripts/setup.sh`
**Windows:** `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`

### Запуск тестов и линтеров
```bash
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

## Skill

Skill лежит здесь: `skills/jira-daily-pm-radar/SKILL.md`.
Главная идея: агент сначала читает `SKILL.md`, затем использует `uvx` для запусков.

## Security gates

В проекте настроены:
- pre-commit (ruff, mypy, bandit, detect-secrets)
- GitHub Actions CI (lint, tests, security scan)

## License

MIT
