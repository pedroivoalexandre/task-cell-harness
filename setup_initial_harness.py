from pathlib import Path
import json, shutil, uuid
from datetime import datetime, timezone

ROOT = Path(".")
DIRS = [
    "config",
    "tasks/pending", "tasks/running", "tasks/review", "tasks/done",
    "tasks/failed", "tasks/needs_revision",
    "knowledge", "contracts", "artifacts", "prompts", "reports",
    "journal", "logs/tasks", "logs/executors", "logs/errors",
]
for d in DIRS:
    Path(d).mkdir(parents=True, exist_ok=True)

Path("logs/harness.log").touch()
Path("journal/project_journal.md").write_text(
    "# Project Journal\n\n"
    f"- {datetime.now(timezone.utc).isoformat()} - Initial harness structure created.\n",
    encoding="utf-8"
)

executors = {
    "executors": {
        "gemini_s10": {
            "type": "cli",
            "container": "debian-gemini",
            "command": "gemini",
            "enabled": False
        },
        "codex_s10": {
            "type": "cli",
            "container": "ubuntu-codex",
            "command": "codex",
            "enabled": False
        }
    }
}
Path("config/executors.json").write_text(json.dumps(executors, indent=2), encoding="utf-8")

runner = r'''from pathlib import Path
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
'''
Path("runner.py").write_text(runner, encoding="utf-8")

fake_task = {
    "id": "fake_initial_task",
    "title": "Fake initial harness test",
    "description": "Validate folder structure, JSONL logs, report generation, and task movement without calling agents.",
    "executor": None,
    "created_at": datetime.now(timezone.utc).isoformat()
}
Path("tasks/pending/fake_initial_task.json").write_text(json.dumps(fake_task, indent=2), encoding="utf-8")

readme = """# Task Cell Harness

Initial local harness for task orchestration experiments.

Current phase:
- No external agents are executed.
- Tasks move through the local filesystem.
- Logs are written as JSON Lines.
- Reports are generated in Markdown.

Planned flow:
1. Gemini implements.
2. Codex reviews.
3. Future arbiters may be added later.
"""
Path("README.md").write_text(readme, encoding="utf-8")
