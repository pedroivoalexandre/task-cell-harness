import tempfile
import unittest
from pathlib import Path

from orchestrator_cycle import run_simulated_cycle


class OrchestratorE2ESimulatedTests(unittest.TestCase):
    def test_simulated_end_to_end_cycle_produces_traceable_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            cell_data = {
                "task_id": "e2e_task",
                "title": "E2E Task",
                "objective": "Prove the orchestrator MVP without real agents.",
                "context": "Simulated end-to-end validation.",
                "inputs": ["docs/task_cell_contract.md", "docs/task_cell_report.md"],
                "constraints": ["No real agents", "No Tablet"],
                "allowed_actions": ["write local files", "generate prompts"],
                "forbidden_actions": ["execute real agents", "use Tablet", "use network"],
                "acceptance_criteria": ["The cycle completes", "Outputs are traceable"],
                "expected_artifacts": [
                    "e2e_task.implementation.md",
                    "e2e_task.review.md",
                    "e2e_task.report.md",
                    "e2e_task.json",
                ],
                "implementer_prompt": "Implement the requested local change.",
                "reviewer_prompt": "Review the local change against the acceptance criteria.",
                "status": "draft",
                "report": "",
            }

            result = run_simulated_cycle(cell_data, workspace)

            self.assertEqual(result["review_decision"], "approved")
            self.assertEqual(result["cell"]["status"], "approved")
            self.assertEqual(result["cell"]["report"], result["report_path"])
            self.assertEqual(Path(result["implementation_path"]).name, "e2e_task.implementation.md")
            self.assertEqual(Path(result["review_path"]).name, "e2e_task.review.md")
            self.assertEqual(Path(result["report_path"]).name, "e2e_task.report.md")
            self.assertTrue((workspace / "e2e_task.implementation.md").exists())
            self.assertTrue((workspace / "e2e_task.review.md").exists())
            self.assertTrue((workspace / "e2e_task.report.md").exists())
            self.assertTrue((workspace / "e2e_task.json").exists())
            report_text = (workspace / "e2e_task.report.md").read_text(encoding="utf-8")
            self.assertIn("Task Cell Report", report_text)
            self.assertIn("Final Status", report_text)
            self.assertIn("approved", report_text)
            self.assertIn("No real agents were executed.", report_text)


if __name__ == "__main__":
    unittest.main()
