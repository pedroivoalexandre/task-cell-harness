import json
import tempfile
import unittest
from pathlib import Path

import runner
from state_machine import InvalidTransition


def configure_runner_root(root):
    runner.ROOT = root
    runner.PENDING = root / "tasks" / "pending"
    runner.RUNNING = root / "tasks" / "running"
    runner.REVIEW = root / "tasks" / "review"
    runner.NEEDS_REVISION = root / "tasks" / "needs_revision"
    runner.DONE = root / "tasks" / "done"
    runner.FAILED = root / "tasks" / "failed"
    runner.REPORTS = root / "reports"
    runner.HARNESS_LOG = root / "logs" / "harness.log"
    runner.TASK_LOG_DIR = root / "logs" / "tasks"
    runner.ERROR_LOG_DIR = root / "logs" / "errors"


def write_requeue_task(root, state="needs_revision", task_id="requeue_task"):
    task_dir = root / "tasks" / state / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": state,
        "objective": "Exercise requeue flow.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
        "revision_count": 1,
        "revision_history": [
            {
                "revision_count": 1,
                "reason": "Initial review requested acceptance criteria.",
                "timestamp": "2026-07-02T00:01:00+00:00",
                "source": "tasks/review/requeue_task",
                "from": "review",
                "to": "needs_revision",
            }
        ],
    }
    (task_dir / "task.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    return task_dir


def read_events(root, task_id):
    return [
        json.loads(line)
        for line in (root / "logs" / "tasks" / f"{task_id}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]


class RunnerRequeueFlowTests(unittest.TestCase):
    def test_requeue_moves_needs_revision_to_pending_and_updates_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_requeue_task(root)

            runner.main(["--requeue", "requeue_task", "--reason", "Acceptance criteria added."])

            task_json = root / "tasks" / "pending" / "requeue_task" / "task.json"
            data = json.loads(task_json.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "pending")
            self.assertEqual(data["revision_count"], 2)
            self.assertEqual(data["last_revision_reason"], "Acceptance criteria added.")
            self.assertIn("last_requeued_at", data)
            self.assertEqual(len(data["revision_history"]), 2)
            self.assertEqual(data["revision_history"][-1]["reason"], "Acceptance criteria added.")
            self.assertEqual(data["revision_history"][-1]["timestamp"], data["last_requeued_at"])
            self.assertEqual(data["revision_history"][-1]["source"], "tasks/needs_revision/requeue_task")

            events = read_events(root, "requeue_task")
            self.assertIn("task_requeue_started", [event["event"] for event in events])
            self.assertIn("task_requeued", [event["event"] for event in events])
            transitions = [
                event["details"]["to"]
                for event in events
                if event["event"] == "task_state_transition"
            ]
            self.assertEqual(transitions, ["pending"])

            report = (root / "reports" / "requeue_task.md").read_text(encoding="utf-8")
            self.assertIn("## Requeue", report)
            self.assertIn("- Revision count: 2", report)

    def test_requeue_invalid_transition_is_blocked_and_logged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            done_task = write_requeue_task(root, state="done", task_id="invalid_requeue")

            with self.assertRaises(InvalidTransition):
                runner.requeue_task(done_task, "Should not requeue from done.")

            task_json = root / "tasks" / "done" / "invalid_requeue" / "task.json"
            data = json.loads(task_json.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "done")
            self.assertEqual(data["revision_count"], 1)
            self.assertEqual(len(data["revision_history"]), 1)

            events = read_events(root, "invalid_requeue")
            self.assertIn("task_requeue_started", [event["event"] for event in events])
            self.assertIn("task_requeue_failed", [event["event"] for event in events])


if __name__ == "__main__":
    unittest.main()
