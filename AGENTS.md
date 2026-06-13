# Agent Instructions

You are working in `jira-daily-pm-radar`, a Python 3.12 project built with `uv`.

## Core idea

This project is an agent skill package for daily PM Jira radar:

- CLI does deterministic batch analysis
- MCP server exposes high-level tools for agents
- Skill explains when to use CLI/MCP and how to interpret output
- Reports are read-only and evidence-based

## Do not

- Do not commit `.env`, tokens, API keys, cookies, credentials, local reports, or raw Jira dumps.
- Do not invent Jira data in tests or examples that looks like real company data.
- Do not make write operations to Jira unless a separate explicit feature is added and reviewed.
- Do not print tokens in logs.

## Required checks before final answer or commit

Run:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv run bandit -r src
uv run python scripts/check_no_secrets.py
```

## Architecture

Keep the agent-facing surface small:

- `SKILL.md` is a router, not an encyclopedia
- `references/00-agent-navigation.md` tells the agent which command/tool to use
- CLI commands are stable and few: `doctor`, `daily`, `sprint`, `backlog`, `issue`
- MCP tools are high-level wrappers, not a raw Jira dump

## Response style for generated PM summaries

Always answer:

1. what changed
2. what is stuck
3. what smells
4. what is poorly described
5. what PM should do today
6. where the HTML report is
7. what data limitations exist
