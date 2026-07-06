import tempfile
import unittest
from pathlib import Path

from orchestrator_cycle import run_simulated_cycle


class OrchestratorCycleTests(unittest.TestCase):
    def test_run_simulated_cycle_creates_artifacts_and_updates_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            cell_data = {
                "task_id": "cycle_task",
                "title": "Cycle Task",
                "objective": "Exercise the simulated cycle.",
                "context": "Local dry-run validation.",
                "inputs": ["docs/task_cell_contract.md"],
                "constraints": ["No real agents"],
                "allowed_actions": ["edit local files"],
                "forbidden_actions": ["execute real agents", "use Tablet"],
                "acceptance_criteria": ["Cycle completes deterministically."],
                "expected_artifacts": ["cycle outputs"],
                "implementer_prompt": "Implement the requested local change.",
                "reviewer_prompt": "Review the local change against the acceptance criteria.",
                "status": "draft",
                "report": "",
            }

            result = run_simulated_cycle(cell_data, workspace)

            self.assertEqual(result["review_decision"], "approved")
            self.assertEqual(result["cell"]["status"], "approved")
            self.assertTrue((workspace / "cycle_task.implementation.md").exists())
            self.assertTrue((workspace / "cycle_task.review.md").exists())
            self.assertTrue((workspace / "cycle_task.report.md").exists())
            self.assertTrue((workspace / "cycle_task.json").exists())
            self.assertIn("Task Cell Report", (workspace / "cycle_task.report.md").read_text(encoding="utf-8"))
            self.assertIn("Gemini Implementer Prompt", result["implementation_prompt"])
            self.assertIn("Codex Reviewer Prompt", result["reviewer_prompt"])


if __name__ == "__main__":
    unittest.main()
