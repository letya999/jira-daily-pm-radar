# Skill scripts

The real CLI entrypoint is the project command:

```bash
jira-radar daily --project TWIN --board-id 123 --since yesterday --out reports/
```

This folder is included so the skill package is self-contained and agents can discover the CLI contract.
