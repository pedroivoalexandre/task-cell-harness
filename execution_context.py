from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionContext:
    execution_id: str
    task_id: str
    task_title: str
    task_status: str
    executor_name: str
    executor_role: str
    started_at: str
    updated_at: str
    attempt_count: int
    revision_count: int
    log_context: dict = field(default_factory=dict)
    review_context: dict = field(default_factory=dict)

    @classmethod
    def create(cls, task=None, task_id=None):
        task = task or {}
        timestamp = utc_now()
        return cls(
            execution_id=str(uuid4()),
            task_id=task.get("id") or task_id or "",
            task_title=task.get("title") or "",
            task_status=task.get("status") or "pending",
            executor_name=task.get("executor") or task.get("executor_name") or "",
            executor_role=task.get("executor_role") or task.get("role") or "",
            started_at=timestamp,
            updated_at=timestamp,
            attempt_count=_int_field(task, "attempt_count"),
            revision_count=_int_field(task, "revision_count"),
        )

    def update(self, **fields):
        for key, value in fields.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = utc_now()
        return self

    def log_fields(self):
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "task_status": self.task_status,
            "executor_name": self.executor_name,
            "executor_role": self.executor_role,
            "attempt_count": self.attempt_count,
            "revision_count": self.revision_count,
        }

    def to_dict(self):
        return asdict(self)


def _int_field(data, field, default=0):
    try:
        return int(data.get(field, default) or default)
    except (TypeError, ValueError):
        return default
