# Deterministic Task Scheduler

The runner uses `scheduler.py` to select the next task from `tasks/pending/`.
Execution remains simulated and does not call Gemini or Codex as subprocesses.

## Selection order

Candidates are sorted by this deterministic key:

1. `priority`
2. queue timestamp
3. `revision_count`
4. `id`

Priority order:

1. `urgent`
2. `high`
3. `normal`
4. `low`

Unknown or empty priorities are treated as `normal`.

## Queue timestamp

New tasks use `created_at` as their queue timestamp.

Requeued tasks with `revision_count > 0` use `last_requeued_at` when present.
This prevents old requeued tasks from permanently blocking newer work at the
same priority.

Invalid or missing timestamps sort last within the same priority.

## Attempts

When the scheduler selects a task for execution, the runner increments:

- `attempt_count`

If the task has no `max_attempts`, the runner writes the default:

- `max_attempts: 3`

If `attempt_count >= max_attempts` before selection is moved to `running`, the
runner:

1. Logs `task_max_attempts_exceeded`.
2. Generates a failure report with a `Scheduler` section.
3. Moves the task through the valid state path `pending -> running -> failed`.

The task is not sent to simulated review in this case.

## Logs

Scheduler-related runner events include:

- `task_selected`
- `task_attempt_incremented`
- `task_max_attempts_exceeded`

State movement continues to be logged by the state machine as
`task_state_transition`.
