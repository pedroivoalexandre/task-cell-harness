import json


class PromptBuilder:
    def build_gemini_prompt(self, task, contract=None, knowledge=None, execution_context=None):
        return self._build_prompt("Gemini", task, contract, knowledge, execution_context)

    def build_codex_prompt(self, task, contract=None, knowledge=None, execution_context=None):
        return self._build_prompt("Codex", task, contract, knowledge, execution_context)

    def _build_prompt(self, target, task, contract, knowledge, execution_context):
        task = task or {}
        sections = [
            f"# Task Cell Harness Prompt for {target}",
            "",
            "## Execution",
            f"- execution_id: {getattr(execution_context, 'execution_id', '')}",
            f"- task_id: {task.get('id') or getattr(execution_context, 'task_id', '')}",
            f"- task_title: {task.get('title') or getattr(execution_context, 'task_title', '')}",
            "",
            "## Task",
            _format_value(task),
            "",
            "## Contract",
            _format_value(contract or {}),
            "",
            "## Knowledge",
            _format_value(knowledge or {}),
            "",
            "## Execution Mode",
            "Simulated dry-run only. Do not execute external agents or subprocesses.",
        ]
        return "\n".join(sections).rstrip() + "\n"


def _format_value(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def build_gemini_prompt(task, contract=None, knowledge=None, execution_context=None):
    return PromptBuilder().build_gemini_prompt(task, contract, knowledge, execution_context)


def build_codex_prompt(task, contract=None, knowledge=None, execution_context=None):
    return PromptBuilder().build_codex_prompt(task, contract, knowledge, execution_context)
