from pathlib import Path
import json
from datetime import datetime, timezone

PRIORITY_ORDER = {
    "urgent": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
}

DEFAULT_PRIORITY = "normal"
DEFAULT_MAX_ATTEMPTS = 3


def task_json_path(task_path):
    task_path = Path(task_path)
    if task_path.is_dir():
        return task_path / "task.json"
    return task_path


def task_id_from_path(task_path):
    task_path = Path(task_path)
    if task_path.is_dir():
        return task_path.name
    return task_path.stem


def parse_timestamp(value):
    if not value:
        return datetime.max.replace(tzinfo=timezone.utc)
    try:
        normalized = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_task_data(task_path):
    json_path = task_json_path(task_path)
    try:
        return json.loads(json_path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return {}, [f"task JSON not found: {json_path}"]
    except json.JSONDecodeError as exc:
        return {}, [f"invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"]


def numeric_field(data, field, default=0):
    try:
        return int(data.get(field, default) or default)
    except (TypeError, ValueError):
        return default


def priority_rank(data):
    priority = str(data.get("priority") or DEFAULT_PRIORITY).lower()
    return PRIORITY_ORDER.get(priority, PRIORITY_ORDER[DEFAULT_PRIORITY])


def queue_timestamp(data):
    revision_count = numeric_field(data, "revision_count")
    if revision_count > 0 and data.get("last_requeued_at"):
        return parse_timestamp(data.get("last_requeued_at"))
    return parse_timestamp(data.get("created_at"))


def scheduling_key(candidate):
    data = candidate["data"]
    return (
        priority_rank(data),
        queue_timestamp(data),
        numeric_field(data, "revision_count"),
        str(data.get("id") or candidate["id"]),
    )


def discover_pending_tasks(pending_dir):
    pending_dir = Path(pending_dir)
    contract_tasks = sorted(task_json.parent for task_json in pending_dir.glob("*/task.json"))
    legacy_tasks = sorted(pending_dir.glob("*.json"))
    return contract_tasks + legacy_tasks


def select_next_task(pending_dir):
    candidates = []
    for task_path in discover_pending_tasks(pending_dir):
        data, errors = load_task_data(task_path)
        candidates.append(
            {
                "path": task_path,
                "id": data.get("id") or task_id_from_path(task_path),
                "data": data,
                "errors": errors,
            }
        )
    if not candidates:
        return None
    return sorted(candidates, key=scheduling_key)[0]


def max_attempts(data):
    value = numeric_field(data, "max_attempts", DEFAULT_MAX_ATTEMPTS)
    return value if value > 0 else DEFAULT_MAX_ATTEMPTS


def attempt_count(data):
    return numeric_field(data, "attempt_count")


def attempts_exhausted(data):
    return attempt_count(data) >= max_attempts(data)


def increment_attempt_count(task_path):
    data, errors = load_task_data(task_path)
    if errors:
        return data, errors
    data["attempt_count"] = attempt_count(data) + 1
    data.setdefault("max_attempts", DEFAULT_MAX_ATTEMPTS)
    task_json_path(task_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return data, []
