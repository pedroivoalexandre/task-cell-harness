import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runner
from executor_registry import ExecutorRegistry
from executors.mock import MockExecutor


def write_config(root, data):
    config = root / "config" / "executors.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(data), encoding="utf-8")
    return config


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


def write_task(root, task_id, **fields):
    task_dir = root / "tasks" / "pending" / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": "pending",
        "objective": "Exercise executor registry.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
        "acceptance_criteria": ["Registry flow can pass review."],
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


class ExecutorRegistryTests(unittest.TestCase):
    def test_resolves_mock_executor_by_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = write_config(
                root,
                {
                    "executors": {
                        "named_mock": {
                            "type": "mock",
                            "role": "worker",
                            "enabled": True,
                            "output": "named output",
                        }
                    }
                },
            )

            registry = ExecutorRegistry(config).load()
            resolved = registry.resolve(name="named_mock", task={"id": "t1"})

            self.assertFalse(resolved["fallback"])
            self.assertEqual(resolved["reason"], "name")
            self.assertIsInstance(resolved["executor"], MockExecutor)
            self.assertEqual(resolved["executor"].execute({"id": "t1"}, {})["output"], "named output")

    def test_resolves_mock_executor_by_role(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = write_config(
                root,
                {
                    "executors": {
                        "role_mock": {
                            "type": "mock",
                            "role": "reviewer",
                            "enabled": True,
                        }
                    }
                },
            )

            registry = ExecutorRegistry(config).load()
            resolved = registry.resolve(role="reviewer", task={"id": "t2"})

            self.assertFalse(resolved["fallback"])
            self.assertEqual(resolved["reason"], "role")
            self.assertEqual(resolved["config"]["name"], "role_mock")

    def test_invalid_config_is_recorded_and_falls_back_to_mock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = write_config(root, {"executors": ["not", "an", "object"]})

            registry = ExecutorRegistry(config).load()
            resolved = registry.resolve(name="missing", task={"id": "t3", "role": "harness"})

            self.assertTrue(registry.errors)
            self.assertTrue(resolved["fallback"])
            self.assertIsInstance(resolved["executor"], MockExecutor)

    def test_disabled_cli_config_falls_back_without_subprocess(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = write_config(
                root,
                {
                    "executors": {
                        "codex_s10": {
                            "type": "cli",
                            "role": "harness",
                            "command": "codex",
                            "enabled": False,
                        }
                    }
                },
            )

            registry = ExecutorRegistry(config).load()
            with patch("subprocess.Popen") as popen:
                resolved = registry.resolve(name="codex_s10", task={"id": "t4"})
                result = resolved["executor"].execute({"id": "t4"}, {"task_id": "t4"})

            self.assertTrue(resolved["fallback"])
            self.assertTrue(result["success"])
            popen.assert_not_called()

    def test_runner_uses_registry_and_logs_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_config(
                root,
                {
                    "executors": {
                        "task_mock": {
                            "type": "mock",
                            "role": "harness",
                            "enabled": True,
                        }
                    }
                },
            )
            write_task(root, "registry_done", executor="task_mock")

            runner.main()

            task_json = root / "tasks" / "done" / "registry_done" / "task.json"
            self.assertEqual(json.loads(task_json.read_text(encoding="utf-8"))["status"], "done")
            events = read_events(root, "registry_done")
            event_names = [event["event"] for event in events]
            self.assertIn("executor_registry_loaded", event_names)
            self.assertIn("executor_resolved", event_names)
            self.assertNotIn("executor_fallback_used", event_names)
            self.assertIn("executor_completed", event_names)

    def test_runner_logs_registry_error_and_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_config(root, {"executors": []})
            write_task(root, "registry_fallback", executor="missing_mock")

            runner.main()

            events = read_events(root, "registry_fallback")
            event_names = [event["event"] for event in events]
            self.assertIn("executor_registry_error", event_names)
            self.assertIn("executor_fallback_used", event_names)
            self.assertIn("executor_resolved", event_names)


if __name__ == "__main__":
    unittest.main()
