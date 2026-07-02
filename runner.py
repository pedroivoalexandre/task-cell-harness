from pathlib import Path
import json
from datetime import datetime, timezone
from state_machine import transition_task

ROOT = Path(".")
PENDING = ROOT / "tasks" / "pending"
RUNNING = ROOT / "tasks" / "running"
REVIEW = ROOT / "tasks" / "review"
NEEDS_REVISION = ROOT / "tasks" / "needs_revision"
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

def validate_running_task(task_path, pre_transition_data=None, pre_transition_errors=None):
    data_path = task_json_path(task_path)
    data, errors = load_task(data_path)
    pre_transition_errors = pre_transition_errors or []
    if task_path.is_dir():
        if pre_transition_errors:
            return pre_transition_data, list(pre_transition_errors)
        if data:
            errors.extend(validate_task_contract(data))
        return data, errors
    return data, errors


def simulated_review(task_path, structural_errors=None):
    review_data, read_errors = load_task(task_json_path(task_path))
    structural_errors = structural_errors or []
    if structural_errors:
        return {
            "decision": "failed",
            "summary": "Structural task errors prevent completion.",
            "errors": structural_errors,
        }
    if read_errors:
        return {
            "decision": "failed",
            "summary": "Review could not read task.json.",
            "errors": read_errors,
        }
    acceptance_criteria = review_data.get("acceptance_criteria") if review_data else None
    if acceptance_criteria:
        return {
            "decision": "done",
            "summary": "Acceptance criteria are present; simulated review approved.",
            "errors": [],
        }
    return {
        "decision": "needs_revision",
        "summary": "Task needs acceptance_criteria before completion.",
        "errors": ["missing or empty acceptance_criteria"],
    }


def write_task_report(task_id, title, status, review_result):
    report = REPORTS / f"{task_id}.md"
    errors = review_result.get("errors") or []
    error_section = ""
    if errors:
        error_section = "- Errors:\n" + "".join(f"  - {error}\n" for error in errors)
    report.write_text(
        f"# Task Report: {task_id}\n\n"
        f"## Title\n{title or ''}\n\n"
        f"## Status\n{status}\n\n"
        f"## Notes\nFake task executed without calling external agents.\n\n"
        f"## Review\n"
        f"- Decision: {review_result.get('decision')}\n"
        f"- Summary: {review_result.get('summary')}\n"
        + error_section
        + f"\n## Finished at\n{now()}\n",
        encoding="utf-8"
    )
    return report

def main():
    for directory in (
        PENDING,
        RUNNING,
        REVIEW,
        NEEDS_REVISION,
        DONE,
        FAILED,
        REPORTS,
        TASK_LOG_DIR,
        ERROR_LOG_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    task = find_task()
    if not task:
        log_event("no_pending_task")
        print("No pending task found.")
        return

    task_id = task_id_from_path(task)
    pre_transition_data = None
    pre_transition_errors = []
    if task.is_dir():
        pre_transition_data, pre_transition_errors = load_task(task_json_path(task))
        if pre_transition_data:
            task_id = pre_transition_data.get("id") or task_id
            pre_transition_errors.extend(validate_task_contract(pre_transition_data))

    log_event("task_found", task_id, {"path": str(task)})
    running_task = transition_task(task, "running", log_event, task_id=task_id)

    data, structural_errors = validate_running_task(
        running_task,
        pre_transition_data=pre_transition_data,
        pre_transition_errors=pre_transition_errors,
    )
    if data:
        task_id = data.get("id") or task_id
    elif not structural_errors:
        raise ValueError("task data could not be loaded")

    log_event("task_started", task_id, {"title": data.get("title") if data else ""})
    review_task = transition_task(running_task, "review", log_event, task_id=task_id)

    log_event(
        "simulated_review_started",
        task_id,
        {"path": str(task_json_path(review_task))},
    )
    review_result = simulated_review(review_task, structural_errors)
    log_event("simulated_review_completed", task_id, review_result)

    decision = review_result["decision"]
    status_title = {
        "done": "Done",
        "needs_revision": "Needs Revision",
        "failed": "Failed",
    }[decision]
    report = write_task_report(
        task_id,
        data.get("title") if data else "",
        status_title,
        review_result,
    )
    log_event("report_created", task_id, {"path": str(report), "review_decision": decision})

    if decision == "failed":
        log_error(task_id, review_result["errors"], task_json_path(review_task))

    final_task = transition_task(review_task, decision, log_event, task_id=task_id)
    if decision == "done":
        print(f"Task completed: {task_id}")
    elif decision == "needs_revision":
        print(f"Task needs revision: {task_id}")
    else:
        print(f"Task failed review: {task_id}")
    return final_task

if __name__ == "__main__":
    main()
