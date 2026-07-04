from events import Event, RuntimeEvent, event_from_name, utc_now


def normalize_event(event, payload=None, execution_id="", task_id="", timestamp=None, event_id=None):
    if isinstance(event, RuntimeEvent):
        return event
    if isinstance(event, dict):
        return RuntimeEvent.from_mapping(event)
    if isinstance(event, str):
        return event_from_name(
            event,
            payload=payload or {},
            execution_id=execution_id or "",
            task_id=task_id or "",
            timestamp=timestamp,
            event_id=event_id,
        )
    raise TypeError(f"unsupported event type: {type(event)!r}")


class EventBus:
    def __init__(self, keep_history=True):
        self.keep_history = keep_history
        self.handlers = {}
        self.history = []
        self.handler_errors = []

    def subscribe(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def emit(self, event, payload=None, execution_id="", task_id="", timestamp=None, event_id=None):
        event = normalize_event(
            event,
            payload=payload,
            execution_id=execution_id,
            task_id=task_id,
            timestamp=timestamp,
            event_id=event_id,
        )
        if self.keep_history:
            self.history.append(event)
        for handler in list(self.handlers.get(event.event_type, [])) + list(self.handlers.get("*", [])):
            try:
                handler(event)
            except Exception as exc:
                self.handler_errors.append({
                    "event_type": event.event_type,
                    "error": str(exc),
                    "timestamp": utc_now(),
                })
        return event
