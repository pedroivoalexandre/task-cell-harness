# Gemini Executor Dry-Run

`executors/gemini_executor.py` prepares a Gemini execution path without running
Gemini CLI. It uses:

- `CLIAdapter` for command metadata and dry-run validation
- `PromptBuilder` for Gemini prompt text
- `ArtifactManager` to register the prepared prompt
- `ExecutionContext` for execution metadata

The executor returns dry-run metadata and never starts a subprocess.
