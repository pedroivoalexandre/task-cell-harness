from pathlib import Path
import json, shutil
from datetime import datetime, timezone

ROOT = Path(".")
PENDING = ROOT / "tasks" / "pending"
RUNNING = ROOT / "tasks" / "running"
DONE = ROOT / "tasks" / "done"
REPORTS = ROOT / "reports"
HARNESS_LOG = ROOT / "logs" / "harness.log"
TASK_LOG_DIR = ROOT / "logs" / "tasks"

def now():
    return datetime.now(timezone.utc).isoformat()

def log_event(event, task_id=None, details=None):
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

def find_task():
    tasks = sorted(PENDING.glob("*.json"))
    return tasks[0] if tasks else None

def main():
    task = find_task()
    if not task:
        log_event("no_pending_task")
        print("No pending task found.")
        return

    task_id = task.stem
    running_task = RUNNING / task.name

    log_event("task_found", task_id, {"path": str(task)})
    shutil.move(str(task), str(running_task))
    log_event("task_moved_to_running", task_id, {"path": str(running_task)})

    data = json.loads(running_task.read_text(encoding="utf-8"))
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

    done_task = DONE / running_task.name
    shutil.move(str(running_task), str(done_task))
    log_event("task_moved_to_done", task_id, {"path": str(done_task)})
    print(f"Task completed: {task_id}")

if __name__ == "__main__":
    main()
