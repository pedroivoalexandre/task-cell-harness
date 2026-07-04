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
        self._counted_terminal_tasks = {
            "done": set(),
            "failed": set(),
            "needs_revision": set(),
        }

    def handle_event(self, event):
        event_type = getattr(event, "event_type", "")
        payload = getattr(event, "payload", {}) or {}
        if isinstance(payload.get("details"), dict):
            merged = dict(payload.get("details"))
            merged.update({key: value for key, value in payload.items() if key != "details"})
            payload = merged
        task_id = getattr(event, "task_id", "") or payload.get("task_id") or payload.get("id") or ""

        if event_type == "task_selected":
            self.metrics["tasks_processed"] += 1
        elif event_type == "task_attempt_incremented":
            self.metrics["attempts_total"] += int(payload.get("attempt_count") or 0)
        elif event_type == "task_requeued":
            self.metrics["requeues_total"] += 1
        elif event_type == "executor_completed":
            self.metrics["executor_success_count"] += 1
        elif event_type == "executor_failed":
            self.metrics["executor_failure_count"] += 1
        elif event_type == "task_completed":
            self._increment_terminal("done", task_id)
        elif event_type == "task_failed":
            self._increment_terminal("failed", task_id)
        elif event_type == "task_needs_revision":
            self._increment_terminal("needs_revision", task_id)
        elif event_type == "task_state_transition":
            target = payload.get("to")
            if target in self._counted_terminal_tasks:
                self._increment_terminal(target, task_id)
        self.write()

    def _increment_terminal(self, terminal_state, task_id):
        if terminal_state not in self._counted_terminal_tasks:
            return
        seen = self._counted_terminal_tasks[terminal_state]
        if task_id and task_id in seen:
            return
        if task_id:
            seen.add(task_id)
        metric_name = {
            "done": "tasks_done",
            "failed": "tasks_failed",
            "needs_revision": "tasks_needs_revision",
        }[terminal_state]
        self.metrics[metric_name] += 1

    def write(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(self.metrics, ensure_ascii=False, indent=2) + chr(10),
            encoding="utf-8",
        )
        return self.output_path
