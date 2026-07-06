import json
import unittest
from pathlib import Path


class QueueFormatTests(unittest.TestCase):
    def test_queue_format_and_state_mapping_are_consistent(self):
        docs_text = Path("docs/queue_format.md").read_text(encoding="utf-8")
        config = json.loads(Path("config/queue_states.json").read_text(encoding="utf-8"))

        self.assertIn("tasks/pending/", docs_text)
        self.assertIn("tasks/running/", docs_text)
        self.assertIn("tasks/review/", docs_text)
        self.assertIn("tasks/needs_revision/", docs_text)
        self.assertEqual(config["operational_mapping"]["created"], "pending")
        self.assertEqual(config["operational_mapping"]["ready"], "pending")
        self.assertEqual(config["operational_mapping"]["implementing"], "running")
        self.assertEqual(config["operational_mapping"]["reviewing"], "review")
        self.assertEqual(config["operational_mapping"]["approved"], "done")
        self.assertEqual(config["operational_mapping"]["needs_changes"], "needs_revision")
        self.assertEqual(config["operational_mapping"]["failed"], "failed")
        self.assertEqual(config["operational_mapping"]["archived"], "done")


if __name__ == "__main__":
    unittest.main()
