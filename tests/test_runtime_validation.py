import tempfile
import unittest
from pathlib import Path

from runtime_validation import REQUIRED_MODULES, RuntimeValidator


class RuntimeValidationTests(unittest.TestCase):
    def test_validate_bootstraps_local_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in ("tasks", "config", "docs", "executors"):
                (root / directory).mkdir(parents=True, exist_ok=True)
            (root / "config" / "executors.json").write_text('{"executors": {}}', encoding="utf-8")
            for module in REQUIRED_MODULES:
                module_path = root / module
                module_path.parent.mkdir(parents=True, exist_ok=True)
                module_path.write_text("", encoding="utf-8")

            result = RuntimeValidator(root).validate()

            self.assertTrue(result["ok"])
            for directory in (
                "artifacts",
                "logs",
                "logs/errors",
                "logs/tasks",
                "reports",
                "runtime/locks",
                "runtime/state",
                "runtime/temp",
            ):
                self.assertTrue((root / directory).exists(), directory)

    def test_validate_runtime_and_write_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in ("tasks", "config", "docs", "executors"):
                (root / directory).mkdir(parents=True)
            (root / "config" / "executors.json").write_text('{"executors": {}}', encoding="utf-8")
            for module in REQUIRED_MODULES:
                module_path = root / module
                module_path.parent.mkdir(parents=True, exist_ok=True)
                module_path.write_text("", encoding="utf-8")

            result = RuntimeValidator(root).write_report(root / "reports" / "runtime_validation.md")

            self.assertTrue(result["ok"])
            self.assertTrue((root / "reports" / "runtime_validation.md").exists())


if __name__ == "__main__":
    unittest.main()
