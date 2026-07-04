import tempfile
import unittest
from pathlib import Path

from runtime_validation import RuntimeValidator


class RuntimeValidationTests(unittest.TestCase):
    def test_validate_runtime_and_write_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in ("tasks", "reports", "logs", "artifacts", "config", "docs", "executors"):
                (root / directory).mkdir(parents=True)
            (root / "config" / "executors.json").write_text('{"executors": {}}', encoding="utf-8")
            for file_name in ("runner.py", "scheduler.py", "state_machine.py", "execution_context.py"):
                (root / file_name).write_text("", encoding="utf-8")

            result = RuntimeValidator(root).write_report(root / "reports" / "runtime_validation.md")

            self.assertTrue(result["ok"])
            self.assertTrue((root / "reports" / "runtime_validation.md").exists())


if __name__ == "__main__":
    unittest.main()
