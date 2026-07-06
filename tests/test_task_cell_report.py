import unittest
from pathlib import Path


class TaskCellReportTests(unittest.TestCase):
    def test_report_template_includes_required_sections(self):
        docs_text = Path("docs/task_cell_report.md").read_text(encoding="utf-8")
        template_text = Path("templates/task_cell_report.md").read_text(encoding="utf-8")

        required_sections = [
            "Task Cell ID",
            "Objective",
            "Implementation Summary",
            "Review Summary",
            "Files Changed",
            "Tests Executed",
            "Acceptance Criteria",
            "Risks",
            "Pending Items",
            "Final Status",
            "Recommendation",
        ]

        for section in required_sections:
            self.assertIn(section, docs_text)
            self.assertIn(section, template_text)


if __name__ == "__main__":
    unittest.main()
