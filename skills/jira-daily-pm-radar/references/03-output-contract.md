# Output Contract

A run should produce:

```text
reports/<PROJECT>-<YYYY-MM-DD>/
  report.html
  summary.md
  signals.json
  action-list.json
  evidence.json
```

The assistant should usually read `summary.md` first and only open JSON files if more detail is needed.

Final answer format:

```text
Проверил Jira по <PROJECT> со вчера

Главное:
- ...

Что сделать сегодня:
1. ...

HTML-отчет:
<path>

Ограничения:
- ...
```
