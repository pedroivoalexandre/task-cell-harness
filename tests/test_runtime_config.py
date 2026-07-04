import json
import tempfile
import unittest
from pathlib import Path

from runtime_config import RuntimeConfig


class RuntimeConfigTests(unittest.TestCase):
    def test_defaults_are_safe_dry_run(self):
        config = RuntimeConfig()
        self.assertEqual(config.execution_mode, "dry_run")
        self.assertTrue(config.dry_run)
        self.assertFalse(config.enable_real_executors)
        self.assertFalse(config.allows_real_execution())

    def test_loads_file_with_safe_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime.json"
            path.write_text(json.dumps({"default_timeout_seconds": 10}), encoding="utf-8")
            config = RuntimeConfig.load(path)
            self.assertEqual(config.default_timeout_seconds, 10)
            self.assertTrue(config.dry_run)

    def test_blocks_real_mode_when_not_enabled(self):
        with self.assertRaises(ValueError):
            RuntimeConfig(execution_mode="real", enable_real_executors=False).validate()

    def test_allows_real_executor_only_with_feature_flag(self):
        config = RuntimeConfig(
            execution_mode="real",
            dry_run=False,
            enable_real_executors=True,
            feature_flags={"real_executors": {"codex_s10": True}},
        )
        config.validate()
        self.assertTrue(config.allows_real_execution())
        self.assertTrue(config.allows_real_executor("codex_s10"))
        self.assertFalse(config.allows_real_executor("gemini_s10"))


if __name__ == "__main__":
    unittest.main()
