import unittest

from execution_context import ExecutionContext
from prompt_builder import PromptBuilder, build_codex_prompt, build_gemini_prompt


class PromptBuilderTests(unittest.TestCase):
    def test_builds_gemini_prompt_with_task_and_context(self):
        context = ExecutionContext.create({"id": "prompt_task", "title": "Prompt Task"})
        prompt = PromptBuilder().build_gemini_prompt(
            {"id": "prompt_task", "title": "Prompt Task", "objective": "Build prompt."},
            contract={"required": ["objective"]},
            knowledge={"note": "Use dry-run."},
            execution_context=context,
        )

        self.assertIn("Task Cell Harness Prompt for Gemini", prompt)
        self.assertIn(context.execution_id, prompt)
        self.assertIn("prompt_task", prompt)
        self.assertIn("Build prompt.", prompt)
        self.assertIn("Simulated dry-run only", prompt)

    def test_builds_codex_prompt(self):
        prompt = build_codex_prompt({"id": "codex_prompt", "title": "Codex Prompt"})

        self.assertIn("Task Cell Harness Prompt for Codex", prompt)
        self.assertIn("codex_prompt", prompt)
        self.assertIn("Do not execute external agents", prompt)

    def test_module_gemini_helper_matches_builder_shape(self):
        prompt = build_gemini_prompt({"id": "helper_task"})

        self.assertIn("Task Cell Harness Prompt for Gemini", prompt)
        self.assertIn("helper_task", prompt)


if __name__ == "__main__":
    unittest.main()
