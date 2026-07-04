from pathlib import Path
import argparse
import json
import sys
from datetime import datetime, timezone
from artifact_manager import ArtifactManager
from execution_context import ExecutionContext
from event_bus import EventBus
from events import event_from_name
from metrics_collector import MetricsCollector
from executor_registry import load_executor_registry
from report_builder import ReportBuilder
from resource_manager import ResourceManager
from runtime_config import RuntimeConfig
from runtime_validation import RuntimeValidator
from scheduler import (
    attempt_count,
    attempts_exhausted,
    discover_pending_tasks,
    increment_attempt_count,
    load_task_data,
    max_attempts,
    numeric_field,
    queue_timestamp,
    scheduling_key,
    select_next_task,
)
from state_machine import transition_task, validate_transition

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
EXECUTOR_CONFIG = ROOT / "config" / "executors.json"
RUNTIME_CONFIG = ROOT / "config" / "runtime.json"
EVENT_BUS = EventBus()
METRICS = None
RESOURCE_MANAGER = None
CURRENT_RUNTIME_CONFIG = RuntimeConfig()

QUEUE_STATES = (
    "pending",
    "running",
    "review",
    "needs_revision",
    "failed",
    "done",
)
REQUIRED_TASK_JSON_FIELDS = (
    "id",
    "title",
    "status",
    "objective",
    "created_at",
    "priority",
    "role",
)

def runtime_config_path():
    if Path(RUNTIME_CONFIG).is_absolute():
        return RUNTIME_CONFIG
    return ROOT / RUNTIME_CONFIG


def initialize_runtime_services():
    global EVENT_BUS, METRICS, RESOURCE_MANAGER, CURRENT_RUNTIME_CONFIG
    CURRENT_RUNTIME_CONFIG = RuntimeConfig.load(runtime_config_path())
    EVENT_BUS = EventBus()
    METRICS = MetricsCollector(REPORTS / "metrics.json")
    RESOURCE_MANAGER = ResourceManager(ROOT / "runtime", project_root=ROOT)
    RESOURCE_MANAGER.ensure_directories()
    EVENT_BUS.subscribe("*", _write_runtime_log_event)
    EVENT_BUS.subscribe("task_validation_failed", _write_error_log_event)
    EVENT_BUS.subscribe("*", METRICS.handle_event)

def _write_jsonl_record(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + chr(10))


def _write_runtime_log_event(event):
    record = event.to_record()
    _write_jsonl_record(HARNESS_LOG, record)
    if event.task_id:
        _write_jsonl_record(TASK_LOG_DIR / f"{event.task_id}.jsonl", record)


def _write_error_log_event(event):
    _write_jsonl_record(ERROR_LOG_DIR / f"{event.task_id or event.event_id}.jsonl", event.to_record())


def _coerce_runtime_event(event, task_id=None, details=None, execution_context=None):
    payload = dict(details or {})
    if execution_context is not None:
        payload.setdefault("execution_id", execution_context.execution_id)
        payload.setdefault("execution_context", execution_context.log_fields())
    if hasattr(event, "event_type") and hasattr(event, "to_record"):
        runtime_event = event
        if payload:
            runtime_event.payload.update(payload)
        if execution_context is not None:
            runtime_event.execution_id = runtime_event.execution_id or execution_context.execution_id
            runtime_event.task_id = runtime_event.task_id or task_id or execution_context.task_id
        elif task_id:
            runtime_event.task_id = runtime_event.task_id or task_id
        return runtime_event
    execution_id = payload.get("execution_id") or (execution_context.execution_id if execution_context else "")
    inferred_task_id = task_id or payload.get("task_id") or (execution_context.task_id if execution_context else "")
    return event_from_name(
        event,
        payload=payload,
        execution_id=execution_id or "",
        task_id=inferred_task_id or "",
    )

def now():
    return datetime.now(timezone.utc).isoformat()

def log_event(event, task_id=None, details=None, execution_context=None):
    runtime_event = _coerce_runtime_event(
        event,
        task_id=task_id,
        details=details,
        execution_context=execution_context,
    )
    EVENT_BUS.emit(runtime_event)
    return runtime_event


