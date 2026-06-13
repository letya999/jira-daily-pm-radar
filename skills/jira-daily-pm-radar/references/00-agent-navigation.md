# Agent Navigation

## First decision

User asks: “что сегодня в Jira”, “что изменилось со вчера”, “проверь спринт и backlog”, “daily radar”

→ Run CLI:

```bash
jira-radar daily --project <PROJECT_KEY> --board-id <BOARD_ID> --since yesterday --out reports/
```

User asks: “где завис текущий спринт”, “кто забыл подвинуть задачи”, “что с текущим спринтом”

→ Run CLI:

```bash
jira-radar sprint --project <PROJECT_KEY> --board-id <BOARD_ID> --out reports/
```

User asks: “что в backlog пахнет”, “что причесать в backlog”, “что плохо оформлено”

→ Run CLI:

```bash
jira-radar backlog --project <PROJECT_KEY> --board-id <BOARD_ID> --out reports/
```

User asks about a specific issue:

→ Use MCP `issue_context(issue_key)` or CLI:

```bash
jira-radar issue <ISSUE_KEY>
```

## Read order after CLI

1. `summary.md` — human summary
2. `action-list.json` — PM actions
3. `signals.json` — all detected signals
4. `evidence.json` — full evidence if asked for details
5. `report.html` — visual artifact

## Response style

Always answer as a PM assistant:

- what changed
- what is stuck
- what smells
- what is poorly described
- what PM should do today
- where the HTML report is
- what limitations exist

Never invent Jira facts.
