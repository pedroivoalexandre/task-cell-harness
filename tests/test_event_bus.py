import unittest

from event_bus import Event, EventBus
from events import TaskSelected


class EventBusTests(unittest.TestCase):
    def test_subscribe_emit_and_history(self):
        bus = EventBus()
        seen = []
        bus.subscribe("task", lambda event: seen.append(event.payload["id"]))
        bus.emit(Event("task", {"id": "one"}))
        self.assertEqual(seen, ["one"])
        self.assertEqual(len(bus.history), 1)

    def test_typed_events_are_serializable(self):
        event = TaskSelected(payload={"task_id": "task_1", "note": "typed"})
        data = event.to_dict()
        self.assertEqual(data["event_type"], "task_selected")
        self.assertTrue(data["event_id"])
        self.assertEqual(event.to_record()["event"], "task_selected")

    def test_handler_errors_are_captured(self):
        bus = EventBus()
        def boom(event):
            raise RuntimeError("bad handler")
        bus.subscribe("task", boom)
        bus.emit(Event("task", {}))
        self.assertEqual(len(bus.handler_errors), 1)
        self.assertIn("bad handler", bus.handler_errors[0]["error"])


if __name__ == "__main__":
    unittest.main()