def log_error(task_id, errors, path, execution_context=None):
    details = {
        "path": str(path),
        "errors": errors,
    }
    log_event("task_validation_failed", task_id, details, execution_context=execution_context)


def log_event_with_context(execution_context):
    def logger(event, task_id=None, details=None):
        log_event(event, task_id, details, execution_context=execution_context)
    return logger



def artifact_root_path():
    return ROOT / "artifacts"


def register_report_artifact(report_path, execution_context, task_id):
    if execution_context is None:
        return None
    manager = ArtifactManager(artifact_root_path())
    artifact = manager.register_file(
        report_path,
        execution_context,
        name=Path(report_path).name,
        kind="markdown_report",
    )
    log_event(
        "artifact_registered",
        task_id,
        {
            "artifact_id": artifact["artifact_id"],
            "path": artifact["path"],
            "kind": artifact["kind"],
        },
        execution_context=execution_context,
    )
    return artifact

def find_task():
    selected = select_next_task(PENDING)
    return selected["path"] if selected else None


def state_directories():
    return {
        "pending": PENDING,
        "running": RUNNING,
        "review": REVIEW,
        "needs_revision": NEEDS_REVISION,
        "failed": FAILED,
        "done": DONE,
    }


def find_needs_revision_task(task_id):
    contract_task = NEEDS_REVISION / task_id
    if (contract_task / "task.json").exists():
        return contract_task

    legacy_task = NEEDS_REVISION / f"{task_id}.json"
    if legacy_task.exists():
        return legacy_task
    return None

def task_json_path(task_path):
    if task_path.is_dir():
        return task_path / "task.json"
    return task_path

def task_id_from_path(task_path):
    if task_path.is_dir():
        return task_path.name
    return task_path.stem


def discover_state_tasks(state, state_dir):
    state_dir = Path(state_dir)
    if state == "pending":
        candidates = []
        for task_path in discover_pending_tasks(state_dir):
            data, errors = load_task_data(task_path)
            candidates.append(
                {
                    "path": task_path,
                    "id": data.get("id") or task_id_from_path(task_path),
                    "data": data,
                    "errors": errors,
                }
            )
        return sorted(candidates, key=scheduling_key)

    contract_tasks = sorted(task_json.parent for task_json in state_dir.glob("*/task.json"))
    legacy_tasks = sorted(state_dir.glob("*.json"))
    tasks = []
    for task_path in contract_tasks + legacy_tasks:
        data, errors = load_task_data(task_path)
        tasks.append(
            {
                "path": task_path,
                "id": data.get("id") or task_id_from_path(task_path),
                "data": data,
                "errors": errors,
            }
        )
    return tasks


def task_status_summary(candidate, fallback_state):
    data = candidate["data"]
    summary = {
        "id": data.get("id") or candidate["id"],
        "title": data.get("title") or "",
        "priority": data.get("priority") or "normal",
        "status": data.get("status") or fallback_state,
        "revision_count": numeric_field(data, "revision_count"),
        "attempt_count": attempt_count(data),
        "max_attempts": max_attempts(data),
        "created_at": data.get("created_at") or "",
    }
    if data.get("last_requeued_at"):
        summary["last_requeued_at"] = data["last_requeued_at"]
    return summary


def format_task_summary(candidate, fallback_state):
    summary = task_status_summary(candidate, fallback_state)
    lines = [
        f"- id: {summary['id']}",
        f"  title: {summary['title']}",
        f"  priority: {summary['priority']}",
        f"  status: {summary['status']}",
        f"  revision_count: {summary['revision_count']}",
        f"  attempt_count: {summary['attempt_count']}",
        f"  max_attempts: {summary['max_attempts']}",
        f"  created_at: {summary['created_at']}",
    ]
    if "last_requeued_at" in summary:
        lines.append(f"  last_requeued_at: {summary['last_requeued_at']}")
    return lines


