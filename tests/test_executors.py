import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runner
from executors.mock import MockExecutor


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


def write_task(root, task_id, **fields):
    task_dir = root / "tasks" / "pending" / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": "pending",
        "objective": "Exercise executor abstraction.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
        "acceptance_criteria": ["Executor flow can pass review."],
    }
    data.update(fields)
    (task_dir / "task.json").write_text(json.dumps(data), encoding="utf-8")
    return task_dir


def read_events(root, task_id):
    return [
        json.loads(line)
        for line in (root / "logs" / "tasks" / f"{task_id}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]


class ExecutorTests(unittest.TestCase):
    def test_mock_executor_success_returns_textual_output_without_process(self):
        executor = MockExecutor(role="harness", should_succeed=True)

        with patch("subprocess.Popen") as popen:
            result = executor.execute(
                {"id": "mock_success", "title": "Mock success"},
                {"task_id": "mock_success"},
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["executor"], "mock")
        self.assertEqual(result["role"], "harness")
        self.assertIn("Mock execution completed", result["output"])
        popen.assert_not_called()

    def test_mock_executor_failure_is_controlled_and_textual(self):
        executor = MockExecutor(
            should_succeed=False,
            output="controlled failure output",
            failure_reason="forced by test",
        )

        result = executor.execute({"id": "mock_failure"}, {"task_id": "mock_failure"})

        self.assertFalse(result["success"])
        self.assertEqual(result["output"], "controlled failure output")
        self.assertEqual(result["error"], "forced by test")

    def test_runner_logs_executor_completion_and_preserves_success_flow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(root, "executor_done")

            runner.main()

            task_json = root / "tasks" / "done" / "executor_done" / "task.json"
            self.assertEqual(json.loads(task_json.read_text(encoding="utf-8"))["status"], "done")
            events = read_events(root, "executor_done")
            event_names = [event["event"] for event in events]
            self.assertIn("executor_started", event_names)
            self.assertIn("executor_completed", event_names)
            self.assertNotIn("executor_failed", event_names)
            transitions = [
                event["details"]["to"]
                for event in events
                if event["event"] == "task_state_transition"
            ]
            self.assertEqual(transitions, ["running", "review", "done"])

    def test_runner_logs_executor_failure_and_routes_to_review_failed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(
                root,
                "executor_failed",
                mock_executor_success="false",
                mock_executor_failure_reason="forced by task",
            )

            runner.main()

            task_json = root / "tasks" / "failed" / "executor_failed" / "task.json"
            self.assertEqual(json.loads(task_json.read_text(encoding="utf-8"))["status"], "failed")
            events = read_events(root, "executor_failed")
            event_names = [event["event"] for event in events]
            self.assertIn("executor_started", event_names)
            self.assertIn("executor_failed", event_names)
            self.assertNotIn("executor_completed", event_names)
            transitions = [
                event["details"]["to"]
                for event in events
                if event["event"] == "task_state_transition"
            ]
            self.assertEqual(transitions, ["running", "review", "failed"])
            report = (root / "reports" / "executor_failed.md").read_text(encoding="utf-8")
            self.assertIn("executor failed: forced by task", report)


if __name__ == "__main__":
    unittest.main()
