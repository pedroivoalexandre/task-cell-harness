from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def _new_event_id():
    return str(uuid4())


@dataclass
class RuntimeEvent:
    event_type: str
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)
    event_id: str = field(default_factory=_new_event_id)
    execution_id: str = ""
    task_id: str = ""

    def to_dict(self):
        return asdict(self)

    def to_record(self):
        record = {
            "timestamp": self.timestamp,
            "event": self.event_type,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "task_id": self.task_id or None,
            "details": self.payload,
            "payload": self.payload,
        }
        if self.execution_id:
            record["execution_id"] = self.execution_id
        return {key: value for key, value in record.items() if value is not None}

    @classmethod
    def from_mapping(cls, data):
        data = data or {}
        payload = data.get("payload")
        if payload is None:
            payload = data.get("details") or {}
        if not isinstance(payload, dict):
            payload = {"value": payload}
        return cls(
            event_type=data.get("event_type") or data.get("event") or "",
            payload=dict(payload),
            timestamp=data.get("timestamp") or utc_now(),
            event_id=data.get("event_id") or _new_event_id(),
            execution_id=data.get("execution_id") or "",
            task_id=data.get("task_id") or "",
        )


class Event(RuntimeEvent):
    def __init__(
        self,
        event_type,
        payload=None,
        timestamp=None,
        event_id=None,
        execution_id="",
        task_id="",
    ):
        super().__init__(
            event_type=event_type,
            payload=dict(payload or {}),
            timestamp=timestamp or utc_now(),
            event_id=event_id or _new_event_id(),
            execution_id=execution_id or "",
            task_id=task_id or "",
        )


class _TypedEvent(RuntimeEvent):
    EVENT_TYPE = ""

    def __init__(
        self,
        payload=None,
        timestamp=None,
        event_id=None,
        execution_id="",
        task_id="",
    ):
        if not self.EVENT_TYPE:
            raise ValueError("typed event must define EVENT_TYPE")
        super().__init__(
            event_type=self.EVENT_TYPE,
            payload=dict(payload or {}),
            timestamp=timestamp or utc_now(),
            event_id=event_id or _new_event_id(),
            execution_id=execution_id or "",
            task_id=task_id or "",
        )


class TaskSelected(_TypedEvent):
    EVENT_TYPE = "task_selected"


class TaskStarted(_TypedEvent):
    EVENT_TYPE = "task_started"


class TaskStateTransitioned(_TypedEvent):
    EVENT_TYPE = "task_state_transition"


class TaskCompleted(_TypedEvent):
    EVENT_TYPE = "task_completed"


class TaskFailed(_TypedEvent):
    EVENT_TYPE = "task_failed"


class TaskNeedsRevision(_TypedEvent):
    EVENT_TYPE = "task_needs_revision"


class ExecutorStarted(_TypedEvent):
    EVENT_TYPE = "executor_started"


class ExecutorCompleted(_TypedEvent):
    EVENT_TYPE = "executor_completed"


class ExecutorFailed(_TypedEvent):
    EVENT_TYPE = "executor_failed"


class TaskRequeueStarted(_TypedEvent):
    EVENT_TYPE = "task_requeue_started"


class TaskRequeued(_TypedEvent):
    EVENT_TYPE = "task_requeued"


class RuntimeValidationCompleted(_TypedEvent):
    EVENT_TYPE = "runtime_validation_completed"


EVENT_CLASS_BY_TYPE = {
    cls.EVENT_TYPE: cls
    for cls in (
        TaskSelected,
        TaskStarted,
        TaskStateTransitioned,
        TaskCompleted,
        TaskFailed,
        TaskNeedsRevision,
        ExecutorStarted,
        ExecutorCompleted,
        ExecutorFailed,
        TaskRequeueStarted,
        TaskRequeued,
        RuntimeValidationCompleted,
    )
}


def event_from_name(event_type, payload=None, execution_id="", task_id="", timestamp=None, event_id=None):
    event_class = EVENT_CLASS_BY_TYPE.get(event_type)
    if event_class is None:
        return Event(
            event_type,
            payload=payload,
            timestamp=timestamp,
            event_id=event_id,
            execution_id=execution_id,
            task_id=task_id,
        )
    return event_class(
        payload=payload,
        timestamp=timestamp,
        event_id=event_id,
        execution_id=execution_id,
        task_id=task_id,
    )
