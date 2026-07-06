# Gemini Implementer Prompt

Task Cell:
- `task_id`: {{task_id}}
- `title`: {{title}}

Objective:
{{objective}}

Context:
{{context}}

Inputs:
{{inputs}}

Constraints:
{{constraints}}

Allowed actions:
{{allowed_actions}}

Forbidden actions:
- do not execute real agents;
- do not use Tablet;
- do not rely on network access.

Acceptance criteria:
{{acceptance_criteria}}

Return:
- a concise implementation summary;
- files changed;
- tests run;
- any risks or follow-ups.
