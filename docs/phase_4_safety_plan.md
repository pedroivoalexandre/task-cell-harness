# FASE 4 Safety Plan

## Purpose

FASE 4 validates real local use of the Task Cell Harness in a supervised mode.
The goal is to support real tasks, prompts, reviews, and reports without autonomous dispatch, distributed execution, or Tablet integration.

## What Agents May Do

- read the Task Cell contract and the current local context;
- generate implementation prompts for a human-approved task;
- generate review prompts for a human-approved task;
- record implementation notes supplied by a human;
- record review notes supplied by a human;
- write local Markdown and JSON task artifacts within the phase 4 scope;
- produce traceable reports that explain what happened and what remains pending.

## What Agents May Not Do

- execute automatically without human approval;
- launch multiple agents in parallel;
- distribute work across machines;
- use the Tablet as a control plane;
- call Gemini, Claude, Codex, or any other CLI as a subprocess without explicit approval;
- change critical projects;
- perform deploys or release actions;
- bypass review or write automation that suppresses the human decision point.

## Human Review Requirements

Human review is required before:

- any prompt is treated as actionable;
- any file write outside the documented scope;
- any Git operation that changes repository state;
- any command that can affect external state;
- any rollback decision;
- any recommendation to advance into FASE 5.

## Shell Limits

- local commands must stay within the documented phase 4 scope;
- shell use must be explicit and auditable;
- no hidden subprocess execution of external agents;
- no network-dependent workflow unless it is explicitly authorized and necessary for review;
- dry-run remains the safe default when the outcome can be validated locally.

## File Write Limits

- prefer narrow file edits over broad rewrites;
- keep phase 4 artifacts in the documented `docs/`, `tasks/`, `reports/`, and `config/` locations;
- avoid touching unrelated source files unless the task is explicitly about them;
- preserve compatibility with clean clones and existing runtime layout.

## Git Limits

- no automatic commit creation;
- no push without explicit authorization;
- no history rewriting;
- no force-push;
- no unstaged follow-up changes that hide what the human reviewed.

## Rollback Policy

- keep changes small enough to revert safely;
- revert only the phase 4 files involved in the issue;
- record the reason for rollback in the relevant report;
- if rollback would cross an architectural boundary, pause and ask Central V2.

## Logs and Reports

- every supervised step should end in a local report entry;
- reports should say whether the step was implemented, reviewed, deferred, or aborted;
- logs should stay local and versioned only when they are intended to be canonical;
- report files should summarize inputs, constraints, outputs, and unresolved items.

## Abort Criteria

Abort execution if any of the following appear:

- a request for distributed execution in phase 4;
- a request to integrate the Tablet in phase 4;
- a request to automate agent execution without approval;
- an architectural change that belongs to FASE 5 or FASE 6;
- a need to alter a critical project outside the harness scope;
- a loss of traceability that prevents safe review;
- a mismatch between the requested task and the approved phase 4 boundary.

## Phase Boundaries

- FASE 4 is local and supervised.
- FASE 5 is the first distributed execution phase.
- FASE 6 is the operations, observability, and stabilization phase.

## Operating Rule

If a change cannot be explained, reviewed, and rolled back locally, it does not belong in FASE 4.
