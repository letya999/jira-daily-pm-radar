# Daily PM Radar: DEMO

Generated: 2026-06-13T03:02:05.194127+05:00
Signals: critical=5, warning=10, info=6

## Главное
- [warning] Issue DEMO-303 returned from sprint to backlog `DEMO-303`: Sprint field was removed in changelog.
- [info] New issue DEMO-401 `DEMO-401`: Issue appeared in Jira changes since selected period.
- [critical] DEMO-101 may be stuck in In Progress `DEMO-101`: Issue stayed in status for 4 days, threshold is 3.
- [critical] High priority DEMO-101 has no recent activity `DEMO-101`: Updated 4 days ago.
- [warning] DEMO-102 may be stuck in QA `DEMO-102`: Issue stayed in status for 3 days, threshold is 2.
- [critical] DEMO-103 may be stuck in To Do `DEMO-103`: Issue stayed in status for 5 days, threshold is 2.
- [warning] DEMO-103 is still To Do after sprint start `DEMO-103`: Sprint started 5 days ago.
- [critical] High priority DEMO-103 has no recent activity `DEMO-103`: Updated 5 days ago.
- [info] DEMO-201 has weak description `DEMO-201`: Description length is 14, minimum is 50.
- [warning] DEMO-201 has no visible acceptance criteria `DEMO-201`: No configured acceptance criteria markers found in description.
- [warning] DEMO-201 has no epic/parent `DEMO-201`: Issue type Task requires epic/parent by configuration.
- [warning] DEMO-202 has no description `DEMO-202`: Description is empty.

## Что сделать сегодня
1. P1: Ask current owner for real state and move/update the issue if needed. (DEMO-101, DEMO-102, DEMO-103)
2. P1: Raise on daily and clarify blocker/next action. (DEMO-101, DEMO-103)
3. P2: Attach to epic/parent or explicitly mark as standalone. (DEMO-201, DEMO-301)
4. P2: Add problem, expected result, and acceptance criteria. (DEMO-202, DEMO-301)
5. P3: Add domain/work type labels if they are used in the team. (DEMO-202, DEMO-301)
6. P3: Add tech/product classification or update label policy. (DEMO-202, DEMO-301)
7. P1: Ask why it returned and whether scope/priority changed. (DEMO-303)
8. P3: Triage the new issue and decide whether it belongs to sprint, next sprint, or backlog. (DEMO-401)
9. P3: Check if this item is really planned for the sprint. (DEMO-103)
10. P3: Clarify problem, scope, and expected result. (DEMO-201)
11. P2: Add acceptance criteria or expected result before planning. (DEMO-201)
12. P2: Close, park, reprioritize, or refresh the issue. (DEMO-301)

## Ограничения
- Possible unanswered comments are heuristic signals, not proof.
- Rank/priority order depends on Jira board ordering and available Rank field.
- Returned-from-sprint detection is best with changelog plus daily snapshots.
