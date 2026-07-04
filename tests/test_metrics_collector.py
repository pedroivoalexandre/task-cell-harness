import json
import tempfile
import unittest
from pathlib import Path

from event_bus import Event, EventBus
from metrics_collector import MetricsCollector


class MetricsCollectorTests(unittest.TestCase):
    def test_collects_metrics_from_event_bus(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "metrics.json"
            bus = EventBus()
            collector = MetricsCollector(output)
            bus.subscribe("*", collector.handle_event)
            bus.emit(Event("task_selected", {"details": {}}))
            bus.emit(Event("executor_completed", {"details": {}}))
            bus.emit(Event("task_state_transition", {"details": {"to": "done"}}))

            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["tasks_processed"], 1)
            self.assertEqual(data["executor_success_count"], 1)
            self.assertEqual(data["tasks_done"], 1)


if __name__ == "__main__":
    unittest.main()
