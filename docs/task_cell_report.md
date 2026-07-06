# Task Cell Report

## Purpose

This document defines the canonical final report shape for a Task Cell.
It is intended to summarize implementation, review, and outcome in a stable format that is easy to audit.

## Required Sections

- Task Cell ID
- objective
- summary of implementation
- summary of review
- files changed
- tests executed
- acceptance criteria
- risks
- pending items
- final status
- recommendation to the human/Central V2

## Recommended Shape

The report may be rendered as Markdown and/or JSON, but the canonical content should always be present.

## Suggested Markdown Layout

```text
# Task Cell Report

## Task Cell ID
{{task_id}}

## Objective
{{objective}}

## Implementation Summary
{{implementation_summary}}

## Review Summary
{{review_summary}}

## Files Changed
{{files_changed}}

## Tests Executed
{{tests_executed}}

## Acceptance Criteria
{{acceptance_criteria}}

## Risks
{{risks}}

## Pending Items
{{pending_items}}

## Final Status
{{final_status}}

## Recommendation
{{recommendation}}
```

## Compatibility Notes

The report format should remain compatible with local Markdown reports, JSON sidecars, and the existing `reports/` directory layout.
