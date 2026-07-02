from pathlib import Path
import json, shutil
from datetime import datetime, timezone

ROOT = Path(".")
PENDING = ROOT / "tasks" / "pending"
RUNNING = ROOT / "tasks" / "running"
DONE = ROOT / "tasks" / "done"
FAILED = ROOT / "tasks" / "failed"
REPORTS = ROOT / "reports"
HARNESS_LOG = ROOT / "logs" / "harness.log"
TASK_LOG_DIR = ROOT / "logs" / "tasks"
ERROR_LOG_DIR = ROOT / "logs" / "errors"
REQUIRED_TASK_JSON_FIELDS = (
    "id",
    "title",
    "status",
    "objective",
    "created_at",
    "priority",
    "role",
)

def now():
    return datetime.now(timezone.utc).isoformat()

def log_event(event, task_id=None, details=None):
    TASK_LOG_DIR.mkdir(parents=True, exist_ok=True)
    HARNESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": now(),
        "event": event,
        "task_id": task_id,
        "details": details or {}
    }
    with HARNESS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    if task_id:
        with (TASK_LOG_DIR / f"{task_id}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def log_error(task_id, errors, path):
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": now(),
        "event": "task_validation_failed",
        "task_id": task_id,
        "details": {
            "path": str(path),
            "errors": errors,
        },
    }
    with (ERROR_LOG_DIR / f"{task_id}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    log_event("task_validation_failed", task_id, record["details"])

def unique_destination(path):
    if not path.exists():
        return path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")

def find_task():
    contract_tasks = sorted(
        task_json.parent for task_json in PENDING.glob("*/task.json")
    )
    if contract_tasks:
        return contract_tasks[0]

    legacy_tasks = sorted(PENDING.glob("*.json"))
    return legacy_tasks[0] if legacy_tasks else None

def task_json_path(task_path):
    if task_path.is_dir():
        return task_path / "task.json"
    return task_path

def task_id_from_path(task_path):
    if task_path.is_dir():
        return task_path.name
    return task_path.stem

def validate_task_contract(data):
    errors = []
    for field in REQUIRED_TASK_JSON_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
        elif data[field] in (None, ""):
            errors.append(f"empty required field: {field}")
    return errors

def load_task(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"]
    return data, []

def write_failure_report(task_id, title, errors):
    report = REPORTS / f"{task_id}.md"
    report.write_text(
        f"# Task Report: {task_id}\n\n"
        f"## Title\n{title or ''}\n\n"
        f"## Status\nFailed\n\n"
        f"## Errors\n"
        + "".join(f"- {error}\n" for error in errors)
        + f"\n## Finished at\n{now()}\n",
        encoding="utf-8"
    )
    return report

def main():
    for directory in (PENDING, RUNNING, DONE, FAILED, REPORTS, TASK_LOG_DIR, ERROR_LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    task = find_task()
    if not task:
        log_event("no_pending_task")
        print("No pending task found.")
        return

    task_id = task_id_from_path(task)
    running_task = unique_destination(RUNNING / task.name)

    log_event("task_found", task_id, {"path": str(task)})
    shutil.move(str(task), str(running_task))
    log_event("task_moved_to_running", task_id, {"path": str(running_task)})

    data_path = task_json_path(running_task)
    data, errors = load_task(data_path)
    if running_task.is_dir():
        if data:
            task_id = data.get("id") or task_id
            errors.extend(validate_task_contract(data))
        if errors:
            log_error(task_id, errors, data_path)
            report = write_failure_report(
                task_id,
                data.get("title") if data else "",
                errors,
            )
            log_event("failure_report_created", task_id, {"path": str(report)})
            failed_task = unique_destination(FAILED / running_task.name)
            shutil.move(str(running_task), str(failed_task))
            log_event("task_moved_to_failed", task_id, {"path": str(failed_task)})
            print(f"Task failed validation: {task_id}")
            return
    elif errors:
        raise ValueError("; ".join(errors))

    log_event("task_started", task_id, {"title": data.get("title")})

    report = REPORTS / f"{task_id}.md"
    report.write_text(
        f"# Task Report: {task_id}\n\n"
        f"## Title\n{data.get('title', '')}\n\n"
        f"## Status\nDone\n\n"
        f"## Notes\nFake task executed without calling external agents.\n\n"
        f"## Finished at\n{now()}\n",
        encoding="utf-8"
    )
    log_event("report_created", task_id, {"path": str(report)})

    done_task = unique_destination(DONE / running_task.name)
    shutil.move(str(running_task), str(done_task))
    log_event("task_moved_to_done", task_id, {"path": str(done_task)})
    print(f"Task completed: {task_id}")

if __name__ == "__main__":
    main()
