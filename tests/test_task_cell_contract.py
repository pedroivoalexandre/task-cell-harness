import json
import unittest
from pathlib import Path


class TaskCellContractTests(unittest.TestCase):
    def test_contract_document_and_schema_reference_the_same_fields(self):
        docs_path = Path("docs/task_cell_contract.md")
        schema_path = Path("config/task_cell_schema.json")
        example_path = Path("tasks/example_task_cell.json")

        docs_text = docs_path.read_text(encoding="utf-8")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        example = json.loads(example_path.read_text(encoding="utf-8"))

        required_fields = schema["required"]
        for field in required_fields:
            self.assertIn(f"`{field}`", docs_text)
            self.assertIn(field, example)

        self.assertEqual(example["task_id"], "example_task_cell")
        self.assertEqual(example["status"], "draft")
        self.assertEqual(example["report"], "reports/example_task_cell.md")


if __name__ == "__main__":
    unittest.main()
