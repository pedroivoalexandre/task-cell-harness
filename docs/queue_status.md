# Queue Status Inspection

`python3 runner.py status` prints the current task queue without executing a task.
The command is read-only: it does not create directories, write logs, move task files,
change task status, increment attempts, or call external agents.

## States

The status output groups tasks in this order:

1. `pending`
2. `running`
3. `review`
4. `needs_revision`
5. `failed`
6. `done`

For each task, the output shows:

- `id`
- `title`
- `priority`
- `status`
- `revision_count`
- `attempt_count`
- `max_attempts`
- `created_at`
- `last_requeued_at`, when present

## Pending Order

`pending` tasks use the same deterministic order as `scheduler.py`:

1. priority
2. queue timestamp
3. `revision_count`
4. `id`

The queue timestamp is `created_at` for new tasks. Requeued tasks with
`revision_count > 0` use `last_requeued_at` when present.

## Next Task

The final section identifies the next pending task candidate and prints its
order basis:

```text
Next task:
- id: example_task_contract
- title: Example task contract
- priority: normal
- attempts: 0/3
- reason/order basis: priority=normal, queue_timestamp=2026-07-02T00:00:00+00:00, revision_count=0, id=example_task_contract
```

If there are no pending tasks, the final section is:

```text
Next task:
- none
```