def format_next_task(candidate):
    if candidate is None:
        return ["Next task:", "- none"]

    data = candidate["data"]
    summary = task_status_summary(candidate, "pending")
    queue_value = queue_timestamp(data).isoformat()
    return [
        "Next task:",
        f"- id: {summary['id']}",
        f"- title: {summary['title']}",
        f"- priority: {summary['priority']}",
        f"- attempts: {summary['attempt_count']}/{summary['max_attempts']}",
        (
            "- reason/order basis: "
            f"priority={summary['priority']}, "
            f"queue_timestamp={queue_value}, "
            f"revision_count={summary['revision_count']}, "
            f"id={summary['id']}"
        ),
    ]


def build_queue_status_lines():
    lines = ["Queue status"]
    all_tasks = {}
    for state, directory in state_directories().items():
        all_tasks[state] = discover_state_tasks(state, directory)

    for state in QUEUE_STATES:
        lines.append("")
        lines.append(f"{state}:")
        tasks = all_tasks[state]
        if not tasks:
            lines.append("- none")
            continue
        for candidate in tasks:
            lines.extend(format_task_summary(candidate, state))

    lines.append("")
    next_task = all_tasks["pending"][0] if all_tasks["pending"] else None
    lines.extend(format_next_task(next_task))
    return lines


def run_status():
    output = "\n".join(build_queue_status_lines())
    print(output)
    return output

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


def executor_request(task_data):
    task_data = task_data or {}
    return {
        "name": task_data.get("executor") or task_data.get("executor_name"),
        "role": task_data.get("executor_role") or task_data.get("role"),
    }


def executor_config_path():
    if Path(EXECUTOR_CONFIG).is_absolute():
        return EXECUTOR_CONFIG
    return ROOT / EXECUTOR_CONFIG


def resolve_executor_for_task(task_id, task_data, execution_context=None):
    request = executor_request(task_data)
    config_path = executor_config_path()
    registry = load_executor_registry(config_path)
    loaded_details = {
        "path": str(config_path),
        "count": len(registry.executors),
    }
    if registry.errors:
        loaded_details["errors"] = registry.errors
        log_event(
            "executor_registry_error",
            task_id,
            loaded_details,
            execution_context=execution_context,
        )
    else:
        log_event(
            "executor_registry_loaded",
            task_id,
            loaded_details,
            execution_context=execution_context,
        )

    resolution = registry.resolve(
        name=request["name"],
        role=request["role"],
        task=task_data or {},
        runtime_config=CURRENT_RUNTIME_CONFIG,
    )
    config = resolution["config"]
    details = {
        "requested_name": request["name"],
        "requested_role": request["role"],
        "resolved_name": config.get("name") if config else None,
        "resolved_role": config.get("role") if config else None,
        "reason": resolution["reason"],
        "kind": resolution.get("kind"),
        "blocked": resolution.get("blocked", False),
        "policy": resolution.get("policy", {}),
    }
    if execution_context is not None:
        execution_context.update(
            executor_name=config.get("name"),
            executor_role=config.get("role"),
        )
    if resolution["fallback"]:
        log_event(
            "executor_fallback_used",
            task_id,
            details,
            execution_context=execution_context,
        )
    if resolution.get("blocked"):
        log_event(
            "executor_policy_blocked",
            task_id,
            details,
            execution_context=execution_context,
        )
    log_event("executor_resolved", task_id, details, execution_context=execution_context)
    return resolution["executor"], details


