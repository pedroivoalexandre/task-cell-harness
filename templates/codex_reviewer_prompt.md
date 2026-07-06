# Codex Reviewer Prompt

Task Cell:
- `task_id`: {{task_id}}
- `title`: {{title}}

Implementation summary:
{{implementation_summary}}

Acceptance criteria:
{{acceptance_criteria}}

Review requirements:
- verify the implementation against the acceptance criteria;
- identify bugs, regressions, or missing coverage;
- call out portability or policy issues;
- keep the review concise and evidence-based.

Forbidden actions:
- do not execute real agents;
- do not use Tablet;
- do not rely on network access.

Return:
- decision: `approved`, `needs_changes`, or `failed`;
- short rationale;
- follow-up actions if needed.
