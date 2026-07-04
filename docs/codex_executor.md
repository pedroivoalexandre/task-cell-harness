# Codex Executor Dry-Run

`executors/codex_executor.py` prepares a Codex execution path without running
Codex CLI. It uses:

- `CLIAdapter` for command metadata and dry-run validation
- `PromptBuilder` for Codex prompt text
- `ArtifactManager` to register the prepared prompt
- `ExecutionContext` for execution metadata

The executor returns dry-run metadata and never starts a subprocess.
