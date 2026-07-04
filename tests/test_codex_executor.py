import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from execution_context import ExecutionContext
from executors.codex_executor import CodexExecutor


class CodexExecutorTests(unittest.TestCase):
    def test_codex_executor_dry_run_prepares_prompt_and_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = ExecutionContext.create({"id": "codex_task", "title": "Codex Task"})
            executor = CodexExecutor({"command": "codex", "role": "developer"}, artifact_root=root / "artifacts")

            with patch("subprocess.Popen") as popen:
                result = executor.execute(
                    {"id": "codex_task", "title": "Codex Task"},
                    {
                        "execution_context": context,
                        "artifact_root": root / "artifacts",
                        "contract": {"mode": "dry-run"},
                        "knowledge": {"note": "No subprocess."},
                    },
                )

            self.assertTrue(result["success"])
            self.assertTrue(result["dry_run"])
            self.assertIn("Task Cell Harness Prompt for Codex", result["prompt"])
            self.assertEqual(result["execution_id"], context.execution_id)
            self.assertEqual(context.executor_name, "codex")
            self.assertEqual(context.executor_role, "developer")
            artifact = result["artifact"]
            self.assertEqual(artifact["kind"], "codex_prompt")
            self.assertTrue(Path(artifact["path"]).exists())
            index = json.loads((root / "artifacts" / "codex_task" / context.execution_id / "artifacts.json").read_text(encoding="utf-8"))
            self.assertEqual(index[0]["name"], "codex_prompt.md")
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
