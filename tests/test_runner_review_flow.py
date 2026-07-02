import json
import tempfile
import unittest
from pathlib import Path

import runner


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


def write_task(root, task_id, extra_fields=None):
    task_dir = root / "tasks" / "pending" / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": "pending",
        "objective": "Exercise simulated review.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
    }
    if extra_fields:
        data.update(extra_fields)
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


class RunnerReviewFlowTests(unittest.TestCase):
    def test_valid_task_with_acceptance_criteria_goes_to_done(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(
                root,
                "review_done",
                {"acceptance_criteria": ["Review can approve this task."]},
            )

            runner.main()

            task_json = root / "tasks" / "done" / "review_done" / "task.json"
            self.assertEqual(json.loads(task_json.read_text(encoding="utf-8"))["status"], "done")
            report = (root / "reports" / "review_done.md").read_text(encoding="utf-8")
            self.assertIn("## Review", report)
            self.assertIn("- Decision: done", report)

            events = read_events(root, "review_done")
            transitions = [
                event["details"]["to"]
                for event in events
                if event["event"] == "task_state_transition"
            ]
            self.assertEqual(transitions, ["running", "review", "done"])
            self.assertIn("simulated_review_completed", [event["event"] for event in events])

    def test_valid_task_without_acceptance_criteria_goes_to_needs_revision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(root, "review_needs_revision")

            runner.main()

            task_json = (
                root
                / "tasks"
                / "needs_revision"
                / "review_needs_revision"
                / "task.json"
            )
            self.assertEqual(
                json.loads(task_json.read_text(encoding="utf-8"))["status"],
                "needs_revision",
            )
            report = (root / "reports" / "review_needs_revision.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Review", report)
            self.assertIn("- Decision: needs_revision", report)

            events = read_events(root, "review_needs_revision")
            transitions = [
                event["details"]["to"]
                for event in events
                if event["event"] == "task_state_transition"
            ]
            self.assertEqual(transitions, ["running", "review", "needs_revision"])

    def test_structural_error_goes_through_review_to_failed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(root, "review_failed", {"status": ""})

            runner.main()

            task_json = root / "tasks" / "failed" / "review_failed" / "task.json"
            self.assertEqual(
                json.loads(task_json.read_text(encoding="utf-8"))["status"],
                "failed",
            )
            report = (root / "reports" / "review_failed.md").read_text(encoding="utf-8")
            self.assertIn("## Review", report)
            self.assertIn("- Decision: failed", report)

            events = read_events(root, "review_failed")
            transitions = [
                event["details"]["to"]
                for event in events
                if event["event"] == "task_state_transition"
            ]
            self.assertEqual(transitions, ["running", "review", "failed"])
            self.assertTrue((root / "logs" / "errors" / "review_failed.jsonl").exists())

    def test_attempt_count_increments_when_task_is_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(
                root,
                "attempt_increment",
                {
                    "acceptance_criteria": ["Review can approve this task."],
                    "attempt_count": 1,
                    "max_attempts": 3,
                },
            )

            runner.main()

            task_json = root / "tasks" / "done" / "attempt_increment" / "task.json"
            data = json.loads(task_json.read_text(encoding="utf-8"))
            self.assertEqual(data["attempt_count"], 2)
            self.assertEqual(data["max_attempts"], 3)

            events = read_events(root, "attempt_increment")
            self.assertIn("task_attempt_incremented", [event["event"] for event in events])

    def test_task_at_max_attempts_moves_to_failed_without_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(
                root,
                "max_attempts_task",
                {
                    "acceptance_criteria": ["Would otherwise pass."],
                    "attempt_count": 3,
                    "max_attempts": 3,
                },
            )

            runner.main()

            task_json = root / "tasks" / "failed" / "max_attempts_task" / "task.json"
            data = json.loads(task_json.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "failed")
            self.assertEqual(data["attempt_count"], 3)

            report = (root / "reports" / "max_attempts_task.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Scheduler", report)
            self.assertIn("- Reason: max_attempts reached before running.", report)

            events = read_events(root, "max_attempts_task")
            event_names = [event["event"] for event in events]
            self.assertIn("task_max_attempts_exceeded", event_names)
            self.assertNotIn("simulated_review_started", event_names)


if __name__ == "__main__":
    unittest.main()
