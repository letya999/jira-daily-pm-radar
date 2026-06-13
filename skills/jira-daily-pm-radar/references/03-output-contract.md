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

Final answer format (sections in order):

```text
# PM Радар: <PROJECT> — <date>
Signals: critical=N, warning=N, info=N

## Текущий спринт
Зависшие задачи (N): KEY-1, KEY-2
  - KEY-1: In Progress уже 5 дн.
Высокий приоритет без активности (N): KEY-3
Плохо описанные задачи в спринте (N): KEY-4, KEY-5

## Следующий спринт
Не готово к планированию (N): KEY-6, KEY-7
Конфликт приоритетов в ранге (N): KEY-8

## Бэклог
КРИТИЧНО — высокоприоритетные задачи давно без движения (N): KEY-9
Протухло (60+ дней): 12 задач — например KEY-10, KEY-11 и ещё 7
Без описания/критериев (N): KEY-12

## Что изменилось с yesterday
Новые задачи (N):
  - KEY-13: краткое описание
Вернулись из спринта в бэклог (N): KEY-14
Переехали в спринт из бэклога (N): KEY-15
Отменены/закрыты (N): KEY-16

## Возможно не отвечены
  - KEY-17: комментарий 3 дн. назад — «вопрос...»

## Что сделать сегодня
1. P1: <действие> (KEY-1, KEY-2)
2. P2: <действие> (KEY-4)

## Ограничения
- ...

HTML-отчет: reports/PROJECT-latest/report.html
```