def execute_task_with_executor(task_id, task_data, task_path, execution_context=None):
    executor, resolution_details = resolve_executor_for_task(
        task_id,
        task_data or {},
        execution_context=execution_context,
    )
    context = {
        "task_id": task_id,
        "task_path": display_path(task_path),
        "executor_resolution": resolution_details,
        "execution_context": execution_context,
        "artifact_root": artifact_root_path(),
    }
    details = {
        "executor": executor.name,
        "role": executor.role,
        "path": context["task_path"],
    }
    log_event("executor_started", task_id, details, execution_context=execution_context)
    if executor is None:
        failure_message = "executor resolution returned no executable instance"
        log_event(
            "executor_failed",
            task_id,
            {**details, "success": False, "error": failure_message},
            execution_context=execution_context,
        )
        return {
            "success": False,
            "executor": None,
            "role": None,
            "output": "",
            "error": failure_message,
        }
    try:
        result = executor.execute(task_data or {}, context)
    except Exception as exc:
        failure = {
            **details,
            "success": False,
            "error": str(exc),
        }
        log_event("executor_failed", task_id, failure, execution_context=execution_context)
        return {
            "success": False,
            "executor": executor.name,
            "role": executor.role,
            "output": "",
            "error": str(exc),
        }

    event_details = {
        **details,
        "success": bool(result.get("success")),
        "output": result.get("output", ""),
    }
    if result.get("success"):
        log_event(
            "executor_completed",
            task_id,
            event_details,
            execution_context=execution_context,
        )
    else:
        event_details["error"] = result.get("error") or "executor returned failure"
        log_event("executor_failed", task_id, event_details, execution_context=execution_context)
    return result


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


def write_task_report(task_id, title, status, review_result, execution_context=None):
    report = REPORTS / f"{task_id}.md"
    ReportBuilder().write_report(
        report,
        task_id,
        title,
        status,
        review_result=review_result,
        execution_context=execution_context,
    )
    return report


def write_attempt_failure_report(task_id, title, attempt_count, max_attempts):
    report = REPORTS / f"{task_id}.md"
    report.write_text(
        f"# Task Report: {task_id}\n\n"
        f"## Title\n{title or ''}\n\n"
        f"## Status\nFailed\n\n"
        f"## Scheduler\n"
        f"- Reason: max_attempts reached before running.\n"
        f"- Attempt count: {attempt_count}\n"
        f"- Max attempts: {max_attempts}\n"
        f"\n## Finished at\n{now()}\n",
        encoding="utf-8",
    )
    return report


def append_requeue_report(task_id, requeue_details):
    report = REPORTS / f"{task_id}.md"
    if report.exists():
        current = report.read_text(encoding="utf-8").rstrip()
    else:
        current = f"# Task Report: {task_id}"
    section = (
        f"\n\n## Requeue\n"
        f"- Revision count: {requeue_details['revision_count']}\n"
        f"- Reason: {requeue_details['reason']}\n"
        f"- Source: {requeue_details['source']}\n"
        f"- Destination: {requeue_details['destination']}\n"
        f"- Requeued at: {requeue_details['timestamp']}\n"
    )
    report.write_text(current + section, encoding="utf-8")
    return report


