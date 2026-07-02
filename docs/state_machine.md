# Task State Machine

The Task Cell Harness uses an explicit state machine to control task lifecycle
movement under `tasks/`.

## Official states

- `pending`
- `running`
- `review`
- `needs_revision`
- `done`
- `failed`

Each state maps to a directory under `tasks/<state>/`.

## Allowed transitions

| From | To |
| --- | --- |
| `pending` | `running` |
| `running` | `review` |
| `running` | `done` |
| `running` | `failed` |
| `review` | `done` |
| `review` | `needs_revision` |
| `review` | `failed` |
| `needs_revision` | `pending` |
| `failed` | `pending` |

`done` is terminal.

## Invalid transitions

Any transition not listed above is blocked by `state_machine.InvalidTransition`.
Unknown states are also rejected.

## Logging

Every successful state transition writes a JSONL event through the runner log
callback:

```json
{
  "event": "task_state_transition",
  "task_id": "example_task_contract",
  "details": {
    "from": "pending",
    "to": "running",
    "source": "tasks/pending/example_task_contract",
    "destination": "tasks/running/example_task_contract",
    "status_updated": true
  }
}
```

The runner callback writes the event to both `logs/harness.log` and
`logs/tasks/<task_id>.jsonl`.

## task.json status

When a task has a readable `task.json`, the state machine updates its `status`
field before moving the task to the destination state directory. It also writes
an `updated_at` timestamp.

Legacy JSON tasks without an explicit `status` use their directory state as the
current state and are still moved through the same transition checks.

## Simulated review flow

The runner currently uses a local simulated review step and does not call Gemini
or Codex as subprocesses.

Current successful execution flow:

```text
pending -> running -> review -> done
```

Revision flow:

```text
pending -> running -> review -> needs_revision
```

The state machine also permits returning revised work to the queue:

```text
needs_revision -> pending
```

The simulated review reads `task.json` and decides:

- `done` when `acceptance_criteria` exists and is not empty.
- `needs_revision` when the task is structurally valid but has no
  `acceptance_criteria`.
- `failed` when structural validation errors are present.

Reports include a `Review` section with the simulated decision and summary.
