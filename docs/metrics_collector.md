# Metrics Collector

`metrics_collector.py` consumes typed runtime events from the `EventBus` and writes `reports/metrics.json`.

## Behavior

- Updates counters from event payloads, not from log record shape.
- Tracks task selection, executor successes/failures, terminal outcomes, attempts, and requeues.
- Remains best-effort and never interrupts execution.
- Accepts legacy event payloads for compatibility, but the primary contract is typed events.
