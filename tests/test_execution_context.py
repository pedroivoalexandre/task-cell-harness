import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runner
from execution_context import ExecutionContext
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
    runner.EXECUTOR_CONFIG = root / "config" / "executors.json"


def write_config(root):
    config = root / "config" / "executors.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "executors": {
                    "context_mock": {
                        "type": "mock",
                        "role": "harness",
                        "enabled": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def write_task(root, task_id, **fields):
    task_dir = root / "tasks" / "pending" / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": "pending",
        "objective": "Exercise execution context.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
        "executor": "context_mock",
        "attempt_count": 0,
        "revision_count": 0,
        "acceptance_criteria": ["Execution context flow can pass review."],
    }
    data.update(fields)
    (task_dir / "task.json").write_text(json.dumps(data), encoding="utf-8")


def read_events(root, task_id):
    return [
        json.loads(line)
        for line in (root / "logs" / "tasks" / f"{task_id}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]


class ExecutionContextTests(unittest.TestCase):
    def test_execution_context_generates_unique_ids_and_log_fields(self):
        first = ExecutionContext.create({"id": "task_a", "title": "Task A", "role": "harness"})
        second = ExecutionContext.create({"id": "task_a", "title": "Task A", "role": "harness"})

        self.assertNotEqual(first.execution_id, second.execution_id)
        self.assertEqual(first.task_id, "task_a")
        self.assertEqual(first.task_title, "Task A")
        self.assertEqual(first.executor_role, "harness")
        self.assertEqual(first.log_fields()["execution_id"], first.execution_id)

    def test_mock_executor_receives_execution_context(self):
        context = ExecutionContext.create({"id": "mock_context", "title": "Mock Context"})
        executor = MockExecutor(role="harness")

        with patch("subprocess.Popen") as popen:
            result = executor.execute(
                {"id": "mock_context", "title": "Mock Context"},
                {"task_id": "mock_context", "execution_context": context},
            )

        self.assertEqual(result["execution_id"], context.execution_id)
        self.assertEqual(context.executor_name, "mock")
        self.assertEqual(context.executor_role, "harness")
        popen.assert_not_called()

    def test_runner_logs_share_execution_id_across_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_config(root)
            write_task(root, "context_done")

            runner.main()

            events = read_events(root, "context_done")
            contextual = [event for event in events if "execution_id" in event]
            self.assertTrue(contextual)
            execution_ids = {event["execution_id"] for event in contextual}
            self.assertEqual(len(execution_ids), 1)
            execution_id = execution_ids.pop()

            event_names = [event["event"] for event in events]
            self.assertIn("task_selected", event_names)
            self.assertIn("task_state_transition", event_names)
            self.assertIn("executor_started", event_names)
            self.assertIn("executor_completed", event_names)
            self.assertIn("simulated_review_completed", event_names)

            for event in contextual:
                self.assertEqual(event["details"]["execution_id"], execution_id)
                self.assertEqual(
                    event["details"]["execution_context"]["execution_id"],
                    execution_id,
                )

    def test_status_does_not_create_execution_context_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_config(root)
            write_task(root, "context_pending")

            runner.main(["status"])

            self.assertFalse((root / "logs" / "harness.log").exists())


if __name__ == "__main__":
    unittest.main()
