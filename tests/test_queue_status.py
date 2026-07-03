import contextlib
import io
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


def write_task(root, state, task_id, **fields):
    task_dir = root / "tasks" / state / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": state,
        "objective": "Exercise queue status.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
    }
    data.update(fields)
    (task_dir / "task.json").write_text(json.dumps(data), encoding="utf-8")
    return task_dir


def snapshot_files(root):
    return {
        path.relative_to(root): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class QueueStatusTests(unittest.TestCase):
    def test_status_lists_states_next_task_and_does_not_modify_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(root, "pending", "normal_old", created_at="2026-07-02T00:00:00+00:00")
            write_task(
                root,
                "pending",
                "urgent_new",
                priority="urgent",
                created_at="2026-07-03T00:00:00+00:00",
                attempt_count=1,
                max_attempts=4,
            )
            write_task(
                root,
                "pending",
                "requeued",
                priority="urgent",
                created_at="2026-07-01T00:00:00+00:00",
                revision_count=1,
                last_requeued_at="2026-07-04T00:00:00+00:00",
            )
            write_task(root, "running", "running_task")
            write_task(root, "review", "review_task")
            write_task(root, "needs_revision", "revision_task", revision_count=1)
            write_task(root, "failed", "failed_task")
            write_task(root, "done", "done_task")
            before = snapshot_files(root)

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                result = runner.main(["status"])

            output = buffer.getvalue()
            self.assertEqual(result, output.rstrip("\n"))
            for state in runner.QUEUE_STATES:
                self.assertIn(f"{state}:\n", output)
            self.assertLess(output.index("- id: urgent_new"), output.index("- id: requeued"))
            self.assertLess(output.index("- id: requeued"), output.index("- id: normal_old"))
            self.assertIn("last_requeued_at: 2026-07-04T00:00:00+00:00", output)
            self.assertIn("Next task:\n- id: urgent_new", output)
            self.assertIn("- attempts: 1/4", output)
            self.assertIn(
                "- reason/order basis: priority=urgent, queue_timestamp=2026-07-03T00:00:00+00:00, revision_count=0, id=urgent_new",
                output,
            )
            self.assertEqual(snapshot_files(root), before)

    def test_status_reports_no_next_task_when_pending_is_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configure_runner_root(root)
            write_task(root, "done", "done_task")

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                output = runner.main(["status"])

            self.assertIn("pending:\n- none", output)
            self.assertIn("Next task:\n- none", output)


if __name__ == "__main__":
    unittest.main()
