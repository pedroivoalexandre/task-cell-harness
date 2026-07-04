# Event Bus

`event_bus.py` is the central in-memory dispatch layer for runtime events.

## Contract

- Supports legacy `Event` objects and typed runtime events.
- Preserves event history in memory when enabled.
- Dispatches to exact-type handlers and `*` wildcard handlers.
- Keeps handler failures isolated from the emitting flow.
- Writes JSONL projections through subscribed consumers, not inside the emitter.

## Typed Events

The runtime uses typed event classes for:

- `task_selected`
- `task_started`
- `task_state_transition`
- `task_completed`
- `task_failed`
- `task_needs_revision`
- `executor_started`
- `executor_completed`
- `executor_failed`
- `task_requeue_started`
- `task_requeued`
- `runtime_validation_completed`

Each event carries `event_id`, `event_type`, `timestamp`, optional `execution_id`, optional `task_id`, and a JSON-serializable `payload`.
