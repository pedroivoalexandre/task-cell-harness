from pathlib import Path
import json
import shutil
from datetime import datetime, timezone

OFFICIAL_STATES = (
    "pending",
    "running",
    "review",
    "needs_revision",
    "done",
    "failed",
)

ALLOWED_TRANSITIONS = {
    "pending": ("running",),
    "running": ("review", "done", "failed"),
    "review": ("done", "needs_revision", "failed"),
    "needs_revision": ("pending",),
    "failed": ("pending",),
    "done": (),
}


class InvalidTransition(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


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


def infer_state_from_path(task_path):
    task_path = Path(task_path)
    state = task_path.parent.name
    if state in OFFICIAL_STATES and task_path.parent.parent.name == "tasks":
        return state
    return None


def root_from_task_path(task_path):
    task_path = Path(task_path)
    state_dir = task_path.parent
    if state_dir.name in OFFICIAL_STATES and state_dir.parent.name == "tasks":
        return state_dir.parent.parent
    return Path(".")


def unique_destination(path):
    path = Path(path)
    if not path.exists():
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")


def validate_state(state):
    if state not in OFFICIAL_STATES:
        raise InvalidTransition(f"unknown task state: {state}")


def validate_transition(from_state, to_state):
    validate_state(from_state)
    validate_state(to_state)
    if to_state not in ALLOWED_TRANSITIONS[from_state]:
        raise InvalidTransition(f"invalid task transition: {from_state} -> {to_state}")


def read_task_status(path):
    json_path = task_json_path(path)
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None
    return data.get("status"), data


def write_task_status(path, data, status):
    json_path = task_json_path(path)
    data["status"] = status
    data["updated_at"] = now()
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def transition_task(task_path, to_state, log_event, task_id=None):
    task_path = Path(task_path)
    from_status, data = read_task_status(task_path)
    from_state = from_status or infer_state_from_path(task_path)

    if from_state is None:
        raise InvalidTransition(f"cannot infer current task state for: {task_path}")
    validate_transition(from_state, to_state)

    root = root_from_task_path(task_path)
    destination_dir = root / "tasks" / to_state
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_destination(destination_dir / task_path.name)

    status_updated = False
    if data is not None:
        write_task_status(task_path, data, to_state)
        status_updated = True

    shutil.move(str(task_path), str(destination))

    task_id = task_id or (data.get("id") if data else None) or task_id_from_path(destination)
    log_event(
        "task_state_transition",
        task_id,
        {
            "from": from_state,
            "to": to_state,
            "source": str(task_path),
            "destination": str(destination),
            "status_updated": status_updated,
        },
    )
    return destination
