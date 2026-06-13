---
name: jira-daily-pm-radar
description: Use this skill when the user wants to understand what changed in Jira since yesterday, where the current sprint is stuck, what backlog items smell, what issues are poorly described, what needs grooming, or needs a daily PM Jira report with HTML output.
---

# Jira Daily PM Radar

This skill answers daily PM questions:

1. What changed since yesterday?
2. Where is the current sprint stuck?
3. Who may have forgotten to move/update issues?
4. What in the next sprint is not ready?
5. What in the backlog smells?
6. What should the PM do today?

## Prerequisites

Only `uv` is required. Install it once:
- Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

Verify: `uv --version`

## Running CLI

Run directly via uvx - no clone needed:

```bash
# Daily report (mock mode, no real Jira needed)
uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git \
  jira-radar daily --project DEMO --mock --out reports/

# Daily report (real Jira)
uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git \
  jira-radar daily --project PROJ --board-id 123 --since yesterday --out reports/

# Check connectivity
uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git \
  jira-radar doctor
```

Environment variables (set before calling or pass via shell):
- `JIRA_BASE_URL` - https://your-domain.atlassian.net
- `JIRA_EMAIL` - your Atlassian email
- `JIRA_API_TOKEN` - your Jira API token

## MCP client config

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
        "JIRA_BASE_URL": "<YOUR_JIRA_URL>",
        "JIRA_EMAIL": "<YOUR_JIRA_EMAIL>",
        "JIRA_API_TOKEN": "<YOUR_JIRA_API_TOKEN>"
      }
    }
  }
}
```

First run downloads and caches the package. Subsequent runs use the cache.

## Installing this skill

```bash
npx skills add -g letya999/jira-daily-pm-radar
```

After install, ensure `uv` is available (see Prerequisites). No other setup required.

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

Use CLI via uvx for batch reports:

```bash
uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git \
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

The summary already contains markdown links with task names and Jira URLs. Preserve them.

Then add a brief natural-language lead-in in the same language the PM used, for example:

> «Проверил Jira по PROJECT. Вот что нашёл:»

Highlight to the PM explicitly:
- any CRITICAL signals (high-priority issues with no activity, high-priority stale backlog)
- tasks stuck in status longer than threshold
- issues that returned from sprint to backlog
- new tasks that arrived since yesterday
- possible unanswered comments

When referencing issues in your lead-in or highlights, ALWAYS use inline markdown links with the task name:
`[TWSC-123 «Task name»](https://jira.example.com/browse/TWSC-123)` — never just the issue key.

Point the PM to the HTML report for the full picture:
> «Полный отчёт: <path from summary>»

Do not invent Jira data. Do not omit limitations section.
