import json
import tempfile
import unittest
from pathlib import Path

from execution_context import ExecutionContext
from report_builder import ReportBuilder


class ReportBuilderTests(unittest.TestCase):
    def test_writes_markdown_and_json_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = ExecutionContext.create({"id": "report_task", "title": "Report Task"})
            result = ReportBuilder().write_report(
                root / "report_task.md",
                "report_task",
                "Report Task",
                "Done",
                review_result={"decision": "done", "summary": "Approved.", "errors": []},
                execution_context=context,
                artifacts=[{"name": "report_task.md", "kind": "markdown_report", "path": "artifact.md"}],
                logs=[{"event": "executor_completed"}],
            )

            markdown = result["markdown"].read_text(encoding="utf-8")
            self.assertIn("# Task Report: report_task", markdown)
            self.assertIn("- Decision: done", markdown)
            self.assertIn(context.execution_id, markdown)
            self.assertTrue(result["json"].exists())

            payload = json.loads(result["json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["task_id"], "report_task")
            self.assertEqual(payload["review"]["decision"], "done")
            self.assertEqual(payload["execution_context"]["execution_id"], context.execution_id)
            self.assertEqual(payload["artifacts"][0]["kind"], "markdown_report")


if __name__ == "__main__":
    unittest.main()
