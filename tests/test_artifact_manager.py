import json
import tempfile
import unittest
from pathlib import Path

import runner
from artifact_manager import ArtifactManager, sha256_file
from execution_context import ExecutionContext


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
    config.write_text(json.dumps({"executors": {}}), encoding="utf-8")


def write_task(root, task_id):
    task_dir = root / "tasks" / "pending" / task_id
    task_dir.mkdir(parents=True)
    (task_dir / "task.json").write_text(
        json.dumps(
            {
                "id": task_id,
                "title": f"Task {task_id}",
                "status": "pending",
                "objective": "Exercise artifact registration.",
                "created_at": "2026-07-02T00:00:00+00:00",
                "priority": "normal",
                "role": "harness",
                "acceptance_criteria": ["Artifact report can be registered."],
            }
        ),
        encoding="utf-8",
    )


class ArtifactManagerTests(unittest.TestCase):
    def test_register_file_copies_artifact_and_updates_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "report.md"
            source.write_text("# Report\n", encoding="utf-8")
            context = ExecutionContext.create({"id": "artifact_task", "title": "Artifact Task"})
            manager = ArtifactManager(root / "artifacts")

            artifact = manager.register_file(source, context, kind="markdown_report")

            target = Path(artifact["path"])
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "# Report\n")
            self.assertEqual(artifact["task_id"], "artifact_task")
            self.assertEqual(artifact["execution_id"], context.execution_id)
            self.assertEqual(artifact["kind"], "markdown_report")
            self.assertEqual(artifact["size_bytes"], source.stat().st_size)
            self.assertEqual(artifact["checksum_sha256"], sha256_file(target))

            index = json.loads(manager.index_path(context).read_text(encoding="utf-8"))
            self.assertEqual(index, [artifact])
            self.assertEqual(context.log_context["artifact_index"], str(manager.index_path(context)))

    def test_runner_registers_markdown_report_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_config(root)
            write_task(root, "artifact_done")

            runner.main()

            artifact_indexes = list((root / "artifacts" / "artifact_done").glob("*/artifacts.json"))
            self.assertEqual(len(artifact_indexes), 1)
            artifacts = json.loads(artifact_indexes[0].read_text(encoding="utf-8"))
            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0]["kind"], "markdown_report")
            self.assertEqual(artifacts[0]["name"], "artifact_done.md")
            self.assertTrue(Path(artifacts[0]["path"]).exists())


if __name__ == "__main__":
    unittest.main()
