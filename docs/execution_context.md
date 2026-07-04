# Execution Context

`execution_context.py` defines the shared execution metadata used during one
runner execution. It keeps execution simulated and does not introduce any real
agent subprocess calls.

## Fields

`ExecutionContext` contains:

- `execution_id`: unique UUID generated for each execution
- `task_id`
- `task_title`
- `task_status`
- `executor_name`
- `executor_role`
- `started_at`
- `updated_at`
- `attempt_count`
- `revision_count`
- `log_context`
- `review_context`

## Propagation

The runner creates an `ExecutionContext` after selecting and loading a pending
task. It then propagates the same object through:

- scheduler-derived task metadata
- state-machine transition logging
- executor registry resolution
- mock executor execution
- simulated review metadata

The state machine API remains unchanged. The runner passes a context-aware log
callback into `transition_task`, so transition records include the same
`execution_id` without changing state semantics.

## Logs

When a context is available, runner logs include:

- top-level `execution_id`
- `details.execution_id`
- `details.execution_context`

`details.execution_context` contains a compact log snapshot with task, executor,
attempt, and revision metadata. Existing logs that happen outside a task
execution, such as `no_pending_task`, remain compatible and may not include an
execution ID.
