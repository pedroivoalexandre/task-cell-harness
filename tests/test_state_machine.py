import json
import tempfile
import unittest
from pathlib import Path

from state_machine import (
    ALLOWED_TRANSITIONS,
    InvalidTransition,
    transition_task,
    validate_transition,
)


class StateMachineTests(unittest.TestCase):
    def test_allowed_transitions_match_contract(self):
        self.assertEqual(
            ALLOWED_TRANSITIONS,
            {
                "pending": ("running",),
                "running": ("review", "done", "failed"),
                "review": ("done", "needs_revision", "failed"),
                "needs_revision": ("pending",),
                "failed": ("pending",),
                "done": (),
            },
        )

    def test_allows_configured_transition(self):
        validate_transition("pending", "running")

    def test_blocks_invalid_transition(self):
        with self.assertRaises(InvalidTransition):
            validate_transition("pending", "done")

    def test_transition_moves_task_updates_status_and_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task_dir = root / "tasks" / "pending" / "sample_task"
            task_dir.mkdir(parents=True)
            (task_dir / "task.json").write_text(
                json.dumps(
                    {
                        "id": "sample_task",
                        "title": "Sample task",
                        "status": "pending",
                        "objective": "Exercise state machine.",
                        "created_at": "2026-07-02T00:00:00+00:00",
                        "priority": "normal",
                        "role": "harness",
                    }
                ),
                encoding="utf-8",
            )
            events = []

            def log_event(event, task_id=None, details=None):
                record = {
                    "event": event,
                    "task_id": task_id,
                    "details": details or {},
                }
                events.append(record)
                harness_log = root / "logs" / "harness.log"
                task_log = root / "logs" / "tasks" / f"{task_id}.jsonl"
                harness_log.parent.mkdir(parents=True, exist_ok=True)
                task_log.parent.mkdir(parents=True, exist_ok=True)
                line = json.dumps(record) + "\n"
                harness_log.write_text(line, encoding="utf-8")
                task_log.write_text(line, encoding="utf-8")

            destination = transition_task(task_dir, "running", log_event)

            self.assertEqual(destination, root / "tasks" / "running" / "sample_task")
            self.assertFalse(task_dir.exists())
            self.assertTrue(destination.exists())

            data = json.loads((destination / "task.json").read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "running")
            self.assertIn("updated_at", data)

            self.assertEqual(events[0]["event"], "task_state_transition")
            self.assertEqual(events[0]["task_id"], "sample_task")
            self.assertEqual(events[0]["details"]["from"], "pending")
            self.assertEqual(events[0]["details"]["to"], "running")
            self.assertTrue(events[0]["details"]["status_updated"])

            harness_records = (root / "logs" / "harness.log").read_text(
                encoding="utf-8"
            ).splitlines()
            task_records = (root / "logs" / "tasks" / "sample_task.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(len(harness_records), 1)
            self.assertEqual(harness_records, task_records)
            self.assertEqual(json.loads(task_records[0])["event"], "task_state_transition")


if __name__ == "__main__":
    unittest.main()
