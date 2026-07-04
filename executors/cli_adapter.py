from pathlib import Path


class CLIAdapter:
    def __init__(self, config=None):
        self.config = config or {}

    def validate_config(self):
        errors = []
        command = self.config.get("command")
        if not command or not isinstance(command, str):
            errors.append("command must be a non-empty string")
        container = self.config.get("container")
        if container is not None and not isinstance(container, str):
            errors.append("container must be a string when provided")
        return errors

    def build_command(self, prompt_path=None):
        command = [self.config.get("command", "")]
        args = self.config.get("args") or []
        if isinstance(args, str):
            args = [args]
        command.extend(args)
        if prompt_path:
            command.extend(["--prompt-file", str(prompt_path)])
        return [part for part in command if part]

    def validate_environment(self):
        return {
            "valid": not self.validate_config(),
            "dry_run": True,
            "container": self.config.get("container"),
        }

    def prepare_stdio(self, prompt):
        return {
            "stdin": prompt or "",
            "stdout": "",
            "stderr": "",
        }

    def dry_run(self, prompt, prompt_path=None):
        errors = self.validate_config()
        return {
            "success": not errors,
            "dry_run": True,
            "command": self.build_command(prompt_path=prompt_path),
            "environment": self.validate_environment(),
            "stdio": self.prepare_stdio(prompt),
            "errors": errors,
        }