def display_path(path):
    path = Path(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def current_task_state(task_path, data):
    if data and data.get("status"):
        return data["status"]
    return Path(task_path).parent.name


def prepare_requeue_metadata(task_path, reason):
    json_path = task_json_path(task_path)
    data, errors = load_task(json_path)
    if errors:
        raise ValueError("; ".join(errors))
    if data is None:
        raise ValueError(f"task.json not found: {json_path}")

    validate_transition(current_task_state(task_path, data), "pending")

    timestamp = now()
    revision_count = int(data.get("revision_count") or 0) + 1
    history = data.get("revision_history") or []
    if not isinstance(history, list):
        history = []

    source = display_path(task_path)
    history_entry = {
        "revision_count": revision_count,
        "reason": reason,
        "timestamp": timestamp,
        "source": source,
        "from": "needs_revision",
        "to": "pending",
    }
    history.append(history_entry)

    data["revision_count"] = revision_count
    data["last_revision_reason"] = reason
    data["last_requeued_at"] = timestamp
    data["revision_history"] = history
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return data, history_entry


def requeue_task(task_path, reason):
    task_path = Path(task_path)
    task_id = task_id_from_path(task_path)
    log_event("task_requeue_started", task_id, {"path": display_path(task_path), "reason": reason})
    try:
        data, history_entry = prepare_requeue_metadata(task_path, reason)
        task_id = data.get("id") or task_id
        destination = transition_task(task_path, "pending", log_event, task_id=task_id)
        details = {
            "source": history_entry["source"],
            "destination": str(destination),
            "reason": reason,
            "revision_count": history_entry["revision_count"],
            "timestamp": history_entry["timestamp"],
        }
        report = append_requeue_report(task_id, details)
        details["report"] = str(report)
        log_event("task_requeued", task_id, details)
        return destination
    except Exception as exc:
        log_event(
            "task_requeue_failed",
            task_id,
            {"path": display_path(task_path), "reason": reason, "error": str(exc)},
        )
        raise

def ensure_directories():
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Task Cell Harness runner")
    parser.add_argument(
        "--requeue",
        metavar="TASK_ID",
        help="move a task from needs_revision back to pending",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("status", "validate-runtime"),
        help="inspect the task queue without executing tasks",
    )
    parser.add_argument(
        "--reason",
        default="Requeued after revision",
        help="reason stored in revision metadata when using --requeue",
    )
    return parser.parse_args(argv)


def run_requeue(task_id, reason):
    task = find_needs_revision_task(task_id)
    if task is None:
        log_event(
            "task_requeue_failed",
            task_id,
            {
                "path": str(NEEDS_REVISION / task_id),
                "reason": reason,
                "error": "task not found in needs_revision",
            },
        )
        raise FileNotFoundError(f"task not found in needs_revision: {task_id}")
    destination = requeue_task(task, reason)
    print(f"Task requeued: {task_id}")
    return destination


def run_validate_runtime():
    REPORTS.mkdir(parents=True, exist_ok=True)
    result = RuntimeValidator(ROOT).write_report(REPORTS / "runtime_validation.md")
    log_event(
        "runtime_validation_completed",
        None,
        {
            "report_path": str(REPORTS / "runtime_validation.md"),
            "ok": result["ok"],
            "warnings": result.get("warnings", []),
        },
    )
    print(f"Runtime validation: {'OK' if result['ok'] else 'FAILED'}")
    return result

def main(argv=None):
    args = parse_args(argv or [])

    ensure_directories()
    initialize_runtime_services()

    if args.command == "status":
        return run_status()
    if args.command == "validate-runtime":
        return run_validate_runtime()

    if args.requeue:
        return run_requeue(args.requeue, args.reason)

    task = find_task()
    if not task:
        log_event("no_pending_task")
        print("No pending task found.")
        return

    task_id = task_id_from_path(task)
    pre_transition_data = None
    pre_transition_errors = []
    scheduler_data, scheduler_errors = load_task(task_json_path(task))
    if scheduler_data:
        task_id = scheduler_data.get("id") or task_id

    if scheduler_errors:
        pre_transition_errors = scheduler_errors
    elif task.is_dir():
        pre_transition_data = scheduler_data
        if pre_transition_data:
            pre_transition_errors.extend(validate_task_contract(pre_transition_data))

    execution_context = ExecutionContext.create(scheduler_data or {}, task_id=task_id)
    if RESOURCE_MANAGER is not None:
        RESOURCE_MANAGER.prepare_execution(execution_context)
    context_log_event = log_event_with_context(execution_context)

    log_event(
        "task_selected",
        task_id,
        {
            "path": str(task),
            "priority": scheduler_data.get("priority") if scheduler_data else None,
            "created_at": scheduler_data.get("created_at") if scheduler_data else None,
            "revision_count": scheduler_data.get("revision_count", 0) if scheduler_data else 0,
            "attempt_count": scheduler_data.get("attempt_count", 0) if scheduler_data else 0,
            "max_attempts": scheduler_data.get("max_attempts", 3) if scheduler_data else 3,
        },
        execution_context=execution_context,
    )

    if scheduler_data and attempts_exhausted(scheduler_data):
        details = {
            "path": str(task),
            "attempt_count": scheduler_data.get("attempt_count", 0),
            "max_attempts": scheduler_data.get("max_attempts", 3),
        }
        log_event(
            "task_max_attempts_exceeded",
            task_id,
            details,
            execution_context=execution_context,
        )
        report = write_attempt_failure_report(
            task_id,
            scheduler_data.get("title", ""),
            details["attempt_count"],
            details["max_attempts"],
        )
        log_event(
            "report_created",
            task_id,
            {"path": str(report), "reason": "max_attempts"},
            execution_context=execution_context,
        )
        register_report_artifact(report, execution_context, task_id)
        execution_context.update(task_status="running")
        running_exhausted_task = transition_task(task, "running", context_log_event, task_id=task_id)
        execution_context.update(task_status="failed")
        transition_task(running_exhausted_task, "failed", context_log_event, task_id=task_id)
        print(f"Task failed max attempts: {task_id}")
        return

    updated_data, attempt_errors = increment_attempt_count(task)
    if attempt_errors:
        pre_transition_errors.extend(attempt_errors)
    elif updated_data:
        scheduler_data = updated_data
        pre_transition_data = updated_data if task.is_dir() else pre_transition_data
        execution_context.update(
            attempt_count=updated_data.get("attempt_count"),
            revision_count=updated_data.get("revision_count"),
        )
        log_event(
            "task_attempt_incremented",
            task_id,
            {
                "attempt_count": updated_data.get("attempt_count"),
                "max_attempts": updated_data.get("max_attempts"),
            },
            execution_context=execution_context,
        )

    log_event("task_found", task_id, {"path": str(task)}, execution_context=execution_context)
    execution_context.update(task_status="running")
    running_task = transition_task(task, "running", context_log_event, task_id=task_id)

    data, structural_errors = validate_running_task(
        running_task,
        pre_transition_data=pre_transition_data,
        pre_transition_errors=pre_transition_errors,
    )
    if data:
        task_id = data.get("id") or task_id
        execution_context.update(
            task_id=task_id,
            task_title=data.get("title"),
            task_status=data.get("status"),
            attempt_count=data.get("attempt_count"),
            revision_count=data.get("revision_count"),
        )
    elif not structural_errors:
        raise ValueError("task data could not be loaded")

    log_event(
        "task_started",
        task_id,
        {"title": data.get("title") if data else ""},
        execution_context=execution_context,
    )
    executor_result = execute_task_with_executor(
        task_id,
        data or {},
        running_task,
        execution_context=execution_context,
    )
    if not executor_result.get("success"):
        structural_errors = list(structural_errors)
        structural_errors.append(
            f"executor failed: {executor_result.get('error') or 'unknown error'}"
        )

    execution_context.update(task_status="review")
    review_task = transition_task(running_task, "review", context_log_event, task_id=task_id)

    log_event(
        "simulated_review_started",
        task_id,
        {"path": str(task_json_path(review_task))},
        execution_context=execution_context,
    )
    review_result = simulated_review(review_task, structural_errors)
    execution_context.review_context = dict(review_result)
    log_event(
        "simulated_review_completed",
        task_id,
        review_result,
        execution_context=execution_context,
    )

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
        execution_context=execution_context,
    )
    log_event(
        "report_created",
        task_id,
        {"path": str(report), "review_decision": decision},
        execution_context=execution_context,
    )
    register_report_artifact(report, execution_context, task_id)
    log_event(
        {"done": "task_completed", "needs_revision": "task_needs_revision", "failed": "task_failed"}[decision],
        task_id,
        {
            "summary": review_result["summary"],
            "errors": review_result["errors"],
            "report": str(report),
        },
        execution_context=execution_context,
    )

    if decision == "failed":
        log_error(
            task_id,
            review_result["errors"],
            task_json_path(review_task),
            execution_context=execution_context,
        )

    execution_context.update(task_status=decision)
    final_task = transition_task(review_task, decision, context_log_event, task_id=task_id)
    if decision == "done":
        print(f"Task completed: {task_id}")
    elif decision == "needs_revision":
        print(f"Task needs revision: {task_id}")
    else:
        print(f"Task failed review: {task_id}")
    return final_task

if __name__ == "__main__":
    main(sys.argv[1:])
