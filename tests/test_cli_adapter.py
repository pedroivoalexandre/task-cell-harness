import unittest
from unittest.mock import patch

from executors.cli_adapter import CLIAdapter


class CLIAdapterTests(unittest.TestCase):
    def test_validates_config_and_builds_command(self):
        adapter = CLIAdapter({"command": "gemini", "args": ["--model", "dry"], "container": "debian"})

        self.assertEqual(adapter.validate_config(), [])
        self.assertEqual(
            adapter.build_command(prompt_path="prompt.md"),
            ["gemini", "--model", "dry", "--prompt-file", "prompt.md"],
        )

    def test_reports_invalid_config(self):
        adapter = CLIAdapter({})

        self.assertIn("command must be a non-empty string", adapter.validate_config())
        self.assertFalse(adapter.dry_run("prompt")["success"])

    def test_dry_run_does_not_execute_subprocess(self):
        adapter = CLIAdapter({"command": "codex"})

        with patch("subprocess.Popen") as popen:
            result = adapter.dry_run("hello")

        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["stdio"]["stdin"], "hello")
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
