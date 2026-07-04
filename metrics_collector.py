import json
from pathlib import Path


DEFAULT_METRICS = {
    "tasks_processed": 0,
    "tasks_done": 0,
    "tasks_failed": 0,
    "tasks_needs_revision": 0,
    "executor_success_count": 0,
    "executor_failure_count": 0,
    "average_execution_time": 0,
    "attempts_total": 0,
    "requeues_total": 0,
}


class MetricsCollector:
    def __init__(self, output_path=Path("reports") / "metrics.json"):
        self.output_path = Path(output_path)
        self.metrics = dict(DEFAULT_METRICS)

    def handle_event(self, event):
        event_type = event.event_type
        payload = event.payload or {}
        details = payload.get("details", {}) if isinstance(payload, dict) else {}
        if event_type == "task_selected":
            self.metrics["tasks_processed"] += 1
        elif event_type == "task_attempt_incremented":
            self.metrics["attempts_total"] += int(details.get("attempt_count") or 0)
        elif event_type == "task_requeued":
            self.metrics["requeues_total"] += 1
        elif event_type == "executor_completed":
            self.metrics["executor_success_count"] += 1
        elif event_type == "executor_failed":
            self.metrics["executor_failure_count"] += 1
        elif event_type == "task_state_transition":
            target = details.get("to")
            if target == "done":
                self.metrics["tasks_done"] += 1
            elif target == "failed":
                self.metrics["tasks_failed"] += 1
            elif target == "needs_revision":
                self.metrics["tasks_needs_revision"] += 1
        self.write()

    def write(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(self.metrics, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return self.output_path
