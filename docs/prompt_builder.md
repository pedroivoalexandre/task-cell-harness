# Prompt Builder

`prompt_builder.py` creates minimal prompts for future Gemini and Codex executor
paths. It does not execute agents.

Inputs:

- `task`
- `contract`
- `knowledge`
- `execution_context`

Outputs:

- Gemini prompt via `build_gemini_prompt`
- Codex prompt via `build_codex_prompt`

Each prompt includes execution metadata, task details, contract content,
knowledge content, and an explicit simulated dry-run instruction.
