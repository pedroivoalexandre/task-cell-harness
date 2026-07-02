# Task Contract

The official Task Cell Harness task format is a directory under `tasks/pending/` containing a `task.json` file.

Example path:

```text
tasks/pending/example_task_contract/task.json
```

## Required fields

A valid `task.json` must include these minimum fields:

- `id`: stable task identifier. It should match the task directory name.
- `title`: short human-readable task title.
- `status`: current lifecycle state, normally `pending` before execution.
- `objective`: concrete goal the harness should execute or validate.
- `created_at`: ISO 8601 timestamp for task creation.
- `priority`: scheduling hint such as `low`, `normal`, or `high`.
- `role`: intended local role for the harness, such as `harness` or `reviewer`.

## Optional fields

Tasks may include extra structured fields when useful. Common optional fields are:

- `description`: additional context.
- `acceptance_criteria`: list of expected outcomes.
- `constraints`: list of restrictions for execution.
- `metadata`: object for non-contract data.

## Compatibility

Legacy tasks stored directly as `tasks/pending/<id>.json` remain supported. The runner prefers official `task.json` tasks when any are present, then falls back to legacy JSON files.

## Invalid task handling

If an official `task.json` is missing required fields, contains empty required values, or cannot be parsed as JSON, the runner must:

1. Write a validation error log under `logs/errors/`.
2. Move the task directory to `tasks/failed/`.
3. Write a failure report under `reports/`.
4. Avoid calling any external agent process.
