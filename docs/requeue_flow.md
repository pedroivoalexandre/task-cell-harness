# Task Requeue Flow

Tasks in `needs_revision` can be returned to `pending` with the runner requeue
option:

```text
python3 runner.py --requeue <task_id> --reason "<reason>"
```

This performs the state transition:

```text
needs_revision -> pending
```

No Gemini or Codex subprocess is executed.

## task.json updates

Before the task is moved, the runner updates `task.json` with:

- `revision_count`: incremented by one.
- `last_revision_reason`: the supplied requeue reason.
- `last_requeued_at`: UTC timestamp for the requeue.
- `revision_history`: appended with reason, timestamp, source path, and state
  movement.

The state machine then updates:

- `status`: `pending`
- `updated_at`: UTC timestamp for the state transition.

## Logs

The requeue flow writes JSONL events through the standard runner logger:

- `task_requeue_started`
- `task_state_transition`
- `task_requeued`

If the task cannot be requeued, the runner writes:

- `task_requeue_failed`

Invalid transitions, such as `done -> pending`, remain blocked by the state
machine.

## Report

The task report at `reports/<task_id>.md` receives a `Requeue` section with the
revision count, reason, source, destination, and requeue timestamp.
