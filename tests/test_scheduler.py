import json
import tempfile
import unittest
from pathlib import Path

from scheduler import select_next_task


def write_task(root, task_id, **fields):
    task_dir = root / "tasks" / "pending" / task_id
    task_dir.mkdir(parents=True)
    data = {
        "id": task_id,
        "title": f"Task {task_id}",
        "status": "pending",
        "objective": "Exercise scheduler.",
        "created_at": "2026-07-02T00:00:00+00:00",
        "priority": "normal",
        "role": "harness",
    }
    data.update(fields)
    (task_dir / "task.json").write_text(json.dumps(data), encoding="utf-8")
    return task_dir


class SchedulerTests(unittest.TestCase):
    def test_priority_order_selects_urgent_before_other_priorities(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_task(root, "normal_task", priority="normal")
            write_task(root, "high_task", priority="high")
            write_task(root, "urgent_task", priority="urgent")
            write_task(root, "low_task", priority="low")

            selected = select_next_task(root / "tasks" / "pending")

            self.assertEqual(selected["id"], "urgent_task")

    def test_created_at_breaks_priority_ties(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_task(root, "newer", priority="high", created_at="2026-07-02T02:00:00+00:00")
            write_task(root, "older", priority="high", created_at="2026-07-02T01:00:00+00:00")

            selected = select_next_task(root / "tasks" / "pending")

            self.assertEqual(selected["id"], "older")

    def test_revision_count_and_id_make_selection_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_task(root, "task_b", revision_count=1)
            write_task(root, "task_a", revision_count=0)
            write_task(root, "task_c", revision_count=0)

            selected = select_next_task(root / "tasks" / "pending")

            self.assertEqual(selected["id"], "task_a")

    def test_requeued_task_uses_last_requeued_at_to_avoid_starvation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_task(
                root,
                "requeued_old_task",
                created_at="2026-07-01T00:00:00+00:00",
                revision_count=1,
                last_requeued_at="2026-07-03T00:00:00+00:00",
            )
            write_task(
                root,
                "new_task",
                created_at="2026-07-02T00:00:00+00:00",
                revision_count=0,
            )

            selected = select_next_task(root / "tasks" / "pending")

            self.assertEqual(selected["id"], "new_task")


if __name__ == "__main__":
    unittest.main()
