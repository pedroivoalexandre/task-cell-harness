# Task Cell Contract

## Purpose

A Task Cell is the canonical unit of work handled by the Task Cell Harness.
It packages the information needed to implement, review, and report a task in a way that remains portable and auditable.

## Required Fields

A Task Cell should define at least the following fields:

- `task_id`
- `title`
- `objective`
- `context`
- `inputs`
- `constraints`
- `allowed_actions`
- `forbidden_actions`
- `acceptance_criteria`
- `expected_artifacts`
- `implementer_prompt`
- `reviewer_prompt`
- `status`
- `report`

## Recommended Shape

The contract can be represented as a JSON document, a task fixture, or a documentation-backed schema.
The key requirement is that the structure stays explicit and easy to review.

## Semantics

- `task_id`: stable identifier for the cell.
- `title`: short human-readable label.
- `objective`: the concrete outcome expected from the cell.
- `context`: background needed to understand the work.
- `inputs`: source material or references available to the implementer.
- `constraints`: boundaries that must not be violated.
- `allowed_actions`: actions permitted during implementation or review.
- `forbidden_actions`: actions explicitly disallowed.
- `acceptance_criteria`: conditions required for success.
- `expected_artifacts`: files or outputs that should exist when the cell is complete.
- `implementer_prompt`: prompt used to guide implementation.
- `reviewer_prompt`: prompt used to guide review.
- `status`: lifecycle state of the cell.
- `report`: final consolidated report for the cell.

## Compatibility Notes

The contract must remain compatible with the existing `tasks/`, `logs/tasks/`, and `reports/` layout.
It should not require real-agent execution, and it should not depend on distributed workers.

## Example

```json
{
  "task_id": "example_task_cell",
  "title": "Example Task Cell",
  "objective": "Demonstrate a complete cell contract.",
  "context": "Local harness validation.",
  "inputs": [],
  "constraints": [],
  "allowed_actions": ["edit local files", "run local tests"],
  "forbidden_actions": ["execute real agents", "use Tablet"],
  "acceptance_criteria": ["Contract fields are present"],
  "expected_artifacts": ["docs/task_cell_contract.md"],
  "implementer_prompt": "Implement the requested local change.",
  "reviewer_prompt": "Review the local change against the acceptance criteria.",
  "status": "draft",
  "report": "reports/example_task_cell.md"
}
```
