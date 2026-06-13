---
name: jira-daily-pm-radar
description: Use this skill when the user wants to understand what changed in Jira since yesterday, where the current sprint is stuck, what backlog items smell, what issues are poorly described, what needs grooming, or needs a daily PM Jira report with HTML output.
---

# Jira Daily PM Radar

This skill helps a project manager quickly understand Jira state every day.

It answers:

1. What changed since yesterday?
2. Where is the current sprint stuck?
3. Who may have forgotten to move/update issues?
4. What in the next sprint is not ready?
5. What in the backlog smells?
6. What should the PM do today?

## Install & Run

This skill can be executed directly via Python (`uvx`) or Node (`npx` / `bunx`). The MCP server provides access to Jira reports.

**Option 1: Using `uvx` (Recommended for Python users)**
```text
uvx jira-daily-pm-radar mcp
```

**Option 2: Using `npx` (Recommended for Node/Claude users)**
```text
npx -y jira-daily-pm-radar-mcp
```

**Option 3: Using `bunx`**
```text
bunx jira-daily-pm-radar-mcp
```

## Agent Installation

If you are an AI agent configuring this skill, use the following definition path:
```text
$skill-installer install https://github.com/letya999/jira-daily-pm-radar/tree/main/skills/jira-daily-pm-radar
```

## MCP client config

Use `skills/jira-daily-pm-radar/references/mcp_config_template.json` as a parameterized template and replace placeholders.

Common launcher configurations:
- **Command**: `npx`
- **Args**: `["-y", "jira-daily-pm-radar-mcp"]`


Credential sources (environment variables):
- `JIRA_BASE_URL`: The base URL of your Jira instance.
- `JIRA_EMAIL`: The email of the Atlassian account.
- `JIRA_API_TOKEN`: The API token for Jira.

## Recommended operator flow

1. `daily_report(...)` to generate a batch report and get the summary.
2. `sprint_report(...)` or `backlog_report(...)` for focused checks.
3. `issue_context(...)` to drill down into a specific issue's history and comments.
4. `search_issues(...)` for custom JQL queries if standard reports are insufficient.

## Exposed tools

- `daily_report(project: str, board_id: int, since: str, out_dir: str, mock: bool)`
- `sprint_report(project: str, board_id: int, out_dir: str, mock: bool)`
- `backlog_report(project: str, board_id: int, out_dir: str, mock: bool)`
- `issue_context(issue_key: str, mock: bool)`
- `search_issues(jql: str, max_results: int)`

## Agent navigation

Read `references/00-agent-navigation.md` first.

## Preferred execution

Use CLI mode for batch reports.

```bash
jira-radar daily --project <PROJECT_KEY> --board-id <BOARD_ID> --since yesterday --out reports/
```

Then read generated files in this order:

1. `reports/<run>/summary.md`
2. `reports/<run>/action-list.json`
3. `reports/<run>/signals.json`
4. `reports/<run>/evidence.json` only for drilldown

## MCP mode

Use MCP for interactive drilldown.
If CLI and MCP are both available, prefer CLI for daily/sprint/backlog reports and MCP for drilldown.

## Do not

- Do not invent Jira data.
- Do not change Jira issues.
- Do not expose tokens.
- Do not treat possible unanswered comments as proven facts.
- Do not manually calculate final metrics if CLI output is available.

## Final response

Read `summary.md` from the report directory and deliver it **as-is** to the PM — do not rephrase, do not summarize the summary.

Then add a brief natural-language lead-in in the same language the PM used, for example:

> «Проверил Jira по PROJECT. Вот что нашёл:»

Highlight to the PM explicitly:
- any CRITICAL signals (high-priority issues with no activity, high-priority stale backlog)
- tasks stuck in status longer than threshold
- issues that returned from sprint to backlog
- new tasks that arrived since yesterday
- possible unanswered comments

Point the PM to the HTML report for the full picture:
> «Полный отчёт: <path from summary>»

Do not invent Jira data. Do not omit limitations section.
