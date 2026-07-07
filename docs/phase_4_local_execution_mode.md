# FASE 4 Local Execution Mode

## Purpose

This document defines how the Task Cell Harness operates in FASE 4 on the Lenovo Yoga.
The mode is real, but it remains supervised, local, and conservative.

## Operating Mode

FASE 4 uses a manual-assisted workflow:

1. the human selects a small, safe Task Cell;
2. the harness prepares prompts and local fixtures;
3. the human approves the prompts;
4. the human runs or simulates the implementation step;
5. the human runs or simulates the review step;
6. the harness records the inputs, outputs, and final decision;
7. the harness emits a report and a final status.

## Execution Rules

- no agent should run automatically;
- no external CLI should be invoked without explicit approval;
- dry-run is the default when a step can be validated without side effects;
- local files are the source of truth for the phase 4 execution trace;
- the human remains the final decision-maker for approval, rollback, and completion.

## Task Cell Approval Criteria

A Task Cell is approved for phase 4 local execution only when:

- the scope is small and easy to revert;
- the task is local to the harness or its documentation;
- the inputs are available locally;
- the acceptance criteria are precise;
- the allowed and forbidden actions are explicit;
- the expected artifacts are concrete;
- the human agrees that the risk is low.

## Abort Criteria

Stop the execution if:

- the task expands into distributed work;
- the task requires Tablet integration;
- the task requires an external agent to run automatically;
- the task changes critical projects;
- the task cannot be reviewed locally;
- the task can no longer be rolled back safely.

## Recommended First Uses

- documentation improvements for the harness itself;
- small validation tasks around Task Cell fixtures;
- small report or template refinements;
- small tests that stay inside the local repository.

## Configuration

The phase 4 execution mode is described in `config/phase_4_execution_mode.json`.
That file is intentionally conservative and can be used as a runtime gate or as a human review checklist.

## Dry-Run Fallback

When the outcome is uncertain, the workflow should remain in dry-run.
Dry-run means:

- prompts are generated;
- expected outputs are described;
- no autonomous execution is attempted;
- the human can review the full change before anything is applied.
