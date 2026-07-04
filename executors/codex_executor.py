from artifact_manager import ArtifactManager
from executors.base import BaseExecutor
from executors.cli_adapter import CLIAdapter
from prompt_builder import PromptBuilder


class CodexExecutor(BaseExecutor):
    name = "codex"

    def __init__(self, config=None, artifact_root="artifacts"):
        self.config = config or {"command": "codex", "enabled": False}
        self.role = self.config.get("role", "codex")
        self.artifact_root = artifact_root
        self.adapter = CLIAdapter(self.config)
        self.prompt_builder = PromptBuilder()

    def execute(self, task, context):
        task = task or {}
        context = context or {}
        execution_context = context.get("execution_context")
        if execution_context:
            execution_context.update(executor_name=self.name, executor_role=self.role)

        prompt = self.prompt_builder.build_codex_prompt(
            task,
            contract=context.get("contract"),
            knowledge=context.get("knowledge"),
            execution_context=execution_context,
        )
        artifact = None
        if execution_context:
            artifact = ArtifactManager(context.get("artifact_root", self.artifact_root)).register_text(
                prompt,
                execution_context,
                "codex_prompt.md",
                kind="codex_prompt",
            )

        dry_run = self.adapter.dry_run(prompt, prompt_path=artifact.get("path") if artifact else None)
        return {
            "success": dry_run["success"],
            "executor": self.name,
            "role": self.role,
            "dry_run": True,
            "execution_id": getattr(execution_context, "execution_id", None),
            "prompt": prompt,
            "artifact": artifact,
            "command": dry_run["command"],
            "output": "Codex dry-run prepared prompt.",
            "error": "; ".join(dry_run["errors"]) if dry_run["errors"] else None,
        }
