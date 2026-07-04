# Event Bus

`event_bus.py` provides an in-memory event bus with safe handler execution.
Handlers can subscribe to a specific event type or `*`. Handler errors are
recorded and do not interrupt the harness.
