# Data Model

The analyzer normalizes Jira into one issue model.

Important fields:

- `key`
- `summary`
- `description`
- `status`
- `status_category`
- `resolution`
- `priority`
- `issue_type`
- `assignee`
- `created`
- `updated`
- `labels`
- `components`
- `sprint`
- `scope`: current_sprint / next_sprint / backlog / unknown
- `rank`
- `epic`
- `parent`
- `story_points`
- `subtasks`
- `comments`
- `changelog`

Every signal must include evidence.
