from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Event:
    event_type: str
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)


class EventBus:
    def __init__(self, keep_history=True):
        self.keep_history = keep_history
        self.handlers = {}
        self.history = []
        self.handler_errors = []

    def subscribe(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def emit(self, event):
        if isinstance(event, str):
            event = Event(event)
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
